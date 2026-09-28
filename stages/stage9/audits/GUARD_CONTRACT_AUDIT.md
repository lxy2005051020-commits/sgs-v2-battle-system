# GUARD Contract Audit

Status ID: `690098`  
Mechanism: `GUARD / 援护`  
Audit Type: `Stage 9 Frozen Contract Independent Review`  
Audit Date: `2026-09-13`

> 本审计不重新研究援护，不重新扫描全量战报。审计目标仅为复核当前 P0 Frozen Contract 的内部闭环、跨 Frozen Contract 一致性、死亡 / target-lock 边界、Stage 8 兼容性与 Stage 9 runtime 设计准入状态。

---

## 1. Repository Baseline

本轮开始与写入前均重新读取远端 `main`，未沿用上一轮 baseline；写入前 HEAD 未发生变化。

```text
sgs-v2-battle-system
exact audit-input main HEAD = 0d881b1e7c396e9540a898085bce5f776d5b8176
audit(stage9): verify taunt frozen contract

sgs-state-mechanics-research
exact audit-input main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
docs(index): mark combo frozen and scope death baseline
```

已继承：

```text
stages/stage9/audits/CONFUSION_CONTRACT_AUDIT.md
→ CFS9-B01 = OPEN

stages/stage9/audits/TAUNT_CONTRACT_AUDIT.md
→ PASS WITH DOC SYNC
→ TAUNT-specific BLOCKER = 0
```

`CFS9-B01` 当前冲突为：

```text
CONFUSION holder-death hard termination
vs
COMBO ACTOR_DEATH_DURING_OWN_OPEN_ACTION exception
```

当前主仓没有后续 re-freeze 或正式修复，因此本轮继续继承为 `OPEN`。本审计只判断它是否产生新的 GUARD-specific blocker。

---

## 2. Authoritative Freeze Source

### 2.1 GUARD P0

主战斗仓正式入口：

```text
stages/stage9/STATE_690098_GUARD_MECHANISM_CONTRACT.md
blob = a496d3e006b3945cf97cd431e0d0d9162aec8653
```

状态研究仓镜像：

```text
states/functional/guard/MECHANISM_CONTRACT.md
blob = a496d3e006b3945cf97cd431e0d0d9162aec8653
```

判定：

```text
DUPLICATE MIRROR
BYTE-IDENTICAL
NO CROSS-REPO CONFLICT
```

因此本轮以主战斗仓 Stage 9 路径作为实现侧 P0 authoritative entry，同时把状态研究仓文件视为 byte-identical P0 mirror。

### 2.2 Supporting authority read

本轮读取并按优先级交叉核对：

```text
P0 / latest Freeze Records
- STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md
- STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md
- STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md
- STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md
- STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md
- STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md
- states/functional/combo/MECHANISM_CONTRACT.md
- states/control/confusion/MECHANISM_CONTRACT.md

P2/P3
- STAGE9_CORE_ARBITRATION_RULES_V2.md
- R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
- R2_TARGET_REDIRECT_AND_GUARD.md
- R4_RECURSION_PERMISSION_MATRIX.md
- R5_DEATH_TERMINATION_MATRIX.md
- R6_MULTI_SOURCE_RULES.md
- R8_PROVENANCE_MODEL.md

Stage 8
- stages/stage8/STAGE8_FREEZE_RECORD.md
```

权威原则维持：若旧 R1/R5/Evidence Matrix 的死亡或 Combo 推论与后续 COMBO P0 冲突，以后续 P0 为准。

---

## 3. Superseded / Stale Sources

### 3.1 R2 terminology

`R2_TARGET_REDIRECT_AND_GUARD.md` 的实证内容与 GUARD P0 的核心目标语义一致：

```text
pre_redirect_target
→ post_redirect_attack_target
→ damage_recipient(s)
```

但历史表述使用“自援护”描述：

```text
attacker == protector
```

当前 P0 已明确：

```text
Self_Guard = protector == holder = FORBIDDEN
attacker == protector = ALLOWED
```

因此 R2 的“自援护”仅可理解为“redirect-created self-hit / 攻击者同时是 protector”，不可据此允许 `protector == holder`。

### 3.2 R1 / R5 death generalization

R1 / R5 仍保留：

```text
actor dies from Counter
→ later Assault / Combo hard abort
```

而后续 COMBO P0 已冻结：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ current Action continues until cfg 733
→ already acquired Combo may still launch NORMAL_ATTACK #2
```

因此 R1/R5 在该特定边界属于 superseded historical research，不得覆盖 COMBO P0，也不得被 GUARD 实现继承成“死 actor 一律禁止 fresh Guard Check”。

### 3.3 Evidence Matrix

`STAGE9_EVIDENCE_MATRIX_V2.md` 中 GUARD 相关 EM-02～EM-07 仍主要是历史 A/B 证据等级，而 GUARD 已存在正式 P0 Frozen Contract。矩阵仍可作为 evidence trace，但不是当前实现状态的权威来源。

---

## 4. State Kernel Audit

冻结定义完整且无歧义：

```text
GUARD
= NORMAL_ATTACK target-resolution redirect
```

不是：

```text
Damage Transfer
Damage Share
Damage Interception after damage
ON_DAMAGED reaction
Generic attack redirect
```

触发合同：

```text
Trigger_Event = NORMAL_ATTACK_ONLY
```

时序：

```text
Target Selection
→ originalTarget
→ GUARD / Cover Check
→ actualTarget
→ Target Lock
→ downstream attack chain
```

因此 GUARD 是动作目标身份改写，不是伤害数值搬运。

`NormalAttackEvent`、`AttackChainContext`、`CoverBuff`、`CoverSlot`、`actualTarget` 等均为 project normative terminology，不宣称为官方源码真实类名 / 字段名。

Result：

```text
PASS
```

---

## 5. Lifecycle Audit

### 5.1 State owner / protector / source

P0 明确：

```text
State Owner = protected target / holder
Linked Entity = protector
sourceUnit / sourceSkill = immutable provenance
```

三者不得混淆。

最小实例字段：

```text
holder
protector
sourceUnit
sourceSkill
applyRound
remainingDuration
isDisabled
```

### 5.2 Duration ownership

冻结：

```text
holder.OnActionStart
→ GUARD lifecycle tick
```

而不是：

```text
protector.OnActionStart
```

Apply-round exemption：

```text
currentRound == applyRound
→ skip duration tick
```

不是“无条件免掉施加后的第一次行动开始”。

到期边界：

```text
remainingDuration 1 → 0
→ Holder Action Start immediate physical removal
→ remove before later action logic
```

### 5.3 Unique slot / First-In Wins

冻结：

```text
one holder → max one CoverBuff
Stacking = FORBIDDEN
Refresh = FORBIDDEN
Replacement = FORBIDDEN
First-In Wins = true
```

同时：

```text
one protector → may protect multiple holders
```

各 holder 的 Guard instance 独立占槽、独立计时。

### 5.4 Zombie slot

只要实例尚未物理删除：

```text
protector dead
or
isDisabled == true
```

仍：

```text
instance exists
slot occupied
holder lifecycle continues
new Guard apply rejected
```

Result：

```text
PASS
```

---

## 6. Trigger Audit

### 6.1 NormalAttack-only gate

只有真正新的：

```text
NORMAL_ATTACK
```

运行 Guard Check。

会运行：

```text
base NormalAttack
Combo #2 NormalAttack
duel / future source if event identity is NORMAL_ATTACK
forced-target NormalAttack
confusion friendly-fire NormalAttack
```

不会独立运行：

```text
Active Skill damage
Assault derived effect
Counter damage
Cleave damage
Chain feedback
Share loss
Distribution loss
Periodic damage
```

### 6.2 Combo granularity

每个 Combo hit 是独立 `NormalAttackInstance`：

```text
#1 fresh Target Selection → fresh Guard Check → lock
#2 fresh Target Selection → fresh Guard Check → lock
```

第二击不得继承第一击：

```text
originalTarget
actualTarget
Guard result
```

两击之间 Guard expiry / protector death / new Guard / disabled / holder death 均由 #2 live read。

Result：

```text
PASS
```

---

## 7. Target Identity Audit

### 7.1 Three-stage identity

必须至少区分：

```text
originalTarget
actualTarget
damageRecipient(s)
```

GUARD 成功后：

```text
originalTarget = selection provenance only
actualTarget = protector
```

### 7.2 originalTarget Zero-Awareness Rule

P0 明确：Guard 成功后 originalTarget：

```text
不收到 Targeted
不收到 ON_NORMAL_ATTACK_RECEIVED
不收到 ON_DAMAGED
不触发受击监听
不检查自己的 Evasion
不消耗自己的 Resistance
不读取自己的 defensive attributes
不参与本攻击链目标条件判断
```

所有运行时目标语义切换到 `actualTarget`。

### 7.3 Single-pass / non-recursive

```text
B guarded by C
C guarded by D
A normal attacks B
→ B → C → STOP
```

一旦 `actualTarget` 解析完成：

```text
NO RE-GUARD
NO CHAIN GUARD
```

### 7.4 attacker == protector

允许：

```text
attacker == protector
```

因此：

```text
Confusion selector chooses protected friendly B
B protected by attacker C
→ originalTarget = B
→ Guard redirect
→ actualTarget = C
→ attacker == actualTarget
```

这不违反 CONFUSION 的 self eligibility：

```text
selector-created self target
!=
post-selection redirect-created self target
```

Result：

```text
PASS
```

---

## 8. Damage / Resolution Pipeline Audit

正确流程：

```text
NormalAttack target selection
↓
GUARD target resolution
↓
actualTarget lock
↓
Defense / DamageRequest participant identity based on actualTarget
↓
Stage8 frozen damage pipeline
↓
Share / Distribution damage partition if applicable
↓
damageRecipient(s)
```

GUARD 不应实现成：

```text
damage calculated for originalTarget
→ move damage to protector
```

### Share

`DAMAGE_SHARE` P0 明确：

```text
DAMAGE_SHARE_TARGET = FINAL_ACTUAL_DAMAGE_TARGET
```

因此只检查 actualTarget 的 Share state。

### Distribution

`DISTRIBUTION` P0 明确继承：

```text
GUARD / TARGET_REDIRECTION
→ FINAL_ACTUAL_DAMAGE_TARGET
→ normal formula
→ damage partition
```

因此只检查 actualTarget 的 Distribution state / participant topology。

Result：

```text
PASS
```

---

## 9. Reaction / Recursion Audit

### 9.1 GUARD × CONFUSION

顺序：

```text
CONFUSION
→ modifies selector legality
→ originalTarget
→ GUARD
→ actualTarget
```

冻结关系：

```text
CONFUSION does not suppress GUARD
GUARD does not rerun CONFUSION
```

混乱选中友军受援护目标时 Guard 正常运行。

若 `CFS9-B01` 所涉死亡 actor 的 Combo #2 最终继续执行 Target Selection，GUARD 只消费该次 selector 给出的 `originalTarget`；GUARD 不负责决定 CONFUSION 在死亡 actor 上是否仍 operational。

Verdict：`CONSISTENT`。

### 9.2 GUARD × TAUNT

顺序：

```text
TAUNT → intended/original target
GUARD → actual target
```

典型：

```text
Taunt source = B
B guarded by C
A normal attacks under Taunt
→ originalTarget = B
→ actualTarget = C
```

Guard 成功后：

```text
B zero-awareness
C = ON_NORMAL_ATTACK_RECEIVED holder
C's CounterStates checked
single-target Assault binds C
Cleave anchor = C
```

Verdict：`CONSISTENT`。

### 9.3 GUARD × COMBO

COMBO P0 明确第二击是新的完整 `NORMAL_ATTACK`，重新：

```text
can_normal_attack
select_target
Guard Check
Target Lock
```

因此：

```text
#1 context != #2 context
```

若 actor 在 own-open-action 中死亡但 COMBO P0 仍允许 #2 执行，GUARD 依然按 #2 live world state 运行。

特殊一致性：若死亡 actor 恰好也是某个 `originalTarget` 的 protector，则：

```text
protector.is_alive() == false
→ Guard fails JIT
→ actualTarget remains originalTarget
```

ACTOR_DEATH exception 不会把 GUARD 的 protector liveness gate 改成 true。

Verdict：`CONSISTENT`。

### 9.4 GUARD × CLEAVE

冻结锚点：

```text
Cleave main-target anchor = post-Guard actualTarget
```

因此：

```text
A attacks B
B guarded by C
→ actualTarget = C
→ Cleave derives around C
```

B 若符合 C 的同阵营副目标条件，可作为 Cleave secondary target 受到群攻。

Cleave secondary damage 不是新 `NORMAL_ATTACK`：

```text
Cleave → Guard = NOT APPLICABLE
```

Verdict：`CONSISTENT`。

### 9.5 GUARD × COUNTERATTACK

Counter P0 触发门禁：

```text
ON_NORMAL_ATTACK_RECEIVED
AND defender = FINAL_ACTUAL_ATTACK_RECIPIENT
```

因此：

```text
A attacks B
B guarded by C
→ Counter owner = C
→ Counter target = A
```

Counter damage 没有 NormalAttack identity：

```text
Counter → Guard = NOT APPLICABLE
```

Verdict：`CONSISTENT`。

### 9.6 GUARD × ASSAULT

TAUNT/Guard 目标锁定合同明确：

```text
single-target Assault
→ inherits post-Guard FinalEventTarget / actualTarget
```

不重新：

```text
Target Selection
Guard Check
```

若 locked actualTarget 在 Assault 前死亡：

```text
empty / invalid target resolution
no fallback to originalTarget
no random retarget
```

Verdict：`CONSISTENT`。

### 9.7 GUARD × DAMAGE_SHARE / DISTRIBUTION

顺序：

```text
originalTarget
→ GUARD
→ FINAL_ACTUAL_DAMAGE_TARGET
→ normal damage calculation
→ Share / Distribution
→ damageRecipient(s)
```

两机制均读取 actualTarget，不回头读取 originalTarget。

Verdict：`CONSISTENT`。

### 9.8 GUARD × CHAIN

NormalAttack 主伤害真正落在 `actualTarget` 后，若该实际受伤节点满足 Chain 条件：

```text
Chain trigger source node = actualTarget's resolved damage node
```

originalTarget 因未被击中，不因自身 Chain state 产生该次主伤害 Chain。

Chain feedback 不是新的 NormalAttack：

```text
Chain → Guard = NOT APPLICABLE
```

Verdict：`CONSISTENT`。

---

## 10. Death / Termination Audit

### A. originalTarget dies before Guard Check

在当前 Frozen pipeline 中：

```text
Target Selection filters alive candidates
→ immediate Target Resolution / Guard
→ Target Lock
```

两者之间没有已冻结的 Reaction / Damage interleaving point，因此“合法选中后、Guard 前死亡”在当前模型中不可达。

结论：

```text
NO NEW BLOCKER
```

实现上不得在 Selection 与 Guard 之间插入可杀死目标的 reaction hook。

### B. protector dies before Guard Check

P0 直接覆盖：

```text
CoverBuff remains
CoverSlot remains occupied
Duration continues
protector.is_alive() == false
→ Guard fails
→ actualTarget = originalTarget
```

```text
NO BLOCKER
```

### C. protector dies after Guard succeeds but before damage

Guard 成功后已进入 target lock：

```text
actualTarget = protector
```

即使 protector 在后续节点真正扣兵前死亡：

```text
NO RE-GUARD
NO RETARGET
NO BOUNCE BACK
```

后续节点对 dead actualTarget 使用节点级死亡守卫。

```text
NO BLOCKER
```

### D. protector dies from main damage

P0 明确：

```text
actualTarget remains dead protector
AttackChainContext continues
bound single-target nodes do not return to originalTarget
Counter from dead target stops
independent-target nodes may continue by their own selector
```

```text
NO BLOCKER
```

### E. attacker dies from Counter

这里存在 Stage9 全局跨合同问题，但不是 GUARD-specific contradiction：

```text
older R1/R5/Counter wording
vs
newer COMBO ACTOR_DEATH_DURING_OWN_OPEN_ACTION P0
```

若当前 P0 允许 Combo #2 继续：

```text
#2 is a new NORMAL_ATTACK
→ fresh Target Selection
→ fresh Guard Check
```

GUARD 不替该全局冲突决定 Action 是否继续。

```text
NO NEW GDS9 BLOCKER
```

### F. holder dies during own open action

普通全局规则：holder death 会使未来 targeting / future scheduling 不再把死亡单位当合法目标。

最新 COMBO P0 对当前行动者增加例外：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ do not immediately clear existing status slots
→ continue current Action until cfg 733
```

因此若 dead actor 本身是某个 Guard holder，其既有 CoverBuff 可在实体容器中暂留到当前 Action 关闭；但 GUARD 的触发前提仍是“未来某个新 NormalAttack 选中该 holder 作为 originalTarget”。标准 Selector 的 Alive Constraint 排除死亡单位，而当前已锁定的攻击链又不会重新 Guard。

所以在当前 Frozen topology 中，没有新的可执行 Guard Check 会因“死亡 holder 状态暂留”改变本次战斗结果。

```text
NO NEW BLOCKER
```

### G. commander death ends battle

GUARD 不拥有独立 Victory authority。当前原子 Action / reaction 是否先收尾由更高层死亡与战斗终止合同决定。

无论 final victory 在何节点宣布，只要 Battle Runtime 已终止：

```text
no future NormalAttack scheduling
no future Guard checks
```

当前已经锁定的 AttackChain 仍遵循自身 Frozen target lock，不因 commander death 把目标弹回 originalTarget。

```text
NO GUARD-SPECIFIC BLOCKER
```

### Source / Protector / Holder death summary

```text
sourceUnit death only
→ provenance remains
→ does not by itself disable/remove Guard
→ if sourceUnit != protector and protector alive, Guard may remain operational

protector death
→ instance remains
→ slot remains occupied
→ duration continues by holder
→ JIT Guard fails

holder death
→ no new Guard can be applied to dead holder
→ normal future target selection excludes dead holder
→ own-open-action exception may temporarily retain existing slot until action close, without creating a new executable Guard trigger
```

Result：

```text
NO GDS9 BLOCKER
```

---

## 11. RNG / Determinism Audit

GUARD runtime resolution is deterministic once `originalTarget` is known：

```text
cover == null → originalTarget
cover disabled → originalTarget
protector dead → originalTarget
otherwise → protector
```

同一 holder 的 multiple Guard source 竞争已在 Apply 阶段通过：

```text
UNIQUE SLOT
First-In Wins
```

解决，因此 runtime 不存在 multiple-guard random arbitration。

禁止为了通用接口无意义调用 RNG。

Result：

```text
PASS
```

---

## 12. Provenance Audit

Stage 9 至少需要保留：

```text
originalTarget
actualTarget
protector
holder
sourceUnit
sourceSkill
```

其中：

```text
originalTarget
= selection provenance

actualTarget
= current NormalAttack chain runtime target after Guard

protector
= Guard linked entity

holder
= Guard state owner / protected target

sourceUnit / sourceSkill
= immutable Guard provenance
```

`damageRecipient(s)` 属于后续 damage-partition 身份，不得与 `actualTarget` 混成单一字段。

R8 同时明确：战报本身没有 `root_action_id / parent_event_id / reaction_depth` 等真实字段；这些属于模拟器内部 reconstructed / engineering provenance。

Result：

```text
PASS
```

---

## 13. Cross-Mechanism Consistency

| Cross Item | Verdict |
|---|---|
| GUARD × CONFUSION | CONSISTENT |
| GUARD × TAUNT | CONSISTENT |
| GUARD × COMBO | CONSISTENT |
| GUARD × CLEAVE | CONSISTENT |
| GUARD × COUNTERATTACK | CONSISTENT |
| GUARD × DAMAGE_SHARE | CONSISTENT |
| GUARD × DISTRIBUTION | CONSISTENT |
| GUARD × CHAIN_LINK | CONSISTENT |

补充：

```text
CFS9-B01 remains OPEN
```

但它决定的是 dead actor 上 CONFUSION 与 COMBO own-open-action 的状态 / Action 边界，不构成新的 GUARD 合同冲突。

---

## 14. Stage8 Compatibility

GUARD 位于 Stage8 之前：

```text
NormalAttack target selection
↓
GUARD Target Resolution
↓
final source / actual target identity
↓
DamageRequest
↓
Stage8 Frozen Damage Pipeline
```

因此 GUARD 不需要修改：

```text
DamageRequest participant validation semantics
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
Frozen Base Formula
DamageResolutionSystem
TroopSystem
```

Stage8 已冻结的核心职责仍然成立；Stage9 只需在创建 DamageRequest 前提供正确的最终参与者身份。

结论：

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
```

---

## 15. Documentation Drift

### GDS9-D01 — core_arbitration_v2 README stale current-state map

当前 README 的“最新状态 / Next Core Research Target / 仍待研究”仍未同步：

```text
GUARD P0 FROZEN
CONFUSION P0 FROZEN
COMBO P0 FROZEN
```

并继续保留旧 Counter death → Combo cancellation 摘要。

判定：

```text
DOC_DRIFT
no contract reopen
```

### GDS9-D02 — STAGE9_EVIDENCE_MATRIX_V2 stale for current contracts

矩阵仍把 GUARD cross items主要作为历史 A/B 证据，并保留：

```text
Share = NEXT RESEARCH TARGET
EM-20 actor death → Combo short circuit
EM-25 Combo re-target = B+ / strong
EM-26 Confusion JIT = historical A
```

而后续 Share / Guard / Combo / Confusion 已有更高优先级 Frozen Contract。

判定：

```text
DOC_DRIFT
valid only as historical evidence trace
```

### GDS9-D03 — state-research root README stale

状态研究仓 root README 仍写：

```text
当前第一个研究对象 = 690081 COMBO
```

且 root-level Target Death 仍只展示无条件 hard termination，没有同步 `STATE_MECHANICS_INDEX.md` 已增加的 own-open-action death exception。

判定：

```text
DOC_DRIFT
```

### GDS9-D04 — R2 historical naming drift

R2 使用“自援护”指 `attacker == protector`，容易与当前 P0 的：

```text
Self_Guard = protector == holder = FORBIDDEN
```

混淆。其行为事实本身与 P0 一致，但术语应视为 historical wording。

判定：

```text
DOC_DRIFT / terminology only
```

### Non-drift notes

```text
stages/stage9/README.md
→ 已正确暴露 GUARD P0 入口；仅导航简略，不构成 GUARD blocker

STATE_MECHANICS_INDEX.md
→ 690098 GUARD 已正确标记 FROZEN
→ 同时已正确记录 ACTOR_DEATH_DURING_OWN_OPEN_ACTION 全局作用域修正
```

---

## 16. Findings

### BLOCKER

```text
GDS9-Bxx = 0
```

### MAJOR

```text
GDS9-Mxx = 0
```

### MINOR

```text
GDS9-Nxx = 0
```

### DOC_DRIFT

```text
GDS9-D01 = OPEN — core_arbitration_v2 README current-state / death summary stale
GDS9-D02 = OPEN — Evidence Matrix stale for current Frozen Contracts
GDS9-D03 = OPEN — state-research root README stale research target / death baseline
GDS9-D04 = OPEN — R2 “self-guard” terminology is historical and ambiguous
```

### HARDENING

#### GDS9-H01 — enforce atomic Target Resolution and typed target identities

Stage9 runtime design / tests should make the following structural invariants explicit：

```text
Target Selection
→ originalTarget
→ exactly one Guard Check
→ actualTarget
→ Target Lock
```

并强制：

```text
no reaction hook between selection and Guard
no recursive Guard on actualTarget
no originalTarget fallback after lock
all downstream target-bound nodes consume actualTarget
Combo #2 creates a new target-resolution context
```

该项为实现防回归 hardening，不是合同缺口。

---

## 17. Final Verdict

### Contract readiness

GUARD P0 本身内部闭环，且以下高风险边界均已有唯一可实现语义：

```text
NormalAttack-only trigger
originalTarget / actualTarget identity split
originalTarget zero-awareness
single-pass non-recursive Guard
AttackChain target lock
holder-owned lifecycle
unique slot / First-In Wins
protector death stale-slot behavior
source/protector/holder identity separation
attacker == protector self-hit outcome
per-Combo-hit fresh Guard
post-Guard Cleave / Counter / Assault target inheritance
Share / Distribution after actualTarget
Chain anchored to actual resolved damage node
```

未发现新的 GUARD-specific blocker / major / minor。

当前遗留仅为文档漂移与实现硬化；`CFS9-B01` 仍为 Stage9 已继承的独立开放 blocker，但不要求 GUARD reopen。

最终裁决：

```text
PASS WITH DOC SYNC
```

准入判断：

```text
GUARD CAN ENTER STAGE9 RUNTIME DESIGN = YES
FORMAL STAGE8 REOPEN REQUIRED = NO
GUARD P0 REOPEN REQUIRED = NO
CFS9-B01 = OPEN / INHERITED / NOT GUARD-SPECIFIC
NEXT MECHANISM = COMBO
```
