# 三国志战略版 V2 战斗系统

- [当前项目状态](PROJECT_STATUS.md)
- [Post-Stage9 当前研究与接入路线](POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)
- [Stage10 Research Scope](stages/stage10/STAGE10_RESEARCH_SCOPE.md)
- [各 Stage 文件夹与材料索引](stages/README.md)
- [历史项目路线图](PROJECT_ROADMAP.md)
- [跨阶段状态研究](research/README.md)
- [Stage 9 authority 导航](stages/stage9/README.md)
- [Stage 9 Final Audit](stages/stage9/STAGE9_FINAL_AUDIT.md)
- [Stage 9 Freeze Record](stages/stage9/STAGE9_FREEZE_RECORD.md)

## 当前边界

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO

Stage 9 = FROZEN
Stage9 Implementation = COMPLETE
Stage9 Final Freeze = COMPLETE

Stage 10 = RESEARCH / DESIGN
Stage10 Production Implementation = NOT AUTHORIZED
```

## 官方状态完成度

当前采用严格完成口径：

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

官方具体状态共 40 个，当前严格完成 8 个，剩余 32 个进入 Post-Stage9 状态完善计划。

Stage10 首批目标为已经研究冻结的 8 个持续性状态：

```text
灼烧 / 水攻 / 中毒 / 溃逃
沙暴 / 叛逃 / 急救 / 休整
```

状态研究主 authority 位于独立仓库：

`lxy2005051020-commits/sgs-state-mechanics-research`

重点文件：

```text
RESEARCH_ROADMAP_V2.md
STATE_COMPLETION_MATRIX.md
STATE_MECHANICS_INDEX.md
```

Stage 9 的冻结运行时语义仍以 `stages/stage9/STAGE9_FREEZE_RECORD.md` 为最终 post-implementation authority；新路线不得静默修改已冻结语义。

从仓库根目录运行：

```bash
python -m pytest -q
python demo.py
```
