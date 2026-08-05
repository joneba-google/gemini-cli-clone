## Commit Message

[SSR Agent] Issue Fix (24944): Exclude background tools from confirming tool queue calculations

## PR Description

fixes #24944
Original issue: https://github.com/google-gemini/gemini-cli/issues/24944

### Context & Problem

The `getConfirmingToolState` function was incorrectly including non-confirming, auto-executing background tools (like `update_topic`) in the overall confirmation queue size calculations. This led to misleading numbers in the UI (e.g. '1 of 2') when only one tool actually required user confirmation.

### Detailed Changes

- **packages/cli/src/ui/utils/confirmingTool.ts**:
  - Restructured `getConfirmingToolState` to calculate the queue size (`total`) and 1-based index (`index`) strictly using the size and indices within the filtered list of `confirmingTools` rather than the `allPendingTools` list.
- **packages/cli/src/ui/utils/confirmingTool.test.ts**:
  - Added robust unit test coverage to:
    - Verify that `null` is returned when no tools are awaiting approval.
    - Verify that background tools are filtered and excluded from the count.
    - Verify correct `index` and `total` calculations when multiple confirming tools are present.
- **packages/cli/src/test-utils/polyfill.ts**:
  - Added a global polyfill for `globalThis.File` under Node 18 environments to prevent Undici reference errors during testing.
- **packages/cli/test-setup.ts**:
  - Imported the polyfill to avoid `ReferenceError` issues in Vitest.

### Verification

Complete unit test coverage for confirming tools has been written and verified successfully inside the Vitest framework. The ESLint check succeeded without issues.
