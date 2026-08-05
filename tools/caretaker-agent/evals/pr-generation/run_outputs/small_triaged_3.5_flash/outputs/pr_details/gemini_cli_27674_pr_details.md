## Commit Message

[SSR Agent] Issue Fix (27674): Prevent git-ignored directories from appearing in session context

## PR Description

fixes #27674

Original Issue: https://github.com/google-gemini/gemini-cli/issues/27674

### Context & Problem

Files and folders specified in `.gitignore` were still included in the session context folder structure. While ignored files were properly skipped, directories marked as ignored by `FileDiscoveryService` were loaded as truncated placeholders with a trailing `...` instead of being completely excluded.

### Detailed Changes

- **getFolderStructure.ts**: Updated the folder reading logic in `readFullStructure`. We now process top-level explicitly configured ignored directories (`ignoredFolders`) first to output truncated folder representations. For folders matched by the `FileDiscoveryService` directory ignoring filters (such as `.gitignore`), we completely skip directory processing rather than creating truncated folder entries.
- **getFolderStructure.test.ts**: Added a unit test validating that directories matched by `.gitignore` (e.g. `.ruff_cache`, `.venv`) are completely excluded from the printed workspace structure, while regular ignored folders like `node_modules` continue to be shown as truncated placeholders.

### Verification

The correctness of this change has been verified via the newly added unit test using the Vitest runner. Additionally, the workspace codebase has been checked for syntax and style correctness via the project's ESLint linter suite, which finished successfully with zero errors.
