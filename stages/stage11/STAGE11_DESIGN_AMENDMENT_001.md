# Stage11 Design Amendment 001 — Legacy Context Compatibility

Status: **APPROVED / DESIGN FROZEN ADDENDUM**

During first full-suite execution, Stage1-10 regression fixtures exposed two integration facts that the original Stage11 design did not model as migration seams:

1. Historical BattleContext fixtures have no attacker/defender role field.
2. Historical ApplyStateEffect callers may carry EmptyStateRuntimeParams for states that Stage11 now gives typed defaults.

Neither changes a research rule.

## A. Exact speed ties without attacker metadata

Frozen rule remains: cross-team exact tie is attacker before defender.

Production contexts should set `context.metadata["attacker_team_id"]`.

For legacy contexts that predate this authority, the runtime uses an explicit compatibility **PROJECT_RUNTIME_DEFAULT**: lexicographically smallest tied team id is treated as attacker for that tie. This is deterministic, consumes no RNG, and is documented as a compatibility default rather than empirical official behavior.

## B. Empty Stage11 params

When a legacy ingress supplies `EmptyStateRuntimeParams` for a Stage11 state whose new typed parameter class has a zero-argument frozen default, StateLifecycleSystem normalizes it to that typed default before validation.

This does not relax stored StateInstance typing and does not permit arbitrary mismatched parameter objects.

## C. Architecture guard

Stage11 state-specific application/conflict policy is moved out of StateLifecycleSystem into `stage11_application_policy.py`. StateLifecycleSystem remains the sole physical mutation owner without becoming a state-id gameplay monolith.

Verdict: **NO RESEARCH SEMANTIC CHANGE / NO STAGE7-10 GAMEPLAY CHANGE**.
