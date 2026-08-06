## Commit Message

[SSR Agent] Issue Fix (24944): Prevent update_topic tool from inflating confirmation queue count

## PR Description

fixes #24944
Original Issue: https://github.com/google-gemini/gemini-cli/issues/24944

### Context & Problem
The `update_topic` tool is an auto-executing background operation, but it was incorrectly included in the tool confirmation queue size calculation in the UI. This led to misleading counts in the CLI tool confirmation queue (e.g., "1 of 2") when only one actionable tool actually requires approval.

### Detailed Changes
- **Core Package Utilities**: Created [tool-visibility.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/core/src/utils/tool-visibility.ts) which defines `ToolVisibilityContext`, `buildToolVisibilityContext`, `isRenderedInHistory`, `belongsInConfirmationQueue`, and `isVisibleInToolGroup`. It filters out the background operation `update_topic` from the confirmation queue count.
- **Export and Clean Up**: Removed obsolete `shouldHideToolCall` from [tool-utils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/core/src/utils/tool-utils.ts) and exported the new `tool-visibility` utilities from the main core library entry point.
- **CLI UI Integration**: Refactored CLI UI modules, updating the tool confirmation queue size selection in [confirmingTool.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/cli/src/ui/utils/confirmingTool.ts), tool rendering visibility in [useGeminiStream.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/useGeminiStream.ts), and visible list grouping logic in [ToolGroupMessage.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/cli/src/ui/components/messages/ToolGroupMessage.tsx).
- **Testing**: Added unit tests in [tool-visibility.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24944/tmp/eval/gemini-cli/packages/core/src/utils/tool-visibility.test.ts) covering and asserting all cases, ensuring `belongsInConfirmationQueue` filters auto-executing background tools correctly.

### Verification
All unit tests in `packages/core/src/utils/tool-visibility.test.ts` pass, and linter check succeeded on edited files.
