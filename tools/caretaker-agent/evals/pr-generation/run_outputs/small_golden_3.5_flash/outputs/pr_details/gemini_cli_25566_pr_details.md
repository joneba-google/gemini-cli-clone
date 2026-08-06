## Commit Message

[SSR Agent] Issue Fix (25566): Gracefully fallback when custom plans directory is outside project root

## PR Description

fixes #25566
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25566

### Context & Problem

When a custom plans directory is configured outside the project root, validation in `this.storage.getPlansDir()` throws an error. Because `Config._initialize()` calls this method directly without catching the validation error, the CLI crashes on startup with an unhandled exception / promise rejection.

### Detailed Changes

- **packages/core/src/config/config.ts**:
  - Wrapped `this.storage.getPlansDir()` in a `try-catch` block during initialization.
  - Enacted a fallback mechanism where any validation errors are caught, a warning is emitted via `coreEvents.emitFeedback`, the custom plans directory is reset to `undefined`, and `plansDir` falls back to the default project temp directory.
- **packages/core/src/config/config.test.ts**:
  - Added unit test to verify that standard initialization gracefully falls back to the default project temp directory when a custom plans directory is invalid or outside the project root.
  - Updated existing assertions to match spy expectations exactly.

### Verification

- Successfully executed Vitest unit tests verifying correct warning logs and fallback behavior.
- Confirmed that the ESLint checks completed without any errors or warnings on any edited files.
