## Commit Message

[SSR Agent] Issue Fix (23230): Reset sequence model when exiting plan mode

## PR Description

fixes #23230
Original issue: https://github.com/google-gemini/gemini-cli/issues/23230

### Context & Problem
Exiting plan mode did not switch the active model immediately within the same interaction turn sequence. This occurred because although `setApprovalMode` correctly fired the `ApprovalModeChanged` event, the `GeminiClient` did not handle setting `currentSequenceModel` to null, resulting in subsequent model calls in the same sequence using the sticky cached Pro model instead of re-evaluating routing.

### Detailed Changes
- **`packages/core/src/config/config.ts`**: Emitted the `ApprovalModeChanged` event if the mode changes.
- **`packages/core/src/utils/events.ts`**: Defined `ApprovalModeChangedPayload` and added support for the `ApprovalModeChanged` event in `CoreEventEmitter`.
- **`packages/core/src/core/client.ts`**: Registered a listener for `ApprovalModeChanged` and reset `this.currentSequenceModel` to `null` if the event corresponds to the current session. Also unsubscribed the event listener upon disposal.
- **`packages/core/src/core/client.test.ts`**: Added a comprehensive unit test to verify that emitting `ApprovalModeChanged` on the current session correctly resets the sequence model on `GeminiClient` and triggers model re-routing.

### Verification
- Static eslint verification checks completed and passed successfully.
- Added robust Vitest unit tests to prevent regressions.
