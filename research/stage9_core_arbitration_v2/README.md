# Stage 9 核心底层机制第二轮定向实证研究规范 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **最新状态**: `CLEAVE / CHAIN CORE MECHANICS FROZEN`  
> **可复现性声明**: **PARTIALLY REPRODUCIBLE FROM REPOSITORY; FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE**

本目录为三国志战略版战斗模拟系统（V2）Stage 9（核心底层机制裁决）的第二轮定向实证研究规范与可复现档案库。

在历史实证研究与提取器审计基础上，后续已对群攻（Cleave）与铁索连环（Chain）核心机制进行逐项人工确认，并分别建立独立冻结记录。若旧统计解释与最新冻结记录冲突，以最新冻结记录和总规为准。毕竟让同一个仓库同时相信两套互斥物理定律，多少有点奢侈。

---

## 一、 目录核心导航

### 1. 核心规范与冻结记录
- [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](STAGE9_CORE_ARBITRATION_RULES_V2.md): Stage 9 核心底层裁决主文件，已同步 Cleave / Chain 冻结状态。
- [`STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`](STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md): 群攻核心机制冻结记录。
- [`STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`](STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md): **铁索连环核心机制冻结记录**，覆盖反馈基数、TRUE_FEEDBACK、许可矩阵、Inline / Deferred 时序、多目标传播、状态覆盖、归属、死亡、净化与 duration 生命周期。
- [`STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md`](STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md): 历史实证提取器审计与修复报告；后续独立审计仍要求对状态存在与 Reaction Execution 语义分离做最终复核。
- [`STAGE9_EVIDENCE_MATRIX_V2.md`](STAGE9_EVIDENCE_MATRIX_V2.md): 历史统计证据矩阵。若与后续直接冻结记录冲突，以冻结记录和总规为准。
- [`STAGE9_V2_CONSISTENCY_AUDIT.md`](STAGE9_V2_CONSISTENCY_AUDIT.md): 历史内部一致性审计表。
- [`STAGE9_V2_REPAIR_CHANGELOG.md`](STAGE9_V2_REPAIR_CHANGELOG.md): v2 修复与重评记录。
- [`STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md`](STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md): v1 到 v2 版本沿革。
- [`EXTRACTION_RUN_MANIFEST.json`](EXTRACTION_RUN_MANIFEST.json): 数据提取运行清单。

### 2. 八大专题报告
- [`R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md`](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md): 普攻生命周期与反应顺序。
- [`R2_TARGET_REDIRECT_AND_GUARD.md`](R2_TARGET_REDIRECT_AND_GUARD.md): 混乱 × 嘲讽、自援护与三级目标解耦。
- [`R3_DAMAGE_DERIVATION_PIPELINE.md`](R3_DAMAGE_DERIVATION_PIPELINE.md): **Cleave / Chain 派生伤害 Pipeline 已同步冻结**；Share 数学与致死边界仍待下一专题。
- [`R4_RECURSION_PERMISSION_MATRIX.md`](R4_RECURSION_PERMISSION_MATRIX.md): **已同步 Cleave / Chain / Share Damage 跨机制许可矩阵**。
- [`R5_DEATH_TERMINATION_MATRIX.md`](R5_DEATH_TERMINATION_MATRIX.md): 9 层死亡与终战模型。
- [`R6_MULTI_SOURCE_RULES.md`](R6_MULTI_SOURCE_RULES.md): 多来源冲突研究；Chain 单实例覆盖规则已由 Chain Freeze 单独确定。
- [`R7_RNG_AND_DETERMINISM.md`](R7_RNG_AND_DETERMINISM.md): 连击目标重选与 RNG 研究。
- [`R8_PROVENANCE_MODEL.md`](R8_PROVENANCE_MODEL.md): 原生日志事实、重构因果模型与工程字段分层。

### 3. 可复现性证据包与基础设施
- [`evidence/MANIFEST.md`](evidence/MANIFEST.md): 证据包清单与本地复现指南。
- [`evidence/lib/`](evidence/lib/): 提取器基础设施核心库。
- [`evidence/tests/`](evidence/tests/): 自动化 QA 测试套件。
- [`evidence/RAW_BATTLE_HASH_MANIFEST.csv`](evidence/RAW_BATTLE_HASH_MANIFEST.csv): 原始战报哈希清单。
- [`evidence/CLAIM_EVIDENCE_INDEX.csv`](evidence/CLAIM_EVIDENCE_INDEX.csv): 断言与战报区间映射。
- `evidence/raw_slices/*.json`: 关键原始切片。
- `evidence/*.py`: 数据提取与验证脚本。
- `evidence/*.json`: 结构化证据集。

---

## 二、 当前 Stage 9 状态摘要

```text
Stage 8:
FROZEN

Stage 9 Cleave Core Mechanics:
FROZEN

Stage 9 Chain Core Mechanics:
FROZEN

Next Core Research Target:
SHARE / 分担
```

### Cleave confirmed

```text
Main final damage × cleave ratio
no second base formula
Evasion allowed
Barrier allowed and consumes one charge
no target-side damage modifier re-entry
Share allowed
FirstAid allowed
Counter blocked
Cleave recursion blocked
Chain allowed from Cleave damage
DamageType inherited
weapon cleave can trigger lifesteal
strategy cleave can trigger strategy recovery
```

### Chain confirmed

```text
TriggerNodeResolvedDamage × current trigger-node ChainRatio
TRUE_FEEDBACK type
0-damage legal resolution can execute Chain with 0 feedback
trigger node dead after source damage → no propagation
no Evasion
no Barrier
no target-side damage modifier
no Share
no second Crit
no FirstAid
no Counter
no Chain recursion
no Lifesteal / StrategyRecovery
no 刚烈不屈 or other hit-response callbacks

Normal / Skill / Periodic / Cleave / Counter damage can trigger Chain
Share passive settlement cannot trigger Chain
PER-DAMAGE INSTANCE
PER-DAMAGE INLINE by default
normal-attack main-target Chain is deferred until Cleave completes
Deferred Chain revalidates source alive + current state
Deferred base damage is fixed, current owner/ratio are read at execution time

same-camp only
slot 0 → slot 1 → slot 2
JIT target revalidation
broadcast full ratio to every legal target
one target death does not stop remaining targets

single active Chain instance per unit
same-source reapply refreshes to 2 turns
different-source reapply overwrites with later owner/ratio and refreshes to 2 turns
Chain damage / kill belong to trigger node's current effect owner
owner death does not remove already-applied Chain
owner-dead self-heal benefit is discarded

duration ticks at target ACTION_START
expiry happens before periodic damage at that ACTION_START
stun does not stop duration tick
cleanse removes Chain immediately
reapply after cleanse creates a new instance

applied troop loss = min(calculated feedback, current troops)
damage statistics use applied troop loss
```

---

## 三、 仍待研究 / 审计的核心问题

```text
1. Share / 分担核心数学与完整 Pipeline
2. Counter → Counter 最终提取器语义复核
3. stronger same-type control replacement
4. same-type multi-reaction execution ordering
5. remaining death atomic boundaries outside frozen Chain rules
6. strict combo transition-matrix statistical closure
```

**下一状态研究目标：`Share / 分担`。**
