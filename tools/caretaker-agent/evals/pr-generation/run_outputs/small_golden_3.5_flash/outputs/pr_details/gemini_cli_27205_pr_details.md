## Commit Message

[SSR Agent] Issue Fix (27205): Pass fileService to getFolderStructure in activate-skill

## PR Description

fixes #27205
Original issue URL: https://github.com/google-gemini/gemini-cli/issues/27205

### Context & Problem

The Gemini CLI automatically mapped and shared the entire local `.venv` directory (and other ignored directories) inside custom skills regardless of `.gitignore` or `.geminiignore` rules. This occurred because `getFolderStructure(path.dirname(skillLocation))` was invoked in `activate-skill.ts` without passing a `fileService` option, which prevented proper filtering of ignored patterns.

### Detailed Changes

- **packages/core/src/tools/activate-skill.ts**: Updated the `getFolderStructure` invocation inside the `ActivateSkillToolInvocation` class to pass `{ fileService: this.config.getFileService() }` as options. This ensures that custom-ignore filters are properly resolved and applied.
- **packages/core/src/tools/activate-skill.test.ts**: Added a Vitest unit test verifying that `ActivateSkillTool` retrieves the `fileService` from the configuration object and passes it to `getFolderStructure`.

### Verification

- The new and existing custom skill activation test cases have been verified using Vitest framework.
- The ESLint checks completed successfully with no errors in the modified files.
