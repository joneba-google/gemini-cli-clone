## Commit Message

[SSR Agent] Issue Fix (19868): Prevent EISDIR errors in ignore file parser

## PR Description

fixes #19868
Issue URL: https://github.com/google-gemini/gemini-cli/issues/19868

### Context & Problem
Path completion fails when configuring customIgnoreFilePaths directories or invalid file paths (e.g. `node_modules`) because synchronous file operations threw an EISDIR error on Node.js.

### Detailed Changes
- **Ignore File Parser**: Updated [getIgnoreFilePaths](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/ignoreFileParser.ts#L115) in [ignoreFileParser.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/ignoreFileParser.ts) to filter out directory paths and only return paths pointing to regular files using `fs.statSync()`.
- **Ignore Rules Loader**: Modified [loadIgnoreRules](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/filesearch/ignore.ts#L14) in [ignore.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/filesearch/ignore.ts) to verify that each target ignore file is a regular file before reading, and safely handle potential filesystem errors via a robust try-catch block.
- **Testing**: Added unit test assertions to [ignoreFileParser.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/ignoreFileParser.test.ts) to verify directories are filtered and `loadIgnoreRules` avoids throwing EISDIR exceptions.

### Verification
All unit tests in [ignoreFileParser.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_19868/tmp/eval/gemini-cli/packages/core/src/utils/ignoreFileParser.test.ts) pass successfully under Vitest. No lint errors are introduced in the modified code sections.
