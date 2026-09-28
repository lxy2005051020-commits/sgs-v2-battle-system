# Stage 9 嘲讽 / TAUNT 最终一致性审计

Status ID: `690106`  
Official Name: `嘲讽`  
English Name: `TAUNT`  
Audit Status: `PASS`  
Freeze Readiness: `READY_FOR_FREEZE`  
Audit Date: `2026-09-13`

本审计针对 `STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md` 及其与 Stage 9 既有规范之间的交叉一致性进行最终检查。目标不是新增嘲讽机制，而是确认已有 40 项阶段性结论是否能够在同一状态机、同一普通攻击目标管线和同一 Stage 9 领域模型中同时成立，并清除旧研究文件中的术语漂移与证据分级混写。

---

## 1. 最终结论

```text
MECHANISM CONTRADICTIONS: 0 blocking
STATE-MACHINE CONTRADICTIONS: 0 blocking
TARGET-PIPELINE CONTRADICTIONS: 0 blocking
DURATION / OFF-BY-ONE BLOCKERS: 0
CROSS-CONTRACT BLOCKERS: 0
DOCUMENTATION TERMINOLOGY ISSUES: 2 found, repaired
EVIDENCE-PROVENANCE WORDING ISSUES: 1 found, repaired
FREEZE READINESS: PASS
```

结论：

> 嘲讽机制本体已经形成闭合、自洽、可实现、可测试的合同。审计中未发现需要重新开启机制研究的问题。发现的问题均属于旧文档术语或证据分级表达问题，已完成修订，不改变已确认的外部战斗行为。

本审计通过后，TAUNT 不再处于 `RESEARCH_COMPLETE_PENDING_FINAL_FREEZE_AUDIT`，而进入：

```text
AUDIT_PASSED_READY_FOR_FREEZE
```

---

## 2. 审计范围

直接核对以下规范：

```text
research/official_state_catalog_v1/OFFICIAL_STATE_CATALOG_V1.md
stages/stage9/research/core_arbitration_v2/STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md
stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md
stages/stage9/research/core_arbitration_v2/R2_TARGET_REDIRECT_AND_GUARD.md
stages/stage9/research/core_arbitration_v2/R6_MULTI_SOURCE_RULES.md
stages/stage9/research/core_arbitration_v2/STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md
stages/stage9/STATE_690098_GUARD_MECHANISM_CONTRACT.md
stages/stage9/research/core_arbitration_v2/README.md
research/README.md
```

同时审计报告中的：

```text
Apply Pipeline
Unique-slot conflict
Multi-suppressor lifecycle
Duration clock
REMOVED terminal semantics
source-death semantics
JIT normal-attack targeting
Confusion priority
Guard redirect
Assault EventTarget inheritance
Counter boundary
Cleave secondary-target boundary
Combo per-NormalAttackInstance behavior
log semantics
minimum test matrix
```

---

## 3. 官方状态语义核对 — PASS

官方目录：

```text
state_id = taunt
Hint ID = 690106
官方分类 = 控制状态
官方原文 = 控制状态，强迫目标的普通攻击以自身为目标
```

专项报告定义：

```text
TAUNT = NormalAttack Primary-Target Override
```

二者一致。

报告没有把嘲讽扩大为：

```text
通用战法目标锁定
反击目标锁定
群攻次级目标锁定
全局仇恨系统
```

因此官方定义边界核对通过。

---

## 4. Apply Pipeline 一致性 — PASS

最终顺序：

```text
Control Immunity Pre-Check
→ TAUNT unique-slot conflict
→ Register TauntInstance
```

审计确认：

```text
Insight active + slot empty
→ immunity reject

Insight active + old suppressed Taunt exists
→ immunity layer still short-circuits first

No Insight + old ACTIVE Taunt exists
→ slot conflict

No Insight + old SUPPRESSED Taunt exists
→ slot conflict

No Insight + source-dead stale Taunt exists
→ slot conflict
```

这与“物理实例存在”“状态是否 operational”“来源是否存活”三维解耦完全一致。

---

## 5. Unique Slot / 强度 / 刷新 — PASS WITH REPAIR

专项研究最终结论：

```text
TAUNT = UNIQUE_SLOT
First-Come, First-Served
same-level mutual exclusion
no refresh
no overwrite
no hidden stronger-taunt hierarchy in current rules
```

### 审计发现 A-01

旧 `R6_MULTI_SOURCE_RULES.md` 仍保留泛化结论：

```text
同类控制是否存在更强覆盖 → UNKNOWN
严禁绝对表述为不可覆盖
```

这在 R6 当时适用于未专项封口的控制状态，但与后续 TAUNT 专项结果发生版本漂移。

### 修复

R6 已改为：

```text
TAUNT = RESOLVED EXCEPTION
现有全部嘲讽同级，不覆盖、不刷新
其他尚未专项封口的控制状态仍保留 stronger replacement UNKNOWN
```

因此该冲突已消除。

---

## 6. 生命周期状态机 — PASS

最终状态机：

```text
ACTIVE ↔ SUPPRESSED
ACTIVE / SUPPRESSED → REMOVED
REMOVED = terminal
```

已确认：

```text
Insight 可加入 suppressor
SOURCE_SKILL_DISABLED 可加入 suppressor
first suppressor: ACTIVE → SUPPRESSED
remove non-last suppressor: remain SUPPRESSED
remove last suppressor: SUPPRESSED → ACTIVE
expiration / cleanse: → REMOVED
REMOVED 后不得 resume / resurrect
```

来源死亡不属于 `ACTIVE / SUPPRESSED / REMOVED` 状态迁移，而是独立 runtime source-validity 维度。

混乱也不属于 lifecycle suppressor，而属于 TargetSelector priority 维度。

无状态机闭环冲突。

---

## 7. 混乱 × 嘲讽术语一致性 — PASS WITH REPAIR

最终机制：

```text
Confusion = ACTIVE
Taunt = ACTIVE

NormalAttack JIT target priority:
ConfusionTargetSelector
>
TauntTargetSelector
>
DefaultTargetSelector
```

混乱不会触发：

```text
嘲讽暂时失效
嘲讽继续生效
```

### 审计发现 A-02

旧 `R2_TARGET_REDIRECT_AND_GUARD.md` 和 Stage 9 总规使用了“混乱压制嘲讽”这一旧术语。其原意只是“目标选择结果上混乱优先”，但 `SUPPRESSED` 已在 TAUNT 专项研究中成为具有明确生命周期含义的正式术语，因此继续使用“压制”会造成实现歧义。

### 修复

R2 已改为：

```text
Confusion target-selector preemption / shadowing
!=
Taunt lifecycle SUPPRESSION
```

TAUNT 正式规范统一使用“抢占 / shadowing”。

Stage 9 总规中若仍出现历史“压制”字样，应按本审计解释为 selector preemption；正式冻结转换时应同步替换为“抢占”，不得据此实现 `TauntState = SUPPRESSED`。

---

## 8. Duration / TurnStart / off-by-one — PASS

最终模型：

```text
DurationClock = target action timeline
```

确认：

```text
1 / 2 / 4 回合嘲讽共享同一模型
目标被震慑仍消耗行动时间窗
SUPPRESSED 不暂停 duration
自然到期发生物理 REMOVED
自然到期立即释放 TAUNT slot
```

报告已经显式禁止：

```python
remaining -= 1
if remaining <= 0:
    remove()
```

这种未经锚点设计的裸前置递减模型。

推荐：

```text
expireAtTargetTurnOrdinal
```

或等价已消费行动窗口模型。

审计未发现 1 回合状态提前消失的 off-by-one 自相矛盾。

---

## 9. 来源死亡与来源自身控制 — PASS

来源死亡：

```text
TauntInstance remains
slot remains occupied
duration continues
runtime source-alive check fails
no Taunt execute log
normal attack falls back to default selector
```

来源自身震慑 / 缴械 / 计穷 / 虚弱：

```text
不等价于 sourceSkill disabled
不删除旧 Taunt
不自动 suppress 旧 Taunt
```

当前仓库关键直接样本索引以“来源震慑”为代表；专项研究结论对其他来源自身行为限制维度继续成立，但报告已增加证据分级说明，避免把代表样本包装成每一种限制状态都存在同等级直接切片。

---

## 10. Source Skill Binding — PASS

已区分：

```text
persistent/sustained source-skill binding
vs
instant active-skill-created TauntInstance
```

前者：

```text
sourceSkill disabled by False Report
→ existing Taunt SUPPRESSED
→ sourceSkill restored
→ existing Taunt may resume if still present and no other suppressor
```

后者：

```text
active skill successfully created Taunt
→ source later gets active-skill Silence
→ old Taunt remains independent
```

并且：

```text
source skill is not a polling aura
REMOVED Taunt is never recreated by old sourceSkill
```

无 lifecycle resurrection 冲突。

---

## 11. JIT 目标解析 — PASS WITH PROVENANCE REPAIR

正式规则：

```text
NormalAttack permission
→ JIT target resolution
→ Confusion
→ Taunt
→ Default
→ Guard
→ final actual target
```

直接连续日志已经证明：

```text
ActionStart Taunt active
→ active-skill phase gains Insight
→ Taunt temporarily invalid
→ same-action normal attack no longer follows old Taunt
```

### 审计发现 A-03

旧报告把：

```text
行动中获得洞察
行动中净化删除 Taunt
```

并列写成同等级实证，容易让读者误以为都已有直接连续战报切片。

### 修复

主报告现已明确区分：

```text
Insight mid-action case = DIRECT LOG FACT
Cleanse-before-normal-attack case = JIT + REMOVED composed mechanism conclusion
```

两者的模拟器预期一致，但证据层级不同。

---

## 12. Guard / Assault / EventTarget — PASS

目标身份：

```text
IntendedTarget
→ Guard redirect
→ FinalAttackTarget / actualTarget
→ EventTarget
```

若 Taunt 锁定 A，而 C 援护 A：

```text
IntendedTarget = A
FinalAttackTarget = C
EventTarget = C
```

随后单体 Assault：

```text
inherits C
```

若 C 已在普攻中死亡：

```text
Assault remains bound to C
→ empty-fire / invalid target
→ no fallback to A
→ no fresh random selector
```

与 `stages/stage9/STATE_690098_GUARD_MECHANISM_CONTRACT.md` 的动作级目标重定向模型一致。

---

## 13. Counter / Cleave / Combo 边界 — PASS

### Counter

```text
Counter.target = triggering normal attacker
Counter is not NormalAttack
Taunt does not redirect Counter
```

与 Counterattack Freeze 一致。

### Cleave

```text
Taunt controls normal-attack primary target only
Cleave secondary targets use Cleave's own target rules
```

无二次 Taunt selector。

### Combo

```text
Combo next hit = new NormalAttackInstance
```

因此每刀独立：

```text
permission
JIT Taunt
Guard
post-hit lifecycle
```

第一刀造成来源死亡后，第二刀重新读取世界状态并跳过旧 Taunt，与 JIT 模型一致。

---

## 14. 日志语义 — PASS

正式区分：

```text
效果已施加
= physical registration

暂时失效
= ACTIVE → SUPPRESSED

继续生效
= SUPPRESSED → ACTIVE after last suppressor removal

执行来自【...】的「嘲讽」效果
= this NormalAttackInstance actually used TauntTargetOverride

效果已消失
= physical REMOVED + slot release
```

审计确认不存在把：

```text
resume
execute
exist
slot occupied
source alive
```

错误合并成同一布尔概念的情况。

---

## 15. 最小测试矩阵审计 — PASS

主报告 26 项测试覆盖：

```text
basic execute
same-type conflict
source death
Insight suppress / immunity
multi-suppressor
expiry while suppressed
cleanse while suppressed
Confusion preemption
Disarm permission gate
Combo per-hit JIT
mid-action state change
Counter boundary
Cleave boundary
Guard redirect
Assault inheritance
Assault dead EventTarget
source action restrictions
active-skill source silence independence
1/2/4 turn duration
```

测试矩阵覆盖所有冻结候选核心不变量，没有发现关键状态迁移或目标管线分支完全遗漏。

---

## 16. 可复现性边界

完整原始战报数据库未随仓库存储，因此：

```text
FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE
```

仓库当前可复现性属于：

```text
PARTIALLY REPRODUCIBLE FROM REPOSITORY
```

这不是机制阻塞项，但冻结记录不得虚构“所有原始日志已入库”。

关键战报文件名、历史 Stage 9 evidence 包与专项报告中的直接样本索引共同构成当前证据入口。

---

## 17. 冻结门禁裁决

全部阻塞门禁：

| Gate | Result |
|---|---|
| Official semantic match | PASS |
| Apply ordering | PASS |
| Same-type slot semantics | PASS |
| Lifecycle closure | PASS |
| Multi-suppressor closure | PASS |
| Duration/off-by-one | PASS |
| Source death | PASS |
| Source skill binding | PASS |
| JIT target resolution | PASS |
| Confusion interaction | PASS |
| Guard/Assault target identity | PASS |
| Counter/Cleave/Combo boundaries | PASS |
| Log semantics | PASS |
| Test coverage | PASS |
| Cross-document contradiction | PASS after repairs |

最终裁决：

```text
TAUNT FINAL CONSISTENCY AUDIT = PASS
TAUNT FREEZE READINESS = READY
```

下一步不再研究新嘲讽问题，只进行正式冻结转换：

```text
create STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md
mark TAUNT = FROZEN
update Stage 9 / research indexes
```
