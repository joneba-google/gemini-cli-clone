# Copyright 2026 Google LLC
# Apache-2.0 License

"""Firestore Dataset Publisher Script for Evaluation Datasets.

Publishes all local JSON specification documents from `evals/pr-generation/datasets/`:
1. Triage Agent Specs (`triage_agent_specs/`) -> Firestore collection `pr-gen-triage-issues`
2. Ground Truth Golden Specs (`ground_truth_specs/`) -> Firestore collection `pr-gen-golden-issues`

Target Database: `gcli-db` in Google Cloud Project `gcli-intern-project-2026`.
"""

import argparse
import glob
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import firestore

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DatasetPublisher")

HELPERS_DIR = Path(__file__).parent.resolve()
EVAL_DIR = HELPERS_DIR.parent.resolve()
BASE_DIR = EVAL_DIR.parent.resolve()

DATASETS_DIR = EVAL_DIR / "datasets"
TRIAGE_SPECS_DIR = DATASETS_DIR / "triage_agent_specs"
GOLDEN_SPECS_DIR = DATASETS_DIR / "ground_truth_specs"


def resolve_document_id(doc_dict: Dict[str, Any], filepath: Path) -> str:
    """Resolves a deterministic Firestore document ID.

    Format: `github_<owner>_<repo>_<issue_number>`
    Fallback: filename stem without `.json`.
    """
    github_meta = doc_dict.get("github_metadata")
    if isinstance(github_meta, dict):
        owner = str(github_meta.get("owner", "google-gemini")).replace("-", "_")
        repo = str(github_meta.get("repo", "gemini-cli")).replace("-", "_")
        issue_num = github_meta.get("issue_number")
        if issue_num:
            return f"github_{owner}_{repo}_{issue_num}"

    # Fallback to file name stem
    return filepath.stem


def normalize_document_payload(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures document schema compliance before writing to Firestore."""
    payload = dict(doc_dict)

    # Inject required top-level default fields if missing
    if "status" not in payload:
        payload["status"] = "TRIAGED"

    if "lock" not in payload or not isinstance(payload.get("lock"), dict):
        payload["lock"] = {"holder": None, "expires_at": None}

    if "triage_attempts" not in payload:
        payload["triage_attempts"] = 0

    if "generation_attempts" not in payload:
        payload["generation_attempts"] = 0

    now_iso = datetime.now(timezone.utc).isoformat()
    if "created_at" not in payload:
        payload["created_at"] = now_iso

    payload["updated_at"] = now_iso

    return payload


def scan_dataset_directory(base_dir: Path) -> List[Tuple[str, Path, Dict[str, Any]]]:
    """Scans all JSON files recursively within a dataset directory.

    Returns:
        List of tuples: (document_id, file_path, document_dict)
    """
    items = []
    if not base_dir.exists():
        logger.warning("Dataset directory does not exist: %s", base_dir)
        return items

    json_files = sorted(list(base_dir.rglob("*.json")))
    for json_path in json_files:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                doc_dict = json.load(f)

            if not isinstance(doc_dict, dict):
                logger.warning("Skipping non-dict JSON file: %s", json_path)
                continue

            doc_id = resolve_document_id(doc_dict, json_path)
            payload = normalize_document_payload(doc_dict)
            items.append((doc_id, json_path, payload))
        except Exception as e:
            logger.error("Failed to parse JSON file %s: %s", json_path, e)

    return items


def publish_documents(
    db: Optional[firestore.Client],
    collection_name: str,
    items: List[Tuple[str, Path, Dict[str, Any]]],
    dry_run: bool = False,
) -> int:
    """Publishes document items to the specified Firestore collection using batch writes."""
    if not items:
        logger.info("No documents found to publish for collection '%s'.", collection_name)
        return 0

    logger.info(
        "Publishing %d documents to collection '%s' (dry_run=%s)...",
        len(items),
        collection_name,
        dry_run,
    )

    if dry_run:
        for doc_id, filepath, payload in items:
            logger.info("  [DRY RUN] Would write doc '%s' (from %s)", doc_id, filepath.name)
        return len(items)

    if db is None:
        raise ValueError("Firestore client is required when dry_run is False.")

    published_count = 0
    batch = db.batch()
    batch_count = 0

    for doc_id, filepath, payload in items:
        doc_ref = db.collection(collection_name).document(doc_id)
        batch.set(doc_ref, payload, merge=True)
        batch_count += 1
        published_count += 1

        # Commit batch every 400 documents (Firestore limit is 500)
        if batch_count >= 400:
            batch.commit()
            logger.info("Committed batch of %d documents to '%s'.", batch_count, collection_name)
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()
        logger.info("Committed final batch of %d documents to '%s'.", batch_count, collection_name)

    return published_count


def main() -> None:
    """Main CLI entrypoint for publishing datasets to Firestore."""
    parser = argparse.ArgumentParser(
        description="Publish evals/pr-generation/datasets JSON specifications to Firestore collections."
    )
    parser.add_argument(
        "--project",
        type=str,
        default=os.environ.get("GOOGLE_CLOUD_PROJECT", "gcli-intern-project-2026"),
        help="Google Cloud Project ID (default: 'gcli-intern-project-2026')",
    )
    parser.add_argument(
        "--database",
        type=str,
        default=os.environ.get("FIRESTORE_DATABASE", "gcli-db"),
        help="Firestore Database ID (default: 'gcli-db')",
    )
    parser.add_argument(
        "--triage-collection",
        type=str,
        default="pr-gen-triage-issues",
        help="Firestore collection for triage agent issues (default: 'pr-gen-triage-issues')",
    )
    parser.add_argument(
        "--golden-collection",
        type=str,
        default="pr-gen-golden-issues",
        help="Firestore collection for golden issues (default: 'pr-gen-golden-issues')",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform scanning and schema validation without writing to remote Firestore",
    )

    args = parser.parse_args()

    logger.info("==========================================================")
    logger.info(" FIRESTORE EVALUATION DATASET PUBLISHER")
    logger.info("==========================================================")
    logger.info(" Project ID:          %s", args.project)
    logger.info(" Database ID:         %s", args.database)
    logger.info(" Triage Collection:   %s", args.triage_collection)
    logger.info(" Golden Collection:   %s", args.golden_collection)
    logger.info(" Dry Run Mode:        %s", args.dry_run)
    logger.info("==========================================================\n")

    db = None
    if not args.dry_run:
        try:
            db = firestore.Client(project=args.project, database=args.database)
            logger.info("Successfully connected to Firestore database '%s' in project '%s'.", args.database, args.project)
        except Exception as e:
            logger.error("Failed to connect to Firestore: %s", e)
            sys.exit(1)

    # 1. Scan and Publish Triage Agent Specs
    triage_items = scan_dataset_directory(TRIAGE_SPECS_DIR)
    triage_count = publish_documents(db, args.triage_collection, triage_items, dry_run=args.dry_run)

    # 2. Scan and Publish Ground Truth Golden Specs
    golden_items = scan_dataset_directory(GOLDEN_SPECS_DIR)
    golden_count = publish_documents(db, args.golden_collection, golden_items, dry_run=args.dry_run)

    logger.info("\n==========================================================")
    logger.info(" PUBLISH SUMMARY")
    logger.info(" Triage Agent Specs Published: %d to '%s'", triage_count, args.triage_collection)
    logger.info(" Golden Issue Specs Published: %d to '%s'", golden_count, args.golden_collection)
    logger.info(" Total Documents Published:    %d", triage_count + golden_count)
    logger.info("==========================================================")


if __name__ == "__main__":
    main()
