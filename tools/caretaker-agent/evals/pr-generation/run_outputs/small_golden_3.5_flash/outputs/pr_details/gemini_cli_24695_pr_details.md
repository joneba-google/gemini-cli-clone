## Commit Message

[SSR Agent] Issue Fix (24695): Reject numeric Google Cloud Project IDs during setup

## PR Description

fixes #24695
Original issue URL: https://github.com/google-gemini/gemini-cli/issues/24695

### Context & Problem
Setting a purely numeric Google Cloud Project Number (e.g., in `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_PROJECT_ID`) instead of an alphanumeric Project ID causes a general 400 'Request contains an invalid argument' error from the Gemini API upstream.

### Detailed Changes
- Exported a new error class `InvalidNumericProjectIdError` in [setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24695/tmp/eval/gemini-cli/packages/core/src/code_assist/setup.ts).
- Added logic inside `setupUser` to validate that the resolved project ID is not purely numeric using `/^\d+$/`. If it is purely numeric, we now throw `InvalidNumericProjectIdError` early.
- Added comprehensive unit tests in [setup.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24695/tmp/eval/gemini-cli/packages/core/src/code_assist/setup.test.ts) to verify early rejection of numeric project IDs for both `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_PROJECT_ID`.

### Verification
- Verified that all linter checks succeeded.
- Verified that the unit tests correctly assert throwing of `InvalidNumericProjectIdError` under the target conditions.
