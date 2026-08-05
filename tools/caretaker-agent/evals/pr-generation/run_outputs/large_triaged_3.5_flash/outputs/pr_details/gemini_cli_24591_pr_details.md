## Commit Message

[SSR Agent] Issue Fix (24591): Prevent node memory flags relaunch in standalone SEA binary

## PR Description

fixes #24591
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/24591

### Context & Problem
Running the compiled Single Executable Application (SEA) binary directly causes CLI argument parsing errors ("Unknown arguments: max-old-space-size, maxOldSpaceSize") if the memory re-launcher calculates a target heap limit higher than the current default state. When relaunching, Node memory flags are erroneously passed as CLI arguments to the binary executable instead of Node itself, which are then rejected by the `yargs` parser.

### Detailed Changes
- **packages/cli/src/gemini.tsx**: Updated the `getNodeMemoryArgs` helper to check if `process.env.IS_BINARY === 'true'` alongside `process.env.GEMINI_CLI_NO_RELAUNCH`. If `true`, it immediately returns an empty array, preventing memory CLI arguments from being generated for relaunching.
- **packages/cli/src/gemini.test.tsx**: Added a new unit test asserting that a relaunch is not performed (an empty array is returned) when `process.env.IS_BINARY` is `'true'`. Added environmental clean-up to prevent side effects in other tests.
- **packages/cli/test-polyfill.ts**: Added a file polyfill to define `globalThis.File` under Node environments when undefined.
- **packages/cli/test-setup.ts**: Imported the newly added file polyfill.

### Verification
- Executed unit tests in `packages/cli/src/gemini.test.tsx` verifying that `process.env.IS_BINARY === 'true'` bypasses the memory relaunch logic, returning `[]` successfully.
