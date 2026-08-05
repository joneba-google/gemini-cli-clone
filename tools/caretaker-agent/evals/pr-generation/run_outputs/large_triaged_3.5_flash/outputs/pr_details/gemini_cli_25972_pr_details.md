## Commit Message

[SSR Agent] Issue Fix (25972): Handle unresolvable @ path-like references gracefully

## PR Description

fixes #25972
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/25972

### Context & Problem
When user prompts contain '@' followed by path-like text, 'atCommandProcessor.ts' misinterprets these tokens as '@path' file inclusion commands. When resolving non-existent paths, file lookup or glob search failures throw errors and crash/interrupt query processing.

### Detailed Changes
- Wrapped path resolution logic block inside `resolveFilePaths()` and permission checks in `checkPermissions()` with `try-catch` blocks.
- Captured errors gracefully, logged them as warnings, and bypassed non-existent / alias paths to fall back to the original literal text.
- Introduced a polyfill/fallback definition for globalThis.File in testing environments.
- Added a unit test verifying unresolvable paths do not crash the CLI.

### Verification
- Executed unit tests in `atCommandProcessor.test.ts`. This confirms `handleAtCommand` successfully falls back to treating `query` with non-existent `@` references as literal text and processes it correctly.
