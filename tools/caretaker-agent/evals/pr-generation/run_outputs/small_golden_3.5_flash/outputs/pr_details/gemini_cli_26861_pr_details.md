## Commit Message

[SSR Agent] Issue Fix (26861): Remove redundant session quoting and fix quoted ID parsing

## PR Description

fixes #26861
https://github.com/google-gemini/gemini-cli/issues/26861

### Context & Problem
When closing a session, the resume session message is printed with unnecessary enclosing double quotes on Windows/PowerShell. Furthermore, the session resolver was unable to parse session IDs wrapped in quotes, preventing users from copy-pasting the resume command directly.

### Detailed Changes
- [SessionSummaryDisplay.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/ui/components/SessionSummaryDisplay.tsx): Removed the conditional `isWindows()` check that wrapped session IDs in extra double-quotes.
- [SessionSummaryDisplay.test.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/ui/components/SessionSummaryDisplay.test.tsx): Updated tests to verify that the session summary message renders without surrounding quotes.
- [sessionUtils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/utils/sessionUtils.ts): Updated `resolveSession` to strip matching enclosing single or double quotes surrounding the session ID.
- [sessionUtils.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_26861/tmp/eval/gemini-cli/packages/cli/src/utils/sessionUtils.test.ts): Added tests verifying that `resolveSession` correctly parses and loads wrapped session IDs.

### Verification
- Checked that human-written unit tests covering the session ID quote stripping behavior were successfully integrated.
- Verified ESLint rules passed for all edited files via the pre-executed linter results saved in `linter_output.txt`.
