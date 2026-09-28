# Stage13 Core Gameplay Mechanism Replan

> Status: CURRENT PROJECT ROUTE AUTHORITY
>
> Effective: 2026-09-28
>
> Supersedes: Stage13 Assault / Stage14 ordinary Active / Stage15 Preparation sequencing

## 1. Decision

The project route after Stage12 is formally replanned.

```text
Stage12 = State Runtime Completion
          FROZEN / COMPLETE

Stage13 = Core Gameplay Mechanism Completion
          游戏底层机制完备化

Stage14+ = Skill System / 战法系统
           exact subtype staging is decided only after Stage13 exit audit
```

The previous Assault-first route is not deleted from history. It is superseded as the current route. Assault remains a future skill-system workstream behind the Stage13 core-engine completion gate.

## 2. Why Stage13 exists

Before large-scale skill integration, the battle engine must expose a complete, canonical, deterministic set of reusable gameplay primitives.

Stage13 therefore asks:

> What game-level mechanisms are still missing, partial, stubbed, under-governed, or implemented only as narrow Stage12 interoperability hooks?

The answer must be established before introducing a broad skill execution layer.

## 3. Stage13 scope

Stage13 begins with a full core-mechanism inventory. At minimum it must audit:

- battle timing / phase model;
- trigger and opportunity model;
- damage families and work identity;
- recovery primitives;
- canonical attribute pipeline;
- speed / action-order mechanics;
- target primitives and target freshness;
- RNG ownership and call topology;
- Effect primitives and composition;
- modifier architecture;
- duration / lifetime;
- usage / charges / frequency control;
- dependency graph coverage;
- death / defeat / pending-work semantics;
- unit / team / relation facts;
- multi-hit / multi-effect execution;
- snapshot vs JIT / ExecutionRight dimensions;
- dispel / cleanse / removal taxonomy;
- buff / debuff classification only where gameplay-relevant;
- event facts vs gameplay authority;
- deterministic replay.

This list is an audit seed, not a declaration that every item is missing.

## 4. Gap classification

Every inventory item must be classified as exactly one of:

```text
ALREADY_IMPLEMENTED
PARTIAL
MISSING
RESEARCH_REQUIRED
RUNTIME_GOVERNANCE_REQUIRED
UNSUPPORTED
NOT_NEEDED
```

A mechanism may not be marked complete merely because one current state or test happens to exercise a narrow slice of it.

## 5. Stage13 phases

```text
Stage13-A
Core Gameplay Mechanism Inventory Audit

Stage13-B
Gap Classification & Research Planning

Stage13-C
Focused Mechanism Research / Runtime Governance

Stage13-D
Core Runtime Architecture Design

Stage13-E
Core Mechanism Implementation

Stage13-F
Independent Engine Completion / Deterministic Replay Audit
```

Focused research is performed only for questions whose gameplay truth is genuinely unknown and implementation-relevant. Existing frozen evidence must be reused rather than rediscovered.

## 6. Non-goals

Stage13 does not yet activate large-scale:

```text
Assault Skill Runtime
ordinary Active Skill Runtime
Preparation Skill Runtime
Passive scheduler
Command scheduler
Formation Skill Runtime
Troop Skill Runtime
bulk concrete-skill catalog integration
```

Minimal metadata or compatibility interfaces may exist when already frozen by prior stages, but Stage13 must not use the core-engine cleanup as an excuse to silently start the Skill System.

## 7. Frozen-stage barrier

Stage1-12 remain frozen according to their existing authorities.

Any Stage13 design that requires changing frozen gameplay semantics must raise an explicit cross-stage reopen finding. Convenience is not a reopen trigger.

Current project totals remain:

```text
Official States = 40
Research FROZEN = 39 / 40
Runtime FROZEN TO CONTRACT = 40 / 40
Strict Complete = 39 / 40

690086 DISTRIBUTION / DSTS9-B02
= OPEN / UNOBSERVED
```

Stage13 does not close the 690086 research debt unless new authority actually resolves it.

## 8. Stage13 exit gate

Stage13 is not complete until all of the following are true:

```text
CORE_GAMEPLAY_MECHANISM_INVENTORY = COMPLETE

UNRESOLVED_IMPLEMENTATION_REQUIRED_GAPS = 0

UNRESOLVED_RUNTIME_GOVERNANCE_BLOCKERS = 0

CORE_GAMEPLAY_ENGINE = FROZEN

DETERMINISTIC_REPLAY_AUDIT = PASS

STAGE1-12_REGRESSION = PASS

Skill Runtime Readiness = READY
```

Bounded unknowns may remain only when they are explicitly non-blocking for skill-system readiness and are represented as such in governance.

## 9. Current gate

```text
Stage12 Runtime = FROZEN
Stage12 Complete = YES

Stage13 Readiness = READY
Stage13 Active = NO

NEXT
= STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY_AUDIT
```

The inventory/entry audit decides whether Stage13 may become ACTIVE and what exact closure program follows.
