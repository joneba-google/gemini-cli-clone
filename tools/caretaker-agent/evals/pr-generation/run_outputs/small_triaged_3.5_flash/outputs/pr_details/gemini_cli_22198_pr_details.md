## Commit Message

[SSR Agent] Issue Fix (22198): Fix tracker task storage directory path

## PR Description

fixes #22198
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/22198

### Context & Problem

Tracker task files were being stored directly under the project temp directory instead of within the session-specific temporary directory. This prevented proper session-level isolation and automatic cleanup behaviors.

### Detailed Changes

- **packages/core/src/config/storage.ts**: Updated `getProjectTempTrackerDir()` to check for `this.sessionId` and dynamically return a session-isolated tracker subdirectory if present, falling back to the project-wide tracker directory if not.
- **packages/core/src/config/storage.test.ts**: Added two unit tests to verify `getProjectTempTrackerDir()` generates the correct path both with and without a defined session ID.

### Verification

The added unit tests successfully verify the isolated path behavior. The Vitest test suite and ESLint checks have executed and passed without issues.
