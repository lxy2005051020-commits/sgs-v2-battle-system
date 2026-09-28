# Stage13 · Core Gameplay Mechanism Completion

> Current status: READINESS READY / NOT ACTIVE
>
> Route authority: [STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN.md](STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN.md)

## Mission

Stage13 completes the reusable game-engine substrate before the project begins large-scale skill-system integration.

It does not start from a predetermined list of missing mechanisms. It first builds a complete inventory of the current engine, then classifies each mechanism and closes every implementation-required gap.

## Current workflow

```text
Stage13-A  Core Gameplay Mechanism Inventory Audit
Stage13-B  Gap Classification & Research Planning
Stage13-C  Focused Research / Runtime Governance
Stage13-D  Core Runtime Architecture Design
Stage13-E  Core Mechanism Implementation
Stage13-F  Independent Engine Completion / Deterministic Replay Audit
```

## Current gate

```text
Stage12 Runtime = FROZEN
Stage12 Complete = YES
FINAL_40_STATE_RUNTIME_AUDIT = PASS
GOVERNANCE_SYNC = PASS

Stage13 Readiness = READY
Stage13 Active = NO

NEXT = STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY_AUDIT
```

## Skill-system boundary

The previous Assault-first Stage13 route is superseded.

Assault, ordinary Active, Preparation, Passive, Command, Formation, Troop and other concrete skill runtimes are deferred until the Stage13 exit gate declares:

```text
CORE_GAMEPLAY_ENGINE = FROZEN
Skill Runtime Readiness = READY
```

Stage13 may reuse existing SkillType / Provider / Permission / Target / ExecutionRight metadata, but must not silently turn those compatibility foundations into full skill runtimes.

## Exit target

See the replan authority for the exact gate. In short: inventory complete, implementation-required gaps closed, runtime-governance blockers closed, deterministic replay audited, Stage1-12 regressions green, and the core gameplay engine independently frozen.
