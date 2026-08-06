## Commit Message

[SSR Agent] Issue Fix (19868): Prevent directories in custom ignore paths from crashing CLI

## PR Description

fixes #19868
Original Issue: https://github.com/google-gemini/gemini-cli/issues/19868

### Context & Problem
Text completion for files and directories breaks when using `@` after adding directories (such as `node_modules/`, `temp/`, `cache/`) to the `context.fileFiltering.customIgnoreFilePaths` setting inside settings.json. The root cause is `fs.existsSync()` checking that returned true for directories, leading to an uncaught `EISDIR` error when trying to read them as files.

### Detailed Changes
- **packages/core/src/services/fileDiscoveryService.ts**: Replaced the `.gitignore` existence check with `fs.statSync()` to ensure the target path is specifically a file before pushing it.
- **packages/core/src/utils/filesearch/ignore.ts**: Wrapped the `fs.readFileSync` call within `loadIgnoreRules` in a try-catch block to gracefully skip unreadable filesystem paths.
- **packages/core/src/utils/ignoreFileParser.ts**: Updated `getIgnoreFilePaths()` to replace `fs.existsSync()` with `fs.statSync()?.isFile()` to filter out custom ignore directories.
- **packages/core/src/services/fileDiscoveryService.test.ts**: Added robust unit tests to verify directory filtering and that non-crash behavior remains intact.

### Verification
All tests in `fileDiscoveryService.test.ts` pass successfully. The linter checks also completed with success on all modified files and code sections.
