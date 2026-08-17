"""
Dataset Schema Migration Utility Script.

Converts existing golden issue JSON files in evals/triage/dataset/golden-issues/
from the legacy schema (issue_title, expected_quality, expected_workable_spec)
to the unified production PR Gen schema (title, status, effort, workable_spec, triage_metadata, github_metadata).

CLI Usage:
  python3 -m evals.triage.tools.migrate_dataset_schema
"""

import json
from pathlib import Path

TRIAGE_EVAL_DIR = Path(__file__).resolve().parent.parent
GOLDEN_ISSUES_DIR = TRIAGE_EVAL_DIR / "dataset" / "golden-issues"


def migrate_issue_data(data: dict) -> dict:
    """Migrates a single issue JSON dictionary to the unified PR Gen schema."""
    owner = data.get("owner") or "google-gemini"
    repo = data.get("repo") or "gemini-cli"
    issue_number = data.get("issue_number")
    title = data.get("title") or data.get("issue_title") or ""
    body = data.get("body") or data.get("issue_body") or ""
    
    status = data.get("status") or data.get("expected_quality") or data.get("triage_metadata", {}).get("quality") or "OK"
    effort = data.get("effort") or data.get("expected_effort") or data.get("triage_metadata", {}).get("effort_estimate") or ""
    
    workable_spec = data.get("workable_spec") or data.get("expected_workable_spec") or {}
    golden_spec_rationale = data.get("golden_spec_rationale") or data.get("triage_metadata", {}).get("reasoning") or ""
    
    pr_number = data.get("pr_number") or data.get("github_metadata", {}).get("pr_number") or 0
    target_version = data.get("target_version") or data.get("github_metadata", {}).get("target_version") or ""
    
    triage_metadata = data.get("triage_metadata") or {
        "quality": status,
        "reasoning": golden_spec_rationale,
        "comment": "",
        "effort_estimate": effort,
        "effort_reasoning": ""
    }

    github_metadata = data.get("github_metadata") or {
        "owner": owner,
        "repo": repo,
        "issue_number": issue_number,
        "title": title,
        "target_version": target_version,
        "pr_number": pr_number,
    }

    unified_doc = {
        "owner": owner,
        "repo": repo,
        "issue_number": issue_number,
        "title": title,
        "body": body,
        "status": status,
        "effort": effort,
        "triage_metadata": triage_metadata,
        "workable_spec": workable_spec,
        "github_metadata": github_metadata,
    }

    if "notes" in data:
        unified_doc["notes"] = data["notes"]
    if "golden_spec_rationale" in data:
        unified_doc["golden_spec_rationale"] = data["golden_spec_rationale"]

    return unified_doc


def migrate_all_golden_issues() -> int:
    json_files = sorted([f for f in GOLDEN_ISSUES_DIR.glob("**/*.json") if not f.name.startswith(".")])
    if not json_files:
        print(f"No JSON files found in {GOLDEN_ISSUES_DIR}")
        return 0

    converted_count = 0
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            migrated = migrate_issue_data(raw_data)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(migrated, f, indent=2)

            converted_count += 1
        except Exception as e:
            print(f"❌ Error migrating {file_path.name}: {e}")

    print(f"Successfully migrated {converted_count} golden issue file(s) to unified schema in {GOLDEN_ISSUES_DIR}.")
    return converted_count


if __name__ == "__main__":
    migrate_all_golden_issues()
