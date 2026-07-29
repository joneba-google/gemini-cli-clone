# Copyright 2026 Google LLC
# Apache-2.0 License

"""Unit tests for eval/eval_diff_judge.py and judge prompt evaluation."""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure eval directory is in sys.path
EVAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval"))
if EVAL_DIR not in sys.path:
    sys.path.insert(0, EVAL_DIR)

from eval_diff_judge import (
    evaluate_single_diff,
    fetch_true_diff,
    find_golden_spec_for_test,
    load_judge_prompt_template,
    main,
)


def test_load_judge_prompt_template():
    """Tests loading the markdown judge prompt template."""
    prompt = load_judge_prompt_template()
    assert "Scoring Rubric" in prompt
    assert "{{PROPOSED_DIFF}}" in prompt
    assert "{{TRUE_DIFF}}" in prompt


@patch("urllib.request.urlopen")
def test_fetch_true_diff_success(mock_urlopen):
    """Tests fetching PR diff from GitHub."""
    mock_response = MagicMock()
    mock_response.read.return_value = b"diff --git a/file.py b/file.py\n+new line"
    mock_urlopen.return_value.__enter__.return_value = mock_response

    diff = fetch_true_diff("google-gemini", "gemini-cli", 25728)
    assert "diff --git" in diff


def test_find_golden_spec_for_test():
    """Tests locating matching golden issue spec by test_id."""
    input_path = os.path.join(os.path.dirname(__file__), "..", "eval_datasets", "golden_issues")
    doc = find_golden_spec_for_test("gemini_cli_25693_25693", input_path)
    assert doc is not None
    assert doc.get("status") == "TRIAGED"
    assert doc.get("github_metadata", {}).get("issue_number") == 25693


@pytest.mark.asyncio
@patch("eval_diff_judge.fetch_true_diff", return_value="diff --git a/src/skill.ts b/src/skill.ts\n+fix")
@patch("eval_diff_judge.AgentRunner")
async def test_evaluate_single_diff_score_3(mock_agent_runner_cls, mock_fetch_diff):
    """Tests evaluating a single diff that receives score 3."""
    mock_agent_runner = MagicMock()
    mock_agent_runner.run_agent = AsyncMock(
        return_value=(
            json.dumps({
                "score": 3,
                "verdict_description": "The proposed diff is identical in functionality to the true fix.",
            }),
            [],
        )
    )
    mock_agent_runner_cls.return_value = mock_agent_runner

    doc_dict = {
        "workable_spec": {"issue_id": "google-gemini/gemini-cli#25693", "summary": {}},
        "github_metadata": {"owner": "google-gemini", "repo": "gemini-cli", "pr_number": 25728, "title": "Test Bug"},
    }

    result = await evaluate_single_diff(
        "gemini_cli_25693", "+ proposed change", doc_dict, "{{PROPOSED_DIFF}} {{TRUE_DIFF}}", "gemini-3.5-flash"
    )

    assert result["score"] == 3
    assert "identical in functionality" in result["verdict_description"]
    assert result["success"] is True


@pytest.mark.asyncio
@patch("eval_diff_judge.fetch_true_diff", return_value="diff --git a/src/skill.ts b/src/skill.ts\n+fix")
@patch("eval_diff_judge.AgentRunner")
async def test_evaluate_single_diff_score_0(mock_agent_runner_cls, mock_fetch_diff):
    """Tests evaluating a single diff that receives score 0."""
    mock_agent_runner = MagicMock()
    mock_agent_runner.run_agent = AsyncMock(
        return_value=(
            json.dumps({
                "score": 0,
                "verdict_description": "Introduces syntax errors and breaks build.",
            }),
            [],
        )
    )
    mock_agent_runner_cls.return_value = mock_agent_runner

    doc_dict = {
        "workable_spec": {"issue_id": "google-gemini/gemini-cli#25693", "summary": {}},
        "github_metadata": {"owner": "google-gemini", "repo": "gemini-cli", "pr_number": 25728, "title": "Test Bug"},
    }

    result = await evaluate_single_diff(
        "gemini_cli_25693", "+ broken code", doc_dict, "{{PROPOSED_DIFF}} {{TRUE_DIFF}}", "gemini-3.5-flash"
    )

    assert result["score"] == 0
    assert "breaks build" in result["verdict_description"]


@patch("sys.argv", ["eval_diff_judge.py", "--run-name", "test_run_1", "--input-path", "eval_datasets/golden_issues"])
@patch("eval_diff_judge.evaluate_single_diff")
def test_main_report_generation(mock_eval_single, tmp_path):
    """Tests full main() evaluation run generating eval_score.txt report."""
    mock_eval_single.return_value = {
        "test_id": "gemini_cli_25693",
        "score": 3,
        "verdict_description": "Full parity fix.",
        "success": True,
    }

    runs_dir = tmp_path / "pr_gen_evals" / "runs" / "test_run_1"
    diffs_dir = runs_dir / "outputs" / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)

    test_diff_file = diffs_dir / "gemini_cli_25693_diff.diff"
    test_diff_file.write_text("diff --git a/file.py b/file.py\n+added line")
    (runs_dir / "test_results.json").write_text(
        json.dumps([{"test_id": "gemini_cli_25693", "attempts": 2, "max_attempts": 5, "runtime_seconds": 45.2}])
    )

    with patch("eval_diff_judge.RUNS_BASE_DIR", str(tmp_path / "pr_gen_evals" / "runs")):
        main()

    score_file = runs_dir / "test_run_1_eval_score.txt"
    assert score_file.exists()
    content = score_file.read_text()
    assert "DIFF EVALUATION SCORE REPORT: test_run_1" in content
    assert "Average Score:   3.00 / 3.00" in content
    assert "Average Turns:   2.00" in content
    assert "Average Runtime: 45.20s" in content
    assert "Max Attempts:         5" in content
    assert "[Score: 3/3] gemini_cli_25693 (Turns: 2, Runtime: 45.20s)" in content
    assert "Full parity fix." in content


@patch("eval_suite.load_test_files")
@patch("eval_suite.run_single_test")
@patch("eval_diff_judge.main")
def test_eval_suite_judge_flag_trigger(mock_judge_main, mock_run_test, mock_load_files, tmp_path):
    """Tests that eval_suite.py automatically triggers eval_diff_judge when --judge is specified."""
    from eval_suite import main as eval_suite_main

    mock_load_files.return_value = [("/tmp/issue.json", {"workable_spec": {}})]
    mock_run_test.return_value = {"success": True, "test_id": "issue_1"}

    with patch("sys.argv", ["eval_suite.py", "--input-path", "golden_issues", "--run-name", "judge_test_run", "--judge"]):
        with patch("eval_suite.BASE_DIR", str(tmp_path)):
            eval_suite_main()

    mock_judge_main.assert_called_once()
