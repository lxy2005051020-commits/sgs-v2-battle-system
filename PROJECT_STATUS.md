# 三国志战略版战斗模拟器 V2 · 当前项目状态

> 本文件维护当前项目状态与后续主线。历史设计、审计、修复与冻结证据继续保存在各阶段正式文件中，不通过本文件无痕改写。

## 1. 当前已完成阶段

```text
Stage 1 基础运行模型                           ✅ 稳定
Stage 2 BattleSystem                          ✅ FROZEN
Stage 3 BattleState                           ✅ 稳定
Stage 4 官方状态代表接入                       ✅ FROZEN（工程阶段）
Stage 5 Effect                                ✅ FROZEN
Stage 6 Skill Runtime                         ✅ FROZEN（基础能力）
Stage 7 Trigger / Recovery                    ✅ FROZEN
Stage 8 Damage Pipeline                       ✅ FROZEN
Stage 9 Cross-Mechanism Runtime Orchestration ✅ FROZEN
Stage 10 Persistent State Runtime Integration ✅ FROZEN / 已合入 main
```

第十阶段正式主分支合入提交：

`30f623f9efed20b5a82044b51519db1af6da86d3`

第十阶段合入后，生产与测试树保持冻结基线，后续新增仅为规划文档时不得修改已冻结语义。

## 2. 当前官方状态严格完成度

官方具体状态总数：40。

严格完成口径：

```text
机制研究冻结
+
运行时冻结到合同
```

第十阶段完成后，严格完成状态为 16 / 40：

```text
连击
群攻
反击
分担
铁索连环
援护
混乱
嘲讽
灼烧
水攻
中毒
溃逃
沙暴
叛逃
急救
休整
```

剩余：

```text
24 / 40 尚未严格完成
```

其中 690082 规避、690083 抵御、690092 必中均已完成 **Research FROZEN**，但 Runtime 均仍为 `NOT_INTEGRATED`，因此严格完成数仍保持 `16 / 40`。

这些状态不再无限拆成零散小阶段，而是集中安排在第十一、十二阶段完成。

## 3. 当前路线权威

当前路线权威：

`POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md`

演示升级规划：

`DEMO_SCENARIO_SUITE_ROADMAP.md`

旧路线：

```text
POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md
PROJECT_ROADMAP.md
```

保留为历史规划，不再作为当前第十一阶段以后的执行 authority。

## 4. 第十一阶段当前状态

第十一阶段定义为：

```text
官方状态补全（一）
```

目标是优先完成不依赖完整战法执行系统的剩余状态，主要覆盖：

```text
伤害类
命中类
恢复类
行动与顺序类
旧运行时骨架与研究债务
```

当前状态：

```text
PLANNING / RESEARCH FREEZE IN PROGRESS
690082 EVASION = RESEARCH FROZEN / RUNTIME NOT_INTEGRATED
690083 RESISTANCE = RESEARCH FROZEN / RUNTIME NOT_INTEGRATED
690092 SURE_HIT = RESEARCH FROZEN / RUNTIME NOT_INTEGRATED
PRODUCTION IMPLEMENTATION = NOT AUTHORIZED
```

Stage11 Battle 侧 authority 桥接：

- stages/stage11/research/690082_EVASION_RESEARCH_AUTHORITY.md
- stages/stage11/research/690083_RESISTANCE_RESEARCH_AUTHORITY.md
- stages/stage11/research/690092_SURE_HIT_RESEARCH_AUTHORITY.md

规划：

`stages/stage11/STAGE11_PLANNING.md`

## 5. 第十二阶段当前状态

第十二阶段定义为：

```text
官方状态补全（二）
```

目标是完成依赖复杂控制、技能类别认识或统一权限判断的剩余状态，并执行官方 40 状态总收口。

第十二阶段允许建立最小战法类别与权限基础，但不正式接入具体战法执行链。

最终目标：

```text
40 / 40 机制研究完成
40 / 40 运行时完成
官方状态体系正式冻结
```

当前状态：

```text
PLANNING ONLY
PRODUCTION IMPLEMENTATION = NOT AUTHORIZED
```

规划：

`stages/stage12/STAGE12_PLANNING.md`

## 6. 第十三阶段以后

状态体系完成后，再进入正式战法主线：

```text
Stage 13 突击战法
Stage 14 普通主动战法
Stage 15 准备战法
Stage 16+ 被动 / 指挥 / 阵法 / 兵种战法等
```

具体后续编号在每阶段开始前仍需重新按依赖审计。

## 7. 演示程序

当前基础 `demo.py` 不足以完整展示已有战斗能力。

从第十一阶段开始，演示程序逐步升级为固定场景套件，至少覆盖：

```text
基础战斗
第九阶段普通攻击反应链
第十阶段持续状态
第十一阶段伤害 / 命中 / 恢复 / 行动状态
第十二阶段复杂控制状态
```

第十三阶段以后再加入真实战法场景。

演示只负责可读展示和综合冒烟验证，不替代正式测试。

## 8. 当前唯一下一动作

研究侧不再重复研究 690082 / 690083 / 690092；三者 Runtime Integration 留待 Stage11 正式设计/施工。

下一研究工作从剩余 Stage11 状态中继续推进。

当前候选：

```text
690093 破阵 / BREAK_FORMATION
```
