## Commit Message

[SSR Agent] Issue Fix (19271): Fix CLI branch tracking in UI footer

## PR Description

fixes #19271
Original Issue: https://github.com/google-gemini/gemini-cli/issues/19271

### Context & Problem

The branch name displayed in the UI footer fails to update when a branch is switched using CLI-based Git commands. This happens because the `useGitBranchName` hook only monitors `.git/logs/HEAD` (the reflog). Certain platforms or Git branch commands update `.git/HEAD` (the canonical reference) directly without modifying the reflog, leaving the UI state stale.

### Detailed Changes

- **Hook Modifications (`useGitBranchName.ts`)**:
  - Updated `fetchBranchName` to take an optional `isMounted` callback, guarding `setBranchName` state updates on unmounted hooks.
  - Refactored `useEffect` to construct and watch both `gitHeadPath` and `gitLogsHeadPath` paths.
  - Added an inner helper function `watchFile` to handle silent setups of `fs.watch` and add active watchers to a trackable `watchers` array.
  - Set up watchers inside `setupWatchers` and cleanly iterate-close all watchers within the `unmount` cleanup handler.
- **Unit Tests (`useGitBranchName.test.tsx`)**:
  - Implemented a new unit test validating that changes to `.git/HEAD` successfully trigger the hook updater and load the correct branch.
  - Updated the existing test for changes to `.git/logs/HEAD`.
  - Refined mock tests to test silent failure when both head files are unlinked, and to ensure both watchers are closed cleanly on hook unmount.

### Verification

- **Linter Audit**: Read through `linter_output.txt` and verified that ESLint check on edited files succeeded without complaints or errors.
- **Unit Testing**: Verified that the test suite `useGitBranchName.test.tsx` thoroughly runs all test behaviors including watcher creation, multi-path triggers, dual-watcher teardown, and unmount.
