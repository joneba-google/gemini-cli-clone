## Commit Message

[SSR Agent] Issue Fix (24810): Fix npm publish tag in release action

## PR Description

fixes #24810
Original Issue: https://github.com/google-gemini/gemini-cli/issues/24810

### Context & Problem

Stable installations of Gemini CLI were automatically updated to nightly build versions because the release workflow used a temporary staging tag and subsequently removed it. This caused the published packages to fall back, overwriting the 'latest' dist-tag on npm and resulting in stable installations updating to nightly builds.

### Detailed Changes

- **Publish Action**: Replaced the previous `staging-tmp` tag strategy in [.github/actions/publish-release/action.yml](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_24810/tmp/eval/gemini-cli/.github/actions/publish-release/action.yml) with `--tag="${{ inputs.npm-tag }}"` across core, cli, and a2a-server publication steps. This ensures that when publishing nightly or preview releases, NPM tags them with the specific channel instead of defaulting to `latest`.
- **Unit Tests**: Created a new test suite [scripts/tests/publish-release-action.test.js](file:///usr/local/google/home/joneba/ssr-prototype/gcli-intern-project/tools/caretaker-agent/evals/pr-generation/run_outputs/medium_triaged_3.5_flash/agent_environments/gemini_cli_24810/tmp/eval/gemini-cli/scripts/tests/publish-release-action.test.js) using Vitest that verifies that all `npm publish` blocks in the action config do not contain any references to temporary tags or `--no-tag` and instead correctly utilize `--tag="${{ inputs.npm-tag }}"`.

### Verification

- Successfully ran static code verification.
- Inspected the ESLint analysis (`linter_output.txt`), which confirmed that all modified and newly created codebase files successfully adhere to lint limits and contain no syntax, typing, or style violations.
