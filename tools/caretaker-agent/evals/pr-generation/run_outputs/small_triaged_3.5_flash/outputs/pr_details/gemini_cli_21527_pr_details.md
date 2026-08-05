## Commit Message

[SSR Agent] Issue Fix (21527): Fix directory checks and recursion in @ commands

## PR Description

fixes #21527
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/21527

### Context & Problem
Referencing directory paths (such as skill directories) via `@` commands caused `EISDIR` warnings from `isBinaryFile` and infinite call stack exhaustion crashes in `handleAtCommand`.

### Detailed Changes
- **packages/core/src/utils/fileUtils.ts**: Checked directories early in `isBinaryFile` using stats to prevent `fs.open` from throwing warnings.
- **packages/core/src/tools/read-many-files.ts**: Filtered out directories in `ReadManyFilesTool` before invocation and type detection.
- **packages/cli/src/ui/hooks/atCommandProcessor.ts**: Prevented infinite recursion and duplicate directory/file path expansion by keeping track of resolved paths with `visitedPaths` `Set`.
- **packages/cli/test-setup.ts & vitest.config.ts**: Polyfilled `globalThis.File` for node compatibility during unit tests.
- **packages/core/src/utils/fileUtils.test.ts**: Added a unit test verifying `isBinaryFile` handles directories gracefully by returning `false`.

### Verification
- Passes Vitest unit tests including the new test coverage in `packages/core/src/utils/fileUtils.test.ts`.
