## Commit Message

[SSR Agent] Issue Fix (24337): Make slash-command IDE status subscription cleanup-safe

## PR Description

fixes #24337
Original issue URL: https://github.com/google-gemini/gemini-cli/issues/24337

### Context & Problem
The `useSlashCommandProcessor` hook registers its IDE status listener using separate asynchronous tasks for registration and cleanup. If the component unmounts before the asynchronous initialization resolves, the registration logic executes after cleanup, causing a leaked event listener.

### Detailed Changes
- **[slashCommandProcessor.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24337/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/slashCommandProcessor.ts)**:
  - Introduced local state `isActive` and tracking reference `activeIdeClient` within the hook's `useEffect`.
  - Added a validation guard `!isActive` post-resolve to prevent listener registration after unmount.
  - Updated cleanup function to set `isActive = false` and synchronously invoke `activeIdeClient?.removeStatusChangeListener`.
- **[slashCommandProcessor.test.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24337/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/slashCommandProcessor.test.tsx)**:
  - Added mock setup for registering and unmounting, handling both pending and resolved asynchronous initialization.
  - Included a test to verify proper listener removal on unmount after async initialization resolves.
  - Included a test to verify no listener registration occurs if unmounted before async initialization resolves.
- **[test-setup.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/small_golden_3.5_flash/agent_environments/gemini_cli_24337/tmp/eval/gemini-cli/packages/cli/test-setup.ts)**:
  - Added global fallback/polyfill for `File` in Node.js test environment to ensure test suite robustness.

### Verification
The changes have been verified via Vitest unit tests:
- `removes the IDE status listener on unmount after async initialization`
- `does not register an IDE status listener if unmounted before async initialization resolves`
All ESLint static analysis and Vitest test runs succeeded without issue.
