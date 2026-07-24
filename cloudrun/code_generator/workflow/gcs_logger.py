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

"""GCS Logging and Artifact Preservation Utility.

Uploads agent execution trajectory logs, git diff patches, and PR details to
the designated Google Cloud Storage (GCS) debug bucket: pr_generation_debug_logs.
"""

import datetime
import json
import logging
import os
from typing import Any

try:
    from google.cloud import storage
except ImportError:
    storage = None


BUCKET_NAME = os.environ.get("PR_GEN_DEBUG_LOGS_BUCKET", "pr_generation_debug_logs")


def _get_utc_timestamp() -> str:
    """Returns current UTC timestamp formatted as YYYYMMDD_HHMMSS."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")


def _parse_repo_slug(
    owner: str | None, repo: str | None, repo_url: str | None = None
) -> tuple[str, str]:
    """Parses repo author and repo name from metadata or repository URL."""
    if owner and repo:
        return owner, repo
    if repo_url:
        clean_url = repo_url.rstrip("/").replace(".git", "")
        parts = clean_url.split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
    return "unknown_owner", "unknown_repo"


def upload_to_bucket(
    blob_path: str, payload: str, content_type: str = "text/plain"
) -> bool:
    """Uploads a string payload directly to the designated GCS bucket.

    Args:
        blob_path: Relative key path inside the GCS bucket.
        payload: String data content to upload.
        content_type: MIME content type string.

    Returns:
        True if successfully uploaded, False otherwise.
    """
    if not BUCKET_NAME:
        logging.info(
            "[GCS Logger] PR_GEN_DEBUG_LOGS_BUCKET not set. Skipping GCS upload."
        )
        return False

    if storage is None:
        logging.warning(
            "[GCS Logger] google.cloud.storage is not available. Skipping GCS upload."
        )
        return False

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)
        blob.upload_from_string(payload, content_type=content_type)
        logging.info(
            "[GCS Logger] Uploaded artifact to gs://%s/%s", BUCKET_NAME, blob_path
        )
        return True
    except Exception as e:
        logging.warning(
            "[GCS Logger] Failed to upload artifact to GCS (gs://%s/%s): %s",
            BUCKET_NAME,
            blob_path,
            e,
        )
        return False


def serialize_chunks(resolved_chunks: list[Any]) -> str:
    """Serializes Antigravity SDK stream chunks into standardized JSON string."""
    serializable = []
    for chunk in resolved_chunks:
        try:
            dumped = chunk.model_dump()
        except AttributeError:
            try:
                dumped = chunk.dict()
            except AttributeError:
                dumped = {"raw": str(chunk)}
        dumped["chunk_type"] = chunk.__class__.__name__
        serializable.append(dumped)

    return json.dumps(serializable, indent=2, default=str)


def upload_agent_trajectory_log(
    owner: str,
    repo: str,
    agent_role_folder: str,  # 'coding_agent' or 'eval_agent'
    issue_number: str | int,
    resolved_chunks: list[Any],
    timestamp: str | None = None,
) -> str | None:
    """Serializes and uploads agent trajectory debug log to GCS."""
    if not resolved_chunks:
        return None

    ts = timestamp or _get_utc_timestamp()
    blob_path = f"{owner}_{repo}/{agent_role_folder}/issue_{issue_number}_{ts}_debug.log"
    payload = serialize_chunks(resolved_chunks)
    if upload_to_bucket(blob_path, payload, content_type="application/json"):
        return blob_path
    return None


def upload_git_diff(
    owner: str,
    repo: str,
    issue_number: str | int,
    diff_content: str,
    timestamp: str | None = None,
) -> str | None:
    """Uploads generated git diff patch artifact to GCS."""
    if not diff_content:
        return None

    ts = timestamp or _get_utc_timestamp()
    blob_path = f"{owner}_{repo}/git_diffs/issue_{issue_number}_{ts}_diff.diff"
    if upload_to_bucket(blob_path, diff_content, content_type="text/plain"):
        return blob_path
    return None


def upload_pr_details(
    owner: str,
    repo: str,
    issue_number: str | int,
    pr_details_content: str,
    timestamp: str | None = None,
) -> str | None:
    """Uploads generated PR details markdown documentation artifact to GCS."""
    if not pr_details_content:
        return None

    ts = timestamp or _get_utc_timestamp()
    blob_path = f"{owner}_{repo}/pr_details/issue_{issue_number}_{ts}_pr_details.md"
    if upload_to_bucket(blob_path, pr_details_content, content_type="text/markdown"):
        return blob_path
    return None
