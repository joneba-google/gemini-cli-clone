## Commit Message

[SSR Agent] Issue Fix (26273): Fix extension installation from SSH repository

## PR Description

fixes #26273
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26273

### Context & Problem
The Gemini extension manager attempts to identify and download extensions via GitHub releases API using [tryParseGithubUrl](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extensions/github.ts#L87). However, it incorrectly parses SSH repository URLs (both standard and SCP-style) as standard GitHub URLs, which causes the application to run into API-based release download flows. As a result, extension installation from an SSH repository fails.

### Detailed Changes
- In [extension-manager.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extension-manager.ts), introduced a guard condition `isSshUrl` to check if the extension's source starts with `git@`, `ssh://`, or `git+ssh://`. This ensures SSH-style installation metadata bypasses [tryParseGithubUrl](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extensions/github.ts#L87) and falls back directly to [cloneFromGit](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extensions/github.ts#L31).
- In [extension-manager.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_26273/tmp/eval/gemini-cli/packages/cli/src/config/extension-manager.test.ts), added unit test cases covering both SCP-style and standard SSH repository URLs to verify they skip download from GitHub release and verify git clone behavior.

### Verification
- ESLint checks ran successfully without errors.
- Unit testing coverage was added for Git SSH extension installation.
