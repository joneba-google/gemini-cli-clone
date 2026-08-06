## Commit Message

[SSR Agent] Issue Fix (28115): Prevent lifecycle scripts failure during release verification

## PR Description

fixes #28115
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/28115

### Context & Problem
During the verify-release GitHub Action setup, running the integration tests command `npm ci` triggered post-install or other lifecycle scripts of dependencies. In the isolated sandbox environment of the action, these scripts failed, leading to a failure of the entire nightly release workflow.

### Detailed Changes
- Updated [.github/actions/verify-release/action.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28115/tmp/eval/gemini-cli/.github/actions/verify-release/action.yml#L86-L90) inside the `Install dependencies for integration tests` step.
- Appended `--ignore-scripts` to the `npm ci` command to prevent dependency lifecycle/post-install scripts from executing.

### Verification
- Inspected [.github/actions/verify-release/action.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28115/tmp/eval/gemini-cli/.github/actions/verify-release/action.yml) to ensure spelling, syntax, and options are correct.
- Verified that lint checks were cleanly passed/skipped as confirmed in [linter_output.txt](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28115/tmp/eval/gemini-cli/linter_output.txt).
