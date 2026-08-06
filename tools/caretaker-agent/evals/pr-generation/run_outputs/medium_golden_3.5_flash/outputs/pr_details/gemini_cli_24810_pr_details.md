## Commit Message

[SSR Agent] Issue Fix (24810): Prevent stable installations updating to nightly builds

## PR Description

fixes #24810
Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/24810

### Context & Problem
Gemini CLI installations on the stable channel were automatically updated or prompted to update to nightly/preview builds because the update check did not perform stability channel checks and solely compared semver numbers.

### Detailed Changes
- **packages/core/src/utils/channel.ts**: Exported `RELEASE_CHANNEL_STABILITY` hierarchy representing stability ranking of release channels, and extracted `getChannelFromVersion` function, refactoring `getReleaseChannel` to leverage it.
- **packages/cli/src/ui/utils/updateCheck.ts**: Integrated stability channel checks within `checkForUpdates` to filter out any target update channel that is less stable than the current release channel.
- **packages/cli/src/utils/handleAutoUpdate.ts**: Added defense-in-depth checks within `handleAutoUpdate` to abort auto-update processes if the target channel's stability is lower than the current channel's.
- **packages/cli/src/ui/utils/updateCheck.test.ts** and **packages/cli/src/utils/handleAutoUpdate.test.ts**: Added comprehensive unit tests validating correct channel filtering behavior.

### Verification
- Vitest unit tests have been added to verify that `checkForUpdates` returns `null` when a stable/preview version is compared against nightly/preview updates.
- An auto-update abort test has been added to ensure `handleAutoUpdate` prevents lower-stability downgrades.
- ESLint checks have successfully run and passed with no errors.
