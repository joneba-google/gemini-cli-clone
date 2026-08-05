## Commit Message

[SSR Agent] Issue Fix (26021): Initialize config to connect MCP servers in non-interactive mode

## PR Description

fixes #26021
Original Issue: https://github.com/google-gemini/gemini-cli/issues/26021

### Context & Problem

In non-interactive mode (such as passing a prompt with `-p` or piped stdin), MCP servers configured in `settings.json` are not connected because `config.initialize()` is bypassed. This results in 'Tool not found' errors when trying to invoke tools registered via MCP.

### Detailed Changes

- **packages/cli/src/nonInteractiveCli.ts**: Checked if `config.isInitialized()` is false, and awaited `config.initialize()` if so, right before setting up the scheduler and chat session.
- **packages/cli/src/nonInteractiveCliAgentSession.ts**: Checked if `config.isInitialized()` is false, and awaited `config.initialize()` if so, right before setting up the scheduler and chat session.
- **packages/cli/src/nonInteractiveCli.test.ts**: Added unit test cases verifying that `runNonInteractive` calls `config.initialize()` when `isInitialized` returns false, and does not call it when it returns true. Mocked the `string-width` module to avoid test failures.
- **packages/cli/test-setup.ts**: Mobbed the `string-width` module to prevent test execution issues.

### Verification

- Unit/integration test cases were added in `nonInteractiveCli.test.ts` verifying that `runNonInteractive` behaves correctly and only invokes `config.initialize()` when the config is not already initialized.
- A static and linter inspection indicates that ESLint check was successful for all edited files with zero issues.
