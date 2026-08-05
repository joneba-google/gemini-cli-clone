## Commit Message

[SSR Agent] Issue Fix (28251): Trust Nix store paths in isTrustedSystemPath

## PR Description

fixes #28251
Issue URL: https://github.com/google-gemini/gemini-cli/issues/28251

### Context & Problem
On Nix-based systems, packages and their binaries (including `ripgrep`) are installed within the `/nix/store` directory. When resolving system pathing, `isTrustedSystemPath` would reject these paths, causing verification to fail and fallback to `GrepTool`, which can hang on large repositories.

### Detailed Changes

- **packages/core/src/utils/paths.ts**:
  - Added `'/nix/store'` to the list of `trustedPrefixes` of the Unix/macOS/Linux platform check branch within `isTrustedSystemPath()`.

- **packages/core/src/utils/paths.test.ts**:
  - Added a test case in the macOS and Linux platform tests verifying that a typical Nix store path, such as `'/nix/store/abc123-ripgrep-13.0.0/bin/rg'`, is recognized and trusted.

### Verification
- Executed lint checks on the modified files successfully.
- Vitest unit tests covering dynamic verification and system path security verification have been successfully implemented.
