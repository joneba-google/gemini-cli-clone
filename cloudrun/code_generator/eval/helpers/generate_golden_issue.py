# Copyright 2026 Google LLC
# Apache-2.0 License

"""Golden Issue Generator CLI Tool for Evaluation Datasets.

Generates golden issue JSON files using:
1. Ground-Truth Method (Backwards PR-diff spec synthesis with fairness pruning pass).
   Saved to: eval/datasets/ground_truth_specs/
2. Triage Agent Method (Forward prediction from issue text via triage worker).
   Saved to: eval/datasets/triage_agent_specs/

Filenames are dynamically generated based on repository name:
  {repo.replace('-', '_')}_{issue_number}.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Ensure repository root and reference_triage / triage_worker are in sys.path
HELPERS_DIR = Path(__file__).parent.resolve()
EVAL_DIR = HELPERS_DIR.parent.resolve()
BASE_DIR = EVAL_DIR.parent.resolve()
REF_TRIAGE_DIR = BASE_DIR / "reference_triage"
TRIAGE_WORKER_DIR = BASE_DIR.parent / "triage-worker" if (BASE_DIR.parent / "triage-worker").exists() else BASE_DIR.parent / "triage_worker"

# Load environment variables from triage worker and code generator .env files
load_dotenv(TRIAGE_WORKER_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(REF_TRIAGE_DIR) not in sys.path:
    sys.path.insert(0, str(REF_TRIAGE_DIR))
if str(TRIAGE_WORKER_DIR) not in sys.path:
    sys.path.insert(0, str(TRIAGE_WORKER_DIR))

# Import helpers from reference_triage and triage_worker
from triage.helpers.github_api import (
    get_issue_details,
    get_pr_details,
    resolve_target_version,
)
from triage.helpers.generate_golden_spec import generate_golden_spec
from triage_orchestrator import process_issue_triage

# Ground truth & triage agent output base directories
GROUND_TRUTH_DIR = BASE_DIR / "eval" / "datasets" / "ground_truth_specs"
TRIAGE_AGENT_DIR = BASE_DIR / "eval" / "datasets" / "triage_agent_specs"


def get_output_filename(repo: str, issue_number: int) -> str:
    """Generates dynamic filename based on repository name and issue number."""
    safe_repo = repo.replace("-", "_")
    return f"{safe_repo}_{issue_number}.json"


def generate_ground_truth_issue(
    owner: str,
    repo: str,
    issue_number: int,
    pr_number: Optional[int] = None,
    issue_data: Optional[Dict[str, Any]] = None,
    pr_data: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """Generates ground truth golden issue JSON using backwards PR-diff spec synthesis."""
    out_dir = output_dir or GROUND_TRUTH_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = get_output_filename(repo, issue_number)
    file_path = out_dir / filename

    if issue_data is None:
        if get_issue_details is None:
            raise RuntimeError("get_issue_details helper is not available.")
        print(f"[GROUND_TRUTH] Fetching Issue #{issue_number} details from {owner}/{repo}...")
        issue_data = get_issue_details(owner, repo, issue_number)

    if pr_number and pr_data is None:
        if get_pr_details is None:
            raise RuntimeError("get_pr_details helper is not available.")
        print(f"[GROUND_TRUTH] Fetching PR #{pr_number} details from {owner}/{repo}...")
        pr_data = get_pr_details(owner, repo, pr_number)

    workable_spec: Dict[str, Any] = {}
    golden_spec_rationale = ""

    if pr_number:
        if generate_golden_spec is None:
            raise RuntimeError("generate_golden_spec helper is not available.")
        print(f"[GROUND_TRUTH] Generating Golden Workable Spec for Issue #{issue_number} using PR #{pr_number}...")
        spec_res = generate_golden_spec(owner, repo, issue_number, issue_data, pr_data or {})
        workable_spec = spec_res.get("workable_spec", {})
        golden_spec_rationale = spec_res.get("golden_spec_rationale", "")

    target_ver = (
        resolve_target_version(owner, repo, issue_data, pr_data)
        if resolve_target_version
        else (pr_data.get("baseRefOid") if pr_data else "main")
    )

    template = {
        "status": "TRIAGED",
        "triage_attempts": 0,
        "generation_attempts": 0,
        "workable_spec": workable_spec,
        "github_metadata": {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number,
            "title": issue_data.get("title", ""),
            "target_version": target_ver,
            "pr_number": pr_number or 0,
        },
        "golden_spec_rationale": golden_spec_rationale,
        "lock": {"holder": None, "expires_at": None},
        "error": "",
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    print(f"[GROUND_TRUTH] Saved golden issue file to: {file_path}")
    return file_path


def generate_triage_agent_issue(
    owner: str,
    repo: str,
    issue_number: int,
    pr_number: Optional[int] = None,
    issue_data: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """Generates golden issue JSON using the Triage Agent forward prediction method via triage_agent_runner."""
    import eval.helpers.triage_agent_runner as tar
    out_dir = output_dir or TRIAGE_AGENT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = get_output_filename(repo, issue_number)
    file_path = out_dir / filename

    print(f"[TRIAGE_AGENT] Running Triage Agent Runner on Issue #{issue_number}...")
    orig_issues_dir = tar.ISSUES_DIR
    try:
        tar.ISSUES_DIR = out_dir
        res = tar.run_single_issue_task(
            issue_number=issue_number,
            worker_id=0,
            owner=owner,
            repo=repo,
        )
    finally:
        tar.ISSUES_DIR = orig_issues_dir

    if not res.get("success"):
        raise RuntimeError(f"Triage agent execution failed: {res.get('error')}")

    print(f"[TRIAGE_AGENT] Saved triage agent golden issue file to: {file_path}")
    return file_path


def main() -> None:
    """Main CLI entrypoint for generating golden issues across datasets."""
    parser = argparse.ArgumentParser(
        description="Generate Golden Issue JSON files for evaluation datasets."
    )
    parser.add_argument("--issue", type=int, nargs="+", required=True, help="GitHub Issue number(s)")
    parser.add_argument("--pr", type=int, nargs="*", default=None, help="Associated PR number(s) (optional)")
    parser.add_argument("--owner", type=str, default="google-gemini", help="Repository owner")
    parser.add_argument("--repo", type=str, default="gemini-cli", help="Repository name")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["ground_truth", "triage_agent", "both"],
        default="both",
        help="Generation mode: 'ground_truth', 'triage_agent', or 'both'",
    )

    args = parser.parse_args()

    issues = args.issue
    prs = args.pr or []

    for idx, issue_num in enumerate(issues):
        pr_num = prs[idx] if idx < len(prs) else None
        if args.mode in ["ground_truth", "both"]:
            generate_ground_truth_issue(
                owner=args.owner,
                repo=args.repo,
                issue_number=issue_num,
                pr_number=pr_num,
            )

        if args.mode in ["triage_agent", "both"]:
            generate_triage_agent_issue(
                owner=args.owner,
                repo=args.repo,
                issue_number=issue_num,
                pr_number=pr_num,
            )


if __name__ == "__main__":
    main()
