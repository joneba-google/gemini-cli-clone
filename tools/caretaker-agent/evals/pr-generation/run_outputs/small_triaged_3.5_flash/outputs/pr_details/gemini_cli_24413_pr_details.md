## Commit Message

[SSR Agent] Issue Fix (24413): Use dynamic CLI version instead of hardcoded '1.0.0'

## PR Description

fixes #24413
Original issue: https://github.com/google-gemini/gemini-cli/issues/24413

### Context & Problem

The `IdeClient` was hardcoding the client version string to '1.0.0' when instantiating MCP Client instances for both HTTP and STDIO connections instead of using the dynamic CLI version.

### Detailed Changes

- **packages/core/src/ide/ide-client.ts**:
  - Imported `getVersion` from `../utils/version.js`.
  - Retrieved the dynamic CLI version asynchronously using `await getVersion()` in both connection setup methods: `establishHttpConnection` and `establishStdioConnection`.
  - Passed the resolved dynamic version to the `Client` constructor.
  - Removed outdated TODO comments.

- **packages/core/src/ide/ide-client.test.ts**:
  - Mocked the `getVersion` utility function in test suite and mocked its resolved value to `'1.2.3'`.
  - Added assertions to verify both `streamable-http-client` and `stdio-client` are instantiated with the correct dynamic version string.

- **packages/core/test-setup.ts**:
  - Added a global polyfill/mock for `File` when it is undefined in the test execution environment to prevent environment setup issues.

### Verification

- Successfully ran Vitest unit tests in `packages/core/src/ide/ide-client.test.ts` to assert correct mock connection setup and Client call arguments.
- Verified that the codebase passes the ESLint lint checking without any errors.
