## Commit Message

[SSR Agent] Issue Fix (28048): Document LLMResponse usageMetadata properties

## PR Description

fixes #28048

Issue URL: https://github.com/google-gemini/gemini-cli/issues/28048

### Context & Problem

The documentation schema for `LLMResponse` in `docs/hooks/reference.md` was missing the `promptTokenCount` and `candidatesTokenCount` properties within `usageMetadata`, which are active and received by hooks at runtime.

### Detailed Changes

- **[reference.md](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_28048/tmp/eval/gemini-cli/docs/hooks/reference.md#L325-L333)**: Updated the documented `LLMResponse` schema representation for `usageMetadata` to accurately include all three properties (`promptTokenCount`, `candidatesTokenCount`, and `totalTokenCount`).
- **[hookTranslator.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_28048/tmp/eval/gemini-cli/packages/core/src/hooks/hookTranslator.test.ts#L438-L452)**: Added unit test assertions to test and verify that all three properties inside `usageMetadata` are translated correctly.

### Verification

The translator translator logic was verified against mock data under `packages/core/src/hooks/hookTranslator.test.ts` using the Vitest test framework. All tests execute successfully, and static analysis/eslint checks passed cleanly.
