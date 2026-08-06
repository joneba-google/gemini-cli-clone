## Commit Message

[SSR Agent] Issue Fix (28048): Update LLMResponse usageMetadata in hooks reference documentation

## PR Description

fixes #28048
Original issue: https://github.com/google-gemini/gemini-cli/issues/28048

### Context & Problem

The hook reference documentation for `LLMResponse.usageMetadata` incorrectly documented the object as containing only the `totalTokenCount` property. However, in practice, hooks actually receive promptTokenCount and candidatesTokenCount as well.

### Detailed Changes

The schema definition block for **LLMResponse** under `LLMResponse.usageMetadata` in [docs/hooks/reference.md](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28048/tmp/eval/gemini-cli/docs/hooks/reference.md) has been updated. The single property definition `totalTokenCount` has been replaced with the complete and expanded configuration containing:
- `promptTokenCount`
- `candidatesTokenCount`
- `totalTokenCount`

### Verification

- The reference documentation in [docs/hooks/reference.md](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28048/tmp/eval/gemini-cli/docs/hooks/reference.md) was manually reviewed to verify layout and schema syntax correctness.
- Properties were verified post-change to ensure they perfectly align with the definitions and implementation within [packages/core/src/hooks/hookTranslator.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_28048/tmp/eval/gemini-cli/packages/core/src/hooks/hookTranslator.ts).
