## Commit Message

[SSR Agent] Issue Fix (25859): Use EncodedCommand for PowerShell execution on Windows

## PR Description

fixes #25859
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25859

### Context & Problem

On Windows, executing shell commands containing internal double quotes with `powershell.exe -Command` causes those quotes to be stripped or mangled by Windows process spawning and PowerShell argument parsing.

### Detailed Changes

* Added the helper function `encodePowerShellCommand` in [shell-utils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_25859/tmp/eval/gemini-cli/packages/core/src/utils/shell-utils.ts) to convert command strings into UTF-16LE Base64 strings.
* Updated `getShellConfiguration` in [shell-utils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_25859/tmp/eval/gemini-cli/packages/core/src/utils/shell-utils.ts) to accept a `useEncodedCommand` flag, switching the argument prefix from `-Command` to `-EncodedCommand` when appropriate.
* Modified `ShellExecutionService` in [shellExecutionService.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_25859/tmp/eval/gemini-cli/packages/core/src/services/shellExecutionService.ts) to detect when running under non-strict PowerShell on Windows, retrieve the `-EncodedCommand` configuration, and Base64 UTF-16LE encode the command before spawning.
* Added corresponding unit tests in [shell-utils.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_25859/tmp/eval/gemini-cli/packages/core/src/utils/shell-utils.test.ts) and [shellExecutionService.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_25859/tmp/eval/gemini-cli/packages/core/src/services/shellExecutionService.test.ts) to verify the PowerShell execution path, command encoding, and correct argument format.

### Verification

* Static analysis and linter checks run and succeeded with zero errors.
* Unit tests verify correct UTF-16LE Base64 encoding.
* Spawn tests verify correct PowerShell execution paths and arguments.
