## Commit Message

[SSR Agent] Issue Fix (26777): Fall back to system ripgrep when bundled files are missing

## PR Description

fixes #26777
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26777

### Context & Problem

When `@google/gemini-cli` is installed globally without bundled ripgrep binaries, the `getRipgrepPath()` function fails to return a path even if ripgrep is installed globally and is present in the system PATH. This makes ripgrep unavailable to the tool.

### Detailed Changes

- **packages/core/src/tools/ripGrep.ts**:
  - Updated `getRipgrepPath()` to look up system `rg` using platform-specific commands (`where rg` on Windows, `which rg` on POSIX) when bundled binaries are missing.
  - Implemented a robust manual PATH directory search fallback to locate `rg` or `rg.exe` directly from the OS environment `PATH` variable when command executors fail or are absent.
- **packages/core/src/tools/ripGrep.test.ts**:
  - Added comprehensive unit tests evaluating fallback paths: verifying POSIX (`which`), Win32 (`where`), manual PATH fallback, and returning `null` when all resolution attempts fail.

### Verification

- The existing unit test suite in `packages/core/src/tools/ripGrep.test.ts` was extended with mocked file system and execution checks, ensuring 100% path coverage for the fallback lookup logic under all major platform modes.
- Linter checks (ESLint) completed successfully without any errors.
