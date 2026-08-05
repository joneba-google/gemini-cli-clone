## Commit Message

[SSR Agent] Issue Fix (18369): Fix wrong session ID after resuming session

## PR Description

fixes #18369
Issue URL: https://github.com/google-gemini/gemini-cli/issues/18369

### Context & Problem
When a CLI session was resumed, executing `/stats session` erroneously displayed a newly generated session ID instead of the resumed session's actual ID. This discrepancy occurred because `useSessionResume.ts` failed to hydrate the telemetric state inside `uiTelemetryService` with the resumed conversation record, meaning the front-end components and telemetry state retained the startup session ID.

### Detailed Changes
- **packages/core/src/telemetry/uiTelemetry.ts**: Implemented `hydrate()` in `UiTelemetryService` to populatemetrics and update `#sessionId` from the restored `ConversationRecord`, subsequently emitting an `'update'` event carrying correct session details.
- **packages/cli/src/ui/hooks/useSessionResume.ts**: Imported `uiTelemetryService` and invoked `hydrate` with the resumed session's conversation record during `loadHistoryForResume`.
- **packages/cli/src/ui/contexts/SessionContext.tsx**: Extended `SessionStatsProvider` to accept `sessionId` as an optional prop and updated the internal React state when either the prop or update events supply a different session ID.
- **packages/cli/src/ui/hooks/useSessionResume.test.ts**: Added robust unit tests to verify `uiTelemetryService.hydrate` is called with the correct resumed conversation record.

### Verification
- Implemented unit tests added in `useSessionResume.test.ts` ensuring session resumption correctly updates the telemetry service and triggers events.
- All modified files pass ESLint rules successfully.
