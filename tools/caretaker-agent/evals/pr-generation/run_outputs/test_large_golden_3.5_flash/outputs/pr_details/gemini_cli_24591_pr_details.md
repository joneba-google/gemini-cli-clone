## Commit Message

[SSR Agent] Issue Fix (24591): Fix SEA relaunch option parsing via NODE_OPTIONS

## PR Description

fixes #24591
Issue URL: https://github.com/google-gemini/gemini-cli/issues/24591

### Context & Problem
When running the Gemini CLI in Single Executable Application (SEA) mode, restarting the process with Node.js runtime arguments (such as `--max-old-space-size`) caused runtime flag arguments to be passed directly to the application's CLI parser (yargs) as unknown arguments. This occurred because `process.execPath` is the binary itself, which forwards all arguments to the application instead of consuming them as Node.js runtime flags.

### Detailed Changes
The agent implemented robust SEA detection, argument slicing, and process relaunch configuration utilities:
- **[processUtils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/test_large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/processUtils.ts)**:
  - Implemented `isSeaEnvironment()`, `isStandardSea()`, `getScriptArgs()`, and `getSpawnConfig()` to cleanly support process relaunch under standard Node.js vs. SEA.
  - SEA mode relaunch now feeds runtime Node options securely through the `NODE_OPTIONS` environment variable after verifying that arguments do not contain risky shell-escapable characters (whitespaces, quotes, or backslashes).
  - Configured `getScriptArgs()` to slice `argv` from index 1 for standard SEA, and from index 2 for standard/relaunched modes, preventing compounding arguments.
- **[index.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/test_large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/index.ts)** & **[relaunch.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/test_large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/relaunch.ts)**:
  - Replaced ad-hoc process/argv slicing and child process spawning parameters with calls to the new process utility helper functions.
- **[processUtils.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/test_large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/processUtils.test.ts)**:
  - Added new comprehensive tests covering standard vs. SEA mode detection, argument slicing, and environment construction.
- **[test-setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/test_large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/test-setup.ts)**:
  - Defined a fallback `File` constructor in test environments where `global.File` is undefined.

### Verification
- Static analysis checks and ESLints have completed successfully without warnings on edited files.
- New unit tests targets for standard and SEA execution behavior have been validated.
