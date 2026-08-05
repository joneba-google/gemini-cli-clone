## Commit Message

[SSR Agent] Issue Fix (28052): Sanitize trailing periods from URLs in auth error messages

## PR Description

fixes #28052
Original issue: https://github.com/google-gemini/gemini-cli/issues/28052

### Context & Problem

When Google sign-in fails, the returned error message displays a URL with trailing punctuation (e.g. 'https://antigravity.google.'), which invalidates the web link.

### Detailed Changes

The agent modified the following files to strip trailing punctuation from error URLs:
- `packages/core/src/utils/errors.ts`: Added helper function `sanitizeUrls` and applied it inside `getErrorMessage` on string values to ensure any generated errors have sanitized URLs.
- `packages/cli/src/core/auth.ts`: Wrapped error messages in `sanitizeUrls` during authentication errors formatting.
- `packages/cli/src/ui/auth/useAuth.ts`: Sanitized authentication error messages in hooks.
- Added comprehensive unit tests in `packages/core/src/utils/errors.test.ts`, `packages/cli/src/core/auth.test.ts`, and `packages/cli/src/ui/auth/useAuth.test.tsx` to verify correct stripping of trailing punctuation without altering valid characters inside the URLs.

### Verification

Executed Vitest unit testing suites across:
- Core utilities: `errors.test.ts`
- CLI auth core and custom UI hook: `auth.test.ts`, `useAuth.test.tsx`
The static code verification and ESLint check succeeded without any errors.
