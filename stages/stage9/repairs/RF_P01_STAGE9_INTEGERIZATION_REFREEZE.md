# RF-P01 Repair Record

## STAGE9_INTEGERIZATION_POLICY_REFREEZE

```text
Package: RF-P01
Level: B
Priority: P0
Execution Type: CONTRACT AND EVIDENCE REPAIR
Need New Extractor: YES (executed and archived)
Repair Date: 2026-09-13
Final Verdict: RF-P01 CLOSED
Affected Findings:
  CHNS9-B01 = CLOSED
  SHS9-B01  = CLOSED
  DSTS9-B01 = CLOSED
  CLVS9-B01 = OPEN (Sub-check only; base layer remains open for RF-P06)
```

---

## 1. Repository Baseline

Repair start exact `main` refs were re-read and verified immediately before modification:

### Battle repository

```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

repair-before exact main HEAD:
2053f3360e4a058bfc254be785da102802070e9f

repair(stage9): sync combo lifecycle re-freeze

repair-before parent:
49aeea81f22ba94cc791eea75f9501b78b484c29
```

### State-mechanics research repository

```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

repair-before exact main HEAD:
96719f98d11cd5ad60cd3eda568bda8d2e0e790d

docs(combo): re-freeze lifecycle ownership contract

repair-before parent:
9d86e54c407913ff020bafacf8196085780b99c6
```

---

## 2. Affected Findings & Dispositions

RF-P01 specifically targets and resolves the integerization semantics across Stage 9 mechanisms:

```text
CHNS9-B01: CHAIN_LINK feedback integerization
SHS9-B01:  DAMAGE_SHARE theoretical partition integerization
DSTS9-B01: DISTRIBUTION target & participant integerization
CLVS9-B01: Cleave numeric formula sub-check (NOT closed here; base layer deferred to RF-P06)
```

Disposition after repair:

```text
CHNS9-B01 = CLOSED
SHS9-B01  = CLOSED
DSTS9-B01 = CLOSED
CLVS9-B01 = OPEN → RF-P06
```

Explicitly preserved as OPEN for later repair packages:

```text
CBS9-B01 = OPEN → RF-P03
CBS9-B03 = OPEN → RF-P04
CFS9-B01 = OPEN → RF-P03
SHS9-B02 = OPEN → RF-P08
DSTS9-B02 = OPEN → RF-P08
CLVS9-B01 = OPEN → RF-P06
```

---

## 3. Authoritative Source of Truth Re-Frozen

The authoritative contracts have been updated and re-frozen across both repositories:

1. **Battle repository**:
   - `stages/stage9/research/core_arbitration_v2/STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`
     - Added Section 2.1 freezing `ChainCalculatedDamage = floor(TriggerNodeResolvedDamage * ChainRatio)`.
     - Updated Section 17 Frozen Declarations.
   - `stages/stage9/research/core_arbitration_v2/STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md`
     - Updated Section 9 & Section 9.1 freezing `Dsharer_theoretical = round_half_up(Dtotal * R)`.
     - Explicitly froze tie-breaking rule: exact `.5` ties round toward positive infinity.
     - Updated Section 26 pseudocode and Section 28 Frozen Declarations.
   - `stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`
     - Updated Section 4.2 freezing `Dtarget = round_half_up(Dtotal * (1 - R))`.
     - Updated Section 4.3 freezing `Dparticipant = round_half_up(Dtransfer / N)`.
     - Added Section 4.5 freezing `ROUND_HALF_UP` tie-breaking rule for both call sites.
     - Updated Section 17 pseudocode, Section 18 regression tests, and Section 19 Frozen Declarations.
2. **State-mechanics research repository**:
   - `states/functional/damage_share/MECHANISM_CONTRACT.md`
     - Semantically identical to battle repo DAMAGE_SHARE contract.
     - Updated Section 9 & 9.1 and Section 26 & 28 freezing `round_half_up` and closing `SHS9-B01`.

---

## 4. Empirical Evidence & Extraction Infrastructure

A dedicated empirical research pipeline was created and executed:
- `stages/stage9/research/integerization/extract_integerization_boundaries.py`
- `stages/stage9/research/integerization/analyze_integerization_candidates.py`
- `stages/stage9/research/integerization/INTEGERIZATION_EVIDENCE.json`
- `stages/stage9/research/integerization/RF_P01_INTEGERIZATION_RESEARCH_REPORT.md`

Dataset: **32,660 indexed battles** scanned from `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`.

### Elimination Summary by Call Site

#### 1. `CHAIN_INTEGERIZATION` (`CHNS9-B01`)
- **Expression**: `ChainCalculatedDamage = integerize(TriggerNodeResolvedDamage * ChainRatio)`
- **Sample Count**: 1,657 samples across multi-hit battles.
- **Candidate Elimination**:
  - `FLOOR`: 1,657 matches / 0 contradictions (**100.0%**) $\implies$ **CONFIRMED**
  - `ROUND_HALF_UP`: 849 matches / 808 contradictions (**ELIMINATED**)
  - `ROUND_HALF_EVEN`: 849 matches / 808 contradictions (**ELIMINATED**)
  - `CEIL`: 1 match / 1,656 contradictions (**ELIMINATED**)
- **Decisive Battle Proofs**:
  - `396 * 28.28% = 111.9888` $\to$ observed = **111** (half-up predicts 112, refuted)
  - `753 * 28.28% = 212.9484` $\to$ observed = **212** (half-up predicts 213, refuted)
  - `551 * 28.28% = 155.8228` $\to$ observed = **155** (half-up predicts 156, refuted)
  - `265 * 22.58% = 59.837` $\to$ observed = **59** (half-up predicts 60, refuted)

#### 2. `SHARE_INTEGERIZATION` (`SHS9-B01`)
- **Expression**: `Dsharer_theoretical = integerize(Dtotal * R)`, `Dtarget = Dtotal - Dsharer_theoretical`
- **Sample Count**: 98 exact-half boundary samples (【严阵以待】$R = 15.00\% = 3/20$).
- **Candidate Elimination**:
  - Even $K$ Ties ($K$ even, theoretical $= K + 0.5$): **47/47 (100%) round UP to $K+1$**.
  - Odd $K$ Ties ($K$ odd, theoretical $= K + 0.5$): **39/39 (100%) round UP to $K+1$**.
  - Eliminates `ROUND_HALF_EVEN` (which predicts even $K$ round down to $K$).
  - Eliminates `FLOOR` (which predicts all ties round down).
  - Controls below 0.5 round down, eliminating `CEIL`.
- **Executable Rule**: **`ROUND_HALF_UP`** $\implies$ **CONFIRMED**

#### 3. `DISTRIBUTION_TARGET_INTEGERIZATION` (`DSTS9-B01`)
- **Expression**: `Dtarget = integerize(Dtotal * (1 - R))`, `Dtransfer = Dtotal - Dtarget`
- **Sample Count**: 12 exact-half boundary samples ($R = 50.00\%$).
- **Candidate Elimination**:
  - Exact-half ties: **12/12 (100%) round UP to $K+1$**.
  - Controls $< 0.5$ round down; controls $> 0.5$ round up.
- **Executable Rule**: **`ROUND_HALF_UP`** $\implies$ **CONFIRMED**

#### 4. `DISTRIBUTION_PARTICIPANT_INTEGERIZATION` (`DSTS9-B01`)
- **Expression**: `Dparticipant = integerize(Dtransfer / N)`
- **Sample Count**: 34 exact-half boundary samples ($N=2$, odd $D_{\text{transfer}}$).
- **Candidate Elimination**:
  - Even $K$ Ties: **17/17 (100%) round UP to $K+1$**.
  - Odd $K$ Ties: **17/17 (100%) round UP to $K+1$**.
  - Eliminates `ROUND_HALF_EVEN` and `FLOOR`.
- **Executable Rule**: **`ROUND_HALF_UP`** $\implies$ **CONFIRMED**

---

## 5. Cross-Mechanism Policy Comparison & Architectural Rules

### Are all 4 call sites identical?
**NO.**
- `CHAIN` uses **`FLOOR`**.
- `SHARE`, `DISTRIBUTION_TARGET`, and `DISTRIBUTION_PARTICIPANT` use **`ROUND_HALF_UP`**.

### Architectural Invariant
1. **No Monolithic Integerization Assumption**:
   A generic global rounding helper cannot be assumed without call-site dispatch.
2. **Deterministic Rational Evaluation**:
   Ties must be evaluated without IEEE 754 floating-point precision loss.
3. **Conservation Invariants**:
   - `DAMAGE_SHARE`: $D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$ guarantees exact theoretical conservation ($D_{\text{target}} + D_{\text{sharer}} = D_{\text{total}}$).
   - `DISTRIBUTION`: Second-order rounding differences are permitted algorithm results; asymmetric remainder compensation to the last participant is strictly forbidden.

---

## 6. Before / After Contract Text Matrix

| Mechanism / Call Site | Before RF-P01 | After RF-P01 | Finding Status |
|---|---|---|---|
| **`CHAIN`** (`ChainCalculatedDamage`) | Unspecified integerization rule (`ChainCalculatedDamage = TriggerNodeResolvedDamage × ChainRatio`) | **`floor(TriggerNodeResolvedDamage × ChainRatio)`** explicitly frozen; 1,657 battle proofs (100.0%) | `CHNS9-B01 = CLOSED` |
| **`DAMAGE_SHARE`** (`Dsharer_theoretical`) | Ambiguous `round(Dtotal * R)` without tie-breaking specification | **`round_half_up(Dtotal * R)`** explicitly frozen; ties round upward; 98 battle proofs eliminate half-even & floor | `SHS9-B01 = CLOSED` |
| **`DISTRIBUTION`** (`Dtarget`) | Ambiguous `round(Dtotal * (1 - R))` | **`round_half_up(Dtotal * (1 - R))`** explicitly frozen; 12 battle proofs | `DSTS9-B01 = CLOSED` |
| **`DISTRIBUTION`** (`Dparticipant`) | Ambiguous `round(Dtransfer / N)` | **`round_half_up(Dtransfer / N)`** explicitly frozen; 34 battle proofs eliminate half-even & floor | `DSTS9-B01 = CLOSED` |
| **`CLEAVE`** (`CLVS9-B01`) | Cleave base layer and secondary target numeric formula open | Sub-check performed; base layer remains unresolved until RF-P06 | `CLVS9-B01 = OPEN` (deferred to RF-P06) |

---

## 7. Deterministic Regression Vectors

| Vector ID | Call Site | Inputs | Formula | Expected Output | Property Verified |
|---|---|---|---|---:|---|
| `VEC-CHN-01` | CHAIN | Trigger=396, Ratio=28.28% | $396 \times 0.2828 = 111.9888$ | **111** | Eliminates round_half_up |
| `VEC-CHN-02` | CHAIN | Trigger=753, Ratio=28.28% | $753 \times 0.2828 = 212.9484$ | **212** | Eliminates round_half_up |
| `VEC-CHN-03` | CHAIN | Trigger=265, Ratio=22.58% | $265 \times 0.2258 = 59.8370$ | **59** | Eliminates round_half_up |
| `VEC-SHR-01` | SHARE | Dtotal=470, R=15.00% | $470 \times 0.15 = 70.5$ | Dsharer=**71**, Dtarget=**399** | Even $K$ tie rounds UP |
| `VEC-SHR-02` | SHARE | Dtotal=250, R=15.00% | $250 \times 0.15 = 37.5$ | Dsharer=**38**, Dtarget=**212** | Odd $K$ tie rounds UP |
| `VEC-SHR-03` | SHARE | Dtotal=10, R=15.00% | $10 \times 0.15 = 1.5$ | Dsharer=**2**, Dtarget=**8** | Small value tie rounds UP |
| `VEC-SHR-04` | SHARE | Dtotal=469, R=15.00% | $469 \times 0.15 = 70.35$ | Dsharer=**70**, Dtarget=**399** | Non-tie low rounds DOWN |
| `VEC-SHR-05` | SHARE | Dtotal=471, R=15.00% | $471 \times 0.15 = 70.65$ | Dsharer=**71**, Dtarget=**400** | Non-tie high rounds UP |
| `VEC-DST-01` | DST_TGT | Dtotal=251, R=50.00% | $251 \times 0.50 = 125.5$ | Dtarget=**126**, Dtransfer=**125** | Target tie rounds UP |
| `VEC-DST-02` | DST_TGT | Dtotal=407, R=50.00% | $407 \times 0.50 = 203.5$ | Dtarget=**204**, Dtransfer=**203** | Target tie rounds UP |
| `VEC-DST-03` | DST_PART | Dtransfer=353, N=2 | $353 / 2 = 176.5$ | Dparticipant=**177** (both) | Even $K$ participant tie rounds UP |
| `VEC-DST-04` | DST_PART | Dtransfer=147, N=2 | $147 / 2 = 73.5$ | Dparticipant=**74** (both) | Odd $K$ participant tie rounds UP |
| `VEC-DST-05` | DST_PART | Dtransfer=100, N=3 | $100 / 3 = 33.333...$ | Dparticipant=**33** (all 3) | Non-tie low rounds DOWN |
| `VEC-DST-06` | DST_PART | Dtransfer=200, N=3 | $200 / 3 = 66.666...$ | Dparticipant=**67** (all 3) | Non-tie high rounds UP |

---

## 8. Commit and Sync Baseline

### Battle repository
- Commit message: `repair(stage9): re-freeze stage9 integerization semantics`
- Modified files:
  - `stages/stage9/research/core_arbitration_v2/STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`
  - `stages/stage9/research/core_arbitration_v2/STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md`
  - `stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`
  - `stages/stage9/repairs/RF_P01_STAGE9_INTEGERIZATION_REFREEZE.md`

### State-mechanics research repository
- Commit message: `docs(damage-share): re-freeze integerization semantics`
- Modified file:
  - `states/functional/damage_share/MECHANISM_CONTRACT.md`

---

## 9. Final Verdict & Gate Status

```text
================================================================================
RF-P01 VERDICT: CLOSED
--------------------------------------------------------------------------------
CHNS9-B01: CLOSED (Floor rule frozen)
SHS9-B01:  CLOSED (Round-half-up rule frozen)
DSTS9-B01: CLOSED (Round-half-up rule frozen)
CLVS9-B01: OPEN (Deferred to RF-P06)

Next Package: RF-P03 (CBS9-B01, CFS9-B01, TAS9-B01, CNS9-B01: Action Start / Dispatch Orchestration)
================================================================================
```
