## Commit Message

[SSR Agent] Issue Fix (28251): Allow Nix store paths in isTrustedSystemPath

## PR Description

fixes #28251
Original issue: https://github.com/google-gemini/gemini-cli/issues/28251

### Context & Problem
When Gemini CLI runs on systems utilizing the Nix package manager, it fails to execute absolute binary paths like `rg` because they reside under `/nix/store/...`. Consequently, `isTrustedSystemPath()` rejects these paths, prompting a catastrophic fallback to `GrepTool`, which ignores `.gitignore` and hangs indefinitely in large repositories.

### Detailed Changes
- **packages/core/src/utils/paths.ts**: Added `/nix/store` to the `trustedPrefixes` array inside the Unix-like system paths branch of `isTrustedSystemPath()`.
- **packages/core/src/utils/paths.test.ts**: Added a unit test to verify that `isTrustedSystemPath()` correctly trusts Unix-like absolute binary paths starting with `/nix/store` on Darwin and Linux mock platforms.

### Verification
- Added mock-platform unit tests in `packages/core/src/utils/paths.test.ts`.
- Verified that all static checks and unit tests run and pass without issues.
