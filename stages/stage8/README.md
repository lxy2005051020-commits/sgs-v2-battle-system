# Stage 8 · Damage Pipeline

状态：`FROZEN`

Stage8 已完成设计冻结、实现、独立审计、Final Audit 和 main 封版验证。
当前项目阶段见 [项目状态](../../PROJECT_STATUS.md)，阶段导航见 [阶段索引](../README.md)。

## Runtime authority

- [主设计合同](STAGE8.md)：Damage Pipeline topology、provider、formula、modifier、RNG、provenance 与 Event ownership。
- [设计冻结补充](STAGE8_DESIGN_FREEZE.md)：public numeric validation ownership 与 typed `StageEvaluationStatus`；这两点与主设计不一致时，以补充为准。
- [Stage8 → Stage10 compatibility](STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md)：后续持续状态接入的兼容边界。
- [Final Audit](STAGE8_FINAL_AUDIT.md)：approved implementation SHA、findings 与验证证据。
- [Freeze Record](STAGE8_FREEZE_RECORD.md)：合并后的 main CI、artifact provenance 与最终冻结依据。
- [冻结时 Evidence Gate](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/historical_stage_gates/stage8/STAGE8_EVIDENCE_MATRIX.md)：冻结时的官方状态映射；当前状态完成度以项目状态和后续冻结权威为准。

## Frozen boundaries

```text
DamageRequest
-> participant validation
-> StateDamageRuleProvider / immutable rule snapshot
-> DamagePreventionSystem
-> HitResolutionSystem
-> DamageFormulaPolicySystem / frozen base formula
-> coefficient
-> DamageModifierSystem / finalization
-> DamageResult + DamagePipelineTrace
-> DamageResolutionSystem
-> TroopSystem
```

`DamageSystem.calculate()` 是理论伤害入口；`DamageResolutionSystem` 协调兵力落地与事实发布；`TroopSystem` 是兵力写入口。Battle RNG 来自 `context.random`。

Stage8 冻结时只有 `weakness` 为 `PASS_STAGE8`，其他 Evidence Gate 状态为 `DEFER`；这描述该次冻结范围，后续接入由对应阶段的正式合同与审计负责。

后续维护必须遵守上述冻结设计与适用的 compatibility addendum。核心 topology、formula、modifier、RNG、provenance 与 Event ownership 的改变需要正式 reopen authority。

Build Prompt、施工报告和逐轮过程可从 Git history 追溯；最终冻结证据集中于 Final Audit 与 Freeze Record。

Research Authority:
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Commit: 95e7fe78430d623c0240e9615f5f054515a90ce9
Path: RESEARCH_AUTHORITY_INDEX.md
Status: CURRENT INDEX; individual contracts retain scoped status
