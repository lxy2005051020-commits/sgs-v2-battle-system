# Stage12 690222 INTIMIDATION Runtime Integration

Date: 2026-09-28  
Status: GOVERNANCE_RESOLVED / PASS / GAMEPLAY_NOT_INTEGRATED

## Current gate

```text
690222 Research = FROZEN
690222 Gameplay = NOT_INTEGRATED
690222 Runtime = NOT_FROZEN
Stage12 Runtime Frozen = 4 / 7
```

The Runtime integration was intentionally not started until the binding-selection weighting gap had explicit project governance.

## Binding-selection governance dependency

```text
IMPLEMENTATION_BLOCKER-690222-BINDING-WEIGHTS-001
= CLOSED
```

Authority:

- `STAGE12_690222_BINDING_SELECTION_RUNTIME_GOVERNANCE_RESOLUTION.md`
- `STAGE12_RUNTIME_DEFAULT_LEDGER.md` / RD-SF-006
- `STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md`

RD-SF-006 freezes the simulator-only selection rule:

```text
supported eligible count = 1
-> sole Provider
-> 0 binding RNG

supported eligible count >= 2
-> RD-SF-002 stable Provider order
-> exactly one BattleContext.random / RandomSystem.choice
-> uniform over the supplied pool

RESUME
-> retain binding
-> 0 binding RNG
```

This is `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`. It is not evidence that the original game uses equal weights.

## Frozen pool boundary retained

Supported Skill Provider families:

```text
ACTIVE
PREPARATION_ACTIVE
ASSAULT
PASSIVE
COMMAND
TROOP
```

Preserved boundaries:

```text
FORMATION = excluded
NORMAL_ATTACK = outside domain
TALENT = unsupported / not frozen
EQUIPMENT = unsupported / not frozen
BINGSHU = unsupported / not frozen
empty eligible pool = UNSUPPORTED_BOUNDARY
```

Loaded Provider enumeration and RD-SF-002 ordering are not redefined here.

## Production work in this governance round

```text
690222 gameplay code = NONE
690222 adapter registration = NONE
Research repo changes = NONE
Shared Foundation redesign = NONE
```

## Resume checklist

The next Runtime Integration round may now implement, in contract order:

1. supported eligible-pool construction;
2. RD-SF-006 binding selection;
3. stable selected `SkillProviderRef` storage;
4. selected-Provider suppression through ProviderValidity;
5. successful REFRESH -> new binding decision;
6. RESUME -> retained binding / zero binding RNG;
7. selected Preparation Active interruption;
8. Gangyi admission rejection before binding RNG;
9. source-Provider dependency for the frozen observed source scope;
10. required cross-state interactions and full regression.

It must not implement source-skill counter formulas, Equipment/Bingshu/TALENT eligibility, empty-pool semantics, specialized removal, source-death semantics, or 690109/690110 gameplay as collateral work.

## Exit from this governance round

After governance validation:

```text
IMPLEMENTATION_BLOCKER-690222-BINDING-WEIGHTS-001 = CLOSED
690222 Research = FROZEN
690222 Gameplay = NOT_INTEGRATED
690222 Runtime = NOT_FROZEN
Stage12 Runtime Frozen = 4 / 7
Governance CI = 36369968103 / success / 1409 passed / demo PASS\nNEXT = Resume 690222 INTIMIDATION Runtime Integration
```
