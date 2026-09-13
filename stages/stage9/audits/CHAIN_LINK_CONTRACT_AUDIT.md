# CHAIN_LINK Contract Audit

> Audit target: `690097 CHAIN_LINK / 铁索连环`  
> Audit date: 2026-09-13  
> Audit type: Stage 9 Frozen Contract Independent Review  
> Final verdict: **REOPEN REQUIRED**  
> Reopen scope: **NARROW REOPEN ONLY** — preserve the confirmed Chain trigger / traversal / attribution / restricted-settlement kernel; reopen only the integerization rule identified in `CHNS9-B01`.

---

## 1. Repository Baseline

本轮开始与写入前均重新读取两个仓库 `main`，没有沿用聊天记录中的旧 baseline。

```text
battle repo:
lxy2005051020-commits/sgs-v2-battle-system
exact audit-input main HEAD = 677953bd4b6d03673b834ee438f4500524187e0f
audit(stage9): verify cleave frozen contract

state research repo:
lxy2005051020-commits/sgs-state-mechanics-research
exact audit-input main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
docs(index): mark combo frozen and scope death baseline
```

因此用户给出的上一轮 CLEAVE audit commit：

```text
677953bd4b6d03673b834ee438f4500524187e0f
```

在本轮写入前仍然确实是 battle repo `main` HEAD。

### 1.1 Inherited OPEN findings

本轮完整读取前五轮独立审计并继承其开放项。

```text
CONFUSION:
CFS9-B01 = OPEN

COMBO:
CBS9-B01 = OPEN
CBS9-B02 = OPEN
CBS9-B03 = OPEN
CBS9-M01 = OPEN
CBS9-M02 = OPEN
CBS9-M03 = OPEN

CLEAVE:
CLVS9-B01 = OPEN
CLVS9-B02 = OPEN
CLVS9-B03 = OPEN
CLVS9-B04 = OPEN
CLVS9-M01 = OPEN
```

TAUNT / GUARD 独立审计结论继续为：

```text
TAUNT = PASS WITH DOC SYNC
GUARD = PASS WITH DOC SYNC
```

本轮没有任何 CHAIN P0 新证据足以正式关闭上述 finding。特别是：

```text
Chain 的 TriggerNodeResolvedDamage 可以精确映射
!=
Cleave 的 MainAttackFinalDamage 已被定义
```

因此 `CLVS9-B01` 必须继续保持 OPEN。

---

## 2. Authoritative Freeze Source

CHAIN 当前最高权威 P0：

```text
stages/stage9/research/core_arbitration_v2/
STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md
```

当前 blob：

```text
4764c3ebebd525f74ab76f54694733c217eaaa90
```

初始冻结提交：

```text
50f93c6dd92fb6c412a0e7da766c0fe5aa56e476
docs(research): freeze stage 9 iron chain mechanics
```

当前状态：

```text
CHAIN CORE MECHANICS FROZEN
```

本轮 Authority Priority：

```text
P0 latest MECHANISM_CONTRACT / FREEZE_RECORD
P1 FREEZE_AUDIT / FINAL_CONSISTENCY_AUDIT
P2 STAGE9_CORE_ARBITRATION_RULES_V2
P3 R1-R8
P4 STAGE9_EVIDENCE_MATRIX_V2
P5 README / INDEX
P6 MINIMUM_USABLE
P7 historical inference
```

### 2.1 State-research repository status

状态研究仓当前：

```text
STATE_MECHANICS_INDEX.md
→ 690097 CHAIN_LINK = MINIMUM_USABLE

states/functional/minimum_usable/690097_CHAIN_LINK.md
→ Stage: MINIMUM_USABLE
```

并且 `states/functional/` 当前只有：

```text
combo/
damage_share/
guard/
minimum_usable/
```

不存在：

```text
states/functional/chain_link/
states/functional/chain/
```

正式 `MECHANISM_CONTRACT.md`。

因此不得假装状态研究仓已经存在独立 CHAIN P0 镜像。

---

## 3. Contract Scope: Core vs Full State

CHAIN 与上一轮 CLEAVE 不同。当前 CHAIN P0 已经直接冻结了大量 L1-L4 内容：

```text
trigger base concept
TRUE_FEEDBACK identity
eligible trigger families
legal-zero behavior
source-death cancel
PER-DAMAGE granularity
INLINE / DEFERRED timing
Deferred JIT fields
target topology
slot order
JIT target revalidation
single instance
same-source refresh
different-source overwrite
duration / expiration
cleanse / dispel
owner death
attribution / kill credit
troop clamp / statistics
restricted callback matrix
```

所以本轮不能机械复制：

```text
CORE title => FULL STATE incomplete
```

的 CLEAVE 结论。

本轮裁决：

```text
CHAIN lifecycle / traversal contract = substantially complete
source-skill-specific apply formula / ratio production = SOURCE-SKILL RESPONSIBILITY
full runtime arithmetic = NOT complete because Chain integerization is undefined
```

因此：

```text
CHAIN CORE MECHANICS FROZEN = YES
FULL 690097 CONTRACT READY = NO
```

唯一新实现阻塞见 `CHNS9-B01`。

---

## 4. State Kernel Audit

冻结 kernel：

```text
TriggerNodeResolvedDamage
×
TriggerNode.activeChainEffect.ratio
=
ChainCalculatedDamage
```

事件族：

```text
TRUE_FEEDBACK
```

明确不是：

```text
new WEAPON DamageRequest
new STRATEGY DamageRequest
new NORMAL_ATTACK
new CLEAVE
copied original DamageType
raw anonymous troops -= x
```

正确语义：

```text
legal resolved damage node
→ qualify Chain on surviving trigger node
→ derive TRUE_FEEDBACK value
→ restricted attributed troop-loss settlement
```

它必须保留：

```text
source state provenance
Chain owner
victim
theoretical ChainCalculatedDamage
actual committed troop loss
kill attribution
statistics attribution
parent trigger node / damage provenance
```

但不重新打开正常 Hit / Damage callback pipeline。

Result：`PASS`。

---

## 5. Trigger Damage Layer Audit

这是本轮第一最高风险项。

### 5.1 Formal damage layers already frozen elsewhere

DAMAGE_SHARE / DISTRIBUTION P0 已经把正常伤害明确拆成：

```text
normal formula
→ Dtotal
→ Share / Distribution partition
→ Dtarget assigned to original target
→ target troop commit
→ ActualTargetTroopLoss
→ credited/statistical damage
```

因此 `TriggerNodeResolvedDamage` 不能靠名字随便选一层。

### 5.2 Exact mapping

本轮 P0 × P0 合并裁决：

```text
TriggerNodeResolvedDamage
=
当前 trigger node 在该 Damage Instance 中
post-partition 的 normal DamageEvent amount
=
Dtarget
```

不是：

```text
A. pre-partition Dtotal             NO
B. post-partition assigned Dtarget  YES
C. actual committed troop loss      NUMERICALLY EQUAL WHEN CHAIN IS ALLOWED,
                                    BUT NOT THE SEMANTIC INPUT LAYER
D. credited/statistical damage      NO
E. battle-log display value         NO
```

理由：

1. DAMAGE_SHARE P0 明确冻结：原目标分担后的正常受伤语义读取 `Dtarget`，`TakeDamageEvent.damage = Dtarget`；`Dsharer` 是被动 Direct Troop Loss，不是第二个 DamageEvent。
2. DISTRIBUTION P0 明确继承 DAMAGE_SHARE 的外围 DamageEvent 规则；承担者损失同样不是 DamageEvent，原目标最终以 `Dtarget` 完成正常受伤后续语义。
3. Chain 监听的是合法伤害结算，而不是任意兵力变化；Share / Distribution participant derived loss 均被阻止再次触发 Chain。
4. Chain P0 又要求 trigger node 在源伤害后仍存活。只要它仍存活，`Dtarget < currentTroops_before_commit`，因此：

```text
ActualTargetTroopLoss = Dtarget
```

在真正可执行 Chain 的场景中，B/C 两层数值恰好相同，但合同语义仍应绑定 `Dtarget`，不能倒过来把统计或 clamp 值当输入定义。

### 5.3 DAMAGE_SHARE example

```text
Dtotal = 1000
Share R = 50%
Dsharer = 500
Dtarget = 500
trigger node survives
```

则：

```text
TriggerNodeResolvedDamage = 500
Chain base = 500
```

不是 1000。

分担者的 500：

```text
Attributed Direct Troop Loss
→ Chain = BLOCKED
```

### 5.4 DISTRIBUTION example

```text
Dtotal
→ Distribution
→ Dtarget
→ participant Direct Troop Loss
```

若原目标最终存活：

```text
TriggerNodeResolvedDamage = Dtarget
```

participant loss：

```text
→ Chain = BLOCKED
```

### 5.5 Overkill / source survival

场景：

```text
trigger node currentTroops = 100
assigned Dtarget = 1000
```

结果：

```text
actual committed = 100
trigger node dies
Chain = CANCELLED
```

所以不存在“该次 Chain 应按 1000 还是 100 传播”的可执行分支。

场景：

```text
currentTroops = 1000
Dtarget = 800
```

结果：

```text
actual committed = 800
source survives
TriggerNodeResolvedDamage = 800
```

场景：

```text
currentTroops = 801
Dtarget = 800
→ source survives with 1 troop
→ TriggerNodeResolvedDamage = 800
```

结论：

```text
CHNS9 blocker candidate 1 = RESOLVED
NO new blocker
```

---

## 6. Trigger Eligibility Audit

必须区分：

```text
legal resolved zero
!=
cancelled / absorbed DamageEvent
```

当前唯一矩阵：

| Source Damage Family | Chain verdict |
|---|---|
| NormalAttack | `ALLOWED` |
| ActiveSkill Damage | `ALLOWED` |
| Assault Damage | `ALLOWED` — 属于合法战法伤害 DamageEvent |
| Periodic Damage | `ALLOWED` |
| Cleave | `ALLOWED` |
| Counter | `ALLOWED` |
| DamageShare derived loss | `BLOCKED` |
| Distribution participant loss | `BLOCKED` |
| Chain feedback | `BLOCKED` |
| Self-cost / sacrifice | `NOT APPLICABLE` — 纯 cost troop mutation 不是合法 DamageEvent trigger |
| legal zero damage | `ALLOWED` |
| Evasion-cancelled damage | `BLOCKED` |
| Resistance-cancelled / absorbed damage | `BLOCKED` |

### 6.1 Legal zero

例如 Weakness：

```text
legal DamageEvent
→ Dtotal = 0
→ Share / Distribution may still legally resolve zero partition
→ post-partition Dtarget = 0
→ trigger node survives + Chain operational
→ Chain executes with 0
```

### 6.2 Cancelled / absorbed event

```text
Evasion success
→ DamageEvent cancelled upstream
→ no resolved trigger node DamageEvent
→ no Chain window

Resistance success
→ DamageEvent absorbed/terminated upstream
→ no Chain window
```

禁止：

```text
if damage == 0: always Chain
```

正确门禁是：

```text
legal resolved DamageEvent
AND source survives
AND source activeChainEffect exists
```

Result：`PASS`。

---

## 7. Inline / Deferred Ordering Audit

### 7.1 Default

冻结：

```text
PER DAMAGE INSTANCE
```

默认：

```text
Damage Instance
→ settle source node damage
→ source death check
→ Chain state check
→ Chain INLINE
→ Chain complete
→ continue outer flow
```

多段战法：

```text
Hit1 → Chain1
Hit2 → Chain2
Hit3 → Chain3
```

禁止按：

```text
skill_id
action_id
```

整段去重。

### 7.2 NormalAttack main-target special defer

当同一次普通攻击存在 Cleave：

```text
Main normal-attack damage
↓
main-target Chain qualification created
↓
Cleave target #1
    ↓
    Cleave damage
    ↓
    target #1 Chain INLINE
↓
Cleave target #2
    ↓
    Cleave damage
    ↓
    target #2 Chain INLINE
↓
Cleave complete
↓
main-target Deferred Chain
↓
CounterBatch
↓
Assault / Combo according to their own contracts
```

因此：

```text
Deferred Chain BEFORE Counter = FROZEN
```

COMBO 后续 death/lifecycle findings 仍由 `CBS9-*` 管辖，本轮不替其修复。

Result：`PASS`。

---

## 8. Deferred JIT / Parameter Binding Audit

Deferred Chain 不是完整伤害事件快照，只是资格对象。

### 8.1 Fixed field

触发时固定：

```text
trigger node identity
triggerDamage = post-partition Dtarget of that triggering Damage Instance
parent damage provenance identity
```

### 8.2 Live fields at execution

执行时 JIT：

```text
source.alive
activeChainEffect existence
activeChainEffect.owner
activeChainEffect.ratio
activeChainEffect metadata
```

场景：

```text
B takes 500
old Chain OwnerA / 20%

while waiting during Cleave:
old Chain removed
new Chain OwnerB / 30%

Deferred Chain executes
```

结果：

```text
triggerDamage = 500
ratio = 30%
damage owner = OwnerB
kill owner = OwnerB
```

若执行前：

```text
B dies
or
activeChainEffect removed / expired / cleansed
```

则：

```text
Deferred Chain CANCELLED
```

### 8.3 Owner death is not source-node death

必须区分：

```text
trigger node / Chain holder
!=
Chain effect owner / applier
```

冻结：

```text
effect owner dead
→ holder's Chain can remain operational
→ Chain still damages
→ attribution remains dead owner
→ owner-side follow-up benefit skipped
```

因此禁止：

```text
if chainEffect.owner.dead:
    cancelChain()
```

Result：`PASS`。

---

## 9. Propagation Target Pool Audit

传播目标的当前资格：

```text
same camp as trigger node
AND alive now
AND active Chain now
AND target != trigger node
```

`same camp` 的锚点是：

```text
trigger node 当前实际 battle-side relationship
```

不是：

```text
original attacker camp
original damage owner camp
Chain effect owner camp
```

Chain 不重新进入：

```text
ConfusionTargetSelector
TauntTargetSelector
Guard redirect
```

因为它根本不是一个新的攻击目标选择动作。

### 9.1 Broadcast, not partition

```text
triggerDamage = 500
ratio = 50%
C/D/E valid

C = 250
D = 250
E = 250
```

不是：

```text
250 / 3
```

某个 target overkill 只影响该 target 的：

```text
AppliedTroopLoss = min(ChainCalculatedDamage, CurrentTroops)
```

不会修改 D/E 的理论 `ChainCalculatedDamage`。

Result：`PASS`。

---

## 10. Multi-Target Traversal Audit

### 10.1 Fixed slot order

冻结顺序：

```text
slot 0 commander
→ slot 1 deputy
→ slot 2 deputy
```

传播源自身在轮到对应 slot 时通过：

```text
target != trigger node
```

被排除；其余 slot 保留固定顺序。

禁止：

```text
set iteration order
dictionary order
RNG order
```

### 10.2 JIT target revalidation

P0 明确同时冻结：

```text
传播目标池不是不可变快照
+
slot-order iteration + JIT target revalidation
```

因此候选身份语义已经唯一：

```text
固定遍历 battle-side slot 0 → 1 → 2
每个 slot 到达时读取当前 live state
每个 slot 最多访问一次
```

### 10.3 Mid-loop newly eligible target

场景：

```text
传播开始时 D 没有 Chain
C 先结算
C 的下游效果在 D 的 slot 到达前给 D 新施加 Chain
```

由于：

```text
target pool is not immutable snapshot
+
JIT active Chain check at target turn
```

所以：

```text
D 若位于尚未访问的后续 slot
→ D 加入本次广播
→ receives current trigger node's Chain feedback
```

反之：

```text
某 earlier slot 已经被访问并跳过
之后它才获得 Chain
→ 不 retroactively 回头插入
```

因为 slot-order iteration 不重启、不回扫。

因此外部行为为：

```text
new later-slot eligibility = INCLUDED
new already-passed-slot eligibility = NOT REVISITED
no duplicate target
no slot reorder
```

结论：

```text
CHNS9 blocker candidate 3 = RESOLVED
```

### 10.4 Target death

P0：

```text
C dies
→ only C settlement ends
→ D / E continue
```

普通目标死亡没有歧义。

Result：`PASS`。

---

## 11. Lifecycle / Reapplication Audit

### 11.1 Single instance

冻结：

```text
one unit → one active Chain instance
```

同源再次施加：

```text
REFRESH / OVERWRITE current instance
owner / ratio / metadata updated according to the new successful application
remaining duration reset to 2
```

异源再次施加：

```text
later source overwrites earlier source
owner / ratio / metadata replaced
remaining duration reset to 2
```

明确：

```text
first-in wins = NO
stronger wins = NO
multiple coexist = NO
```

### 11.2 Ratio binding

Stage9 Chain runtime 消费的是：

```text
activeChainEffect.ratio
```

该字段属于当前状态实例。

因此：

```text
execution-time read = LIVE READ OF CURRENT INSTANCE FIELD
```

不是：

```text
execution-time recalculate source attributes automatically
```

具体来源战法如何计算 ratio、是否在成功重新施加时重新计算，属于：

```text
SOURCE-SKILL RESPONSIBILITY
```

Stage9 不得凭空编造属性公式。

### 11.3 Duration

冻结：

```text
duration = 2
Duration owner = holder
Tick = holder ACTION_START
1 → 0 => immediate physical removal
then periodic damage / later action logic
```

震慑 / Cannot Act：

```text
ACTION_START still occurs
→ Chain duration ticks
→ later actual action may fail
```

### 11.4 Apply-round boundary

CHAIN P0 没有定义 GUARD 式：

```text
if currentRound == applyRound: skip tick
```

也没有其他 apply-round exemption。

由于 duration 已被事件化定义为：

```text
while instance exists, holder ACTION_START ticks it
```

所以唯一合同行为是：

```text
Chain successfully applied BEFORE holder's ACTION_START in the same round
→ that ACTION_START sees the instance
→ consumes one duration tick

Chain applied AFTER holder already passed ACTION_START
→ first tick waits until holder's next ACTION_START
```

这不是从其他状态类推，而是当前 P0 的 event-anchor 直接结果。

因此：

```text
CHNS9 blocker candidate 4 = RESOLVED
```

若某具体来源战法选择“延迟注册 Chain state”到别的时点，那属于该来源战法 Apply timing，不属于 690097 state runtime 自己增加 apply-round exemption。

### 11.5 Cleanse / Dispel

冻结：

```text
negative cleanse / dispel
→ immediate physical removal
```

Deferred Chain 若在等待期间被清掉：

```text
execute-time activeChainEffect == null
→ CANCEL
```

### 11.6 Suppression

当前 P0 没有冻结一个通用：

```text
CHAIN SUPPRESSED lifecycle state
```

也没有证据允许把 FALSE_REPORT / owner disabled 自动映射成 Chain suppression。

当前已冻结的是：

```text
owner death does not disable Chain
physical removal / expiry invalidates Chain
```

任何未来来源技能若要求 source-bound operational suppression，必须由该 source-skill contract 显式提供，不能在 690097 通用状态层自行发明。

Result：`PASS`。

---

## 12. Attribution / Owner Death Audit

冻结归属：

```text
chain_effect_owner
=
trigger node current activeChainEffect owner

chain_damage_owner
=
chain_effect_owner

chain_kill_owner
=
chain_effect_owner
```

原始伤害来源：

```text
does NOT own Chain feedback damage
```

传播目标自己的 Chain owner / ratio：

```text
does NOT participate in the current received feedback calculation
```

只在该单位未来自己成为合法 trigger node 时使用。

### Owner dead

```text
effect owner dies
→ state stays on holder if otherwise valid
→ duration continues
→ holder later takes legal damage
→ Chain still works
→ damage / kill attribution remains dead owner
→ dead owner's owner-dependent recovery / benefit is skipped
```

因此 provenance 至少要区分：

```text
physical triggering damage source
Chain effect owner
trigger node
feedback victim
credit owner
parent Damage Instance
```

Result：`PASS`。

---

## 13. Share / Distribution / Cleave / Counter Audit

### 13.1 CHAIN × DAMAGE_SHARE

双向冻结：

```text
Share derived loss → Chain = BLOCKED
Chain TRUE_FEEDBACK → Share = BLOCKED
```

原目标主 DamageEvent：

```text
Dtotal
→ Share
→ Dtarget
→ target survives
→ Chain base = Dtarget
```

不得使用 `Dtotal`。

### 13.2 CHAIN × DISTRIBUTION

P0 × P0 合并：

```text
Distribution participant Direct Troop Loss → Chain = BLOCKED
Chain TRUE_FEEDBACK → Distribution = BLOCKED
```

原目标：

```text
Dtotal
→ Distribution
→ Dtarget
→ target commits last
→ target survives
→ Chain base = Dtarget
```

Distribution P0 已将 participant loss 定义为非 DamageEvent，因此不需要 CHAIN P0 再逐字重复一次才能得出 BLOCKED。

### 13.3 CHAIN × CLEAVE

冻结：

```text
Cleave → Chain = ALLOWED
Cleave target Chain = INLINE
NormalAttack main-target Chain = DEFERRED when Cleave exists
```

`CLVS9-B01` 对 Cleave 自己的 `MainAttackFinalDamage` 层仍未解决，因而会作为上游数值依赖影响：

```text
Cleave derived amount
→ Cleave target normal settlement
→ possible Share/Distribution
→ Cleave target Dtarget
→ Chain base
```

但一旦合法 Cleave target 的 post-partition `Dtarget` 已确定，Chain 本身的 trigger base 不再有第二重歧义。

所以：

```text
NO duplicate CHAIN blocker
CLVS9-B01 remains OPEN
```

### 13.4 CHAIN × COUNTER

Counter P0：

```text
Counter → Chain = ALLOWED
```

流程：

```text
Counter damage
→ target commits normal damage
→ if target survives and Chain active
→ Chain INLINE
```

若 Counter 将原攻击者打死：

```text
trigger node dead
→ Chain CANCELLED
```

这与 Chain P0 自身一致。

Counter-kill 后 Assault / Combo 是否继续仍由 `CBS9-B01` 等 OPEN finding 管辖，本轮不裁决。

Result：`PASS`。

---

## 14. Death / Battle Termination Audit

这是本轮第三最高风险项。

### 14.1 Trigger node death

冻结 death check 位于：

```text
source Damage troop commit
→ trigger node death check
→ if dead: no Chain qualification/execution
```

禁止：

```text
先生成完整 Chain broadcast
→ 再发现 trigger node 已死亡
```

### 14.2 Propagated ordinary target death

```text
ordinary propagated target dies
→ finish that target settlement
→ continue later slots
```

### 14.3 Commander death mid-broadcast

这里当前不是 UNKNOWN。

CHAIN P0 §8.4 使用全称规则：

```text
target death
→ only current target settlement ends
→ remaining targets continue
```

更关键的是 R5 存在专门 Chain commander-death 直接证据：

```text
Chain broadcast kills commander
→ remaining linked teammates continue receiving Chain
→ current Chain traversal completes
→ then commander-death collateral / Victory finalization
```

R5 对该直接样本等级为：

```text
Grade C / 5 cases
```

因此当前 P0 + direct R5 supporting evidence 可以唯一裁决：

```text
commander propagated target dies
→ remaining slot(s) CONTINUE
```

不是：

```text
commander dies
→ immediately stop current Chain broadcast
```

结论：

```text
CHNS9 blocker candidate 2 = RESOLVED
```

### 14.4 Logical victory vs finalization

必须分开：

```text
commander currentTroops reaches 0
→ logical victory condition becomes satisfied

but current Chain atomic traversal owns remaining slots
→ traversal continues

Chain block complete
→ commander-death collateral / battle Victory finalization
→ no future independent action scheduling
```

因此实现不能让一个过早的：

```text
battle.finished = true
```

在 commander feedback commit 后立即使 slot1 / slot2 loop return。

更合适的是显式区分：

```text
victoryConditionSatisfied
battleFinalizationPending
battleTerminated
```

或等价状态。

### 14.5 Death / termination matrix

| Scenario | Chain behavior |
|---|---|
| ordinary propagated target dies | current target ends; later slots continue |
| commander propagated target dies | later slots continue; victory finalization after current Chain broadcast |
| trigger node is commander and survives source damage | Chain may execute normally |
| trigger node dies from source damage | Chain cancelled |
| enemy commander already died and battle was finalized before a new Chain starts | no new Chain scheduling |
| battle victory condition becomes true mid-broadcast | do not abort current Chain traversal; finalization waits until broadcast completes |

Result：`PASS`。

---

## 15. Restricted Settlement / Stage8 Audit

CHAIN 与 CLEAVE 不能塞进同一个“万能派生伤害管线然后配十几个 boolean”。

Cleave 需要：

```text
derived value
→ Evasion
→ Resistance
→ partition
→ troop loss
→ selected callbacks
```

CHAIN 则是：

```text
post-partition trigger-node resolved damage
→ ratio
→ TRUE_FEEDBACK
→ restricted attributed troop-loss settlement
→ no normal defensive / partition / hit callbacks
```

Stage8 已冻结：

```text
DamageSystem.calculate
= unique theoretical standard-damage calculation entry

DamageResolutionSystem
= theoretical result → troop mutation / battle fact coordinator

TroopSystem
= troop mutation boundary
```

CHAIN 不需要重新进入标准 `DamageSystem.calculate()`。

推荐架构分类：

```text
B. typed DerivedDamagePolicy / TRUE_FEEDBACK policy
+
C. Stage8-compatible extension seam reusing TroopSystem / provenance / statistics ownership
```

也可以在 Stage9 外层表现为一个 restricted settlement wrapper，但必须保留 typed provenance。

当前没有证据要求修改：

```text
Stage8 base formula ownership
Stage8 normal modifier ordering
Stage8 normal HitResolution ownership
```

所以：

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
```

结论：

```text
CHNS9 blocker candidate 6 = NOT FOUND
```

---

## 16. Provenance / RNG / Rounding Audit

### 16.1 Provenance

建议 Stage9 engineering model 至少保留：

```text
root_action_id
parent_damage_event_id
event_family = TRUE_FEEDBACK
derivation_kind = CHAIN
triggerNode
triggerDamage
chainEffectOwner
chainEffectSourceSkill / metadata
chainRatio
feedbackTarget
chainCalculatedDamage
actualAppliedTroopLoss
creditOwner
```

这些是 simulator engineering fields，不得声称为官方战报原生字段。

### 16.2 RNG

CHAIN：

```text
fixed battle-side slot order
no random membership selection
no random target ordering
```

因此 Chain target traversal 不应调用 `RandomSystem`。

### 16.3 Rounding / integerization

这是本轮唯一真实实现 blocker。

P0 冻结：

```text
ChainCalculatedDamage
=
TriggerNodeResolvedDamage × ChainRatio
```

但没有冻结乘法结果的整数化规则：

```text
round ?
floor ?
ceil ?
truncate ?
banker's rounding ?
other project-global integerization ?
```

DAMAGE_SHARE / DISTRIBUTION P0 在各自数学里显式写了 `round(...)`；CHAIN P0 没有对应条款。

更重要的是，Chain 被明确冻结为：

```text
TRUE_FEEDBACK
→ no standard base formula
→ restricted direct troop-loss settlement
```

因此不能自动宣称它继承 Stage8 标准 `DamageSystem.calculate()` 内部的普通伤害取整点。Stage8 Freeze Record 也没有冻结一个可无条件应用到所有 Stage9 TRUE_FEEDBACK 数值的“全局派生伤害整数化算子”。

若：

```text
TriggerNodeResolvedDamage × ratio = 100.5
```

则不同整数化规则可能改变：

```text
actual troop loss
kill / survive
later target world state
battle outcome
```

所以不能把它降格为纯展示差异。

Result：**CHNS9-B01**。

---

## 17. Cross-Mechanism Consistency

| Cross Item | Verdict | Note |
|---|---|---|
| CHAIN × CONFUSION | `NOT APPLICABLE` | Chain target topology does not reopen a TargetSelector |
| CHAIN × TAUNT | `NOT APPLICABLE` | no NormalAttack primary-target selection |
| CHAIN × GUARD | `CONSISTENT` | Guard can decide upstream actualTarget; that actual damaged node may later trigger Chain; feedback does not rerun Guard |
| CHAIN × COMBO | `CONSISTENT` for Chain-owned boundary | Chain completes before Counter / later Combo checkpoint; inherited `CBS9-*` remain OPEN downstream |
| CHAIN × CLEAVE | `CONSISTENT` | Cleave target Chain inline; main-target Chain deferred; `CLVS9-B01` remains upstream numeric dependency |
| CHAIN × COUNTERATTACK | `CONSISTENT` | Counter damage may trigger Chain; lethal Counter target death cancels that Chain |
| CHAIN × DAMAGE_SHARE | `CONSISTENT` | base = post-Share Dtarget; Share derived loss blocked; Chain feedback cannot Share |
| CHAIN × DISTRIBUTION | `CONSISTENT` | base = post-Distribution Dtarget; participant loss blocked; Chain feedback cannot Distribution |

### Recursion matrix

| From Chain | To | Verdict |
|---|---|---|
| Chain | Chain | `BLOCKED` |
| Chain | Share | `BLOCKED` |
| Chain | Distribution | `BLOCKED` |
| Chain | FirstAid | `BLOCKED` |
| Chain | Counter | `BLOCKED` |
| Chain | Cleave | `NOT APPLICABLE / BLOCKED BY EVENT IDENTITY` |
| Chain | Lifesteal | `BLOCKED` |
| Chain | StrategyRecovery | `BLOCKED` |
| Chain | Guard | `NOT APPLICABLE` |
| Chain | Taunt | `NOT APPLICABLE` |
| Chain | Combo | `NOT APPLICABLE` |

根因是：

```text
TRUE_FEEDBACK event identity
+
restricted settlement permission policy
```

不是把状态名做成一排硬编码 `if`。

---

## 18. Documentation Drift

### CHNS9-D01 — state-research minimum skeleton is partially superseded

当前：

```text
states/functional/minimum_usable/690097_CHAIN_LINK.md
```

仍把以下列为：

```text
Feedback Event Family = UNRESOLVED
Eligible Damage Families = UNRESOLVED
Multiple Chain Sources = UNRESOLVED
Cleanse / Reapplication = UNRESOLVED
Precise Event Ordering = UNRESOLVED
```

但 battle P0 已明确冻结：

```text
TRUE_FEEDBACK
Normal / Skill / Periodic / Cleave / Counter eligible
single instance + refresh / overwrite
cleanse / dispel immediate removal
PER-DAMAGE INLINE + main-target deferred special case
```

所以该 minimum skeleton 是：

```text
PARTIALLY SUPERSEDED
```

### CHNS9-D02 — R4 recursion report is incomplete after Distribution freeze

`R4_RECURSION_PERMISSION_MATRIX.md` 的 Chain trigger blocked list 明确写了：

```text
Share Passive Numeric Settlement → Chain = BLOCKED
```

但没有同步后续 Distribution P0 已冻结的：

```text
Distribution participant derived loss → Chain = BLOCKED
```

当前 `STAGE9_CORE_ARBITRATION_RULES_V2.md` 已正确补上该项，所以这是低权威报告同步漂移，不是机制 blocker。

### CHNS9-D03 — Evidence Matrix global research-status footer is stale

Evidence Matrix 的 CHAIN 行本身基本正确，包括：

```text
EM-16 Chain feedback math
EM-18 Chain pipeline
EM-22 target death continuation
```

但底部仍写：

```text
Share Core Mechanics = NEXT RESEARCH TARGET
Counter self-recursion = PENDING FINAL EXTRACTOR AUDIT
```

已被后续 Share / Counter P0 supersede。

这是全局文档代际漂移，不改变 CHAIN P0。

### Non-drift / conservative status notes

```text
core_arbitration_v2/README.md
→ Chain frozen summary is substantially current

STATE_MECHANICS_INDEX.md
→ 690097 still MINIMUM_USABLE
```

本轮**不**把 `STATE_MECHANICS_INDEX = MINIMUM_USABLE` 单独判为错误，因为：

```text
state repo has no formal Chain MECHANISM_CONTRACT mirror
+
CHNS9-B01 still blocks full runtime contract readiness
```

因此该状态标记虽然没有展示 battle repo 的 core-freeze 进展，但仍是保守而不虚假的导航状态。

状态研究仓 root README 的旧 research target / blanket death wording属于前轮已经识别的全局文档代际问题，本轮不重复制造新的 CHNS9 finding。

---

## 19. Findings

### CHNS9-B01 — BLOCKER — ChainCalculatedDamage integerization is not frozen

**Severity:** `BLOCKER`

当前：

```text
TriggerNodeResolvedDamage × ChainRatio
```

可能产生非整数，而 P0 未规定整数化函数。TRUE_FEEDBACK 又绕过标准 Damage formula，因此不能安全继承普通伤害取整点。

Required narrow re-freeze：

```text
明确 ChainRatio 乘法后的整数化规则
并至少覆盖：
- fractional < .5
- exact .5
- fractional > .5
- lethal boundary where one-point difference changes death
```

只需补这一条数学边界，不需要推翻当前 Chain kernel。

### CHNS9-D01 — DOC_DRIFT — state-research minimum skeleton still marks frozen Chain core fields unresolved

```text
Blocking: NO
Action: sync only after narrow Chain re-freeze / formal state contract publication
```

### CHNS9-D02 — DOC_DRIFT — R4 missing Distribution participant loss → Chain = BLOCKED

```text
Blocking: NO
Authority already correct in newer P0/P2
```

### CHNS9-D03 — DOC_DRIFT — Evidence Matrix footer is stale for Share / Counter current state

```text
Blocking: NO
Historical evidence rows remain usable
```

### CHNS9-H01 — HARDENING — encode Chain as typed one-pass slot traversal with restricted settlement

Stage9 runtime tests should structurally assert：

```text
1. triggerDamage = post-partition Dtarget
2. lethal trigger-node damage cancels Chain
3. legal zero still opens Chain
4. cancelled/absorbed event does not
5. slot 0 → 1 → 2, each slot max once
6. later-slot newly linked before visitation joins current broadcast
7. passed slot is not revisited
8. propagated commander death does not abort remaining current broadcast
9. feedback bypasses Share / Distribution / Guard / hit callbacks
10. owner death does not cancel holder Chain
11. Deferred Chain fixes triggerDamage but live-reads current owner/ratio
```

### Finding totals

```text
BLOCKER   = 1
MAJOR     = 0
MINOR     = 0
DOC_DRIFT = 3
HARDENING = 1
TOTAL     = 5
```

### Candidate disposition

```text
candidate 1 TriggerNodeResolvedDamage layer ambiguity
→ RESOLVED, no finding

candidate 2 commander death mid-broadcast
→ RESOLVED, no finding

candidate 3 candidate-set snapshot vs mid-loop eligibility
→ RESOLVED, no finding

candidate 4 apply-round / duration boundary
→ RESOLVED from holder ACTION_START event semantics, no exemption

candidate 5 Chain rounding rule
→ CONFIRMED BLOCKER = CHNS9-B01

candidate 6 Stage8 restricted settlement requires formal reopen
→ NOT FOUND
```

### Inherited findings disposition

```text
CFS9-B01 = KEEP OPEN

CBS9-B01 = KEEP OPEN
CBS9-B02 = KEEP OPEN
CBS9-B03 = KEEP OPEN
CBS9-M01 = KEEP OPEN
CBS9-M02 = KEEP OPEN
CBS9-M03 = KEEP OPEN

CLVS9-B01 = KEEP OPEN
CLVS9-B02 = KEEP OPEN
CLVS9-B03 = KEEP OPEN
CLVS9-B04 = KEEP OPEN
CLVS9-M01 = KEEP OPEN
```

CHAIN 提供的直接 P0 约束对这些 finding 的影响只有：

```text
IMPACT ON EXISTING FINDING:
- Chain itself confirms its Deferred work occurs before Counter.
- Chain itself confirms its current broadcast can finish across propagated commander death.
- Neither fact re-freezes COMBO death/Victory semantics.
- TriggerNodeResolvedDamage = post-partition Dtarget does not define Cleave MainAttackFinalDamage.
```

因此没有 finding 被本轮偷偷关闭。

---

## 20. Final Verdict

# REOPEN REQUIRED

Reopen scope：

```text
NARROW REOPEN ONLY
```

CHAIN 已确认且应保留的核心合同：

```text
TriggerNodeResolvedDamage = post-partition target DamageEvent amount Dtarget
Share after Chain base = Dtarget, not Dtotal
Distribution after Chain base = Dtarget, not Dtotal
legal resolved zero can Chain
Evasion / Resistance cancelled event cannot Chain
lethal trigger-node source damage cancels Chain
PER-DAMAGE INSTANCE
INLINE by default
main NormalAttack target + Cleave = Deferred Chain
Cleave target Chain = INLINE
Deferred triggerDamage fixed
Deferred owner / ratio / metadata live-read
same-camp + alive + active Chain + not source target pool
fixed slot 0 → 1 → 2
slot JIT revalidation
later-slot newly eligible target can join current broadcast
already-passed slot is not revisited
broadcast, not partition
one target overkill does not change siblings
ordinary propagated target death does not abort siblings
commander propagated target death does not abort siblings
Victory finalization waits until current Chain broadcast completes
Cleave → Chain allowed
Counter → Chain allowed
Share / Distribution participant derived loss → Chain blocked
Chain → Share / Distribution / FirstAid / Counter / Chain / recovery blocked
single-instance Chain state
same-source refresh / different-source overwrite
owner death does not cancel holder Chain
holder ACTION_START duration tick
no apply-round exemption
cleanse / dispel immediate removal
fixed slot order / no RNG
Formal Stage8 Reopen = NO
```

唯一必须 re-freeze 后才能称：

```text
FULL 690097 CONTRACT READY
```

的是：

```text
ChainCalculatedDamage integerization / rounding rule
```

最终准入：

```text
CHAIN CORE RUNTIME TOPOLOGY = READY
CHAIN RESTRICTED SETTLEMENT SHAPE = READY
CHAIN NUMERIC INTEGERIZATION = NOT READY
FULL 690097 CONTRACT READY = NO
CHAIN NARROW REOPEN REQUIRED = YES
FORMAL STAGE8 REOPEN REQUIRED = NO
NEXT MECHANISM = DAMAGE_SHARE
```
