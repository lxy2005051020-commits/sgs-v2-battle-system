# Stage13-B2.5 Full Damage Advancement Question Ledger

Status: AUTHORITATIVE / B2.5 AUDITED
Effective: 2026-09-29
Parent authority: STAGE13_FULL_DAMAGE_ADVANCEMENT_HIDDEN_MECHANISM_RESEARCH_ROUTE.md
Corpus base: 34,755 Battle Reports (`d:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`)
Replayed sample: 3,500 battles, 84,673 clean damage events

## 1. Authoritative Question Ledger

| ID | Research Question | Final B2.5 Verdict | Empirical Evidence & Mathematical Rationale | Runtime Action |
| --- | --- | --- | --- | --- |
| **A-Q1** | Is $E_{out}$ (attacker advancement) in the ordinary outgoing pool or an independent multiplier? | **METHOD_GATE** | Across 84,673 replayed events, Same-Pool and Independent Multiplier legal prediction sets are completely identical in **96.31%** (81,554) of events. In PVP battles, SP won in 677 cases and IND won in 643 cases, with error delta $\le 1$ damage. Models are **OBSERVATIONALLY EQUIVALENT** within the discrete RNG $R \in [86..94]$ band. | Retain canonical default `same_pool` in runtime engine (`damage_system.py`). Document equivalence. |
| **A-Q2** | Is $E_{in}$ (target advancement) in the ordinary incoming pool or an independent multiplier? | **METHOD_GATE** | Same mathematical observational equivalence. Across 84,673 replayed events, legal intervals $[0.86 F_{in}, 0.94 F_{in}]$ overlap completely in over 96% of cases. Non-discriminating within integer boundary. | Retain canonical default `same_pool` in runtime engine (`damage_system.py`). Document equivalence. |
| **A-Q3** | Does $E_{out}$ participate in the $-90\%$ same-side outgoing modifier floor? | **CLOSED-INHERITED** | Stage13-B2 Q46 contract verified. Outgoing net modifier accumulator $A_{out} = \max(-0.90, OI + E_{out} - OD)$ holds across extreme debuff events. No counterexample exceeding $-90\%$ floor. | Enforce `max(-0.90, ...)` outgoing floor. |
| **A-Q4** | Does $E_{in}$ participate in the $-90\%$ same-side incoming modifier floor? | **CLOSED-INHERITED** | Stage13-B2 Q46 contract verified. Incoming net modifier accumulator $A_{in} = \max(-0.90, II - ID - E_{in})$ holds. No counterexample exceeding $-90\%$ floor. | Enforce `max(-0.90, ...)` incoming floor. |
| **A-Q5** | How does $E_{out}$ compose with critical / strategy-critical damage? | **CLOSED-INHERITED** | Stage13-B2 Q47 contract verified. Critical hit operates as an additive injection to the output modifier pool: $F_{out} = 1.0 + A_{out} + \text{CritBonus}$. Full replay of 1,230 critical events confirms additive pool alignment. | Maintain additive critical bonus in output multiplier. |
| **A-Q6** | How does incoming advancement $E_{in}$ interact on critical strikes? | **CLOSED** | Replay confirms cross-side multiplication $F_{out} \times F_{in}$. Target advancement reduces incoming critical damage multiplicatively through the target pool $F_{in}$. | Retain cross-side multiplication. |
| **A-Q7** | How does advancement compose with DOT (Continuous Damage) snapshots? | **CLOSED-INHERITED** | Stage13-B2 Q48 verified. DOT snapshots attacker force/intelligence, $E_{out}$, and outgoing modifiers at application time $t_0$, while taking target incoming modifiers dynamically at tick settlement time. | Maintain $t_0$ snapshot architecture in runtime. |
| **A-Q8** | How does advancement compose with delayed / deferred damage families? | **PARTIAL** | Immediate delayed triggers snapshot attacker attributes and advancement at prep/cast time; deferred settlement ticks evaluate target defensive modifiers at hit resolution. | Retain existing phase separation. |
| **A-Q9** | What is the relative position of advancement and discrete RNG $R \in [86..94]$? | **METHOD_GATE** | Under scalar multiplication, $B_0 \times \text{coef} \times \text{restr} \times \text{morale} \times \text{rng} \times F_{out} \times F_{in}$ is commutative. Integer boundary differences between pre-RNG and post-RNG placement are within $\pm 1$ damage. | Implement continuous multiplication before final integerization. |
| **A-Q10** | What is the relationship between advancement and integerization (CEIL vs FLOOR)? | **METHOD_GATE** | Stage13-B2 rejected per-phase repeated CEIL as an absolute global rule. In B2.5 replay, Legacy V1 (repeated ceil) achieves exact match on 14,620 events, while Continuous Floor achieves exact match on 12,850 events. Both remain legal candidate prediction bounds. | Retain candidate interval $[ \lfloor \cdot \rfloor, \lceil \cdot \rceil ]$ in research verifier. |
| **A-Q11** | Do Weapon damage and Strategy damage share the same advancement topology? | **CLOSED** | Both channels share identical military book advancement scaling ($+2\%$ per star for $E_{out}$, $-2\%$ per star for $E_{in}$), same-side additive pooling, and cross-side multiplication. | Share unified advancement logic in `DamageSystem`. |
| **A-Q12** | Do Normal, Active, Assault, Command, and Passive damage share the same topology? | **CLOSED** | Confirmed across 83,087 normal attacks, 1,418 active weapon strikes, and 168 active strategy skills in the replay dataset. All attack families route through identical $F_{out} \times F_{in}$ modifier channels. | Unified pipeline confirmed. |

## 2. Methodology & Closure Rules Applied

1. **Anti-Hallucination Discipline**: No question is marked `CLOSED` without positive discriminating empirical evidence. Questions where two candidate models fall within the overlapping legal discrete RNG interval are strictly classified as **`METHOD_GATE`**.
2. **Canonical Engineering Default**: For `METHOD_GATE` questions (A-Q1, A-Q2, A-Q9, A-Q10), the system preserves the inherited Stage13-B2 canonical implementation (`same_pool`, continuous multiplication with final integerization) to ensure system stability and zero runtime disruption.
3. **Traceability**: All conclusions are backed by the 84,673 events in `STAGE13_FULL_DAMAGE_REPLAY_OUTPUT.csv` and residual tracking in `STAGE13_FULL_DAMAGE_RESIDUAL_LEDGER.csv`.
