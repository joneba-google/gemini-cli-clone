## Commit Message

[SSR Agent] Issue Fix (27674): Omit ignored folders in directory context formatting

## PR Description

fixes #27674
Issue URL: https://github.com/google-gemini/gemini-cli/issues/27674

### Context & Problem
Folders and files designated by `.gitignore` were previously displayed as truncated entries in the chatbot's session context rather than being completely omitted. This consumed valuable token budget and included irrelevant information.

### Detailed Changes
- **[getFolderStructure.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27674/tmp/eval/gemini-cli/packages/core/src/utils/getFolderStructure.ts)**: Introduced the `showIgnoredFolders` flag (defaulting to `true` to preserve backward compatibility). When set to `false`, the directory traversal routine skips ignored directories completely instead of capturing them as truncated entries.
- **[environmentContext.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27674/tmp/eval/gemini-cli/packages/core/src/utils/environmentContext.ts)**: Configured `getFolderStructure` to invoke with `showIgnoredFolders: false` inside the session context generation.
- **[getFolderStructure.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27674/tmp/eval/gemini-cli/packages/core/src/utils/getFolderStructure.test.ts)** & **[environmentContext.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27674/tmp/eval/gemini-cli/packages/core/src/utils/environmentContext.test.ts)**: Added regression unit tests to verify that ignored directories are excluded from output context, and mock assertions verify that the option is passed correctly.

### Verification
- Added unit tests in `getFolderStructure.test.ts` and updated mock expectations in `environmentContext.test.ts`.
- Verified that all Vitest unit tests pass successfully.
