## Commit Message

[SSR Agent] Issue Fix (26777): Resolve ripgrep from system PATH when bundled binary missing

## PR Description

fixes #26777
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26777

### Context & Problem
The previous `getRipgrepPath()` function failed to find the ripgrep executable (`rg`) when bundled binary files were missing because it only checked hardcoded paths. This agent has refactored the function to fall back to searching the system's PATH environment variable while strictly validating paths for safety.

### Detailed Changes

#### Packages Core (`packages/core/src/tools/ripGrep.ts`)
* Replaced the `getRipgrepPath()` function with `resolveRipgrepPath()`.
* Implemented `isTrustedSystemPath()` to validate system-resolved paths based on OS-specific standard binary paths.
* Integrated the shell utility `resolveExecutable('rg')` to safely locate external ripgrep executables.
* Enforced canonical path resolution via `resolveToRealPath` (or `path.win32.resolve` on Windows) and added strict security checks to filter out paths located within the current working directory to prevent potential Remote Code Execution (RCE) or path manipulation attacks.
* Updated `canUseRipgrep()`, `ensureRgPath()`, and `GrepToolInvocation.execute()` to utilize `resolveRipgrepPath()`.

#### Test Suite (`packages/core/src/tools/ripGrep.test.ts`)
* Renamed imports and test invocations to target `resolveRipgrepPath()`.
* Created a comprehensive test suite mocking bundled binary file absence and validating trusted system path detection, Homebrew cellar paths on macOS, and path rejection when configured inside the current working directory (CWD) on Unix and Windows OS.

### Verification
All unit tests for RipGrep have been added to `packages/core/src/tools/ripGrep.test.ts` and successfully passed using Vitest. Additionally, the static code quality checks (ESLint) ran on all modified files and succeeded without error, as verified by the linter output.
