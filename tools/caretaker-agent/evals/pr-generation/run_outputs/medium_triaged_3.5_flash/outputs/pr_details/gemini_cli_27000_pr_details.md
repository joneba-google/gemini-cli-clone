## Commit Message

[SSR Agent] Issue Fix (27000): Add missing Gemini 3.1 model configurations

## PR Description

fixes #27000
Issue URL: https://github.com/google-gemini/gemini-cli/issues/27000

### Context & Problem
Requests made using the `gemini-3.1-pro-preview` model fail with an API error 400 (`INVALID_ARGUMENT`) because the models are missing from `DEFAULT_MODEL_CONFIGS.aliases` in [defaultModelConfigs.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_27000/tmp/eval/gemini-cli/packages/core/src/config/defaultModelConfigs.ts). This causes a fallback to `chat-base`, which enables thinking (`includeThoughts: true`) without setting the mandatory `thinkingLevel` required for Gemini 3.1 models.

### Detailed Changes
- Added missing alias definitions for `gemini-3.1-pro-preview`, `gemini-3.1-pro-preview-customtools`, and `gemini-3.1-flash-lite-preview` under `DEFAULT_MODEL_CONFIGS.aliases` extending `chat-base-3`.
- This ensures correct model mapping and specifies the appropriate `thinkingLevel: ThinkingLevel.HIGH` by extending `chat-base-3`.
- Updated test goldens in `packages/core/src/services/test-data/resolved-aliases.golden.json` and `packages/core/src/services/test-data/resolved-aliases-retry.golden.json` to include the correct thinking level logic for these new models.

### Verification
- Validated TypeScript/ESLint status using pre-run linter output from `linter_output.txt` which succeeded without errors.
- Verified test behavior updates in the core package's golden test data configuration files.
