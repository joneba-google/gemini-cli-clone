## Commit Message

[SSR Agent] Issue Fix (25182): Fix policy bypass and enforce workspace trust in A2A

## PR Description

fixes #25182
Issue URL: https://github.com/google-gemini/gemini-cli/issues/25182

### Context & Problem

The A2A server in Gemini CLI did not load default security policies, leading to bypassed policy checks and inconsistent enforcement compared to interactive CLI mode. This issue was caused by `loadConfig` setting `policyEngineConfig` with an empty rules array in non-YOLO mode and loading workspace settings unconditionally without verifying folder trust.

### Detailed Changes

- **packages/a2a-server/src/types.ts**: Added optional `isTrusted` field to `AgentSettings`.
- **packages/a2a-server/src/config/settings.ts**: Updated `loadSettings` to evaluate workspace trust via `checkPathTrust` when trust override is undefined, skipped loading workspace settings when not trusted, and strictly prevented workspace override of security `policyPaths` and `adminPolicyPaths`.
- **packages/a2a-server/src/config/config.ts**: Updated `loadConfig` to accept `trusted` parameter and initialize default security rules using `createPolicyEngineConfig` instead of returning empty rules.
- **packages/a2a-server/src/agent/executor.ts**: Read and passed `isTrusted` field from `agentSettings` into load configurations.
- **packages/a2a-server/src/http/app.ts**: Checked path trust on startup and passed trust settings to configuration loaders.
- **scripts/copy_bundle_assets.js**: Added logic to copy default policy definitions to the `packages/a2a-server/dist/policies` directory.
- **packages/a2a-server/vitest.config.ts** / **vitest.setup.ts**: Configured testing setup to support File API global fallback compatibility in Vitest node environment.

### Verification

- Successfully executed Vitest unit tests to assert the initialization of policy rules and folder trust constraints.
- Verified that `createPolicyEngineConfig` is invoked with mapped settings.
- Confirmed that untrusted settings are ignored and overrides of policy paths are prevented.
