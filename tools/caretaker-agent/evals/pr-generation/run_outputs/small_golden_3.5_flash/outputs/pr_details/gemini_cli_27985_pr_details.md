## Commit Message

[SSR Agent] Issue Fix (27985): Support cached and thought tokens in ACP PromptResponse usage

## PR Description

fixes #27985
Original Issue: https://github.com/google-gemini/gemini-cli/issues/27985

### Context & Problem

When running as an ACP server, the per-turn token usage reported only included input and output tokens, omitting cached and thought/reasoning token counts, which inflated client cost estimates. Standard ACP clients (like OpenHands) assumed 0 cached read tokens and overstated actual spend by approximately 3x. Populating the standard `PromptResponse.usage` field was necessary for clients to obtain accurate estimates.

### Detailed Changes

- **`packages/cli/src/acp/acpSession.ts`**:
  - Moved accumulators `totalInputTokens` and `totalOutputTokens` to the top layer of `Session.prompt` and initialized `totalCachedTokens` and `totalThoughtTokens` alongside them.
  - Implemented the `buildUsage()` helper function to construct the standard `acp.Usage` payload incorporating cached and thought tokens.
  - Tracked turn-specific cached and thought tokens, extracted them from the `GeminiEventType.Finished` stream event, and added them to their cumulative accumulators on turn completion.
  - Updated all `PromptResponse` return paths across `Session.prompt` to include the standard `usage` metadata via `buildUsage()`.

- **`packages/cli/src/acp/acpSession.test.ts`**:
  - Added a new unit test `'reports token usage in the standard ACP usage field (incl. cached and thought tokens)'` to mock usage metadata (including cached and thought tokens) in a streaming response and verify that `Session.prompt` returns the expected standard usage values.

### Verification

Static code analysis and ESLint verification succeeded for all modified files.
