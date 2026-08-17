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

# DEPRECATED DEPLOYMENT WRAPPER
# This script has been consolidated into the root Caretaker Agent deployment script.
# Delegating to: scripts/deploy.sh --target pr-gen "$@"

echo "=========================================================="
echo " ⚠️  DEPRECATION NOTICE:"
echo " cloudrun/pr-generator/update_deployment.sh has been"
echo " consolidated into the unified deploy script."
echo ""
echo " Delegating execution to:"
echo "   ../../scripts/deploy.sh --target pr-gen $@"
echo "=========================================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

exec "${ROOT_DIR}/scripts/deploy.sh" --target pr-gen "$@"
