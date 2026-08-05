## Commit Message

[SSR Agent] Issue Fix (27725): Only populate structuredContent with non-array object records

## PR Description

fixes #27725
Issue URL: https://github.com/google-gemini/gemini-cli/issues/27725

### Context & Problem

The MCP tool `mcp_google_workspace_calendar_listEvents` fails with an "Invalid input: expected record, received array" validation error when trying to retrieve calendar events. This happens because [McpComplianceTransport](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.ts#L23) in [fixStructuredContent](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.ts#L69) was previously assigning parsed JSON content directly to `result.structuredContent`. Since calendar event lists parse to a JSON array, setting `structuredContent` as an array violated the schema constraints of the MCP SDK Zod validation which expects a Record object (`Record<string, unknown>`).

### Detailed Changes

* **[mcp-compliance-transport.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.ts)**:
  - Inside [fixStructuredContent](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.ts#L69-L105), a strict type and array check is added: `typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)`.
  - This ensures `structuredContent` is only populated when the parsed output evaluates to a Record object, and remains unmodified for array or primitive outputs.

* **[mcp-compliance-transport.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.test.ts)**:
  - Added a test case ensuring that JSON arrays parsed in text responses are not assigned to `structuredContent`, keeping it undefined.
  - Added a test case ensuring that primitives parsed in text responses do not populate `structuredContent`.

### Verification

* Executed the newly added unit tests in [mcp-compliance-transport.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_triaged_3.5_flash/agent_environments/gemini_cli_27725/tmp/eval/gemini-cli/packages/core/src/tools/mcp-compliance-transport.test.ts) using Vitest, confirming all tests pass correctly.
* Checked that ESLint passed successfully with no errors or warnings for the modified files.
