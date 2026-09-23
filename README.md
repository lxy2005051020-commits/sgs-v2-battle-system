# 三国志战略版 V2 战斗系统

## 当前导航

- [当前项目状态](PROJECT_STATUS.md)
- [Canonical State Planning Matrix](CANONICAL_STATE_PLANNING_MATRIX.md)
- [第十阶段后 · 官方状态补全与战法接入总路线](POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md)
- [演示场景套件升级规划](DEMO_SCENARIO_SUITE_ROADMAP.md)
- [各阶段文件夹与材料索引](stages/README.md)
- [第十一阶段规划](stages/stage11/STAGE11_PLANNING.md)
- [第十二阶段规划](stages/stage12/STAGE12_PLANNING.md)
- [跨阶段状态研究](research/README.md)

历史路线：
- [第九阶段后旧研究与接入路线](POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)
- [更早期项目路线快照](PROJECT_ROADMAP.md)

## 当前工程边界

```text
Stage8  = FROZEN
Stage9  = FROZEN
Stage10 = FROZEN / MAIN INTEGRATION COMPLETE
Stage11 = ACTIVE / RESEARCH CLOSURE + RUNTIME INTEGRATION DESIGN
Stage12 = PLANNING ONLY
Stage13 = NOT ACTIVE
```

Stage10 正式主分支合入提交：

`30f623f9efed20b5a82044b51519db1af6da86d3`

当前生产与测试子树仍与 Stage10 冻结 pin 完全一致，Stage10 冻结语义没有被后续文档工作改写。

## 官方状态统一完成度

官方具体状态共 40 个。

```text
Research FROZEN            = 24 / 40
Runtime FROZEN TO CONTRACT = 16 / 40
Strict Complete            = 16 / 40
```

严格完成仍只认：

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

Stage10 的 8 个持续状态已经正式 Runtime Freeze，因此与此前 8 个严格完成状态合计为 `16 / 40`。

## 当前 Project Stage

当前项目处于：

```text
Stage11 = 官方状态补全（一）
Canonical Scope = 17 states
Research FROZEN = 8
Research Open / Debt = 9
Runtime FROZEN = 0
```

已 Research FROZEN：

```text
690082 规避
690083 抵御
690092 必中
690093 破阵
690070 会心
690069 奇谋
690094 倒戈
690095 攻心
```

这 8 个状态的下一工程动作是 **Runtime Integration Design**，不是直接 Implementation。

## Project Stage 与 Research Wave

Project Stage 是产品建设顺序，Battle repository 为 authority。

Research Wave 是研究依赖顺序，Research repository 可以调整，但不得重编号 Project Stage。

```text
Stage11
  Research Wave 2: 伤害 / 命中 / 恢复
  Research Wave 3: 行动 / 顺序 / 控制
  Research Debt: 690086 分摊

Stage12
  Research Wave 4: 技能权限 / 目标控制
  Research Wave 5: 装备 / 复合控制

Stage13 = 突击战法
Stage14 = 普通主动战法
Stage15 = 准备战法
```

## 当前唯一下一动作

Research side：继续关闭 Stage11 未完成研究、证据阻塞和研究债务。

Runtime side：对已经 Research FROZEN 的 Stage11 状态进入 **Runtime Integration Design → Independent Design Audit → Design Freeze**。

在 Stage11 Exit Gate 满足前，不得把 Stage12 或 Stage13 标为 Active，也不得启动整体 Stage11 production implementation。
