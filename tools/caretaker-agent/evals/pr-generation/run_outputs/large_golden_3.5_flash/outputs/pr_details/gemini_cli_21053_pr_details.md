## Commit Message

[SSR Agent] Issue Fix (21053): Resolve MCP schema validation failures for non-compliant server responses

## PR Description

fixes #21053
Issue URL: https://github.com/google-gemini/gemini-cli/issues/21053

### Context & Problem
MCP tool calls failed with a protocol error when an MCP server returned schema-backed results inside the `content` field rather than `structuredContent`. Previously, the CLI only wrapped Xcode `mcpbridge` transport with a correction mechanism, but other non-compliant MCP servers or transport types encounters schema validation issues when returning stringified JSON in the `content` text array.

### Detailed Changes
- Renamed `XcodeMcpBridgeFixTransport` to `McpComplianceTransport` and moved its implementation from `packages/core/src/tools/xcode-mcp-fix-transport.ts` to `packages/core/src/tools/mcp-compliance-transport.ts`.
- Exposed a read-only `transport` property in `McpComplianceTransport` and implemented proxy delegation to forward methods and fields seamlessly to the underlying transport.
- Updated `packages/core/src/tools/mcp-client.ts` to replace imports of `XcodeMcpBridgeFixTransport` with `McpComplianceTransport`.
- Modified `createTransportWithOAuth` and `createTransport` to wrap all stdio, HTTP, and SSE transports unconditionally with `McpComplianceTransport` to ensure broad compatibility.
- Updated the debug mode to unwrap the compliance transport class using an updated `instanceof` check.
- Renamed the test suite file to `packages/core/src/tools/mcp-compliance-transport.test.ts` and added comprehensive unit tests checking that non-compliant JSON content is repaired while valid compliant content, plain text, and error responses remain untouched.

### Verification
Vitest unit tests were executed and passed successfully for `packages/core/src/tools/mcp-compliance-transport.test.ts`. An ESLint validation on the edited files passed without errors.
