# Copyright 2026 Google LLC
# Apache-2.0 License

"""Unit tests for eval/eval_orchestrator.py target_version checkout and evaluation runs."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure evals/pr-generation directory is in sys.path
PR_GEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARETAKER_ROOT = os.path.abspath(os.path.join(PR_GEN_DIR, "..", ".."))
WORKFLOW_DIR = os.path.join(CARETAKER_ROOT, "cloudrun", "pr-generator", "workflow")

for p in (PR_GEN_DIR, CARETAKER_ROOT, WORKFLOW_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from helpers.eval_config import EvalConfig
from helpers.eval_orchestrator import EvalOrchestrator


@pytest.fixture
def mock_eval_config():
    """Returns a mock EvalConfig instance."""
    doc_dict = {
        "workable_spec": {"issue_id": "google-gemini/gemini-cli#25693"},
        "github_metadata": {
            "owner": "google-gemini",
            "repo": "gemini-cli",
            "issue_number": 25693,
            "target_version": "a38e2f00488a08797f4da2f7bcf2e90bfce03a03",
        },
    }
    return EvalConfig(workspace_root="/tmp/test_workspace", firestore_doc_dict=doc_dict)


@patch("helpers.eval_orchestrator.CommandExecutor.run")
def test_sync_or_clone_repository_target_version(mock_cmd_run, mock_eval_config):
    """Tests that _sync_or_clone_repository checks out specified target_version commit SHA."""
    orc = EvalOrchestrator(mock_eval_config)

    with patch("os.path.exists", return_value=True):
        orc._sync_or_clone_repository()

    # Verify git checkout -B eval-agent-issue-25693 a38e2f00488a08797f4da2f7bcf2e90bfce03a03 was invoked
    calls = [str(call) for call in mock_cmd_run.call_args_list]
    assert any("git fetch origin" in call for call in calls)
    assert any("git checkout -B eval-agent-issue-25693 a38e2f00488a08797f4da2f7bcf2e90bfce03a03" in call for call in calls)


@patch("helpers.eval_orchestrator.CommandExecutor.run")
def test_sync_or_clone_repository_main_fallback(mock_cmd_run):
    """Tests falling back to origin/main when target_version is omitted."""
    doc_dict = {
        "workable_spec": {"issue_id": "google-gemini/gemini-cli#25693"},
        "github_metadata": {
            "owner": "google-gemini",
            "repo": "gemini-cli",
            "issue_number": 25693,
        },
    }
    config = EvalConfig(workspace_root="/tmp/test_workspace", firestore_doc_dict=doc_dict)
    orc = EvalOrchestrator(config)

    with patch("os.path.exists", return_value=True):
        orc._sync_or_clone_repository()

    calls = [str(call) for call in mock_cmd_run.call_args_list]
    assert any("git checkout -B eval-agent-issue-25693 origin/main" in call for call in calls)


@patch("helpers.eval_orchestrator.CommandExecutor.run")
def test_sync_or_clone_repository_exclude_file(mock_cmd_run, tmp_path):
    doc_dict = {
        "workable_spec": {"issue_id": "google-gemini/gemini-cli#25693"},
        "github_metadata": {"owner": "google", "repo": "test-repo", "issue_number": 100},
    }
    config = EvalConfig(workspace_root=str(tmp_path / "env"), firestore_doc_dict=doc_dict)
    config.pr_repo_path = str(tmp_path / "repo")
    (tmp_path / "repo" / ".git" / "info").mkdir(parents=True, exist_ok=True)
    orc = EvalOrchestrator(config)
    orc._sync_or_clone_repository()
    exclude_file = tmp_path / "repo" / ".git" / "info" / "exclude"
    assert exclude_file.exists()
    assert "firestore_doc.json" in exclude_file.read_text()
