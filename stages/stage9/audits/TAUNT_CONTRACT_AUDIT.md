# TAUNT Contract Audit

Status ID: `690106`  
Mechanism: `TAUNT / 嘲讽`  
Audit Type: `Stage 9 Frozen Contract Independent Review`  
Audit Date: `2026-09-13`

> 本审计不重新研究 TAUNT，不重新扫描全量战报。审计目标仅为复核当前 P0 Frozen Contract 的内部闭环、与其他更新 P0 合同的交叉一致性、Stage 8 兼容性、死亡边界与文档漂移，并判断其是否可直接进入 Stage 9 runtime 设计。

---

## 1. Repository Baseline

本轮开始时重新读取远端 `main`，未沿用上一轮 baseline。

```text
sgs-v2-battle-system
exact main HEAD = d4f4c8f4560fed662319272cd10d70be0545087b
audit(stage9): verify confusion frozen contract

sgs-state-mechanics-research
exact main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
docs(index): mark combo frozen and scope death baseline
```

写入前再次读取两个远端 `main`，HEAD 均未变化，因此本审计完整基于上述 exact baseline。

上一轮：

```text
stages/stage9/audits/CONFUSION_CONTRACT_AUDIT.md
```

已读取并继承其 finding：

```text
CFS9-B01
CONFUSION holder-death hard termination
vs
COMBO ACTOR_DEATH_DURING_OWN_OPEN_ACTION exception
Status = OPEN
```

当前主仓 HEAD 正是上一轮 CONFUSION 审计提交，仓库中没有后续正式修复或 re-freeze，因此本轮不得把 `CFS9-B01` 视为关闭。

本轮只判断该开放 blocker 是否产生新的 TAUNT-specific 合同矛盾，不重新研究 `CFS9-B01` 本身。

---

## 2. Authoritative Freeze Source

### 2.1 TAUNT P0 source

当前 TAUNT 最高权威实现合同：

```text
stages/stage9/research/core_arbitration_v2/
STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md
```

当前 blob：

```text
d3c370a2f693a03ff4f435e8750678264348fc0d
```

正式 Freeze Record 初始冻结提交：

```text
14397caab46356fc4615ea715da31c53780730ff
docs(stage9): freeze taunt core mechanics
```

随后总规正式同步 TAUNT 为 FROZEN：

```text
2f2dfe62942601664e123dea38e0bc2ab03254a4
docs(stage9): freeze taunt in core arbitration rules
```

当前路径由 Stage 目录整理提交迁移：

```text
83a7a44374399efed01dacc1e869b724089201c4
chore: organize stage artifacts into dedicated stage folders
```

路径迁移未改变当前 Freeze Record 的冻结语义。

### 2.2 P1 audit source

```text
stages/stage9/research/core_arbitration_v2/
STAGE9_TAUNT_FINAL_CONSISTENCY_AUDIT.md

blob = 992be660a19752c46358d8dfee23b9e0e904b6b9
Audit Status = PASS
Freeze Readiness = READY_FOR_FREEZE
```

P1 已审计 Apply Pipeline、unique slot、lifecycle、duration、source death、Confusion、Guard、Counter、Cleave、Combo、Assault 与日志语义，并在正式冻结前修复了 R2/R6 的旧术语漂移。

### 2.3 Supporting sources read

本轮同时读取：

```text
STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md
STAGE9_CORE_ARBITRATION_RULES_V2.md
R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
R2_TARGET_REDIRECT_AND_GUARD.md
R5_DEATH_TERMINATION_MATRIX.md
R6_MULTI_SOURCE_RULES.md
R7_RNG_AND_DETERMINISM.md
R8_PROVENANCE_MODEL.md

STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md
STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md
STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md
STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md
STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md
stages/stage9/STATE_690098_GUARD_MECHANISM_CONTRACT.md

states/control/confusion/MECHANISM_CONTRACT.md
states/functional/combo/MECHANISM_CONTRACT.md
```

### 2.4 Authority decision

```text
AUTHORITATIVE CONTRACT
=
stages/stage9/research/core_arbitration_v2/
STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md
@ blob d3c370a2f693a03ff4f435e8750678264348fc0d
```

P1 audit 与 Research Report 是解释与证据支持层，不得覆盖 P0 Freeze Record。

状态研究仓当前没有独立的 `states/control/taunt/MECHANISM_CONTRACT.md` P0 镜像。TAUNT 的状态仓材料仍停留在 `minimum_usable` skeleton，因此不能与主仓 P0 并列。

---

## 3. Superseded / Stale Sources

### 3.1 State-research minimum skeleton

```text
sgs-state-mechanics-research/
states/control/minimum_usable/690106_TAUNT.md
```

状态：

```text
SUPERSEDED SKELETON
```

它只表达“普攻目标被强制指定为嘲讽来源”等最小语义，不包含当前已冻结的 unique slot、multi-suppressor、source-death stale slot、JIT source liveness、duration、Confusion shadowing、Guard、Combo 等完整合同。

### 3.2 State mechanics index

当前：

```text
690106 TAUNT = MINIMUM_USABLE
```

而主仓 P0 已正式：

```text
690106 TAUNT = FROZEN
```

判定：

```text
DOC_DRIFT
```

不得因此降低 TAUNT 机制状态。

### 3.3 `core_arbitration_v2/README.md`

README 已正确写明：

```text
Stage 9 Taunt Core Mechanics = FROZEN
```

所以 TAUNT 自身 freeze status 已同步。

但同一文件仍保留：

```text
Next Core Research Target = 690103 CONFUSION
690103 CONFUSION / 690081 COMBO 仍待研究
```

以及旧 Counter 摘要中的：

```text
original attacker death DOES cancel pending ... Combo
```

后者已被更新的 COMBO P0 `ACTOR_DEATH_DURING_OWN_OPEN_ACTION` 例外推翻。

判定：

```text
PARTIALLY STALE / DOC_DRIFT
```

### 3.4 `STAGE9_EVIDENCE_MATRIX_V2.md`

矩阵仍主要停留在历史统计证据层：

```text
EM-01 Confusion × Taunt = 历史 A
EM-20 反击致死后续 Combo 短路 = 历史 A
EM-25 Combo 重索敌 = B+ / strong
```

并且“当前研究状态”仍只把 Cleave / Chain 标成 FROZEN、Share 标成 next target。

这些内容可继续作为历史 evidence trace，但不能覆盖后续 TAUNT / CONFUSION / COMBO 等 P0 Frozen Contract。

判定：

```text
STALE FOR CURRENT CONTRACT STATUS / DOC_DRIFT
```

### 3.5 Death-boundary lower-authority docs

以下低优先级材料仍保留旧“行动者死亡后中止当前/后续 Combo”的一般化表述：

```text
R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
R5_DEATH_TERMINATION_MATRIX.md
sgs-state-mechanics-research/README.md
```

而当前状态仓 `STATE_MECHANICS_INDEX.md` 已经正确加入：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ do not immediately clear existing status slots
→ continue current action until cfg 733
```

因此旧 R1/R5/root README 在该特定边界上属于 superseded / stale，不得覆盖 COMBO P0。

### 3.6 `stages/stage9/research/README.md`

当前 Stage 目录下不存在该文件；`stages/stage9/research/` 只有 `core_arbitration_v1/` 与 `core_arbitration_v2/`。历史 P1 审计中提到的 `research/README.md` 不构成当前 Stage9 权威入口。

---

## 4. State Kernel Audit

P0 冻结核心：

```text
TAUNT = NormalAttack Primary-Target Override
```

其职责严格限于：

```text
新的 NormalAttackInstance
→ primary intended target selection
```

明确不是：

```text
Damage Redirect
Damage Transfer
Universal Target Override
ActiveSkill Target Override
Counter Target Override
Cleave Secondary Target Override
Post-hit Reaction
```

普通攻击目标选择优先级统一为：

```text
ConfusionTargetSelector
>
TauntTargetSelector
>
DefaultTargetSelector
```

并位于 GUARD 之前：

```text
NormalAttack permission
↓
JIT Target Resolution
  Confusion branch if applicable
  ↓ else
  Taunt forced intended target if operational
  ↓ else
  Default selector
↓
intended / pre_redirect_target
↓
GUARD / COVER
↓
post_redirect_attack_target / actualTarget
```

结果：

```text
PASS
```

P0 与 P1、R2、GUARD contract、CONFUSION P0 的阶段划分一致。

---

## 5. Lifecycle Audit

### 5.1 Container and reapplication

P0：

```text
Container = UNIQUE_SLOT
First-Come, First-Served
same-level mutual exclusion
Refresh = DISALLOWED
Overwrite = DISALLOWED
```

同一 holder 最多物理存在一个 `TauntInstance`。

Apply Gate：

```text
ApplyTauntRequest
→ Insight immunity pre-check
→ existing TAUNT slot conflict
→ register instance
```

因此：

```text
existing Taunt + Insight active
→ 新 Taunt 在 immunity gate 直接失败
→ 不是因为旧 slot 被覆盖或刷新
```

已有 Taunt 后获得 Insight：

```text
existing Taunt
→ INSIGHT suppressor added
→ ACTIVE → SUPPRESSED
```

这是“已有实例被压制”，与“新 Apply 被免疫拒绝”两个不同层级。

### 5.2 Suppression

至少冻结两个 suppressor：

```text
INSIGHT
SOURCE_SKILL_DISABLED
```

状态机：

```text
ACTIVE ↔ SUPPRESSED
ACTIVE / SUPPRESSED → REMOVED
REMOVED = terminal
```

多压制源规则：

```text
first suppressor added
→ ACTIVE → SUPPRESSED

remove one but others remain
→ stay SUPPRESSED

remove last suppressor
→ SUPPRESSED → ACTIVE
```

同时：

```text
SUPPRESSED duration continues
expiry / cleanse while SUPPRESSED
→ REMOVED terminal
```

所以：

```text
SUPPRESSED != REMOVED
```

### 5.3 Slot occupancy invariant

冻结强不变量：

```text
只要 TauntInstance 物理存在，就占 TAUNT slot。
```

因此以下都继续阻塞新 Apply：

```text
ACTIVE instance
SUPPRESSED instance
source-dead stale instance
logical lifetime exhausted but expiration removal transition has not yet physically removed instance
```

只有：

```text
REMOVED
```

才释放 slot。

结果：

```text
PASS
```

---

## 6. Trigger Audit

TAUNT 运行时触发点不是：

```text
ActionStart snapshot
RoundStart
Damage-time
Post-hit reaction
```

而是每一个新的：

```text
NormalAttackInstance
→ after NormalAttack permission gate
→ JIT primary target resolution
```

### Permission gate

冻结顺序：

```text
NormalAttack permission
BEFORE
Taunt target resolution
```

因此：

```text
DISARM / STUN / other normal-attack denial
→ no executable NormalAttackInstance target phase
→ no Taunt selector
→ no Taunt execution log
```

禁止实现：

```text
先解析 Taunt target
→ 再发现当前不能普通攻击
```

结果：

```text
PASS
```

---

## 7. Target Identity Audit

TAUNT 需要与 Stage9 公共目标身份模型保持至少三级解耦：

```text
intended / pre_redirect_target
post_redirect_attack_target / actualTarget
damage_recipient(s)
```

例如：

```text
Taunt source = A
Guard protector = C

TAUNT
→ intendedTarget = A

GUARD
→ actualTarget = C
```

A 仍保留为 selection provenance，但 GUARD 成功后：

```text
A 不获得该次攻击链的 Targeted / ON_NORMAL_ATTACK_RECEIVED / ON_DAMAGED
A 不消耗规避 / 抵御
A 不触发受击反应
```

真正的普通攻击承受者为 C。

后续：

```text
Counter owner = actual recipient C
single-target Assault target = C
Cleave main-target anchor = C
```

若 C 在普攻阶段死亡，单体 Assault 仍绑定已锁定的 C，不回退 A、不重新执行 Taunt、不随机重选。

结果：

```text
PASS
```

---

## 8. Damage / Resolution Pipeline Audit

TAUNT 不计算伤害，也不改变 Stage8 的伤害公式。

正确架构：

```text
NormalAttack permission
↓
Stage9 TargetSelector arbitration
↓
TAUNT if operational
↓
GUARD redirect
↓
final target identities
↓
DamageRequest
↓
unchanged Stage8 Damage Pipeline
```

TAUNT 不应被实现为：

```text
DamageRequest.target 被伤后再搬运
Damage transfer
Stage8 modifier
```

DAMAGE_SHARE / DISTRIBUTION 位于正常伤害公式后的 damage partition 层，它们读取 post-Guard final actual damage target，与 TAUNT 的 intended-target override 不冲突。

结果：

```text
PASS
```

---

## 9. Reaction / Recursion Audit

TAUNT 本身不创建 post-hit reaction，也不赋予递归攻击权限。

事件类型边界：

```text
ActiveSkill target selection
→ TAUNT NOT READ

Counter
→ target = triggering attacker
→ Counter is not NormalAttack
→ TAUNT NOT READ

Cleave secondary target selection
→ follows Cleave rules
→ TAUNT NOT READ

Chain
→ downstream damage propagation from a resolved damage node
→ no new NormalAttack primary-target selection
→ TAUNT NOT READ

Share / Distribution
→ post-formula partition / passive troop-loss settlement
→ no new NormalAttack primary-target selection
→ TAUNT NOT READ
```

Single-target Assault 属于 parent-target inheritance：

```text
parent NormalAttack actualTarget
→ Assault inherits target
```

因此 Assault 不重新运行 Taunt selector。

结果：

```text
PASS
```

---

## 10. Death / Termination Audit

### 10.1 Taunt source death

P0 明确：

```text
source dead
→ TauntInstance remains physically present
→ duration continues
→ TAUNT slot remains occupied
```

`sourceUnit.is_alive()` 不属于 `lifecycleState`。

因此合法状态组合包括：

```text
ACTIVE + source dead
SUPPRESSED + source dead
```

每次新的 NormalAttackInstance JIT 解析：

```text
Taunt exists
AND lifecycleState == ACTIVE
AND source.is_alive() == false
→ Taunt override silent-fail
→ no Taunt execute log
→ fallback to next selector path
```

这不是 `REMOVED`，也不释放 slot。

### 10.2 Actor-death during own open action

更新 COMBO P0 已正式冻结：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ current ActionContext continues
→ existing status slots are not immediately cleared
→ existing statuses remain readable by the current action
→ new status application to the dead actor is rejected
→ future Action scheduling is forbidden
```

TAUNT P0 自身的 operational gate 为：

```text
TauntInstance exists
AND Taunt lifecycleState == ACTIVE
AND Taunt source alive
```

TAUNT P0 没有：

```text
holder / attacker must be alive
```

这一额外 gate。

因此当：

```text
A = actor + Taunt holder
NormalAttack #1 reaction chain kills A
COMBO P0 keeps current Action open
TauntInstance existed before A died
```

第二击：

```text
NormalAttack #2
→ standard permission / target pass under COMBO open-action exception
→ existing TauntInstance remains readable
→ if Taunt ACTIVE and source alive: TAUNT may still force intended target
→ if Taunt source dead: TAUNT silent-fails and falls through
```

该结果由现有 P0 合同唯一决定。

### 10.3 Relationship to CFS9-B01

`CFS9-B01` 仍然 OPEN，因为 CONFUSION P0 自己写有：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_ACTION
```

它与 COMBO P0 open-action exception 正面冲突。

但 TAUNT 没有同样的 holder-death hard-termination 条款，因此：

```text
NO NEW TAUNT BLOCKER
```

更精确地说：

```text
TAUNT-only dead-actor Combo #2
= fully determined

TAUNT + CONFUSION coexisting on the dead actor
= whether CONFUSION still exists on #2 remains governed by OPEN CFS9-B01
```

如果未来 CFS9-B01 裁决“Confusion 仍可读”，则 #2 先走 Confusion selector，TAUNT 被 shadow；如果裁决“Confusion 已删除”，则 #2 才有机会进入 TAUNT selector。

这属于 CONFUSION 上游 blocker 对混合场景的影响，不是 TAUNT P0 内部矛盾，因此本轮不新建 `TAS9-Bxx`。

结果：

```text
TAUNT CONTRACT: PASS
CFS9-B01: REMAINS OPEN
NEW TAUNT BLOCKER: NO
```

---

## 11. RNG / Determinism Audit

允许冻结的工程行为：

```text
TAUNT forced-target resolution itself
→ does not require RandomSystem target selection
```

当 Taunt operational：

```text
forced intended target = live Taunt source
```

不需要再从默认敌方候选池随机抽取。

但禁止升级为：

```text
official internal PRNG definitely does not advance
```

战报无法直接证明官方内部 PRNG state 是否在不可见路径发生变化。

若：

```text
Taunt source dead
Taunt SUPPRESSED
Confusion absent
```

导致回落到 DefaultTargetSelector，则是否消耗项目 `RandomSystem` 由 fallback selector 自己的 Selection Strategy 决定。

若 Confusion 抢占，则沿 CONFUSION 修改后的原 Selection Strategy 处理 RNG。

结果：

```text
PASS
```

---

## 12. Provenance Audit

Stage9 工程模型至少需要保留：

```text
TauntInstance.holder
TauntInstance.source / sourceUnit
TauntInstance.sourceSkill
forced intended / pre_redirect_target
post-Guard actualTarget
final damage recipient(s)
```

目的：

- 解释哪一个 TauntInstance 提供强制主目标；
- 区分“被嘲讽锁定”与“最终实际挨打”；
- 保留 source death stale-slot 的来源归因；
- 保留 Guard 后 Assault / Counter / Cleave 的真实目标身份；
- 支持日志、调试与审计。

这些字段名称属于：

```text
PROJECT IMPLEMENTATION MODEL
```

不是：

```text
OFFICIAL SOURCE FIELD PROOF
```

结果：

```text
PASS
```

---

## 13. Cross-Mechanism Consistency

| Cross Mechanism | Contract relationship | Verdict |
|---|---|---|
| `TAUNT × CONFUSION` | `ConfusionTargetSelector > TauntTargetSelector`; 两状态可同时 ACTIVE；Confusion 只 shadow selector，不生成 TAUNT suppressor、不改 TAUNT duration；施加先后不改变优先级；Confusion 消失后未来新选择重新有机会读 TAUNT | `CONSISTENT` |
| `TAUNT × GUARD` | TAUNT 决定 intended/original target；GUARD 后置单次重定向为 actualTarget；原 intended target 零受击感知；Counter/Assault/Cleave 使用 post-Guard attack target | `CONSISTENT` |
| `TAUNT × COMBO` | 每击都是新 NormalAttackInstance；每击重新 permission + JIT target + Guard；#1 目标绝不直接继承给 #2；两击间 expiry/purge/suppress/resume/source-death/confusion change 均由 #2 live read | `CONSISTENT` |
| `TAUNT × CLEAVE` | TAUNT 只控制普通攻击 primary intended target；Cleave secondary targets 不读 TAUNT；GUARD 后 actualTarget 是 Cleave 主目标锚点 | `CONSISTENT / NO DIRECT SECONDARY OVERRIDE` |
| `TAUNT × CHAIN` | Chain 是已结算伤害节点的传播；不创建新 NormalAttack target selection | `NOT APPLICABLE DIRECTLY` |
| `TAUNT × DAMAGE_SHARE` | Share 在正常终伤后的 partition 层读取 final actual damage target；不回读 TAUNT intended target | `NOT APPLICABLE DIRECTLY / PIPELINE CONSISTENT` |
| `TAUNT × DISTRIBUTION` | Distribution 同样发生于 final actual damage target 后的 partition 层 | `NOT APPLICABLE DIRECTLY / PIPELINE CONSISTENT` |
| `TAUNT × COUNTERATTACK` | Counter 由 final actual normal-attack recipient 触发，target 固定为 triggering attacker；Counter 自身不是 NormalAttack，不读 TAUNT | `CONSISTENT` |

### 13.1 TAUNT × CONFUSION detailed check

```text
施加先后改变结果？
NO

Confusion 结束后 Taunt 是否仍可参与未来选择？
YES, if Taunt instance still exists + ACTIVE + source alive

Confusion 是否修改 Taunt duration？
NO

Confusion 是否生成 Taunt suppressor？
NO

Taunt source dead + Confusion active？
Current selection uses Confusion branch first; Taunt source liveness is irrelevant because Taunt branch is not entered.
After Confusion ceases, dead-source Taunt silent-fails and selector falls through.
```

### 13.2 TAUNT × GUARD detailed check

```text
Taunt source 被选为 intended target
→ 可以产生 Taunt execution provenance/log

Guard succeeds
→ protector becomes actualTarget
→ Taunt source does not become hit recipient merely because it was intended target
```

因此不能把“执行嘲讽”误解为“嘲讽来源必然收到本次普攻受击事件”。

### 13.3 TAUNT × COMBO detailed check

第二击读取第二击当时 live world：

```text
Taunt expired / purged
→ #2 no Taunt

Taunt SUPPRESSED
→ #2 no Taunt override

Taunt resumes before #2
→ #2 may use Taunt if source alive

Taunt source dies between hits
→ #2 Taunt silent-fail

Confusion appears before #2
→ Confusion preempts Taunt

Confusion disappears before #2
→ #2 may enter Taunt branch
```

结果：

```text
PASS
```

---

## 14. Stage8 Compatibility

Stage8 Frozen Contract 的职责是 Damage Pipeline；Target Selection、Guard redirect、Combo/action orchestration、reaction scheduling 属于 Stage9 或更高编排层。

TAUNT 正确接入点：

```text
Stage8 BEFORE
=
Stage9 NormalAttack orchestration / Target Selection
```

流程：

```text
NormalAttack permission
↓
TargetSelector arbitration
↓
TAUNT if operational
↓
GUARD redirect
↓
final target identities
↓
DamageRequest
↓
Stage8 unchanged damage pipeline
```

TAUNT 不要求改变：

```text
Stage8 base damage formula
Stage8 damage modifier ordering
Stage8 troop commit semantics
```

裁决：

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
```

---

## 15. Documentation Drift

### TAS9-D01 — State Mechanics Index still marks TAUNT as MINIMUM_USABLE

Severity: `DOC_DRIFT`

Current stale entry:

```text
sgs-state-mechanics-research/STATE_MECHANICS_INDEX.md
690106 TAUNT = MINIMUM_USABLE
```

Current authority:

```text
main TAUNT Freeze Record = FROZEN
```

Impact:

```text
navigation/status drift only
no mechanism downgrade
```

### TAS9-D02 — core_arbitration_v2 README partially stale

Severity: `DOC_DRIFT`

The README correctly marks TAUNT FROZEN, but still lists CONFUSION / COMBO as future research and retains an old Counter death summary saying attacker death cancels pending Combo.

Impact:

```text
may mislead future Stage9 design around open-action death
P0 contracts remain unambiguous
```

### TAS9-D03 — Evidence Matrix is historical, not current freeze status

Severity: `DOC_DRIFT`

`STAGE9_EVIDENCE_MATRIX_V2.md` retains historical confidence/state entries and old `EM-20` Combo death-short-circuit language superseded by COMBO P0.

Impact:

```text
historical evidence trace remains useful
must not be used as current runtime contract
```

### TAS9-D04 — Lower-authority death documentation is not uniformly synchronized

Severity: `DOC_DRIFT`

Affected cluster:

```text
R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
R5_DEATH_TERMINATION_MATRIX.md
sgs-state-mechanics-research/README.md
```

They retain blanket death-abort/clear wording on the boundary now refined by COMBO P0.

`STATE_MECHANICS_INDEX.md` is already correctly scoped with the own-open-action exception, so the repository currently contains mixed documentation generations.

Impact on TAUNT:

```text
none at P0 authority level
but stale docs could cause an implementation to wrongly clear Taunt before Combo #2
```

Per this audit's submission rule, these drifts are recorded only. No unrelated files are modified in this commit.

---

## 16. Findings

### TAS9-D01 — TAUNT state index status stale

```text
Type: DOC_DRIFT
Blocking: NO
Action: future docs sync
```

### TAS9-D02 — Stage9 core README partially stale after CONFUSION / COMBO freezes

```text
Type: DOC_DRIFT
Blocking: NO
Action: future docs sync
```

### TAS9-D03 — Stage9 Evidence Matrix still represents historical pre-freeze state

```text
Type: DOC_DRIFT
Blocking: NO
Action: future docs sync; retain historical evidence attribution
```

### TAS9-D04 — death-boundary lower-authority docs not fully synchronized to COMBO P0 exception

```text
Type: DOC_DRIFT
Blocking: NO for TAUNT
Action: future docs sync
```

### TAS9-H01 — Add explicit open-action-death TAUNT regression coverage

```text
Type: HARDENING
Blocking: NO
```

Recommended runtime regression cases after Stage9 design begins:

```text
1. actor holds ACTIVE Taunt, source alive, dies after Combo #1
   → #2 still JIT reads existing Taunt

2. same but Taunt source dies between hits
   → #2 silent-fails Taunt and falls through

3. actor holds Taunt + Confusion and dies between hits
   → expected result remains tied to future CFS9-B01 resolution
   → test must not silently pick one Confusion death policy before that blocker is resolved
```

This hardening does not indicate a TAUNT contract ambiguity. It exists to prevent lower-authority death docs from leaking back into implementation.

### Finding totals

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 0
DOC_DRIFT = 4
HARDENING = 1
```

Inherited external finding:

```text
CFS9-B01 = OPEN
```

It remains a Stage9 global blocker for the CONFUSION × COMBO holder-death mixed case, not a TAUNT-specific blocker.

---

## 17. Final Verdict

```text
TAUNT CONTRACT INTERNAL CONSISTENCY = PASS
TAUNT × CONFUSION = CONSISTENT, subject only to inherited CFS9-B01 in dead-actor mixed-state case
TAUNT × GUARD = CONSISTENT
TAUNT × COMBO = CONSISTENT
ACTOR-DEATH OPEN-ACTION NEW TAUNT BLOCKER = NO
FORMAL STAGE8 REOPEN REQUIRED = NO
BLOCKER = 0
MAJOR = 0
MINOR = 0
DOC_DRIFT = 4
HARDENING = 1
```

Final Verdict:

# PASS WITH DOC SYNC

TAUNT 当前 P0 Frozen Contract 已形成可直接进入 Stage9 runtime 设计的唯一语义：

```text
TAUNT
= NormalAttack primary intended-target override
= JIT per new NormalAttackInstance
= after normal-attack permission
= below CONFUSION selector precedence
= before GUARD redirection
= UNIQUE_SLOT / First-In Wins
= multi-suppressor lifecycle
= source-death-retained but source-liveness-gated
= target-action-timeline duration
```

本轮未发现需要 Reopen TAUNT 的机制冲突。

必须继续保留：

```text
CFS9-B01 = OPEN
```

因此：

```text
TAUNT independent contract readiness = PASS WITH DOC SYNC
Stage9 overall design gate = still must carry CFS9-B01 until CONFUSION/COMBO death boundary is formally resolved
```

下一独立机制审计：

```text
690098 GUARD / 援护
```
