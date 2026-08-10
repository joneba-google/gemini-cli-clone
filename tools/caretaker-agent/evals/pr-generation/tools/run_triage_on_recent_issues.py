"""
CLI Tool to run the Gemini CLI Triage Agent on the most recent N GitHub issues.

CLI Usage:
    cloudrun/pr-generator/.venv/bin/python evals/pr-generation/tools/run_triage_on_recent_issues.py --run-name 100_test --count 100 --concurrency 10
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

# Setup sys.path to ensure evals and cloudrun/triage-worker are importable
PR_GEN_TOOLS_DIR = Path(__file__).resolve().parent
PR_GEN_DIR = PR_GEN_TOOLS_DIR.parent
EVALS_DIR = PR_GEN_DIR.parent
CARETAKER_ROOT = EVALS_DIR.parent
TRIAGE_WORKER_DIR = CARETAKER_ROOT / "cloudrun" / "triage-worker"

for p in (str(CARETAKER_ROOT), str(EVALS_DIR), str(TRIAGE_WORKER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from evals.triage.helpers.github_api import _get_github_headers
from evals.triage.runner import run_suite


def fetch_recent_open_issue_numbers(owner: str, repo: str, count: int = 100) -> list[int]:
    """Fetches the N most recent open issue numbers (excluding pull requests) from GitHub API."""
    open_issues = []
    page = 1
    print(f"Fetching recent {count} open issues from {owner}/{repo} via GitHub API...")
    headers = _get_github_headers()
    while len(open_issues) < count and page <= 15:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=open&per_page=100&page={page}&sort=created&direction=desc"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data:
                    break
                for item in data:
                    if "pull_request" not in item:
                        open_issues.append(int(item["number"]))
                        if len(open_issues) >= count:
                            break
                page += 1
        except Exception as e:
            print(f"Error fetching GitHub API page {page}: {e}")
            break
    print(f"Successfully fetched {len(open_issues)} open issue IDs.")
    return open_issues


def main():
    parser = argparse.ArgumentParser(
        description="Fetch recent open issues and run them through the Triage Agent LLM worker."
    )
    parser.add_argument("--run-name", type=str, required=True, help="Target run directory name (e.g. '100_test')")
    parser.add_argument("--count", type=int, default=100, help="Number of recent open issues to process (default: 100)")
    parser.add_argument("--concurrency", type=int, default=10, help="Parallel triage worker threads (default: 10)")
    parser.add_argument("--owner", type=str, default="google-gemini", help="Repository owner")
    parser.add_argument("--repo", type=str, default="gemini-cli", help="Repository name")

    args = parser.parse_args()

    issues = fetch_recent_open_issue_numbers(args.owner, args.repo, args.count)
    if not issues:
        print("Error: No open issues fetched.")
        sys.exit(1)

    print(f"\n==========================================================")
    print(f" Running Triage Agent on {len(issues)} Recent Open Issues")
    print(f" Run Name:    {args.run_name}")
    print(f" Concurrency: {args.concurrency}")
    print(f"==========================================================\n")

    # Run Triage Agent runner in --no-judge mode
    run_suite(
        filter_issues=issues,
        concurrency=args.concurrency,
        judge=False,
        run_name=args.run_name,
    )

    triage_output_dir = EVALS_DIR / "triage" / "dataset" / args.run_name
    pr_gen_spec_dir = PR_GEN_DIR / "datasets" / "triage_agent_specs" / args.run_name

    # Also copy generated specs to pr-generation/datasets/triage_agent_specs/<run_name>/ for convenience
    if triage_output_dir.exists():
        pr_gen_spec_dir.mkdir(parents=True, exist_ok=True)
        for json_file in triage_output_dir.glob("*.json"):
            shutil.copy2(json_file, pr_gen_spec_dir / json_file.name)
        print(f"Copied specs to pr-generation dataset folder: {pr_gen_spec_dir}")

    print(f"\n==========================================================")
    print(f" Triage Agent Execution Complete")
    print(f" Output Datasets:")
    print(f"   1. {triage_output_dir}")
    print(f"   2. {pr_gen_spec_dir}")
    print(f"==========================================================\n")


if __name__ == "__main__":
    main()
