# Stage 8 · Damage Pipeline

状态：`FINAL AUDIT PASSED / APPROVED FOR MERGE TO MAIN`

Stage 8 当前尚未 FROZEN；Stage 9 尚未开始。

从 Stage 8 开始，阶段资料统一按“一阶段一目录”管理。production code 继续按职责放在 `sgs_v2/`，测试继续放在 `tests/`；阶段目录只收纳设计合同、Evidence、施工 Prompt、审计与封版材料。别把源码也按 Stage 切成考古层，那会把整洁从美德变成事故。

## Canonical files

```text
stages/stage8/
├── README.md
├── STAGE8.md
├── STAGE8_DESIGN_FREEZE.md
├── STAGE8_EVIDENCE_MATRIX.md
├── STAGE8_BUILD_PROMPT.md
├── STAGE8_IMPLEMENTATION_REPORT.md
└── STAGE8_FINAL_AUDIT.md
```

含义：

- `STAGE8.md`：第二轮独立设计复审通过的 v2 主设计合同。
- `STAGE8_DESIGN_FREEZE.md`：DESIGN FROZEN 的 normative freeze-prep addendum；只补充 numeric validation ownership 与 typed StageEvaluationStatus，两者与主设计共同构成冻结合同。
- `STAGE8_EVIDENCE_MATRIX.md`：官方状态 production mapping 的 Evidence Gate。
- `STAGE8_BUILD_PROMPT.md`：Stage 8 正式施工 Prompt。
- `STAGE8_IMPLEMENTATION_REPORT.md`：production implementation 施工报告与独立实现审计入口记录；保留其历史时间点描述，不作为当前状态文档。
- `STAGE8_FINAL_AUDIT.md`：锁定 Final Audit approved exact SHA、审计 findings、CI 与 artifact provenance 的正式 Final Audit 记录。

## Frozen design authority

Stage 8 施工与实现审计必须同时遵守：

```text
STAGE8.md
+ STAGE8_DESIGN_FREEZE.md
+ STAGE8_EVIDENCE_MATRIX.md
```

如果主设计与 freeze-prep addendum 只在以下两点存在差异，以 `STAGE8_DESIGN_FREEZE.md` 为准：

```text
1. public numeric boundary validation ownership
2. DamagePipelineTrace 的 typed StageEvaluationStatus
```

其他核心 topology / provider / formula / modifier / RNG / provenance / Event ownership / Stage 8-9 boundary 不得借目录整理改变。

## Current Evidence Gate

```text
weakness                  PASS_STAGE8

evasion                   DEFER
barrier                   DEFER
sure_hit                   DEFER
defense_pierce            DEFER
vigilance                 DEFER
critical                  DEFER
strategy_critical         DEFER
damage_reduction_pierce   DEFER
rebellion                 DEFER
```

`weakness` 的 PASS 仅允许迁移既有冻结行为；其余 DEFER 状态不得出现 official production binding。

## Current process state

Stage 8 production implementation 位于：

```text
stage8-damage-pipeline
```

完成顺序：

```text
Second Independent Re-Audit
→ PASSED

Third Independent Re-Audit
→ PASSED

Stage 8 Final Audit
→ PASSED

S8-RN-01
→ CLOSED by docs-only correction

next:
merge stage8-damage-pipeline → main
```

Final Audit approved exact SHA：

```text
446ac5a9d4ae595dcc79abc3c03873cad22893f8
```

Final Audit 结论：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 0

VERDICT = APPROVED FOR MERGE TO MAIN
```

唯一 remaining finding `S8-RN-01` 属于 documentation / process，要求在 merge 前修复 current-state chronology。本次 Post-Final-Audit docs-only correction 只修改当前状态文档并保存正式 Final Audit 报告，不触碰 runtime、tests、workflow、Frozen Design 或 Evidence Matrix。

Final Audit baseline verification：

```text
Run #161
run_id = 34497232784
head_sha = 446ac5a9d4ae595dcc79abc3c03873cad22893f8
pytest -q = 326 passed
demo.py = success
workflow conclusion = success
```

本次 docs-only correction 产生的新 exact HEAD 必须取得自己的 CI 与 audit artifact provenance，验证通过后才是最终 merge source。

当前状态仍然不是：

```text
Stage 8 FROZEN
```

Stage 8 只有在后续完成以下独立流程后才能 FROZEN：

```text
merge stage8-damage-pipeline → main
↓
resolve main exact merge SHA
↓
main exact-head pytest
↓
main exact-head demo
↓
main exact-head GitHub Actions
↓
main exact-head artifact provenance
↓
final freeze docs/status
↓
Stage 8 FROZEN
```

Stage 9 在此之前不得开始。

## Folder convention

Stage 9 及以后默认采用同样结构：

```text
stages/stageN/
├── README.md
├── STAGEN.md
├── STAGEN_EVIDENCE_MATRIX.md   # 如需要 Evidence Gate
├── STAGEN_DESIGN_FREEZE.md
├── STAGEN_BUILD_PROMPT.md
├── STAGEN_IMPLEMENTATION_AUDIT.md
└── STAGEN_FINAL_AUDIT.md
```

历史 Stage 1～7 暂不在本次 Stage 8 整理中迁移。它们已经 FROZEN，后续若统一目录，应做单独 docs-only path migration，不和 production 施工混在一起。
