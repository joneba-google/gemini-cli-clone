"""
Golden Issue Generator CLI Tool (Main Entrypoint).

CLI usage:
  python3 -m evals.triage.tools.generate_golden_issue --issue <number...> [--pr <number...>] [--max-workers <n>]
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

from evals.triage.helpers.github_api import (
    get_issue_details,
    get_pr_details,
    resolve_target_version
)
from evals.triage.helpers.generate_golden_spec import generate_golden_spec

OUTPUT_DIR = Path(__file__).parent.parent / "dataset" / "golden-issues"


def generate_golden_issue(
    owner: str,
    repo: str,
    issue_number: int,
    pr_number: Optional[int] = None,
    output_dir: Optional[str] = None,
    pr_gen: bool = False
) -> Path:
    """Main orchestrator for generating a single Golden Issue JSON file."""
    print(f"Fetching Issue #{issue_number} details from {owner}/{repo}...")
    issue_data = get_issue_details(owner, repo, issue_number)
    
    pr_data = {}
    if pr_number:
        print(f"Fetching PR #{pr_number} details from {owner}/{repo}...")
        pr_data = get_pr_details(owner, repo, pr_number)

    workable_spec = {}
    golden_spec_rationale = ""

    if pr_number:
        print(f"[EVAL] Generating Golden Workable Spec for Issue #{issue_number} using PR #{pr_number}...")
        spec_res = generate_golden_spec(owner, repo, issue_number, issue_data, pr_data)
        workable_spec = spec_res["workable_spec"]
        golden_spec_rationale = spec_res["golden_spec_rationale"]

    # Extract effort from labels if present
    labels = [l.get("name", "").lower() for l in issue_data.get("labels", []) if isinstance(l, dict)]
    effort_from_labels = ""
    for effort in ["small", "medium", "large"]:
        if f"effort/{effort}" in labels:
            effort_from_labels = effort.upper()
            break

    # Default quality to 'OK' if a PR is attached, otherwise empty string ''
    expected_quality_default = "OK" if pr_number else ""
    target_ver = resolve_target_version(owner, repo, issue_data, pr_data)

    if pr_gen:
        template = {
            "status": "TRIAGED" if workable_spec else "UNTRIAGED",
            "triage_attempts": 1 if workable_spec else 0,
            "generation_attempts": 0,
            "workable_spec": workable_spec,
            "expected_quality": expected_quality_default,
            "expected_effort": effort_from_labels or "SMALL",
            "github_metadata": {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "title": issue_data.get("title", ""),
                "target_version": target_ver,
                "pr_number": pr_number or 0,
            },
            "notes": f"Created at {issue_data.get('createdAt', '')} by automated generate_golden_issue.py",
            "golden_spec_rationale": golden_spec_rationale,
            "lock": {
                "holder": None,
                "expires_at": None,
            },
            "error": "",
        }
    else:
        template = {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number,
            "issue_title": issue_data.get("title", ""),
            "issue_body": issue_data.get("body", ""),
            "pr_number": pr_number or 0,
            "target_version": target_ver,
            "expected_quality": expected_quality_default,
            "expected_effort": effort_from_labels,
            "notes": f"Created at {issue_data.get('createdAt', '')} by automated generate_golden_issue.py",
            "golden_spec_rationale": golden_spec_rationale,
            "expected_workable_spec": workable_spec,
        }

    target_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"gemini_cli_{issue_number}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    print(f"Successfully saved golden issue file to: {file_path}")
    return file_path


def batch_generate_golden_issues(
    owner: str,
    repo: str,
    issue_pr_pairs: List[Tuple[int, Optional[int]]],
    output_dir: Optional[str] = None,
    pr_gen: bool = False,
    max_workers: int = 4
):
    """Concurrently generates golden issue JSON files for multiple (issue, pr) pairs."""
    if len(issue_pr_pairs) == 1:
        issue, pr = issue_pr_pairs[0]
        generate_golden_issue(owner, repo, issue, pr, output_dir=output_dir, pr_gen=pr_gen)
        return

    print(f"\n==========================================================")
    print(f" Starting Concurrent Golden Issue Generation ({len(issue_pr_pairs)} items)")
    print(f" Target Repository: {owner}/{repo}")
    print(f" Max Workers:       {max_workers}")
    print(f"==========================================================\n")

    def _worker(pair: Tuple[int, Optional[int]]) -> Tuple[int, Optional[int], bool, Optional[str]]:
        issue, pr = pair
        try:
            generate_golden_issue(owner, repo, issue, pr, output_dir=output_dir, pr_gen=pr_gen)
            return (issue, pr, True, None)
        except Exception as e:
            print(f"❌ Error generating golden issue #{issue} (PR #{pr}): {e}")
            return (issue, pr, False, str(e))

    success_count = 0
    failure_count = 0

    with ThreadPoolExecutor(max_workers=min(max_workers, len(issue_pr_pairs))) as executor:
        futures = [executor.submit(_worker, pair) for pair in issue_pr_pairs]
        for future in as_completed(futures):
            issue, pr, success, err = future.result()
            if success:
                success_count += 1
            else:
                failure_count += 1

    print(f"\n==========================================================")
    print(f" Batch Golden Issue Generation Complete")
    print(f" Total Issues: {len(issue_pr_pairs)} | Success: {success_count} | Failed: {failure_count}")
    print(f"==========================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Generate Golden Issue JSON file(s) concurrently.")
    parser.add_argument("--issue", "--issues", type=int, nargs="+", required=True, help="GitHub Issue number(s)")
    parser.add_argument("--pr", "--prs", type=int, nargs="+", default=None, help="Associated PR number(s) (optional)")
    parser.add_argument("--owner", type=str, default="google-gemini", help="Repository owner")
    parser.add_argument("--repo", type=str, default="gemini-cli", help="Repository name")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory path for generated JSON specs")
    parser.add_argument("--pr-gen", action="store_true", default=False, help="Format JSON spec for pr_gen evaluation suite ingestion")
    parser.add_argument("--max-workers", type=int, default=4, help="Max concurrent worker threads")

    args = parser.parse_args()

    issues = args.issue
    prs = args.pr or []

    # Match issue and PR arguments by position
    pairs = []
    for idx, issue in enumerate(issues):
        pr = prs[idx] if idx < len(prs) else None
        pairs.append((issue, pr))

    batch_generate_golden_issues(
        owner=args.owner,
        repo=args.repo,
        issue_pr_pairs=pairs,
        output_dir=args.output_dir,
        pr_gen=args.pr_gen,
        max_workers=args.max_workers
    )


if __name__ == "__main__":
    main()
