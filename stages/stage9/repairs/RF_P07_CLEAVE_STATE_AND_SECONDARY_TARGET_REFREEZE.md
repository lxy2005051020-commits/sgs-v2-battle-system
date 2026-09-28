# RF-P07 Repair Record

## CLEAVE_STATE_AND_SECONDARY_TARGET_REFREEZE

```text
Package: RF-P07
Level: A
Priority: P0
Execution Type: EMPIRICAL EXTRACTION, CONTRACT SPECIFICATION AND RE-FREEZE
Need New Extractor: YES (executed and archived: extract_cleave_state_lifecycle.py, extract_cleave_secondary_order.py)
Repair Date: 2026-09-13
Final Verdict: RF-P07 CLOSED
Affected Findings:
  CLVS9-B02 = CLOSED (690084 State Container, Reapply REFRESH, Multi-source COEXIST, Skill-slot Order)
  CLVS9-B03 = CLOSED (Secondary Candidate Pool, Guard-redirect Inclusion, GLOBAL_SLOT_ASCENDING, EFFECT_MAJOR_ORDER, JIT Revalidation)
Preserved Open Findings:
  CLVS9-B04 = OPEN → RF-P04 (Death & Battle Finalization Barrier)
```

---

## 1. Repository Baseline

Repair start exact `main` refs were re-read and verified immediately before modification:

### Battle repository

```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

repair-before exact main HEAD:
154b9b9584bf2661c529ffa7cdfb94fa3c726e77
repair(stage9): re-freeze cleave damage layer semantics
```

### State-mechanics research repository

```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

repair-before exact main HEAD:
38259cd938e734b68eb9d86679bd23fe51065930
docs(combo): narrow action-death execution semantics
```

Both repositories confirmed `HEAD == origin/main`.

Inherited closures from prior packages:
- `RF-P01`: `CHAIN = FLOOR`, `SHARE = ROUND_HALF_UP`, `DISTRIBUTION = ROUND_HALF_UP`.
- `RF-P02`: Core owns NormalAttack master lifecycle.
- `RF-P03`: `CBS9-B01 = CLOSED`, `CFS9-B01 = CLOSED AS UNREACHABLE`, `SHS9-M01 = CLOSED`, `DSTS9-M01 = CLOSED`.
- `RF-P06`: `CLVS9-B01 = CLOSED` (`MainAttackFinalDamage ≡ ActualTargetTroopLoss`, `floor`), `CLVS9-M01 = CLOSED` (`PER-SECONDARY DAMAGE EVENT`, `Dtarget` recovery basis).

---

## 2. Affected Findings & Dispositions

```text
CLVS9-B02: 690084 state lifecycle, container model, multi-source coexistence, execution ordering, ratio binding
CLVS9-B03: secondary target candidate pool, count, deterministic ordering, Guard redirection, JIT liveness revalidation
```

Disposition after repair:

```text
CLVS9-B02 = CLOSED
CLVS9-B03 = CLOSED
```

Explicitly preserved as OPEN for downstream package RF-P04:

```text
CLVS9-B04 = OPEN → RF-P04 (Battle Finalization Barrier)
```

---

## 3. Existing Frozen Kernel (from RF-P06)

The core damage derivation established in RF-P06 remains intact:

$$\mathbf{MainAttackFinalDamage} \equiv \mathbf{ActualTargetTroopLoss} = \min(D_{target}, \text{mainTarget.currentTroops})$$
$$\mathbf{CleaveDerivedCalculatedDamage} = \lfloor \mathbf{ActualTargetTroopLoss} \times \mathbf{CleaveRatio} \rfloor$$

Invariants:
- Derived damage, not NormalAttack;
- No second base formula, no secondary target modifier re-entry;
- Evasion before Resistance (consumes 1 charge);
- Secondary Share / Distribution allowed;
- Secondary FirstAid / Chain allowed;
- Counter and recursive Cleave strictly blocked;
- DamageType inherited.

---

## 4. Research Corpus

Two high-performance empirical extractors were executed across the 32,999+ battle corpus:
1. **Track A (State Lifecycle Extractor)**:
   - `stages/stage9/research/cleave_state_and_targets/extract_cleave_state_lifecycle.py`
   - Store: `CLEAVE_STATE_EVIDENCE.json`
   - Scanned: **32,999 battles**
   - Results: **2,256 Apply**, **203 Refresh**, **1,283 Expire**, **121 Multi-source Cleave attacks**.
2. **Track B (Secondary Target Extractor)**:
   - `stages/stage9/research/cleave_state_and_targets/extract_cleave_secondary_order.py`
   - Store: `CLEAVE_TARGET_ORDER_EVIDENCE.json`
   - Scanned: **32,999 battles**
   - Results: **2,596 verified attack sequences with exact lineup positions**, **15 Guard redirected Cleave cases**.

---

## 5. Cleave State Model (`CLVS9-B02`)

### 5.1 Container Model: `SOURCE_BOUND_EFFECT_LIST`
- When an actor has multiple Cleave sources (e.g. Inherent skill 【槊血纵横】 + learned skill 【瞋目横矛】), they do NOT merge into a single ratio (`MERGED_RATIO_STATE` refuted).
- Each Cleave source attaches as an independent `CleaveEffectInstance` bound to its source skill and slot.
- Across 121 multi-source battles, both skills triggered independent, successive Cleave events with their own specific ratios.

### 5.2 Same-source Reapply: `REFRESH`
- When the same skill casts Cleave again while already active, the game engine triggers:
  `[武将]身上的「群攻」效果已刷新` (203 verified occurrences).
- The remaining duration is reset to the skill's max duration.
- It does NOT create duplicate stacks, does NOT increase ratio, and does NOT reject execution (`cfg: 23` count = 0).

### 5.3 Multi-source Model: `COEXIST`
- Different sources coexist without mutual exclusion or replacement.
- When multiple Cleave sources are present on the same actor, both remain active and trigger sequentially.

### 5.4 Execution Comparator: `SKILL_SLOT_ORDER`
- Multi-source execution strictly follows the actor's skill slot ordering:
  $$\mathbf{Skill\ Slot\ Order:\ Slot\ 0\ (Inherent)\ \to\ Slot\ 1\ (Second)\ \to\ Slot\ 2\ (Third)}$$
- Empirical proof: Across all 121 multi-source attacks, 【槊血纵横】 (Slot 0) executed first, followed by 【瞋目横矛】 (Slot 1) second:
  $$\mathbf{121\ /\ 121\ (100.0\%)\ Slot\ 0 \to Slot\ 1/2}$$
  Zero slot-order contradictions.

### 5.5 Ratio Binding
- `PERMANENT_SOURCE_BOUND` (inherent skills): Ratio is resolved from skill configuration/level.
- `TEMPORARY_TIMED` (active/assault skills): Ratio is resolved at Apply-time from the source skill instance.
- No dynamic attribute scaling exists for existing Cleave skills.

### 5.6 Duration / Expiration
- Inherent passive/command skills have no duration and persist for the entire battle.
- Active skills (e.g. 瞋目横矛) possess a 2-round duration, ticked down during the holder's `ACTION_START` maintenance phase. Upon expiration, `「群攻」效果已消失` is emitted (1,283 verified instances).

### 5.7 Suppression / Source Death
- If the actor is under Disarm (缴械) or Stun (震慑) and cannot launch a normal attack, the parent normal attack is prevented, so Cleave cannot trigger.
- If the normal attack successfully lands and deals damage, the derived Cleave phase proceeds.

---

## 6. Secondary Target Planning & Ordering (`CLVS9-B03`)

### 6.1 Secondary Candidate Pool
- Centered on the **post-Guard `actualTarget`**.
- Candidate pool: All **alive teammates** of `actualTarget` on the same battle side.
- Strict Exclusions:
  - The attacker is strictly excluded (100% exclusion).
  - The `actualTarget` is strictly excluded (100% exclusion, 2,596 / 2,596).

### 6.2 Guard Redirection Case (Ironclad Proof)
- Scenario: Attacker targets B (originalTarget), C guards B $\implies$ `actualTarget = C`.
- Question: Does B (originalTarget) have immunity from the subsequent Cleave?
- **Empirical Verdict**: **NO IMMUNITY**. In 15 / 15 (100.0%) verified Guard redirect cases (e.g. `战报_1068287_pid1063304.json` Event 301-307), original target B was an alive teammate of C, and B was **100% selected as a secondary target and hit by Cleave**.

### 6.3 Target Count
- Dynamically determined by the number of alive teammates:
  - 3-hero full team: **2 secondary targets**.
  - 2-hero surviving team (1 teammate dead): **1 secondary target**.
  - 1-hero sole survivor (0 teammates alive): **0 secondary targets** (Cleave derived phase terminates cleanly without zero-loss events).

### 6.4 Deterministic Secondary Ordering: `GLOBAL_SLOT_ASCENDING`
Across 2,596 verified battle sequences, secondary target ordering strictly follows the **global ascending position order** of the target team (`pos 1` Commander $\to$ `pos 2` Deputy 1 $\to$ `pos 3` Deputy 2), filtered by alive status and excluding `actualTarget`:

| actualTarget Position | Secondary Target Sequence Observed | Frequency | Verification Ratio | Ordering Rule |
|---|---|---:|---:|---|
| **Pos 1 (Commander)** | **`(pos 2, pos 3)`** | 431 | 100.0% (both alive) | `GLOBAL_SLOT_ASCENDING` |
| **Pos 2 (Deputy 1)** | **`(pos 1, pos 3)`** | 469 | 100.0% (both alive) | `GLOBAL_SLOT_ASCENDING` |
| **Pos 3 (Deputy 2)** | **`(pos 1, pos 2)`** | 534 | 100.0% (both alive) | `GLOBAL_SLOT_ASCENDING` |

### 6.5 Multi-source Queue Composition: `EFFECT_MAJOR_ORDER`
When multiple Cleave sources trigger from a single normal attack:
$$\mathbf{EFFECT\_MAJOR\_ORDER:\ CleaveEffect_A[\text{sec}_1, \text{sec}_2] \to CleaveEffect_B[\text{sec}_1, \text{sec}_2]}$$
Cleave Effect A completely finishes all its secondary targets and inline reactions before Cleave Effect B begins.

### 6.6 JIT Liveness Revalidation
- Before each secondary step in the sequence, the runtime re-validates `secondary.currentTroops > 0`.
- If a planned secondary target was killed by earlier downstream damage (e.g., secondary #1's inline Chain or Share killed secondary #2), the step is **skipped (SKIP)**.
- Dead units receive no Cleave event.
- Visited slots are never revisited (NO REVISIT).

---

## 7. State Repository Contract Decision

Following Section 47-49 of the closure specification:
- Created authoritative P0 contract: [`states/functional/cleave/MECHANISM_CONTRACT.md`](file:///C:/Users/34187/Desktop/antigravity工作文件/sgs-state-mechanics-research/states/functional/cleave/MECHANISM_CONTRACT.md) in `sgs-state-mechanics-research`.
- Canonical Identifier: `CLEAVE` (State ID: `690084`).
- Updated [`states/functional/minimum_usable/690084_SPLASH.md`](file:///C:/Users/34187/Desktop/antigravity工作文件/sgs-state-mechanics-research/states/functional/minimum_usable/690084_SPLASH.md) to point to the authoritative P0 contract.
- Contract Status: `CORE + STATE + TARGET CONTRACT FROZEN; DEATH/FINALIZATION NARROW REOPEN REMAINS (CLVS9-B04)`.

---

## 8. Cross-Mechanism Verification

- **CLEAVE × GUARD**: Guard anchors actualTarget; originalTarget retains standard secondary candidate eligibility without immunity. Verified.
- **CLEAVE × MULTI-SOURCE**: Multi-source effects execute in `EFFECT_MAJOR_ORDER` sorted by `SKILL_SLOT_ORDER`. Verified.
- **CLEAVE × CHAIN**: Secondary #1 triggers inline Chain; secondary #2 undergoes JIT liveness revalidation. Verified.
- **CLEAVE × COUNTER**: Secondary events lack NormalAttack identity $\implies$ Counter strictly blocked. Verified.

---

## 9. Remaining Cleave Findings Ledger

```text
CLVS9-B01 = CLOSED (RF-P06)
CLVS9-M01 = CLOSED (RF-P06)
CLVS9-B02 = CLOSED (RF-P07 — Container, Reapply, Multi-source, Ordering)
CLVS9-B03 = CLOSED (RF-P07 — Pool, Count, GLOBAL_SLOT_ASCENDING, JIT)
CLVS9-B04 = OPEN → RF-P04 (Death & Battle Finalization Barrier)
CLVS9-D01 = OPEN → RF-C02 (Barrier → RESISTANCE normalization)
CLVS9-D02 = OPEN → RF-C02 (Evidence Matrix drift)
CLVS9-D03 = OPEN → RF-C02 (Minimum usable superseded nav)
CLVS9-D04 = OPEN → RF-C02 (State README drift)
CLVS9-H01 = OPEN → RF-C01 (Typed DerivedDamage runtime tests)
```

---

## 10. Regression Matrix

```yaml
regressions:
  - id: CLEAVE_STATE_01_MULTI_SOURCE_SLOT_ORDER
    actor: 马超
    skills:
      - slot: 0
        name: 槊血纵横
        ratio: 0.54
      - slot: 1
        name: 瞋目横矛
        ratio: 0.70
    expected_execution_order: ["槊血纵横", "瞋目横矛"]
    expected_queue_composition: "EFFECT_MAJOR_ORDER"

  - id: CLEAVE_STATE_02_SAME_SOURCE_REFRESH
    actor: 马超
    existing_state:
      skill: 瞋目横矛
      remaining_duration: 1
    action: "cast 瞋目横矛"
    expected_result: "REFRESH"
    expected_remaining_duration: 2
    expected_log: "[马超]身上的「群攻」效果已刷新"

  - id: CLEAVE_TARGET_01_ACTUAL_TARGET_POS_1
    target_team:
      pos1: "刘备 (alive)"
      pos2: "张飞 (alive)"
      pos3: "主公 (alive)"
    actual_target: "刘备 (pos 1)"
    expected_secondaries_order: ["张飞 (pos 2)", "主公 (pos 3)"]

  - id: CLEAVE_TARGET_02_ACTUAL_TARGET_POS_2
    target_team:
      pos1: "周瑜 (alive)"
      pos2: "主公 (alive)"
      pos3: "程普 (alive)"
    actual_target: "主公 (pos 2)"
    expected_secondaries_order: ["周瑜 (pos 1)", "程普 (pos 3)"]

  - id: CLEAVE_TARGET_03_ACTUAL_TARGET_POS_3
    target_team:
      pos1: "周瑜 (alive)"
      pos2: "主公 (alive)"
      pos3: "程普 (alive)"
    actual_target: "程普 (pos 3)"
    expected_secondaries_order: ["周瑜 (pos 1)", "主公 (pos 2)"]

  - id: CLEAVE_TARGET_04_GUARD_ORIGINAL_TARGET_ELIGIBILITY
    attacker: "马超"
    original_target: "主公 (pos 2)"
    guarder: "程普 (pos 3)"
    actual_target: "程普 (pos 3)"
    expected_secondaries_hit: ["周瑜 (pos 1)", "主公 (pos 2)"]
    guard_original_target_hit: true

  - id: CLEAVE_TARGET_05_DEAD_TEAMMATE_SKIPPED
    target_team:
      pos1: "许褚 (alive)"
      pos2: "文聘 (alive)"
      pos3: "董袭 (dead)"
    actual_target: "许褚 (pos 1)"
    expected_secondaries_order: ["文聘 (pos 2)"]
    dead_teammates_zero_loss_log: false
```

---

## 11. Changed Files

### Battle repository (`sgs-v2-battle-system`)
- `stages/stage9/research/cleave_state_and_targets/extract_cleave_state_lifecycle.py` (NEW)
- `stages/stage9/research/cleave_state_and_targets/extract_cleave_secondary_order.py` (NEW)
- `stages/stage9/research/cleave_state_and_targets/CLEAVE_STATE_EVIDENCE.json` (NEW)
- `stages/stage9/research/cleave_state_and_targets/CLEAVE_TARGET_ORDER_EVIDENCE.json` (NEW)
- `stages/stage9/research/cleave_state_and_targets/RF_P07_CLEAVE_STATE_AND_TARGET_RESEARCH_REPORT.md` (NEW)
- `stages/stage9/research/core_arbitration_v2/STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` (MODIFIED)
- `stages/stage9/repairs/RF_P07_CLEAVE_STATE_AND_SECONDARY_TARGET_REFREEZE.md` (NEW)

### State research repository (`sgs-state-mechanics-research`)
- `states/functional/cleave/MECHANISM_CONTRACT.md` (NEW)
- `states/functional/minimum_usable/690084_SPLASH.md` (MODIFIED)

---

## 12. Commits & Final Verdict

- **Battle Research Commit**: `research(stage9): resolve cleave state and target ordering`
- **State Repo Commit**: `docs(cleave): freeze state and secondary target contract`
- **Battle Repair Commit**: `repair(stage9): re-freeze cleave state and target semantics`
- **Final Verdict**: **`RF-P07 CLOSED`**
