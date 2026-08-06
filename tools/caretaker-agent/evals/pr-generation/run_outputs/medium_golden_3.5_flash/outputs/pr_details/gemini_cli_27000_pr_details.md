## Commit Message

[SSR Agent] Issue Fix (27000): Map Gemini 3.1 models in DEFAULT_MODEL_CONFIGS

## PR Description

fixes #27000

Original Issue: https://github.com/google-gemini/gemini-cli/issues/27000

### Context & Problem
Attempting to prompt Gemini 3.1 models (such as `gemini-3.1-pro-preview`) resulted in an `INVALID_ARGUMENT (400)` API Error because they were requested without the required `thinkingLevel` parameter. This occurred because Gemini 3.1 models were absent from the configuration registry in `DEFAULT_MODEL_CONFIGS`, preventing them from extending the `chat-base-3` template configuration where the suitable default is defined.

### Detailed Changes
- Added configurations for `gemini-3.1-pro-preview`, `gemini-3.1-pro-preview-customtools`, and `gemini-3.1-flash-lite-preview` in [defaultModelConfigs.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_27000/tmp/eval/gemini-cli/packages/core/src/config/defaultModelConfigs.ts), mapping them to extend `chat-base-3`.
- Added unit tests in [models.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_27000/tmp/eval/gemini-cli/packages/core/src/config/models.test.ts) to verify that `modelConfigService.getResolvedConfig` successfully resolves with a defined `thinkingLevel` of `'HIGH'` in `generateContentConfig`'s `thinkingConfig` block.
- Updated golden snapshot files `resolved-aliases-retry.golden.json` and `resolved-aliases.golden.json` to include correct configuration mapping resolution for the new models.

### Verification
- Executed Vitest unit tests in [models.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_27000/tmp/eval/gemini-cli/packages/core/src/config/models.test.ts) confirming successful validation of resolved model configurations.
- Verified that all ESLint pre-commit checks succeeded without errors.
