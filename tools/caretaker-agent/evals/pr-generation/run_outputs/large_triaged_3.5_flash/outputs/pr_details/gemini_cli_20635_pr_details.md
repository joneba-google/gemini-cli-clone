## Commit Message

[SSR Agent] Issue Fix (20635): Enforce strict validation of policy schema fields

## PR Description

fixes #20635
Original Issue: https://github.com/google-gemini/gemini-cli/issues/20635

### Context & Problem

A typo in a policy rule property name (such as `toolname` instead of `toolName`) was previously silently stripped during schema parsing. Because Zod's `z.object()` does not enforce strict key validation by default, the unrecognized keys were discarded, potentially leaving critical fields like `toolName` undefined, which inadvertently matches and allows all tools.

### Detailed Changes

- **packages/core/src/policy/toml-loader.ts**:
  - Appended `.strict()` to the `PolicyRuleSchema` Zod object schema definition.
  - Appended `.strict()` to the `SafetyCheckerRuleSchema` Zod object schema definition.
- **packages/core/src/policy/toml-loader.test.ts**:
  - Added a unit test to verify that loading a policy TOML containing unknown keys in rules produces a `schema_validation` error.
  - Added a unit test to verify that loading a policy TOML containing unknown keys in safety checkers produces a `schema_validation` error.

### Verification

- Leveraged Vitest to run policy configuration tests including the newly added schema validation scenarios.
- All ESLint checks passed successfully.
