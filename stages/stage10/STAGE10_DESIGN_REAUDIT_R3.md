# Stage10 Independent Design Re-Audit Round 3

> Project: 三国志战略版战斗模拟器 V2  
> Audit mode: `INDEPENDENT / ADVERSARIAL / REPOSITORY-DRIVEN`  
> Scope: Stage10 Architecture Design Draft V3 Independent Design Re-Audit  
> Audit date: `2026-09-15`  
> Production implementation: `NOT AUTHORIZED`  
> Design freeze: `NOT AUTHORIZED`

---

## 0. Metadata

### 0.1 Audited repository identity

Battle Runtime repository:

```text
lxy2005051020-commits/sgs-v2-battle-system
branch: stage10-persistent-state-research
Audited Battle HEAD: dfe9008ab74269c3239c214b65d25d626127884a
Commit message: docs(stage10): repair round-2 architecture findings
Working tree: CLEAN
```

Audited document blob SHAs:

```text
stages/stage10/STAGE10.md
blob SHA: 1519189a744a0a7c4b31f8e834a08b4df39496ad

stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md
blob SHA: 64cdb7d86c8bda5b9123b49afcb924db7e1fd485

stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md
blob SHA: 4c1e22eda97bdc0ef74ab6175a28672845771ddc

stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md
blob SHA: 737b058cefd08a1d0a08526436098a3455a8168f

stages/stage10/STAGE10_DESIGN_REAUDIT_R2.md
blob SHA: d4e3185b7f35f04373a439f3048976aa7a581182
```

Gameplay Mechanism Authority repository:

```text
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
Audited Gameplay Authority HEAD: a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
Commit message: docs(stage10): formalize targeted research authority promotion (R2-A4)
Working tree: CLEAN
```

Gameplay Authority key document blobs:

```text
stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md
blob SHA: 11a36e5e60f875f3c820a5d1d81541ea2dabd24a

stage10/RECOVERY_RNG_EDGE_RESEARCH.md
blob SHA: d669659243db6d2060166121d92265ff507598e0

stage10/STAGE10_TARGETED_RESEARCH_AUTHORITY_PROMOTION.md
blob SHA: 99cb60ce3324fb547af35ef1e0490b603ad20eb0

states/persistent/first_aid/MECHANISM_CONTRACT.md
blob SHA: 2dc32ea70941660a0ac580601febfdd538822d36
```

### 0.2 Scope verification and baseline integrity

Compare between R2 input baseline (`ecde9d1...`) and current HEAD (`dfe9008...`):

```text
41cd51f docs(stage9): add Stage10 aftermath compatibility addendum
dfe9008 docs(stage10): repair round-2 architecture findings
```

Independent verification confirms:
- Production code (`sgs_v2/**/*.py`): **UNTOUCHED**
- Test suites (`tests/**`): **UNTOUCHED**
- Verification scripts (`demo.py`): **UNTOUCHED**
- Workflow definitions (`.github/workflows/**`): **UNTOUCHED**

Baseline execution verification:

```text
pytest -q
→ 753 passed in 1.88s

python demo.py
→ PASS (full 8-round simulation executed to completion; A team victory on round 7)
```

GitHub Actions CI run status:

```text
Run ID: 34929855445
Head SHA: dfe9008ab74269c3239c214b65d25d626127884a
Event: pull_request #6
Conclusion: SUCCESS
Job ID: 104255636618
```

The green CI status confirms Stage 1-9 baseline integrity; it does not constitute proof of Stage 10 design correctness.

---

## 1. Executive Verdict

```text
Round 2 findings reviewed (12 total):
CLOSED           = 10
PARTIALLY CLOSED = 2  (S10-R2-M02, S10-R2-N02)
STILL OPEN       = 0
REGRESSED        = 0

New Round 3 findings:
BLOCKER   = 1  (S10-R3-B01: Target Defeat vs Owner Defeat Conflation in ExecutionRight Abort Scope)
MAJOR     = 2  (S10-R3-M01: RecoveryOpportunitySystem Gate 2 Damage Dependency on RECUPERATION;
                S10-R3-M02: ExecutionRightSystem.evaluate_rule_intent Typed Input Contract Underdefined)
MINOR     = 1  (S10-R3-N01: Native RandomSystem.chance Draw Invariant Documentation)
HARDENING = 0

AUTHORITY SYNC VERDICT = PASS (Canonical Authority main @ a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe)

TWO-IMPLEMENTER TEST = FAIL (Scenario 5 fails determinism)
PRODUCTION WIRING TEST = PASS (DAG constructible)

FINAL AUDIT VERDICT = FAIL / DESIGN REPAIR ROUND 3 REQUIRED
DESIGN FREEZE ELIGIBLE = NO
STAGE10 IMPLEMENTATION AUTHORIZED = NO
```

### Executive Summary

Draft V3 represents significant progress:
1. **Gameplay Authority Synchronization is fully closed (`PASS`)**: Commit `a9a05cef` on `main` officially incorporates targeted research on zero-loss FIRST_AID eligibility (`S10-TR-03`), recovery RNG determinism (`S10-TR-01/02`), and the formal promotion record. All invalid SHA references have been purged.
2. **Stage9 Compatibility Reopen is formalized (`PASS`)**: `STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` formally authorizes `SourceType.ASSAULT` for `ReactionPermissionPolicy.can_trigger_recovery()` and reconciles Cleave ordering by preserving Stage9 frozen order (`Cleave target settlement → Share direct loss → DamageAftermathPort → attacker recovery → callbacks`).
3. **End-to-end generation provenance is closed**: Table 13.2 normatively maps `StateApplicationGenerationId` across all 14 request/result/trace/event DTOs.
4. **`PersistentSourceSkillGate` is normatively mapped**: Table 12.1 correctly specifies gate modes across DOTs, FIRST_AID, RECUPERATION, and External Auras.
5. **Battle-end teardown is established**: `StateLifecycleSystem.clear_all_on_battle_end(context)` cleanses all states after finalization drain.

**Why Draft V3 fails Design Freeze Eligibility:**
Draft V3 conflates **State Owner Defeat** and **Target Defeat** in its ExecutionRight abort scope (`ABORT_OWNER_STATE_REMAINDER`). In §4.2 line 259, it declares that `ABORT_OWNER_STATE_REMAINDER` discards all remaining intents belonging to the state owner, while in §4.3 line 287 it states that it skips intents targeting the defeated unit. In a multi-intent batch where state owner P1's effect kills target P2, this ambiguity causes one implementer to cancel P1's subsequent intents targeting living P3, while another implementer executes them. Because two conforming implementations produce different observable gameplay outcomes, this is a **BLOCKER** under the Two-Implementer Test. Furthermore, `RecoveryOpportunitySystem` Gate 2 unconditionally requires `DamageAftermathFact`, breaking non-damage `RECUPERATION`.

---

## 2. Repository / Authority Baseline

### 2.1 Gameplay Authority Canonical State

Gameplay Authority repository `sgs-state-mechanics-research` on branch `main`:
- Canonical HEAD: `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`
- Promotion commit chain verified:
  - `4661f4ffa1074045ce17d9158499dc03a8dfbec3`: complete targeted recovery RNG research reports (`S10-TR-01`, `S10-TR-02`), tools, and parsed logs.
  - `0b9e172a4d3ce3b29025347b086738c0253e56ac`: `states/persistent/first_aid/MECHANISM_CONTRACT.md` updated with zero-loss, full-troop, and trigger eligibility alignment (`S10-TR-03`).
  - `7f6557360783e9913798cda9efa8bc89a8979305`: local provenance exhaustion and recovery report (`R2-A3`).
  - `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`: formalization of targeted research authority promotion (`R2-A4`, `PROMOTION_STAGE10_R2_A4.md`).

### 2.2 SHA Reference Hygiene Audit

Search for deprecated/erroneous commit SHAs:
- `4661f4fa3d3ef4237d8258e7275ec9f79888ea4e`: **0 occurrences** across repository.
- `0b9e1722e03889ba488d55c8c5c7dc2cf39ee484`: **0 occurrences** across repository.
All active design documents (`STAGE10.md`, `README.md`, `STAGE10_TARGETED_RESEARCH_QUESTIONS.md`) reference canonical full SHA `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe` and genuine promotion commits.

Authority synchronization status: **PASS**.

---

## 3. Round 2 Finding Closure Matrix

| Finding | Severity | R2-B Claim | Independent R3 Verification | R3 Verdict |
|---|---|---|---|---|
| `S10-R2-B01` | BLOCKER | REPAIR CLAIMED | `STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` created; Cleave ordering formally reconciled to Stage9 frozen order (`Cleave target settlement → Share direct loss → DamageAftermathPort → attacker recovery → callbacks`). | `CLOSED` |
| `S10-R2-B02` | BLOCKER | REPAIR CLAIMED | Formally authorized `SourceType.ASSAULT` in Stage9 addendum §4.3 and `ReactionPermissionPolicy.can_trigger_recovery()`. Aligned with authority `Pursuit_Counterattack: ELIGIBLE`. | `CLOSED` |
| `S10-R2-M01` | MAJOR | CLOSED BY AUTHORITY SYNC | Formally promoted in R2-A4 to Gameplay Authority `main` @ `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`. Verified in actual authority git tree. | `CLOSED` |
| `S10-R2-M02` | MAJOR | REPAIR CLAIMED | Nominal 3-way split (ExecutionRightSystem, RuleHookSystem, EffectExecutor) introduced, but `ABORT_OWNER_STATE_REMAINDER` conflates owner defeat with target defeat in §4.2 vs §4.3. Interface signature underdefined. | `PARTIALLY CLOSED` |
| `S10-R2-M03` | MAJOR | REPAIR CLAIMED | Table 12.1 added with normative mappings for DOTs, FIRST_AID, RECUPERATION, and External Auras. Explicit semantics for `ALWAYS_ACTIVE`, `QUERY_SKILL_RUNTIME`, and `EXTERNAL_LIFECYCLE`. | `CLOSED` |
| `S10-R2-M04` | MAJOR | REPAIR CLAIMED | Table 13.2 added with complete 14-entity propagation matrix for `StateApplicationGenerationId`. Section 13.3 partitions immutable snapshot from JIT dynamic queries. | `CLOSED` |
| `S10-R2-M05` | MAJOR | REPAIR CLAIMED | Section 8.1 defines `StateLifecycleSystem.clear_all_on_battle_end(context)` executing after victory latched and admitted work drained. Emits `STATE_CLEARED_ON_BATTLE_END`. | `CLOSED` |
| `S10-R2-N01` | MINOR | REPAIR CLAIMED | Section 9.1 freezes exact 7-step ordering at `UNIT_ACTION_START`: set acting unit → mark action start → publish observation → trigger/hook evaluation → expiry. | `CLOSED` |
| `S10-R2-N02` | MINOR | REPAIR CLAIMED | Normalized sequence between §18 and §22, but §22 Gate 2 introduces an unconditional `DamageAftermathFact` dependency that breaks `RECUPERATION`. | `PARTIALLY CLOSED` |
| `S10-R2-N03` | MINOR | REPAIR CLAIMED | Section 34 updated with regression obligations for ASSAULT, battle teardown, generation propagation, and mixed-hook execution. | `CLOSED` |
| `S10-R2-H01` | HARDENING | ACCEPTED FOR BUILD | Exactly-once defeat-cleanup conformance spy accepted and incorporated into §34 build obligations. | `CLOSED` |
| `S10-R2-H02` | HARDENING | ACCEPTED FOR BUILD | Frozen-lane zero live formula read instrumentation accepted and incorporated into §34 build obligations. | `CLOSED` |

---

## 4. Stage7 Compatibility Audit

### 4.1 Dispatch and Atomicity
Stage7 compatibility preserves:
- Deterministic pre-collection pass via `TriggerSystem.collect()`.
- Single immutable tuple batch dispatch.
- No dynamic re-collection, re-sorting, or event feedback loops.

### 4.2 Defect in ExecutionRight Abort Scope (Root of S10-R3-B01)
`STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md` §4.3 & §6 clearly distinguished:
- `OWNER_DEFEATED`: Hook actor / state-resolution owner died. Discard remaining `STATE_RESOLUTION` intents for that defeated owner.
- `TARGET_DEFEATED`: An effect's target died. Deny execution of that specific intent targeting the dead unit; unrelated intents for surviving targets proceed.

Draft V3 §4.2 & §4.3 attempted to synthesize these into a single decision `ABORT_OWNER_STATE_REMAINDER`:
- In §4.2 line 259: "All remaining intents/effects in the current batch belonging to the same state/owner are discarded."
- In §4.3 line 287: "skips any remaining intents targeting Unit X."
This conflates State Owner Defeat with Target Defeat, creating a gameplay ambiguity detailed in Section 9.

Stage7 Compatibility verdict: **FAIL (due to execution-right decision conflation)**.

---

## 5. Stage8 Compatibility Audit

`STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md` remains authoritative and unchanged:
- Live runtime pipeline (`LIVE_RUNTIME`) is untouched.
- `FROZEN_APPLICATION` is a dedicated calculation basis for persistent continuous damage.
- Historical source identity, frozen application-time source attributes, frozen formula policy, and locked modifier plan are uniquely consumed by `DamageSystem`.
- Current target attributes, target defense, current weakness gate, and tick-time base formula RNG are live-evaluated.
- Source unit death does not recalculate or cancel existing DOT ticks.
- `REBELLION` route and defense policy are locked at application/refresh.

Stage8 Compatibility verdict: **PASS / UNCHANGED**.

---

## 6. Stage9 Compatibility Audit

### 6.1 Formal Reopen Verification
`STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md` was checked in at commit `41cd51f` and blob `737b058c...`.
It establishes a formal, narrow reopen covering:
1. `DamageAftermathPort` insertion into settlement routes.
2. Defeat cleanup coordination on lethal damage.
3. Cleave derived damage settlement ordering.
4. `ReactionPermissionPolicy.can_trigger_recovery()` allow-list extension for `SourceType.ASSAULT`.

### 6.2 Settlement Route Invariants
- **NoPartition**: Target settlement → defeat cleanup if fatal → `DamageAftermathPort` if surviving → callbacks.
- **Share**: Target settlement → if target survives: commit sharer `DirectTroopLoss` → defeat cleanup on sharer if dead → `DamageAftermathPort(target)` → callbacks. Share arithmetic remains preplanned; FIRST_AID does not retroactively alter share calculations.
- **Distribution**: Drain participant `DirectTroopLoss` in fixed slot order → target settlement → `DamageAftermathPort(target)` if surviving.
- **Chain**: Restricted feedback settlement remains frozen; `can_trigger_recovery` returns `False`.
- **DirectTroopLoss**: Non-damage internal troop loss never generates a `DamageAftermathFact`.
- **BattleFinalization**: Admitted `DamageInstance` drains local aftermath under `VICTORY_LATCHED`; no new global branches are admitted.

Stage9 Compatibility verdict: **PASS**.

---

## 7. ASSAULT / FIRST_AID Permission Audit

### 7.1 Authority Alignment
Official Gameplay Authority (`states/persistent/first_aid/MECHANISM_CONTRACT.md` §3) mandates:
```text
Pursuit_Counterattack: ELIGIBLE (突击与反击伤害可触发急救)
```
In Stage9, pursuit skills are classified under `SourceType.ASSAULT`.

### 7.2 Permission Granularity & Blast-Radius Audit
The audit examined whether adding `SourceType.ASSAULT` to `ReactionPermissionPolicy.can_trigger_recovery()` creates unintended side-effects:
1. In production runtime, `can_trigger_recovery()` is queried in exactly two contexts:
   - `DamageAftermathPort` (for FIRST_AID eligibility).
   - `CleaveDerivedDamageSystem` (line 195: for Cleave aftermath and attacker recovery; Cleave uses `SourceType.CLEAVE`, never `ASSAULT`).
2. In game mechanics, Assault skills (突击战法) deal weapon damage. When an assault skill hits a target, it legitimately triggers:
   - Target's FIRST_AID (急救).
   - Attacker's lifesteal/leech (倒戈), if the attacker has an active lifesteal state.
Both reaction behaviors are valid under official game rules.
3. `can_trigger_recovery()` strictly governs recovery reactions from damage events. It does not grant general action rights, combo permissions, or evasion bypass.
4. `ReactionPermissionPolicy.can_trigger_recovery(source_type)` is confirmed as the **Single Authoritative Permission Owner**. No second allow-list exists in `TriggerSystem` or `DamageAftermathPort`.

ASSAULT Permission verdict: **PASS**.

---

## 8. DamageAftermath / Cleave / Share / Distribution Audit

### 8.1 Cleave Exact Ordering Reconciliation
Draft V3 §24.4 reconciles Cleave ordering with Stage9 frozen runtime:

```text
1. Cleave Target Settlement:
   - DamageResolutionSystem.settle(target, assigned)
   - If target defeated:
       - DefeatCleanupPort.commit_defeat(target)
       - FinalizationCoordinator.observe_damage_instance_death
       - Discard pending sharer direct loss
       - Abort Aftermath (target dead)
       - Return CleaveDerivedDamageResult(TARGET_DEATH_INTERRUPT)
2. Sharer Direct Troop Loss (if target survives):
   - Commit sharer DirectTroopLoss
   - If sharer defeated:
       - DefeatCleanupPort.commit_defeat(sharer)
       - FinalizationCoordinator.observe_damage_instance_death
3. Damage Aftermath Recovery Checkpoint (DamageAftermathPort):
   - Invoke shared DamageAftermathPort(target)
   - Executes target FIRST_AID if eligible
4. Attacker Recovery:
   - Execute attacker recovery (倒戈) using pre-calculated CleaveRecoveryFact(assigned)
5. Callbacks & Finalization:
   - Callbacks accepted; Cleave completed
```

Verification points:
- **Share calculation timing**: Fixed at initial partition plan creation, before target settlement.
- **Sharer death latching**: Observed immediately upon direct loss commit, prior to aftermath.
- **Share fact immutability**: FIRST_AID on target occurs *after* sharer loss and cannot retroactively modify sharer direct loss.
- **Attacker recovery basis**: Built from `assigned` target damage, independent of target's post-FIRST_AID troop state.

Cleave / Share / Distribution audit verdict: **PASS**.

---

## 9. ExecutionRight Ownership Audit

### 9.1 Three-Way Architectural Boundary
Draft V3 §4.1 partitions roles:
- **Decision Owner**: `ExecutionRightSystem` (evaluates `evaluate_rule_intent`)
- **Dispatch Owner**: `RuleHookSystem` (orchestrates batch iteration and abort control)
- **Execution Router**: `EffectExecutor` (routes admitted Effects; performs zero secondary permission checks)

### 9.2 The Conflation Defect (Finding S10-R3-B01)
In §4.2, Draft V3 defines:
```text
ABORT_OWNER_STATE_REMAINDER
→ Current Effect is aborted because state owner is defeated/invalidated.
→ All remaining intents/effects in the current batch belonging to the same state/owner are discarded.
→ Effects belonging to other living units in the same batch proceed.
```
In §4.3 lines 284-288, Draft V3 describes:
```text
2. Effect B evaluation:
   - RuleHookSystem requests evaluation from ExecutionRightSystem for Effect B (target/owner Unit X).
   - ExecutionRightSystem detects Unit X is defeated.
   - ExecutionRightSystem returns ABORT_OWNER_STATE_REMAINDER.
   - RuleHookSystem records typed abort for Effect B and skips any remaining intents targeting Unit X.
   - Effect B is NEVER dispatched to EffectExecutor.
```

**Contradiction and Ambiguity**:
1. §4.2 line 259 defines the abort scope as: **all remaining intents belonging to the same state/owner**.
2. §4.3 line 287 defines the abort scope as: **skips any remaining intents targeting Unit X**.
3. In §4.3, the author assumed `(target/owner Unit X)` were the same unit (as in a self-inflicted DOT tick). However, in general combat:
   - State Owner $P_1$ (e.g. caster or bearer of an aura/skill) applies effects to multiple targets.
   - Target $P_2$ is killed by Intent A.
   - Intent B (same state owner $P_1$, target $P_2$) cannot execute because target $P_2$ is dead.
   - Intent C (same state owner $P_1$, target $P_3$) targets living unit $P_3$.
   - Intent D (state owner $P_4$, target $P_3$) targets living unit $P_3$.

**Concrete Failure Scenario**:
- **Implementer 1** follows §4.2 line 259: ExecutionRightSystem returns `ABORT_OWNER_STATE_REMAINDER`. RuleHookSystem discards all remaining intents belonging to state owner $P_1$. **Intent C is aborted**, even though $P_1$ and $P_3$ are alive.
- **Implementer 2** follows §4.3 line 287: RuleHookSystem only skips intents targeting dead unit $P_2$. **Intent C executes**.

Two conforming implementations produce divergent observable gameplay!
Under Gameplay Authority and Stage7 Addendum §4.3, the decision must distinguish:
- `OWNER_DEFEATED`: State owner died → abort remaining state-resolution intents for that owner.
- `TARGET_DEFEATED`: Effect target died → reject that specific intent (`REJECT_CURRENT(TARGET_DEFEATED)`), while intents for living targets proceed.

ExecutionRight Ownership verdict: **FAIL / BLOCKER (`S10-R3-B01`)**.

---

## 10. RuleIntent Ordering Audit

### 10.1 Sibling RuleIntent Model (Model B)
Draft V3 §20 defines:
```text
TriggerIntentBatch.ordered_intents: tuple[Effect | RecoveryOpportunity, ...]
```
Given a mixed batch:
```text
Effect A → RecoveryOpportunity B → Effect C
```
`RuleHookSystem` processes the tuple sequentially:
1. Intent A (`Effect`) → checked by `ExecutionRightSystem` → forwarded to `EffectExecutor`.
2. Intent B (`RecoveryOpportunity`) → checked by `ExecutionRightSystem` → forwarded to `RecoveryOpportunitySystem`.
3. Intent C (`Effect`) → checked by `ExecutionRightSystem` → forwarded to `EffectExecutor`.

There is no pre-sorting by type, no dual lists, and no EventBus re-injection. Ordered outcome union `RuleIntentResult = EffectExecutionResult | RecoveryOpportunityResult | AbortedRuleIntentResult` guarantees 1-to-1 correspondence with collected intents.

RuleIntent Ordering verdict: **PASS**.

---

## 11. PersistentSourceSkillGate Audit

### 11.1 Normative Family Mapping (Table 12.1)
The normative mapping table is fully specified:
- **Periodic DOTs** (`BURN`, `FLOOD`, `POISON`, `ROUT`, `SANDSTORM`, `REBELLION`): `ALWAYS_ACTIVE`. Source death or silence does not cancel or suppress ticks.
- **FIRST_AID (Passive/Command)**: `QUERY_SKILL_RUNTIME`. Queries `SkillRuntime.enabled`. Temporary deactivation suppresses opportunity; duration continues.
- **FIRST_AID (Active)**: `ALWAYS_ACTIVE`. Buff runs to duration completion.
- **RECUPERATION (Passive/Command)**: `QUERY_SKILL_RUNTIME`. Queries `SkillRuntime.enabled`.
- **RECUPERATION (Active)**: `ALWAYS_ACTIVE`.
- **External Aura**: `EXTERNAL_LIFECYCLE`. External provider controls physical lifecycle.

### 11.2 Safety against Source Death Regressions
- `QUERY_SKILL_RUNTIME` queries only `SkillRuntime.enabled`. It explicitly does **not** query `source.is_alive`.
- Source death does not automatically disable `SkillRuntime.enabled`.
- DOTs do not query `SkillRuntime.enabled` at all. Source death cannot inadvertently cancel DOT damage ticks.

PersistentSourceSkillGate verdict: **PASS**.

---

## 12. Generation Provenance Audit

### 12.1 End-to-End Propagation Matrix (Table 13.2)
Draft V3 §13.2 defines typed propagation across 14 entities:
- Direct carriers: `StateInstance.current_generation_id`, `StateGenerationSnapshot.application_generation_id`, `DamageRequest.source_generation_id`, `DamageResult.source_generation_id`, `RecoveryRequest.source_generation_id`, `RecoveryResult.source_generation_id`, `DamageAftermathFact.source_state_generation`, `DamagePipelineTrace.source_generation_id`.
- Observation events: `STATE_APPLIED`, `STATE_REFRESHED` (old/new), `STATE_EXPIRED`, `STATE_REMOVED`, `DAMAGE_RESOLVED`, `RECOVERY_RESOLVED`.

### 12.2 Pending Intent Generation Invariant
In the pending intent test:
- $G_1$ produces intent $I_1$ carrying immutable snapshot.
- State refreshes to $G_2$ (new generation ID, new potency, new window).
- $I_1$ executes:
  - Potency, rates, source attributes, formula policy, source skill identity: **immutable $G_1$ snapshot**.
  - Dynamic skill gate: queries current `SkillRuntime.enabled` for $G_1$'s source skill.
  - Target defense, missing troops, healing ban: **current JIT state**.
  - Result & Event generation ID: **$G_1$ generation ID**.
No rebinding or generation leakage occurs.

Generation Provenance verdict: **PASS**.

---

## 13. Battle-End Cleanup Audit

### 13.1 Timeline and Boundary Separation
Draft V3 §8.1 separates gameplay expiration from battle teardown:
```text
1. Victory Condition Met → Victory Latched (VICTORY_LATCHED)
2. Admitted Work Drains (DamageInstance completes, local aftermath finishes)
3. Battle Finalization Latch (FINALIZED)
4. State Teardown: StateLifecycleSystem.clear_all_on_battle_end(context)
5. Return BattleResult
```
- Scope: Cleanses all states across all units (winners and losers).
- Event: `STATE_CLEARED_ON_BATTLE_END` (observation-only).
- Post-battle inspection of `context.states` yields clean state with zero ghost instances.

Battle-End Cleanup verdict: **PASS**.

---

## 14. Recovery Admission / RNG Policy Audit

### 14.1 Engineering RNG Determinism Policy
- Simulator policy: Every ADMITTED opportunity consumes exactly one `context.random.chance(probability)` call.
- Official authority status: PRNG consumption for $p=0$, $p=1$, and $\text{gap}=0$ is officially `UNKNOWN / UNOBSERVABLE`. The one-draw policy is strictly labeled **Simulator Engineering Policy**.
- Production verification: Production `sgs_v2/battle_core/random_system.py` lines 36-39:
  ```python
  def chance(self, probability: float) -> bool:
      if not 0.0 <= probability <= 1.0:
          raise ValueError("probability must be in [0.0, 1.0]")
      return self.random() < probability
  ```
  `RandomSystem.chance()` always evaluates `self.random() < probability`, consuming exactly one draw for $p=0.0$ and $p=1.0$ without shortcutting. No RandomSystem modification or reopen is required.

### 14.2 The RECUPERATION Dependency Defect (Finding S10-R3-M01)
In §22 lines 1366-1370, Draft V3 specifies the normalized admission sequence:
```text
2. Hit Topology & Reaction Permission Gate:
   - Validate DamageAftermathFact.hit_topology == DamageHitTopology.RESOLVED_HIT.
   - Validate ReactionPermissionPolicy.can_trigger_recovery(source_type) == True.
   - If not resolved hit or source ineligible: abort opportunity; NO RNG draw.
```
`RecoveryOpportunitySystem` is the unified executor for:
- `FIRST_AID` (damage aftermath recovery)
- `RECUPERATION` (action-start turn recovery)
`RECUPERATION` does not originate from a damage event and has no `DamageAftermathFact`. Unconditionally validating `DamageAftermathFact.hit_topology` in Gate 2 will cause `RECUPERATION` to be aborted or crash on `None`.
Gate 2 must explicitly specify: **`NOT_APPLICABLE` for non-aftermath recovery (e.g. RECUPERATION)**.

Recovery Admission verdict: **FAIL / MAJOR (`S10-R3-M01`)**.

---

## 15. ActionProgress / Lifecycle Audit

### 15.1 ActionProgressTracker Exact Sequence (§9.1)
The exact 7-step sequence at `UNIT_ACTION_START`:
1. `set_current_acting_unit(owner_id)`
2. `mark_action_start(owner_id, current_round)`
3. Publish `UNIT_ACTION_START` event
4. Collect action-start triggers and persistent opportunities
5. Execute hook/intent batch via `RuleHookSystem`
6. Synchronous physical expiration check (`current_round >= last_eligible_round`)
7. Hand off to Action Phase

For an $N=1$ persistent state applied in Round 1:
- Round 1 ActionStart: steps 4 & 5 collect and execute its 1st opportunity.
- Step 6: `current_round (1) >= last_eligible_round (1)` → state expires immediately after the hook batch.
- Exactly one opportunity is produced; state is cleaned up prior to regular action.

ActionProgress / Lifecycle verdict: **PASS**.

---

## 16. Dependency / Composition Audit

### 16.1 Construction DAG
The composition root order in §32 is acyclic and constructible:
```text
1. BattleContext registries & ActionProgressTracker
2. UnitRegistry, TroopSystem, StateRegistry, StateLifecycleSystem, ExecutionRightSystem
3. DefeatCleanupPort
4. RecoverySystem + RecoveryOpportunitySystem
5. Stage8 Formula and Rule components
6. DamageResolutionSystem, DirectTroopLoss, DamagePartitionCoordinator, BattleFinalizationCoordinator
7. TriggerSystem
8. DamageAftermathSystem
9. DamageInstanceCoordinator
10. Cleave / Chain / Counter systems
11. EffectExecutor
12. RuleHookSystem
13. ActionSystem
14. BattleEngine
```
No hidden late-binding cycles or service locators are required.

Composition verdict: **PASS**.

---

## 17. Authority Pin / Evidence Gate Audit

- Canonical Gameplay Authority: `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe` (`PASS`).
- Zero-loss FIRST_AID rules are backed by promoted authority commit `0b9e172a`.
- Evasion, Barrier, Crit, Strategy Crit, and Damage Reduction Pierce remain under Evidence Gate; typed topology support is permitted without promoting unevidenced production bindings.

Authority Pin verdict: **PASS**.

---

## 18. Regression Contract Audit

Section 34 regression contract includes:
- Lifecycle ($N=1, N=2$, before/after action apply, refresh timing)
- Battle teardown (`clear_all_on_battle_end`, zero state leakage)
- Generation provenance (DTO propagation, old generation intent isolation)
- ASSAULT and COUNTER FIRST_AID eligibility
- DirectTroopLoss FIRST_AID exclusion
- Cleave / Share / Distribution ordering and aftermath
- Defeat cleanup exactly-once conformance spy (`S10-R2-H01`)
- Frozen-lane zero live formula read instrumentation (`S10-R2-H02`)

Regression Contract verdict: **PASS**.

---

## 19. Two-Implementer Test

| Scenario | Conforming Implementer 1 | Conforming Implementer 2 | Divergent? |
|---|---|---|:---:|
| 1. ASSAULT resolved hit triggers FIRST_AID? | YES | YES | NO |
| 2. Share direct troop loss triggers FIRST_AID? | NO | NO | NO |
| 3. Cleave + Share + FIRST_AID ordering? | Target → Share → Aftermath → Attacker recovery | Target → Share → Aftermath → Attacker recovery | NO |
| 4. Owner dies in mixed intent batch? | Owner state tail aborted; other units proceed | Owner state tail aborted; other units proceed | NO |
| **5. Target dies but intent owner survives?** | **Aborts all owner intents (per §4.2 line 259)** | **Only skips intents for dead target (per §4.3 line 287)** | **YES (DIVERGENT)** |
| 6. G1 intent executes after G2 refresh? | Uses G1 snapshot; JIT dynamic checks | Uses G1 snapshot; JIT dynamic checks | NO |
| 7. p=1 recovery RNG draw? | Consumes 1 draw via `chance(1.0)` | Consumes 1 draw via `chance(1.0)` | NO |
| 8. Battle ends with persistent states? | `clear_all_on_battle_end` cleanses all states | `clear_all_on_battle_end` cleanses all states | NO |
| 9. Source dies before DOT tick? | DOT tick executes using frozen snapshot | DOT tick executes using frozen snapshot | NO |
| 10. Second ActionStart in same round? | Suppressed by `ActionProgressTracker` | Suppressed by `ActionProgressTracker` | NO |

**Result**: Scenario 5 produces divergent observable behavior between two independent implementers due to the scope contradiction between §4.2 and §4.3.

Two-Implementer Test verdict: **FAIL**.

---

## 20. Production Wiring Test

Question: Can Draft V3 be wired into the current production codebase without the implementer making arbitrary architectural or gameplay decisions?
- Composition root wiring: Feasible without cycles.
- ExecutionRight and Aftermath integration: Implementer would be forced to resolve the `ABORT_OWNER_STATE_REMAINDER` scope conflict and how `RECUPERATION` handles Gate 2.

Production Wiring Test verdict: **FAIL (conditional on finding repairs)**.

---

## 21. New Findings

### BLOCKER

#### S10-R3-B01 — Conflation of Target Defeat and Owner Defeat in `ExecutionRightDecision.ABORT_OWNER_STATE_REMAINDER`
- **ID**: `S10-R3-B01`
- **Severity**: `BLOCKER`
- **Source location**: `stages/stage10/STAGE10.md` §4.2 line 257-260 vs §4.3 line 284-288.
- **Contract location**: `sgs_v2/battle_core/rule_hook_system.py`, `sgs_v2/battle_core/execution_right_system.py`.
- **Problem**:
  In §4.2, `ABORT_OWNER_STATE_REMAINDER` is defined as discarding all remaining intents belonging to the **state owner**.
  In §4.3, for Effect B where target Unit X was killed by Effect A, the design states that `ExecutionRightSystem` returns `ABORT_OWNER_STATE_REMAINDER`, which causes `RuleHookSystem` to skip remaining intents **targeting Unit X**.
  When State Owner $P_1$ applies an effect that kills Target $P_2$:
  - If `ABORT_OWNER_STATE_REMAINDER` discards all remaining intents of owner $P_1$, then valid subsequent intents of living owner $P_1$ targeting living unit $P_3$ are erroneously aborted.
  - If it only skips intents targeting $P_2$, then a true owner defeat fails to abort the owner's remaining state resolution.
- **Why it matters**: Directly causes Two-Implementer Test Scenario 5 to diverge in observable gameplay.
- **Required repair**:
  Formally restore the dual-decision model from `STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md` §4.3:
  1. `OWNER_DEFEATED` (or `ABORT_OWNER_STATE_REMAINDER`): State owner died. Abort remaining state-resolution intents for that defeated owner.
  2. `TARGET_DEFEATED` (or `REJECT_CURRENT(TARGET_DEFEATED)`): Target of the specific effect died. Reject only that intent; subsequent intents in the batch for other living targets proceed.
  Eliminate the conflation in §4.3 lines 284-288.
- **Gameplay research required**: `NO`.
- **Authority sync required**: `NO`.

---

### MAJOR

#### S10-R3-M01 — `RecoveryOpportunitySystem` Gate 2 Unconditionally Asserts `DamageAftermathFact`, Breaking `RECUPERATION`
- **ID**: `S10-R3-M01`
- **Severity**: `MAJOR`
- **Source location**: `stages/stage10/STAGE10.md` §22 line 1366-1370.
- **Contract location**: future `RecoveryOpportunitySystem.admit_opportunity()`.
- **Problem**:
  Section 22 lists the normalized admission sequence for `RecoveryOpportunitySystem`. Gate 2 states:
  ```text
  2. Hit Topology & Reaction Permission Gate:
     - Validate DamageAftermathFact.hit_topology == DamageHitTopology.RESOLVED_HIT.
     - Validate ReactionPermissionPolicy.can_trigger_recovery(source_type) == True.
  ```
  `RecoveryOpportunitySystem` is the sole recovery opportunity engine for both `FIRST_AID` (damage aftermath) and `RECUPERATION` (turn action-start). `RECUPERATION` has no `DamageAftermathFact` or damage `source_type`.
- **Why it matters**: A conforming implementation will crash or reject all `RECUPERATION` opportunities at Gate 2.
- **Required repair**:
  Explicitly specify in Gate 2:
  - For damage aftermath recovery (`FIRST_AID`): validate `DamageAftermathFact.hit_topology` and `ReactionPermissionPolicy.can_trigger_recovery(source_type)`.
  - For action-start recovery (`RECUPERATION`): Gate 2 is **`NOT_APPLICABLE`** (proceed directly from Gate 1 to Gate 3).
- **Gameplay research required**: `NO`.
- **Authority sync required**: `NO`.

---

#### S10-R3-M02 — `ExecutionRightSystem.evaluate_rule_intent` Typed Interface Contract Underdefined
- **ID**: `S10-R3-M02`
- **Severity**: `MAJOR`
- **Source location**: `stages/stage10/STAGE10.md` §4.1 line 217, §31 line 1724.
- **Contract location**: `sgs_v2/battle_core/execution_right_system.py`.
- **Problem**:
  Draft V3 designates `ExecutionRightSystem` as the sole decision owner evaluating `evaluate_rule_intent(intent, context)`. However, it does not specify the typed interface signature or how it extracts `(intent_owner, state_owner, target_id, source_ref, generation_id)` across heterogeneous intents (`DamageEffect`, `RecoverEffect`, `ApplyStateEffect`, `RecoveryOpportunity`).
- **Why it matters**: Implementation requires ad-hoc duck typing or reflection, risking duplicate checks between `RuleHookSystem` and `EffectExecutor`.
- **Required repair**:
  Define the concrete protocol/signature of `evaluate_rule_intent` and specify how intent properties are mapped into the decision inputs.
- **Gameplay research required**: `NO`.
- **Authority sync required**: `NO`.

---

### MINOR

#### S10-R3-N01 — Native `RandomSystem.chance` Draw Invariant Documentation
- **ID**: `S10-R3-N01`
- **Severity**: `MINOR`
- **Source location**: `stages/stage10/STAGE10.md` §18 / §22.
- **Contract location**: `sgs_v2/battle_core/random_system.py` line 39.
- **Problem**:
  Draft V3 mandates that $p=0$ and $p=1$ consume exactly one draw under simulator engineering policy, but leaves ambiguity as to whether `RandomSystem` requires modification or reopen.
- **Why it matters**: Auditors or implementers might suspect a Stage 2 random contract violation. In reality, `RandomSystem.chance` already evaluates `self.random() < probability` without shortcutting.
- **Required repair**: Explicitly state that production `RandomSystem.chance` natively satisfies the one-draw invariant for all $p \in [0.0, 1.0]$ and requires no code changes or compatibility reopen.
- **Gameplay research required**: `NO`.
- **Authority sync required**: `NO`.

---

### HARDENING

*(None new in Round 3; S10-R2-H01 and S10-R2-H02 remain accepted for build obligations.)*

---

## 22. Final Freeze Gate

| Freeze Gate Criterion | Status | Evaluation |
|---|:---:|---|
| BLOCKER Count = 0 | **FAIL** | 1 BLOCKER (`S10-R3-B01`) |
| MAJOR Count = 0 | **FAIL** | 2 MAJOR (`S10-R3-M01`, `S10-R3-M02`) |
| Gameplay Authority Sync | **PASS** | Canonical HEAD `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe` |
| Stage7 Compatibility Addendum | **FAIL** | Abort scope conflation contradicts addendum §4.3 |
| Stage8 Compatibility Addendum | **PASS** | FROZEN_APPLICATION replay lane fully valid |
| Stage9 Compatibility Addendum | **PASS** | Cleave ordering and ASSAULT permission formalized |
| Two-Implementer Determinism | **FAIL** | Scenario 5 produces divergent gameplay |
| Production Wiring Feasibility | **FAIL** | Ambiguities in Gate 2 and abort scopes block wiring |
| FROZEN_APPLICATION Status | **UNCHANGED** | Preserves Stage8 frozen contract |

---

## 23. Final Verdict

```text
================================================================================
FINAL VERDICT: FAIL / DESIGN REPAIR ROUND 3 REQUIRED
================================================================================

Design Freeze Authorized:           NO
Build Prompt Authorized:            NO
Production Implementation:          NOT AUTHORIZED
PR Merge Authorized:                NO

Next Step:
Execute Stage10 Design Repair Round 3 (R3-B) addressing S10-R3-B01, S10-R3-M01,
and S10-R3-M02 in STAGE10.md without modifying production code or tests.
```
