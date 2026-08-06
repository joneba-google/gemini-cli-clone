## Commit Message

[SSR Agent] Issue Fix (28052): Sanitize URLs in error messages by stripping trailing periods

## PR Description

fixes #28052
Original Issue: https://github.com/google-gemini/gemini-cli/issues/28052

### Context & Problem

When an interactive sign-in error occurs, the error message sometimes contains a URL with an extra trailing period (e.g., `https://antigravity.google.`). This dangling period makes the URL invalid and prevents it from loading correctly in several environments and browsers.

### Detailed Changes

- **errors.ts** (`packages/core/src/utils/errors.ts`):
  - Refactored `getErrorMessage` to store the parsed error message in a local `message` variable.
  - Sanitized the message using a safe regular expression `/https?:\/\/[^\s]+/g` to find all URLs and strip trailing period characters sequentially.
- **errors.test.ts** (`packages/core/src/utils/errors.test.ts`):
  - Added unit tests verifying that `getErrorMessage` correctly sanitizes both `Error` objects and raw strings containing URLs with trailing periods.

### Verification

- Unit tests in `packages/core/src/utils/errors.test.ts` have been added to verify that error messages with trailing period URLs ('https://antigravity.google.') are properly sanitized to 'https://antigravity.google'.
- ESLint checks have succeeded for the edited files without any errors.
