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


RUNS_BASE_DIR = os.path.join(BASE_DIR, "pr_gen_evals", "runs")
GOLDEN_ISSUES_DIR = os.path.join(BASE_DIR, "golden_issues")
JUDGE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "judge_prompt.md")


def parse_args():
    parser = argparse.ArgumentParser(description="LLM-as-a-Judge Diff Evaluator")
    parser.add_argument("--run-name", required=True, help="Run identifier (e.g. 'run_1')")
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


def find_golden_spec_for_test(test_id: str) -> dict | None:
    """Finds matching reformatted golden issue JSON by test_id or issue number."""
    # Attempt direct file match e.g. gemini_cli_25693.json
    for filepath in glob.glob(os.path.join(GOLDEN_ISSUES_DIR, "*.json")):
        base = os.path.splitext(os.path.basename(filepath))[0]
        if base in test_id or test_id.startswith(base):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
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
    agent_runner = AgentRunner(config)

    try:
        raw_output, _ = await agent_runner.run_agent(prompt)
        
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
    print(f" Diff Files Found: {len(diff_files)}")
    print(f" Judge Model:     {args.model}")
    print("==========================================================\n")

    prompt_template = load_judge_prompt_template()
    results = []

    import asyncio

    for diff_file in sorted(diff_files):
        test_id = os.path.basename(diff_file).replace("_diff.diff", "")
        with open(diff_file, "r", encoding="utf-8") as f:
            proposed_diff = f.read()

        doc_dict = find_golden_spec_for_test(test_id) or {}
        eval_res = asyncio.run(
            evaluate_single_diff(test_id, proposed_diff, doc_dict, prompt_template, args.model)
        )
        results.append(eval_res)

    # Compute overall score average
    total_score = sum(r["score"] for r in results)
    avg_score = total_score / len(results) if results else 0.0

    # Output file path: runs/{run_name}/{run_name}_eval_score.txt
    eval_score_file = os.path.join(run_dir, f"{args.run_name}_eval_score.txt")
    with open(eval_score_file, "w", encoding="utf-8") as f:
        f.write("==========================================================\n")
        f.write(f" DIFF EVALUATION SCORE REPORT: {args.run_name}\n")
        f.write("==========================================================\n")
        f.write(f"Average Score: {avg_score:.2f} / 3.00\n")
        f.write(f"Evaluated Test Cases: {len(results)}\n\n")

        f.write("----------------------------------------------------------\n")
        f.write(" DETAILED TEST CASE SCORES & VERDICTS\n")
        f.write("----------------------------------------------------------\n")
        for r in results:
            f.write(f"[Score: {r['score']}/3] {r['test_id']}\n")
            f.write(f"  Verdict: {r['verdict_description']}\n\n")

    print("\n==========================================================")
    print(f" Diff Evaluation Complete!")
    print(f" Average Score: {avg_score:.2f} / 3.00 across {len(results)} test cases")
    print(f" Score Report:  {eval_score_file}")
    print("==========================================================")


if __name__ == "__main__":
    main()
