## Commit Message

[SSR Agent] Issue Fix (24501): Fix visual analysis with computer-use expression models

## PR Description

fixes #24501
Issue URL: https://github.com/google-gemini/gemini-cli/issues/24501

### Context & Problem
The `analyze_screenshot` tool in the browser agent fails to return visual results and encounters `400 INVALID_ARGUMENT` or empty responses when used with computer-use models like `gemini-2.5-computer-use-preview-10-2025`. This is because computer-use models require a `computerUse` tool declaration in every request, and standard response parsing in the system was discarding any `functionCall` parts returned by the model.

### Detailed Changes
- **Model Detection**: Created a `isComputerUseModel` helper and `COMPUTER_USE_MODEL_PATTERN` in [modelAvailability.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_24501/tmp/eval/gemini-cli/packages/core/src/agents/browser/modelAvailability.ts) to identify computer-use capable models.
- **Tool Declaration**: In [analyzeScreenshot.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_24501/tmp/eval/gemini-cli/packages/core/src/agents/browser/analyzeScreenshot.ts), conditionally built a `tools` array configured with `Environment.ENVIRONMENT_BROWSER` and Action exclusions to pass to `generateContent` when computer-use models are used.
- **Enhanced Response Parsing**: Updated response-parsing logic in [analyzeScreenshot.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_24501/tmp/eval/gemini-cli/packages/core/src/agents/browser/analyzeScreenshot.ts) to parse, filter, and structure both `text` and `functionCall` components into clean text output.
- **Test Coverage**: Updated positive tests and added new unit tests in [analyzeScreenshot.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_24501/tmp/eval/gemini-cli/packages/core/src/agents/browser/analyzeScreenshot.test.ts) to verify correct `tools` declaration omitted for non-computer-use models, included for computer-use models, and that dual components-parsing works as expected.

### Verification
- Checked that linter (ESLint) passed on all modified files.
- Verified that all unit tests correctly execute and validate standard as well as computer-use configurations.
