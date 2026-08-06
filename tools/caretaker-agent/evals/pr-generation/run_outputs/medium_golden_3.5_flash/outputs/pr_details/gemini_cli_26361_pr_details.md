## Commit Message

[SSR Agent] Issue Fix (26361): Fix proxy-agent imports in bundled ESM code

## PR Description

fixes #26361
Issue URL: https://github.com/google-gemini/gemini-cli/issues/26361

### Context & Problem
When executing bundled ESM code, calling Vertex AI / Gemini API or fallback proxy paths through an HTTP/HTTPS proxy failed with a `TypeError: HttpsProxyAgent is not a constructor`. This occurred because esbuild ESM code-splitting converts CommonJS dependencies (`https-proxy-agent` and `http-proxy-agent`) into default exports in split chunks, resolving named imports like `HttpsProxyAgent` as `undefined` at runtime.

### Detailed Changes
- **esbuild Configuration**: Added aliases for `http-proxy-agent` and `https-proxy-agent` to resolve to local patch files instead of directly to their node_modules packages.
- **Local Patch Re-exports**: Created `packages/cli/src/patches/http-proxy-agent.ts` and `packages/cli/src/patches/https-proxy-agent.ts` to explicitly re-export the named constructors, ensuring they are preserved in split chunks without requiring externalization.
- **Bundle Resolution Test**: Added `scripts/tests/proxy-agent-bundle.test.ts` to perform a test bundle build with code-splitting active and verify that the resulting dynamic imports properly expose constructable constructor functions.

### Verification
- Executed Vitest test suite (`npm run test` or `npx vitest scripts/tests/proxy-agent-bundle.test.ts`) and verified it passes successfully.
- ESLint checks on modified files succeeded without any lint errors.
