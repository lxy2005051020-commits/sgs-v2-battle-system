# Stage 8 Evidence Matrix

> Repository: `lxy2005051020-commits/sgs-v2-battle-system`
>
> Purpose: Stage 8 production mapping gate for Damage Prevention / Hit Resolution / Formula Policy / Damage Modifier rules.
>
> Verdict is restricted to `PASS_STAGE8` or `DEFER`.
>
> A `DEFER` row does not block synthetic infrastructure tests. It blocks official production mapping for that state.

## Evidence baseline

Stage 8 v1 design commit:

```text
98b23726ab1d28e4c378e998314a4abe1a39e5b7
```

Frozen implementation baseline used by the first independent design audit:

```text
8f51a9ebd06038ec163e858164bc26e8a7637ed2
```

Official static text source:

```text
repository: lxy2005051020-commits/sgs-v2-battle-system
commit: 98b23726ab1d28e4c378e998314a4abe1a39e5b7
path: sgs_v2/battle_core/official_state_catalog.py
```

Existing weakness behavior source:

```text
repository: lxy2005051020-commits/sgs-v2-battle-system
commit: 98b23726ab1d28e4c378e998314a4abe1a39e5b7
paths:
- sgs_v2/battle_core/damage_system.py
- tests/test_stage4_states.py
```

External research repository references must be recorded as `repository + commit SHA + file path` when actual evidence is used. No Stage 8 state is allowed to cite “previous chat”, recollection, or an unpinned branch as evidence.

## Matrix

| state_id | official text | evidence level / source | rule family | DamageType scope | DamageSourceType scope | runtime params | probability | stacking | consumption | prevention / hit semantics | formula policy | modifier phase / kind | precedence | rounding | RNG | provenance | remaining unknowns | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `weakness` | 控制状态，无法造成伤害 | A: official catalog; existing production regression in `damage_system.py` + `tests/test_stage4_states.py` at pinned battle-repo commit | PREVENTION | Existing behavior applies before formula; no new expansion claimed | Existing DamageRequest behavior only; no new source-type expansion claimed | Existing state params unchanged | N/A | Deterministic presence check; multiple-instance decisive-instance selection is engineering trace only | No consumption in frozen behavior | Source cannot continue into hit/formula; returns compatible prevented damage result | NORMAL not reached | N/A | Before HIT | N/A | No RNG consumed | Exact weakness StateInstance must be traceable after migration | Architecture migration must preserve every Stage 4 observable; do not infer new official scope | `PASS_STAGE8` |
| `evasion` | 功能性增益状态，可回避伤害，规避几率为非线性叠加 | A: official catalog only | HIT | UNKNOWN | UNKNOWN | UNKNOWN | Probability exists, exact source/normalization UNKNOWN | Official text explicitly says nonlinear stacking; formula UNKNOWN | UNKNOWN | Can avoid damage, exact multi-instance adjudication UNKNOWN | N/A | N/A | Interaction order with barrier / sure_hit / other hit rules not fully evidenced | UNKNOWN | Exact roll/aggregation order UNKNOWN | Multi-instance contributors must be representable | Nonlinear aggregation, instance interaction, source-type scope, consumption | `DEFER` |
| `barrier` | 功能性增益状态，可免疫伤害 | A: official catalog only | HIT | UNKNOWN | UNKNOWN | UNKNOWN | N/A or UNKNOWN if any probabilistic variant exists | Multi-instance semantics UNKNOWN | Consumption / charges UNKNOWN | Damage immunity concept known; exact resource semantics UNKNOWN | N/A | N/A | Interaction with evasion / sure_hit known only partially from sure_hit text | UNKNOWN | No RNG assumed only for synthetic infrastructure, not claimed official | Contributor(s) must be traceable | Charges, timing, multiple instances, exact priority | `DEFER` |
| `sure_hit` | 功能性增益状态，发动战法及普通攻击命中目标时无视规避及抵御 | A: official catalog only | HIT bypass policy | Text supports bypass of evasion/barrier for relevant damage, full DamageType scope still evidence-gated | Text names skill + normal attack; mapping to current enum and edge sources requires evidence | UNKNOWN | N/A | Multi-instance semantics likely irrelevant but not formally evidenced | UNKNOWN | May bypass evasion and barrier; must not bypass weakness or arbitrary prevention | N/A | N/A | Exact precedence with multiple hit rules requires Matrix confirmation | N/A | Bypassed evasion must not consume synthetic evasion RNG; official client RNG order UNKNOWN | Source instance must be traceable | Exact `DamageSourceType` mapping, edge interactions, consumption | `DEFER` |
| `defense_pierce` | 功能性增益状态，造成伤害时无视目标统率及智力 | A: official catalog only | FORMULA_POLICY | Text suggests weapon/strategy relevant defensive attribute, but production scope still gated | UNKNOWN | Likely no numeric params for full ignore; exact state runtime contract not yet frozen | N/A | Multiple instances semantics UNKNOWN | UNKNOWN | N/A | Candidate `IGNORE_RELEVANT_TARGET_DEFENSE` | N/A | Must occur before frozen base formula | Existing frozen formula rounding preserved | No extra RNG; base-formula RNG position must remain unchanged | Source instance must be traceable | DamageSourceType scope, interaction with other attribute rules, multiple instances | `DEFER` |
| `vigilance` | 功能性增益状态，可减少单次受到的伤害 | A: official catalog only | MODIFIER | UNKNOWN | UNKNOWN | UNKNOWN | N/A unless state application supplies probabilistic activation | UNKNOWN | Charge / count / removal UNKNOWN | N/A | NORMAL | `SINGLE_HIT_ADJUSTMENT` candidate | Exact order vs incoming reduction / pierce UNKNOWN | UNKNOWN | UNKNOWN | Owner/applier/instance must be traceable | Fixed vs percent, magnitude, charge consumption, zero/prevented interaction, stacking | `DEFER` |
| `critical` | 有概率造成双倍兵刃伤害 | A: official catalog only | MODIFIER | WEAPON only supported by text | UNKNOWN | Probability param/source UNKNOWN | Probability exists; exact source + multi-source combination UNKNOWN | Multiple critical sources UNKNOWN | UNKNOWN | N/A | NORMAL | `CRITICAL_MULTIPLIER`, factor 2.0 | Stage 8 phase order is D engineering only | Frozen finalization remains after modifier | Wrong DamageType must not roll; exact official RNG stream order UNKNOWN | Contributor instance must be traceable | Probability source, stacking/selection, source-type scope | `DEFER` |
| `strategy_critical` | 有概率造成双倍谋略伤害 | A: official catalog only | MODIFIER | STRATEGY only supported by text | UNKNOWN | Probability param/source UNKNOWN | Probability exists; exact source + multi-source combination UNKNOWN | Multiple sources UNKNOWN | UNKNOWN | N/A | NORMAL | `CRITICAL_MULTIPLIER`, factor 2.0 | Stage 8 phase order is D engineering only | Frozen finalization remains after modifier | Wrong DamageType must not roll; exact official RNG stream order UNKNOWN | Contributor instance must be traceable | Probability source, stacking/selection, source-type scope | `DEFER` |
| `damage_reduction_pierce` | 造成伤害时无视目标一定比例的受到伤害降低效果 | A: official catalog only | MODIFIER transform | UNKNOWN | UNKNOWN | Pierce-rate params UNKNOWN | N/A | Multiple pierce sources UNKNOWN | UNKNOWN | N/A | Must not affect formula defense | May transform only `INCOMING_REDUCTION` effective operand | Unknown whether per-contribution or aggregate | UNKNOWN | No RNG indicated by text; do not claim official absence beyond evidence | Pierce source and affected reduction contributors must both be traceable | Reduction aggregation, pierce aggregation, order, cap, rounding | `DEFER` |
| `rebellion` | 持续性状态，每回合对武将部队造成伤害，无视防御 | A: official catalog only | PERIODIC DAMAGE + FORMULA_POLICY | DamageType UNKNOWN | CONTINUOUS candidate, exact current enum mapping and trigger origin requires evidence | Damage coefficient/base reference UNKNOWN | UNKNOWN | Multiple instances UNKNOWN | Duration/refresh handled elsewhere; exact trigger semantics still evidence-gated | Periodic damage exists; exact trigger and source lifecycle unresolved in evidence | Candidate ignore relevant defensive contribution | N/A unless other modifier evidence emerges | Trigger/order with lifecycle UNKNOWN | Base/reference rounding UNKNOWN | RNG depends on eventual base-damage reference; UNKNOWN | State owner/applier/instance must be preserved in DamageRequest provenance | Damage type, base damage reference, coefficient, trigger timing, source attribution/lifecycle | `DEFER` |

## Hard gate

A row may change from `DEFER` to `PASS_STAGE8` only when every behavior that materially changes production results is supported by pinned evidence and the corresponding runtime/test contract is specified.

The following do **not** count as evidence:

```text
synthetic modifier behavior
deterministic instance ordering chosen for engineering
an unpinned `main` branch
chat recollection
"this is probably how the game works"
```

Synthetic rules may validate infrastructure while every official row except the existing `weakness` migration remains `DEFER`.
