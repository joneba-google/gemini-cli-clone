## Commit Message

[SSR Agent] Issue Fix (2407): Safely resolve user tier if current tier is undefined

## PR Description

fixes #2407
Issue URL: https://github.com/google-gemini/gemini-cli/issues/2407

### Context & Problem
The `/privacy` slash command failed with an "Error loading Opt-in settings" error because the `getTier` function threw an exception when the `loadCodeAssist` response did not contain a `currentTier`. This occurred primarily for licensed accounts using Google Account + GOOGLE_CLOUD_PROJECT, where `currentTier` may be left undefined.

### Detailed Changes
- Modified `getTier` function in [usePrivacySettings.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts) to safely resolve the user tier when `currentTier` is undefined. It first checks `allowedTiers` for a default tier and returns its ID, otherwise falling back to `UserTierId.LEGACY` instead of throwing an error.
- Added comprehensive unit tests in [usePrivacySettings.test.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.test.ts) to cover hook loading, free vs non-free tiers, fallback resolution of undefined tier, error states, and opt-in updates.

### Verification
- Tested locally using Vitest. Unit tests successfully verify that when `loadCodeAssist` returns a response with an undefined `currentTier`, the hook gracefully sets `isFreeTier: false` and `isLoading: false` without triggering any errors.
- Verification passes linter (ESLint) checks without any errors or warnings.
