# Stage12 · 690108 PROVOCATION Research Authority Sync

> Sync Date: **2026-09-26**
>
> Battle Runtime Status: **NOT_INTEGRATED**
>
> Research Status: **FROZEN**
>
> Stage12 Production Active: **NO**
>
> Purpose: mirror the frozen research authority into the Battle repository without treating Research Freeze as Runtime completion.

## 1. Research authority

Repository:
`lxy2005051020-commits/sgs-state-mechanics-research`

Canonical path:
`states/control/provocation/MECHANISM_CONTRACT.md`

Frozen contract:
`v1.0-frozen`

Authority pins:

```text
Contract commit                    = 5c1382c76bb49bb09444cef807dd758a8a1838b2
Contract blob                      = 8c93111a6dedaeb84148a3f387b04d16788d74e6
Question ledger commit             = bb0e4ad31622be608aa3b95ff7bd7b7496e8f5b2
Question ledger blob               = 574cc0e478235bf37fece0708a7d147bc731e0d4
Falsification audit commit         = 45534501f072f892f17d5543d678efe734daa882
Falsification audit blob           = 8dff98eac5c54545b87412702c0f0cdec5172da3
Final freeze audit commit          = 78583a902cf7dd27af929796613e85aebe336d82
Final freeze audit blob            = 1e3f9cce51202c82afe11daf0a84f28e74ebcb37
Freeze record commit               = 91a116a2660bfa16ca1bdf1d7515951a7219bf4d
Freeze record blob                 = 8d61d0ee1601c1c404f9456d37a117ae65e7a1dd
Research completion matrix commit  = 843cfeb63ce40b112260a85ad6d671d73cfbc17c
Research completion matrix blob    = fb9ee7e9cb55d56bb870bc445959eb693ce71eab
Research mechanics index commit    = 921e60f2e2da5d2c51129514b70fe6a891e231ec
Research mechanics index blob      = 77fce3801d15bcaec7c512667f24bdbc028535aa
```

## 2. Frozen observable model

```text
Eligible enemy target-producing operation
+ Provocation resident/effective
+ successful proc
+ Source admissible in current operation
→ Source forced/included according to Target Contract
```

Target-contract behavior is frozen for observed:

- Enemy Single;
- Random / deterministic enemy selector;
- Choose-N with bounded slot/RNG micro-order;
- Fixed-All;
- Primary + Derived;
- Independent Multi-Query;
- Locked Multi-Hit;
- inherited vs independent Assault components.

Friendly / Healing / Self operations do not cross-redirect to enemy Source.

## 3. Target-control and lifecycle boundaries

```text
Taunt:
  Normal Attack forced-target domain

Provocation:
  eligible Skill target-operation domain

Confusion:
  when Confusion controls the target decision,
  Provocation does not additionally force Source

Insight:
  existing protection can reject application
  later Insight can suppress resident Provocation

Exhaustion:
  blocked Skill gives no observable target-resolution opportunity to Provocation

FalseReport:
  tested Source provider suppression can suspend dependent resident Provocations
  Holder FalseReport does not inherently suppress an external Provocation

Source death:
  does not remove State
  dead Source is not forced
```

## 4. Critical contract corrections

Battle Runtime design must preserve these distinctions:

1. **Resident != Effective**.
2. `cfg_96` is not Provocation-exclusive.
3. Provocation execution event does not guarantee target replacement.
4. Locked/closed target contexts can reject an inadmissible external Source.
5. Damage reduction / `cfg_71` is **not intrinsic to State 690108** and remains source-skill dependent.
6. The contract does **not** freeze Guard / Resistance / Evasion / Damage Sharing ordering.
7. The contract does **not** freeze a `TargetSystem`, `TargetSelectorInterceptor`, or other specific runtime owner/class.
8. Multiple-source latest-wins and same-source refresh are PROJECT_DEFAULT only if Runtime needs unsupported-overlap behavior.
9. 【独行赴斗】 Taunt→Provocation production is source-skill-owned, not generic 690108 reapplication.

## 5. Canonical Q43 restoration

Original Q43 is:

```text
挑拨期间来源转换阵营/关系。
若 Confusion / Control / 特殊阵营认定导致 Source legality 变化，
Provocation 行为如何处理。
若游戏不可能出现，则 OUT_OF_SCOPE / NO NATURAL CASE。
```

Final disposition:

```text
BOUNDED_UNKNOWN / NO_NATURAL_CASE
Frozen boundary: current-operation Source admissibility is never overridden.
```

This closes the documentation blocker that previously prevented FG-19 from passing.

## 6. Final audit disposition

```text
Round 1–6 Research Campaign     = COMPLETE
Adversarial Falsification       = PASS
Unexplained Core Counterexample = 0
Final Contract Correction       = PASS
Freeze Gate FG-01..FG-20        = 20 / 20 PASS

Research FROZEN                 = YES
Mechanism Contract FROZEN       = YES
Runtime FROZEN TO CONTRACT      = NO
Strict Complete                 = NO
Stage12 Production Active       = NO
```

## 7. Runtime obligations

Later contract-aligned design must provide at least the behaviors required by the frozen 25-case minimum test matrix, including:

- single/random/deterministic targeting;
- every frozen multi-target family;
- friendly/heal/self exclusion;
- dead Source;
- locked Duel event-without-redirect case;
- Confusion / Taunt / Insight / Exhaustion / FalseReport boundaries;
- inherited and independent Assault;
- event-code disambiguation;
- Source-death state persistence.

These are obligations for future implementation, not evidence that Runtime already exists.

## 8. Bounded unknowns

Non-blocking research debt remains explicit for:

- hidden selector/RNG micro-order;
- strict all-configurations Choose-N micro-order;
- no-target/environment edges;
- rare non-death Source-invalidity classes;
- target-selected/effect-created race timing;
- simultaneous multi-source/reapplication;
- unseen special immunity bypasses;
- fixed-target variants beyond tested Duel;
- insufficient-target micro-policy;
- Q43 Source relation/allegiance mutation;
- same-window lifecycle micro-order.

Current Battle disposition:

```text
Research FROZEN            = YES
Runtime FROZEN TO CONTRACT = NO
Strict Complete            = NO
Next                       = Stage12 contract-aligned Runtime Design
```
