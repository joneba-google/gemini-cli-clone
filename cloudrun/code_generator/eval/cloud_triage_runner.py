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

"""Cloud Run Job Entrypoint for Batch Triage Agent Spec Generation.

Executes triage_agent_runner.py with CLI arguments and syncs outputs to GCS.
Usage:
    python3 eval/cloud_triage_runner.py --issues 19868,21527 --concurrency 3 --gcs
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
EVAL_DIR = Path(__file__).parent.resolve()
BASE_DIR = EVAL_DIR.parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from eval.helpers.triage_agent_runner import main as run_triage_batch

logger = logging.getLogger("CloudTriageRunner")


def main() -> None:
    """Entrypoint for Cloud Run Job execution."""
    logger.info("Starting Cloud Triage Runner...")
    try:
        run_triage_batch()
        logger.info("Cloud Triage Runner completed successfully.")
    except Exception as e:
        logger.critical(
            f"Cloud Triage Runner failed with unhandled error: {e}", exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
