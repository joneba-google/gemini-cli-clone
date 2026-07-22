#!/usr/bin/env python3
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

"""Local Evaluation Suite Runner for SSR Code Generator Agent.

Usage:
  python3 eval/eval_suite.py --input-path <dir_or_file> --run-name <name> [--max-workers <N>]
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any

# Ensure workflow and eval directories are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflow")
EVAL_DIR = os.path.dirname(__file__)

if WORKFLOW_DIR not in sys.path:
    sys.path.append(WORKFLOW_DIR)
if EVAL_DIR not in sys.path:
    sys.path.append(EVAL_DIR)

from eval_config import EvalConfig
from eval_orchestrator import EvalOrchestrator


import datetime


class JsonlLoggingHandler(logging.Handler):
    """Logging handler that formats and writes records as JSON Lines."""

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath
        self.file = open(filepath, "a", encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = {
                "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            self.file.write(json.dumps(log_entry) + "\n")
            self.file.flush()
        except Exception:
            self.handleError(record)

    def close(self) -> None:
        if hasattr(self, "file") and not self.file.closed:
            self.file.close()
        super().close()


def parse_args():
    parser = argparse.ArgumentParser(description="SSR Code Generator Local Evaluation Suite")
    parser.add_argument("--input-path", required=True, help="Path to JSON test file or directory of JSON files")
    parser.add_argument("--run-name", required=True, help="Run identifier (e.g. 'run_1')")
    parser.add_argument("--max-workers", type=int, default=1, help="Max parallel test execution processes")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max repair iterations per test case")
    parser.add_argument("--keep-env", action="store_true", help="Keep agent_environments directory after run")
    return parser.parse_args()


def load_test_files(input_path: str) -> list[tuple[str, dict]]:
    """Loads all valid test message JSON files from a file or directory."""
    files = []
    abs_path = os.path.abspath(input_path)
    if os.path.isfile(abs_path):
        paths = [abs_path]
    elif os.path.isdir(abs_path):
        paths = [
            os.path.join(abs_path, f)
            for f in sorted(os.listdir(abs_path))
            if f.endswith(".json") and not f.startswith(".")
        ]
    else:
        raise ValueError(f"Input path does not exist: {input_path}")

    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "workable_spec" in data:
                    files.append((p, data))
        except Exception as e:
            print(f"Warning: Skipping invalid test JSON {p}: {e}")

    return files


def run_single_test(args_tuple: tuple) -> dict[str, Any]:
    """Worker process function executing a single evaluation test case."""
    file_path, doc_dict, run_dir, max_attempts, keep_env = args_tuple

    file_base = os.path.splitext(os.path.basename(file_path))[0]
    github_meta = doc_dict.get("github_metadata", {})
    issue_num = github_meta.get("issue_number", "0")
    test_id = f"{file_base}_{issue_num}"

    # Setup distinct directories for this run under pr_gen_evals/runs/{run_name}/
    env_dir = os.path.join(run_dir, "agent_environments", test_id)
    logs_dir = os.path.join(run_dir, "logs")
    jsonl_dir = os.path.join(run_dir, "jsonl")
    diffs_dir = os.path.join(run_dir, "outputs", "diffs")
    pr_details_dir = os.path.join(run_dir, "outputs", "pr_details")

    os.makedirs(env_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(jsonl_dir, exist_ok=True)
    os.makedirs(diffs_dir, exist_ok=True)
    os.makedirs(pr_details_dir, exist_ok=True)

    log_file_txt = os.path.join(logs_dir, f"{test_id}_logs.log")
    log_file_jsonl = os.path.join(jsonl_dir, f"{test_id}_logs.jsonl")

    # Configure per-process file logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for h in logger.handlers[:]:
        logger.removeHandler(h)

    fh = logging.FileHandler(log_file_txt, mode="w", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(fh)

    jh = JsonlLoggingHandler(log_file_jsonl)
    logger.addHandler(jh)

    logging.info("Starting local evaluation for test case: %s", test_id)

    # Instantiate config (dynamically resolving repo from github_metadata) & orchestrator
    config = EvalConfig(workspace_root=env_dir, firestore_doc_dict=doc_dict)
    config.max_attempts = max_attempts
    orchestrator = EvalOrchestrator(config)

    # Execute async pipeline
    try:
        result = asyncio.run(orchestrator.run())
        result["test_id"] = test_id
        result["file_base"] = file_base
        result["issue_num"] = issue_num

        # Save output artifacts on success
        if result.get("success"):
            if result.get("diff"):
                diff_path = os.path.join(diffs_dir, f"{test_id}_diff.diff")
                with open(diff_path, "w", encoding="utf-8") as f:
                    f.write(result["diff"])
            if result.get("pr_details"):
                pr_path = os.path.join(pr_details_dir, f"{test_id}_pr_details.md")
                with open(pr_path, "w", encoding="utf-8") as f:
                    f.write(result["pr_details"])

    except Exception as e:
        logging.exception("Unhandled exception during test execution: %s", e)
        result = {
            "test_id": test_id,
            "file_base": file_base,
            "issue_num": issue_num,
            "success": False,
            "status": "CRASHED",
            "error": str(e),
        }
    finally:
        # Close logging handlers
        jh.close()
        fh.close()

        # Cleanup temporary environment folder unless keep_env is specified
        if not keep_env and os.path.exists(env_dir):
            try:
                shutil.rmtree(env_dir)
            except OSError as err:
                logging.warning("Failed to clean up env dir %s: %s", env_dir, err)

    return result


def main():
    args = parse_args()

    # Create root run output directory under pr_gen_evals/runs/{run_name}/
    runs_base_dir = os.path.abspath(os.path.join(BASE_DIR, "pr_gen_evals", "runs"))
    run_dir = os.path.join(runs_base_dir, args.run_name)
    os.makedirs(run_dir, exist_ok=True)

    test_files = load_test_files(args.input_path)
    if not test_files:
        print(f"Error: No valid test message JSON files found at '{args.input_path}'.")
        sys.exit(1)

    print("==========================================================")
    print(f" Starting Local Evaluation Suite Run: {args.run_name}")
    print(f" Input Target:  {args.input_path}")
    print(f" Test Cases:    {len(test_files)}")
    print(f" Max Workers:   {args.max_workers}")
    print(f" Output Folder: {run_dir}")
    print("==========================================================\n")

    start_time = time.time()
    results = []

    tasks = [
        (file_path, doc_dict, run_dir, args.max_attempts, args.keep_env)
        for file_path, doc_dict in test_files
    ]

    if args.max_workers > 1:
        with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
            results = list(executor.map(run_single_test, tasks))
    else:
        results = [run_single_test(t) for t in tasks]

    elapsed = time.time() - start_time
    passed_count = sum(1 for r in results if r.get("success"))
    failed_count = len(results) - passed_count

    # Generate Results.txt summary
    results_txt_path = os.path.join(run_dir, "Results.txt")
    with open(results_txt_path, "w", encoding="utf-8") as f:
        f.write("==========================================================\n")
        f.write(f" EVALUATION SUITE RESULTS: {args.run_name}\n")
        f.write("==========================================================\n")
        f.write(f"Total Test Cases: {len(results)}\n")
        f.write(f"Passed:           {passed_count}\n")
        f.write(f"Failed:           {failed_count}\n")
        f.write(f"Execution Time:   {elapsed:.2f} seconds\n\n")

        f.write("----------------------------------------------------------\n")
        f.write(" DETAILED TEST BREAKDOWN\n")
        f.write("----------------------------------------------------------\n")
        for r in results:
            status_symbol = "✅ PASS" if r.get("success") else "❌ FAIL"
            f.write(f"[{status_symbol}] {r['test_id']}\n")
            if not r.get("success"):
                f.write(f"    Error: {r.get('error', 'Unknown failure')}\n")
            f.write("\n")

    print("\n==========================================================")
    print(f" Evaluation Suite Complete ({elapsed:.2f}s)")
    print(f" Results: {passed_count}/{len(results)} Passed ({failed_count} Failed)")
    print(f" Summary: {results_txt_path}")
    print("==========================================================")


if __name__ == "__main__":
    main()
