## Commit Message

[SSR Agent] Issue Fix (23230): Clear cached model when exiting plan mode

## PR Description

fixes #23230
Original Issue: https://github.com/google-gemini/gemini-cli/issues/23230

### Context & Problem
When plan mode is enabled, the agent was staying stuck on the Pro model even after exiting plan mode. This happened because `GeminiClient` caches the selected model in `currentSequenceModel` to maintain multi-turn model consistency, but failed to reset/clear this cache upon transition.

### Detailed Changes
* **packages/core/src/core/client.ts**: Added a public method `clearCurrentSequenceModel()` to reset `currentSequenceModel` to `null`.
* **packages/core/src/config/config.ts**: Invoked `clearCurrentSequenceModel()` during plan/yolo mode transitions if the Gemini client is initialized.
* **integration-tests/plan-mode.test.ts**: Added a new integration test `should switch model to flash immediately after exiting plan mode` with mock responses to verify the correct sequence of model requests (pro request followed by flash request post-exit).

### Verification
The added integration test verifies that the model switches from a 'pro' model to a 'flash' model immediately after exiting/confirming plan mode, ensuring the bug is completely resolved. All ESLint and static analysis checks succeeded with no errors.
