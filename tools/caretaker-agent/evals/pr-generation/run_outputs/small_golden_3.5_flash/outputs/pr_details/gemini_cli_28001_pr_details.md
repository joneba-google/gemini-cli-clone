## Commit Message

[SSR Agent] Issue Fix (28001): Add default fallbacks for nightly release workflow variables

## PR Description

fixes #28001
Issue URL: https://github.com/google-gemini/gemini-cli/issues/28001

### Context & Problem
The Nightly Release workflow failed during the publish step for scheduled runs because the workflow was recently moved to the `internal` environment where repository variables (`CLI_PACKAGE_NAME`, `CORE_PACKAGE_NAME`, `A2A_PACKAGE_NAME`, `NPM_REGISTRY_PUBLISH_URL`, `NPM_REGISTRY_URL`, and `NPM_REGISTRY_SCOPE`) are empty or not configured.

### Detailed Changes
- Modified `.github/workflows/release-nightly.yml` to supply default fallback values using the logic-OR `||` operator for all missing repository variables inside the workflow invocation parameters.

### Verification
- Verified that standard GitHub Actions expression syntax is used.
- Validated that if corresponding `vars` are undefined, the workflow cleanly falls back to correct default registry and package name properties.
