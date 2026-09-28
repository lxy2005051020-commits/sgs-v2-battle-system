# RF-P05 Partition Transaction Death Research Report

> Project: 三国志战略版战斗模拟器 V2  
> Package: **RF-P05 — PARTITION_TRANSACTION_DEATH**  
> Priority: P0 (Blocker)  
> Scope: Empirical arbitration of target/participant death boundaries in Damage Partition transactions  
> Affected Findings:  
> - `SHS9-B02`: DAMAGE_SHARE target-first commit — target lethal from $D_{\text{target}}$ -> pending sharer loss cancellation  
> - `DSTS9-B02`: DISTRIBUTION participants-first commit — commander participant death -> later participant & target commit continuation  
> Date: 2026-09-13  
> Status: **RESEARCH COMPLETE / VERDICT REACHED**

---

## 1. Executive Summary

This research package executes the empirical investigation and contract closure for **RF-P05 (PARTITION_TRANSACTION_DEATH)**, resolving the fatal intersection between entity death and multi-step damage partition transactions across two distinct mechanisms:

1. **TRACK A — DAMAGE_SHARE (`SHS9-B02`)**:
   - **Hypothesis under test**: In target-first commit topology, if the protected target takes $D_{\text{target}}$ and is reduced to 0 troops (dies), does the pending theoretical share loss $D_{\text{sharer}}$ commit to the living sharer or is it cancelled?
   - **Empirical result**: Across 2,128 damage share battle reports (13,834 share events), **128 unconfounded lethal target samples** were identified using a new lethal-first unbiased extractor.
   - In **128 / 128 cases (100.0%)**, the pending sharer loss was **completely cancelled / dropped**. The living sharer suffered exactly 0 damage and 0 troop loss.
   - **Verdict**: **`TARGET_DEATH_CANCELS_PENDING_SHARER` (TARGET_DEATH_INTERRUPT)** is 100% empirically confirmed. **`SHS9-B02 = CLOSED`**.

2. **TRACK B — DISTRIBUTION (`DSTS9-B02`)**:
   - **Hypothesis under test**: In participants-first commit topology, if an earlier participant—specifically the **Commander (Slot 0)**—dies from $D_{\text{participant}}$, do later participants and the original target continue committing their assigned amounts, or does commander death abort the transaction?
   - **Control verification**: Ordinary deputy participant death continuation was re-verified via direct Grade A battle evidence (`战报_596995_pid594340.json`: deputy 程普 reached 0 troops, and original target 刘备 subsequently committed $D_{\text{target}}=266$).
   - **Empirical result for Commander participant death**: Across the entire 32,999 battle report corpus, 20 reports feature 【义心昭烈】/ 分摊 (68 distinct participant executions). In all 28 cases where the commander acted as a participant, the commander survived. **Zero cases** of commander death during a Distribution participant commit exist in the corpus.
   - **Verdict**: Commander participant death is **`EMPIRICALLY UNOBSERVED (0 cases in 32,999 corpus)`**. In strict compliance with consolidation admission standards, no unproven rule is fabricated. **`DSTS9-B02 REMAINS OPEN`**.

**Package Final Verdict**: **`RF-P05 PARTIALLY CLOSED`** (`SHS9-B02 = CLOSED`, `DSTS9-B02 = OPEN / UNRESOLVED`).

---

## 2. Selection Bias Fix in Extractor Architecture

Historical extractors (e.g., `r6_fendan_math_data.json`, 11,381 cases, `lethal_count = 0`) exhibited severe selection bias: they required locating a sharer execution/loss event (`cfg_id: 28` on sharer) as the extraction anchor, and then searched backwards for target damage. This naturally filtered out any event where the target died and the sharer event never occurred!

RF-P05 constructed two independent, unbiased extractors:

1. **`extract_share_lethal_target.py`**:
   - Anchor: **Target DamageEvent with operational Share** (`[目标]由于【战法】的「分担」效果，本次攻击受到的伤害减少了 R%`).
   - Reconstructs partition: $D_{\text{target}}$ and estimated $D_{\text{sharer\_theoretical}}$.
   - Filters for **Target Lethal Commit**: Target troop loss event where remaining troops reaches 0 (`损失了兵力 X（0）`).
   - Scans forward through the transaction window to inspect whether any sharer commit occurs before the next action/target.

2. **`extract_distribution_commander_participant.py`**:
   - Anchor: Distribution transaction start announcement on protected target (`[目标]执行来自【义心昭烈】的「分摊」效果`).
   - Tracks participant commit sequence (Slot 0 -> Slot 1 -> Slot 2) and final target commit.
   - Specifically monitors whether Slot 0 (Commander) or any deputy participant reaches 0 troops.

---

## 3. TRACK A: DAMAGE_SHARE Lethal Target Matrix (`SHS9-B02`)

### 3.1 Corpus Statistics
- Total battle files scanned: **2,128**
- Total verified lethal target candidates: **128**
- Outcome counts:
  - `TARGET_DEATH_CANCELS_PENDING_SHARER`: **128 (100.0%)**
  - `TARGET_DEATH_DOES_NOT_CANCEL_PENDING_SHARER`: **0 (0.0%)**
  - `CONFOUNDED`: **0**
  - `INSUFFICIENT_WINDOW`: **0**
- Non-lethal control cases verified: **20** (100% had normal sharer commit)

### 3.2 SHARE_LETHAL_MATRIX (Representative Grade A Samples)

| Sample ID | Battle Report ID | Target | Sharer | $D_{\text{total}}$ (est) | $D_{\text{target}}$ | $D_{\text{sharer}}$ (theor) | Target Lethal? | Sharer Alive? | Sharer Committed? | Final Verdict |
|---|---|---|---|---:|---:|---:|:---:|:---:|:---:|---|
| `SHARE_LETHAL_001` | `战报_1008108_pid1003335.json` | 曹洪 | 傅士仁 | 42 | 36 | 6 | YES (rem=0) | YES (rem=203) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_002` | `战报_1105153_pid1100248.json` | 夏侯惇 | 曹操 | 127 | 108 | 19 | YES (rem=0) | YES (rem=3940) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_003` | `战报_1481635_pid1504808.json` | 庞德 | 纪灵 | 199 | 169 | 30 | YES (rem=0) | YES (rem=2391) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_014` | `战报_1642878_pid1642868.json` | 司马懿 | 曹操 | 107 | 91 | 16 | YES (rem=0) | YES (rem=4520) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_025` | `战报_2112836_pid2176378.json` | 关羽 | 赵云 | 235 | 200 | 35 | YES (rem=0) | YES (rem=1850) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_048` | `战报_2245864_pid2317157.json` | 华雄 | 纪灵 | 65 | 55 | 10 | YES (rem=0) | YES (rem=2840) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_060` | `战报_2491044_pid2598352.json` | 主公 | 曹操 | 1079 | 917 | 162 | YES (rem=0) | YES (rem=2461) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_061` | `战报_2492146_pid2599832.json` | 庞德 | 纪灵 | 33 | 28 | 5 | YES (rem=0) | YES (rem=1465) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_067` | `战报_2495884_pid2604789.json` | 韩遂 | 纪灵 | 699 | 594 | 105 | YES (rem=0) | YES (rem=3120) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_072` | `战报_2496204_pid2605194.json` | 乐进 | 夏侯惇 | 625 | 531 | 94 | YES (rem=0) | YES (rem=1800) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_085` | `战报_2501198_pid2611695.json` | 郭嘉 | 张辽 | 345 | 293 | 52 | YES (rem=0) | YES (rem=3249) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |
| `SHARE_LETHAL_120` | `战报_3448318_pid3812171.json` | 主公 | 曹操 | 101 | 86 | 15 | YES (rem=0) | YES (rem=3268) | **NO (0 loss)** | `TARGET_DEATH_CANCELS_PENDING_SHARER` |

### 3.3 Target Death Interrupt Mechanism
The empirical data establishes the exact execution flow of `TARGET_DEATH_INTERRUPT`:
```text
[DamageEvent Partition Completed]
  D_target = D_total - D_sharer_theor
  ↓
[Target Commit]
  target.currentTroops -= D_target
  target.death_check()
  ↓
[Target Dies: target.currentTroops == 0]
  OnTargetDeath triggered
  Transaction-local interrupt: ABORT_PENDING_SHARE_COMMIT
  D_sharer_theor DISCARDED (vanishes)
  Sharer commits: NONE (0 troop loss)
```
This is fully consistent with RF-P03: the interrupt is **strictly transaction-local**. It does not abort the outer action or other targets in an AOE sequence, but only drops the pending micro-commit to the sharer.

---

## 4. TRACK B: DISTRIBUTION Commander Participant Matrix (`DSTS9-B02`)

### 4.1 Corpus Statistics
- Entire battle corpus scanned: **32,999 files**
- Files containing 【义心昭烈】/ 分摊: **20 files** (27 combat group sessions)
- Total Distribution transactions analyzed: **68**
- Cases with commander as a participant: **28**
- **Commander participant lethal cases: 0 (EMPIRICALLY UNOBSERVED)**
- **Ordinary participant lethal cases (Control): 1** (`战报_596995_pid594340.json`)

### 4.2 Control Case: Ordinary Participant Lethal Commit
In `战报_596995_pid594340.json` (Round 3, event 20-28):
1. **Target**: Commander `[刘备]` has Distribution from 【义心昭烈】.
2. **Participant Plan**: `[主公]` (Slot 1), `[程普]` (Slot 2).
3. **Participant Commit 1**: `[主公]` loses 71 troops (survives, 971 troops remaining).
4. **Participant Commit 2 (LETHAL)**: `[程普]` loses 49 troops -> **reaches 0 troops (`兵力为0，无法再战`)**.
5. **Target Commit**: Despite deputy `[程普]` dying in step 2, target `[刘备]` **continues and commits $D_{\text{target}} = 266$** (reducing troops from 312 to 46).
6. **Verdict**: **`ORDINARY_PARTICIPANT_DEATH_CONTINUES`** is empirically validated with Grade A direct evidence.

### 4.3 DISTRIBUTION_COMMANDER_MATRIX

| Sample ID | Battle Report ID | Target | Commander Participant | Commander Dies? | Later Participant Exists? | Later Participant Commits? | Target Commits? | Finalization Marker | Verdict |
|---|---|---|---|:---:|:---:|:---:|:---:|:---:|---|
| `DIST_CONTROL_001` | `战报_596995_pid594340.json` | 刘备 (Cmd) | None (程普 deputy died) | NO | NO (was last part) | N/A | **YES (Dtarget=266)** | None (battle continues) | `ORDINARY_PARTICIPANT_DEATH_CONTINUES` |
| `DIST_CMD_CANDIDATE` | All 32,999 Reports | Deputy | Commander | **NO (0 cases)** | N/A | N/A | N/A | N/A | **`EMPIRICALLY UNOBSERVED`** |

### 4.4 Disposition of DSTS9-B02
Because zero instances of a commander participant dying during Distribution exist in the entire empirical dataset:
- We **refuse to invent an unverified empirical rule**.
- In the Stage 9 Consolidation Ledger, **`DSTS9-B02 REMAINS OPEN / UNRESOLVED`**.
- An explicit engineering default (e.g. following the ordinary participant continuation model, where the transaction finishes before battle finalization checks) may be adopted in runtime implementation, but the formal empirical finding remains unclosed.

---

## 5. Summary of Finding Dispositions for RF-P05

| Finding ID | Mechanism | Severity | Disposition | Empirical Evidence |
|---|---|---|---|---|
| **`SHS9-B02`** | DAMAGE_SHARE | BLOCKER | **CLOSED** | 128 / 128 (100.0%) lethal target samples confirm `TARGET_DEATH_INTERRUPT` (sharer takes 0 loss). |
| **`DSTS9-B02`** | DISTRIBUTION | BLOCKER | **OPEN / UNRESOLVED** | 0 commander lethal participant samples in 32,999 corpus (`EMPIRICALLY UNOBSERVED`). Control case confirmed ordinary participant death continuation. |

**Final Package Verdict**: **`RF-P05 PARTIALLY CLOSED`**.
All research evidence and extractors are permanently archived in `stages/stage9/research/partition_transaction_death/`.
