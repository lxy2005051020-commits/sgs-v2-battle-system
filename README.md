# 三国志战略版 V2 战斗系统

## 当前导航

- [当前项目状态](PROJECT_STATUS.md)
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
第八阶段：已冻结
第九阶段：已冻结
第十阶段：已冻结并正式合入主分支

第十一阶段：规划 / 研究准备
第十二阶段：规划 / 研究准备
```

第十阶段正式主分支合入提交：

`30f623f9efed20b5a82044b51519db1af6da86d3`

后续主分支允许继续增加规划文档，但不得无正式重开流程修改第十阶段冻结语义。

## 官方状态完成度

当前采用严格完成口径：

```text
机制研究冻结
+
运行时冻结到合同
```

官方具体状态共 40 个。

第十阶段完成后，当前严格完成：

```text
16 / 40
```

已严格完成：

```text
连击 / 群攻 / 反击 / 分担
铁索连环 / 援护 / 混乱 / 嘲讽
灼烧 / 水攻 / 中毒 / 溃逃
沙暴 / 叛逃 / 急救 / 休整
```

剩余 24 个状态优先安排在第十一、十二阶段补齐。

## 后续主线

```text
第十一阶段：先补伤害 / 命中 / 恢复 / 行动类状态
↓
第十二阶段：补复杂控制与技能权限相关状态，并做 40 / 40 总收口
↓
第十三阶段：突击战法
↓
第十四阶段：普通主动战法
↓
第十五阶段：准备战法
↓
后续：被动 / 指挥 / 阵法 / 兵种战法等
```

## 演示程序

当前 `demo.py` 仍可作为基础入口，但后续将升级为多个固定场景组成的演示套件，用于直观展示已经冻结的战斗能力。

演示不代替正式测试，也不定义机制真相。

从仓库根目录运行：

```bash
python -m pytest -q
python demo.py
```

状态研究主权威仓库：

`lxy2005051020-commits/sgs-state-mechanics-research`
