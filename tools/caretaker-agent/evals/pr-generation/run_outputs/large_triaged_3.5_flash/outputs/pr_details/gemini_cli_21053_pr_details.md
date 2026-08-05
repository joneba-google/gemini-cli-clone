## Commit Message

[SSR Agent] Issue Fix (21053): Populate structuredContent for all schema-backed MCP tool responses

## PR Description

fixes #21053
Issue URL: https://github.com/google-gemini/gemini-cli/issues/21053

### Context & Problem

MCP tool calls fail with error -32600 when tools registered with an `outputSchema` return flat JSON text inside `content` instead of `structuredContent`. Previously, a workaround (`XcodeMcpBridgeFixTransport`) was only applied to Xcode's `mcpbridge` stdio transport, leaving other transports (HTTP, SSE, and non-Xcode stdio) unhandled.

### Detailed Changes

- Renamed `XcodeMcpBridgeFixTransport` to `McpStructuredContentFixTransport` in `packages/core/src/tools/xcode-mcp-fix-transport.ts` to represent its general nature, and kept `XcodeMcpBridgeFixTransport` as a subclass of it for backward compatibility.
- Updated `packages/core/src/tools/mcp-client.ts` to wrap all created transports (stdio and URL-based streamable HTTP or SSE transports) with `McpStructuredContentFixTransport`.
- Updated debug transport unwrapping logic in `createTransport` to check for instances of both transport classes.
- Added new vitest unit tests in `packages/core/src/tools/xcode-mcp-fix-transport.test.ts` to verify the general transport interception behavior.

### Verification

- Comprehensive unit tests were run on `packages/core/src/tools/xcode-mcp-fix-transport.test.ts` to verify transport interception and automatic JSON parsing.
- The ESLint syntax and format checks successfully passed.
