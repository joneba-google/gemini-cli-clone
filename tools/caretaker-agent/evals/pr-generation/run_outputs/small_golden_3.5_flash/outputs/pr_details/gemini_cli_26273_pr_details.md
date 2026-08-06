## Commit Message

[SSR Agent] Issue Fix (26273): Support installing extensions from ssh:// repository URLs

## PR Description

fixes #26273
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26273

### Context & Problem
Installing an extension from a git repository with an SSH URL (e.g., 'ssh://url.domain.com') fails with an "Install source not found" error because the extension manager's URL validation does not recognize the `ssh://` protocol prefix.

### Detailed Changes
- Updated `packages/cli/src/config/extension-manager.ts`:
  - Added support for the `ssh://` protocol prefix by adding `source.startsWith('ssh://')` to the validation logic in the `inferInstallMetadata` function.
- Updated `packages/cli/src/config/extension-manager.test.ts`:
  - Added unit tests to verify that `ssh://` URLs are correctly identified as git source types.
  - Added unit tests to cover standard protocols identified as git source types.

### Verification
The changes have been verified through:
- Unit tests added to `packages/cli/src/config/extension-manager.test.ts` to test parsing of `ssh://` URLs.
- Successful ESLint checking as documented in `linter_output.txt`.
