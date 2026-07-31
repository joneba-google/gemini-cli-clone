# Copyright 2026 Google LLC
# Apache-2.0 License

"""Unit tests for eval/generate_golden_issue.py."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Ensure eval directory is in sys.path
EVAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval"))
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)

from eval.helpers.generate_golden_issue import (
    generate_ground_truth_issue,
    generate_triage_agent_issue,
    get_output_filename,
    main,
)


def test_get_output_filename():
    """Tests dynamic output filename generation based on repository name."""
    assert get_output_filename("gemini-cli", 17733) == "gemini_cli_17733.json"
    assert get_output_filename("custom-repo", 456) == "custom_repo_456.json"
    assert get_output_filename("my_repo_name", 789) == "my_repo_name_789.json"


def test_generate_ground_truth_issue(tmp_path):
    """Tests generating ground truth golden issue JSON file."""
    issue_data = {
        "title": "Bug in config loader",
        "body": "Detailed description of bug",
        "createdAt": "2026-01-28T03:35:15Z",
    }
    pr_data = {
        "baseRefOid": "abcd1234efgh5678",
        "diff": "diff --git a/config.ts b/config.ts\n+fix",
    }

    mock_spec_res = {
        "workable_spec": {
            "summary": {"problem": "Config bug", "root_cause": "Typo", "context": "Loader"},
            "implementation_plan": {"files_to_modify": ["config.ts"], "steps": ["Fix typo"]},
            "testing_strategy": {"test_file": "config.test.ts", "framework": "Vitest"},
        },
        "golden_spec_rationale": "Pruned lockfiles and docs.",
    }

    with patch("eval.helpers.generate_golden_issue.generate_golden_spec", return_value=mock_spec_res):
        out_file = generate_ground_truth_issue(
            owner="google-gemini",
            repo="gemini-cli",
            issue_number=17733,
            pr_number=17734,
            issue_data=issue_data,
            pr_data=pr_data,
            output_dir=tmp_path,
        )

    assert out_file.exists()
    assert out_file.name == "gemini_cli_17733.json"

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["status"] == "TRIAGED"
    assert data["github_metadata"]["owner"] == "google-gemini"
    assert data["github_metadata"]["repo"] == "gemini-cli"
    assert data["github_metadata"]["issue_number"] == 17733
    assert data["github_metadata"]["pr_number"] == 17734
    assert data["github_metadata"]["target_version"] == "abcd1234efgh5678"
    assert data["workable_spec"]["summary"]["problem"] == "Config bug"
    assert data["golden_spec_rationale"] == "Pruned lockfiles and docs."


def test_generate_triage_agent_issue_custom_repo(tmp_path):
    """Tests generating triage agent issue JSON file with custom repository name via triage_agent_runner."""
    def mock_run_single_issue(issue_number, worker_id, owner, repo):
        out_file = tmp_path / f"{repo.replace('-', '_')}_{issue_number}.json"
        out_file.write_text(
            json.dumps({
                "status": "TRIAGED",
                "triage_attempts": 1,
                "expected_quality": "OK",
                "expected_effort": "SMALL",
                "github_metadata": {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": issue_number,
                    "pr_number": 1000,
                },
                "workable_spec": {"summary": {"problem": "Custom issue"}},
            }),
            encoding="utf-8",
        )
        return {"success": True, "issue_number": issue_number, "spec_path": str(out_file)}

    with patch("eval.helpers.triage_agent_runner.run_single_issue_task", side_effect=mock_run_single_issue):
        out_file = generate_triage_agent_issue(
            owner="my-org",
            repo="custom-agent-repo",
            issue_number=999,
            pr_number=1000,
            output_dir=tmp_path,
        )

    assert out_file.exists()
    assert out_file.name == "custom_agent_repo_999.json"

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["status"] == "TRIAGED"
    assert data["triage_attempts"] == 1
    assert data["expected_quality"] == "OK"
    assert data["expected_effort"] == "SMALL"
    assert data["github_metadata"]["owner"] == "my-org"
    assert data["github_metadata"]["repo"] == "custom-agent-repo"
    assert data["github_metadata"]["issue_number"] == 999
    assert data["github_metadata"]["pr_number"] == 1000
    assert data["workable_spec"]["summary"]["problem"] == "Custom issue"


def test_main_cli_dispatch(tmp_path):
    """Tests CLI main function dispatching to both generation methods."""
    with patch("eval.helpers.generate_golden_issue.generate_ground_truth_issue") as mock_gt:
        with patch("eval.helpers.generate_golden_issue.generate_triage_agent_issue") as mock_ta:
            test_args = [
                "generate_golden_issue.py",
                "--issue", "17733",
                "--pr", "17734",
                "--owner", "google-gemini",
                "--repo", "gemini-cli",
                "--mode", "both",
            ]
            with patch("sys.argv", test_args):
                main()

            mock_gt.assert_called_once_with(
                owner="google-gemini",
                repo="gemini-cli",
                issue_number=17733,
                pr_number=17734,
            )
            mock_ta.assert_called_once_with(
                owner="google-gemini",
                repo="gemini-cli",
                issue_number=17733,
                pr_number=17734,
            )


def test_main_cli_dispatch_multiple_issues(tmp_path):
    """Tests CLI main function dispatching multiple issue and PR numbers."""
    with patch("eval.helpers.generate_golden_issue.generate_ground_truth_issue") as mock_gt:
        with patch("eval.helpers.generate_golden_issue.generate_triage_agent_issue") as mock_ta:
            test_args = [
                "generate_golden_issue.py",
                "--issue", "2407", "24501",
                "--pr", "28304", "24502",
                "--mode", "triage_agent",
            ]
            with patch("sys.argv", test_args):
                main()

            assert mock_gt.call_count == 0
            assert mock_ta.call_count == 2
            mock_ta.assert_any_call(
                owner="google-gemini",
                repo="gemini-cli",
                issue_number=2407,
                pr_number=28304,
            )
            mock_ta.assert_any_call(
                owner="google-gemini",
                repo="gemini-cli",
                issue_number=24501,
                pr_number=24502,
            )
