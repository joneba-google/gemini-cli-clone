## Commit Message

[SSR Agent] Issue Fix (27205): Ignore .venv and respect local ignore rules in skills

## PR Description

fixes #27205
Original issue: https://github.com/google-gemini/gemini-cli/issues/27205

### Context & Problem

When activating custom skills, Gemini CLI aggressively scanned `.venv` folders, flooding the LLM context with virtual environment files. Additionally, it failed to respect local `.gitignore` or `.geminiignore` rules within the skill directory because a local `FileDiscoveryService` was not initialized and passed for the skill path.

### Detailed Changes

- **getFolderStructure.ts**: Added `.venv` to the list of `DEFAULT_IGNORED_FOLDERS` to ignore Python virtual environments by default.
- **activate-skill.ts**: Initialized a new instance of `FileDiscoveryService` targeting the skill directory (`path.dirname(skillLocation)`) and passed it to `getFolderStructure` under the `{ fileService }` option parameter.
- **getFolderStructure.test.ts**: Added unit tests using Vitest to verify that `.venv` is ignored by default and that local `.gitignore`/`.geminiignore` rules are respected during folder structure generation.

### Verification

- ESLint checks passed successfully.
- Vitest unit tests were added and successfully executed to verify default exclusion of `.venv` and enforcement of local ignore files.
