## Commit Message

[SSR Agent] Issue Fix (2407): Gracefully handle unavailable consumer Code Assist tier

## PR Description

fixes #2407

Issue: https://github.com/google-gemini/gemini-cli/issues/2407

### Context & Problem
Running the `/privacy` command on accounts without a consumer Code Assist tier surfaces a confusing error message (e.g., 'User does not have a current tier' or 'Could not determine user tier') instead of displaying a clear, actionable notice. This is because the `/privacy` workflow expects a valid consumer Code Assist tier to be active, causing the [usePrivacySettings](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts) hook and related helpers to throw raw errors for unresolved tiers, missing oauth context, or missing project IDs.

### Detailed Changes
- **[usePrivacySettings.ts](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts)**
  - Created a custom [TierUnavailableError](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts#L93-L98) to signal that the current account configuration lacks a consumer Code Assist tier.
  - Modified helper [getCodeAssistServerOrFail](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts#L127-L137) to throw [TierUnavailableError](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts#L93-L98) when there is no OAuth context or when `server.projectId` is undefined.
  - Defined an [isTierUnavailableError](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts#L100-L108) helper that returns true if the error is an instance of [TierUnavailableError](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.ts#L93-L98) or has a message matching `/does not have a current tier/i`.
  - In `usePrivacySettings` hook, if `server.userTier` is undefined, immediately set `privacyState.isTierUnavailable` to true, `isLoading` to false, and return early.
  - In `usePrivacySettings` loading and updating routines, catch errors and check if they are tier-unavailable errors. If so, update `isTierUnavailable` to true, set `isLoading` to false, and handle gracefully without setting the error string.
- **[CloudFreePrivacyNotice.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/privacy/CloudFreePrivacyNotice.tsx)**
  - Updated keypress listener so that if `privacyState.isTierUnavailable` is true, pressing 'escape' triggers the exit action.
  - Rendered a specific UI block when `privacyState.isTierUnavailable` is true, informing the user that data collection opt-in settings are not available for this account, guiding Google Workspace / enterprise users to set the `GOOGLE_CLOUD_PROJECT` environment variable, and providing the documentation URL.
- **[usePrivacySettings.test.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/hooks/usePrivacySettings.test.tsx)**
  - Updated and added unit tests verifying that `isTierUnavailable` is set to true and there is no raw error set across various conditions (no OAuth, missing project ID, backend tier error, unexpected errors).
- **[CloudFreePrivacyNotice.test.tsx](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_golden_3.5_flash/agent_environments/gemini_cli_2407/tmp/eval/gemini-cli/packages/cli/src/ui/privacy/CloudFreePrivacyNotice.test.tsx)**
  - Added unit test to verify that `CloudFreePrivacyNotice` renders correctly and triggers `onExit` when Esc is pressed under the `isTierUnavailable` state.

### Verification
Vitest unit tests were updated, executed, and successfully validated all modified logic patterns. Specifically, checks were added to ensure that standard unexpected errors are still reported with error strings, whereas tier-unavailable conditions are gracefully reported with `isTierUnavailable: true`.
