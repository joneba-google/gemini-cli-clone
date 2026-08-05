## Commit Message

[SSR Agent] Issue Fix (24695): Retain exit_plan_mode tool declaration upon plan exit

## PR Description

fixes #24695
Original Issue: https://github.com/google-gemini/gemini-cli/issues/24695

### Context & Problem

When exiting plan mode via `exit_plan_mode`, the active approval mode transitions from `PLAN` to `DEFAULT` or `AUTO_EDIT`. This causes `ToolRegistry` to immediately exclude the `exit_plan_mode` block from its active function declarations, triggering a 400 Bad Request (`INVALID_ARGUMENT`) on subsequent Gemini API requests because the conversation history still contains the un-declared `exit_plan_mode` tool call and response.

### Detailed Changes

- **`packages/core/src/tools/tool-registry.ts`**:
  - Maintained transition state memory (`hasExitedPlanMode` and `lastObservedApprovalMode`) to track when the session has transitioned out of plan mode.
  - Ensured `hasExitedPlanMode` and `lastObservedApprovalMode` are correctly copied during registry cloning to preserve transition tracking state.
  - Updated `isActiveTool()` to retain `exit_plan_mode` as an active tool declaration once plan mode has been entered and subsequently exited in the session.
  - Shifted unused local variables safely within scope block inside `getFunctionDeclarations()`.

### Verification

- Added a new Vitest unit test in `packages/core/src/tools/tool-registry.test.ts` to verify `exit_plan_mode` remains active and visible even after transitioning back to `DEFAULT` mode.
- Confirmed that all tools of the registry pass build and ESLint requirements.
