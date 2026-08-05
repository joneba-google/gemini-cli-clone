## Commit Message

[SSR Agent] Issue Fix (28106): Defer editor settings initialization to avoid Windows startup delay

## PR Description

fixes #28106
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/28106

### Context & Problem
During the initialization of Gemini CLI on Windows, a severe startup delay of over 50 seconds occurs because the interactive CLI bundle eagerly instantiates [EditorSettingsManager](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L20-L54) at the top level of the ESM module. This constructor synchronously runs [hasValidEditorCommand](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L9) for all 16+ editor types via synchronous shell calls, blocking the main thread.

### Detailed Changes
- Refactored [EditorSettingsManager](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L20-L54) in [editorSettingsManager.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts) to remove eager command check loops from the constructor.
- Introduced a lazy loader pattern for the [availableEditors](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L21) property, initializing it to `null`.
- Updated [getAvailableEditorDisplays](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L23-L53) to check, populate (with [hasValidEditorCommand](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L9) and [allowEditorTypeInSandbox](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L8)), cache, and return available editor displays on demand.
- Implemented comprehensive Vitest unit tests in [editorSettingsManager.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.test.ts) to assert that:
  - Instantiation does not call [hasValidEditorCommand](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L9).
  - The first call to [getAvailableEditorDisplays](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L23-L53) executes the check while subsequent calls return the cached response.
  - Editor displays are accurately mapped according to installation and sandbox-allowance status.

### Verification
- Executed Vitest unit tests to ensure that [EditorSettingsManager](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts#L20-L54) behaves correctly, loads lazily, and caches as expected.
- Verified that all static scans and linter rules pass.
