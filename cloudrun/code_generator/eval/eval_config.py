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

"""Evaluation Configuration Subclass.

Extends standard Config to support isolated workspace directories per test case
and dynamic target repository resolution from github_metadata.
"""

import os
import sys

# Ensure workflow directory is in sys.path for clean imports
WORKFLOW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workflow"))
if WORKFLOW_DIR not in sys.path:
    sys.path.insert(0, WORKFLOW_DIR)

from config import Config


class EvalConfig(Config):
    """Custom configuration for local evaluation suite runs."""

    def __init__(self, workspace_root: str, firestore_doc_dict: dict) -> None:
        """Initializes configuration scoped to a specific test workspace.

        Args:
            workspace_root: Directory path for this test case's agent environment.
            firestore_doc_dict: Pre-parsed dictionary representing the Firestore spec.
        """
        super().__init__()
        self.firestore_doc_dict = firestore_doc_dict

        # Dynamically target the repository specified in the test file's github_metadata
        github_meta = firestore_doc_dict.get("github_metadata", {})
        owner = github_meta.get("owner")
        repo = github_meta.get("repo")
        if owner and repo:
            self.repo_url = f"https://github.com/{owner}/{repo}"
            self.repo_name = repo
        else:
            self.repo_url = os.environ.get(
                "REPO_URL", "https://github.com/joneba-google/gemini-cli-clone"
            )
            self.repo_name = (
                self.repo_url.rstrip("/").split("/")[-1].replace(".git", "")
            )

        # Override tmp paths to execute inside isolated agent_environments folder
        self.tmp_dir = os.path.join(workspace_root, "tmp")
        self.pr_dir = os.path.join(self.tmp_dir, "pr")
        self.eval_dir = os.path.join(self.tmp_dir, "eval")

        self.pr_repo_path = os.path.join(self.pr_dir, self.repo_name)
        self.eval_repo_path = os.path.join(self.eval_dir, self.repo_name)

        # Execution identifier
        self.execution_id = os.environ.get("EXECUTION_ID", "local-eval-execution")

    def load_and_validate_firestore_doc(self) -> dict:
        """Returns the pre-loaded Firestore dictionary directly."""
        return self.firestore_doc_dict
