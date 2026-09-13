# 阶段文件索引

每个阶段的设计、Prompt、证据、审计和研究材料统一存放在 `stages/stageN/`。

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline](stage8/README.md)
- [Stage 9：核心裁决研究](stage9/README.md)

共享源码保留在 `sgs_v2/`，运行测试保留在 `tests/`，跨阶段状态目录保留在 `research/`。Stage 9 研究脚本和证据随研究目录完整归档。

阶段状态以 [PROJECT_STATUS.md](../PROJECT_STATUS.md) 及对应阶段的正式合同为准。本次目录整理不改变阶段状态或历史验证结果。

旧路径对应关系见 [迁移清单](PATH_MIGRATION.md)。Stage 8 的四个旧入口仅包含跳转说明，已并入正式文件；历史提交中的旧路径仍可通过对应提交访问。
