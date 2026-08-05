## Commit Message

[SSR Agent] Issue Fix (24501): Fix screenshot tool and parsing for computer-use models

## PR Description

fixes #24501
Original Issue: https://github.com/google-gemini/gemini-cli/issues/24501

### Context & Problem
The `analyze_screenshot` tool in the browser agent fails with computer-use models (e.g., `gemini-2.5-computer-use-preview-10-2025`) because they require a `computerUse` tool declaration in the configuration to avoid `400 INVALID_ARGUMENT` errors. Additionally, computer-use models return `functionCall` response parts instead of plain text, which are ignored by the current parser, resulting in empty visual analysis errors.

### Detailed Changes
- **packages/core/src/agents/browser/analyzeScreenshot.ts**:
  - Detected when a computer-use model is in use by checking if the model name contains `'computer-use'`.
  - Conditioned the inclusion of the `computerUse` tool declaration (with empty `excludedPredefinedFunctions`) on whether a computer-use model is targetted, ensuring standard vision models do not receive it.
  - Updated the response parsing loop to defensively extract both text and `functionCall` parts (stringified), avoiding empty responses when `functionCall` parts are returned.

### Verification
- Added Vitest unit tests to [analyzeScreenshot.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_24501/tmp/eval/gemini-cli/packages/core/src/agents/browser/analyzeScreenshot.test.ts) covering:
  - Injection of the `computerUse` tool declaration when calling with a computer-use model.
  - Absence of the tool declaration when using standard vision models.
  - Successful extraction and JSON-stringifying of `functionCall` parts from the model output.
