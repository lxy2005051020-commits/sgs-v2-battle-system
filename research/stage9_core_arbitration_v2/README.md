# Stage 9 核心底层机制第二轮定向实证研究规范 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **最新状态**: `REPAIRED & CONSISTENT; CLEAVE CORE MECHANICS FROZEN`  
> **可复现性声明**: **PARTIALLY REPRODUCIBLE FROM REPOSITORY; FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE**

本目录为三国志战略版战斗模拟系统（V2）Stage 9（核心底层机制裁决）的第二轮定向实证研究规范与可复现档案库。

针对第一轮探索性研究（v1）与第二轮初次交付中发现的内部矛盾、过度绝对化表述与评级虚高问题，本版本完成了彻底的一致性修复（Consistency Repair）与证据等级真实核定（Evidence Regrade）。后续又对群攻（Cleave）核心机制进行了逐项人工确认，并建立独立冻结记录。

---

## 一、 目录核心导航

### 1. 核心规范与汇总报告
- [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](STAGE9_CORE_ARBITRATION_RULES_V2.md): **Stage 9 核心底层裁决规范主文件**（包含 12 项公共底层规则、群攻冻结同步与 Stage 8 边界说明）。
- [`STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`](STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md): **群攻核心机制冻结记录**（伤害基数、规避、抵御、分担、急救、递归阻断、DamageType 与倒戈/攻心边界）。
- [`STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md`](STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md): **实证提取器审计与修复报告**。注意：后续独立审计仍要求对状态存在与 Reaction Execution 的语义分离做最终复核。
- [`STAGE9_EVIDENCE_MATRIX_V2.md`](STAGE9_EVIDENCE_MATRIX_V2.md): **证据等级评级矩阵**（历史统计证据矩阵；若与后续直接冻结记录冲突，以更新后的机制冻结记录和总规为准，并应在下一轮一致性审计中统一收口）。
- [`STAGE9_V2_CONSISTENCY_AUDIT.md`](STAGE9_V2_CONSISTENCY_AUDIT.md): **内部结论一致性审计表**。
- [`STAGE9_V2_REPAIR_CHANGELOG.md`](STAGE9_V2_REPAIR_CHANGELOG.md): **v2 内部修复与重评详细记录**。
- [`STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md`](STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md): **v1 到 v2 早期版本沿革记录**。
- [`EXTRACTION_RUN_MANIFEST.json`](EXTRACTION_RUN_MANIFEST.json): **数据提取全量运行清单**。

### 2. 八大专题深入实证报告
- [`R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md`](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md): 普攻生命周期、五类反应术语统一与反应顺序。
- [`R2_TARGET_REDIRECT_AND_GUARD.md`](R2_TARGET_REDIRECT_AND_GUARD.md): 混乱 × 嘲讽、自援护与三级目标解耦模型。
- [`R3_DAMAGE_DERIVATION_PIPELINE.md`](R3_DAMAGE_DERIVATION_PIPELINE.md): **群攻核心 Pipeline 已同步冻结**；铁索与致死分担边界继续保持独立研究状态。
- [`R4_RECURSION_PERMISSION_MATRIX.md`](R4_RECURSION_PERMISSION_MATRIX.md): **已同步 Cleave→Cleave / Cleave→Counter / Share Damage 递归阻断规则**；Counter / Chain 自递归仍待最终提取器语义复核。
- [`R5_DEATH_TERMINATION_MATRIX.md`](R5_DEATH_TERMINATION_MATRIX.md): 9 层死亡与终战模型。
- [`R6_MULTI_SOURCE_RULES.md`](R6_MULTI_SOURCE_RULES.md): 控制状态先占排斥与更强效果覆盖未知说明。
- [`R7_RNG_AND_DETERMINISM.md`](R7_RNG_AND_DETERMINISM.md): 连击第二击多维分层统计与目标重选模型。
- [`R8_PROVENANCE_MODEL.md`](R8_PROVENANCE_MODEL.md): 原生日志事实、重构因果模型与模拟器工程字段的三层分离。

### 3. 可复现性证据包与基础设施
- [`evidence/MANIFEST.md`](evidence/MANIFEST.md): 证据包清单、数据说明与本地复现指南。
- [`evidence/lib/`](evidence/lib/): **提取器基础设施核心库**（`unit_identity`, `state_tracker`, `target_pool`, `action_segmenter`, `battle_parser`, `evidence_utils`）。
- [`evidence/tests/`](evidence/tests/): **提取器自动化 QA 测试套件**。
- [`evidence/RAW_BATTLE_HASH_MANIFEST.csv`](evidence/RAW_BATTLE_HASH_MANIFEST.csv): 核心断言依赖战报的 SHA-256 哈希值清单。
- [`evidence/CLAIM_EVIDENCE_INDEX.csv`](evidence/CLAIM_EVIDENCE_INDEX.csv): 核心断言与战报事件起止区间映射索引。
- `evidence/raw_slices/*.json`: 关键断言的真实战报原生切片。
- `evidence/*.py`: 战报数据挖掘、重提取与验证脚本。
- `evidence/*.json`: 清洗后的结构化证据数据集与抽检报告。

---

## 二、 当前 Stage 9 状态摘要

```text
Stage 8: FROZEN

Stage 9 Cleave Core Mechanics:
FROZEN

Cleave confirmed:
- Main final damage × cleave ratio
- no second base formula
- evasion allowed
- barrier allowed and consumes one charge
- no target-side damage increase/reduction re-entry
- share allowed
- first aid allowed
- counter blocked
- cleave recursion blocked
- damage type inherited
- weapon cleave can trigger lifesteal
- strategy cleave can trigger strategy recovery
- share damage is passive numeric settlement and does not reopen hit reactions

Still pending outside Cleave:
- Counter self-recursion final extractor audit
- Chain self-recursion / pipeline boundary
- stronger same-type control replacement
- same-type multi-reaction ordering
- remaining death atomic boundaries
- strict combo transition-matrix statistical closure
```
