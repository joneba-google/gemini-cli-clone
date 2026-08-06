## Commit Message

[SSR Agent] Issue Fix (25693): Fix skill loader parsing for single line descriptions

## PR Description

fixes #25693

Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/25693

### Context & Problem
The skill discovery process failed to find local skills defined in `SKILL.md` when the `description` in the frontmatter was written on a single line, or if the file started with a UTF-8 BOM, or contained trailing whitespace after the triple-dash markers. Additionally, the fallback simple frontmatter parser was brittle, failing to handle case-insensitive keys or whitespace around colons, and could swallow valid properties into the description if subsequent keys were indented.

### Detailed Changes
- **Regular Expression Update**: Updated `FRONTMATTER_REGEX` in `packages/core/src/skills/skillLoader.ts` to support an optional UTF-8 Byte Order Mark (`\uFEFF`) at the beginning, and optional trailing horizontal whitespace (`[ \t]*`) after the start/end triple-dash boundaries (`---`).
- **Fallback Parser Robustness**:
  - Modified `parseSimpleFrontmatter` in `packages/core/src/skills/skillLoader.ts` to perform case-insensitive matching (`/i`) on keys and allow optional whitespace before and after the colon separator.
  - Refined the multi-line description parser's continuation condition to verify that the next line does not match standard keys like `name` or `description` before appending it to the description list.
- **Improved Testing**:
  - Added comprehensive unit tests in `packages/core/src/skills/skillLoader.test.ts` covering UTF-8 BOM, trailing whitespaces in markers, case-insensitivity/spacing, and prevention of key-swallowing under the fallback parsing path.

### Verification
- Running `Vitest` unit tests successfully verifies these changes. The linter checks also passed successfully for the modified files.
