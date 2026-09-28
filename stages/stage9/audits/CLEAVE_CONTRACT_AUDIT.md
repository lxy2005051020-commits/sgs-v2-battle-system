# CLEAVE Contract Audit

> Audit target: `690084 CLEAVE / SPLASH / 群攻`  
> Audit date: 2026-09-13  
> Audit type: Stage 9 Frozen Contract Independent Review  
> Final verdict: **REOPEN REQUIRED**  
> Reopen scope: **NARROW REOPEN** — preserve the confirmed Cleave derived-damage kernel; reopen only the unresolved base-layer, full-state, target-order, and death/termination boundaries identified below.

---

## 1. Repository Baseline

本轮开始时重新读取两个仓库 `main`，没有沿用聊天记录中的旧 HEAD。

```text
battle repo:
lxy2005051020-commits/sgs-v2-battle-system
exact main HEAD = 1b5605d402370372ff92db276834981b0a74a9e2
audit(stage9): verify combo frozen contract

state research repo:
lxy2005051020-commits/sgs-state-mechanics-research
exact main HEAD = 9d86e54c407913ff020bafacf8196085780b99c6
docs(index): mark combo frozen and scope death baseline
```

已完整继承前四轮独立审计：

```text
CONFUSION_CONTRACT_AUDIT.md
TAUNT_CONTRACT_AUDIT.md
GUARD_CONTRACT_AUDIT.md
COMBO_CONTRACT_AUDIT.md
```

继承状态：

```text
CFS9-B01 = OPEN

COMBO:
CBS9-B01 = OPEN — Counter-kill death conflict
CBS9-B02 = OPEN — COMBO §5 lifecycle ownership conflict
CBS9-B03 = OPEN — Victory termination conflict
CBS9-M01/M02/M03 = OPEN
```

本轮不会关闭上述 finding；仅判断 CLEAVE 是否与其发生新的实现交集。

Authority priority：

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

特别规则：

```text
P0 CORE MECHANISM FREEZE
!=
P0 FULL STATE CONTRACT
```

---

## 2. Authoritative Freeze Source

CLEAVE 当前 P0：

```text
stages/stage9/research/core_arbitration_v2/
STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md

current blob SHA = e1a70b82afc1246b9ecdb506d823deb85cb18f7a
status = CORE MECHANISM FROZEN
```

冻结提交：

```text
ddacbda09fe2f95e3b00564ebed21cefaeefcb5c
docs(research): freeze confirmed stage 9 cleave mechanics
```

P0 冻结的核心表达为：

```text
MainAttackFinalDamage
× CleaveRatio
= CleaveDerivedDamage
```

并冻结：

```text
Cleave = DERIVED DAMAGE
Cleave != new NormalAttack
Cleave != second base-damage calculation
Cleave != unconditional direct troop loss
```

状态研究仓当前没有：

```text
states/functional/cleave/
states/functional/splash/
```

正式 `MECHANISM_CONTRACT.md`。

当前仅有：

```text
states/functional/minimum_usable/690084_SPLASH.md
blob = 569d07b10b9bb937dd98a6aa0e3f527036bbf11b
Stage = MINIMUM_USABLE
```

该 skeleton 自己仍把以下内容列为 Deferred：

```text
Damage Formula
Multi-source / Reapplication
Precise Event Ordering
Modifier Compatibility
Evasion / Resistance / Distribution / Damage Share
```

后续 P0 已经覆盖其中一部分 core interaction，但并没有把完整 L2 state lifecycle 一并冻结。

---

## 3. Contract Scope: Core vs Full State

### 3.1 已冻结的 Core Kernel

以下结论可以保留：

```text
NORMAL_ATTACK-derived main hit
→ derive Cleave damage from an already-resolved main-hit value
→ no new base formula
→ no secondary target defense/offense recalculation
→ Evasion allowed
→ Resistance allowed
→ successful Resistance consumes one charge
→ Share allowed
→ FirstAid allowed
→ Chain allowed
→ Counter blocked
→ Cleave recursion blocked
→ DamageType inherited
```

这足以定义一个 **Cleave derived-damage operator** 的主要许可边界。

### 3.2 尚未形成 Full State Contract

当前 P0 没有冻结完整 `690084` 状态实例语义：

```text
Apply
Reapply
Refresh
Stack
Replace
Duration
Expiration
Source death
Holder death
Suppression
Dispel
Multiple sources
Source ordering
Ratio snapshot vs live read
```

而状态研究方法明确把这些属于 L2 STATE_INSTANCE_LIFECYCLE 的项目列为状态机制 IN SCOPE。

因此：

```text
CLEAVE CORE MECHANISM FROZEN = YES
FULL 690084 STATE CONTRACT READY = NO
```

R6 的历史研究存在：

```text
多个群攻来源
→ 按战法栏位顺序判定
→ 独立执行各自溅射
```

但它只有 P3 权威，不能代替缺失的 P0 state container / reapplication / lifecycle 合同。

Result：**CLVS9-B02**。

---

## 4. State Kernel Audit

### 4.1 Event identity

CLEAVE 必须保持：

```text
parent = one NormalAttack instance
family/source_type = CLEAVE
NormalAttackIdentity = false
```

因此 Cleave secondary damage 不产生新的：

```text
Guard Check
Taunt Check
Confusion primary-target selection
Combo Checkpoint
Counter ON_NORMAL_ATTACK_RECEIVED window
Cleave recursive window
```

它仍然是一个合法 DamageEvent-family derived damage，因此可以按 permission matrix 进入：

```text
Evasion
Resistance
Share / Distribution partition
FirstAid
Chain
DamageType-specific recovery eligibility
```

### 4.2 SourceType vs DamageType

两者必须正交：

```text
source_type / event_family = CLEAVE
damage_type = WEAPON | STRATEGY
```

不得实现：

```text
Cleave == Weapon
```

Weapon/Strategy 只决定继承的 DamageType 以及相应恢复资格，不改变 CLEAVE 事件身份。

Result：`PASS`。

---

## 5. Derived Damage Base Audit

这是本轮第一核心问题。

### 5.1 当前项目已经存在至少四个不同伤害层

DAMAGE_SHARE / DISTRIBUTION P0 已经明确区分：

```text
normal formula
→ Dtotal
→ damage partition
→ assigned target amount (Dtarget)
→ actual troop-loss commit / troop clamp
→ credited/statistical damage
```

因此以下值不是同一个概念：

```text
A. pre-partition Dtotal
B. post-partition target assigned damage Dtarget
C. actual committed target troop loss
D. credited/statistical damage
```

### 5.2 Cleave P0 没有唯一映射 `MainAttackFinalDamage`

CLEAVE P0 只写：

```text
主攻击最终结算伤害
MainAttackFinalDamage
```

但没有显式冻结它等于：

```text
Dtotal
Dtarget
ActualTargetTroopLoss
battle-log displayed loss
```

Core Arbitration / R3 继续使用“最终结算伤害”措辞，也没有把该变量映射到 Share / Distribution P0 后来建立的正式分层字段。

因此当主普通攻击本身命中一个具有 DAMAGE_SHARE 或 DISTRIBUTION 的 actualTarget 时：

```text
CleaveRatio × Dtotal
```

和：

```text
CleaveRatio × Dtarget
```

会产生不同群攻数值，而当前 P0 无法唯一决定。

这不是变量命名问题，而是战斗结果级语义缺口。

Result：**CLVS9-B01**。

### 5.3 Overkill

场景：

```text
main actualTarget currentTroops = 100
normal formula result = 1000
```

当前 P0 无法证明 Cleave base 应为：

```text
1000
```

还是：

```text
100
```

现有 `r3_cleave_damage_data.json` 的 `main_damage` 来自战报可观察伤害值；当前证据包没有建立一个专门受控的“主目标 overkill calculated value vs actual troop loss”映射来证明哪个内部层等于 `MainAttackFinalDamage`。

同时，Chain P0 已经明确区分：

```text
ChainCalculatedDamage
AppliedTroopLoss
CreditedDamage
```

CLEAVE 不应在没有证据时把这些层混成一个 `finalDamage`。

正式裁决：

```text
MainAttackFinalDamage precise layer = UNRESOLVED
1000 vs 100 overkill base = UNRESOLVED
```

该缺口已包含于 **CLVS9-B01**。

### 5.4 Crit / upstream modifier inheritance

不论 B01 最终选择 Dtotal、Dtarget 或另一个明确层，只要该层位于正常主攻击 Crit / 普通增减伤之后，则：

```text
main-hit Crit effect = INHERITED VIA BASE VALUE
main-hit source-side modifier = INHERITED VIA BASE VALUE
main-hit actualTarget defense/modifier result = INHERITED VIA BASE VALUE
```

而 Cleave secondary 自己：

```text
Crit reroll = BLOCKED
attacker offense recalculation = BLOCKED
secondary defense recalculation = BLOCKED
secondary target damage modifier re-entry = BLOCKED
```

因此不能把“Crit=yes/no”写成一个布尔；正确区分是：

```text
INHERITED VIA BASE VALUE
vs
RE-EVALUATED
```

---

## 6. Pipeline Audit

| Stage | CLEAVE behavior |
|---|---|
| Base formula | `BLOCKED` — no second base formula |
| Source offense | `INHERITED` via main-hit base value; no secondary recalculation |
| Target defense | `INHERITED` only through main-hit base value; secondary target defense is not re-evaluated |
| Crit reroll | `BLOCKED` |
| Main-hit crit inheritance | `INHERITED` via base value |
| Source damage modifier | `INHERITED` via base value |
| Target damage modifier | `BLOCKED` for secondary re-entry; main-hit target modifier result is inherited via base |
| Evasion | `RE-EVALUATED` on each Cleave secondary DamageEvent |
| Resistance / Barrier | `RE-EVALUATED` after Evasion |
| Damage Share | `ALLOWED` / live-read on Cleave secondary target |
| Distribution | `ALLOWED` / live-read on Cleave secondary target, from Distribution P0 inheritance |
| Troop clamp | `RE-EVALUATED` at each committed recipient settlement |
| FirstAid | `ALLOWED` on the normal Cleave target DamageEvent |
| Lifesteal | `ALLOWED` for WEAPON Cleave; exact post-Distribution recovery base remains externally unresolved |
| Strategy recovery | `ALLOWED` for STRATEGY Cleave; exact post-Distribution/multi-target base remains externally unresolved |
| Counter | `BLOCKED` |
| Chain | `ALLOWED` |
| Cleave recursion | `BLOCKED` |

### 6.1 Evasion / Resistance exact order

当前唯一兼容顺序：

```text
CleaveDerivedDamage
→ Evasion
   → success: DamageEvent cancelled; Resistance NOT consumed
→ Resistance
   → success: damage absorbed/invalid; consume 1 Resistance charge
→ damage partition stage
→ troop settlement
```

状态仓 `690083_RESISTANCE.md` 明确：

```text
EVASION BEFORE RESISTANCE
Evasion success -> resistance not consumed
```

同时 Share / Distribution P0 均把 Evasion / Resistance 放在 partition 之前。

### 6.2 Barrier terminology

CLEAVE P0 使用 `Barrier`，当前状态体系使用：

```text
690083 RESISTANCE / 抵御
```

两者在中文机制、消耗 1 次抵御以及 Evasion→Resistance 顺序上对应同一 Gate。当前没有证据支持再建立第二个独立 `Barrier` Gate。

工程规范应统一为：

```text
RESISTANCE (690083)
```

`Barrier` 仅视为旧英文术语。

Result：**CLVS9-D01**。

---

## 7. Target / Guard Audit

GUARD P0 已冻结：

```text
Target Selection
→ originalTarget
→ Guard Check
→ actualTarget
→ Target Lock
```

CLEAVE 锚点必须读取：

```text
post-Guard actualTarget
```

场景：

```text
A attacks B
B guarded by C
→ actualTarget = C
→ Cleave is centered around C's team/context
```

B 只保留 originalTarget provenance；若 B 同时满足 Cleave secondary target 的普通资格，它可以作为副目标重新被群攻命中。

禁止：

```text
originalTarget 曾被选中
→ 获得 Cleave immunity / priority
```

Cleave secondary damage 本身也不会重新执行 Guard。

### 7.1 Secondary target set / order is not P0-complete

CLEAVE P0 没有完整冻结：

```text
secondary candidate pool
secondary count
source/self inclusion/exclusion
stable target ordering
multi-secondary commit order
```

P6 `690084_SPLASH.md` 只写：

```text
目标所在部队的其他存活武将
```

这不足以作为 P0。

“具体来源战法给多少 Cleave ratio / 如何制造状态”可以属于 source-skill layer；但 Stage9 runtime 至少必须获得一个**已解析、稳定排序的 ordered secondary target set**，否则：

```text
secondary #1 Share/Chain/death
```

可能改变：

```text
secondary #2 当前世界状态
```

并产生不同兵损。

在当前没有 P0 明确把 ordered target set 定义为 source-effect input，也没有 P0 定义统一 Cleave selector 的情况下，Stage9 不能自行选择排序规则。

Result：**CLVS9-B03**。

---

## 8. State Lifecycle / Multi-source Audit

### 8.1 Multi-Cleave

P3 R6 支持：

```text
multiple Cleave sources
→ independent execution
→ skill-slot order
→ ratios not merged into one Cleave
```

但当前 Cleave P0 没有正式冻结：

```text
Container = UNIQUE_SLOT | MULTI_INSTANCE_LIST | SOURCE_BOUND EFFECT LIST
same-source reapply
cross-source coexist/replace
execution comparator
```

因此不能把 R6 直接编码成完整 `690084` P0。

### 8.2 Ratio semantics

精确 `CleaveRatio` 来源公式可以安全归类为：

```text
SOURCE-SKILL RESPONSIBILITY
```

如果 Stage9 Cleave operator 接收：

```text
already-resolved cleave_ratio
sourceUnit
sourceSkill
sourceEffect identity
```

则“ratio 如何由来源战法公式计算”不是 CLEAVE blocker。

但是如果 `690084` 本身作为持续 state instance 保存 ratio，则：

```text
snapshot vs live read
refresh replacement
source replacement
```

仍属于状态生命周期，当前没有冻结。

结论：

```text
ratio acquisition formula = NON-BLOCKING SOURCE-SKILL RESPONSIBILITY
ratio binding/lifecycle inside 690084 instance = NOT FULLY FROZEN
```

后者归入 **CLVS9-B02**。

---

## 9. Reaction / Recursion Audit

### 9.1 Recursion Permission Matrix

| From CLEAVE to | Verdict | Basis |
|---|---|---|
| Cleave | `BLOCKED` | Cleave P0 |
| Counter | `BLOCKED` | no NormalAttack identity; Counter P0 trigger gate |
| Chain | `ALLOWED` | Chain P0 + Cleave P0/R4 |
| Share | `ALLOWED` | Cleave P0 + Share P0 |
| Distribution | `ALLOWED` | Distribution P0 inherits Share common DamageEvent eligibility; no Cleave exception |
| FirstAid | `ALLOWED` | Cleave P0 |
| Lifesteal | `ALLOWED` for WEAPON Cleave | Cleave P0 |
| StrategyRecovery | `ALLOWED` for STRATEGY Cleave | Cleave P0 |
| Combo | `NOT APPLICABLE` | no new NormalAttack / no Combo Checkpoint |
| Guard | `NOT APPLICABLE` | no new NormalAttack target-resolution phase |
| Taunt | `NOT APPLICABLE` | no NormalAttack primary-target selector |

### 9.2 Counter identity gate

正确原因是：

```text
Counter trigger requires incoming event has NormalAttack identity
Cleave DamageEvent has no NormalAttack identity
```

因此：

```text
main actualTarget receives main NormalAttack
→ Counter possible later at CounterBatch

Cleave secondary receives Cleave DamageEvent
→ Counter blocked
```

禁止用：

```text
if source_type == CLEAVE: skipCounter
```

作为唯一机制定义；应由 event identity / trigger-family 自然拒绝。

### 9.3 Combo

COMBO 稳定 kernel 仍成立：

```text
NormalAttack #1 → Cleave possible
NormalAttack #2 → Cleave independently possible
Cleave itself → no Combo Checkpoint
```

且：

```text
Attack #1 Cleave / Chain / Counter / Assault
must finish according to owning contracts
before Combo Checkpoint
```

本轮不关闭 COMBO 已开放的 death / lifecycle / Victory findings。

---

## 10. Chain Ordering Audit

Chain P0 与 Core Arbitration 对 Cleave 顺序一致：

```text
Main NormalAttack Damage
↓
main-target immediate reactions
↓
if main-target Chain eligible and Cleave exists:
    defer main-target Chain qualification
↓
Cleave target #1
    ↓
    Cleave damage
    ↓
    target #1 Chain INLINE if eligible
↓
Cleave target #2
    ↓
    Cleave damage
    ↓
    target #2 Chain INLINE if eligible
↓
Cleave complete
↓
main-target Deferred Chain JIT revalidation
↓
CounterBatch
↓
if attacker alive: Assault
↓
if attacker alive and contract permits: Combo checkpoint
```

Deferred main-target Chain 不由 Cleave 复制参数。

Chain P0 已冻结：

```text
triggerDamage = fixed at qualification time
source.alive = JIT recheck
activeChainEffect existence = JIT recheck
owner / ratio / metadata = live-read at execution
```

因此：

```text
Cleave complete
→ return control to Chain-owned deferred qualification
```

没有发现 Cleave P0 与 Chain P0 的直接 ordering contradiction。

Result：`CONSISTENT`。

---

## 11. Share / Distribution Audit

### 11.1 Cleave secondary → DAMAGE_SHARE

明确：

```text
Cleave DamageEvent
→ Evasion
→ Resistance
→ secondary target's current DAMAGE_SHARE check
→ partition
→ target/share settlement
```

读取的是：

```text
Cleave secondary target's Share
```

不是：

```text
main actualTarget's Share
originalTarget's Share
```

Share P0 还明确把 `群攻 / Splash` 列入 Eligible DamageEvent。

### 11.2 Cleave secondary → DISTRIBUTION

结论：

```text
ALLOWED
```

权威来源不是“Distribution 类似 Share”的类推，而是 Distribution P0 的显式继承条款：

```text
DISTRIBUTION inherits DAMAGE_SHARE common pipeline rules
EXCEPT distribution-specific overrides
```

该 P0 同时冻结：

```text
EVASION / RESISTANCE
→ upstream cancellation
→ normal formula / already-established damage value
→ DAMAGE_PARTITION stage
```

而 Share P0 已明确把 Splash/Cleave 纳入外层 DamageEvent 准入。

当前没有 Distribution-specific 条款排除 Cleave。

因此：

```text
Cleave → Distribution = ALLOWED
```

不是 BLOCKER。

### 11.3 Share vs Distribution precedence

当前 P0 冻结：

```text
DAMAGE_SHARE > DISTRIBUTION
```

并且两种状态不会在同一 target 同一 Damage Instance 同时参与 partition。

因此对 Cleave DamageEvent 同样：

```text
Cleave
→ Evasion / Resistance
→ resolve target's effective partition state
→ if DAMAGE_SHARE operational: Share wins
→ otherwise Distribution may execute if operational
```

### 11.4 Main-hit partition vs Cleave base

注意：

```text
Cleave secondary event can enter Share / Distribution
```

已经解决，和：

```text
main hit itself经过 Share / Distribution 后
Cleave base 到底读取 Dtotal 还是 Dtarget
```

是两个不同问题。

后者仍是 **CLVS9-B01**。

---

## 12. Death / Termination Audit

CLEAVE P0 没有冻结一个明确的：

```text
CLEAVE_ATOMIC_BLOCK
```

也没有冻结 pending secondary targets 在死亡/终战边界上的继续/取消规则。

| Scenario | Current result |
|---|---|
| A. main actualTarget dies from main hit | `UNRESOLVED` — P0 没有明确 survival gate，也没有明确 dead anchor 是否仍派生 Cleave |
| B. Cleave secondary target dies | 当前目标 settlement 结束；其自身 Chain 因 trigger node dead 应取消；remaining Cleave targets 是否继续未由 Cleave P0 冻结 |
| C. attacker dies before Cleave phase | `UNRESOLVED` — pending Cleave资格是否作为已产生派生工作继续，没有 Cleave P0 条款 |
| D. attacker dies during Cleave target #1 downstream Chain | current Chain 遵循 Chain P0；回到 Cleave 后 target #2 是否继续未冻结 |
| E. commander dies from Cleave | `UNRESOLVED` — current Cleave block 是否完成后再 Victory 未冻结 |
| F. commander dies from Cleave-triggered Chain | Chain 自己的当前广播可按 Chain P0完成；返回后剩余 Cleave / deferred main Chain / Counter 的终战边界未由 Cleave P0唯一决定 |
| G. one Cleave secondary target dies before later secondaries | remaining secondary continuation not explicitly frozen |
| H. battle logically finishes with pending Cleave targets | current Cleave atomicity vs global Victory barrier not uniquely frozen |

R5 旧模型证明“不同原子块的死亡短路不同”，Chain P0 又只冻结 **Chain 自己**的广播继续规则；这些不能自动外推为 Cleave 原子块规则。

同时 COMBO 独立审计已经证明：

```text
actor death
Victory termination
```

目前存在 P0 级开放冲突，不能拿任何一条旧通用布尔规则直接覆盖 CLEAVE。

不同选择会改变后续 Cleave / Chain / Share 的实际兵损，因此属于实现阻塞。

Result：**CLVS9-B04**。

---

## 13. DamageType / Recovery / Provenance Audit

### 13.1 DamageType inheritance

冻结：

```text
Weapon main source → Weapon Cleave
Strategy main source → Strategy Cleave
```

Cleave provenance 至少需要：

```text
root action
parent NormalAttack instance
Cleave derived event identity
secondary target
source unit
source skill/effect
DamageType
CleaveRatio
resolved base value
```

### 13.2 FirstAid

FIRST_AID P0 的 Trigger 为：

```text
AFTER_DAMAGE_EVENT
PER_ELIGIBLE_DAMAGE_EVENT
```

且伤害比例型急救动态读取“当次受击扣减伤害量”。

Cleave P0 明确 `Cleave → FirstAid = ALLOWED`，因此 Cleave 模块应只发出统一合格 DamageEvent/settlement fact，不应内置 FIRST_AID 专用公式。

### 13.3 Lifesteal / Strategy Recovery

Cleave P0 已冻结资格：

```text
WEAPON Cleave → Lifesteal allowed
STRATEGY Cleave → StrategyRecovery allowed
```

DAMAGE_SHARE P0 进一步明确：

```text
attacker recovery basis
→ original target's post-share DamageEvent Dtarget
→ does not include sharer passive numeric loss
```

因此 Cleave + Share 的恢复口径可以复用统一 Share 语义。

但是当前状态仓：

```text
690094 LIFE_STEAL = MINIMUM_USABLE
Distribution Interaction = UNRESOLVED_FOR_ACCURACY_PHASE

690095 STRATEGY_LIFE_STEAL = MINIMUM_USABLE
Multi-target Recovery Basis = UNRESOLVED_FOR_ACCURACY_PHASE
```

DISTRIBUTION P0 冻结 participant loss 的 attribution/statistics，但没有把“participant attributed direct troop loss 是否计入倒戈/攻心恢复基数”升级成统一恢复合同。

因此：

```text
Cleave → Distribution → Lifesteal/StrategyRecovery exact recovery basis
= UNRESOLVED EXTERNAL RECOVERY CONTRACT
```

这不改变 Cleave DamageEvent 本身是否允许进入 Distribution，也不要求重开 Cleave damage kernel；但在恢复状态正式实现前必须封口。

Result：**CLVS9-M01**。

---

## 14. Cross-Mechanism Consistency

| Cross Item | Verdict | Note |
|---|---|---|
| CLEAVE × CONFUSION | `NOT APPLICABLE` | Confusion modifies primary TargetSelector; Cleave secondary damage does not reopen it |
| CLEAVE × TAUNT | `NOT APPLICABLE` | Taunt only overrides NormalAttack primary target |
| CLEAVE × GUARD | `CONSISTENT` | anchor = post-Guard actualTarget; secondary does not re-run Guard |
| CLEAVE × COMBO — living/normal lifecycle | `CONSISTENT` | each standard NormalAttack can independently Cleave; Cleave creates no Combo checkpoint |
| CLEAVE × COMBO — death/Victory boundary | `CONFLICT` | inherited COMBO death/Victory findings remain open; CLEAVE cannot close them |
| CLEAVE × CHAIN ordering | `CONSISTENT` | Cleave-target Chain INLINE; main-target Chain deferred until Cleave complete |
| CLEAVE × COUNTERATTACK | `CONSISTENT` | main NormalAttack can Counter later; Cleave secondary lacks NormalAttack identity |
| CLEAVE secondary × DAMAGE_SHARE | `CONSISTENT` | explicitly eligible |
| CLEAVE main-base × DAMAGE_SHARE | `CONFLICT` | `MainAttackFinalDamage` pre/post partition layer undefined — CLVS9-B01 |
| CLEAVE secondary × DISTRIBUTION | `CONSISTENT` | inherited DamageEvent eligibility from Distribution P0 |
| CLEAVE main-base × DISTRIBUTION | `CONFLICT` | `MainAttackFinalDamage` pre/post partition layer undefined — CLVS9-B01 |

这里的 `CONFLICT` 包含“两个 P0 组合后无法得到唯一运行时结果”，不表示 Share/Distribution 自身合同错误。

---

## 15. Stage8 Compatibility

Stage8 已冻结主链：

```text
DamageRequest
→ prevention / hit resolution
→ formula
→ modifier
→ finalization
→ DamageResult
→ DamageResolutionSystem
→ TroopSystem
```

CLEAVE 需要的是一个**受限派生伤害入口**：

```text
pre-resolved derived base
→ Evasion / Resistance
→ partition
→ troop settlement
→ selected callbacks
```

同时必须跳过：

```text
base formula
secondary offense
secondary defense
secondary normal damage modifier re-entry
Crit reroll
```

因此不应实现为：

```text
call DamageSystem.calculate()
+ random skip flags
```

更合适的设计分类：

```text
B. Stage9 wrapper/orchestrator
+
C. Stage9-compatible derived-damage extension seam / policy
```

例如工程上可表达：

```text
DerivedDamageRequest
DerivedDamagePolicy
DerivedDamageKind = CLEAVE
permission matrix
```

然后复用 Stage8 已有可组合的 prevention / result / troop mutation ownership，而不改写 Frozen base formula ownership。

结论：

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
```

只有在后续代码设计证明“无法增加外围 seam 而必须修改 Stage8 Frozen ownership / formula topology”时，才升级为 Formal Reopen；当前合同证据不足以支持 D。

---

## 16. Documentation Drift

### CLVS9-D01 — `Barrier` terminology should normalize to `690083 RESISTANCE`

CLEAVE P0/R3 使用 `Barrier`，当前状态正式命名为：

```text
690083 RESISTANCE / 抵御
```

行为语义相同，当前没有第二个独立 Barrier Gate 证据。

Classification：`DOC_DRIFT / TERMINOLOGY NORMALIZATION`。

### CLVS9-D02 — Evidence Matrix contains stale global current-state rows

`STAGE9_EVIDENCE_MATRIX_V2.md` 的 CLEAVE EM-17 已同步 core freeze，但同一矩阵仍把：

```text
Share Core Mechanics = NEXT RESEARCH TARGET
Counter → Counter = PENDING
```

等后续已被更高 P0 更新的条目保留为 current status。

Classification：`DOC_DRIFT`，不改变本轮 Cleave findings。

### CLVS9-D03 — `690084_SPLASH.md` is partially superseded, partially still correct

P6 skeleton 仍把：

```text
Damage Formula
Modifier Compatibility
Evasion / Resistance / Distribution / Damage Share
```

整体列为 Deferred；其中大部分 core pipeline 已被后续 P0 冻结。

但它把：

```text
Multi-source / Reapplication
Precise Event Ordering
```

保留为 Deferred，恰好仍与本轮 full-state 缺口一致。

因此该文件不是“全部错误”，而是：

```text
PARTIALLY SUPERSEDED MINIMUM_USABLE DOC
```

### CLVS9-D04 — state-research root README is stale

状态研究仓根 README 仍写：

```text
当前第一个研究对象 = 690081 COMBO
```

并保留无条件 Target Death hard-termination baseline；这已经落后于后续合同与独立审计。

`STATE_MECHANICS_INDEX.md` 仍把 690084 标成 `MINIMUM_USABLE`，本轮认为**这不构成 Cleave-specific drift**：它准确反映了“core frozen，但 full state contract 尚未完成”的现实。

---

## 17. Findings

### BLOCKER

#### CLVS9-B01 — MainAttackFinalDamage layer is not uniquely defined

```text
Dtotal
vs Dtarget after Share/Distribution
vs actual committed troop loss
vs credited/log damage
```

当前 Cleave P0 无法唯一选择。影响 Share/Distribution 交叉与 overkill，直接改变 Cleave 数值。

Required narrow re-freeze：明确 `MainAttackFinalDamage` 对应的正式 DamageResult/partition/settlement 层，并给出 main-hit overkill 1000-vs-100 的直接裁决。

#### CLVS9-B02 — CORE freeze does not provide a full 690084 state lifecycle / multi-source contract

缺失 P0：

```text
Apply/Reapply/Refresh/Stack/Replace
Duration/Expiration
Source/Holder death
Suppression/Dispel
Container cardinality
multiple source coexist/order
ratio binding semantics
```

R6 P3 不得替代 P0。

#### CLVS9-B03 — secondary target set/count/order is not P0-frozen

Stage9 必须获得唯一、稳定的 secondary target queue；否则较早 secondary 的 Share/Chain/death 会改变后续目标世界状态并导致不同结果。

可以通过后续合同把“目标数量/来源规则”留在 source-skill layer，但必须明确 Cleave runtime 消费的 ordered secondary-target set 及其 live/dead revalidation contract。

#### CLVS9-B04 — pending Cleave execution across death / battle termination is not frozen

至少以下场景缺少唯一规则：

```text
main actualTarget dies from main hit
attacker dies before/during Cleave
secondary dies before later secondaries
commander dies from Cleave
commander dies from Cleave-triggered Chain
battle becomes logically finished with pending Cleave work
```

不得拿 R5 的其他 atomic-loop 结论或 COMBO 当前冲突 death exception 自动类推。

### MAJOR

#### CLVS9-M01 — exact recovery basis after Cleave → Distribution remains outside a frozen recovery contract

Cleave eligibility itself已冻结，但 690094/690095 仍为 MINIMUM_USABLE，并显式 defer Distribution/multi-target recovery basis。

Cleave 模块应输出统一 damage/provenance facts，不得自行决定 participant loss 是否计入倒戈/攻心。

### MINOR

```text
CLVS9-Nxx = 0
```

### DOC_DRIFT

```text
CLVS9-D01 = OPEN — Barrier → RESISTANCE terminology normalization
CLVS9-D02 = OPEN — Evidence Matrix global current-state rows stale
CLVS9-D03 = OPEN — 690084 minimum-usable doc partially superseded by newer core P0
CLVS9-D04 = OPEN — state-research root README research/death baseline stale
```

### HARDENING

#### CLVS9-H01 — use typed DerivedDamage identity / permission policy

Stage9 design should make these explicit engineering fields or equivalent typed concepts：

```text
root_action_id
parent_normal_attack_id
event_family = CLEAVE
source_type = CLEAVE
damage_type = WEAPON | STRATEGY
sourceUnit/sourceSkill/sourceEffect
secondaryTarget
cleaveRatio
derivedBaseValue
permissionPolicy
```

Then obtain naturally：

```text
Counter = BLOCKED
Cleave = BLOCKED
Chain = ALLOWED
Share = ALLOWED
Distribution = ALLOWED
FirstAid = ALLOWED
Guard/Taunt/Combo = NOT APPLICABLE
```

不要以战法名/状态名字符串分支，也不要只靠 `reaction_depth` 防递归。

### Finding counts

```text
BLOCKER   = 4
MAJOR     = 1
MINOR     = 0
DOC_DRIFT = 4
HARDENING = 1
TOTAL     = 10
```

---

## 18. Final Verdict

# REOPEN REQUIRED

这是 **NARROW REOPEN**，不是推翻 CLEAVE 已确认 kernel。

可以保留：

```text
Cleave = derived damage, not NormalAttack
no second base formula
no secondary target modifier re-entry
main-hit Crit/modifier result inherited through the chosen base layer
no Crit reroll
Evasion before Resistance
successful Resistance consumes one charge
Share allowed
Distribution allowed via Distribution P0 inheritance
DAMAGE_SHARE > DISTRIBUTION
FirstAid allowed
Cleave → Chain allowed
Cleave target Chain INLINE
main-target Chain deferred until Cleave complete
Counter blocked by missing NormalAttack identity
Cleave recursion blocked
DamageType inherited
post-Guard actualTarget is Cleave anchor
Confusion/Taunt do not rerun on secondary targets
Stage8 Formal Reopen = NO
```

必须在 Stage9 正式 `690084 STATE CONTRACT READY` 前关闭：

```text
1. MainAttackFinalDamage exact layer
2. overkill base
3. full state lifecycle / multi-source semantics
4. ordered secondary-target contract
5. Cleave block death / commander-death / Victory termination semantics
```

并单独保留外部依赖：

```text
Lifesteal / StrategyRecovery exact Distribution recovery basis
```

前四轮开放 finding disposition：

```text
CFS9-B01 = KEEP OPEN
CBS9-B01 = KEEP OPEN
CBS9-B02 = KEEP OPEN
CBS9-B03 = KEEP OPEN
```

CLEAVE 新证据没有关闭它们。相反，CLEAVE 的 pending-block death / Victory 审计再次证明 Stage9 不能采用一个全局简单 `if dead: stop/continue` 布尔规则。

最终准入：

```text
CLEAVE CORE OPERATOR DESIGN = PARTIALLY READY
690084 FULL STATE CONTRACT READY = NO
CLEAVE P0 NARROW REOPEN REQUIRED = YES
FORMAL STAGE8 REOPEN REQUIRED = NO
NEXT MECHANISM = CHAIN_LINK
```
