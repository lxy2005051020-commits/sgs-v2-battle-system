# Stage 10 · Persistent State Runtime Integration · Design Freeze Record

> Project: 三国志战略版战斗模拟器 V2  
> Document Type: Formal Design Freeze Record  
> Scope: Stage 10 Persistent State Runtime Integration  
> Status: `DESIGN FROZEN`  
> Governance Authority: Stage10 Final Independent Design Freeze-Gate Audit  
> Freeze Date: 2026-09-15  

---

## 1. Freeze Metadata & Baseline

```text
Freeze Date:                      2026-09-15
Freeze Commit:                    populated by freeze commit / see repository history
Frozen Battle Base HEAD:          e11c897bd171db297e23f1727417f80a4f5010cd
Battle Repository:                lxy2005051020-commits/sgs-v2-battle-system
Battle Branch:                    stage10-persistent-state-research
Gameplay Authority Repository:    lxy2005051020-commits/sgs-state-mechanics-research
Gameplay Authority Branch:        main
Gameplay Authority HEAD:          a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
Final Audit Document:             stages/stage10/STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md
Final Audit Verdict:              PASS / DESIGN FREEZE ELIGIBLE
Final Audit Findings:             BLOCKER = 0, MAJOR = 0, MINOR = 0, HARDENING = 2
```

---

## 2. Frozen Audited Artifacts (Battle Repo)

The following exact file blobs were audited by the Final Independent Design Freeze-Gate Audit (`STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md`) and are hereby permanently frozen:

| Frozen Artifact | Repository Path | Frozen Audited Blob SHA |
|---|---|---|
| **Stage10 Architecture Design** | `stages/stage10/STAGE10.md` | `b87dc4c40abe13373e25cf4028ea27a08b413076` |
| **Stage7 Compatibility Addendum** | `stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md` | `64cdb7d86c8bda5b9123b49afcb924db7e1fd485` |
| **Stage8 Compatibility Addendum** | `stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md` | `4c1e22eda97bdc0ef74ab6175a28672845771ddc` |
| **Stage9 Compatibility Addendum** | `stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` | `737b058cefd08a1d0a08526436098a3455a8168f` |
| **Final Freeze-Gate Audit Report** | `stages/stage10/STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md` | `e32bef16453bc24ae7117e1e7d89ef8c95d4f0ad` |

> *Note on Post-Freeze Header Metadata*: The freeze commit modifies only top-level governance metadata (status banner) in `STAGE10.md`. The technical architecture and normative contracts within `STAGE10.md` are identical byte-for-byte to the audited blob `b87dc4c40abe13373e25cf4028ea27a08b413076`.

---

## 3. Pinned Gameplay Authority Artifacts

The Stage10 design contracts are grounded in canonical Gameplay Authority at HEAD `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`:

| Authority Artifact | Path in Authority Repository | Pinned Blob SHA |
|---|---|---|
| **Recovery RNG Edge Research** | `stage10/RECOVERY_RNG_EDGE_RESEARCH.md` | `d669659243db6d2060166121d92265ff507598e0` |
| **First Aid Zero-Loss Eligibility** | `stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md` | `11a36e5e60f875f3c820a5d1d81541ea2dabd24a` |
| **Targeted Research Promotion Record** | `stage10/STAGE10_TARGETED_RESEARCH_AUTHORITY_PROMOTION.md` | `99cb60ce3324fb547af35ef1e0490b603ad20eb0` |
| **First Aid Mechanism Contract** | `states/persistent/first_aid/MECHANISM_CONTRACT.md` | `2dc32ea70941660a0ac580601febfdd538822d36` |

---

## 4. Frozen Architecture Scope

The following 27 architectural contracts are frozen as immutable implementation specifications:

1. **Persistent Lifecycle Model**: Formal state application, duration countdown, and expiration semantics.
2. **PRE_BATTLE / Combat-Round Semantics**: Explicit PRE_BATTLE application domain and combat round alignment.
3. **Physical Expiration Rules**: Synchronous evaluation at action window completion (`current_round >= state.last_eligible_round`).
4. **Owner Death & Source Death Semantics**: Synchronous removal of bearer states on owner defeat; persistence of existing applications upon source death.
5. **DefeatCleanup Boundary**: Single authoritative `DefeatCleanupPort` executed across all destructive troop-loss paths.
6. **ActionProgressTracker Contract**: Round consumption tracking; maximum 1 action-start opportunity per owner per combat round.
7. **StateApplicationGenerationId**: Immutable generation identity allocated on initial application and every refresh.
8. **Refresh-and-Overwrite Semantics**: Container instance ID retention paired with fresh generation snapshot generation.
9. **FROZEN_APPLICATION Damage Lane**: Replay of locked application-time formula inputs and modifier decisions.
10. **Persistent Continuous Damage Architecture**: Periodic damage execution without live source attribute/troops queries.
11. **FIRST_AID AFTER_DAMAGE Architecture**: Reaction recovery opportunity triggered at reconciled damage aftermath checkpoints.
12. **RECUPERATION Action-Start Architecture**: Turn-based recovery opportunity evaluated at `UNIT_ACTION_START`.
13. **RecoveryOpportunityKind**: Strongly-typed enum discriminating `FIRST_AID_AFTER_DAMAGE` from `RECUPERATION_ACTION_START`.
14. **RecoveryOpportunity Admission Model**: Normalized gate sequence; Gate 2 required for FIRST_AID and not applicable for RECUPERATION.
15. **Simulator Recovery RNG Determinism Policy**: Exactly one `RandomSystem.chance(probability)` draw per admitted opportunity.
16. **PersistentSourceSkillGate**: Normative family-to-mode mapping (`ALWAYS_ACTIVE`, `QUERY_SKILL_RUNTIME`, `EXTERNAL_LIFECYCLE`).
17. **SkillRuntime Registry/Lookup**: Authoritative lookup by `(owner_id, skill_slot)` on `BattleContext`.
18. **RuleIntent Sibling Hierarchy**: Sibling typed intents (`Effect` vs `RecoveryOpportunity`) under `RuleIntent`.
19. **RuleIntentExecutionDescriptor**: Strongly-typed immutable descriptor carried by all intents.
20. **ExecutionRightDecision & Abort Scopes**: `ALLOW`, `REJECT_CURRENT(TARGET_DEFEATED)`, `ABORT_OWNER_STATE_REMAINDER(OWNER_DEFEATED)`, `ABORT_HOOK`.
21. **DamageAftermathPort**: Reconciled aftermath intake across standard, Share, Distribution, and Cleave pipelines.
22. **Stage9 Reaction Permission Ownership**: `ReactionPermissionPolicy.can_trigger_recovery` as sole authoritative permission arbiter.
23. **Stage9 Cleave / Share / Distribution Compatibility Ordering**: Target settlement $\to$ Sharer direct loss $\to$ Aftermath recovery $\to$ Attacker recovery.
24. **Battle Finalization / Teardown**: Admitted work draining upon victory latching; `StateLifecycleSystem.clear_all_on_battle_end` post-victory teardown.
25. **Provenance & Trace Architecture**: End-to-end `StateApplicationGenerationId` propagation across DTOs, results, and events.
26. **Dependency DAG / Composition Root**: Strictly acyclic architectural layering across all battle systems.
27. **Evidence Gate Boundaries**: Formal separation of frozen core contracts from deferred external mechanisms.

---

## 5. Frozen Gameplay Surface

Stage10 formally freezes runtime integration for exactly eight persistent states:

```text
1. 690072 BURN (灼烧)         - Continuous elemental damage
2. 690073 FLOOD (水攻)        - Continuous elemental damage
3. 690074 POISON (中毒)       - Continuous elemental damage
4. 690075 ROUT (溃逃)         - Continuous physical damage
5. 690076 SANDSTORM (沙暴)    - Continuous elemental damage
6. 690077 REBELLION (叛逃)    - Continuous true/direct damage
7. 690078 FIRST_AID (急救)    - After-damage reaction recovery
8. 690079 RECUPERATION (休整) - Action-start periodic recovery
```

---

## 6. Out of Stage10 Frozen Scope (Deferred / External Boundaries)

The following mechanisms remain explicitly deferred and are protected by Evidence Gate boundaries:

- **Full Evasion Implementation**: Consumes topology facts; full evasion system remains deferred.
- **Full Barrier / Shield Implementation**: Consumes absorption topology; full barrier remains deferred.
- **Universal Positive-State Dispel**: Universal dispel target selection remains deferred.
- **Undocumented / Future Persistent States**: Outside Stage10 scope.
- **Unresearched Critical Hit Variants**: Full crit system deferred; application-time locking handles Stage8-authorized crits only.
- **Future Stage 11+ Mechanisms**: Out of scope.

---

## 7. Frozen Engineering Decisions

The following decisions are frozen simulator engineering contracts (not official gameplay authority):

```text
CLASSIFICATION: ENGINEERING CONTRACT (NOT OFFICIAL GAMEPLAY AUTHORITY)
- Same-node deterministic ordering among persistent state intents
- StateApplicationGenerationId format and propagation model
- Strongly-typed DTO and execution descriptor schema
- Simulator one-draw RNG policy per admitted recovery opportunity via native RandomSystem.chance
- Battle-end teardown observation event schema (STATE_CLEARED_ON_BATTLE_END)
- DamagePipelineTrace frozen-application representation
```

---

## 8. Mandatory Build Verification Obligations

The two hardening items from the Final Design Freeze-Gate Audit are formally converted into mandatory build acceptance tests:

### S10-FG-H01 (Execution Descriptor Precondition Validation)
- Implementation build must include debug assertions verifying that `intent.execution_descriptor` is non-null and that `intent_owner_id` is populated before calling `evaluate_rule_intent`.
- Automated test must verify that `ExecutionRightSystem` reads only typed fields from `RuleIntentExecutionDescriptor` with zero duck-typing or attribute probing.

### S10-FG-H02 (RECUPERATION Aftermath-Fact Isolation)
- Implementation build must verify that `RecoveryOpportunitySystem` executing `RECUPERATION_ACTION_START` operates with `DamageAftermathFact = None` and never queries `ReactionPermissionPolicy`.
- Automated test must verify that passing an unexpected aftermath fact to an action-start opportunity raises an invariant violation or is strictly ignored.

---

## 9. Frozen Build Acceptance Contract

The **Mandatory Regression Plan V4** defined in `stages/stage10/STAGE10.md` §34 is hereby adopted as the **Frozen Build Acceptance Contract**. The implementation build must implement and pass all listed regression test cases across:
- `LIFECYCLE`
- `FIRST_AID AFTERMATH`
- `RECUPERATION`
- `RNG & ADMISSION GATES`
- `DEATH & EXECUTION RIGHT`
- `STAGE8 (FROZEN_APPLICATION & LIVE_RUNTIME)`
- `STAGE9 / AFTERMATH (Cleave, Share, Distribution, ASSAULT)`
- `BATTLE TEARDOWN`
- `GENERATION PROVENANCE & DTO PROPAGATION`
- `TWO-IMPLEMENTER CONFORMANCE SUITE`

---

## 10. Compatibility Addenda Governance & Precedence

### 10.1 Compatibility Governance
Stage10 implementation is governed by the original frozen stage specifications as amended by the Stage10 compatibility addenda:
- **Stage 7**: Governed by `STAGE7_DESIGN_FREEZE.md` except clauses explicitly reopened in `stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md`.
- **Stage 8**: Governed by `STAGE8_DESIGN_FREEZE.md` except clauses explicitly reopened in `stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md`.
- **Stage 9**: Governed by `STAGE9_DESIGN_FREEZE.md` except clauses explicitly reopened in `stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md`.

### 10.2 Authority Precedence Stack
In the event of any interpretive conflict during implementation, the following precedence stack is absolute:

```text
    Gameplay Authority (sgs-state-mechanics-research @ a9a05cef)
                    ↓
       Original Frozen Stage Contracts (Stage 7 / 8 / 9)
                    ↓
     Explicit Stage10 Compatibility Addenda (Stage 7 / 8 / 9)
                    ↓
         Stage10 Frozen Architecture Design (STAGE10.md)
                    ↓
              Production Implementation
```

If production implementation code conflicts with any upper layer, the implementation is incorrect.

---

## 11. Stage10 Build Entry Gate

Production implementation of Stage10 is authorized to begin **only** when all of the following conditions are satisfied:

```text
[ ] Build prompt created strictly adhering to STAGE10_DESIGN_FREEZE.md
[ ] Implementation builds against exact frozen artifact blobs
[ ] Zero gameplay decisions or architectural choices invented by implementer
[ ] Existing baseline tests remain 100% green (753/753 passed)
[ ] Implementation modifies only production code and tests within authorized Stage10 scope
```

### Invariant: Strict Prohibition of Implementation Reinterpretation
If an implementer discovers an apparent ambiguity or unhandled edge case during code construction:
1. **STOP BUILD IMMEDIATELY.**
2. Do **NOT** choose a subjective interpretation.
3. Submit a formal `DESIGN REOPEN REQUEST` with detailed triage against Gameplay Authority.

---

## 12. Design Reopen Policy

Any proposed change affecting the following areas constitutes a **Design Reopen**:
- Gameplay observable behavior or formulas
- Execution right, defeat boundaries, or abort scopes
- Event ordering or hook dispatch sequences
- RandomSystem determinism or RNG draw count
- Lifecycle or state expiration boundaries
- Public DTOs or generation provenance contracts
- Stage 7 / 8 / 9 compatibility boundaries

A Design Reopen requires:
1. Formal justification and impact analysis.
2. Independent design audit.
3. Creation of an updated design revision and freeze record.

### Permitted Non-Reopen Changes
Implementers are permitted to adjust internal details that do not alter the frozen observable contract:
- Private helper function names and module layouts within `sgs_v2`
- Test organization and internal assertion structure
- Non-observable performance refactoring

---

## 13. Frozen Artifact Integrity Verification Table

Future audits, build steps, and CI checks can verify freeze integrity using Git plumbing commands:

```bash
# Verify Stage10 Architecture Design blob
git rev-parse HEAD:stages/stage10/STAGE10.md
# Expected: b87dc4c40abe13373e25cf4028ea27a08b413076 (audited)

# Verify Stage7 Compatibility Addendum blob
git rev-parse HEAD:stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md
# Expected: 64cdb7d86c8bda5b9123b49afcb924db7e1fd485

# Verify Stage8 Compatibility Addendum blob
git rev-parse HEAD:stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md
# Expected: 4c1e22eda97bdc0ef74ab6175a28672845771ddc

# Verify Stage9 Compatibility Addendum blob
git rev-parse HEAD:stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md
# Expected: 737b058cefd08a1d0a08526436098a3455a8168f

# Verify Final Design Freeze-Gate Audit blob
git rev-parse HEAD:stages/stage10/STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md
# Expected: e32bef16453bc24ae7117e1e7d89ef8c95d4f0ad
```

Any blob hash deviation indicates contract drift and invalidates the freeze.

---

## 14. Formal Freeze Conclusion

```text
================================================================================
STAGE10 DESIGN FREEZE FORMALIZATION: COMPLETE
STATUS: STAGE10 ARCHITECTURE DESIGN FROZEN
NEXT AUTHORIZED STEP: STAGE10 BUILD PROMPT PREPARATION
================================================================================
```
