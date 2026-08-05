## Commit Message

[SSR Agent] Issue Fix (25655): Prevent double rendering of SessionStart hook systemMessage

## PR Description

fixes #25655
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25655

### Context & Problem
When a `SessionStart` hook returned a `systemMessage`, the Gemini CLI rendered the message twice: once during the session startup and again after running the `clear` command. This occurred because `HookEventHandler` emits a `CoreEvent.HookSystemMessage` that was handled automatically, but `AppContainer.tsx` and `clearCommand.ts` were also manually appending `result.systemMessage` to `historyManager` and the UI display, leading to double-rendering.

### Detailed Changes

- **packages/cli/src/ui/AppContainer.tsx**: Removed the redundant manual append to `historyManager` for `result.systemMessage` following `fireSessionStartEvent` execution.
- **packages/cli/src/ui/commands/clearCommand.ts**: Removed the redundant manual append to `context.ui` for `result.systemMessage` following `fireSessionStartEvent` execution.
- **packages/cli/src/test-utils/polyfill-file.ts**: Created a helper file to polyfill the Web standard `File` API using `node:buffer` in Node.js environments lacking global `File` definition.
- **packages/cli/test-setup.ts**: Cleaned up the imports order to ensure no executable code blocks occur before import statements.
- **packages/cli/src/ui/commands/clearCommand.test.ts**: Reordered imports to follow ESM boundaries and added unit tests to verify that `clearCommand` does not redundantly call `context.ui.addItem` when `fireSessionStartEvent` returns a `systemMessage`.

### Verification

- Successfully verified with a unit test assertion that `clearCommand` does not append messages to the UI if `fireSessionStartEvent` returns a `systemMessage`.
- Improved imports layout to satisfy standard ESLint conventions, avoiding executable statement hoisting warnings.
