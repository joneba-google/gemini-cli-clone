## Commit Message

[SSR Agent] Issue Fix (24874): Set terminalBuffer to false by default and fix regressions

## PR Description

fixes #24874
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/24874

### Context & Problem

The default setting of `terminalBuffer` to `true` has caused significant performance regressions on systems with long chat histories. Additionally, virtualized components like `ScrollableList` resulted in rendering regressions when running outside alternate buffer/terminal buffer modes.

### Detailed Changes

- **packages/cli/src/config/settingsSchema.ts**, **packages/core/src/config/config.ts**, and **schemas/settings.schema.json**: Changed default value of `terminalBuffer` to `false`.
- **packages/cli/src/interactiveCli.tsx**: Updated `renderProcess` to activate only when both `config.getUseRenderProcess()` and `config.getUseTerminalBuffer()` are `true`.
- **packages/cli/src/ui/components/InputPrompt.tsx**: Implemented slice rendering of `scrollableData` with React Fragments instead of using `ScrollableList` when `isAlternateBuffer` is false.
- **packages/cli/src/ui/components/messages/ToolResultDisplay.tsx**: Switched to using `MaxSizedBox` and direct rendering of `visibleLines` (with proper hidden line counts calculated) in non-alternate buffer mode instead of utilizing virtualized list components.
- **packages/cli/src/ui/components/shared/MaxSizedBox.tsx**: Retained truncation indicators when `totalHiddenLines > 0` even when `effectiveMaxHeight` is undefined.
- **Test Updates**: Added test coverage in `InputPrompt.test.tsx` and updated existing test snapshots/expectations to align with the new non-alternate buffer rendering behavior.

### Verification

Vitest tests were verified and passed successfully in `packages/cli/src/ui/components/InputPrompt.test.tsx` and `packages/cli/src/ui/components/messages/ToolResultDisplay.test.tsx`.
