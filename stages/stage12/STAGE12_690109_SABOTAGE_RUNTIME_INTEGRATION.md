# Stage12 690109 SABOTAGE Runtime Integration

Date: 2026-09-28  
Status: **IMPLEMENTED_PENDING_RUNTIME_AUDIT / RUNTIME NOT YET FROZEN**

## Current gate

```text
690109 Research = FROZEN
690109 Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690109 Runtime = NOT YET FROZEN
Integration Exit Gate = PASS
Independent Runtime Freeze Audit = PENDING

Stage12 Gameplay Implementation = 6 / 7
Stage12 Runtime Frozen = 5 / 7
Stage11 Reopen Required = NO
Research Reopen Required = NO
Shared Foundation Reopen Required = NO

NEXT = 690109 SABOTAGE Independent Runtime Freeze Audit
```

This record deliberately does **not** freeze 690109 Runtime. The independent audit is a separate gate.

## Repository lock

```text
Battle main at integration start
= 7ff8bbe7d1f0af6ece8591939e891a6ebe8f9d1c

Research main
= e18ae56a4db5662b87458dfa8fdff25dcdd8053b

Research repository
= READ ONLY / UNCHANGED
```

Research authority: `states/control/sabotage/MECHANISM_CONTRACT.md` v1.0-frozen.

## Runtime architecture

690109 is integrated as canonical Provider/effectiveness policy composition, not as an equipment inventory facade.

```text
physical EquipmentProviderRef remains resident
-> Sabotage StateNode becomes effective
-> target-owned Equipment Provider validity becomes SUPPRESSED
-> EquipmentEffectivenessPolicy excludes its contributions
-> existing explicit Provider-dependent live effects become ineffective
-> suppression ends
-> the same Provider / still-live effect becomes effective again
```

No equipment object is unequipped, deleted, slot-cleared, recreated or toggled through an `enabled` mutation.

Stable identity remains:

```text
EquipmentProviderRef(owner_id, provider_key)
```

Skill Provider identity remains separate.

## Supported equipment contribution domains

The single Provider gate is consumed by the existing production domain owners for:

- ATTRIBUTE
- DAMAGE_MODIFIER
- RECOVERY_MODIFIER
- TRIGGER
- SCHEDULED_TRIGGER
- LIVE_EFFECT

Weapon / Armor / Mount / Treasure provider identities are all covered. The policy filters contributions; it does not calculate attributes, damage, recovery or schedules.

## Production consumer coverage

### Attribute

`AttributeSystem` queries canonical equipment effectiveness at contribution gather time. Base attributes are never subtract/add mutated, so repeated suppress/resume cycles cannot accumulate drift.

### Damage modifier

`DamageModifierSystem` gates an equipment-owned modifier before provider-owned modifier probability RNG. Settled historical damage is not recalculated.

### Recovery modifier

`RecoverySystem` gates the equipment-owned recovery modifier while preserving the existing Recovery pipeline and historical results.

### Deterministic trigger

`TriggerSystem.evaluate_equipment_dependency()` consumes the canonical `EquipmentTriggerGate`. Missed windows are not replayed.

### Scheduled trigger

The frozen tested due-window uses `ExecutionRightSupport` with `RECHECK_AT_EXECUTION`. A due opportunity inside the Sabotage window is denied; later resume does not backfill it. Broader queued/in-flight micro-order remains B-SAB-07 / UNSUPPORTED_BOUNDARY.

### Existing / remote live effect

A still-live state follows equipment effectiveness only when it has an explicit `ProviderDependency(EquipmentProviderRef, ...)`, the production equivalent of the frozen EquipmentProviderDependency concept.

Remote ownership is provider-owned:

```text
A equipment Provider -> dependent effect on B
Sabotage A -> dependent B effect suppressed
Sabotage B alone -> A Provider unaffected
```

Attribution alone creates no dependency edge.

## Admission / lifecycle

- effective INSIGHT rejects incoming SABOTAGE through the existing 690089 protected-control admission owner;
- later INSIGHT suppresses resident SABOTAGE, immediately restoring equipment contribution effectiveness without removing the SABOTAGE instance;
- when INSIGHT ends and SABOTAGE is still live, the same SABOTAGE instance/generation/lifetime resumes;
- same-envelope removal uses the existing RD-SF-003 due-removal batch and creates no ghost re-suppression;
- effective Gangyi rejects incoming SABOTAGE at admission;
- supported default same-state reapplication is rejected with no refresh;
- numeric stronger/weaker mapping remains unsupported because the contract does not freeze a `StateCandidate.strength` orientation;
- ordinary observed cleanse is supported;
- specialized/scripted gameplay removal remains an explicit unsupported boundary;
- no source-death special rule is added.

## Dynamic equipment boundary

B-SAB-09 remains bounded. If an equipment contribution appears after Sabotage committed and its Provider was not part of the committed dependency topology, the contribution returns `UNSUPPORTED_BOUNDARY` rather than silently claiming dynamic equipment semantics.

## FalseReport / Capture boundary

FalseReport keeps its narrow tested equipment-special scope. A contribution suppressed by both FalseReport and Sabotage stays ineffective when only one known cause is removed, and resumes only after the final known cause is gone.

690110 CAPTURE gameplay is not implemented by this integration. No Capture state-id branch is added to the 690109 adapter or equipment consumers.

## RNG / events

```text
Sabotage adapter RNG = 0
EquipmentEffectivenessPolicy RNG = 0
suppression/resume RNG = 0
equipment policy query public events = 0
```

Equipment-owned probability remains owned by the equipment consumer and is skipped when the contribution is already ineffective.

## Executable integration tests

Primary suite:

```text
tests/test_stage12_690109_sabotage.py
```

Coverage includes:

- application/effective truth;
- stable equipment identity and physical retention;
- all four equipment slot families;
- all frozen contribution taxonomy kinds;
- Attribute / Damage / Recovery real consumer paths;
- deterministic trigger and scheduled execution-right paths;
- local and remote explicit ProviderDependency propagation;
- attribution negative;
- Insight incoming rejection and resident suppress/resume;
- suppression lifetime and same-envelope expiry;
- Gangyi admission rejection;
- equal reapplication / stronger-weaker boundary;
- natural expiry / observed cleanse / unsupported removal;
- FalseReport cause composition in both removal orders;
- FalseReport ordinary-equipment negative;
- dynamic equipment bounded behavior;
- zero RNG / zero query event;
- static architecture guards.

## Validated checkpoint

```text
Pre-integration full-suite baseline = 1483 passed
Validated code/test SHA = 9d2b6aa37dffef1ea28ad4a5984ccc147114af89
PR CI = 36379462582 / success
Full pytest = 1525 passed
Net new test nodes = +42
Demo = PASS

Stage9 regression = INCLUDED IN FULL PASS
Stage10 regression = INCLUDED IN FULL PASS
Stage11 regression = INCLUDED IN FULL PASS
690089 regression = INCLUDED IN FULL PASS
690101 regression = INCLUDED IN FULL PASS
690107 regression = INCLUDED IN FULL PASS
690108 regression = INCLUDED IN FULL PASS
690222 regression = INCLUDED IN FULL PASS
Shared Foundation regression = INCLUDED IN FULL PASS
```

The full-suite count is strictly above the 1483 baseline and the same CI run completed the demo smoke test.

## Files created / updated

Production:
- `sgs_v2/battle_core/sabotage_integration.py`
- `sgs_v2/battle_core/battle_systems.py`

Tests:
- `tests/test_stage12_690109_sabotage.py`

Governance:
- this integration record;
- Stage12 README / planning / runtime test matrix;
- project status / canonical matrix / root README.

## Implementation blockers

```text
IMPLEMENTATION_BLOCKER-690109-xxx = NONE
Research reopen = NO
Runtime governance reopen = NO
Shared Foundation reopen = NO
```

Preserved bounded areas are not blockers because the supported contract path can explicitly surface them as unsupported rather than inventing gameplay.

## Exit

```text
690109 SABOTAGE Gameplay
= IMPLEMENTED_PENDING_RUNTIME_AUDIT

690109 SABOTAGE Runtime
= NOT YET FROZEN

Stage12 Runtime Frozen
= 5 / 7

NEXT
= 690109 SABOTAGE Independent Runtime Freeze Audit
```
