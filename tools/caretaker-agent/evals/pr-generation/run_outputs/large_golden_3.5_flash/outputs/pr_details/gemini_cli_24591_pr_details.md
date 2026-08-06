## Commit Message

[SSR Agent] Issue Fix (24591): Support Node arguments via NODE_OPTIONS during SEA relaunch

## PR Description

fixes #24591
Issue URL: https://github.com/google-gemini/gemini-cli/issues/24591

### Context & Problem
When running Gemini CLI as a Single Executable Application (SEA), Node.js runtime arguments (such as `--max-old-space-size`) passed during process relaunch are treated as command-line arguments and passed to yargs, causing an "Unknown arguments: max-old-space-size, maxOldSpaceSize" error. This is because in SEA mode, `process.execPath` (the executable binary) forwards all command-line arguments directly to the application parser instead of consuming them as Node.js runtime flags.

### Detailed Changes
- Modified [processUtils.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/processUtils.ts) to export utility functions: `isSeaEnvironment()`, `isStandardSea()`, `getScriptArgs()`, and `getSpawnConfig()` to handle process relaunch parameters correctly in standard and SEA environments.
- Updated `getSpawnConfig()` to propagate Node.js options to the `NODE_OPTIONS` environment variable when running in a SEA mode, while validating that options do not contain any unsafe/unescaped characters.
- Modified [index.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/index.ts) and [relaunch.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/relaunch.ts) to use `getScriptArgs()` and `getSpawnConfig()` rather than custom process argument parsing and slicing, preventing argument compounding.
- Added comprehensive unit tests in [processUtils.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/large_golden_3.5_flash/agent_environments/gemini_cli_24591/tmp/eval/gemini-cli/packages/cli/src/utils/processUtils.test.ts) covering both standard Node.js environments and SEA environments.

### Verification
Tests were successfully executed and verified using the Vitest framework. The tests confirm that the relaunch configuration maps arguments to `NODE_OPTIONS` under SEA conditions and throws the expected error when unsupported characters are passed.
