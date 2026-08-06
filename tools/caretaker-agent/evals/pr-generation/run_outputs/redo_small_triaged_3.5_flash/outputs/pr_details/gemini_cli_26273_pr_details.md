## Commit Message

[SSR Agent] Issue Fix (26273): Fix extension installation from SSH repository URLs

## PR Description

fixes #26273

Original Issue: https://github.com/google-gemini/gemini-cli/issues/26273

### Context & Problem
Gemini CLI extensions could not be installed from repository URLs using `ssh://` or `git+ssh://` protocols, failing with an 'Install source not found' error. This occurred because the `inferInstallMetadata` function did not recognize SSH-related protocol schemes as git sources, causing them to be incorrectly treated as local paths.

### Detailed Changes
- Modified `inferInstallMetadata` in [extension-manager.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/redo_small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extension-manager.ts) to check for `ssh://` and `git+ssh://` URL prefixes when inferring installation source.
- Added comprehensive unit tests in [extension-manager.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/redo_small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extension-manager.test.ts) to verify the metadata inference works correctly for SSH repository URLs.

### Verification
- ESLint linting checks executed and verified in `linter_output.txt`.
- Unit tests added to explicitly verify behavior and they correctly assert that SSH URLs return type `git`.
