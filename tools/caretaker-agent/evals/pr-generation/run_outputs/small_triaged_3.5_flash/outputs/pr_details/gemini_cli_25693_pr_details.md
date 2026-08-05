## Commit Message

[SSR Agent] Issue Fix (25693): Fix frontmatter single-line description parsing with unquoted colons

## PR Description

fixes #25693
https://github.com/google-gemini/gemini-cli/issues/25693

### Context & Problem
Local skills discovery fails when the description field in frontmatter of SKILL.md is a single line containing unquoted punctuation or colons. Due to the unquoted colons/special characters, compiling via js-yaml fails. When falling back, the parseFrontmatter function delegates to parseSimpleFrontmatter, which previously failed to cleanly parse, sanitize, or unquote single-line description values.

### Detailed Changes
- Added [safeString](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.ts#L34-L39) and [stripSurroundingQuotes](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.ts#L41-L50) utility helpers inside [skillLoader.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.ts) to clean up and normalize names and descriptions.
- Updated [parseFrontmatter](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.ts#L59-L82) to stringify and trim fields correctly even if parsed as non-string metadata.
- Updated [parseSimpleFrontmatter](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.ts#L88-L140) to strip surrounding quotes from single-line descriptions and trim/coerce both the name and description correctly.
- Added extensive test coverage inside [skillLoader.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_25693/tmp/eval/gemini-cli/packages/core/src/skills/skillLoader.test.ts#L272-L345) covering single-line descriptions containing unquoted punctuation & colons, quoted descriptions requiring stripping, and non-string numeric values.

### Verification
- Checked that unit tests pass successfully under Vitest, ensuring correct discovery of skills regardless of description formatting.
- Verified ESLint rules run with zero violations under ESLint checks.
