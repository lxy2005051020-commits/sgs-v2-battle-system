# Stage 8 · Damage Pipeline

状态：`✅ FROZEN`

Stage 8 已完成设计冻结、实现、独立审计、Final Audit、main 合并与 main exact-head 封版验证。Stage 9 尚未开始，但现在可以进入新的独立设计阶段。

各阶段资料已统一按“一阶段一目录”管理，见[阶段索引](../README.md)。production code 继续按职责放在 `sgs_v2/`，测试继续放在 `tests/`；本目录收纳 Stage 8 的设计合同、Evidence、施工 Prompt、审计与封版材料。

## Canonical files

```text
stages/stage8/
├── README.md
├── STAGE8.md
├── STAGE8_DESIGN_FREEZE.md
├── STAGE8_EVIDENCE_MATRIX.md
├── STAGE8_BUILD_PROMPT.md
├── STAGE8_IMPLEMENTATION_REPORT.md
├── STAGE8_FINAL_AUDIT.md
└── STAGE8_FREEZE_RECORD.md
```

含义：

- `STAGE8.md`：第二轮独立设计复审通过的 v2 主设计合同。
- `STAGE8_DESIGN_FREEZE.md`：DESIGN FROZEN 的 normative freeze-prep addendum；只补充 numeric validation ownership 与 typed StageEvaluationStatus，两者与主设计共同构成冻结合同。
- `STAGE8_EVIDENCE_MATRIX.md`：官方状态 production mapping 的 Evidence Gate。
- `STAGE8_BUILD_PROMPT.md`：Stage 8 正式施工 Prompt。
- `STAGE8_IMPLEMENTATION_REPORT.md`：production implementation 施工报告与独立实现审计入口记录；保留其历史时间点描述，不作为当前状态文档。
- `STAGE8_FINAL_AUDIT.md`：锁定 Final Audit approved exact SHA、审计 findings、CI 与 artifact provenance 的正式 Final Audit 记录。
- `STAGE8_FREEZE_RECORD.md`：记录 Stage 8 进入 main 后的 exact-head CI、artifact provenance 与最终 FROZEN 依据。

## Frozen design authority

Stage 8 后续维护必须同时遵守：

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

其他核心 topology / provider / formula / modifier / RNG / provenance / Event ownership / Stage 8-9 boundary 不得在后续 Stage 9+ 施工中反向改变，除非出现明确 freeze-breaking defect 并执行正式 reopen 流程。

## Evidence Gate at Freeze

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

`weakness` 的 PASS 仅允许迁移既有冻结行为；其余 DEFER 状态不得因为 Stage 8 已 FROZEN 就被视为 official behavior 已实现。

## Final process state

Stage 8 implementation lineage 最终合并源：

```text
202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

Final Audit approved implementation SHA：

```text
446ac5a9d4ae595dcc79abc3c03873cad22893f8
```

完成顺序：

```text
Second Independent Re-Audit
→ findings repaired

Third Independent Re-Audit
→ PASSED

Stage 8 Final Audit
→ PASSED
→ APPROVED FOR MERGE TO MAIN

S8-RN-01
→ CLOSED by docs-only correction

stage8-damage-pipeline → main
→ FAST-FORWARD MERGED

main exact-head verification
→ PASSED

Stage 8
→ FROZEN
```

Final Audit 结论：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 0

VERDICT = APPROVED FOR MERGE TO MAIN
```

Final Audit 中唯一 remaining finding `S8-RN-01` 属于 documentation / process，已在 merge source `202647135f97db31e08b6ad1d917d7e5a8e6ce15` 中通过 docs-only correction 关闭。

Final Audit baseline verification：

```text
Run #161
run_id = 34497232784
head_sha = 446ac5a9d4ae595dcc79abc3c03873cad22893f8
pytest -q = 326 passed
demo.py = success
workflow conclusion = success
```

最终 merge-source branch verification：

```text
Run #163
run_id = 34502709262
head_sha = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
pytest -q = 326 passed
demo.py = success
workflow conclusion = success
```

Stage 8 通过 fast-forward 进入 `main` 后，main exact HEAD 仍为：

```text
202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

main 封版验证：

```text
Run #164
run_id = 34503212432
head_sha = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
pytest -q = 326 passed in 1.30s
demo.py = success
workflow conclusion = success
```

main audit artifact：

```text
stage8-independent-audit-202647135f97db31e08b6ad1d917d7e5a8e6ce15
Artifact ID = 10162718752
SHA-256 = ca4af39fe3c069f3b050416c1b52e136560e20270dd31a085d024fbd421ee531
AUDIT_SOURCE_SHA = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

因此 Stage 8 封版条件已经满足：

```text
Final Audit PASSED
+
all blocking findings CLOSED
+
S8-RN-01 CLOSED
+
implementation entered main
+
main exact-head pytest / demo / CI PASS
+
main exact-head artifact provenance PASS
=
Stage 8 FROZEN
```

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
├── STAGEN_FINAL_AUDIT.md
└── STAGEN_FREEZE_RECORD.md     # 封版时如需要
```

历史 Stage 1～7 暂不因 Stage 8 封版而迁移。Stage 9 必须作为新的独立阶段设计，不得顺手重写 Stage 8 frozen contracts。
