## Commit Message

[SSR Agent] Issue Fix (19271): Resolve git directory dynamically for branch watcher

## PR Description

fixes #19271
Original issue URL: https://github.com/google-gemini/gemini-cli/issues/19271

### Context & Problem

In the Gemini CLI, switching git branches using a shell execution (e.g., `!` command) did not update the active branch name displayed in the UI footer. This occurred because the `useGitBranchName` hook hardcoded the git path to watch as `path.join(cwd, '.git', 'logs', 'HEAD')`. When the CLI is run inside a git repository's subdirectory, or if the `.git` directory is structured differently (such as inside a worktree), this hardcoded path was invalid or failed to trigger filesystem events.

### Detailed Changes

- **useGitBranchName.ts**: Modified `useGitBranchName` to dynamically resolve the appropriate git directory path by spawning `git rev-parse --git-dir`. It falls back to watching `.git/HEAD` if `.git/logs/HEAD` is missing or inaccessible, ensuring git branch change notifications are triggered even on new/bare repos or inside nested subdirectories.
- **useGitBranchName.test.tsx**: Added comprehensive unit tests validating the hook's ability to:
  - Correctly resolve git repository/branch details when run within nested subdirectories.
  - Detect and trigger state updates when git `HEAD` file content is modified directly (for systems/repos lacking logs/HEAD).

### Verification

Verified and passed all Vitest unit tests for the updated hook, and verified the project compiles and lint checks pass cleanly.
