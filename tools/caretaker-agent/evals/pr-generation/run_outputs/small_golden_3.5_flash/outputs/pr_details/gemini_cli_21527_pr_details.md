## Commit Message

[SSR Agent] Issue Fix (21527): Fix EISDIR errors when reading directories as files

## PR Description

fixes #21527
Original Issue: https://github.com/google-gemini/gemini-cli/issues/21527

### Context & Problem

The CLI crashed with EISDIR and call stack size exceeded errors when directory paths were treated and read as binary or normal text files. This occurred because the helper function `isBinaryFile` lacked directory checks and `read-many-files.ts` verified existence with `fsPromises.access` which resolves successfully for directories.

### Detailed Changes

- **fileUtils.ts**: Modified `isBinaryFile` to fetch file statistics using `fsPromises.stat` first. If the file path represents a directory (non-file), the function returns `false` early. Otherwise, it calls the library with the file size parameter: `isBinaryFileCheck(filePath, stats.size)`.
- **read-many-files.ts**: Replaced `fsPromises.access` path existence check with `fsPromises.stat` and set `exists` to `st.isFile()`, ensuring folders are ignored in file list candidates.
- **Polyfill & Test Setup**: Added a polyfill for `globalThis.File` in `packages/core/polyfill.cjs` and `packages/core/test-setup.ts` for environment robustness.
- **Test Coverage**: Added clean verification unit tests in `read-many-files.test.ts` and `fileUtils.test.ts` validating directory-skipping behavior.

### Verification

All corresponding unit and integration tests under the Vitest framework have been verified. Passed tests ensure directory structures are cleanly ignored.
