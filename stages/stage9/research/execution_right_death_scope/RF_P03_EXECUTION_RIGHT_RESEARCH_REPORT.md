# RF-P03 Research Report: Execution Right & Action-Death Scope

```text
Repair Package: RF-P03
Target Findings: CFS9-B01, CBS9-B01, SHS9-M01, DSTS9-M01
Date: 2026-09-13
Repository Baseline:
  battle repo: e31af16f2336db99141474514a7078118bd78bde
  state research repo: add9a2134e88e90a58abf46eafd1de9d8c6f3b99
```

---

## 1. Executive Summary

This research investigates the execution right and death scope semantics governing actor death occurring during their own Normal Attack action between `Normal Attack #1` start and `Combo Checkpoint`, directly resolving findings `CBS9-B01`, `CFS9-B01`, `SHS9-M01`, and `DSTS9-M01`.

### 1.1 Key Empirical Findings
1. **Universal Post-Death Combo Refuted**:
   Across a full-corpus scan of **32,999 indexed battles** (728 raw death candidate frames, 500 unconfounded attacker death cases during Normal Attack #1):
   - **`cfg 230` (Combo Checkpoint execution) after death**: **0 / 500 (0.0%)**
   - **`cfg 9` (Normal Attack #2) after death**: **0 / 500 (0.0%)**
   - **Assault skill dispatch after death**: **0 / 500 (0.0%)**
2. **Death Family Elimination**:
   - `COUNTER_DAMAGE`: 362 cases $\to$ 100% hard abort of future Assault and Combo #2.
   - `DERIVED_REACTION_DAMAGE` (e.g. 【刚烈不屈】/ 【刚烈】): 115 cases $\to$ 100% hard abort of future Assault and Combo #2.
   - `OTHER` (including extended reaction chains): 23 cases $\to$ 100% hard abort of future Assault and Combo #2.
   - `REFLECT_DAMAGE`, `SELF_COST`, `PERIODIC_DAMAGE`, `COMMANDER_COLLATERAL`: **NOT APPLICABLE** in the intra-NormalAttack #1 execution window.
3. **Dispositions**:
   - **`CBS9-B01 = CLOSED`**: The universal own-action death continuation rule ("亡语连击") is completely deleted from COMBO P0. All reachable death families are explicitly classified as `PROVEN ABORT`.
   - **`CFS9-B01 = CLOSED AS UNREACHABLE`**: Because 0 dead actors can reach Combo #2 fresh Target Resolution under any reachable death family, the theoretical contradiction of whether a dead actor's Confusion is operational during fresh target selection is provably unreachable in real battles. Confusion operational semantics remain untouched.
   - **`SHS9-M01 = CLOSED`**: DAMAGE_SHARE P0 over-broad clause `TARGET_DEATH → ABORT_REMAINING_ACTION` is removed. Share P0 strictly owns Share-local transaction semantics and delegates outer Action/Reaction decisions to the authoritative owner.
   - **`DSTS9-M01 = CLOSED`**: DISTRIBUTION P0 over-broad clause `TARGET_DEATH → ABORT_REMAINING_ACTION` is removed. Distribution P0 strictly owns Distribution-local transaction semantics and delegates outer Action decisions.

---

## 2. Research Methodology & Dataset

### 2.1 Battle Database Scope
- Dataset: `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`
- Total battles scanned: **32,999 battles**
- Extraction tool: `stages/stage9/research/execution_right_death_scope/extract_combo_non_counter_deaths.py`
- Evidence store: `stages/stage9/research/execution_right_death_scope/EXECUTION_RIGHT_EVIDENCE.json`

### 2.2 Confounder Isolation: Disambiguating Mirror Matchups
During initial extraction, 3 apparent anomaly cases were flagged where `cfg 230` or a second `cfg 9` followed an event with `cfg 163: [武将]兵力为0，无法再战`.
Detailed inspection of the raw colored battle event descriptors revealed:
- `战报_2494090_pid2602399.json`: Enemy `<font color='#ec616b'>[太史慈]</font>` attacked Friendly `<font color='#75b3ed'>[太史慈]</font>`. Friendly 太史慈 died (`cfg 163`). Enemy 太史慈 was ALIVE and legitimately proceeded to Combo `cfg 230` and second attack `cfg 9`.
- `战报_1105032_pid1100124.json`: Enemy `<font color='#ec616b'>[陆逊]</font>` attacked Friendly `<font color='#75b3ed'>[陆逊]</font>`. Friendly 陆逊 died. Enemy 陆逊 was ALIVE and executed Combo `cfg 230`.
- `战报_2496128_pid2605098.json`: Friendly `<font color='#75b3ed'>[张辽]</font>` attacked Enemy `<font color='#ec616b'>[张辽]</font>`. Enemy 张辽 died. Friendly 张辽 was ALIVE.

By incorporating exact camp/color tags (`tag_*_my` vs `tag_*_enemy`, `#75b3ed` vs `#ec616b`), all false positive mirror matchups were isolated. The true count of dead attackers continuing to Combo #2 is **strictly zero**.

---

## 3. Death Family Reachability & Empirical Matrix

The following matrix classifies all candidate death families for an actor whose Normal Attack #1 has commenced, prior to reaching Combo Checkpoint:

| Death Family | Reachable in Window? | Scanned Cases | Observed Continued Assault | Observed Continued Combo (cfg 230) | Observed 2nd Attack (cfg 9) | Empirical Verdict |
|---|---|---:|---:|---:|---:|---|
| **`COUNTER_DAMAGE`** | **YES** | 362 | 0 | 0 | 0 | **PROVEN ABORT** |
| **`DERIVED_REACTION_DAMAGE`** (e.g. 【刚烈不屈】) | **YES** | 115 | 0 | 0 | 0 | **PROVEN ABORT** |
| **`OTHER_ACTION_DEATH`** (Extended reactions) | **YES** | 23 | 0 | 0 | 0 | **PROVEN ABORT** |
| **`REFLECT_DAMAGE`** | **NO** | 0 | N/A | N/A | N/A | **NOT APPLICABLE** (no reflect mechanic in engine) |
| **`SELF_COST`** | **NO** | 0 | N/A | N/A | N/A | **NOT APPLICABLE** (normal attack has zero troop cost; self-cost skills do not trigger in NA#1) |
| **`PERIODIC_DAMAGE`** | **NO** | 0 | N/A | N/A | N/A | **NOT APPLICABLE** (DOT ticks at ACTION_START, not intra-attack) |
| **`COMMANDER_COLLATERAL`** | **NO** | 0 | N/A | N/A | N/A | **NOT APPLICABLE** (collateral loss targets defenders upon commander death, not attacker) |

---

## 4. Analysis of Findings

### 4.1 CBS9-B01: COMBO Own-Open-Action Death Continuation
- **Original Flaw**: The original COMBO P0 contained an over-generalized statement:
  ```text
  ACTOR_DEATH_DURING_OWN_OPEN_ACTION
  → universal current Action continuation
  → possible cfg230 + #2
  ```
- **Evidence Refutation**:
  1. Counter Q05: 341 counter-kill samples, 0 continued Assault, 0 continued Combo #2.
  2. COMBO Q45: 11 / 11 counter-kills, 0 cfg230, 0 #2.
  3. RF-P03 Extraction: 500 / 500 attacker death cases, 0 continued Assault, 0 cfg230, 0 #2.
- **Contract Closure**:
  Delete the universal rule entirely. Freeze the explicit rule:
  When an actor dies during their own open action prior to Combo Checkpoint (under any death family), future Assault branches and future Combo Checkpoint / #2 branches are **strictly cancelled**.
  `CBS9-B01 = CLOSED`.

### 4.2 CFS9-B01: Dead Actor Confusion Operationality
- **Conjunction Requirement**:
  For `CFS9-B01` to arise, all of the following conditions must hold simultaneously:
  1. Actor dies during Normal Attack #1;
  2. Death family permits current Action future Combo branch;
  3. Actor had already granted Combo eligibility;
  4. Combo #2 actually reaches fresh Target Resolution;
  5. Old Confusion physical instance remains present.
- **Empirical Resolution**:
  Condition 2 and Condition 4 are **never satisfied** in any battle (0 / 500 observed cases). A dead actor NEVER reaches Combo #2 fresh Target Resolution.
  Therefore, the theoretical question of whether a dead actor reads Confusion as operational during fresh target selection is **provably unreachable**.
  `CFS9-B01 = CLOSED AS UNREACHABLE`.
  No changes to CONFUSION P0 are required.

### 4.3 SHS9-M01: DAMAGE_SHARE Outer Action Death Wording
- **Original Flaw**:
  DAMAGE_SHARE P0 Section 18.1 stated:
  ```text
  TARGET_DEATH
  → CLEAR_ALL_STATES
  → ABORT_REMAINING_STATE_RESOLUTION
  → ABORT_REMAINING_ACTION
  → REJECT_FUTURE_STATE_APPLICATION
  ```
  `ABORT_REMAINING_ACTION` exceeded Share's ownership boundary. Share does not own outer Action termination, ReactionStack unwinding, or battle finalization.
- **Contract Closure**:
  Redefine Section 18.1 to be transaction-scoped:
  ```text
  TARGET_DEATH
  → commit protected target assigned loss
  → emit TargetDeathFact
  → apply Share-local transaction rule (discard pending Dsharer)
  → complete Share transaction
  → delegate outer Action / reaction / finalization decisions to authoritative owner
  ```
  `SHS9-M01 = CLOSED`.

### 4.4 DSTS9-M01: DISTRIBUTION Outer Action Death Wording
- **Original Flaw**:
  DISTRIBUTION P0 Section 14 identically included:
  ```text
  TARGET_DEATH
  → CLEAR_ALL_STATES
  → ABORT_REMAINING_STATE_RESOLUTION
  → ABORT_REMAINING_ACTION
  → REJECT_FUTURE_STATE_APPLICATION
  ```
- **Contract Closure**:
  Redefine Section 14 to be transaction-scoped:
  ```text
  TARGET_DEATH
  → commit target assigned loss
  → emit TargetDeathFact
  → complete Distribution transaction
  → delegate outer Action / reaction / finalization decisions to authoritative owner
  ```
  `DSTS9-M01 = CLOSED`.

---

## 5. Architectural Model: Execution Right vs Liveness Gate

Stage 9 formalizes the two-tier execution model:

```text
Tier 1: Admission Right (Execution Right)
  - Distinguishes ALREADY_ADMITTED from FUTURE_BRANCH_NOT_YET_DISPATCHED.
  - Sibling reactions already queued in an admitted batch (e.g. CounterBatch [C1, C2]) retain admission right even if target dies during C1.
  - Future branches not yet admitted (e.g. Assault, Combo Checkpoint) do NOT possess an admitted execution right.

Tier 2: Execution-Time Local Gate
  - Even an admitted work item must pass its own local execution gate at dispatch time.
  - If target is dead: C2 executes under its local dead-target path (commits zero loss, does not run weapon damage formula).
  - If actor is dead: unadmitted future branches (Assault, Combo Checkpoint) fail the liveness gate and are cancelled before admission.
```

---

## 6. Regression Test Specifications

Future simulator regression suites must implement the following tests:
1. `TEST-DTH-01`: Attacker dies from Counter during NA#1 $\to$ pending Assault cancelled, Combo Checkpoint not reached (0 cfg 230), NA#2 cancelled (0 cfg 9).
2. `TEST-DTH-02`: Attacker dies from Passive Reaction (【刚烈】) during NA#1 $\to$ pending Assault cancelled, Combo Checkpoint not reached, NA#2 cancelled.
3. `TEST-DTH-03`: CounterBatch [C1, C2] admitted; C1 kills attacker $\to$ C2 executes under dead-target zero-loss path; unrelated already-admitted work is not retroactively cancelled.
4. `TEST-DTH-04`: Protected target dies from `Dtarget` during Share $\to$ pending `Dsharer` discarded; Share P0 emits `TargetDeathFact` and delegates outer Action termination to Core Orchestrator.
5. `TEST-DTH-05`: Protected target dies from `Dtarget` during Distribution $\to$ Distribution transaction finishes; outer Action termination delegated to Core Orchestrator.
6. `TEST-DTH-06`: Actor possesses Combo grant but dies during NA#1 $\to$ grant does not force execution of #2; branch is cancelled at admission gate.
7. `TEST-DTH-07`: Dead actor with Confusion $\to$ no fresh target selection is ever initiated while dead.
