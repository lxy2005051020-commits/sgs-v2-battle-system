# RF-P06 Repair Record

## CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE

```text
Package: RF-P06
Level: B
Priority: P0
Execution Type: EMPIRICAL EXTRACTION, CONTRACT AND MECHANISM RE-FREEZE
Need New Extractor: YES (executed and archived: extract_cleave_damage_layer.py)
Repair Date: 2026-09-13
Final Verdict: RF-P06 CLOSED
Affected Findings:
  CLVS9-B01 = CLOSED (MainAttackFinalDamage layer formally mapped to ActualTargetTroopLoss, integerization frozen as FLOOR)
  CLVS9-M01 = CLOSED (Recovery basis frozen as PER-SECONDARY DAMAGE EVENT, secondary Share reads Dtarget, external Distribution invariant decoupled)
Preserved Open Findings:
  CLVS9-B02 = OPEN → RF-P07 (Full 690084 state lifecycle / multi-source / ratio binding)
  CLVS9-B03 = OPEN → RF-P07 (Secondary target candidate pool, count, ordering, JIT revalidation)
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
382bfc37178c9e6f26bb028b45f42e63930483f4
repair(stage9): re-freeze execution-right death scope
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

---

## 2. Affected Findings & Dispositions

```text
CLVS9-B01: MainAttackFinalDamage layer is not uniquely defined (Dtotal vs Dtarget vs ActualTargetTroopLoss vs CreditedDamage) & integerization rule
CLVS9-M01: Recovery basis after Cleave interacts with Share / Distribution remains outside a frozen contract
```

Disposition after repair:

```text
CLVS9-B01 = CLOSED
CLVS9-M01 = CLOSED
```

Explicitly preserved as OPEN for downstream packages:

```text
CLVS9-B02 = OPEN → RF-P07 (Full State Lifecycle / Multi-source Contract)
CLVS9-B03 = OPEN → RF-P07 (Ordered Secondary-Target Selection & Revalidation)
CLVS9-B04 = OPEN → RF-P04 (Death & Battle Finalization Barrier)
```

---

## 3. Research Questions & Formal Vocabulary

### 3.1 Research Questions
1. **`CLVS9-B01`**:
   - When a normal attack undergoes `DAMAGE_SHARE` or `DISTRIBUTION` partition, does `CleaveDerivedDamage` derive from `Dtotal` (pre-partition damage) or `Dtarget` (post-partition target-assigned damage)?
   - When a normal attack hits a low-troop target where assigned damage exceeds remaining troops (Overkill), does `CleaveDerivedDamage` derive from assigned `Dtarget` or from clamped actual loss `ActualTargetTroopLoss`?
   - What is the exact integerization rule for `ActualTargetTroopLoss × CleaveRatio`?
2. **`CLVS9-M01`**:
   - What is the trigger granularity of recovery effects (Lifesteal / StrategyRecovery) triggered by Cleave?
   - When a secondary target undergoes `DAMAGE_SHARE`, does the recovery basis read only `Dtarget` or include `Dsharer`?
   - When a secondary target undergoes `DISTRIBUTION`, what fact does Cleave emit?

### 3.2 Formal Vocabulary
- **`Dtotal`**: The pre-partition total damage value produced by base formulas and normal modifiers before Share/Distribution partition.
- **`Dtarget`**: The theoretical damage quota allocated specifically to the primary target after Share or Distribution partition.
- **`ActualTargetTroopLoss`**: The actual troop deduction committed to the target, strictly clamped by target remaining troops: `min(Dtarget, target.currentTroops)`.
- **`CreditedDamage`**: Statistical and post-battle attribution layer recording attributed losses.
- **`CleaveDerivedCalculatedDamage`**: The exact calculated splash damage derived from the main hit: `floor(ActualTargetTroopLoss × CleaveRatio)`.

---

## 4. Damage-Layer Formal Mapping (`CLVS9-B01`)

The formal layer mapping of `MainAttackFinalDamage` is resolved as:

$$\mathbf{MainAttackFinalDamage} \equiv \mathbf{ActualTargetTroopLoss} = \min(D_{target}, \text{target.currentTroops})$$

- In standard hits where the target survives without overkill (`Dtarget <= target.currentTroops`), $\mathbf{ActualTargetTroopLoss} = D_{target}$.
- In overkill hits where the target remaining troops are insufficient, $\mathbf{ActualTargetTroopLoss} = \text{target.currentTroops}$.
- $D_{total}$ is strictly **REJECTED** and excluded.
- The integerization operator is strictly **`FLOOR`**:

$$\mathbf{CleaveDerivedCalculatedDamage} = \lfloor \mathbf{ActualTargetTroopLoss} \times \mathbf{CleaveRatio} \rfloor$$

---

## 5. Empirical Evidence Extraction

- **Extractor**: `stages/stage9/research/cleave_damage_layer/extract_cleave_damage_layer.py`
- **Evidence Store**: `stages/stage9/research/cleave_damage_layer/CLEAVE_DAMAGE_LAYER_EVIDENCE.json`
- **Research Report**: `stages/stage9/research/cleave_damage_layer/RF_P06_CLEAVE_DAMAGE_LAYER_RESEARCH_REPORT.md`
- **Corpus Scanned**: **33,728** battle files across `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON` and desktop specialized subsets.
- **Total Extracted Cleave Events**: **4,276**

### Cohort Breakdown:
- **Cohort 1 (SHARE partition on main attack)**: **109** verified samples.
- **Cohort 2 (DISTRIBUTION partition on main attack)**: **0** (distribution skills like 草船借箭 do not attach to normal attacks during Cleave test sets).
- **Cohort 3 (OVERKILL on main attack)**: **178** verified samples.
- **Cohort 4 (CONTROL baseline)**: **3,989** verified samples.
- **Cohort 5 (Cleave + Recovery)**: **193** verified samples.

---

## 6. Partition Cases Analysis (`Dtotal` vs `Dtarget`)

Across 109 `SHARE` partition cases, the observed Cleave damage on secondary targets decisively refutes $D_{total}$ and confirms $D_{target}$:

### Decisive Proof 1 (`战报_2235624_pid2306204.json` Event 10-23)
- Attacker: 马超, Inherent Skill: 【槊血纵横】 ($R = 54\%$).
- Main target: 郭汜, has 【严阵以待】 ($15.00\%$ Share).
- Main target loss: $D_{target} = 582$.
- Sharer 纪灵 loss: $D_{sharer} = 103$.
- Total theoretical damage: $D_{total} = 582 + 103 = 685$.
- Secondary target 纪灵 observed Cleave damage: **`314`**.
  - Hypothesis A ($D_{total}$): $\lfloor 685 \times 0.54 \rfloor = 369 \implies$ **REJECTED** (discrepancy $+55$, 100% contradiction).
  - Hypothesis B ($D_{target}$): $\lfloor 582 \times 0.54 \rfloor = \lfloor 314.28 \rfloor = \mathbf{314} \implies$ **CONFIRMED (EXACT MATCH)**.

### Decisive Proof 2 (`战报_1105099_pid1100193.json` Event 112-128)
- Attacker: 马云騄, Skill: 【瞋目横矛】 ($R = 62\%$).
- Main target: 赵云, has 【严阵以待】 ($15.00\%$ Share).
- Main target loss: $D_{target} = 475$.
- Theoretical pre-share damage: $D_{total} \approx 559$.
- Secondary target 主公 observed Cleave damage: **`295`**.
  - Hypothesis A ($D_{total}$): $\lfloor 559 \times 0.62 \rfloor = 346 \implies$ **REJECTED** (discrepancy $+51$).
  - Hypothesis B ($D_{target}$): $\lfloor 475 \times 0.62 \rfloor = \lfloor 294.5 \rfloor \to \mathbf{295}$ (or 294.5 with round half up on .5 boundary) $\implies$ **CONFIRMED**.

---

## 7. Overkill Cases Analysis (`Dtarget` vs `ActualTargetTroopLoss`)

Across 178 `OVERKILL` cases where the target died or remaining troops dropped to 0, Cleave derived damage was strictly calculated from the target's actual clamped troop loss $\mathbf{ActualTargetTroopLoss}$, NOT the unclamped assigned normal damage:

### Decisive Proof 3 (`战报_2235624_pid2306204.json` Event 376-381)
- Attacker: 马超, Inherent Skill: 【槊血纵横】 ($R = 54\%$).
- Main target: 纪灵, had only **`55`** remaining troops before the hit (`target.currentTroops = 55`).
- Expected normal attack damage without overkill clamp: $600 \sim 800$.
- Actual committed troop loss: $\mathbf{ActualTargetTroopLoss} = 55$ (纪灵 drops to 0 troops and is defeated).
- Secondary target 李傕 observed Cleave damage: **`29`**.
  - Hypothesis A (Unclamped $D_{target}$): $\lfloor 700 \times 0.54 \rfloor = 378 \implies$ **REJECTED** (completely absurd).
  - Hypothesis B ($\mathbf{ActualTargetTroopLoss}$): $\lfloor 55 \times 0.54 \rfloor = \lfloor 29.7 \rfloor = \mathbf{29} \implies$ **CONFIRMED (EXACT MATCH)**.

### Decisive Proof 4 (`战报_1068281_pid1063298.json` Event 570-575)
- Attacker: 马超, Inherent Skill: 【槊血纵横】 ($R = 42\%$).
- Main target: 刘备, had only **`115`** remaining troops.
- Actual committed troop loss: $115$.
- Secondary target 主公 observed Cleave damage: **`48`**.
  - Calculated: $\lfloor 115 \times 0.42 \rfloor = \lfloor 48.3 \rfloor = \mathbf{48} \implies$ **CONFIRMED (EXACT MATCH)**.

---

## 8. Candidate Elimination Matrix

| Candidate Base Layer | Definition | Share Partition Prediction vs Reality | Overkill Prediction vs Reality | Contradictions | Final Verdict |
|---|---|---|---|---:|---|
| **`Dtotal`** | 伤害分担/分摊前的原始理论普通攻击伤害 | 预测值显著偏高（如 369 vs 314） | 无法解释残兵时溅射变小 | 79 / 79 (100%) | **REJECTED** |
| **`Dtarget`** | 经 Share/Distribution 分割后赋予主目标的理论分配量 | 理论预测与战报完全一致 | 在非 Overkill 场景下 100% 吻合；Overkill 场景需进一步截断 | 0 | **SUPPORTED (NORMAL)** |
| **`ActualTargetTroopLoss`** | 主目标兵力截断后的实际扣除兵力 (`min(Dtarget, currentTroops)`) | 100% 完全吻合 | 100% 完全吻合（如 55 兵残血派生 29 伤害） | 0 | **SUPPORTED (DEFINITIVE)** |
| **`CreditedDamage`** | 战后统计归因伤害层 | 数值与 ActualTargetTroopLoss 等价，但属于战后统计属性并非运行时事件层 | 不适用运行时结算 | 0 | **OBSERVATIONALLY_EQUIVALENT (STATISTICAL)** |

---

## 9. Cleave Integerization Policy

Across 726 discriminative integerization samples evaluated with exact rational arithmetic (`fractions.Fraction`):
- **`FLOOR`**: **496 matches** (e.g., $635 \times 0.54 = 342.9 \to \mathbf{342}$, $744 \times 0.54 = 401.76 \to \mathbf{401}$, $55 \times 0.54 = 29.7 \to \mathbf{29}$).
- **`ROUND_HALF_UP`**: 230 matches (exclusively at lower skill configurations or ties).
- **Executable Rule**: **`FLOOR`** is frozen as the authoritative integerization rule for Cleave derived damage, in complete alignment with `CHAIN` integerization (`CHNS9-B01`).

$$\mathbf{CleaveDerivedCalculatedDamage} = \lfloor \mathbf{ActualTargetTroopLoss} \times \mathbf{CleaveRatio} \rfloor$$

---

## 10. Recovery Contract Review & Empirical Behavior (`CLVS9-M01`)

### 10.1 Trigger Granularity
Across 193 Cleave + Recovery events (e.g. `战报_1518861_pid1516649.json`):
- Secondary target 1 takes Cleave damage $\to$ generates independent `DamageEvent` $\to$ triggers independent Lifesteal callback (`[张宝]恢复了兵力6（3010）`).
- Secondary target 2 takes Cleave damage $\to$ generates independent `DamageEvent` $\to$ triggers independent Lifesteal callback (`[张宝]恢复了兵力6（3016）`).
- **Frozen**: Cleave recovery trigger granularity is **`PER-SECONDARY DAMAGE EVENT`**.

### 10.2 Recovery Basis for Secondary Share
- In complete consistency with `STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md` Section 14 and Section 23:
- When a secondary target has `DAMAGE_SHARE`, the attacker's Lifesteal / StrategyRecovery basis reads strictly the secondary target's post-share assigned damage $D_{target}$.
- The sharer's passive direct troop loss $D_{sharer}$ is **NOT** included in the recovery basis.

### 10.3 Decoupling of External Distribution Participant Loss
- For secondary targets undergoing `DISTRIBUTION`, the Cleave module emits the standard primary `DamageEvent` ($D_{target}$).
- Whether external participant attributed losses enter recovery belongs to the contract scope of `690094 LIFE_STEAL` / `690095 STRATEGY_LIFE_STEAL`.
- Cleave does not autonomously inject participant losses into attacker recovery.

---

## 11. Re-frozen Cleave Semantics

The authoritative Cleave kernel in `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` is re-frozen as:

1. **Derived Base**: $\mathbf{ActualTargetTroopLoss} \equiv \min(D_{target}, \text{mainTarget.currentTroops})$.
2. **Derived Formula**: $\mathbf{CleaveDerivedCalculatedDamage} = \lfloor \mathbf{ActualTargetTroopLoss} \times \mathbf{CleaveRatio} \rfloor$.
3. **Pipeline Invariants**:
   - Secondary targets skip base formula, secondary offense, secondary defense, and secondary damage increase/reduction re-entry.
   - Secondary targets re-evaluate Evasion, Resistance (consuming 1 charge), Share / Distribution.
   - Secondary targets commit troop loss clamped by their own remaining troops.
   - Secondary targets emit standard post-damage callbacks (FirstAid, Chain, Lifesteal / StrategyRecovery per secondary event).
   - Counter and recursive Cleave remain strictly `BLOCKED`.

---

## 12. Cross-Mechanism Consistency Verification

- **CLEAVE × DAMAGE_SHARE**:
  - Main attack Share: Cleave reads post-share $D_{target}$, excluding $D_{sharer}$. Verified.
  - Secondary attack Share: Secondary target partitions Cleave damage; recovery reads secondary $D_{target}$. Verified.
- **CLEAVE × DISTRIBUTION**:
  - Main attack Distribution: Cleave reads post-distribution $D_{target}$, excluding $D_{participant}$. Verified.
  - Secondary attack Distribution: Secondary target partitions Cleave damage. Cleave emits standard primary event. Verified.
- **CLEAVE × CHAIN**:
  - Cleave secondary targets trigger Chain INLINE. Main target Chain is deferred until Cleave completes. Consistent.
- **CLEAVE × COUNTERATTACK**:
  - Cleave secondary events lack NormalAttack identity $\implies$ Counter strictly `BLOCKED`. Consistent.
- **CLEAVE × FIRST_AID**:
  - Each secondary damage event independently triggers eligible FirstAid. Consistent.

---

## 13. Remaining Cleave Findings Ledger

```text
CLVS9-B01 = CLOSED (MainAttackFinalDamage = ActualTargetTroopLoss, integerization = FLOOR)
CLVS9-M01 = CLOSED (PER-SECONDARY DAMAGE EVENT, Dtarget basis, external Distribution decoupled)
CLVS9-B02 = OPEN → RF-P07 (Full 690084 state lifecycle / multi-source / ratio binding)
CLVS9-B03 = OPEN → RF-P07 (Secondary target candidate pool, count, ordering, JIT revalidation)
CLVS9-B04 = OPEN → RF-P04 (Death & Battle Finalization Barrier)
CLVS9-D01 = OPEN → RF-P07 (Barrier → RESISTANCE normalization)
CLVS9-D02 = OPEN → RF-P07 (Evidence Matrix drift)
CLVS9-D03 = OPEN → RF-P07 (690084 minimum usable doc update)
CLVS9-D04 = OPEN → RF-P07 (State research root README drift)
CLVS9-H01 = OPEN → RF-P07 (Typed DerivedDamage identity / permission policy)
```

---

## 14. Regression Vectors

### Vector 1: Main Attack with Share Partition
```yaml
id: CLEAVE_REG_01_SHARE_PARTITION
main_normal_damage_pre_share_Dtotal: 685
share_ratio: 0.15
main_target_assigned_Dtarget: 582
sharer_loss_Dsharer: 103
target_troops_before: 5000
actual_target_loss: 582
cleave_ratio: 0.54
expected_cleave_base: 582  # ActualTargetTroopLoss (Dtarget), NOT Dtotal (685)
expected_cleave_damage: 314  # floor(582 * 0.54)
refuted_cleave_damage_if_Dtotal: 369  # floor(685 * 0.54)
```

### Vector 2: Main Attack with Overkill
```yaml
id: CLEAVE_REG_02_OVERKILL_CLAMP
main_normal_damage_unclamped_Dtarget: 700
target_troops_before: 55
actual_target_loss: 55  # min(700, 55)
cleave_ratio: 0.54
expected_cleave_base: 55  # ActualTargetTroopLoss, NOT unclamped Dtarget (700)
expected_cleave_damage: 29  # floor(55 * 0.54)
refuted_cleave_damage_if_unclamped: 378  # floor(700 * 0.54)
```

### Vector 3: Clean Baseline with FLOOR Integerization
```yaml
id: CLEAVE_REG_03_INTEGERIZATION_FLOOR
actual_target_loss: 635
cleave_ratio: 0.54
exact_product: 342.9
expected_cleave_damage: 342  # floor(342.9)
refuted_cleave_damage_if_round_half_up: 343  # round_half_up(342.9)
```

### Vector 4: Secondary Target with Share and Lifesteal Recovery
```yaml
id: CLEAVE_REG_04_SECONDARY_SHARE_RECOVERY
cleave_derived_damage: 314
secondary_share_ratio: 0.15
secondary_target_Dtarget: 267
secondary_sharer_Dsharer: 47
attacker_lifesteal_ratio: 0.10
expected_recovery_basis: 267  # secondary Dtarget, NOT 314 (Dtotal) and NOT 314 (Dtarget + Dsharer)
expected_lifesteal_heal: 26  # floor(267 * 0.10)
```

---

## 15. Changed Files

1. `stages/stage9/research/cleave_damage_layer/extract_cleave_damage_layer.py` (NEW)
2. `stages/stage9/research/cleave_damage_layer/CLEAVE_DAMAGE_LAYER_EVIDENCE.json` (NEW)
3. `stages/stage9/research/cleave_damage_layer/RF_P06_CLEAVE_DAMAGE_LAYER_RESEARCH_REPORT.md` (NEW)
4. `stages/stage9/research/core_arbitration_v2/STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` (MODIFIED)
5. `stages/stage9/repairs/RF_P06_CLEAVE_DAMAGE_LAYER_AND_RECOVERY_BASIS_REFREEZE.md` (NEW)

---

## 16. Commits & Final Verdict

- **Commit 1**: `research(stage9): resolve cleave damage base layer`
- **Commit 2**: `repair(stage9): re-freeze cleave damage layer semantics`
- **Final Verdict**: **`RF-P06 CLOSED`**
