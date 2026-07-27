# Copyright 2026 Google LLC
# Apache-2.0 License

"""Reformatting script for golden_issues/*.json dataset files.

Converts golden_issues JSON files into the standard system ingestion schema:
- status: "TRIAGED"
- workable_spec: { issue_id, summary, implementation_plan, testing_strategy }
- github_metadata: { owner, repo, issue_number, title, target_version, pr_number }
"""

import json
import glob
import os


GOLDEN_ISSUES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "golden_issues")
)


def reformat_file(filepath: str) -> bool:
    """Reformats a single golden_issue JSON file into standard schema."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        owner = data.get("owner", "google-gemini")
        repo = data.get("repo", "gemini-cli")
        issue_number = data.get("issue_number", 0)
        title = data.get("issue_title", "")
        pr_number = data.get("pr_number", 0)
        target_version = data.get("target_version", "")

        workable_spec = data.get("expected_workable_spec", data.get("workable_spec", {}))

        # Ensure issue_id format
        if "issue_id" not in workable_spec:
            workable_spec["issue_id"] = f"{owner}/{repo}#{issue_number}"

        reformatted = {
            "status": "TRIAGED",
            "triage_attempts": 0,
            "generation_attempts": 0,
            "workable_spec": workable_spec,
            "github_metadata": {
                "owner": owner,
                "repo": repo,
                "issue_number": issue_number,
                "title": title,
                "target_version": target_version,
                "pr_number": pr_number,
            },
            "lock": {
                "holder": None,
                "expires_at": None,
            },
            "error": "",
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(reformatted, f, indent=2)

        return True
    except Exception as e:
        print(f"Error reformatting {filepath}: {e}")
        return False


def main():
    json_files = glob.glob(os.path.join(GOLDEN_ISSUES_DIR, "*.json"))
    reformatted_count = 0

    for filepath in sorted(json_files):
        if reformat_file(filepath):
            reformatted_count += 1

    print(f"Reformatted {reformatted_count}/{len(json_files)} golden_issues JSON files to standard ingestion schema.")


if __name__ == "__main__":
    main()
