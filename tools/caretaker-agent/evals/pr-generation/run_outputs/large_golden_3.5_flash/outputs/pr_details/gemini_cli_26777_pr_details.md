## Commit Message

[SSR Agent] Issue Fix (26777): Resolve system ripgrep when bundled binary is missing

## PR Description

fixes #26777

Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26777

### Context & Problem
The getRipgrepPath() function only checked hardcoded paths relative to the bundle's directory structure. If the bundled binaries were missing, it failed to resolve a valid ripgrep executable and fell back to GrepTool, even when ripgrep was installed on the user's system.

### Detailed Changes
- Replaced `getRipgrepPath()` with an exported helper `resolveRipgrepPath()` function in [ripGrep.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_26777/tmp/eval/gemini-cli/packages/core/src/tools/ripGrep.ts).
- Integrated a system search fallback using `resolveExecutable('rg')` from the shell utility module when bundled binaries are absent.
- Implemented robust security validation: resolved canonical paths using `resolveToRealPath()`, rejected executables under the current working directory, and restricted allowed paths to standard trusted directories across platforms.
- Created helper function `isTrustedSystemPath()` in [shell-utils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_26777/tmp/eval/gemini-cli/packages/core/src/utils/shell-utils.ts) to filter trusted platform paths.
- Added thorough test coverage in [ripGrep.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_26777/tmp/eval/gemini-cli/packages/core/src/tools/ripGrep.test.ts), covering environment scenarios, fallback, CWD rejection, and OS compatibility.

### Verification
Static evaluation, linter outputs, and standard Vitest unit tests in [ripGrep.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_26777/tmp/eval/gemini-cli/packages/core/src/tools/ripGrep.test.ts) were executed and verified to pass.
