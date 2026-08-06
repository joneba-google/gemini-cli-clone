## Commit Message

[SSR Agent] Issue Fix (26021): Auto-allow configured MCP servers in headless mode

## PR Description

fixes #26021

Original Issue: https://github.com/google-gemini/gemini-cli/issues/26021

### Context & Problem
MCP servers configured in settings are not available in non-interactive/headless mode (using `-p`) because tool authorization rules for configured MCP servers are not automatically registered, preventing headless execution from functioning without interactive prompt confirmation.

### Detailed Changes
- **packages/core/src/policy/types.ts**: Added an optional `autoAllowInHeadless` boolean flag to the `mcp` object type definition of the `PolicySettings` interface.
- **packages/core/src/policy/config.ts**: Implemented logic in `createPolicyEngineConfig` to automatically generate policy allow rules for configured MCP servers when running in headless mode (`!interactive`), provided `settings.mcp?.autoAllowInHeadless` is enabled. It avoids duplicate rule creation by skipping any MCP servers that are already explicitly allowed, covered under the `'*'` wildcard permissions, or marked with `trust: true`.
- **packages/core/src/policy/config.test.ts**: Written a comprehensive Vitest suite verifying auto-allow rule generation under headless execution, exclusion of rules when interactive is enabled, and correct duplicate-avoidance behavior.
- **packages/core/test-setup.ts**: Polyfilled `globalThis.File` to enable compatibility in the test suite context.

### Verification
- All tests specified under `packages/core/src/policy/config.test.ts` pass successfully using Vitest.
- The ESLint static check ran on the modified files and succeeded without any linting errors or warnings.
