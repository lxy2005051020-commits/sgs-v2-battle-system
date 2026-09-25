# Stages / 项目阶段索引

每个阶段的设计、研究、证据、审计、冻结和实施材料统一存放在 `stages/stageN/`。

## 1. 阶段导航

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态代表接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline — FROZEN](stage8/README.md)
- [Stage 9：Cross-Mechanism Runtime Orchestration — FROZEN](stage9/README.md)
- [Stage 10：Persistent State Runtime Integration — FROZEN / main integrated](stage10/README.md)
- [Stage 11：官方状态补全（一）— ACTIVE](stage11/README.md)
- [Stage 12：官方状态补全（二）— PLANNING ONLY](stage12/README.md)

## 2. 当前阶段

```text
Stage 8  = FROZEN
Stage 9  = FROZEN
Stage 10 = FROZEN / MAIN INTEGRATION COMPLETE
Stage 11 = ACTIVE / RESEARCH CLOSURE + RUNTIME INTEGRATION DESIGN
Stage 12 = PLANNING ONLY
Stage 13 = NOT ACTIVE
```

Stage10 main integration commit：

`30f623f9efed20b5a82044b51519db1af6da86d3`

## 3. 当前统一状态数字

```text
Official States            = 40
Research FROZEN            = 31
Runtime FROZEN TO CONTRACT = 16
Strict Complete            = 16
```

Stage11：

```text
Canonical Scope       = 17
Research FROZEN       = 15
Research non-FROZEN/debt = 2
Runtime FROZEN        = 0
```

Stage12：

```text
Canonical Scope = 7
Status          = PLANNING ONLY
```

## 4. 当前路线 Authority

项目级路线：

- [第十阶段后官方状态补全与战法接入总路线](../POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md)
- [Canonical State Planning Matrix](../CANONICAL_STATE_PLANNING_MATRIX.md)
- [当前项目状态](../PROJECT_STATUS.md)

Stage 规划：

- [Stage11 Planning](stage11/STAGE11_PLANNING.md)
- [Stage12 Planning](stage12/STAGE12_PLANNING.md)

Research mechanism authority：

`lxy2005051020-commits/sgs-state-mechanics-research`

## 5. Project Stage 与 Research Wave

```text
Project Stage11
  Research Wave 2 = 伤害 / 命中 / 恢复
  Research Wave 3 = 行动 / 顺序 / 控制
  Research Debt   = 690086 分摊

Project Stage12
  Research Wave 4 = 技能权限 / 目标控制
  Research Wave 5 = 装备 / 复合控制

Project Stage13 = 突击战法
Project Stage14 = 普通主动战法
Project Stage15 = 准备战法
```

Research Wave 是研究顺序，不得覆盖项目阶段编号。

## 6. 当前 Stage11 Research FROZEN

```text
690082 规避
690083 抵御
690092 必中
690093 破阵
690070 会心
690069 奇谋
690094 倒戈
690095 攻心
690090 先攻
690091 遇袭
690102 缴械
690104 虚弱
690105 禁疗
690111 震慑
690221 看破
```

这 15 个 Stage11 Research-FROZEN 状态 Runtime 均未 FROZEN TO CONTRACT，因此不增加 Strict Complete。

## 7. Stage11 特殊开放项

```text
690099 警戒 = EVIDENCE BLOCKED / DEFERRED
690221 看破 = RESEARCH FROZEN / Runtime NOT_INTEGRATED
690086 分摊 = DSTS9-B02 empirical research debt
```

Evidence blockage 不等于改变 Project Stage ownership。

## 8. 当前下一动作

```text
Research closure
↓
Mechanism Contract
↓
Runtime Integration Design
↓
Independent Design Audit
↓
Design Freeze
↓
Implementation
```

已经 Research FROZEN 的状态可以进入 Runtime Integration Design，但 Stage11 整体 production implementation 尚未授权。

Stage11 Exit Gate 满足前，不进入 Stage12 Active 或 Stage13 Skill Runtime。
