## Commit Message

[SSR Agent] Issue Fix (23410): Consistently reference lowercase default system prompt filename

## PR Description

fixes #23410
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/23410

### Context & Problem
The system prompt documentation in `docs/cli/system-prompt.md` inconsistently referenced the default system prompt filename as the uppercase `SYSTEM.md` and lowercase `system.md`. This was confusing because the CLI defaults to checking `.gemini/system.md` in lowercase when `GEMINI_SYSTEM_MD=1` is set.

### Detailed Changes
- Standardized references throughout `docs/cli/system-prompt.md` to consistently use the lowercase `system.md` filename instead of capitalized `SYSTEM.md`.
- Clarified that `.gemini/system.md` is the default lowercase path read when `GEMINI_SYSTEM_MD=1` is set.
- Updated shell examples and troubleshooting steps to refer to the lowercase path, standardizing the documentation.

### Verification
- Manually reviewed the document to verify that all inconsistent/uppercase references of `SYSTEM.md` (except reference to `DEFAULT_SYSTEM.md` output file) have been corrected to `system.md` or `.gemini/system.md`.
- No functional code changes were made, and linter check succeeded (ESLint was skipped because no TS/JS files were modified).
