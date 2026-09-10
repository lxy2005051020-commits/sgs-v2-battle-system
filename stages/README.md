# Stage Artifacts

从 Stage 8 开始，项目采用“一阶段一目录”的文档组织方式：

```text
stages/
└── stageN/
    ├── README.md
    ├── STAGEN.md
    ├── STAGEN_DESIGN_FREEZE.md
    ├── STAGEN_EVIDENCE_MATRIX.md   # 如需要
    ├── STAGEN_BUILD_PROMPT.md
    ├── STAGEN_IMPLEMENTATION_AUDIT.md
    └── STAGEN_FINAL_AUDIT.md
```

阶段目录管理的是设计、证据、Prompt、审计与封版材料。production code 继续按系统职责组织在 `sgs_v2/`，测试继续放在 `tests/`，不要按 Stage 拆源码。

历史 Stage 1～7 暂时保留原路径，避免打断已冻结阶段的审计引用。若未来统一迁移，必须作为独立 docs-only 任务执行。