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

"""Unit tests for eval.triage_agent_runner module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from eval.helpers.triage_agent_runner import (
    get_output_filename,
    parse_args,
    resolve_issue_target_version,
    run_single_issue_task,
    sync_triage_specs_to_gcs,
)


def test_get_output_filename():
    assert get_output_filename("gemini-cli", 19868) == "gemini_cli_19868.json"
    assert get_output_filename("custom-repo", 123) == "custom_repo_123.json"


def test_parse_args():
    test_args = ["triage_agent_runner.py", "--issues", "19868,21527", "--concurrency", "4"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.issues == "19868,21527"
        assert args.concurrency == 4
        assert args.owner == "google-gemini"
        assert args.repo == "gemini-cli"
        assert args.gcs is False


def test_resolve_issue_target_version_open():
    issue_data = {"state": "OPEN"}
    target_ver, pr_num = resolve_issue_target_version("google-gemini", "gemini-cli", issue_data, None)
    assert target_ver == "origin/main"
    assert pr_num is None


@patch("eval.helpers.triage_agent_runner.resolve_target_version", return_value="sha12345")
def test_resolve_issue_target_version_closed(mock_resolve):
    issue_data = {"state": "CLOSED"}
    target_ver, pr_num = resolve_issue_target_version("google-gemini", "gemini-cli", issue_data, 100)
    assert target_ver == "sha12345"
    assert pr_num == 100
    assert mock_resolve.called


@patch("eval.helpers.triage_agent_runner.get_issue_details")
@patch("eval.helpers.triage_agent_runner.add_worktree")
@patch("eval.helpers.triage_agent_runner.remove_worktree")
@patch("eval.helpers.triage_agent_runner.process_issue_triage")
def test_run_single_issue_task_success(
    mock_triage, mock_remove_wt, mock_add_wt, mock_get_issue, tmp_path
):
    mock_get_issue.return_value = {"title": "EISDIR crash", "body": "Directory error", "state": "OPEN"}
    mock_add_wt.return_value = (tmp_path / "wt_0", "origin/main")
    mock_triage.return_value = (
        True,
        json.dumps({
            "workable_spec": {"summary": {"problem": "EISDIR"}},
            "quality": "OK",
            "effort": "SMALL"
        }),
    )

    issues_dir = tmp_path / "triage_agent_issues"
    logs_dir = tmp_path / "logs"

    with patch("eval.helpers.triage_agent_runner.ISSUES_DIR", issues_dir), \
         patch("eval.helpers.triage_agent_runner.LOGS_DIR", logs_dir):
        result = run_single_issue_task(19868, worker_id=0, owner="google-gemini", repo="gemini-cli")

    assert result["success"] is True
    assert result["issue_number"] == 19868
    mock_remove_wt.assert_called_with(0)

    spec_file = issues_dir / "gemini_cli_19868.json"
    assert spec_file.exists()
    content = json.loads(spec_file.read_text(encoding="utf-8"))
    assert content["status"] == "TRIAGED"
    assert content["expected_quality"] == "OK"
    assert content["expected_effort"] == "SMALL"
    assert content["github_metadata"]["issue_number"] == 19868


@patch("eval.helpers.triage_agent_runner.get_issue_details", side_effect=RuntimeError("GitHub API rate limit"))
def test_run_single_issue_task_fetch_error(mock_get_issue, tmp_path):
    issues_dir = tmp_path / "triage_agent_issues"
    logs_dir = tmp_path / "logs"

    with patch("eval.helpers.triage_agent_runner.ISSUES_DIR", issues_dir), \
         patch("eval.helpers.triage_agent_runner.LOGS_DIR", logs_dir):
        result = run_single_issue_task(21527, worker_id=1, owner="google-gemini", repo="gemini-cli")

    assert result["success"] is False
    assert "GitHub API rate limit" in result["error"]

    err_file = logs_dir / "gemini_cli_21527_error.json"
    assert err_file.exists()
    content = json.loads(err_file.read_text(encoding="utf-8"))
    assert content["status"] == "FAILED"
    assert content["issue_number"] == 21527


@patch("eval.helpers.triage_agent_runner.get_issue_details")
@patch("eval.helpers.triage_agent_runner.add_worktree")
@patch("eval.helpers.triage_agent_runner.remove_worktree")
@patch("eval.helpers.triage_agent_runner.process_issue_triage", side_effect=RuntimeError("LLM error"))
def test_run_single_issue_task_triage_error_and_cleanup(
    mock_triage, mock_remove_wt, mock_add_wt, mock_get_issue, tmp_path
):
    mock_get_issue.return_value = {"title": "Bug", "body": "Body", "state": "OPEN"}
    mock_add_wt.return_value = (tmp_path / "wt_1", "origin/main")

    issues_dir = tmp_path / "triage_agent_issues"
    logs_dir = tmp_path / "logs"

    with patch("eval.helpers.triage_agent_runner.ISSUES_DIR", issues_dir), \
         patch("eval.helpers.triage_agent_runner.LOGS_DIR", logs_dir):
        result = run_single_issue_task(22198, worker_id=1, owner="google-gemini", repo="gemini-cli")

    assert result["success"] is False
    assert "LLM error" in result["error"]
    # Ensures worktree cleanup was executed in finally block
    mock_remove_wt.assert_called_with(1)

    err_file = logs_dir / "gemini_cli_22198_error.json"
    assert err_file.exists()


@patch("google.cloud.storage.Client")
def test_sync_triage_specs_to_gcs(mock_storage_client, tmp_path):
    issues_dir = tmp_path / "triage_agent_issues"
    logs_dir = tmp_path / "logs"
    issues_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    (issues_dir / "gemini_cli_19868.json").write_text("{}", encoding="utf-8")
    (logs_dir / "gemini_cli_21527_error.json").write_text("{}", encoding="utf-8")

    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.return_value.bucket.return_value = mock_bucket

    with patch("eval.helpers.triage_agent_runner.ISSUES_DIR", issues_dir), \
         patch("eval.helpers.triage_agent_runner.LOGS_DIR", logs_dir):
        sync_triage_specs_to_gcs()

    assert mock_storage_client.return_value.bucket.called
    assert mock_bucket.blob.called


@patch("eval.helpers.triage_agent_runner.get_repo")
@patch("eval.helpers.triage_agent_runner.run_single_issue_task")
def test_triage_agent_runner_main_cli(mock_task, mock_get_repo):
    mock_task.return_value = {"success": True, "issue_number": 19868}
    test_args = ["triage_agent_runner.py", "--issues", "19868", "--concurrency", "1"]
    with patch("sys.argv", test_args):
        from eval.helpers.triage_agent_runner import main as runner_main
        runner_main()
    assert mock_get_repo.called
    assert mock_task.called


@patch("eval.cloud_triage_runner.run_triage_batch")
def test_cloud_triage_runner_main(mock_run_batch):
    from eval.cloud_triage_runner import main as cloud_main
    cloud_main()
    assert mock_run_batch.called

