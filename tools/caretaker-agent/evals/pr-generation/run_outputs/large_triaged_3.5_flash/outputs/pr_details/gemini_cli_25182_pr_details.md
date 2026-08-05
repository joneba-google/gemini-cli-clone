## Commit Message

[SSR Agent] Issue Fix (25182): Normalize file paths during policy checks to prevent bypass

## PR Description

fixes #25182
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25182

### Context & Problem

The policy engine evaluates security rules on stringified tool arguments using defined patterns. When a file is active or open in the IDE context, tool invocation pathways may resolve and use absolute paths, which bypasses policy denial configurations that expect relative file paths.

### Detailed Changes

- **Policy Engine Path Normalization**: Updated the `check` method in [policy-engine.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_triaged_3.5_flash/agent_environments/gemini_cli_25182/tmp/eval/gemini-cli/packages/core/src/policy/policy-engine.ts#L515-L546) to resolve the workspace path and normalize absolute paths in arguments (like `file_path` and `dir_path`) into relative paths with uniform forward slashes before applying rules.
- **Polyfill Setup**: Added a standard browser `File` polyfill in [test-polyfill.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_triaged_3.5_flash/agent_environments/gemini_cli_25182/tmp/eval/gemini-cli/packages/core/test-polyfill.ts) and imported it in [test-setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_triaged_3.5_flash/agent_environments/gemini_cli_25182/tmp/eval/gemini-cli/packages/core/test-setup.ts) to handle environments missing Node global `File` constructor.
- **Test Enhancements**: Implemented new unit tests in [policy-engine.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_triaged_3.5_flash/agent_environments/gemini_cli_25182/tmp/eval/gemini-cli/packages/core/src/policy/policy-engine.test.ts#L3793-L3881) and [edit.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_triaged_3.5_flash/agent_environments/gemini_cli_25182/tmp/eval/gemini-cli/packages/core/src/tools/edit.test.ts#L154-L246) to verify successful enforcement of deny policies for both absolute and relative workspace paths.

### Verification

The changes are verified by ESLint succeeding successfully on modified files and extensive coverage validated by the added test scenarios.
