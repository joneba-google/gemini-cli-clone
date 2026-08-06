## Commit Message

[SSR Agent] Issue Fix (18369): Fix session ID displayed after resuming a session

## PR Description

fixes #18369
Original Issue: https://github.com/google-gemini/gemini-cli/issues/18369

### Context & Problem

When resuming a session using `gemini --resume <session-id>`, executing `/stats session` or accessing stats/telemetry/logging displayed a newly generated start-up session ID instead of the resumed session's ID. This occurred because `SessionStatsProvider`, downstream telemetry logs, and CLI modules relied on a static module-level `sessionId` exported from `@google/gemini-cli-core` which was created once on module load.

### Detailed Changes

- **packages/core/src/utils/session.ts** & **packages/core/src/index.ts**: Removed the static `sessionId` constant, keeping only `createSessionId()`.
- **packages/core/src/telemetry/trace.ts**: Updated `runInDevTraceSpan` to dynamically accept and trace using a `sessionId` property.
- **packages/core/src/agents/subagent-tool.ts**, **loggingContentGenerator.ts**, **scheduler.ts**, **tool-executor.ts**, **useGeminiStream.ts**: Passed the dynamic session ID from the loaded configuration (`config.getSessionId()`) to `runInDevTraceSpan`.
- **packages/cli/src/gemini.tsx**: Resolved the resumed session's actual ID prior to full CLI config loading when `--resume` is supplied, and initialized code with the correct session ID.
- **packages/cli/src/ui/contexts/SessionContext.tsx**: Modified `SessionStatsProvider` to accept `sessionId` as a component prop, dynamically updating its state if the prop changes.
- **packages/cli/src/utils/sessionUtils.ts**: Configured `SessionSelector` to support loading storage and session IDs dynamically, making it robust and fully backwards compatible.
- Updated all test suites and components to pass the required dynamic session ID.

### Verification

- Successfully updated Vitest unit tests in `packages/cli/src/ui/contexts/SessionContext.test.tsx` and `packages/cli/src/ui/hooks/useLogger.test.tsx`.
- Verified that all edited files pass static check configurations.
