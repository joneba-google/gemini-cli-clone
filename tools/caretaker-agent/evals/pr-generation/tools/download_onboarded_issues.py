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

"""
CLI Tool to download onboarded issue JSON files from GCS bucket.

GCS Path: gs://triage-eval-results/onboarded_issues/
Excludes: summary.json

Default Output Directory:
    evals/pr-generation/datasets/triage_agent_specs/onboarded_issues/

Usage:
    cloudrun/pr-generator/.venv/bin/python evals/pr-generation/tools/download_onboarded_issues.py
"""

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PR_GEN_TOOLS_DIR = Path(__file__).resolve().parent
PR_GEN_DIR = PR_GEN_TOOLS_DIR.parent
DEFAULT_OUTPUT_DIR = PR_GEN_DIR / "datasets" / "triage_agent_specs" / "onboarded_issues"


def download_blob(gcs_uri: str, target_file: Path) -> tuple[str, bool, str]:
    """Downloads a single GCS blob to target_file using gcloud storage."""
    try:
        cmd = ["gcloud", "storage", "cp", gcs_uri, str(target_file)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return gcs_uri, True, ""
        else:
            return gcs_uri, False, res.stderr.strip()
    except Exception as e:
        return gcs_uri, False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Download onboarded issue JSON files from gs://triage-eval-results/onboarded_issues/."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Local directory where downloaded JSON files will be saved (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--bucket-uri",
        type=str,
        default="gs://triage-eval-results/onboarded_issues/",
        help="GCS URI to list and download from.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=16,
        help="Max parallel worker threads for downloading.",
    )

    args = parser.parse_args()

    output_path = Path(args.output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Listing blobs from {args.bucket_uri}...")
    ls_cmd = ["gcloud", "storage", "ls", args.bucket_uri]
    ls_res = subprocess.run(ls_cmd, capture_output=True, text=True)

    if ls_res.returncode != 0:
        print(f"❌ Error listing GCS bucket: {ls_res.stderr.strip()}")
        sys.exit(1)

    lines = [line.strip() for line in ls_res.stdout.splitlines() if line.strip()]

    # Filter out summary.json and non-json files
    target_blobs = [
        line for line in lines
        if line.startswith("gs://") and not line.endswith("summary.json") and line.endswith(".json")
    ]

    print(f"Found {len(target_blobs)} issue blobs to download (excluded summary.json).")
    if not target_blobs:
        print("No issue blobs found to download.")
        return

    print(f"Downloading to: {output_path} (Parallel Workers: {args.max_workers})...\n")

    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_blob = {}
        for gcs_uri in target_blobs:
            filename = Path(gcs_uri).name
            target_file = output_path / filename
            future = executor.submit(download_blob, gcs_uri, target_file)
            future_to_blob[future] = gcs_uri

        for future in as_completed(future_to_blob):
            gcs_uri, success, err_msg = future.result()
            filename = Path(gcs_uri).name
            if success:
                success_count += 1
            else:
                fail_count += 1
                print(f"❌ Failed to download {filename}: {err_msg}")

    print(f"\n==========================================================")
    print(f" Download Complete!")
    print(f" Directory: {output_path}")
    print(f" Success:   {success_count} / {len(target_blobs)}")
    print(f" Failed:    {fail_count} / {len(target_blobs)}")
    print(f"==========================================================\n")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
