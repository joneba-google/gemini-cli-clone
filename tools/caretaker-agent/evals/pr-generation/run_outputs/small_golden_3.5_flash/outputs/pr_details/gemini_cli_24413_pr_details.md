## Commit Message

[SSR Agent] Issue Fix (24413): Use dynamic CLI version for IDE client

## PR Description

fixes #24413
Original issue: https://github.com/google-gemini/gemini-cli/issues/24413

### Context & Problem

The [ide-client.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/src/ide/ide-client.ts) initialization hardcoded the connection version string parameter to `'1.0.0'` in both HTTP/SSE and STDIO connection establishment methods. Consequently, the IDE client did not report its actual active integration version dynamic CLI value resolved via the `getVersion` utility.

### Detailed Changes

- **Core connection updates**: Modified [ide-client.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/src/ide/ide-client.ts) to import `getVersion` and `await getVersion()` while instantiating [Client](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/src/ide/ide-client.ts#L590-L593) for `StreamableHTTPClientTransport` and [Client](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/src/ide/ide-client.ts#L624-L627) for `StdioClientTransport`.
- **Test coverage**: Updated [ide-client.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/src/ide/ide-client.test.ts) to mock `getVersion`, and asserted that the instantiated `Client` parameters contain the mocked dynamic version for both connection methods.
- **Polyfill handling**: Added a standard global `File` polyfill in [test-setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24413/tmp/eval/gemini-cli/packages/core/test-setup.ts) to ensure tests pass in environments where `globalThis.File` is not natively available.

### Verification

- **Linting**: Static code quality checks verified via ESLint. All checks completed successfully with no violations.
- **Unit Tests**: Mock checks and assertions implemented in the test suite ensure that the correct version returned by `getVersion()` is passed upstream to the constructor during Client initialization under both transport mechanisms.
