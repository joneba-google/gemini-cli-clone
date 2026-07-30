#!/usr/bin/env python3
# Copyright 2026 Google LLC
# Apache-2.0 License

"""LLM-as-a-Judge Diff Evaluator for SSR Code Generator Evaluation Runs.

Usage:
    python3 eval/eval_diff_judge.py --run-name run_1 [--model gemini-3.5-flash]
"""

import argparse
import glob
import json
import logging
import os
import re
import sys
import urllib.request
from typing import Any

# Ensure workflow directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflow")
if WORKFLOW_DIR not in sys.path:
    sys.path.insert(0, WORKFLOW_DIR)

from agent_runner import AgentRunner
from config import Config


RUNS_BASE_DIR = os.path.join(BASE_DIR, "eval", "run_outputs")
JUDGE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "judge_prompt.md")


def parse_args():
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge Diff Evaluator")
    parser.add_argument("--run-name", required=True, help="Run identifier (e.g. 'run_1')")
    parser.add_argument("--input-path", "--input-dir", required=True, help="Input directory or file containing golden issue JSON specs")
    parser.add_argument("--model", default="gemini-3.5-flash", help="LLM model for judge evaluation")
    return parser.parse_args()


def load_judge_prompt_template() -> str:
    """Loads the markdown template for the judge prompt."""
    if not os.path.exists(JUDGE_PROMPT_PATH):
        raise FileNotFoundError(f"Judge prompt file not found: {JUDGE_PROMPT_PATH}")
    with open(JUDGE_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def fetch_true_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetches the ground-truth PR diff from GitHub."""
    if not owner or not repo or not pr_number:
        return ""
    url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    req = urllib.request.Request(url, headers={"User-Agent": "SSR-Eval-Judge"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        logging.warning("Failed to fetch true diff from GitHub (%s): %s", url, e)
        return ""


def find_golden_spec_for_test(test_id: str, input_path: str) -> dict | None:
    """Finds matching reformatted golden issue JSON by test_id or issue number within input_path."""
    if not input_path or not os.path.exists(input_path):
        return None
    if os.path.isfile(input_path):
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                doc = json.load(f)
                base = os.path.splitext(os.path.basename(input_path))[0]
                if base in test_id or test_id.startswith(base):
                    return doc
        except Exception:
            return None
        return None

    for filepath in glob.glob(os.path.join(input_path, "*.json")):
        base = os.path.splitext(os.path.basename(filepath))[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                doc = json.load(f)
                issue_num = str(doc.get("github_metadata", {}).get("issue_number", ""))
                if base in test_id or test_id.startswith(base) or (issue_num and f"issue_{issue_num}" in test_id):
                    return doc
        except Exception:
            pass
    return None


async def evaluate_single_diff(
    test_id: str,
    proposed_diff: str,
    doc_dict: dict,
    prompt_template: str,
    model_name: str,
) -> dict[str, Any]:
    """Evaluates a single proposed diff against ground-truth using LLM judge."""
    github_meta = doc_dict.get("github_metadata", {})
    workable_spec = doc_dict.get("workable_spec", {})

    owner = github_meta.get("owner", "google-gemini")
    repo = github_meta.get("repo", "gemini-cli")
    pr_number = github_meta.get("pr_number", 0)

    true_diff = fetch_true_diff(owner, repo, pr_number)
    if not true_diff:
        true_diff = "# (Ground truth diff unavailable from GitHub REST API)"

    # Render judge prompt template
    prompt = prompt_template.replace("{{OWNER}}", owner)
    prompt = prompt.replace("{{REPO}}", repo)
    prompt = prompt.replace("{{ISSUE_ID}}", str(workable_spec.get("issue_id", f"{owner}/{repo}#{github_meta.get('issue_number')}")))
    prompt = prompt.replace("{{ISSUE_TITLE}}", str(github_meta.get("title", "")))
    prompt = prompt.replace("{{ISSUE_SUMMARY}}", json.dumps(workable_spec.get("summary", {}), indent=2))
    prompt = prompt.replace("{{TRUE_DIFF}}", true_diff)
    prompt = prompt.replace("{{PROPOSED_DIFF}}", proposed_diff if proposed_diff.strip() else "# No changes generated.")

    config = Config()
    config.model_name = model_name
    agent_runner = AgentRunner(
        project_id=config.project_id,
        location=config.location,
        model_name=model_name,
    )

    try:
        raw_output, _ = await agent_runner.run_agent(
            role="LLM Diff Judge",
            prompt=prompt,
            repo_path=config.tmp_dir,
        )
        
        # Parse JSON payload from judge response
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            score = int(parsed.get("score", 0))
            verdict = str(parsed.get("verdict_description", raw_output))
        else:
            score = 1 if "Score: 1" in raw_output or "2" in raw_output else 0
            verdict = raw_output.strip()

        # Clamp score between 0 and 3
        score = max(0, min(3, score))

        return {
            "test_id": test_id,
            "score": score,
            "verdict_description": verdict,
            "success": True,
        }
    except Exception as e:
        logging.error("Failed LLM evaluation for %s: %s", test_id, e)
        return {
            "test_id": test_id,
            "score": 0,
            "verdict_description": f"Evaluation exception: {e}",
            "success": False,
        }


def load_test_metrics_for_run(run_dir: str) -> tuple[dict[str, tuple[Any, Any]], dict[str, Any]]:
    """Loads turn counts (attempts, max_attempts) and runtimes mapped by test_id from test_results.json or Results.txt."""
    turn_map = {}
    runtime_map = {}
    json_path = os.path.join(run_dir, "test_results.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    tid = item.get("test_id")
                    if tid:
                        turn_map[tid] = (item.get("attempts", "?"), item.get("max_attempts", "?"))
                        runtime_map[tid] = item.get("runtime_seconds")
            return turn_map, runtime_map
        except Exception as e:
            logging.warning("Failed to read test_results.json: %s", e)

    results_txt_path = os.path.join(run_dir, "Results.txt")
    if os.path.exists(results_txt_path):
        try:
            with open(results_txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r"\[.*?\]\s+(\S+)\s+\(Turns:\s+(\w+)(?:,\s+Runtime:\s+([\d.]+s))?\)", line)
                    if match:
                        turn_map[match.group(1)] = (match.group(2), "?")
                        if match.group(3):
                            runtime_map[match.group(1)] = float(match.group(3).rstrip("s"))
        except Exception as e:
            logging.warning("Failed to read Results.txt: %s", e)

    return turn_map, runtime_map


def main():
    args = parse_args()
    run_dir = os.path.join(RUNS_BASE_DIR, args.run_name)
    diffs_dir = os.path.join(run_dir, "outputs", "diffs")

    if not os.path.exists(run_dir):
        print(f"Error: Run directory does not exist: {run_dir}")
        sys.exit(1)

    diff_files = glob.glob(os.path.join(diffs_dir, "*_diff.diff"))
    if not diff_files:
        print(f"Error: No diff output files found in '{diffs_dir}'.")
        sys.exit(1)

    print("==========================================================")
    print(f" Starting LLM-as-a-Judge Evaluation: {args.run_name}")
    print(f" Input Path:      {args.input_path}")
    print(f" Diff Files Found: {len(diff_files)}")
    print(f" Judge Model:     {args.model}")
    print("==========================================================\n")

    prompt_template = load_judge_prompt_template()
    turn_map, runtime_map = load_test_metrics_for_run(run_dir)
    results = []

    import asyncio

    for diff_file in sorted(diff_files):
        test_id = os.path.basename(diff_file).replace("_diff.diff", "")
        with open(diff_file, "r", encoding="utf-8") as f:
            proposed_diff = f.read()

        doc_dict = find_golden_spec_for_test(test_id, args.input_path) or {}
        eval_res = asyncio.run(
            evaluate_single_diff(test_id, proposed_diff, doc_dict, prompt_template, args.model)
        )
        attempts, max_att = turn_map.get(test_id, ("?", "?"))
        eval_res["attempts"] = attempts
        eval_res["max_attempts"] = max_att
        eval_res["runtime_seconds"] = runtime_map.get(test_id)
        results.append(eval_res)

    # Compute overall score average, average turns, and average runtime
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / len(results) if results else 0.0

    valid_turns = [int(r["attempts"]) for r in results if str(r.get("attempts", "")).isdigit()]
    avg_turns = sum(valid_turns) / len(valid_turns) if valid_turns else 0.0
    avg_turns_str = f"{avg_turns:.2f}" if valid_turns else "?"

    valid_runtimes = [float(r["runtime_seconds"]) for r in results if r.get("runtime_seconds") is not None]
    avg_runtime = sum(valid_runtimes) / len(valid_runtimes) if valid_runtimes else 0.0
    avg_runtime_str = f"{avg_runtime:.2f}s" if valid_runtimes else "?"

    max_att_str = next((str(r["max_attempts"]) for r in results if r.get("max_attempts") != "?"), "?")

    # Output file path: runs/{run_name}/{run_name}_eval_score.md (Markdown format)
    eval_score_file = os.path.join(run_dir, f"{args.run_name}_eval_score.md")
    with open(eval_score_file, "w", encoding="utf-8") as f:
        f.write(f"# 📊 Diff Evaluation Score Report: {args.run_name}\n\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Average Score** | **{avg_score:.2f} / 3.00** |\n")
        f.write(f"| **Average Turns** | **{avg_turns_str}** |\n")
        f.write(f"| **Average Runtime** | **{avg_runtime_str}** |\n")
        f.write(f"| **Evaluated Test Cases** | **{len(results)}** |\n")
        if max_att_str != "?":
            f.write(f"| **Max Attempts** | **{max_att_str}** |\n")
        f.write("\n---\n\n")

        f.write("## 🔍 Detailed Test Case Scores & Verdicts\n\n")
        f.write("| Status | Issue | Turns | Runtime | Score | Verdict & Critique |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            status_icon = "✅ PASS" if r.get("score", 0) >= 2 else "❌ FAIL"
            attempts = r.get("attempts", "?")
            runtime_val = r.get("runtime_seconds")
            runtime_str = f"{runtime_val:.2f}s" if runtime_val is not None else "N/A"
            verdict_clean = str(r.get("verdict_description", "")).replace("|", "\\|").replace("\n", " ")
            
            # Extract clean issue number for table display
            issue_num = r.get("doc", {}).get("github_metadata", {}).get("issue_number")
            if not issue_num:
                parts = r["test_id"].split("_")
                for p in parts:
                    if p.isdigit():
                        issue_num = p
                        break
                if not issue_num:
                    issue_num = parts[-1]
            issue_label = f"#{issue_num}"
            f.write(f"| {status_icon} | `{issue_label}` | {attempts} | {runtime_str} | **{r['score']}/3** | {verdict_clean} |\n")
        f.write("\n---\n\n")
        f.write("*Generated by LLM-as-a-Judge Diff Evaluator.*\n")

    print("\n==========================================================")
    print(f" Diff Evaluation Complete!")
    print(f" Average Score:   {avg_score:.2f} / 3.00 across {len(results)} test cases")
    print(f" Average Turns:   {avg_turns_str}")
    print(f" Average Runtime: {avg_runtime_str}")
    print(f" Score Report:    {eval_score_file}")
    print("==========================================================")


if __name__ == "__main__":
    main()
