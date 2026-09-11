# Stage 9 核心底层机制第二轮定向实证研究规范 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **最新状态**: `REPAIRED & CONSISTENT (READY FOR AUDIT)`  
> **可复现性声明**: **PARTIALLY REPRODUCIBLE FROM REPOSITORY; FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE**

本目录为三国志战略版战斗模拟系统（V2）Stage 9（核心底层机制裁决）的**第二轮定向实证研究规范与可复现档案库**。

针对第一轮探索性研究（v1）与第二轮初次交付中发现的内部矛盾、过度绝对化表述与评级虚高问题，本版本完成了彻底的一致性修复（Consistency Repair）与证据等级真实核定（Evidence Regrade）。

---

## 一、 目录核心导航

### 1. 核心规范与汇总报告
- [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](STAGE9_CORE_ARBITRATION_RULES_V2.md): **Stage 9 核心底层裁决规范主文件**（包含 12 项公共底层规则的统一定论与 Stage 8 边界说明）。
- [`STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md`](STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md): **实证提取器全面审计与修复报告**（模块化解析器 `evidence/lib/`、10/10 QA 单元测试、全量重提取、0.00% 抽检错误率与最终 PASS 判定）。
- [`STAGE9_EVIDENCE_MATRIX_V2.md`](STAGE9_EVIDENCE_MATRIX_V2.md): **证据等级评级矩阵**（覆盖 26 项核心断言：14 项 A 级，8 项 B 级，4 项 C 级，严禁虚构评级）。
- [`STAGE9_V2_CONSISTENCY_AUDIT.md`](STAGE9_V2_CONSISTENCY_AUDIT.md): **内部结论一致性审计表**（逐项对照 R 报告、总规、矩阵与 README，消灭互斥断言）。
- [`STAGE9_V2_REPAIR_CHANGELOG.md`](STAGE9_V2_REPAIR_CHANGELOG.md): **v2 内部修复与重评详细记录**（BF-01 ~ BF-09 逐条修复闭环及提取器全面审计重构）。
- [`STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md`](STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md): **v1 到 v2 早期版本沿革记录**。
- [`EXTRACTION_RUN_MANIFEST.json`](EXTRACTION_RUN_MANIFEST.json): **数据提取全量运行清单**（记录提取时间戳、输入候选数、有效/排除分母与输出哈希）。

### 2. 八大专题深入实证报告
- [`R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md`](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md): 普攻生命周期、五类反应术语统一（受击回调/群攻/反击/突击/连击）与绝地反击反例排查。
- [`R2_TARGET_REDIRECT_AND_GUARD.md`](R2_TARGET_REDIRECT_AND_GUARD.md): 混乱 × 嘲讽判定冲突定向实证（1,351 例）、自援护发现与三级目标解耦模型。
- [`R3_DAMAGE_DERIVATION_PIPELINE.md`](R3_DAMAGE_DERIVATION_PIPELINE.md): 群攻、铁索与分担的基数模型（fixed derived base + target modifier）及致死分担观察事实。
- [`R4_RECURSION_PERMISSION_MATRIX.md`](R4_RECURSION_PERMISSION_MATRIX.md): 补充有效机会分母后的递归许可矩阵（区分 BLOCKED 与 NOT OBSERVED）。
- [`R5_DEATH_TERMINATION_MATRIX.md`](R5_DEATH_TERMINATION_MATRIX.md): 9 层死亡与终战模型（区分立即硬短路与多目标原子循环延迟终战）。
- [`R6_MULTI_SOURCE_RULES.md`](R6_MULTI_SOURCE_RULES.md): 控制状态先占排斥（cfg 23）实证与更强效果覆盖未知说明。
- [`R7_RNG_AND_DETERMINISM.md`](R7_RNG_AND_DETERMINISM.md): 连击第二击多维正交分层统计（34,639 对）与独立均匀 1/K 索敌定律。
- [`R8_PROVENANCE_MODEL.md`](R8_PROVENANCE_MODEL.md): 原生日志事实（平铺事件）、重构因果模型与模拟器工程字段的三层绝对分离。

### 3. 可复现性证据包与基础设施
- [`evidence/MANIFEST.md`](evidence/MANIFEST.md): 证据包清单、数据说明与本地复现指南。
- [`evidence/lib/`](evidence/lib/): **提取器基础设施核心库**（`unit_identity`, `state_tracker`, `target_pool`, `action_segmenter`, `battle_parser`, `evidence_utils`）。
- [`evidence/tests/`](evidence/tests/): **提取器自动化 QA 测试套件**（10/10 单元测试全部通过）。
- [`evidence/RAW_BATTLE_HASH_MANIFEST.csv`](evidence/RAW_BATTLE_HASH_MANIFEST.csv): 核心断言依赖战报的 SHA-256 哈希值清单。
- [`evidence/CLAIM_EVIDENCE_INDEX.csv`](evidence/CLAIM_EVIDENCE_INDEX.csv): 核心断言与战报事件起止区间的精确映射索引。
- `evidence/raw_slices/*.json`: 关键断言的真实战报原生切片（供无原始库环境下独立核验）。
- `evidence/*.py`: 全自动战报数据挖掘、重提取与双重抽检验证脚本。
- `evidence/*.json`: 清洗后的结构化证据数据集与抽检报告。
