## Commit Message

[SSR Agent] Issue Fix (24874): Disable terminalBuffer by default and fix rendering regressions

## PR Description

fixes #24874
Issue URL: https://github.com/google-gemini/gemini-cli/issues/24874

### Context & Problem
Using terminal buffer mode causes performance regressions with long chat histories. To address this, terminal buffer mode needs to be disabled by default, and several rendering regressions for non-terminal buffer mode must be resolved (e.g., rendering artifacts on virtualization and missing truncation indicators).

### Detailed Changes
- **Configuration Defaults**: Changed the default value of `terminalBuffer` / `ui.terminalBuffer` from `true` to `false` in `packages/cli/src/config/settingsSchema.ts`, `packages/core/src/config/config.ts`, and `schemas/settings.schema.json`.
- **Interactive CLI**: Updated `renderProcess` activation in `startInteractiveUI` (`packages/cli/src/interactiveCli.tsx`) to only trigger when both terminal buffer and render process are enabled.
- **Input Prompt Component**: Modified `packages/cli/src/ui/components/InputPrompt.tsx` to conditionally render a directly-sliced sub-array of `scrollableData` using React fragments instead of virtualized `ScrollableList` when outside terminal buffer mode.
- **Tool Result Display Component**: Updated array rendering in `packages/cli/src/ui/components/messages/ToolResultDisplay.tsx` to slice and display visible lines via `MaxSizedBox` instead of `ScrollableList` when `isAlternateBuffer` is false.
- **MaxSizedBox Layout**: Adjusted the checks in `packages/cli/src/ui/components/shared/MaxSizedBox.tsx` to retain truncation indicators when hidden lines are present even if `effectiveMaxHeight` is undefined.
- **Testing**: Added unit test in `packages/cli/src/ui/components/messages/ToolResultDisplay.test.tsx` verifying that outputs correctly stay scrolled to the bottom in non-alternate-buffer mode.

### Verification
- Executed Vitest tests in `packages/cli/src/ui/components/InputPrompt.test.tsx` and `packages/cli/src/ui/components/messages/ToolResultDisplay.test.tsx`.
- Ensured correctness and verified success of the test suite verifying that `ToolResultDisplay` stays scrolled to the bottom as lines are incrementally added.
