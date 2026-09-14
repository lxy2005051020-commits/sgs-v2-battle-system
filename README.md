# 三国志战略版 V2 战斗系统

- [各 Stage 文件夹与材料索引](stages/README.md)
- [当前项目状态](PROJECT_STATUS.md)
- [项目路线图](PROJECT_ROADMAP.md)
- [跨阶段状态研究](research/README.md)
- [Stage 9 authority 导航](stages/stage9/README.md)
- [Stage 9 Final Audit](stages/stage9/STAGE9_FINAL_AUDIT.md)
- [Stage 9 Freeze Record](stages/stage9/STAGE9_FREEZE_RECORD.md)

当前边界：

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO

Stage 9 = FROZEN
Stage9 Implementation = COMPLETE
Stage9 Final Re-Audit = PASS
Stage9 Pre-Freeze Verification Repair Re-Audit = PASS
Stage9 Final Freeze = COMPLETE
```

Stage 9 的冻结运行时语义以 `stages/stage9/STAGE9_FREEZE_RECORD.md` 为最终 post-implementation authority；`STAGE9_BUILD_PROMPT.md` 保持其 audited blob 不变，历史 audits / repairs / implementation reports 不回写。

从仓库根目录运行：

```bash
python -m pytest -q
python demo.py
```
