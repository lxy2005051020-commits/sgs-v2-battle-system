# Stage 10 · Persistent State Runtime Integration

当前状态：

```text
Mechanism Research:          COMPLETE
Independent Design Audit:    FAIL / REPAIR REQUIRED
Authority Gap Triage:        COMPLETE
Targeted Research:           COMPLETE AS R1-C INPUT
Architecture Repair R1-C:    COMPLETE
Design Re-Audit:             NOT STARTED
Production:                  NOT AUTHORIZED
Design Freeze:               NOT AUTHORIZED
```

当前设计版本：

```text
STAGE10.md
= ARCHITECTURE DESIGN DRAFT V2
= R1-C REPAIR COMPLETE
= READY FOR INDEPENDENT DESIGN RE-AUDIT
```

Stage10 目标仍然是将以下 8 个 persistent state 正式接入 Runtime：

```text
690072 BURN / 灼烧
690073 FLOOD / 水攻
690074 POISON / 中毒
690075 ROUT / 溃逃
690076 SANDSTORM / 沙暴
690077 REBELLION / 叛逃
690078 FIRST_AID / 急救
690079 RECUPERATION / 休整
```

## 当前文档

- [Stage10 Research Scope](STAGE10_RESEARCH_SCOPE.md)
- [Stage10 Research Matrix](STAGE10_RESEARCH_MATRIX.md)
- [Stage10 Runtime Mapping](STAGE10_RUNTIME_MAPPING.md)
- [Stage10 Open Questions](STAGE10_OPEN_QUESTIONS.md)
- [Stage10 Architecture Design Draft V2](STAGE10.md)
- [Stage10 Independent Design Audit Round 1](STAGE10_DESIGN_AUDIT.md)
- [Stage10 Authority Gap Triage](STAGE10_AUTHORITY_GAP_TRIAGE.md)
- [Stage10 Targeted Research Questions](STAGE10_TARGETED_RESEARCH_QUESTIONS.md)
- [Stage7 → Stage10 Compatibility Addendum](../stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Stage8 → Stage10 Compatibility Addendum](../stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Post-Stage9 项目路线](../../POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)

## R1-C repair result

第一轮独立设计审计结果：

```text
BLOCKER   = 7
MAJOR     = 6
MINOR     = 4
HARDENING = 5
VERDICT   = FAIL
```

R1-C 已为全部 7 BLOCKER 与 6 MAJOR 提供显式修复合同，并在 `STAGE10.md` 中建立 Finding Closure Matrix。

当前只能写：

```text
BLOCKER repair claimed = 7 / 7
MAJOR repair claimed   = 6 / 6
```

不能写：

```text
DESIGN PASS
DESIGN FROZEN
IMPLEMENTATION AUTHORIZED
```

最终是否关闭由 Round 2 独立设计审计决定。

## Key architecture repairs

```text
1. Stage7 death-abort compatibility reopen
2. Stage8 FROZEN_APPLICATION limited compatibility reopen
3. frozen-input replay model replaces Draft V1 nominal_damage shortcut
4. PRE_BATTLE lifecycle off-by-one repaired
5. physical expiry moved to deterministic last ActionStart window completion
6. one synchronous DefeatCleanupPort across all death-capable troop-loss paths
7. battle-authoritative SkillRuntimeRegistry keyed by (owner, SkillSlot)
8. physical StateInstance identity separated from application-generation identity
9. FIRST_AID zero-loss resolved-hit eligibility corrected
10. official hidden PRNG uncertainty isolated from simulator determinism policy
11. RecoveryOpportunity hierarchy closed as sibling typed RuleIntent
12. one shared DamageAftermathPort for standard/Cleave-compatible aftermath
13. Stage9 Share / Distribution / victory-latch local ordering frozen
14. dependency and BattleSystems composition DAG explicitly closed
```

## FIRST_AID corrected boundary

Stage10 Draft V2 no longer uses:

```text
ActualTargetTroopLoss > 0
```

as eligibility.

Required observable topology:

```text
weakness-zero → opportunity YES
barrier-zero  → opportunity YES
evasion/miss  → opportunity NO
fatal target  → opportunity NO
```

`ActualTargetTroopLoss == 0` may still produce an admitted FIRST_AID opportunity.

## Full-troop recovery boundary

```text
recoverable_gap == 0
!=
skip opportunity
```

An admitted successful recovery request may resolve with:

```text
actual recovery = 0
```

through existing RecoverySystem / TroopSystem cap semantics.

## Simulator RNG policy

Official hidden PRNG consumption remains:

```text
UNKNOWN / UNOBSERVABLE
```

R1-C simulator policy is:

```text
every admitted RecoveryOpportunity
→ exactly one context.random.chance(probability) call
→ including probability 0.0 / 1.0
→ regardless of recoverable_gap
```

Classification:

```text
ENGINEERING DETERMINISM
NOT OFFICIAL GAMEPLAY AUTHORITY
```

## Authority synchronization note

R1-C pinned Gameplay Authority at:

```text
61f2be7e87e6bfab1433657ee7f766ae0c53da9d
```

At that exact repository HEAD, the task-referenced targeted-research markdown files are not present and the checked-in FIRST_AID contract still predates the zero-loss correction. `STAGE10.md` records this explicitly and treats the project-owner supplied targeted-research closure as R1-C authoritative input without modifying the Gameplay Authority repository.

This repository-sync issue is not silently rewritten as research evidence.

## Next gate

Only the following workflow is authorized:

```text
Stage10 Design Draft V2
+ Stage7 compatibility addendum
+ Stage8 compatibility addendum
↓
Stage10 Independent Design Re-Audit Round 2
↓
repair again if required
↓
PASS only
↓
Stage10 Design Freeze
↓
Build Prompt
↓
production implementation
```

R1-C itself authorizes no production change.
