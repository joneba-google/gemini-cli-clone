## Commit Message

[SSR Agent] Issue Fix (23410): Consistently use lowercase system.md in system prompt documentation

## PR Description

fixes #23410
Original issue: https://github.com/google-gemini/gemini-cli/issues/23410

### Context & Problem
The system prompt documentation page inconsistently referred to the default system prompt markdown file as both `SYSTEM.md` and `system.md`. This causes confusion on case-sensitive filesystems, where the actual default filename is lowercase `system.md`.

### Detailed Changes
Modified [docs/cli/system-prompt.md](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_23410/tmp/eval/gemini-cli/docs/cli/system-prompt.md) to consistently use lowercase `system.md` in all headers, bullet points, file examples, and descriptions, while preserving the uppercase `GEMINI.md` references.

### Verification
Manually verified that all specified occurrences of `SYSTEM.md` in [docs/cli/system-prompt.md](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_23410/tmp/eval/gemini-cli/docs/cli/system-prompt.md) were correctly renamed to `system.md`, and that `GEMINI.md` is preserved as uppercase. Since this was a documentation change, no TypeScript/JavaScript source code was modified, and the lint checks were skipped successfully.
