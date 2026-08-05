## Commit Message

[SSR Agent] Issue Fix (25566): Prevent crash when plans directory is outside project root

## PR Description

fixes #25566
Issue URL: https://github.com/google-gemini/gemini-cli/issues/25566

### Context & Problem

The CLI crashed on startup with an unhandled promise rejection if `planSettings.directory` was configured to a path outside the project root. This occurred because the path validation checks in `this.storage.getPlansDir()` were executed outside of catch block handlers during initial configuration setup, and during session updates.

### Detailed Changes

- **packages/core/src/config/config.ts**:
  - Moved the `this.storage.getPlansDir()` invocation inside the `try/catch` block of `Config._initialize()`.
  - Added safe `try/catch` error wrapping around `this.storage.getPlansDir()` within `setSessionId` and `refreshSessionScopedPlansDirectory` to prevent uncaught exceptions when session updates occur with an invalid custom plans directory.
- **packages/core/src/config/config.test.ts**:
  - Added a unit test to verify that Config initialization succeeds without throwing even when `planSettings.directory` is configured to a path outside the project root.
  - Added a unit test to verify that updating sessions succeeds without throwing when an invalid plans directory is configured.

### Verification

The changes have been verified via ESLint checks which succeeded, and corresponding unit tests added to check config initialization and session updates with an invalid plans directory.
