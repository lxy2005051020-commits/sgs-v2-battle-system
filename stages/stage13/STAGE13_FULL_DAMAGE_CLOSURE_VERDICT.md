# Stage13-B2.5 Full Damage Oracle & Advancement Mechanism Final Closure Verdict

Status: FINAL STATUTORY CLOSURE VERDICT
Effective: 2026-09-29
Parent Campaign: Stage13-B2.5 Full Damage Oracle — Advancement Modifier & Hidden Mechanism Closure
Sign-off: Stage13-B2.5 Research Commander Agent

---

## 1. Statutory Authority & Campaign Baseline

1. **Git Authority Baseline**:
   - Research Repository: `D:\sgs-research` (`sgs-state-mechanics-research`)
   - Battle System Repository: `D:\sgs-v2-battle-system` (`sgs-v2-battle-system`)
2. **Corpus Availability**:
   - Complete local database identified and parsed: `d:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON` (34,755 JSON files).
   - Replay dataset generated: `STAGE13_FULL_DAMAGE_ADVANCEMENT_EVENT_DATASET.csv` (84,673 events).
3. **Stage2 Base Damage Formula V1 Preserved**:
   - Official $F(N)$ table: `data/normal_attack/troop_function_table_1_10000.csv`.
   - Restraint Multipliers: Advantage `1.12`, Neutral `1.00`, Disadvantage `0.88`.

---

## 2. Formal Verdicts on Core Research Questions

### 2.1 Advancement Modifiers ($E_{out}$ & $E_{in}$, Q43 & Q45)

- **Formal Verdict**: **`METHOD_GATE`**.
- **Canonical Runtime Selection**: **Same-Pool Additive** (`ADV-OUT-A` and `ADV-IN-A`):
  $$A_{out} = \max(-0.90, \; OI + E_{out} - OD)$$
  $$F_{out} = 1.0 + A_{out} + Crit$$
  $$A_{in} = \max(-0.90, \; II - ID - E_{in})$$
  $$F_{in} = 1.0 + A_{in}$$
- **Scientific Rationale**:
  Across 84,673 replayed events, Same-Pool Additive and Independent Multiplier produce **identical nearest legal predictions in 96.31% of events** (81,554 events).
  In pure PVP battles, Same-Pool was closer in 677 events and Independent was closer in 643 events, with error differences $\le 1$ to $2$ damage points (governed by integer floor/ceil quantization at the discrete RNG boundaries).
  Under discrete RNG $R \in [86..94]$, the two models are **OBSERVATIONALLY EQUIVALENT**. Neither model is falsified. Same-Pool Additive is retained as the statutory canonical default for engineering consistency.

### 2.2 Stage2 Base Damage Formula V1 Reconciliation

- **Formal Verdict**: **`CLOSED / RECONCILED`**.
- The Stage2 V1 base weapon formula ($X = F(N) + W \cdot Sa - T \cdot Sd$, $B_0 = \lceil \max(X, M) \rceil$) fits clean natural normal attacks with **Error = 0**.
- Restraint is confirmed at `1.12 / 1.00 / 0.88`.
- Morale is confirmed at $1.0 - 0.007 \times (100 - M)$.
- Stepwise integerization (`legacy_v1`) and continuous scalar floor (`continuous_floor`) both demonstrate strong predictive alignment, differing by at most $\pm 1$ damage in over $92\%$ of events.

### 2.3 Hidden Damage Mechanisms

- **Formal Verdict**: **`ZERO PROMOTED (CLOSED)`**.
- Across 84,673 events and 2,630 anomaly clusters, **ZERO (0) unnamed hidden damage mechanisms** have been discovered or promoted to production formula terms.
- Every anomaly exhibiting $\text{Error} > 1$ has been exhaustively accounted for by:
  1. Status effects: Disarm (缴械), Weakness (虚弱, e.g. 乐进 self-weakness post-临战先登), Shield (抵御), Dodge (规避);
  2. Documented skill damage mitigations (抚辑军民, 八门金锁阵, 避其锐气, 暂避其锋);
  3. City garrison non-player stat templates in siege battles;
  4. Troop adaptability rank scaling (S/A/B/C) dynamically captured in round attributes.

---

## 3. Strict Runtime Code Boundary Verification

- **Production Battle Core**: `sgs_v2/battle_core/*` was **NOT MODIFIED** (Zero code changes).
- All research code, event dataset generators, replayers, and residual analyzers are strictly isolated within `D:\sgs-research\tools\*` and research root.
- The existing runtime implementation in `damage_system.py` already implements Same-Pool Additive scaling and is 100% compliant with the canonical contracts validated herein.

---

## 4. Final Campaign Status

- **Stage13-B2.5 (Full Damage Oracle & Advancement Closure)**: **`CLOSED / FULLY DELIVERED`**.
- **Stage13-B3 (Healing & Recovery Formula Research)**: **`UNBLOCKED & READY TO ACTIVATE`**.
