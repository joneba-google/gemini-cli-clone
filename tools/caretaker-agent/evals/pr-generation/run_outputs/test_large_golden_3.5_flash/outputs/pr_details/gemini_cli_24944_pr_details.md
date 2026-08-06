## Commit Message

[SSR Agent] Issue Fix (24944): Filter background tools from confirmation queue count

## PR Description

fixes #24944
https://github.com/google-gemini/gemini-cli/issues/24944

### Context & Problem
The `update_topic` tool is an auto-executing background operation, but it was incorrectly included in the tool confirmation queue size calculation in the UI, causing misleading counts (e.g., '1 of 2') when only one actionable tool required approval. This occurred because `getConfirmingToolState` calculated the pending confirmation queue size using `allPendingTools.length` without filtering out background or non-actionable tools like `UPDATE_TOPIC_TOOL_NAME`, while tool visibility rules were fragmented across multiple modules.

### Detailed Changes
- **Core Library (`@google/gemini-cli-core`)**:
  - A centralized `packages/core/src/utils/tool-visibility.ts` module was created to implement visibility rules via `belongsInConfirmationQueue`, `isRenderedInHistory`, and `isVisibleInToolGroup`.
  - The visibility utility functions and types are exported via `packages/core/src/index.ts`.
  - Outdated static functions (`shouldHideToolCall`) were removed from `packages/core/src/utils/tool-utils.ts` and corresponding tests were cleaned up in `packages/core/src/utils/tool-utils.test.ts`.
  - New comprehensive tests were added in `packages/core/src/utils/tool-visibility.test.ts`.
- **CLI (`@google/gemini-cli`)**:
  - `belongsInConfirmationQueue` was integrated into `getConfirmingToolState` inside `packages/cli/src/ui/utils/confirmingTool.ts` to filter out background tools from the confirmation queue count.
  - The `buildToolVisibilityContextFromDisplay` helper was added in `packages/cli/src/ui/utils/historyUtils.ts`.
  - `ToolGroupMessage.tsx` and `useGeminiStream.ts` were refactored to consume the standard core visibility functions instead of fragmented logic or raw inline checks.

### Verification
- An ESLint check was executed on the modified files and successfully passed.
- Comprehensive unit tests covering `belongsInConfirmationQueue`, `isRenderedInHistory`, and `isVisibleInToolGroup` behavior were added in `tool-visibility.test.ts`.
