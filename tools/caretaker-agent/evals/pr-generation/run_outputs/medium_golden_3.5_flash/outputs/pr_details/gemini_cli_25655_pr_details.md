## Commit Message

[SSR Agent] Issue Fix (25655): Fix session start hook systemMessage duplicate rendering

## PR Description

fixes #25655
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25655

### Context & Problem

When a SessionStart hook emits a systemMessage, it renders twice at session start — once with a command source annotation tag and once without. This happens because `AppContainer` was directly invoking `historyManager.addItem` for the system message upon completing the session start event while also receiving the same message via the event-bus listener.

### Detailed Changes

- **packages/cli/src/ui/AppContainer.tsx**: Removed the direct `historyManager.addItem` invocation for `result.systemMessage` inside the session start `useEffect` block, and removed the associated `eslint-disable` comment for `react-hooks/exhaustive-deps`.
- **packages/core/src/hooks/hookEventHandler.ts**: Updated the check from `if (result.output?.systemMessage && result.outputFormat === 'json')` to `if (result.output?.systemMessage)` so that hook system messages are emitted to the event bus for both JSON and text formats.
- **packages/cli/src/ui/AppContainer.test.tsx**: Added a unit test to verify that the start of a session does not trigger direct history manager items.
- **packages/core/src/hooks/hookEventHandler.test.ts**: Added tests to check that system messages are emitted for both JSON and text output formats.

### Verification

Executed and verified tests:
- `AppContainer.test.tsx` (specifically the new test checking historyManager calls on session start)
- `hookEventHandler.test.ts` (specifically checking systemMessage emissions on both formats)
