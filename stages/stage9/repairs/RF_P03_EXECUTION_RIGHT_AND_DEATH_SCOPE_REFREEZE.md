# RF-P03 Repair Record

## EXECUTION_RIGHT_AND_DEATH_SCOPE_REFREEZE

`	ext
Package: RF-P03
Level: A
Priority: P0
Execution Type: CONTRACT, EMPIRICAL EVIDENCE, AND ARBITRATION REPAIR
Need New Extractor: CONDITIONAL YES (Executed and archived: extract_combo_non_counter_deaths.py)
Repair Date: 2026-09-13
Final Verdict: RF-P03 CLOSED
Affected Findings:
  CBS9-B01 = CLOSED
  CFS9-B01 = CLOSED AS UNREACHABLE
  SHS9-M01 = CLOSED
  DSTS9-M01 = CLOSED
`

---

## 1. Repository Baseline

Repair start exact main refs were re-read and verified immediately before modification:

### Battle repository

`	ext
Repository:
lxy2005051020-commits/sgs-v2-battle-system

repair-before exact main HEAD:
e31af16f2336db99141474514a7078118bd78bde

repair(stage9): re-freeze integerization semantics
`

### State-mechanics research repository

`	ext
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

repair-before exact main HEAD:
add9a2134e88e90a58abf46eafd1de9d8c6f3b99

docs(damage-share): re-freeze integerization semantics
`

---

## 2. Affected Findings & Dispositions

RF-P03 specifically targets and resolves the action-death scope, execution rights, and transaction boundaries across Stage 9 mechanisms:

`	ext
CBS9-B01: COMBO own-open-action death continuation (universal rule deletion & empirical classification)
CFS9-B01: CONFUSION operationality upon dead actor reaching #2 fresh target resolution
SHS9-M01: DAMAGE_SHARE P0 over-owning outer Action upon target death
DSTS9-M01: DISTRIBUTION P0 over-owning outer Action upon target death
`

Disposition after repair:

`	ext
CBS9-B01  = CLOSED
CFS9-B01  = CLOSED AS UNREACHABLE
SHS9-M01  = CLOSED
DSTS9-M01 = CLOSED
`

Explicitly preserved as OPEN for later repair packages:

`	ext
CBS9-B03  = OPEN → RF-P04 (Battle Finalization Barrier)
SHS9-B02  = OPEN → RF-P05 (Target-Death Remainder Loss Commit)
DSTS9-B02 = OPEN → RF-P05 (Target-Death Remainder Loss Commit)
CLVS9-B01 = OPEN → RF-P06 (Cleave Architecture Re-Freeze)
CLVS9-B04 = OPEN → RF-P04 (Battle Finalization Barrier)
`

---

## 3. Authoritative Source of Truth Re-Frozen

The authoritative contracts have been updated and re-frozen across both repositories:

1. **Battle repository**:
   - stages/stage9/research/core_arbitration_v2/STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md
     - Created comprehensive shared execution ownership contract.
     - Formally defined 9 distinct Execution Scopes (GLOBAL_BATTLE, ROUND_PHASE, MAJOR_ACTION, REACTION_CHAIN, STATE_MICRO_TRANSACTION, TARGET_QUEUE_STEP, ATTRIBUTION_STATISTICS, MUTATION_PIPELINE, TERMINATION_BARRIER).
     - Established Two-Tier State Execution Model (Admission Right vs Local Liveness Gate).
     - Codified 7 Core Invariants preventing mechanism over-ownership.
   - stages/stage9/research/core_arbitration_v2/STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md
     - Updated Section 18.1: Replaced ABORT_REMAINING_ACTION with Transaction-Scoped Ownership. Delegated outer Action and finalization to Core Orchestrator / RF-P04. Closed SHS9-M01.
     - Updated Section 28 Frozen Declarations.
   - stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md
     - Updated Section 14: Replaced ABORT_REMAINING_ACTION with Transaction-Scoped Ownership. Delegated outer Action and finalization to Core Orchestrator / RF-P04. Closed DSTS9-M01.
     - Updated Section 19 Frozen Declarations.

2. **State-mechanics research repository**:
   - states/functional/combo/MECHANISM_CONTRACT.md
     - Header metadata & Finding Ledger updated (CBS9-B01 = CLOSED, CFS9-B01 = CLOSED AS UNREACHABLE, CBS9-B03 = OPEN → RF-P04).
     - Section 18: Completely deleted universal own-action death continuation rule. Added Empirical Death Family Matrix showing PROVEN ABORT for all reachable intra-action death families. Closed CBS9-B01.
     - Section 19: Proved dead actor reaching #2 fresh target resolution is 0/500 (0.0%). Closed CFS9-B01 as CLOSED AS UNREACHABLE without modifying CONFUSION operational semantics.
   - states/functional/damage_share/MECHANISM_CONTRACT.md
     - Updated Section 18.1 and Section 28 identical to battle repository, keeping both repos semantically synchronized.

---

## 4. Empirical Evidence & Extraction Infrastructure

A high-performance empirical extractor was developed and executed across the complete 32,999 battle corpus:

- Extractor: stages/stage9/research/execution_right_death_scope/extract_combo_non_counter_deaths.py
- Evidence Store: stages/stage9/research/execution_right_death_scope/EXECUTION_RIGHT_EVIDENCE.json
- Research Report: stages/stage9/research/execution_right_death_scope/RF_P03_EXECUTION_RIGHT_RESEARCH_REPORT.md

### Empirical Corpus Statistics:
- Total battle files scanned: **32,999**
- Attacker deaths during Normal Attack #1 before Combo Checkpoint: **500 verified unconfounded cases**
- Distribution across Action-Death Families:
  - COUNTER_DAMAGE: 362 cases (72.4%)
  - DERIVED_REACTION_DAMAGE (e.g., 【刚烈不屈】/ 【刚烈】): 115 cases (23.0%)
  - OTHER_ACTION_DEATH (reaction chains): 23 cases (4.6%)
  - REFLECT_DAMAGE, SELF_COST, PERIODIC_DAMAGE, COMMANDER_COLLATERAL: 0 reachable cases in intra-Normal Attack #1 window.

### Key Findings:
1. **Total Continued Combo (cfg 230)**: **0 / 500 (0.00%)**
2. **Total Second Normal Attack (cfg 9)**: **0 / 500 (0.00%)**
3. **Total Assault Skill Dispatch**: **0 / 500 (0.00%)**
4. **CFS9-B01 Reachability**: **0 / 500 (0.00%)** dead actors reached fresh target resolution.

### Mirror Matchup Disambiguation:
The empirical investigation resolved critical mirror-matchup confounders (e.g., Friendly 太史慈 vs Enemy 太史慈). In logs without color tags, defender deaths followed by the alive attacker's combo could be misread as "dead attacker continuing combo". Preserving HTML color tags (#ec616b enemy vs #75b3ed friendly) definitively proved 100% of combo executions belong to alive generals.

---

## 5. Scope Separation & Next Package

All Stage 9 boundaries remain strictly maintained:
- RF-P01 (Integerization Policy): CLOSED
- RF-P02 (Combo Lifecycle Contract): CLOSED
- RF-P03 (Execution Right and Death Scope): CLOSED
- Next recommended package: **RF-P06 — CLEAVE_ARCHITECTURE_REFREEZE** (or RF-P04 — BATTLE_FINALIZATION_BARRIER)
