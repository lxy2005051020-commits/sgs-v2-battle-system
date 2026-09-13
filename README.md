# 三国志战略版 V2 战斗系统

- [各 Stage 文件夹与材料索引](stages/README.md)
- [当前项目状态](PROJECT_STATUS.md)
- [项目路线图](PROJECT_ROADMAP.md)
- [跨阶段状态研究](research/README.md)
- [Stage 9 当前合同闭环与 authority 导航](stages/stage9/README.md)

当前边界：

```text
Stage 8 = FROZEN
Formal Stage8 Reopen = NO
Stage 9 = contract closure / orchestration research around Stage8 seams
Stage 9 production implementation authority = NOT CREATED YET
STAGE9.md = DESIGN FROZEN — PENDING FREEZE AUDIT
```

Stage 9 的 current authority、九机制状态与 RF-C02 文档同步结果统一从 [`stages/stage9/README.md`](stages/stage9/README.md) 进入；历史 audits/research 不因后续 repair 而被无痕改写。

从仓库根目录运行现有生产系统：

```bash
python -m pytest -q
python demo.py
```
