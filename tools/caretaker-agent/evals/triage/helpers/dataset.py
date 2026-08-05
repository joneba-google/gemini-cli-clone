"""Firestore & Local Golden Dataset Streaming"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

load_dotenv()

TRIAGE_EVAL_DIR = Path(__file__).resolve().parent.parent
GOLDEN_ISSUES_DIR = TRIAGE_EVAL_DIR / "dataset" / "golden-issues"


def get_env_var(name: str) -> str:
    """Helper that loads an environment variable and fails fast if missing."""
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"Missing required environment variable '{name}'. "
            f"Please ensure your .env file or environment is properly configured."
        )
    return val


def load_local_golden_issues(
    filter_issues: Optional[Union[List[int], str]] = None
) -> List[Dict[str, Any]]:
    """Loads golden issue test cases directly from local JSON files in dataset/golden-issues/."""
    if not GOLDEN_ISSUES_DIR.exists():
        print(f"⚠️ Warning: Local golden issues directory '{GOLDEN_ISSUES_DIR}' does not exist.")
        return []

    json_files = sorted(
        [f for f in GOLDEN_ISSUES_DIR.glob("**/*.json") if not f.name.startswith(".")]
    )
    issues = []

    is_all = (
        filter_issues == "all"
        or (isinstance(filter_issues, str) and filter_issues.lower() == "all")
    )
    target_filter_set = set(filter_issues) if isinstance(filter_issues, list) else None

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            issue_num = data.get("issue_number")
            if issue_num is None:
                continue

            issue_num_int = int(issue_num)
            data["issue_number"] = issue_num_int

            if not is_all and target_filter_set is not None:
                if issue_num_int not in target_filter_set:
                    continue

            issues.append(data)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load local golden issue JSON '{file_path}': {e}")

    issues.sort(key=lambda x: x["issue_number"])
    return issues


def load_issues(
    filter_issues: Optional[Union[List[int], str]] = None
) -> List[Dict[str, Any]]:
    """Loads golden issue test cases from Firestore if available, falling back to local JSON dataset."""
    project_id = os.environ.get("PROJECT_ID")
    db_id = os.environ.get("FIRESTORE_DATABASE")
    collection_name = os.environ.get("FIRESTORE_EVAL_COLLECTION")

    if project_id and db_id and collection_name:
        try:
            from google.cloud import firestore

            db = firestore.Client(project=project_id, database=db_id)
            docs = db.collection(collection_name).stream()

            issues = []
            is_all = (
                filter_issues == "all"
                or (isinstance(filter_issues, str) and filter_issues.lower() == "all")
            )
            target_filter_set = set(filter_issues) if isinstance(filter_issues, list) else None

            for doc in docs:
                data = doc.to_dict()
                issue_num = data.get("issue_number")
                if issue_num is None:
                    continue
                issue_num_int = int(issue_num)
                data["issue_number"] = issue_num_int

                if not is_all and target_filter_set is not None:
                    if issue_num_int not in target_filter_set:
                        continue

                issues.append(data)

            issues.sort(key=lambda x: x["issue_number"])
            if issues:
                return issues
        except Exception as e:
            print(f"ℹ️ Firestore load unavailable or failed ({e}); falling back to local JSON dataset.")

    return load_local_golden_issues(filter_issues)


def prep_payload(item: Dict[str, Any]) -> Dict[str, Any]:
    """Preprocesses and wraps title & body to simulate production Ingestion Layer safety encapsulation."""
    raw_body = item.get("issue_body") or item.get("body") or ""
    escaped_body = raw_body.replace("</untrusted_context>", "\\</untrusted_context>")
    sanitized_body = f"<untrusted_context>\n{escaped_body}\n</untrusted_context>"

    raw_title = item.get("issue_title") or item.get("title") or ""
    escaped_title = raw_title.replace("</untrusted_context>", "\\</untrusted_context>")
    sanitized_title = f"<untrusted_context>\n{escaped_title}\n</untrusted_context>"

    return {
        "issue_number": item.get("issue_number"),
        "title": sanitized_title,
        "body": sanitized_body,
        "repository": f"{item.get('owner', 'google-gemini')}/{item.get('repo', 'gemini-cli')}"
    }

