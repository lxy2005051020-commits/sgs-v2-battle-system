# Stage12 690222 INTIMIDATION Runtime Integration

Date: 2026-09-28  
Status: IMPLEMENTED / RUNTIME_FROZEN_TO_CONTRACT

## Current gate

```text
690222 Research = FROZEN
690222 Gameplay = IMPLEMENTED
690222 Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Stage12 Runtime Frozen = 5 / 7
NEXT = 690109 SABOTAGE Runtime Integration
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


## Runtime integration resume implementation

The production integration now uses the canonical Shared Foundation owners rather
than a 690222 lifecycle facade.

- loaded Skill Providers are exact-identity validated before taxonomy filtering,
  then ordered by RD-SF-002;
- ACTIVE (including preparation-required ACTIVE), ASSAULT, PASSIVE, COMMAND,
  and TROOP are supported eligible Provider families;
- FORMATION is the frozen exclusion; TALENT remains an unsupported runtime
  boundary rather than a Research-confirmed exclusion, and
  Normal Attack is not a Provider candidate;
- empty supported pool remains UNSUPPORTED_BOUNDARY;
- one candidate consumes zero binding RNG; multiple candidates consume exactly
  one BattleContext.random.choice after all non-writing dependency preflights;
- the selected full SkillProviderRef is stored as StateInstance.bound_provider_ref;
- CREATE and REFRESH perform binding decisions, while effectiveness RESUME
  preserves the same binding and consumes zero binding RNG;
- Provider suppression is represented through ProviderValidity and dependency
  causes without mutating SkillRuntime.enabled;
- selected preparation-required ACTIVE work is interrupted with PROVIDER scope;
- explicit ProviderDependency controls source gating and downstream Provider-owned
  state effectiveness; source attribution alone does not create dependency;
- tested generic cleanse rejects Intimidation; specialized removal stays an
  unsupported boundary; source-death behavior is not invented.

RD-SF-006 provenance remains PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN.

### TROOP consumer audit

The production tree has Provider-level TROOP identity and suppression support,
but no separate concrete TROOP execution consumer is currently present. The
integration therefore represents suppression truth without inventing a consumer.
The independent Runtime Freeze Audit adjudicated this as a **NON-BLOCKING NOTE**:
690222 owns the canonical ProviderValidity suppression truth, while any future
concrete TROOP consumer must consume that truth rather than invent a second owner.

### Exit gate

This integration round may advance gameplay only to:

    690222 Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
    690222 Runtime = NOT_YET_FROZEN
    Stage12 Runtime Frozen = 4 / 7
    NEXT = 690222 INTIMIDATION Independent Runtime Freeze Audit

No statement in this document freezes 690222 Runtime.


## Final implementation checkpoint

```text
Implementation code SHA = 834f6e7508c8006342ff37593454ef91d8e8d0a4
Push CI = 36372015077 / success / 1453 passed / demo PASS
PR CI = 36372018782 / success / 1453 passed / demo PASS
Research repository = READ ONLY / UNCHANGED
Stage11 Reopen Required = NO
Stage13 / Stage14 / Stage15 Active = NO

690222 Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690222 Runtime = NOT_YET_FROZEN
Stage12 Gameplay Implementation = 5 / 7
Stage12 Runtime Frozen = 4 / 7
NEXT = 690222 INTIMIDATION Independent Runtime Freeze Audit
```

The integration round intentionally stops here. Runtime freeze, freeze-count
increment, and any independent-audit authority remain out of scope until the
separate 690222 Independent Runtime Freeze Audit passes.


## Independent Runtime Freeze closure — 2026-09-28

The separate independent audit has now passed.

```text
690222 Research = FROZEN
690222 Gameplay = IMPLEMENTED
690222 Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit test SHA = 0b3e5d62b1c2e25e4b2177ccfa5dd456819ddc96
Push CI = 36374423908 / success
PR CI = 36374443142 / success
pytest = 1483 passed
demo = PASS
BLOCKER = 0
unresolved MAJOR = 0
Stage12 Gameplay Implementation = 5 / 7
Stage12 Runtime Frozen = 5 / 7
Stage11 Reopen Required = NO
Research Reopen Required = NO
Shared Foundation Reopen Required = NO
NEXT = 690109 SABOTAGE Runtime Integration
```

Freeze authority: `STAGE12_690222_INTIMIDATION_RUNTIME_FREEZE_AUDIT.md`.

Earlier `IMPLEMENTED_PENDING_RUNTIME_AUDIT` and `NOT_YET_FROZEN` blocks in this file are retained as historical integration-round exit records; they no longer describe the current project gate.
