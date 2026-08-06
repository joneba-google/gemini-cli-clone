## Commit Message

[SSR Agent] Issue Fix (27725): Prevent JSON arrays from populating structuredContent

## PR Description

fixes #27725
https://github.com/google-gemini/gemini-cli/issues/27725

### Context & Problem
The `calendar.listEvents` tool failed with an "Invalid input: expected record, received array" error. This happened because the `McpComplianceTransport` parsed the tool's text content and inappropriately assigned the parsed JSON array directly to `structuredContent`, which strictly expects a key-value record/object wrapper.

### Detailed Changes
- Added an `isRecord` helper utility in [mcp-compliance-transport.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.ts) to identify non-null, non-array objects.
- Updated the try-catch parsing logic block in `McpComplianceTransport` to ensure `structuredContent` is only populated if the parsed JSON is indeed a record.
- Added a comprehensive Vitest unit test in [mcp-compliance-transport.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.test.ts) to verify that JSON arrays are not treated as `structuredContent` and the initial text content remains intact.

### Verification
- Executed `vitest` unit tests covering the compliance transport parser, specifically verifying the new test case "should NOT use JSON arrays as structuredContent". All tests passed successfully.
- Confirmed that the ESLint static checks succeeded without errors.
