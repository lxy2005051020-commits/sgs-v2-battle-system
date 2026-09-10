# Stage 8 · Damage Pipeline

状态：`IMPLEMENTATION REPAIRED / PENDING SECOND INDEPENDENT RE-AUDIT`

从 Stage 8 开始，阶段资料统一按“一阶段一目录”管理。production code 继续按职责放在 `sgs_v2/`，测试继续放在 `tests/`；阶段目录只收纳设计合同、Evidence、施工 Prompt、审计与封版材料。别把源码也按 Stage 切成考古层，那会把整洁从美德变成事故。

## Canonical files

```text
stages/stage8/
├── README.md
├── STAGE8.md
├── STAGE8_DESIGN_FREEZE.md
├── STAGE8_EVIDENCE_MATRIX.md
├── STAGE8_BUILD_PROMPT.md
└── STAGE8_IMPLEMENTATION_REPORT.md
```

含义：

- `STAGE8.md`：第二轮独立设计复审通过的 v2 主设计合同。
- `STAGE8_DESIGN_FREEZE.md`：DESIGN FROZEN 的 normative freeze-prep addendum；只补充 numeric validation ownership 与 typed StageEvaluationStatus，两者与主设计共同构成冻结合同。
- `STAGE8_EVIDENCE_MATRIX.md`：官方状态 production mapping 的 Evidence Gate。
- `STAGE8_BUILD_PROMPT.md`：Stage 8 正式施工 Prompt。
- `STAGE8_IMPLEMENTATION_REPORT.md`：production implementation 施工报告与独立实现审计入口记录；不是 FINAL_AUDIT。

后续 Stage 8 产生的实现审计、最终审计也放入本目录，例如：

```text
STAGE8_IMPLEMENTATION_AUDIT.md
STAGE8_FINAL_AUDIT.md
```

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

## Current implementation state

Stage 8 production implementation 位于：

```text
stage8-damage-pipeline
```

第一次 Independent Re-Audit 后，`S8-M-02` 被 reopened，`S8-N-01` 保持 PARTIAL，并发现 README process-state mismatch。第二轮 findings repair 已补强 typed scope runtime boundary：constructor 继续 canonicalize 合法 iterable，resolver runtime validation 则只接受冻结合同规定的 canonical immutable representation，并在 scope filtering 与 RNG 之前 fail-fast。

当前状态为：

```text
IMPLEMENTATION REPAIRED / PENDING SECOND INDEPENDENT RE-AUDIT
```

`S8-N-01` 仅可记为 addressed / pending independent verification，不在本轮自行宣布 CLOSED。

这不等于 `READY FOR FINAL AUDIT`，更不等于 `Stage 8 FROZEN`。只有第二次独立 re-audit 确认 findings 后，才有资格决定是否进入 FINAL_AUDIT。

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
