# Copyright 2026 Google LLC
# Apache-2.0 License

"""Unit tests for agent trace logging formatting and JsonlLoggingHandler filtering."""

import json
import logging
import os
import sys
from unittest.mock import MagicMock

import pytest

# Ensure evals/pr-generation and workflow directory are in sys.path
PR_GEN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CARETAKER_ROOT = os.path.abspath(os.path.join(PR_GEN_DIR, "..", ".."))
WORKFLOW_DIR = os.path.join(CARETAKER_ROOT, "cloudrun", "pr-generator", "workflow")

for p in (PR_GEN_DIR, CARETAKER_ROOT, WORKFLOW_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


from gcs_logger import _get_gcs_blob_prefix, serialize_chunks, upload_agent_trajectory_log


def test_get_gcs_blob_prefix_eval_mode(monkeypatch):
    """Tests that _get_gcs_blob_prefix generates pr-generation-eval-results/runs/... path when EVAL_GCS_RUN_NAME is set."""
    # Standard mode
    monkeypatch.delenv("EVAL_GCS_RUN_NAME", raising=False)
    monkeypatch.delenv("EVAL_GCS_RUN_TIMESTAMP", raising=False)
    prefix_prod = _get_gcs_blob_prefix("google-gemini", "gemini-cli", "coding_agent")
    assert prefix_prod == "google-gemini_gemini-cli/coding_agent"

    # Eval mode with run_name and timestamp
    monkeypatch.setenv("EVAL_GCS_RUN_NAME", "benchmark_run_1")
    monkeypatch.setenv("EVAL_GCS_RUN_TIMESTAMP", "20260729_215645")
    prefix_eval = _get_gcs_blob_prefix("google-gemini", "gemini-cli", "coding_agent")
    assert prefix_eval == "runs/benchmark_run_1_20260729_215645/coding_agent"


def test_serialize_chunks_consolidates_text_deltas():
    """Tests that serialize_chunks merges consecutive Text deltas with the same step_index."""
    class Text:
        def __init__(self, step_index, text):
            self.step_index = step_index
            self.text = text

        def model_dump(self):
            return {"step_index": self.step_index, "text": self.text}

    class ToolCall:
        def model_dump(self):
            return {"name": "view_file"}

    chunks = [
        Text(1, "Hello "),
        Text(1, "world!"),
        Text(1, " How are you?"),
        ToolCall(),
        Text(2, "Final "),
        Text(2, "answer."),
    ]

    result_json = serialize_chunks(chunks)
    data = json.loads(result_json)

    assert len(data) == 3
    assert data[0]["chunk_type"] == "Text"
    assert data[0]["step_index"] == 1
    assert data[0]["text"] == "Hello world! How are you?"

    assert data[1]["chunk_type"] == "ToolCall"
    assert data[1]["name"] == "view_file"

    assert data[2]["chunk_type"] == "Text"
    assert data[2]["step_index"] == 2
    assert data[2]["text"] == "Final answer."


def test_upload_agent_trajectory_log_local_trace_dir(tmp_path, monkeypatch):
    """Tests that upload_agent_trajectory_log saves traces to LOCAL_TRACE_DIR subfolders."""
    monkeypatch.setenv("LOCAL_TRACE_DIR", str(tmp_path))
    monkeypatch.setenv("DISABLE_GCS_LOGGING", "true")

    class Thought:
        def model_dump(self):
            return {"text": "Analyzing repo..."}

    class ToolCall:
        def model_dump(self):
            return {"name": "replace_file_content"}

    mock_chunk_1 = Thought()
    mock_chunk_2 = ToolCall()

    # Upload coding agent trajectory turn 1
    upload_agent_trajectory_log(
        owner="test_owner",
        repo="test_repo",
        agent_role_folder="coding_agent",
        issue_number=123,
        resolved_chunks=[mock_chunk_1],
        timestamp="20260729_120000",
        attempt_index=1,
    )

    # Upload a second turn for coding agent turn 2
    upload_agent_trajectory_log(
        owner="test_owner",
        repo="test_repo",
        agent_role_folder="coding_agent",
        issue_number=123,
        resolved_chunks=[mock_chunk_2],
        timestamp="20260729_120500",
        attempt_index=2,
    )

    # Upload eval agent trajectory turn 1
    upload_agent_trajectory_log(
        owner="test_owner",
        repo="test_repo",
        agent_role_folder="eval_agent",
        issue_number=123,
        resolved_chunks=[mock_chunk_2],
        timestamp="20260729_121000",
        attempt_index=1,
    )

    consolidated_file = tmp_path / "issue_123.json"
    assert consolidated_file.exists()

    data = json.loads(consolidated_file.read_text(encoding="utf-8"))
    assert data["issue_number"] == 123
    assert data["owner"] == "test_owner"
    assert data["repo"] == "test_repo"

    assert "coding_1" in data
    assert len(data["coding_1"]) == 1
    assert data["coding_1"][0]["chunk_type"] == "Thought"

    assert "coding_2" in data
    assert len(data["coding_2"]) == 1
    assert data["coding_2"][0]["chunk_type"] == "ToolCall"

    assert "eval_1" in data
    assert len(data["eval_1"]) == 1
    assert data["eval_1"][0]["chunk_type"] == "ToolCall"


def test_file_handler_logs_info_logs(tmp_path):
    """Tests that FileHandler logs standard [INFO] progress logs."""
    log_file = tmp_path / "test_logs.log"
    fh = logging.FileHandler(str(log_file), mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    logger = logging.getLogger("test_file_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(fh)

    # Standard INFO log
    logger.info("Starting local evaluation for test case: gemini_cli_12345")
    logger.info("[Coding Agent Tool Call]: replace_file_content with args {'file': 'src/index.ts'}")

    fh.close()
    logger.removeHandler(fh)

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")

    assert "[INFO] test_file_logger: Starting local evaluation for test case: gemini_cli_12345" in content
    assert "[Coding Agent Tool Call]: replace_file_content" in content


def test_test_progress_filter_filters_starting_iteration():
    """Tests that TestProgressFilter blocks Starting Iteration messages from terminal output."""
    from eval_suite import TestProgressFilter

    progress_filter = TestProgressFilter()

    # Should permit
    record1 = logging.LogRecord("test", logging.INFO, "", 0, "Starting local evaluation for test case: test1", (), None)
    record2 = logging.LogRecord("test", logging.INFO, "", 0, "[Cleanup] Deleting temp workspace", (), None)
    record3 = logging.LogRecord("test", logging.INFO, "", 0, "=== [LOCAL EVAL] SUCCESS: Patch Approved and Verified ===", (), None)

    # Should filter OUT
    record4 = logging.LogRecord("test", logging.INFO, "", 0, "=== [LOCAL EVAL] Starting Iteration 1/5 ===", (), None)
    record5 = logging.LogRecord("test", logging.INFO, "", 0, "Arbitrary debug log message", (), None)

    assert progress_filter.filter(record1) is True
    assert progress_filter.filter(record2) is True
    assert progress_filter.filter(record3) is True
    assert progress_filter.filter(record4) is False
    assert progress_filter.filter(record5) is False


def test_root_warning_filter():
    """Tests that RootWarningFilter blocks System step error and Task is overloaded messages."""
    from eval_suite import RootWarningFilter

    root_filter = RootWarningFilter()

    rec_normal = logging.LogRecord("root", logging.WARNING, "", 0, "Normal system warning", (), None)
    rec_error1 = logging.LogRecord("root", logging.WARNING, "", 0, "WARNING:root:System step error (HTTP 429): Encountered retryable error", (), None)
    rec_error2 = logging.LogRecord("root", logging.WARNING, "", 0, "Task is overloaded (in-flight-requests)", (), None)

    assert root_filter.filter(rec_normal) is True
    assert root_filter.filter(rec_error1) is False
    assert root_filter.filter(rec_error2) is False


def test_clean_error_message():
    """Tests that _clean_error_message extracts single-line summary from protobuf traces."""
    from orchestrator import _clean_error_message

    long_protobuf_error = (
        'error_contexts { rpc_idenitifer { target: "blade:uniserve" } }\n'
        'request failed (code 429): Resource exhausted. Please try again later.\n'
        'Transitioning to evaluation...'
    )
    cleaned = _clean_error_message(Exception(long_protobuf_error))
    assert cleaned == "request failed (code 429): Resource exhausted. Please try again later."


def test_upload_eval_run_artifacts(tmp_path, monkeypatch):
    """Tests that upload_eval_run_artifacts uploads Results.txt, score report, logs, and outputs to GCS."""
    from unittest.mock import patch
    from gcs_logger import upload_eval_run_artifacts

    monkeypatch.setenv("EVAL_GCS_RUN_NAME", "run_test_gcs")
    monkeypatch.setenv("EVAL_GCS_RUN_TIMESTAMP", "20260730_150000")
    monkeypatch.delenv("DISABLE_GCS_LOGGING", raising=False)

    run_dir = tmp_path / "run_test_gcs"
    outputs_diffs = run_dir / "outputs" / "diffs"
    logs_dir = run_dir / "logs"
    outputs_diffs.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "Results.txt").write_text("Results summary content")
    (run_dir / "run_test_gcs_eval_score.md").write_text("# Score Report")
    (outputs_diffs / "issue_25693_20260730_150000_diff.diff").write_text("diff content")
    (logs_dir / "issue_25693_20260730_150000_logs.log").write_text("log content")

    uploaded_blobs = []

    def fake_upload_to_bucket(blob_path, content, content_type="text/plain"):
        uploaded_blobs.append((blob_path, content, content_type))
        return True

    with patch("gcs_logger.upload_to_bucket", side_effect=fake_upload_to_bucket):
        upload_eval_run_artifacts(str(run_dir), "run_test_gcs")

    blob_paths = [b[0] for b in uploaded_blobs]
    assert "runs/run_test_gcs_20260730_150000/Results.txt" in blob_paths
    assert "runs/run_test_gcs_20260730_150000/run_test_gcs_eval_score.md" in blob_paths
    assert "runs/run_test_gcs_20260730_150000/outputs/diffs/issue_25693_20260730_150000_diff.diff" in blob_paths
    assert "runs/run_test_gcs_20260730_150000/logs/issue_25693_20260730_150000_logs.log" in blob_paths

