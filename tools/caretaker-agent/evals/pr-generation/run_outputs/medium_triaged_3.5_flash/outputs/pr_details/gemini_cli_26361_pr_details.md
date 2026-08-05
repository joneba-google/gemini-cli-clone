## Commit Message

[SSR Agent] Issue Fix (26361): Fix proxy support by instantiating static http/https proxy agents

## PR Description

fixes #26361

Original Issue URL: https://github.com/google-gemini/gemini-cli/issues/26361

### Context & Problem
Calling Vertex AI or Gemini API through an HTTP/HTTPS proxy throws a `TypeError: HttpsProxyAgent is not a constructor`. This occurs because ESM bundling and code splitting with esbuild inside `gaxios` lost dynamic named exports, causing `HttpsProxyAgent` to resolve to `undefined`.

### Detailed Changes
- **Core Logic (`packages/core/src/core/contentGenerator.ts`)**:
  - Imported `HttpProxyAgent` and `HttpsProxyAgent` statically to bypass `gaxios` dynamic imports.
  - Trimmed and parsed config proxy URL.
  - Conditionally instantiated `HttpProxyAgent` or `HttpsProxyAgent` based on whether the destination uses the `http://` protocol.
  - Injected the pre-instantiated proxy agent into `GoogleGenAI` constructor via `googleAuthOptions.clientOptions.transporterOptions.agent`.
- **Dependencies Configuration (`package.json`, `packages/core/package.json`)**:
  - Added `http-proxy-agent` as a dependency.
- **Unit Tests (`packages/core/src/core/contentGenerator.test.ts`)**:
  - Added test cases to verify HTTP and HTTPS proxy injection, trimming of whitespace from proxy URL, and option omission when no proxy is configured.

### Verification
- Covered by Vitest unit tests in `contentGenerator.test.ts`.
- The ESLint syntax and rule compliance check completed successfully.
