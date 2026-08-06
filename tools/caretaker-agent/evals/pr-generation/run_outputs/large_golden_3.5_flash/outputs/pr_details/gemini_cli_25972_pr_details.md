## Commit Message

[SSR Agent] Issue Fix (25972): Prevent filesystem crashes when prompts contain logs or traces

## PR Description

fixes #25972
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/25972

### Context & Problem
The CLI previously crashed with filesystem errors (such as `ENAMETOOLONG`) when user prompts contained test logs or stack traces. This occurred because the CLI misinterpreted large text blocks and log fragments containing markers like `AssertionError:` or `FAIL` as file paths and attempted to resolve them via system filesystem APIs without validating path length or structure.

### Detailed Changes
- **Path Validation**: Created `validatePath` in [path-validator.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/core/src/utils/path-validator.ts) to check inputs for control/newline characters, log markers, length limits (total path length <= 4096 and individual component length <= 255), and suspicious quotes, backticks, or ellipses.
- **Embedded Path Extraction**: Implemented `tryExtractPath` and `resolveAtCommandPath` in [atCommandUtils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/core/src/utils/atCommandUtils.ts) to safely extract and validate subpaths from logs on a best-effort basis.
- **Security Check Integration**: Updated `Config.validatePathAccess` in [config.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/core/src/config/config.ts) to execute `validatePath` immediately at the start of permission checks.
- **AT-Command Refactor**: Updated path resolution in [atCommandProcessor.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/atCommandProcessor.ts) and [acpSession.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/cli/src/acp/acpSession.ts) to resolve paths via `resolveAtCommandPath`.
- **Exports**: Exported the new helpers in [index.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/core/src/index.ts).
- **Unit Testing**: Implemented unit tests inside [path-validator.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_25972/tmp/eval/gemini-cli/packages/core/src/utils/path-validator.test.ts) covering a wide array of success and error constraints.

### Verification
Vitest unit tests were implemented for all validator and extraction functions, verifying correct handling of log fragments, newlines, control characters, valid paths containing brackets/spaces, and bounds/component checking. Static analysis checks and TypeScript compile checks successfully validated without warnings or errors.
