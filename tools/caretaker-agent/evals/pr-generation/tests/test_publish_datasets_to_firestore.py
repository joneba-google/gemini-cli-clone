# Copyright 2026 Google LLC
# Apache-2.0 License

"""Unit tests for eval/helpers/publish_datasets_to_firestore.py."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure evals/pr-generation and workflow directory are in sys.path
PR_GEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARETAKER_ROOT = os.path.abspath(os.path.join(PR_GEN_DIR, "..", ".."))
WORKFLOW_DIR = os.path.join(CARETAKER_ROOT, "cloudrun", "pr-generator", "workflow")

for p in (PR_GEN_DIR, CARETAKER_ROOT, WORKFLOW_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers.publish_datasets_to_firestore import (
    main,
    normalize_document_payload,
    publish_documents,
    resolve_document_id,
    scan_dataset_directory,
)


def test_resolve_document_id():
    doc_dict = {
        "github_metadata": {
            "owner": "google-gemini",
            "repo": "gemini-cli",
            "issue_number": 19868,
        }
    }
    path = Path("/tmp/gemini_cli_19868.json")
    doc_id = resolve_document_id(doc_dict, path)
    assert doc_id == "github_google_gemini_gemini_cli_19868"


def test_resolve_document_id_fallback():
    doc_dict = {}
    path = Path("/tmp/custom_issue_123.json")
    doc_id = resolve_document_id(doc_dict, path)
    assert doc_id == "custom_issue_123"


def test_normalize_document_payload():
    raw_doc = {"workable_spec": {"problem": "test"}}
    normalized = normalize_document_payload(raw_doc)
    assert normalized["status"] == "TRIAGED"
    assert normalized["lock"] == {"holder": None, "expires_at": None}
    assert normalized["triage_attempts"] == 0
    assert normalized["generation_attempts"] == 0
    assert "created_at" in normalized
    assert "updated_at" in normalized


def test_scan_dataset_directory(tmp_path):
    sub_dir = tmp_path / "specs"
    sub_dir.mkdir(parents=True, exist_ok=True)
    sample_file = sub_dir / "gemini_cli_100.json"
    sample_file.write_text(
        json.dumps({"github_metadata": {"owner": "google", "repo": "test", "issue_number": 100}}),
        encoding="utf-8",
    )

    items = scan_dataset_directory(sub_dir)
    assert len(items) == 1
    doc_id, path, payload = items[0]
    assert doc_id == "github_google_test_100"
    assert payload["status"] == "TRIAGED"


def test_publish_documents_dry_run():
    items = [("doc_1", Path("f.json"), {"status": "TRIAGED"})]
    published = publish_documents(db=None, collection_name="test_col", items=items, dry_run=True)
    assert published == 1


def test_publish_documents_batch_write():
    mock_db = MagicMock()
    mock_batch = MagicMock()
    mock_db.batch.return_value = mock_batch
    mock_doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref

    items = [("doc_1", Path("f.json"), {"status": "TRIAGED"})]
    published = publish_documents(db=mock_db, collection_name="test_col", items=items, dry_run=False)

    assert published == 1
    assert mock_batch.set.called
    assert mock_batch.commit.called


@patch("helpers.publish_datasets_to_firestore.scan_dataset_directory", return_value=[])
def test_main_dry_run(mock_scan):
    with patch("sys.argv", ["publish_datasets_to_firestore.py", "--dry-run"]):
        main()
    assert mock_scan.called
