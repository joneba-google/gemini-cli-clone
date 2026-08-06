## Commit Message

[SSR Agent] Issue Fix (28001): Add fallback package names for nightly releases

## PR Description

fixes #28001
Issue URL: https://github.com/google-gemini/gemini-cli/issues/28001

### Context & Problem
The nightly release workflow failed during the "Publish Release" step because repository environment variables specifying the package names were not defined in the workspace environment. This caused the input package names to evaluate to empty strings, resulting in a failure when running `npm publish --workspace=`.

### Detailed Changes
- Modified [.github/actions/publish-release/action.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/redo_small_triaged_3.5_flash/agent_environments/gemini_cli_28001/tmp/eval/gemini-cli/.github/actions/publish-release/action.yml) to include default values for `cli-package-name` ('@google/gemini-cli'), `core-package-name` ('@google/gemini-cli-core'), and `a2a-package-name` ('@google/gemini-cli-a2a-server').
- Modified [.github/actions/tag-npm-release/action.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/redo_small_triaged_3.5_flash/agent_environments/gemini_cli_28001/tmp/eval/gemini-cli/.github/actions/tag-npm-release/action.yml) to add identical package name default values.
- Updated [.github/workflows/release-nightly.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/redo_small_triaged_3.5_flash/agent_environments/gemini_cli_28001/tmp/eval/gemini-cli/.github/workflows/release-nightly.yml) to use fallback expressions (such as `${{ vars.CLI_PACKAGE_NAME || '@google/gemini-cli' }}`) to resolve package name parameters when calling the publish-release action.

### Verification
- Static inspection verified the YAML syntax and compliance with GitHub Actions schema and fallback paradigms.
- The linter check successfully recorded no TypeScript/JavaScript modifications, confirming zero impact on the package runtime codebase.
