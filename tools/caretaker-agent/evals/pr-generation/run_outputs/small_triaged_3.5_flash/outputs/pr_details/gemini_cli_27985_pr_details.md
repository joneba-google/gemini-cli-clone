## Commit Message

[SSR Agent] Issue Fix (27985): Populate cached and thought tokens in ACP PromptResponse usage

## PR Description

fixes #27985

### Context & Problem
When running in ACP server mode (`gemini --acp`), token usage reported in `PromptResponse` omitted cached and thought tokens from the Gemini `usageMetadata`. This caused ACP clients to overestimate costs because they did not receive complete usage statistics about cached content token counts and thought token counts.

### Detailed Changes
- **Session Prompt Initialization**: Updated the `prompt` method inside [acpSession.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27985/tmp/eval/gemini-cli/packages/cli/src/acp/acpSession.ts) to track `totalCachedReadTokens` and `totalThoughtTokens`.
- **Turn Initialization**: Initialized `turnCachedReadTokens` and `turnThoughtTokens` alongside standard input/output tokens in the prompt loop.
- **Finished Event Handling**: Updated the `GeminiEventType.Finished` stream event handler to extract and fallback-assign `cachedContentTokenCount` and `thoughtsTokenCount` from `usageMetadata`.
- **Response Population**: Ensured that standard ACP `usage` schema properties (`inputTokens`, `outputTokens`, `cachedReadTokens`, `thoughtTokens`, and `totalTokens`) are correctly populated in all `PromptResponse` object returns (for early exit and loop completion conditions).
- **Unit Tests**: Added comprehensive test cases in [acpSession.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27985/tmp/eval/gemini-cli/packages/cli/src/acp/acpSession.test.ts) to verify the returned `PromptResponse` contains the correct standard ACP `usage` properties with matching mock stream token metrics.

### Verification
- **Linter Status**: Checked and verified that ESLint completed successfully on the edited files.
- **Tests**: Automated Vitest check verifies successful message stream mock simulation with token-usage verification.

### Original Issue
- URL: https://github.com/google-gemini/gemini-cli/issues/27985
