#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# update_deployment.sh
# Production-grade deployment script for Cloud Run Job and Cloud Workflows.
#
# Usage:
#   ./update_deployment.sh [--project-id gcli-intern-project-2026] [--region us-central1] [--tag TAG]

set -euo pipefail

# Configuration defaults
PROJECT_ID="gcli-intern-project-2026"
REGION="us-central1"
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")
TAG="${GIT_SHA}"

# Parse command line flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --project-id) PROJECT_ID="$2"; shift 2 ;;
    --region)     REGION="$2"; shift 2 ;;
    --tag)        TAG="$2"; shift 2 ;;
    -h|--help)    echo "Usage: $0 [--project-id ID] [--region REGION] [--tag TAG]"; exit 0 ;;
    *)            echo "Unknown argument: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

IMAGE_REPO="us-central1-docker.pkg.dev/${PROJECT_ID}/pr-gen-repo/jetski-worker"
IMAGE_NAME="${IMAGE_REPO}:${TAG}"
LATEST_NAME="${IMAGE_REPO}:latest"

JOB_NAME="pr-gen-job"
WORKFLOW_NAME="pr-gen-workflow"
WORKFLOW_SA="triaged-issue-ingestion@${PROJECT_ID}.iam.gserviceaccount.com"
EXEC_SA="code-gen-job-execution-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================================="
echo " Starting Production Deployment Pipeline"
echo " Project:   ${PROJECT_ID}"
echo " Region:    ${REGION}"
echo " Image Tag: ${IMAGE_NAME}"
echo " Directory: ${SCRIPT_DIR}"
echo "=========================================================="

# 1. Build and push container image using Cloud Build (Async to avoid VPC-SC streaming restrictions)
echo ""
echo "[1/3] Submitting Cloud Build for container image: ${IMAGE_NAME}"
BUILD_ID=$(gcloud builds submit \
  --tag "${IMAGE_NAME}" \
  --project="${PROJECT_ID}" \
  --async \
  --format="value(ID)")

echo "Cloud Build started with ID: ${BUILD_ID}. Waiting for build completion..."

STATUS="WORKING"
while [[ "${STATUS}" == "WORKING" || "${STATUS}" == "QUEUED" || "${STATUS}" == "PENDING" ]]; do
  sleep 5
  STATUS=$(gcloud builds describe "${BUILD_ID}" --project="${PROJECT_ID}" --format="value(status)")
  echo "  Build status: ${STATUS}"
done

if [[ "${STATUS}" != "SUCCESS" ]]; then
  echo "Error: Cloud Build ${BUILD_ID} failed with status: ${STATUS}" >&2
  exit 1
fi
echo "Cloud Build completed successfully."

# Mirror tag as latest
gcloud container images add-tag "${IMAGE_NAME}" "${LATEST_NAME}" --quiet || true

# 2. Deploy Cloud Run Job revision referencing immutable tag
echo ""
echo "[2/3] Deploying Cloud Run Job: ${JOB_NAME}"
gcloud run jobs deploy "${JOB_NAME}" \
  --image="${IMAGE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --memory=8Gi \
  --cpu=2 \
  --task-timeout=3600 \
  --max-retries=2 \
  --service-account="${EXEC_SA}" \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=global,MODEL_NAME=gemini-3.5-flash,FIRESTORE_DATABASE=gcli-db,FIRESTORE_COLLECTION=issues,PR_GEN_DEBUG_LOGS_BUCKET=pr_generation_debug_logs" \
  --set-secrets="GIT_TOKEN=PR_GEN_GITHUB_PUSH_KEY:latest" \
  --quiet

# 3. Deploy Cloud Workflow definition
echo ""
echo "[3/3] Deploying Cloud Workflow definition: ${WORKFLOW_NAME}"
gcloud workflows deploy "${WORKFLOW_NAME}" \
  --source="workflow.yaml" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --service-account="${WORKFLOW_SA}" \
  --set-env-vars="FIRESTORE_DATABASE=gcli-db,FIRESTORE_COLLECTION=issues" \
  --quiet

echo ""
echo "=========================================================="
echo " Deployment pipeline updated successfully!"
echo " Image Deployed: ${IMAGE_NAME}"
echo "=========================================================="
