# 三国志战略版战斗模拟器 V2 · 当前阶段状态

> 本文件维护当前项目状态与封版验证基线。历史 lifecycle 证据保存在各阶段正式审计、repair 与 freeze 文件中，不通过 current-state 文档无痕改写。

## 当前已冻结工程阶段

```text
Stage 1 基础运行模型                           ✅ 回归稳定
Stage 2 BattleSystem                          ✅ FROZEN
Stage 3 BattleState                           ✅ 稳定
Stage 4 官方状态代表接入                       ✅ FROZEN（工程阶段）
Stage 5 Effect                                ✅ FROZEN
Stage 6 Skill Runtime                         ✅ FROZEN
Stage 7 Trigger / Recovery                    ✅ FROZEN
Stage 8 Damage Pipeline                       ✅ FROZEN
Stage 9 Cross-Mechanism Runtime Orchestration ✅ FROZEN
```

重要区分：

```text
Stage FROZEN
!=
该 Stage 中出现过的每个官方状态都已完成机制研究
```

例如 Stage4 / Stage7 的部分代表状态属于旧工程 skeleton，不自动计为状态机制 Research FROZEN。

## Stage9 Final Freeze

Frozen runtime source:

`7380682164cf4a71256e23207bd031171c3e6231`

Final verified closure：

```text
42 / 42 runtime invariants PASS
45 / 45 gameplay regressions PASS
12 / 12 architecture guarantees PASS
6 / 6 finalization contracts PASS
5 / 5 integerization vectors PASS
6 / 6 FutureBranch families PASS
753 tests PASS
Demo PASS
CI PASS
artifact provenance PASS
```

Stage8 permanent boundary：

```text
Stage8 = FROZEN
Formal Stage8 Reopen = NO
```

Stage9 未改变 Stage8 的 weapon base formula、strategy base formula、DamagePrevention、HitResolution、DamageModifier 或 DamageFormulaPolicy ownership。

## 官方状态严格完成度

官方具体 BattleState：40。

当前严格完成：8。

```text
combo / 连击
cleave / 群攻
counterattack / 反击
damage_share / 分担
chain_link / 铁索连环
guard / 援护
confusion / 混乱
taunt / 嘲讽
```

严格口径：

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

才计为状态彻底完成。

`damage_split / 分摊` Runtime 已有 Stage9 项目默认，但 `DSTS9-B02` 仍为 empirical OPEN / UNOBSERVED，因此不计入最终 40/40 完成数。

当前严格统计：

```text
8 / 40 COMPLETE
32 / 40 NOT YET FULLY COMPLETE
```

权威完成度矩阵：

`lxy2005051020-commits/sgs-state-mechanics-research/STATE_COMPLETION_MATRIX.md`

## 当前路线 authority

Stage9 之后的新路线：

`POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md`

旧 `PROJECT_ROADMAP.md` 保留为历史规划快照，不再作为 Stage10+ 当前路线 authority。

状态研究仓库当前 authority：

```text
lxy2005051020-commits/sgs-state-mechanics-research
├─ RESEARCH_ROADMAP_V2.md
├─ STATE_COMPLETION_MATRIX.md
└─ STATE_MECHANICS_INDEX.md
```

## Stage10 当前状态

Stage10 重新定义为：

```text
Persistent State Runtime Integration
```

目标状态：

```text
burn
flood
poison
rout
sandstorm
rebellion
first_aid
recuperation
```

上述 8 个状态当前研究已 FROZEN / RE-FROZEN，Stage10 负责在不破坏 Stage7/8/9 冻结边界的前提下完成正式 Runtime Integration。

当前生命周期边界：

```text
STAGE 9 = FROZEN

STAGE 10 = RESEARCH / DESIGN / BOUNDARY DEFINITION

Stage10 production implementation = NOT AUTHORIZED
```

Stage10 当前 scope：

`stages/stage10/STAGE10_RESEARCH_SCOPE.md`
