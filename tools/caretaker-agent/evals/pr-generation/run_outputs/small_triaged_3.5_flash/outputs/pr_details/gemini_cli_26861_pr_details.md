## Commit Message

[SSR Agent] Issue Fix (26861): Strip surrounding quotes from session identifier on resume

## PR Description

fixes #26861
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26861

### Context & Problem
When closing a session, the resume message includes instructions such as `gemini --resume <session_id>`. On some shells, especially in Windows Command Prompt, copying and running the command with single or double quotes around the session ID literally passed the quotes in `process.argv` and resulted in an "Invalid session identifier" because `SessionSelector.findSession` did not strip surrounding quotes.

### Detailed Changes
- Removed the problematic logic forcing surrounding quotes for session ID in the footer message in [SessionSummaryDisplay.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/ui/components/SessionSummaryDisplay.tsx) and simplified it to print a clean session ID.
- Updated `SessionSelector.findSession` in [sessionUtils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/utils/sessionUtils.ts) to strip leading and trailing single or double quotes from the user-specified session identifier before attempting any session lookup.
- Created [polyfill-file.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/test-utils/polyfill-file.ts) to polyfill `global.File` under Node environments for file operations in tests, introducing import in [test-setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/test-setup.ts).
- Added unit tests in [SessionSummaryDisplay.test.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/ui/components/SessionSummaryDisplay.test.tsx) and unit tests in [sessionUtils.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/utils/sessionUtils.test.ts) to verify correct handling/resolution of both unquoted and quoted session identifiers.

### Verification
- Executed Vitest unit tests to confirm `SessionSummaryDisplay` and `SessionSelector` behave correctly.
- Confirmed that the ESLint static code analyzer passed cleanly with zero errors on the modified files.
