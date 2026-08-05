## Commit Message

[SSR Agent] Issue Fix (24337): Make slash-command IDE status subscription cleanup-safe

## PR Description

fixes #24337
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/24337

### Context & Problem

The hook `useSlashCommandProcessor` previously added and removed its IDE status listener through separate, uncoordinated async callback IIFEs which retrieved the `IdeClient` instance. If the hook unmounted before the first asynchronous retrieval promise resolved, the registration callback could execute after the cleanup callback, leaving a dangling listener that caused memory leaks and invalid command reload triggers.

### Detailed Changes

- **packages/cli/src/ui/hooks/slashCommandProcessor.ts**:
  - Implemented local cancellation state tracking within `useEffect` using `isCancelled` flag.
  - Stored a reference to the active `IdeClient` in `acquiredClient`.
  - Added verification checks inside the asynchronous setup callback to ensure registration is aborted if the hook unmounts early.
  - Cleaned up the registration by ending any pending steps and removing the listener synchronously if the client is already acquired.

- **packages/cli/src/ui/hooks/slashCommandProcessor.test.tsx**:
  - Added a test to verify proper registration and cleanup of the listener on unmount.
  - Added a race-condition test that simulates unmounting before `IdeClient.getInstance()` resolves to verify that no listener is added or left dangling after early unmount.

### Verification

- Successfully run standard Vitest unit tests verifying correct early-unmount behavior and listener life-cycle management.
- ESLint checks compile successfully without any error reports.
