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

"""Unit tests for workflow/db/db_interface.py."""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest

from db.db_interface import (
    ClaimAction,
    IssueStatus,
    ReleaseAction,
    acquire_lock,
    create_issue,
    get_firestore_id,
    get_issue,
    mark_needs_human,
    mark_pr_created,
    release_lock,
    update_status,
)


def test_get_firestore_id_precedence(monkeypatch):
    """Tests document ID resolution prioritization."""
    monkeypatch.setenv("FIRESTORE_ID", "env_doc_123")
    assert get_firestore_id() == "env_doc_123"

    # Explicit doc_id takes top priority
    assert get_firestore_id(doc_id="explicit_doc_456") == "explicit_doc_456"

    # Reconstruct from metadata when env is unset
    monkeypatch.delenv("FIRESTORE_ID", raising=False)
    monkeypatch.delenv("firestore_id", raising=False)
    assert (
        get_firestore_id(owner="google", repo="gemini-cli", issue_number=100)
        == "github_google_gemini-cli_100"
    )


def test_get_firestore_id_missing_raises():
    """Tests error when document ID cannot be resolved."""
    with pytest.raises(ValueError):
        get_firestore_id()


@patch("db.db_interface.get_firestore_client")
def test_create_issue_new(mock_get_client):
    """Tests creating a new issue document when snapshot does not exist."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = False
    mock_doc_ref.get.return_value = mock_snapshot

    created = create_issue(
        owner="google",
        repo="gemini-cli",
        issue_number=42,
        title="Test Issue",
        doc_id="github_google_gemini-cli_42",
    )

    assert created is True
    mock_tx.set.assert_called_once()


@patch("db.db_interface.get_firestore_client")
def test_acquire_lock_proceed(mock_get_client):
    """Tests acquiring an available lock on a TRIAGED issue."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": IssueStatus.TRIAGED.value,
        "generation_attempts": 0,
        "lock": {"holder": None, "expires_at": None},
    }
    mock_doc_ref.get.return_value = mock_snapshot

    action = acquire_lock(lock_holder="exec-123", doc_id="test-doc-1")
    assert action == ClaimAction.PROCEED
    mock_tx.update.assert_called_once()


@patch("db.db_interface.get_firestore_client")
def test_acquire_lock_skip_active_holder(mock_get_client):
    """Tests skipping lock acquisition when active lock is held by another worker."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": IssueStatus.COMMIT_GENERATION.value,
        "generation_attempts": 1,
        "lock": {
            "holder": "other-exec-456",
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
        },
    }
    mock_doc_ref.get.return_value = mock_snapshot

    action = acquire_lock(lock_holder="exec-123", doc_id="test-doc-1")
    assert action == ClaimAction.SKIP


@patch("db.db_interface.get_firestore_client")
def test_acquire_lock_needs_human_on_max_attempts(mock_get_client):
    """Tests escalating to NEEDS_HUMAN when attempts limit is reached."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": IssueStatus.TRIAGED.value,
        "generation_attempts": 2,
        "lock": {"holder": None, "expires_at": None},
    }
    mock_doc_ref.get.return_value = mock_snapshot

    action = acquire_lock(lock_holder="exec-123", doc_id="test-doc-1")
    assert action == ClaimAction.NEEDS_HUMAN


@patch("db.db_interface.get_firestore_client")
def test_release_lock_success(mock_get_client):
    """Tests releasing lock after successful PR creation."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": IssueStatus.COMMIT_GENERATION.value,
        "lock": {"holder": "exec-123"},
        "generation_attempts": 1,
    }
    mock_doc_ref.get.return_value = mock_snapshot

    action = mark_pr_created(
        lock_holder="exec-123",
        pr_number="101",
        doc_id="test-doc-1",
    )
    assert action == ReleaseAction.COMPLETE
    mock_tx.update.assert_called_once()


@patch("db.db_interface.get_firestore_client")
def test_mark_needs_human(mock_get_client):
    """Tests mark_needs_human state update and lock release."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_doc_ref = MagicMock()
    mock_client.collection.return_value.document.return_value = mock_doc_ref

    mock_tx = MagicMock()
    mock_client.transaction.return_value = mock_tx

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": IssueStatus.COMMIT_GENERATION.value,
        "lock": {"holder": "exec-123"},
        "generation_attempts": 1,
    }
    mock_doc_ref.get.return_value = mock_snapshot

    action = mark_needs_human(
        lock_holder="exec-123",
        reason="Line count limit exceeded",
        doc_id="test-doc-1",
    )
    assert action in (ReleaseAction.COMPLETE, ReleaseAction.RETRY)
    mock_tx.update.assert_called_once()
