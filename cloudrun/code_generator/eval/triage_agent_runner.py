#!/usr/bin/env python3
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

"""Master Parallel Batch Runner for Triage Agent Spec Generation.

Usage:
    python3 eval/triage_agent_runner.py --issues 19868,21527,22198 [--concurrency 3] [--gcs]
"""

import argparse
import contextlib
import io
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Path resolution
EVAL_DIR = Path(__file__).parent.resolve()
BASE_DIR = EVAL_DIR.parent.resolve()
REF_TRIAGE_DIR = BASE_DIR / "reference_triage"
TRIAGE_WORKER_DIR = (
    BASE_DIR.parent / "triage-worker"
    if (BASE_DIR.parent / "triage-worker").exists()
    else BASE_DIR.parent / "triage_worker"
)

# Load environment variables
load_dotenv(TRIAGE_WORKER_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(REF_TRIAGE_DIR) not in sys.path:
    sys.path.insert(0, str(REF_TRIAGE_DIR))
if str(TRIAGE_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(TRIAGE_WORKER_DIR))

# Dynamic imports
from triage.helpers.github_api import (
    get_issue_details,
    get_pr_details,
    resolve_target_version,
)
from triage.helpers.worktrees import add_worktree, get_repo, remove_worktree
from triage_orchestrator import process_issue_triage

# Target Directories
OUTPUT_BASE_DIR = BASE_DIR / "eval" / "datasets" / "triage_agent_specs"
ISSUES_DIR = OUTPUT_BASE_DIR / "triage_agent_issues"
LOGS_DIR = OUTPUT_BASE_DIR / "logs"

logger = logging.getLogger("TriageAgentRunner")


def parse_args() -> argparse.Namespace:
    """Parses CLI arguments for the batch generator runner."""
    parser = argparse.ArgumentParser(
        description="Batch Triage Agent Spec Generator Runner"
    )
    parser.add_argument(
        "--issues",
        type=str,
        required=True,
        help="Comma-separated list of GitHub issue numbers (e.g. '19868,21527,22198')",
    )
    parser.add_argument(
        "--owner",
        type=str,
        default="google-gemini",
        help="GitHub repository owner (default: google-gemini)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="gemini-cli",
        help="GitHub repository name (default: gemini-cli)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Maximum parallel worker threads (default: 3)",
    )
    parser.add_argument(
        "--gcs",
        action="store_true",
        help="Upload output specs and error logs to GCS (gs://pr-gen-eval-results/triage_agent_specs/)",
    )
    parser.add_argument(
        "--keep-worktrees",
        action="store_true",
        help="Debug flag to preserve worktree directories after execution",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging output from the triage agent and SDK",
    )
    return parser.parse_args()


def get_output_filename(repo: str, issue_number: int) -> str:
    """Generates dynamic output filename based on repo name and issue number."""
    safe_repo = repo.replace("-", "_")
    return f"{safe_repo}_{issue_number}.json"


def resolve_issue_target_version(
    owner: str, repo: str, issue_data: Dict[str, Any], pr_number: Optional[int] = None
) -> Tuple[str, Optional[int]]:
    """Resolves target_version: baseRefOid for closed issues with PRs, origin/main for open issues."""
    state = issue_data.get("state", "").upper()
    resolved_pr_number = pr_number

    # Attempt PR details fetching if closed or pr_number supplied
    pr_data = None
    if resolved_pr_number:
        try:
            pr_data = get_pr_details(owner, repo, resolved_pr_number)
        except Exception as e:
            logger.warning(f"Failed to fetch PR #{resolved_pr_number} details: {e}")

    if state == "OPEN" and not pr_data:
        return "origin/main", resolved_pr_number

    # For closed issues or issues with PRs, resolve via github_api helper
    target_ver = resolve_target_version(owner, repo, issue_data, pr_data)
    return target_ver or "origin/main", resolved_pr_number


def run_single_issue_task(
    issue_number: int,
    worker_id: int,
    owner: str = "google-gemini",
    repo: str = "gemini-cli",
    pr_number: Optional[int] = None,
    keep_worktrees: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Executes spec generation for a single issue in an isolated Git worktree."""
    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    filename = get_output_filename(repo, issue_number)
    output_spec_path = ISSUES_DIR / filename
    error_log_path = LOGS_DIR / f"{repo.replace('-', '_')}_{issue_number}_error.json"

    logger.info(f"[Worker {worker_id}] Starting Issue #{issue_number}")
    start_time = time.time()

    # Step 1: Fetch GitHub Issue Details
    try:
        issue_data = get_issue_details(owner, repo, issue_number)
    except Exception as e:
        err_msg = f"Failed to fetch GitHub issue #{issue_number}: {e}"
        logger.error(f"[Worker {worker_id}] {err_msg}")
        err_record = {
            "issue_number": issue_number,
            "status": "FAILED",
            "error": err_msg,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(error_log_path, "w", encoding="utf-8") as f:
            json.dump(err_record, f, indent=2)
        return {"success": False, "issue_number": issue_number, "error": err_msg}

    title = issue_data.get("title", "")
    body = issue_data.get("body", "")
    target_ver, resolved_pr_num = resolve_issue_target_version(
        owner, repo, issue_data, pr_number
    )

    # Step 2: Prepare Worktree and Run Triage Agent
    worktree_dir = None
    try:
        worktree_dir, actual_version = add_worktree(worker_id, target_ver)
        logger.info(
            f"[Worker {worker_id}] Created worktree for Issue #{issue_number} at {actual_version[:10]}"
        )

        payload = {
            "issue_number": issue_number,
            "title": title,
            "body": body,
            "repository": f"{owner}/{repo}",
        }

        if not verbose:
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    success, raw_output = process_issue_triage(
                        payload, target_cwd=str(worktree_dir)
                    )
                except TypeError:
                    success, raw_output = process_issue_triage(payload)
        else:
            try:
                success, raw_output = process_issue_triage(
                    payload, target_cwd=str(worktree_dir)
                )
            except TypeError:
                success, raw_output = process_issue_triage(payload)

        if not success:
            raise RuntimeError(f"Triage agent execution failed: {raw_output}")

        try:
            agent_result = json.loads(raw_output)
        except Exception:
            agent_result = {"workable_spec": {}, "raw_output": raw_output}

        workable_spec = agent_result.get("workable_spec", {})
        expected_quality = agent_result.get(
            "quality", agent_result.get("expected_quality", "OK")
        )
        expected_effort = agent_result.get(
            "effort", agent_result.get("expected_effort", "MEDIUM")
        )

        # Step 3: Format Golden Spec Document Schema
        spec_doc = {
            "status": "TRIAGED",
            "triage_attempts": 1,
            "generation_attempts": 0,
            "workable_spec": workable_spec,
            "expected_quality": expected_quality,
            "expected_effort": expected_effort,
            "github_metadata": {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "title": title,
                "target_version": actual_version,
                "pr_number": resolved_pr_num or 0,
            },
            "lock": {"holder": None, "expires_at": None},
            "error": "",
        }

        with open(output_spec_path, "w", encoding="utf-8") as f:
            json.dump(spec_doc, f, indent=2)

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            f"[Worker {worker_id}] Successfully generated spec for Issue #{issue_number} ({elapsed}s)"
        )
        return {
            "success": True,
            "issue_number": issue_number,
            "spec_path": str(output_spec_path),
            "execution_time_seconds": elapsed,
        }

    except Exception as e:
        err_msg = str(e)
        logger.error(
            f"[Worker {worker_id}] Error processing Issue #{issue_number}: {err_msg}"
        )
        err_record = {
            "issue_number": issue_number,
            "status": "FAILED",
            "error": err_msg,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(error_log_path, "w", encoding="utf-8") as f:
            json.dump(err_record, f, indent=2)
        return {"success": False, "issue_number": issue_number, "error": err_msg}

    finally:
        # Per-Task Worktree Cleanup
        if not keep_worktrees and worktree_dir:
            try:
                remove_worktree(worker_id)
                logger.info(f"[Worker {worker_id}] Cleaned up worktree slot {worker_id}")
            except Exception as cleanup_err:
                logger.warning(
                    f"[Worker {worker_id}] Worktree cleanup failed: {cleanup_err}"
                )


def sync_triage_specs_to_gcs() -> None:
    """Syncs output specs and error logs to GCS bucket gs://pr-gen-eval-results/triage_agent_specs/."""
    try:
        from google.cloud import storage

        bucket_name = os.environ.get(
            "PR_GEN_EVAL_RESULTS_BUCKET", "pr-generation-eval-results"
        )
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        for folder_name, folder_path in [
            ("triage_agent_issues", ISSUES_DIR),
            ("logs", LOGS_DIR),
        ]:
            if not folder_path.exists():
                continue
            for file_path in folder_path.glob("*.json"):
                blob_path = f"{folder_name}/{file_path.name}"
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(
                    str(file_path), content_type="application/json; charset=utf-8"
                )
                logger.info(f"[GCS SYNC] Uploaded {blob_path} to gs://{bucket_name}/")

    except Exception as e:
        logger.error(f"[GCS SYNC FAILED] {e}")


def setup_logging(verbose: bool = False) -> None:
    """Configures logging for TriageAgentRunner, suppressing verbose sub-agent logs unless verbose=True."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO if verbose else logging.WARNING)

    logger.setLevel(logging.INFO)
    logging.getLogger("CloudTriageRunner").setLevel(logging.INFO)

    if not verbose:
        for name in [
            "root",
            "google",
            "google.antigravity",
            "google.antigravity.hooks.policy",
            "httpx",
            "urllib3",
            "asyncio",
            "triage_orchestrator",
            "agent_logger",
        ]:
            logging.getLogger(name).setLevel(logging.WARNING)


def main() -> None:
    """Main CLI entrypoint for parallel triage agent spec generation."""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    # Parse issue list
    try:
        issue_numbers = [int(i.strip()) for i in args.issues.split(",") if i.strip()]
    except ValueError as e:
        logger.error(f"Invalid --issues list format: {e}")
        sys.exit(1)

    if not issue_numbers:
        logger.error("No valid issue numbers provided.")
        sys.exit(1)

    logger.info("==========================================================")
    logger.info("  Starting Batch Triage Agent Spec Generator Runner")
    logger.info(f"  Target Repo:   {args.owner}/{args.repo}")
    logger.info(f"  Issue Count:   {len(issue_numbers)}")
    logger.info(f"  Concurrency:   {args.concurrency}")
    logger.info(f"  GCS Sync:      {args.gcs}")
    logger.info("==========================================================")

    # Initialize base repository
    get_repo()

    start_time = time.time()
    results = []

    # Map tasks across ThreadPoolExecutor workers (slots 0..concurrency-1)
    def task_wrapper(index_and_issue: Tuple[int, int]) -> Dict[str, Any]:
        idx, issue_num = index_and_issue
        worker_slot = idx % args.concurrency
        return run_single_issue_task(
            issue_number=issue_num,
            worker_id=worker_slot,
            owner=args.owner,
            repo=args.repo,
            keep_worktrees=args.keep_worktrees,
            verbose=args.verbose,
        )

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(task_wrapper, enumerate(issue_numbers)))

    total_time = round(time.time() - start_time, 2)
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    logger.info("==========================================================")
    logger.info(f" Batch Generation Complete ({total_time}s)")
    logger.info(f" Successful: {len(successful)} / {len(issue_numbers)}")
    logger.info(f" Failed:     {len(failed)} / {len(issue_numbers)}")
    logger.info("==========================================================")

    if args.gcs:
        logger.info("Triggering GCS synchronization...")
        sync_triage_specs_to_gcs()


if __name__ == "__main__":
    main()
