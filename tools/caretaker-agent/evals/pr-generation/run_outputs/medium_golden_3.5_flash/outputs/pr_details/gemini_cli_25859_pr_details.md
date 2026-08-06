## Commit Message

[SSR Agent] Issue Fix (25859): Prefer PowerShell 7 on Windows to preserve double quotes

## PR Description

fixes #25859
Original issue URL: https://github.com/google-gemini/gemini-cli/issues/25859

### Context & Problem

On Windows, `run_shell_command` incorrectly strips double quotes from commands because it defaults to Windows PowerShell 5.1 (`powershell.exe`), which drops inline double quotes when passing arguments to native executables.

### Detailed Changes

- **Synchronous Executable Resolution**: Refactored `resolveExecutable` from asynchronous to synchronous in `packages/core/src/utils/shell-utils.ts` utilizing `fs.accessSync` under the hood. Added an internal helper `isExecutable`.
- **PowerShell 7 Preference**: Updated `getShellConfiguration()` on Windows to try resolving `pwsh.exe` via `resolveExecutable` synchronously before falling back to `powershell.exe`.
- **Reference Updates**: Updated references to `resolveExecutable` in `packages/core/src/services/shellExecutionService.ts` and `packages/core/src/tools/ripGrep.ts` to be synchronous.
- **Test Coverage**: Updated unit tests in `shellExecutionService.test.ts`, `shell-utils.test.ts`, and `ripGrep.test.ts` to align with synchronous resolution and mocked `fs.accessSync`. Added a new integration test file `packages/core/src/services/shellExecutionService.windows.integration.test.ts` to assert that complex commands with nested double quotes preserve quotes correctly.

### Verification

All Vitest unit testing suites and integration mock configurations succeed, ensuring seamless cross-platform shell compatibility.
