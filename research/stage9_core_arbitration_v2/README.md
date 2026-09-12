# Stage 9 核心底层机制第二轮定向实证研究规范 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **最新状态**: `CLEAVE / CHAIN / SHARE / DISTRIBUTION / COUNTERATTACK CORE MECHANICS FROZEN; TAUNT RESEARCH COMPLETE, PENDING FINAL FREEZE AUDIT`  
> **可复现性声明**: **PARTIALLY REPRODUCIBLE FROM REPOSITORY; FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE**

本目录为三国志战略版战斗模拟系统（V2）Stage 9（核心底层机制裁决）的第二轮定向实证研究规范与可复现档案库。

在历史实证研究与提取器审计基础上，后续已对群攻（Cleave）、铁索连环（Chain）、分担（Damage Share）、分摊（Distribution）与反击（Counterattack）核心机制进行逐项人工确认，并分别建立独立冻结记录。嘲讽（Taunt）已完成专项机制探索与 40 项阶段性结论收敛，当前进入最终一致性审计。若旧统计解释与最新冻结记录/专项研究报告冲突，以最新冻结记录、通过审计的专项报告和总规为准。毕竟让同一个仓库同时相信两套互斥物理定律，多少有点奢侈。

---

## 一、目录核心导航

### 1. 核心规范、冻结记录与专项报告
- [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](STAGE9_CORE_ARBITRATION_RULES_V2.md): Stage 9 核心底层裁决主文件。
- [`STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`](STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md): 群攻核心机制冻结记录。
- [`STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`](STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md): 铁索连环核心机制冻结记录。
- [`STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md`](STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md): `690087 分担 / DAMAGE_SHARE` 正式实现合同。
- [`STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`](STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md): `690086 分摊 / DISTRIBUTION` 正式实现合同。
- [`STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md`](STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md): **`690085 反击 / COUNTERATTACK` 正式实现合同**，覆盖 NormalAttack-only 触发、精确时序、独立兵刃伤害、权限矩阵、多来源反击列表、同源刷新、批次快照、实时上下文、死亡边界与生命周期。
- [`STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md`](STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md): **`嘲讽 / TAUNT` 专项研究收敛报告**，覆盖唯一槽位、免疫准入、多源压制、来源死亡空挂、来源战法绑定、JIT 普攻索敌、混乱抢占、援护/突击事件目标继承、日志语义与 26 项最小测试矩阵。当前状态：`RESEARCH_COMPLETE_PENDING_FINAL_FREEZE_AUDIT`。
- [`STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md`](STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md): 历史实证提取器审计与修复报告。
- [`STAGE9_EVIDENCE_MATRIX_V2.md`](STAGE9_EVIDENCE_MATRIX_V2.md): 历史统计证据矩阵；若与后续直接冻结记录冲突，以冻结记录和总规为准。
- [`STAGE9_V2_CONSISTENCY_AUDIT.md`](STAGE9_V2_CONSISTENCY_AUDIT.md): 历史内部一致性审计表。
- [`STAGE9_V2_REPAIR_CHANGELOG.md`](STAGE9_V2_REPAIR_CHANGELOG.md): v2 修复与重评记录。
- [`STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md`](STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md): v1 到 v2 版本沿革。
- [`EXTRACTION_RUN_MANIFEST.json`](EXTRACTION_RUN_MANIFEST.json): 数据提取运行清单。

### 2. 八大专题报告
- [`R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md`](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md): 普攻生命周期与反应顺序。
- [`R2_TARGET_REDIRECT_AND_GUARD.md`](R2_TARGET_REDIRECT_AND_GUARD.md): 混乱 × 嘲讽、自援护与三级目标解耦。
- [`R3_DAMAGE_DERIVATION_PIPELINE.md`](R3_DAMAGE_DERIVATION_PIPELINE.md): Cleave / Chain 派生伤害 Pipeline 历史专题；Share / Distribution / Counterattack 的最终机制以对应 Freeze Record 为准。
- [`R4_RECURSION_PERMISSION_MATRIX.md`](R4_RECURSION_PERMISSION_MATRIX.md): 跨机制许可矩阵历史专题；Counter → Counter 现已由 Counterattack Freeze 正式冻结为 BLOCKED。
- [`R5_DEATH_TERMINATION_MATRIX.md`](R5_DEATH_TERMINATION_MATRIX.md): 死亡与终战模型。
- [`R6_MULTI_SOURCE_RULES.md`](R6_MULTI_SOURCE_RULES.md): 多来源冲突研究；Counterattack 多来源并存规则现以 Counterattack Freeze 为准。
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

## 二、当前 Stage 9 状态摘要

```text
Stage 8:
FROZEN

Stage 9 Cleave Core Mechanics:
FROZEN

Stage 9 Chain Core Mechanics:
FROZEN

Stage 9 Share Core Mechanics:
FROZEN

Stage 9 Distribution Core Mechanics:
FROZEN

Stage 9 Counterattack Core Mechanics:
FROZEN

Stage 9 Taunt Mechanics Research:
RESEARCH COMPLETE / PENDING FINAL FREEZE AUDIT

Next Core Research Target:
TAUNT FINAL CONSISTENCY AUDIT → NEXT STATE
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
no Evasion / Barrier / target-side modifier / Share / Distribution
no second Crit / FirstAid / Counter / Chain recursion
no Lifesteal / StrategyRecovery / standard hit-response callbacks
Normal / Skill / Periodic / Cleave / Counter damage can trigger Chain
Share / Distribution passive settlement cannot trigger Chain
PER-DAMAGE INSTANCE
PER-DAMAGE INLINE by default
normal-attack main-target Chain can be deferred until Cleave completes
```

### Share confirmed

```text
DAMAGE_SHARE is a unique-slot post-formula partition operator
Dsharer = round(Dtotal × R)
Dtarget = Dtotal - Dsharer
target-first commit
target death discards pending sharer loss
Share derived loss is attributed direct troop loss, not second DamageEvent
PER-DAMAGE INSTANCE live validation
DAMAGE_SHARE > DISTRIBUTION
```

### Distribution confirmed

```text
DISTRIBUTION inherits common DAMAGE_SHARE pipeline gates
but has its own partition topology and commit order
Dtarget = round(Dtotal × (1 - R))
Dtransfer = Dtotal - Dtarget
Dparticipant = round(Dtransfer / N)
participants evaluated at Damage-Time
participants Slot ASC first, target commits last
participant death does not abort remaining distribution
participant overflow discarded without redistribution
DAMAGE_SHARE > DISTRIBUTION
```

### Counterattack confirmed

```text
Trigger = ON_NORMAL_ATTACK_RECEIVED only
PER-NORMAL-ATTACK-INSTANCE
Counter damage is standard WEAPON EFFECT DAMAGE, not NormalAttack
Counter → Counter = BLOCKED
Counter → Assault = BLOCKED
Counter → Cleave = BLOCKED
Counter → Chain = ALLOWED
Crit / Weakness / Evasion / Resistance / Share / FirstAid / Lifesteal allowed
Counter uses independent weapon damage resolution, never incomingDamage × ratio
Counter executes after normal-attack-derived Cleave / Chain and before Assault / Combo next hit

counterStates = MULTI_INSTANCE_LIST
different sources coexist and all execute
same-source reapply = REFRESH
finite duration ticks at holder ACTION_START
False Report suppresses operational state without physical removal

CounterBatch eligibility is snapshotted at ON_NORMAL_ATTACK_RECEIVED
but each Counter microstep reads LIVE runtime world state
C1 killing original attacker does NOT cancel already-enqueued C2
queued C2 still emits Execute and commits 0 troop loss to already-dead target
original attacker death DOES cancel pending Assault / Combo / later owner-driven action
```

### Taunt research confirmed — pending final freeze audit

```text
TAUNT = NormalAttack primary-target override
UNIQUE_SLOT
first-come / same-level mutual exclusion / no refresh / no overwrite
Apply pipeline: Insight immunity → TAUNT slot conflict → register
existing Taunt + Insight → state-level SUPPRESSED
source-skill disabled → state-level SUPPRESSED
multi-suppressor set; only last suppressor removal resumes
SUPPRESSED duration continues; expiry/cleanse → REMOVED terminal state
source death does not remove Taunt; stale instance still occupies slot
source liveness checked JIT per NormalAttackInstance
source stun/disarm/silence-like action restriction does not disable existing Taunt
instant active-skill Taunt survives source's later active-skill silence
Confusion > Taunt > DefaultTargetSelector
Confusion shadows Taunt; does not suppress it
NormalAttack permission gate occurs before Taunt resolution
Combo creates new NormalAttackInstance and re-evaluates Taunt each hit
ActiveSkill / Counter / Cleave secondary targets do not read Taunt
Guard acts after Taunt intended-target selection
single-target Assault inherits post-Guard FinalEventTarget
FinalEventTarget dead before Assault effect → empty fire; no retarget
1 / 2 / 4-turn Taunts share one target-action-timeline duration model
```

---

## 三、仍待研究 / 审计的核心问题

```text
1. TAUNT final internal-consistency / wording / implementation-contract audit
2. stronger same-type control replacement outside TAUNT (TAUNT itself resolved: no strength hierarchy)
3. same-type multi-reaction execution ordering outside frozen Counter pairwise rules
4. remaining death atomic boundaries outside frozen Chain / Share / Distribution / Counter rules
5. strict combo transition-matrix statistical closure
6. exact universal Counter source comparator — DEFERRED_NON_BLOCKING
7. universal Counter Dispel semantics — DEFERRED_NON_BLOCKING
8. next functional state research target — after TAUNT freeze audit
```

当前 `690085 COUNTERATTACK / 反击` 已完成核心机制冻结，不再列为实现阻塞研究项。`TAUNT / 嘲讽` 已停止机制扩题，下一步仅做最终一致性审计与冻结转换。
