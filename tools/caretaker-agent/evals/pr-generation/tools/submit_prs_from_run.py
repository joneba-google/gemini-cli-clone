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

"""GitHub App PR Submission Helper CLI for Evaluation Runs.

Invokes the TypeScript Octokit helper (submit_prs_from_run.ts) with appropriate
arguments, or executes PR submissions programmatically.
"""

import os
import sys
import subprocess
from pathlib import Path


def main() -> None:
    current_dir = Path(__file__).resolve().parent
    ts_script = current_dir / "submit_prs_from_run.ts"

    if not ts_script.exists():
        print(f"❌ Error: TypeScript helper script not found at {ts_script}", file=sys.stderr)
        sys.exit(1)

    cmd = ["npx", "tsx", str(ts_script)] + sys.argv[1:]
    
    # Run from the project root directory
    repo_root = current_dir.parents[4]
    
    try:
        res = subprocess.run(cmd, cwd=str(repo_root))
        sys.exit(res.returncode)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error executing Octokit PR submission script: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
