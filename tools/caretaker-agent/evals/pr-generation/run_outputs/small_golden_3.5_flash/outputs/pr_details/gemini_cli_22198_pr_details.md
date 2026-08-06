## Commit Message

[SSR Agent] Issue Fix (22198): Isolate tracker task paths using active session ID

## PR Description

fixes #22198
Original Issue: https://github.com/google-gemini/gemini-cli/issues/22198

### Context & Problem
Tracker tasks were previously stored directly under the project's temporary directory without considering the active session. This could cause collisions and read/write conflicts across multiple concurrent sessions running in the same project.

### Detailed Changes
- [storage.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_22198/tmp/eval/gemini-cli/packages/core/src/config/storage.ts): Updated the `getProjectTempTrackerDir` method under the `Storage` class to inspect `this.sessionId`. If a session ID is present, it returns a path nested within the session-specific folder (i.e. `path.join(this.getProjectTempDir(), this.sessionId, 'tracker')`), keeping tasks isolated. Otherwise, it falls back to the default tracker directory.
- [storage.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_22198/tmp/eval/gemini-cli/packages/core/src/config/storage.test.ts): Added two unit tests to verify the behavior of `getProjectTempTrackerDir` both when `sessionId` is present and when it is absent.

### Verification
The changes and newly added unit tests were verified with the Vitest testing framework and the codebase linter check passed successfully.
