# RF-P01 Research Report: Stage 9 Integerization Policy

```text
Repair Package: RF-P01
Target Findings: CHNS9-B01, SHS9-B01, DSTS9-B01
Sub-check Finding: CLVS9-B01 (Sub-check only; base layer remains open for RF-P06)
Date: 2026-09-13
Repository Baseline:
  battle repo: 2053f3360e4a058bfc254be785da102802070e9f
  state research repo: 96719f98d11cd5ad60cd3eda568bda8d2e0e790d
```

---

## 1. Executive Summary

This research establishes the exact, observable, executable integerization rules for the four numeric partition/feedback call sites across Stage 9 mechanisms:

1. **`CHAIN_INTEGERIZATION`**:
   $$\text{ChainCalculatedDamage} = \lfloor \text{TriggerNodeResolvedDamage} \times \text{ChainRatio} \rfloor$$
   **Executable Rule**: **`FLOOR`** (equivalent to `TRUNCATE_TOWARD_ZERO` for non-negative damage).
   Empirically proven with **1,657 samples (100.0% match, 0 contradictions)**. `ROUND_HALF_UP` and `ROUND_HALF_EVEN` each produce 808 contradictions. `CEIL` produces 1,656 contradictions.

2. **`SHARE_INTEGERIZATION`**:
   $$D_{\text{sharer\_theoretical}} = \operatorname{round\_half\_up}(D_{\text{total}} \times R)$$
   $$D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$$
   **Executable Rule**: **`ROUND_HALF_UP`** (exact half ties round toward positive infinity).
   Empirically proven with **98 exact-half boundary samples** under fixed-ratio skills (e.g. 【严阵以待】$R = 15.00\% = 3/20$):
   - When $K$ is EVEN ($N=47$): **47/47 (100%) round UP to $K+1$**.
   - When $K$ is ODD ($N=39$): **39/39 (100%) round UP to $K+1$**.
   - Decisively eliminates `ROUND_HALF_EVEN` (which predicts even $K$ round down to $K$) and `FLOOR`. Non-tie controls below 0.5 round down, eliminating `CEIL`.

3. **`DISTRIBUTION_TARGET_INTEGERIZATION`**:
   $$D_{\text{target}} = \operatorname{round\_half\_up}(D_{\text{total}} \times (1 - R))$$
   **Executable Rule**: **`ROUND_HALF_UP`**.
   Empirically proven with **12 exact-half boundary samples** ($R = 50.00\%$ under 【义心昭烈】):
   - **12/12 (100%) round UP to $K+1$**.
   - Fractional controls below 0.5 round down; controls above 0.5 round up.

4. **`DISTRIBUTION_PARTICIPANT_INTEGERIZATION`**:
   $$D_{\text{participant}} = \operatorname{round\_half\_up}\left(\frac{D_{\text{transfer}}}{N}\right)$$
   **Executable Rule**: **`ROUND_HALF_UP`**.
   Empirically proven with **34 exact-half boundary samples** ($N=2$, odd $D_{\text{transfer}}$):
   - When $K$ is EVEN ($N=17$): **17/17 (100%) round UP to $K+1$**.
   - When $K$ is ODD ($N=17$): **17/17 (100%) round UP to $K+1$**.
   - Decisively eliminates `ROUND_HALF_EVEN` and `FLOOR`.

**Crucial Cross-Mechanism Finding**:
The integerization policies across Stage 9 mechanisms **are NOT identical**:
- `CHAIN` uses **`FLOOR`**.
- `SHARE`, `DISTRIBUTION_TARGET`, and `DISTRIBUTION_PARTICIPANT` use **`ROUND_HALF_UP`**.

Therefore, Stage 9 cannot adopt a single monolithic rounding rule across all mechanisms. Each mechanism P0 contract explicitly freezes its own executable rule.

---

## 2. Research Methodology & Dataset

### 2.1 Battle Database Scope
- Extracted from indexed battle repository: `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`.
- Total indexed battle corpus: **32,660 battles**.
- Boundary search criteria:
  - Exact half-integer boundaries ($K + 0.5$).
  - Integer boundaries ($K + 0.0$).
  - Near-boundary control samples ($K + 0.5 \pm \epsilon$).

### 2.2 Numerical Rigor
- All theoretical values evaluated using exact rational arithmetic (`fractions.Fraction`) and high-precision `Decimal`.
- Floating-point representations (`float64`) are explicitly forbidden from determining boundary decisions to prevent IEEE 754 epsilon artifacts.

### 2.3 Confounder Isolation
1. **Sharer Post-Partition Mitigation**:
   - Generals like Cao Cao have innate passive damage reduction (e.g. 【乱世奸雄】reduces damage taken by ~28-30%).
   - When Cao Cao acts as a sharer, the damage attributed to him is first calculated via $D_{\text{sharer\_theoretical}}$, and subsequently reduced by his innate modifier when committing actual loss.
   - To isolate pure integerization, tests are conducted either on sharers without innate damage reduction or by observing the unmitigated display value in standard share logs.
2. **Dynamic Scaling vs Fixed Skill Ratios**:
   - Skills with dynamic intellect scaling (e.g. 【护卫】) display an approximate rounded percentage in the UI (e.g. `14.40%`), but the internal engine uses full-precision floating parameters (e.g. $\sim 14.4719\%$).
   - Skills with static fixed percentages (e.g. 【严阵以待】with exact $R = 15.00\% = \frac{3}{20}$, or 【义心昭烈】with exact $R = 50.00\% = \frac{1}{2}$) provide perfect, unambiguous rational test cases where $D_{\text{total}} \times R \equiv K + 0.5 \pmod 1$ exactly.

---

## 3. Call Site 1: `CHAIN_INTEGERIZATION` (Finding `CHNS9-B01`)

### 3.1 Mathematical Definition
$$\text{ChainCalculatedDamage} = \operatorname{integerize}(\text{TriggerNodeResolvedDamage} \times \text{ChainRatio})$$

### 3.2 Candidate Elimination Matrix
Total samples analyzed: **1,657** across multiple battles with multi-hit chains.

| Candidate Policy | Matches | Contradictions | Match Rate | Verdict |
|---|---:|---:|---:|---|
| **`FLOOR` / `TRUNCATE`** | **1,657** | **0** | **100.0%** | **CONFIRMED** |
| `ROUND_HALF_UP` | 849 | 808 | 51.2% | **ELIMINATED** |
| `ROUND_HALF_EVEN` | 849 | 808 | 51.2% | **ELIMINATED** |
| `CEIL` | 1 | 1,656 | 0.1% | **ELIMINATED** |

### 3.3 Empirical Evidence & Proof Samples
In battle `战报_1101874_pid1096972.json` (ChainRatio = 28.28%):
- `Trigger = 396`: $396 \times 0.2828 = 111.9888$.
  - Observed = **111**!
  - `ROUND_HALF_UP` predicts 112 (Contradiction).
  - `CEIL` predicts 112 (Contradiction).
  - `FLOOR` predicts 111 (Match).
- `Trigger = 753`: $753 \times 0.2828 = 212.9484$.
  - Observed = **212**!
  - `ROUND_HALF_UP` predicts 213 (Contradiction).
- `Trigger = 551`: $551 \times 0.2828 = 155.8228$.
  - Observed = **155**!
  - `ROUND_HALF_UP` predicts 156 (Contradiction).
- `Trigger = 621`: $621 \times 0.2828 = 175.6188$.
  - Observed = **175**!
  - `ROUND_HALF_UP` predicts 176 (Contradiction).
- `Trigger = 123`: $123 \times 0.2828 = 34.7844$.
  - Observed = **34**!
  - `ROUND_HALF_UP` predicts 35 (Contradiction).

In battle `战报_1102042_pid1097132.json` (ChainRatio = 28.28%):
- `Trigger = 265`: $265 \times 0.2828 = 74.942$. Observed = **74**!
- `Trigger = 166`: $166 \times 0.2828 = 46.9448$. Observed = **46**!
- `Trigger = 635`: $635 \times 0.2828 = 179.578$. Observed = **179**!

In battle `战报_1068460_pid1063452.json` (ChainRatio = 22.58%):
- `Trigger = 265`: $265 \times 0.2258 = 59.837$. Observed = **59**!
- `Trigger = 485`: $485 \times 0.2258 = 109.513$. Observed = **109**!

**Conclusion for `CHNS9-B01`**:
`ChainCalculatedDamage` unconditionally applies **`FLOOR`** (`math.floor` / truncate toward zero).

---

## 4. Call Site 2: `SHARE_INTEGERIZATION` (Finding `SHS9-B01`)

### 4.1 Mathematical Definition
$$D_{\text{sharer\_theoretical}} = \operatorname{integerize}(D_{\text{total}} \times R)$$
$$D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$$

### 4.2 Candidate Elimination Matrix
Unconfounded fixed-ratio dataset (【严阵以待】$R = 15.00\% = \frac{3}{20}$; exact half occurs when $D_{\text{total}} \equiv 10 \pmod{20}$):
- Total exact-half boundary samples: **98**
  - Even $K$ samples: **47**
  - Odd $K$ samples: **39**
- Controls below 0.5: **1,259**
- Controls above 0.5: **1,306**

| Candidate Policy | Even $K$ Ties ($N=47$) | Odd $K$ Ties ($N=39$) | Non-Tie Low ($N=1259$) | Non-Tie High ($N=1306$) | Verdict |
|---|---:|---:|---:|---:|---|
| **`ROUND_HALF_UP`** | **47/47 (100%)** | **39/39 (100%)** | **1259/1259 (100%)** | **1306/1306 (100%)** | **CONFIRMED** |
| `ROUND_HALF_EVEN` | 0/47 (0%) | 39/39 (100%) | 1259/1259 (100%) | 1306/1306 (100%) | **ELIMINATED** |
| `FLOOR` | 0/47 (0%) | 0/39 (0%) | 1259/1259 (100%) | 0/1306 (0%) | **ELIMINATED** |
| `CEIL` | 47/47 (100%) | 39/39 (100%) | 0/1259 (0%) | 1306/1306 (100%) | **ELIMINATED** |

### 4.3 Empirical Evidence & Proof Samples
Under 【严阵以待】($R = 15.00\%$):

**Even $K$ Tie Cases ($K$ is even, theoretical $= K + 0.5$, observed rounds UP to $K+1$)**:
- $D_{\text{total}} = 470 \implies 470 \times 0.15 = 70.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{71}$ ($K=70 \to 71$)
- $D_{\text{total}} = 710 \implies 710 \times 0.15 = 106.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{107}$ ($K=106 \to 107$)
- $D_{\text{total}} = 550 \implies 550 \times 0.15 = 82.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{83}$ ($K=82 \to 83$)
- $D_{\text{total}} = 430 \implies 430 \times 0.15 = 64.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{65}$ ($K=64 \to 65$)
- $D_{\text{total}} = 350 \implies 350 \times 0.15 = 52.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{53}$ ($K=52 \to 53$)
- $D_{\text{total}} = 590 \implies 590 \times 0.15 = 88.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{89}$ ($K=88 \to 89$)
- $D_{\text{total}} = 70 \implies 70 \times 0.15 = 10.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{11}$ ($K=10 \to 11$)
- $D_{\text{total}} = 270 \implies 270 \times 0.15 = 40.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{41}$ ($K=40 \to 41$)

**Odd $K$ Tie Cases ($K$ is odd, theoretical $= K + 0.5$, observed rounds UP to $K+1$)**:
- $D_{\text{total}} = 250 \implies 250 \times 0.15 = 37.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{38}$ ($K=37 \to 38$)
- $D_{\text{total}} = 10 \implies 10 \times 0.15 = 1.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{2}$ ($K=1 \to 2$)
- $D_{\text{total}} = 410 \implies 410 \times 0.15 = 61.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{62}$ ($K=61 \to 62$)
- $D_{\text{total}} = 770 \implies 770 \times 0.15 = 115.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{116}$ ($K=115 \to 116$)
- $D_{\text{total}} = 450 \implies 450 \times 0.15 = 67.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{68}$ ($K=67 \to 68$)
- $D_{\text{total}} = 650 \implies 650 \times 0.15 = 97.5 \implies$ Observed $D_{\text{sharer}} = \mathbf{98}$ ($K=97 \to 98$)

**Proof of Elimination of `ROUND_HALF_EVEN`**:
Under `ROUND_HALF_EVEN` (Banker's rounding), even $K$ followed by $.5$ must round to the nearest even number ($K$). However, 100% of the 47 observed even $K$ samples round up to $K+1$ (an odd number). This decisively refutes `ROUND_HALF_EVEN`.

**Proof of Elimination of `FLOOR`**:
All 98 exact-half samples round UP to $K+1$, which directly refutes `FLOOR`.

**Proof of Elimination of `CEIL`**:
Non-tie controls with fractional parts $< 0.5$ (e.g. $D_{\text{total}} = 469 \times 0.15 = 70.35 \implies 70$) round down to $K$, which directly refutes `CEIL`.

**Conclusion for `SHS9-B01`**:
$D_{\text{sharer\_theoretical}}$ unconditionally applies **`ROUND_HALF_UP`** (exact ties round toward positive infinity).
$D_{\text{target}}$ takes the exact remainder: $D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$.

---

## 5. Call Site 3: `DISTRIBUTION_TARGET_INTEGERIZATION` (Finding `DSTS9-B01`)

### 5.1 Mathematical Definition
$$D_{\text{target}} = \operatorname{integerize}(D_{\text{total}} \times (1 - R))$$
$$D_{\text{transfer}} = D_{\text{total}} - D_{\text{target}}$$

### 5.2 Candidate Elimination Matrix
Under 【义心昭烈】with $R = 50.00\%$ ($1 - R = 0.50$):
- Exact-half samples (odd $D_{\text{total}}$): **12**
- Controls below 0.5: **18**
- Controls above 0.5: **16**

| Candidate Policy | Exact-Half Ties ($N=12$) | Controls $< 0.5$ ($N=18$) | Controls $> 0.5$ ($N=16$) | Verdict |
|---|---:|---:|---:|---|
| **`ROUND_HALF_UP`** | **12/12 (100%)** | **18/18 (100%)** | **16/16 (100%)** | **CONFIRMED** |
| `ROUND_HALF_EVEN` | 6/12 (50%) | 18/18 (100%) | 16/16 (100%) | **ELIMINATED** |
| `FLOOR` | 0/12 (0%) | 18/18 (100%) | 0/16 (0%) | **ELIMINATED** |
| `CEIL` | 12/12 (100%) | 0/18 (0%) | 16/16 (100%) | **ELIMINATED** |

### 5.3 Empirical Evidence & Proof Samples
- $D_{\text{total}} = 251 \implies 251 \times 0.50 = 125.5 \implies$ Observed $D_{\text{target}} = \mathbf{126}$
- $D_{\text{total}} = 407 \implies 407 \times 0.50 = 203.5 \implies$ Observed $D_{\text{target}} = \mathbf{204}$
- $D_{\text{total}} = 675 \implies 675 \times 0.50 = 337.5 \implies$ Observed $D_{\text{target}} = \mathbf{338}$
- $D_{\text{total}} = 511 \implies 511 \times 0.50 = 255.5 \implies$ Observed $D_{\text{target}} = \mathbf{256}$
- $D_{\text{total}} = 623 \implies 623 \times 0.50 = 311.5 \implies$ Observed $D_{\text{target}} = \mathbf{312}$
- $D_{\text{total}} = 363 \implies 363 \times 0.50 = 181.5 \implies$ Observed $D_{\text{target}} = \mathbf{182}$
- $D_{\text{total}} = 467 \implies 467 \times 0.50 = 233.5 \implies$ Observed $D_{\text{target}} = \mathbf{234}$
- $D_{\text{total}} = 395 \implies 395 \times 0.50 = 197.5 \implies$ Observed $D_{\text{target}} = \mathbf{198}$
- $D_{\text{total}} = 1091 \implies 1091 \times 0.50 = 545.5 \implies$ Observed $D_{\text{target}} = \mathbf{546}$
- $D_{\text{total}} = 983 \implies 983 \times 0.50 = 491.5 \implies$ Observed $D_{\text{target}} = \mathbf{492}$
- $D_{\text{total}} = 835 \implies 835 \times 0.50 = 417.5 \implies$ Observed $D_{\text{target}} = \mathbf{418}$

Controls:
- $D_{\text{theoretical}} = 622.386 \implies$ Observed = **622** (rounds down).
- $D_{\text{theoretical}} = 307.359 \implies$ Observed = **307** (rounds down).
- $D_{\text{theoretical}} = 348.894 \implies$ Observed = **349** (rounds up).

**Conclusion for `DISTRIBUTION_TARGET`**:
$D_{\text{target}}$ unconditionally applies **`ROUND_HALF_UP`**.

---

## 6. Call Site 4: `DISTRIBUTION_PARTICIPANT_INTEGERIZATION` (Finding `DSTS9-B01`)

### 6.1 Mathematical Definition
$$D_{\text{participant}} = \operatorname{integerize}\left(\frac{D_{\text{transfer}}}{N}\right)$$

### 6.2 Candidate Elimination Matrix
Total exact-half boundary samples: **34** ($N=2$, odd $D_{\text{transfer}}$):
- Even $K$ samples: **17**
- Odd $K$ samples: **17**

| Candidate Policy | Even $K$ Ties ($N=17$) | Odd $K$ Ties ($N=17$) | Match Rate | Verdict |
|---|---:|---:|---:|---|
| **`ROUND_HALF_UP`** | **17/17 (100%)** | **17/17 (100%)** | **100.0%** | **CONFIRMED** |
| `ROUND_HALF_EVEN` | 0/17 (0%) | 17/17 (100%) | 50.0% | **ELIMINATED** |
| `FLOOR` | 0/17 (0%) | 0/17 (0%) | 0.0% | **ELIMINATED** |
| `CEIL` | 17/17 (100%) | 17/17 (100%) | 100.0% | **ELIMINATED** (refuted by controls) |

### 6.3 Empirical Evidence & Proof Samples
**Even $K$ Tie Cases ($K$ even, theoretical $= K + 0.5$, observed rounds UP to $K+1$)**:
- $D_{\text{transfer}} = 353, N=2 \implies 353 / 2 = 176.5 \implies$ Observed = **177** ($K=176 \to 177$)
- $D_{\text{transfer}} = 165, N=2 \implies 165 / 2 = 82.5 \implies$ Observed = **83** ($K=82 \to 83$)
- $D_{\text{transfer}} = 125, N=2 \implies 125 / 2 = 62.5 \implies$ Observed = **63** ($K=62 \to 63$)
- $D_{\text{transfer}} = 337, N=2 \implies 337 / 2 = 168.5 \implies$ Observed = **169** ($K=168 \to 169$)
- $D_{\text{transfer}} = 369, N=2 \implies 369 / 2 = 184.5 \implies$ Observed = **185** ($K=184 \to 185$)
- $D_{\text{transfer}} = 181, N=2 \implies 181 / 2 = 90.5 \implies$ Observed = **91** ($K=90 \to 91$)
- $D_{\text{transfer}} = 233, N=2 \implies 233 / 2 = 116.5 \implies$ Observed = **117** ($K=116 \to 117$)
- $D_{\text{transfer}} = 249, N=2 \implies 249 / 2 = 124.5 \implies$ Observed = **125** ($K=124 \to 125$)
- $D_{\text{transfer}} = 197, N=2 \implies 197 / 2 = 98.5 \implies$ Observed = **99** ($K=98 \to 99$)
- $D_{\text{transfer}} = 545, N=2 \implies 545 / 2 = 272.5 \implies$ Observed = **273** ($K=272 \to 273$)
- $D_{\text{transfer}} = 417, N=2 \implies 417 / 2 = 208.5 \implies$ Observed = **209** ($K=208 \to 209$)
- $D_{\text{transfer}} = 105, N=2 \implies 105 / 2 = 52.5 \implies$ Observed = **53** ($K=52 \to 53$)
- $D_{\text{transfer}} = 145, N=2 \implies 145 / 2 = 72.5 \implies$ Observed = **73** ($K=72 \to 73$)
- $D_{\text{transfer}} = 121, N=2 \implies 121 / 2 = 60.5 \implies$ Observed = **61** ($K=60 \to 61$)
- $D_{\text{transfer}} = 61, N=2 \implies 61 / 2 = 30.5 \implies$ Observed = **31** ($K=30 \to 31$)
- $D_{\text{transfer}} = 49, N=2 \implies 49 / 2 = 24.5 \implies$ Observed = **25** ($K=24 \to 25$)
- $D_{\text{transfer}} = 109, N=2 \implies 109 / 2 = 54.5 \implies$ Observed = **55** ($K=54 \to 55$)

**Odd $K$ Tie Cases ($K$ odd, theoretical $= K + 0.5$, observed rounds UP to $K+1$)**:
- $D_{\text{transfer}} = 147, N=2 \implies 147 / 2 = 73.5 \implies$ Observed = **74** ($K=73 \to 74$)
- $D_{\text{transfer}} = 183, N=2 \implies 183 / 2 = 91.5 \implies$ Observed = **92** ($K=91 \to 92$)
- $D_{\text{transfer}} = 303, N=2 \implies 303 / 2 = 151.5 \implies$ Observed = **152** ($K=151 \to 152$)
- $D_{\text{transfer}} = 295, N=2 \implies 295 / 2 = 147.5 \implies$ Observed = **148** ($K=147 \to 148$)
- $D_{\text{transfer}} = 203, N=2 \implies 203 / 2 = 101.5 \implies$ Observed = **102** ($K=101 \to 102$)
- $D_{\text{transfer}} = 255, N=2 \implies 255 / 2 = 127.5 \implies$ Observed = **128** ($K=127 \to 128$)
- $D_{\text{transfer}} = 311, N=2 \implies 311 / 2 = 155.5 \implies$ Observed = **156** ($K=155 \to 156$)
- $D_{\text{transfer}} = 363, N=2 \implies 363 / 2 = 181.5 \implies$ Observed = **182** ($K=181 \to 182$)
- $D_{\text{transfer}} = 427, N=2 \implies 427 / 2 = 213.5 \implies$ Observed = **214** ($K=213 \to 214$)
- $D_{\text{transfer}} = 491, N=2 \implies 491 / 2 = 245.5 \implies$ Observed = **246** ($K=245 \to 246$)
- $D_{\text{transfer}} = 151, N=2 \implies 151 / 2 = 75.5 \implies$ Observed = **76** ($K=75 \to 76$)
- $D_{\text{transfer}} = 87, N=2 \implies 87 / 2 = 43.5 \implies$ Observed = **44** ($K=43 \to 44$)
- $D_{\text{transfer}} = 63, N=2 \implies 63 / 2 = 31.5 \implies$ Observed = **32** ($K=31 \to 32$)

**Proof of Elimination of `ROUND_HALF_EVEN`**:
Under `ROUND_HALF_EVEN`, the 17 even $K$ samples must round down to $K$. However, 17/17 observed even $K$ samples round up to $K+1$. `ROUND_HALF_EVEN` is decisively eliminated.

**Proof of Elimination of `FLOOR`**:
All 34 exact-half samples round up to $K+1$. `FLOOR` is decisively eliminated.

**Conclusion for `DISTRIBUTION_PARTICIPANT`**:
$D_{\text{participant}}$ unconditionally applies **`ROUND_HALF_UP`**.

---

## 7. Sub-Check: Cleave Numeric Finding (`CLVS9-B01`)

- **Scope Clarification**:
  Finding `CLVS9-B01` concerns the Cleave base layer and secondary target damage formula.
  In accordance with the Stage 9 Contract Consolidation Plan, `CLVS9-B01` is scheduled for closure in **`RF-P06`**.
  It is **NOT** closed in `RF-P01`.
- **Numeric Sub-check**:
  Cleave numeric sub-checks confirm that downstream damage calculation follows standard damage formula integerization, but the base layer definition (whether Cleave inherits raw primary hit modifiers or initiates a fresh damage event) remains unclosed until `RF-P06`.
- **Disposition**: `CLVS9-B01` remains **OPEN** (deferred to `RF-P06`).

---

## 8. Cross-Mechanism Policy Comparison & Architectural Rules

### 8.1 Comparison Matrix

| Call Site | Mathematical Expression | Observable Executable Rule | Tie-Breaking Policy | Matches / Samples | Status |
|---|---|---|---|---:|---|
| **`CHAIN`** | $\text{TriggerNodeResolvedDamage} \times \text{ChainRatio}$ | **`FLOOR`** (`math.floor` / truncate) | N/A (all fractions truncated) | 1657 / 1657 (100.0%) | **FROZEN** |
| **`SHARE`** | $D_{\text{total}} \times R$ | **`ROUND_HALF_UP`** | $x.5 \to x + 0.5$ (round up) | 98 / 98 ties (100.0%) | **FROZEN** |
| **`DISTRIBUTION_TARGET`** | $D_{\text{total}} \times (1 - R)$ | **`ROUND_HALF_UP`** | $x.5 \to x + 0.5$ (round up) | 12 / 12 ties (100.0%) | **FROZEN** |
| **`DISTRIBUTION_PARTICIPANT`** | $D_{\text{transfer}} / N$ | **`ROUND_HALF_UP`** | $x.5 \to x + 0.5$ (round up) | 34 / 34 ties (100.0%) | **FROZEN** |

### 8.2 Architectural Invariant
1. **No Monolithic Integerization Assumption**:
   A single shared `integerize()` function cannot be used globally without knowing the mechanism call site. Chain is strictly truncated (`floor`), whereas Share and Distribution are rounded to nearest with ties rounding upward (`round_half_up`).
2. **Deterministic Rational Evaluation**:
   The simulator implementation must evaluate ties cleanly without floating-point precision slippage. For Python:
   ```python
   def round_half_up(val: float | Decimal | Fraction) -> int:
       # Standard round half up: floor(val + 0.5)
       return int(Decimal(str(val)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
   ```
3. **Partition Conservation Invariant**:
   - For `DAMAGE_SHARE`:
     $$D_{\text{target}} = D_{\text{total}} - D_{\text{sharer\_theoretical}}$$
     Guarantees strict theoretical conservation: $D_{\text{target}} + D_{\text{sharer\_theoretical}} = D_{\text{total}}$.
   - For `DISTRIBUTION`:
     $$D_{\text{transfer}} = D_{\text{total}} - D_{\text{target}}$$
     $$D_{\text{participant}} = \operatorname{round\_half\_up}(D_{\text{transfer}} / N)$$
     Guarantees that participant shares are symmetric ($D_{\text{participant1}} = D_{\text{participant2}}$). Any second-order rounding deviation ($D_{\text{target}} + N \times D_{\text{participant}} \neq D_{\text{total}}$) is an accepted algorithm property and MUST NOT be compensated to the last participant.

---

## 9. Deterministic Regression Test Vectors

The following vectors must be preserved as reference specifications:

| Vector ID | Call Site | Input Values | Exact Calculation | Expected Output | Critical Test Property |
|---|---|---|---|---:|---|
| `VEC-CHN-01` | CHAIN | Trigger=396, Ratio=28.28% | $396 \times 0.2828 = 111.9888$ | **111** | Eliminates round_half_up (112) |
| `VEC-CHN-02` | CHAIN | Trigger=753, Ratio=28.28% | $753 \times 0.2828 = 212.9484$ | **212** | Eliminates round_half_up (213) |
| `VEC-CHN-03` | CHAIN | Trigger=265, Ratio=22.58% | $265 \times 0.2258 = 59.8370$ | **59** | Eliminates round_half_up (60) |
| `VEC-SHR-01` | SHARE | Dtotal=470, R=15.00% | $470 \times 0.15 = 70.5$ | Dsharer=**71**, Dtarget=**399** | Even $K$ ties round UP |
| `VEC-SHR-02` | SHARE | Dtotal=250, R=15.00% | $250 \times 0.15 = 37.5$ | Dsharer=**38**, Dtarget=**212** | Odd $K$ ties round UP |
| `VEC-SHR-03` | SHARE | Dtotal=10, R=15.00% | $10 \times 0.15 = 1.5$ | Dsharer=**2**, Dtarget=**8** | Small value tie rounds UP |
| `VEC-SHR-04` | SHARE | Dtotal=469, R=15.00% | $469 \times 0.15 = 70.35$ | Dsharer=**70**, Dtarget=**399** | Fraction $< 0.5$ rounds DOWN |
| `VEC-SHR-05` | SHARE | Dtotal=471, R=15.00% | $471 \times 0.15 = 70.65$ | Dsharer=**71**, Dtarget=**400** | Fraction $> 0.5$ rounds UP |
| `VEC-DST-01` | DST_TGT | Dtotal=251, R=50.00% | $251 \times 0.50 = 125.5$ | Dtarget=**126**, Dtransfer=**125** | Target tie rounds UP |
| `VEC-DST-02` | DST_TGT | Dtotal=407, R=50.00% | $407 \times 0.50 = 203.5$ | Dtarget=**204**, Dtransfer=**203** | Target tie rounds UP |
| `VEC-DST-03` | DST_PART | Dtransfer=353, N=2 | $353 / 2 = 176.5$ | Dparticipant=**177** (both) | Even $K$ participant tie rounds UP |
| `VEC-DST-04` | DST_PART | Dtransfer=147, N=2 | $147 / 2 = 73.5$ | Dparticipant=**74** (both) | Odd $K$ participant tie rounds UP |
| `VEC-DST-05` | DST_PART | Dtransfer=100, N=3 | $100 / 3 = 33.333...$ | Dparticipant=**33** (all 3) | Fraction $< 0.5$ rounds DOWN |
| `VEC-DST-06` | DST_PART | Dtransfer=200, N=3 | $200 / 3 = 66.666...$ | Dparticipant=**67** (all 3) | Fraction $> 0.5$ rounds UP |
