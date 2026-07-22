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

"""Evaluation Orchestrator Subclass.

Bypasses Firestore locking and GitHub PR submission for local evaluation runs.
"""

import json
import logging
import os
import re
import sys

# Ensure workflow directory is in sys.path for clean imports
WORKFLOW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workflow"))
if WORKFLOW_DIR not in sys.path:
    sys.path.insert(0, WORKFLOW_DIR)

from orchestrator import Orchestrator, OrchestrationError
from command_executor import CommandExecutor


class EvalOrchestrator(Orchestrator):
    """Subclass of Orchestrator adapted for offline evaluation runs."""

    def __init__(self, config) -> None:
        super().__init__(config)
        self.generated_diff: str | None = None
        self.pr_details_content: str | None = None

    async def run(self) -> dict:
        """Executes orchestration pipeline locally without GCP or GitHub calls.

        Returns:
            Dictionary containing evaluation status, diff content, and pr_details.
        """
        self._setup_workspace()
        firestore_doc = self.config.load_and_validate_firestore_doc()

        issue_id = firestore_doc.get("workable_spec", {}).get("issue_id", "unknown")
        github_metadata = firestore_doc.get("github_metadata", {})
        issue_num = github_metadata.get("issue_number", 0)

        branch_name = f"eval-agent-issue-{issue_num}"

        # 1. Sync / Clone target repository locally
        self._sync_or_clone_repository()
        
        # 2. Persist firestore_doc.json into PR repo workspace
        spec_pr_path = os.path.join(self.config.pr_repo_path, "firestore_doc.json")
        try:
            with open(spec_pr_path, "w", encoding="utf-8") as f:
                json.dump(firestore_doc, f, indent=2)
        except IOError as e:
            raise OrchestrationError(f"Failed to save firestore_doc.json to workspace: {e}") from e

        # Install NPM packages inside PR workspace if node_modules is missing
        node_modules_path = os.path.join(self.config.pr_repo_path, "node_modules")
        if not os.path.exists(node_modules_path):
            logging.info("Installing node dependencies inside PR repository workspace...")
            try:
                npm_install_cmd = 'NODE_OPTIONS="--max-old-space-size=4096" npm ci --no-audit --no-fund --maxsockets 3'
                CommandExecutor.run(npm_install_cmd, self.config.pr_repo_path)
            except Exception as e:
                raise OrchestrationError(f"Failed to install NPM dependencies in PR workspace: {e}") from e

        approved = False
        loop_count = 0
        verdict = "NEEDS_REVISION"
        commit_line_count = 0

        while loop_count < self.config.max_attempts and not approved:
            loop_count += 1
            logging.info("=== [LOCAL EVAL] Starting Iteration %s/%s ===", loop_count, self.config.max_attempts)

            # Phase 1: Code Generation
            await self._run_code_generation(loop_count)

            # Stage edits and generate diff
            diff_content = self._prepare_iteration_commit(issue_num, loop_count)
            if not diff_content:
                logging.info("[LOCAL EVAL] No code modifications detected in iteration %s.", loop_count)
                continue
            self.generated_diff = diff_content

            # Phase 2: Evaluation
            verdict = await self._run_evaluation(diff_content, firestore_doc)

            if verdict in ["APPROVED", "PASS"]:
                logging.info("[LOCAL EVAL] Patch approved by Evaluator. Running regression checks...")
                approved = await self._run_regression_checks()

                if approved:
                    try:
                        diff_stat = CommandExecutor.run("git diff --stat origin/main", self.config.pr_repo_path)
                        logging.info("Diff Stat summary:\n%s", diff_stat)
                        lines = diff_stat.split("\n")
                        last_line = lines[-1] if lines else ""
                        insertions = re.search(r"(\d+)\s+insertion", last_line)
                        deletions = re.search(r"(\d+)\s+deletion", last_line)
                        if insertions:
                            commit_line_count += int(insertions.group(1))
                        if deletions:
                            commit_line_count += int(deletions.group(1))
                    except Exception as e:
                        logging.warning("Failed to parse modifications line count: %s", e)

            if not approved:
                self._save_feedback_to_coding_workspace()

        # Extract pr_details.md if generated
        pr_details_path = os.path.join(self.config.eval_repo_path, "pr_details.md")
        if os.path.exists(pr_details_path):
            try:
                with open(pr_details_path, "r", encoding="utf-8") as f:
                    self.pr_details_content = f.read()
            except IOError:
                pass

        if approved:
            if commit_line_count > 500:
                logging.error("[LOCAL EVAL] Approved but modifications (%s lines) exceed 500 limit.", commit_line_count)
                return {
                    "success": False,
                    "status": "EXCEEDED_LINE_LIMIT",
                    "diff": self.generated_diff,
                    "pr_details": self.pr_details_content,
                    "error": f"Commit modifications ({commit_line_count} lines) exceed 500 lines limit.",
                }
            logging.info("=== [LOCAL EVAL] SUCCESS: Patch Approved and Verified ===")
            return {
                "success": True,
                "status": "APPROVED",
                "diff": self.generated_diff,
                "pr_details": self.pr_details_content,
                "error": None,
            }
        else:
            logging.error("=== [LOCAL EVAL] FAILED: Exceeded Max Attempts without Approval ===")
            return {
                "success": False,
                "status": "REJECTED",
                "diff": self.generated_diff,
                "pr_details": None,
                "error": f"Failed to reach approval after {self.config.max_attempts} iterations.",
            }
