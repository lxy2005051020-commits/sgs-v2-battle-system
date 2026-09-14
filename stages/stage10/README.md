# Stage 10 · Persistent State Runtime Integration

当前状态：

```text
MECHANISM RESEARCH EXTRACTION = COMPLETE
RUNTIME MAPPING RESEARCH      = COMPLETE
ARCHITECTURE DESIGN           = DRAFT COMPLETE
DESIGN AUDIT                  = NOT STARTED
PRODUCTION IMPLEMENTATION     = NOT AUTHORIZED
```

Stage10 当前目标：将 8 个已经在状态研究仓库完成研究冻结的持续性状态正式接入 Runtime。

```text
690072 burn / 灼烧
690073 flood / 水攻
690074 poison / 中毒
690075 rout / 溃逃
690076 sandstorm / 沙暴
690077 rebellion / 叛逃
690078 first_aid / 急救
690079 recuperation / 休整
```

## 当前文档

- [Stage10 Research Scope](STAGE10_RESEARCH_SCOPE.md)
- [Stage10 Research Matrix](STAGE10_RESEARCH_MATRIX.md)
- [Stage10 Runtime Mapping](STAGE10_RUNTIME_MAPPING.md)
- [Stage10 Open Questions](STAGE10_OPEN_QUESTIONS.md)
- [Stage10 Architecture Design](STAGE10.md)
- [Post-Stage9 项目路线](../../POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)

研究 authority：

```text
lxy2005051020-commits/sgs-state-mechanics-research
├─ RESEARCH_ROADMAP_V2.md
├─ STATE_COMPLETION_MATRIX.md
└─ STATE_MECHANICS_INDEX.md
```

## Research closure

已完成：

```text
8 / 8 Mechanism Contract 读取与提取
6 个持续伤害状态 family 归并
FIRST_AID / RECUPERATION 恢复拓扑拆分
触发时点、快照、刷新、死亡、RNG、生命周期映射
Stage7 Trigger / Recovery 映射
Stage8 Damage Pipeline 映射
Stage9 operation / partition / finalization 映射
implementation-blocking gap 分类
```

当前没有已知的 Stage10 核心机制问题要求在架构设计前继续追加战报研究。

## Architecture design closure

`STAGE10.md` 当前已经为研究阶段提出的 4 个 P0 与 6 个 P1 设计项给出架构答案。

核心决定：

```text
continuous damage
→ FrozenContinuousDamageBasis
→ DamageSystem FROZEN_APPLICATION lane

source-dead DOT
→ historical provenance allowed only on valid PERIODIC_DAMAGE frozen-basis request

finite lifecycle
→ BattleContext.action_progress + PersistentLifecycleWindow

same-name reapply
→ StateLifecycleSystem atomic refresh / physical instance id retained

RECUPERATION + FIRST_AID probability
→ RecoveryOpportunityEffect
→ RecoveryOpportunitySystem
→ context.random
→ RecoverySystem

FIRST_AID
→ synchronous DamageInstance-local AfterDamageHookSystem
→ no EventBus rule execution
→ no new FutureBranchKind
```

设计同时明确发现并接受：

```text
Stage8 requires an explicit LIMITED COMPATIBILITY REOPEN
```

受限 Reopen 只允许加入 `FROZEN_APPLICATION` 计算输入/participant validation/trace 表达，禁止改变既有基础公式数学、普通 LIVE_RUNTIME 路径、DamageResult 分层、Stage9 settlement 或 TroopSystem ownership。

`STAGE10.md` 仍是设计草案，不等于 `DESIGN FROZEN`。

## Next gate

```text
STAGE10.md
↓
independent STAGE10_DESIGN_AUDIT.md
↓
repair / re-audit if needed
↓
PASS only
↓
STAGE10_DESIGN_FREEZE.md
↓
STAGE10_BUILD_PROMPT.md
↓
production implementation
```

在独立 Design Audit 明确 PASS 之前不得进入 production implementation。
