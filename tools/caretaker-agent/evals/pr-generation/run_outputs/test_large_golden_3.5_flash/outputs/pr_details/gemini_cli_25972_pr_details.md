## Commit Message

[SSR Agent] Issue Fix (25972): Prevent CLI crashes on log and stack trace prompts

## PR Description

fixes #25972
Original Issue: https://github.com/google-gemini/gemini-cli/issues/25972

### Context & Problem
The CLI would crash with filesystem errors (such as `ENAMETOOLONG`) when user prompts contained test failure logs or stack traces. This occurred because the CLI incorrectly interpreted large log snippets or stack trace fragments containing markers like `AssertionError:` or `FAIL ` as path names and performed direct filesystem operations on them.

### Detailed Changes
- **Path Validation**: Added a robust path validation helper `validatePath` in `packages/core/src/utils/path-validator.ts` which rejects paths containing newline/control characters, log markers (`AssertionError:`, `FAIL `, etc.), suspicious quotes/ellipses, and paths exceeding length limits (`MAX_PATH_LENGTH = 4096`, `MAX_COMPONENT_LENGTH = 255`).
- **Path Extraction & Resolution**: Added `resolveAtCommandPath` and `tryExtractPath` in `packages/core/src/utils/atCommandUtils.ts` to extract valid embedded paths from log fragments.
- **Integration**:
  - Exported the new helper utilities from the core index.
  - Integration with `Config.validatePathAccess` to prevent arbitrary filesystem checks on suspect paths.
  - Refactored `resolveFilePaths` in the hooks `atCommandProcessor.ts` to utilize the safe `resolveAtCommandPath` resolution.
  - Refactored ACP session path resolution in `acpSession.ts` to call `resolveAtCommandPath` for safe file lookup.
- **Testing**:
  - Added intensive unit tests in `packages/core/src/utils/path-validator.test.ts` covering path validation and best-effort extraction from stack traces and logs.

### Verification
- Checked that linter (ESLint) ran successfully for all edited files with no warnings or errors.
- Verified test coverage is comprehensive for path sanitization and recovery logic.
