## Commit Message

[SSR Agent] Issue Fix (28106): Lazily compute available editors to prevent startup delay

## PR Description

fixes #28106
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/28106

### Context & Problem

The Gemini CLI suffered from severe startup delays (50s to over 1.5 minutes) on Windows. This occurred during the ESM import of the main interactive UI module, where eager module-level instantiation of the `EditorSettingsManager` synchronously ran environment checks for more than 16 editor types via `execSync`.

### Detailed Changes

- Refactored `EditorSettingsManager` in [editorSettingsManager.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.ts) to lazily evaluate and cache available editors.
  - Exported the class definition.
  - Made the `availableEditors` array nullable (`EditorDisplay[] | null`).
  - Moved the scanning logic to a new private method `computeAvailableEditors()`.
  - Kept the constructor side-effect-free (empty).
  - Lazily initialized and cached the result on the first call to `getAvailableEditorDisplays()`.
- Added comprehensive unit tests in [editorSettingsManager.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_28106/tmp/eval/gemini-cli/packages/cli/src/ui/editors/editorSettingsManager.test.ts) to verify that import and instantiation do not trigger checks and that lazy loading, sorting, caching, and formatting work reliably.

### Verification

All unit tests successfully run and pass via Vitest, confirming correct behaviour and elimination of startup delays.
