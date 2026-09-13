# Stage 9 嘲讽 / TAUNT 核心机制冻结记录

Status ID: `690106`  
Official Name: `嘲讽`  
English Name: `TAUNT`  
Status: `FROZEN`  
Freeze Date: `2026-09-13`

本文件为 `sgs-v2-battle-system` 中 `690106 TAUNT / 嘲讽` 的正式实现合同。

冻结依据：

```text
STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md
→ 40 项阶段性机制结论收敛

STAGE9_TAUNT_FINAL_CONSISTENCY_AUDIT.md
→ PASS
→ 0 blocking mechanism contradictions
→ 0 state-machine blockers
→ 0 target-pipeline blockers
→ 0 duration/off-by-one blockers
→ 0 cross-contract blockers
```

若历史 `R2 / R6 / Stage 9` 旧表述与本文冲突，以本文为 TAUNT 专项最高优先级实现依据。

---

## 1. Official Semantic Baseline

```text
state_id = taunt
Hint ID = 690106
官方分类 = 控制状态
官方原文 = 控制状态，强迫目标的普通攻击以自身为目标
```

冻结工程定义：

```text
TAUNT = NormalAttack Primary-Target Override
```

嘲讽不是通用目标重定向，不影响主动战法原生选敌，不改写反击目标，也不改写群攻次级目标。

---

## 2. Classification

```yaml
Category: CONTROL_STATE
Family: TARGET_REDIRECT_CONTROL
PrimaryScope: NORMAL_ATTACK_PRIMARY_TARGET
Container: UNIQUE_SLOT
Stacking: MUTUALLY_EXCLUSIVE
Refresh: DISALLOWED
Overwrite: DISALLOWED
StrengthHierarchy: NONE_FOR_CURRENT_TAUNT_RULESET
TargetResolution: JUST_IN_TIME
DurationClock: TARGET_ACTION_TIMELINE
Suppression: MULTI_SOURCE
Status: FROZEN
```

关键不变量：

```text
同一 holder 同时最多物理存在 1 个 TauntInstance。
只要实例物理存在，就占用 TAUNT 槽位。
ACTIVE / SUPPRESSED / source dead 均不释放槽位。
只有 REMOVED 才释放槽位。
```

---

## 3. Apply Pipeline — FROZEN

新嘲讽施加严格按以下顺序：

```text
ApplyTauntRequest
→ Control Immunity Pre-Check
→ Same-Type TAUNT Slot Conflict Check
→ Register TauntInstance
```

### 3.1 Insight immunity first

目标存在有效洞察时：

```text
[X]执行来自【...】的「洞察」效果
[X]由于「洞察」的效果，「嘲讽」对其无效
```

流程立即失败，不进入 TAUNT 槽位冲突。

### 3.2 Unique-slot conflict

若没有洞察免疫，但目标已经物理持有 `TauntInstance`：

```text
[X]身上已存在同等或更强的「嘲讽」效果
```

新嘲讽拒绝。

冲突检查只看旧实例是否存在，不看：

```text
旧实例 ACTIVE / SUPPRESSED
旧来源是否死亡
剩余持续时间长短
来源战法类型
来源武将属性
```

### 3.3 No strength replacement

当前现有嘲讽统一冻结为：

```text
First-Come, First-Served
Strictly Mutually Exclusive
Non-Refreshable
Non-Overwriteable
```

“同等或更强”属于通用冲突文案，不应据此为 TAUNT 实现未被证据支持的强度层级。

---

## 4. TauntInstance Lifecycle — FROZEN

规范状态机：

```text
ACTIVE ↔ SUPPRESSED
  │           │
  └─────┬─────┘
        │ expire / cleanse
        ▼
     REMOVED
     terminal
```

推荐最小状态语义：

```text
TauntInstance
├─ target
├─ sourceUnit
├─ sourceSkill
├─ expireAtTargetTurnOrdinal / equivalent duration clock
├─ lifecycleState: ACTIVE | SUPPRESSED | REMOVED
└─ suppressors: Set<SuppressionReason>
```

`sourceUnit.is_alive()` 不属于 lifecycleState，必须作为独立运行时维度。

---

## 5. Duration — FROZEN

所有已核验 1 / 2 / 4 回合嘲讽统一使用：

```text
TARGET ACTION TIMELINE
```

即持续时间绑定受控者自身行动机会 / TurnStart 时间轴，而不是：

```text
全局 Round
来源武将行动次数
成功普通攻击次数
```

冻结规则：

```text
受控者被震慑无法行动
→ 该行动机会仍推进 Taunt 生命周期

Taunt 处于 SUPPRESSED
→ duration 仍继续推进

SUPPRESSED 期间先到期
→ 直接 REMOVED
→ 打印「嘲讽」效果已消失
→ 不先 Resume
```

实现禁止裸前置：

```python
remaining -= 1
if remaining <= 0:
    remove()
```

因为会制造 1 回合状态 off-by-one。应使用目标行动序号到期边界或等价的“已消费行动窗口”模型。

---

## 6. Multi-Suppressor — FROZEN

至少已确认两类压制源：

```text
INSIGHT
SOURCE_SKILL_DISABLED
```

冻结状态转换：

```text
suppressors: empty → non-empty
→ ACTIVE → SUPPRESSED
→ 打印「嘲讽」暂时失效

remove one suppressor but others remain
→ stay SUPPRESSED
→ no resume log

remove last suppressor
→ SUPPRESSED → ACTIVE
→ 打印「嘲讽」继续生效
```

### Insight has dual role

洞察同时承担：

```text
A. existing-control state suppressor
B. new-control application immunity pre-check
```

二者不得合并成一个普通攻击阶段 runtime filter。

---

## 7. Source Skill Dependency — FROZEN

### 7.1 Sustained source-skill relationship

对于已实证具有来源战法生命周期绑定的嘲讽：

```text
sourceSkill 被伪报失能
→ existing Taunt 加入 SOURCE_SKILL_DISABLED
→ 「嘲讽」暂时失效

sourceSkill 恢复
→ remove SOURCE_SKILL_DISABLED
→ 若无其他 suppressor，则「嘲讽」继续生效
```

这是已有实例的 Suspend / Resume，不是重新施加。

### 7.2 Instant active-skill Taunt

主动战法成功创建旧 TauntInstance 后：

```text
source 后续被计穷
→ 只影响 source 后续主动战法发动资格
→ 不影响已经注册的旧 TauntInstance
```

### 7.3 No aura recreation

旧 Taunt 被净化 / 到期进入 `REMOVED` 后：

```text
sourceSkill 后续恢复或继续存在
→ 不得自动重新创建旧 Taunt
```

`REMOVED` 为终态。

---

## 8. Source Death — FROZEN

来源死亡不删除 TauntInstance：

```text
source dead
→ TauntInstance remains
→ duration continues
→ TAUNT slot remains occupied
```

但每次普通攻击 JIT 目标解析时：

```text
Taunt exists
AND Taunt ACTIVE
AND source.is_alive() == false
→ TauntTargetOverride silent-fail
→ no「执行嘲讽」log
→ fallback to default selector if no higher branch
```

来源死亡后的空挂 Taunt 仍会阻止新 Taunt 注册。

状态层 Resume 与来源存活正交：即使 source dead，最后一个 suppressor 解除仍可能产生 `SUPPRESSED → ACTIVE / 继续生效`；但下一次普通攻击仍因 source dead 无法执行 Taunt override。

---

## 9. Source Self-Restriction — FROZEN

只要来源仍存活，来源自身以下限制不影响已有 Taunt：

```text
震慑
缴械
计穷
虚弱
```

因此 Taunt 执行不得依赖：

```text
source.canAct()
source.canNormalAttack()
source.canCastActiveSkill()
```

现行规则中不存在独立于死亡之外的“存活但不可被普通攻击选中”机制，因此 TAUNT 来源运行时合法性可实现为：

```text
source.isValidNormalAttackTargetFor(attacker)
≡ source.is_alive()
```

可保留语义接口，但不得凭空增加隐身 / untargetable 状态。

---

## 10. Normal Attack Target Pipeline — FROZEN

冻结顺序：

```text
NormalAttackInstance
→ NormalAttack Permission Check
→ JIT Target Resolution
    → ConfusionTargetSelector
    → TauntTargetSelector
    → DefaultTargetSelector
→ Guard / Interception
→ FinalActualAttackTarget
→ Hit / Damage
→ downstream attack chain
```

### 10.1 Disarm before Taunt

受控者被缴械：

```text
NormalAttack permission fails
→ no target resolution
→ no Taunt execution
→ no Taunt execute log
```

### 10.2 JIT, never ActionStart snapshot

Taunt 目标不得在行动开始时锁死。

若行动过程中、普通攻击之前：

```text
Taunt 被洞察压制
source 被主动战法击杀
Taunt 被实际 RemoveStatus 删除
```

则后续普通攻击读取最新状态；不得继续使用旧目标快照。

其中“中途洞察压制”和“中途 source death”有直接行为证据；“中途实际删除后不再读取旧 Taunt”属于已冻结 JIT + REMOVED 终态的组合结论。

---

## 11. Confusion × Taunt — FROZEN

冻结优先级：

```text
ConfusionTargetSelector
>
TauntTargetSelector
>
DefaultTargetSelector
```

混乱对嘲讽是：

```text
runtime target-selector preemption / shadowing
```

不是：

```text
Taunt immunity
Taunt suppressor
Taunt slot conflict
```

两者可同时 `ACTIVE`。混乱期间不产生因混乱本身导致的：

```text
「嘲讽」暂时失效
「嘲讽」继续生效
```

混乱结束后，如果 Taunt 仍存在且 ACTIVE，只是下一次普通攻击重新进入 Taunt selector 分支。

先混乱后施加 Taunt 也可正常注册，前提是没有洞察免疫和 TAUNT 槽位冲突。

---

## 12. Combo Boundary — FROZEN FOR TAUNT

每次连击产生新的 `NormalAttackInstance`：

```text
NormalAttack #1 → independent JIT Taunt check
Combo dispatch
NormalAttack #2 → independent JIT Taunt check
```

不得复用第一刀已解析目标。

若第一刀击杀 Taunt source：

```text
第二刀重新检查 source.is_alive()
→ false
→ no Taunt execute log
→ default targeting
```

若第一刀因 Guard 转给 C 且 C 死亡，但 Taunt source A 仍活：

```text
第二刀重新 Taunt → A
→ C 已死，Guard 不再成立
→ 第二刀可直接攻击 A
```

本节仅冻结 TAUNT 与新 NormalAttackInstance 的交互，不替代后续 Combo 专项研究。

---

## 13. Scope Boundaries — FROZEN

### Active Skill

```text
ActiveSkill TargetSelector does not read Taunt
```

### Counterattack

```text
Counter target = triggering attacker
Taunt does not redirect Counter
```

### Cleave secondary targets

```text
Taunt only controls NormalAttack primary target
Cleave secondary target selection follows Cleave rules
```

### Single-target Assault

Taunt 不直接控制 Assault。Assault 消费当前普通攻击链的最终事件目标：

```text
Taunt selects IntendedTarget A
→ Guard may redirect to C
→ FinalAttackTarget / EventTarget = C
→ single-target Assault follows C
```

若 C 在普通攻击阶段死亡：

```text
Assault remains bound to dead C
→ empty resolution / invalid target
→ no fallback to A
→ no random retarget
```

---

## 14. Guard × Taunt — FROZEN

冻结三级目标语义：

```text
IntendedTarget
→ Taunt may set to source A

FinalAttackTarget / ActualRecipient
→ Guard may redirect to protector C

DamageRecipient(s)
→ later Share / Distribution may further split troop loss
```

TAUNT 只负责第一层普通攻击主目标意图；Guard 位于其后。

禁止使用单一 `target` 字段覆盖全部目标身份。

---

## 15. Log Semantics — FROZEN

```text
「嘲讽」效果已施加
= TauntInstance registered

「嘲讽」暂时失效
= ACTIVE → SUPPRESSED

「嘲讽」继续生效
= SUPPRESSED → ACTIVE after last suppressor removal

执行来自【...】的「嘲讽」效果
= this NormalAttackInstance actually used TauntTargetOverride

「嘲讽」效果已消失
= physical removal / REMOVED / slot release
```

以下情况下实例可仍存在，但不得打印 Taunt execution log：

```text
attacker disarmed before target phase
Taunt SUPPRESSED
Confusion branch preempts Taunt
source dead at JIT check
```

---

## 16. Minimal Implementation Contract

```python
def apply_taunt(target, source, source_skill, duration):
    if target.has_effective_insight():
        return APPLY_FAILED_IMMUNE

    if target.status_container.has_instance("TAUNT"):
        return APPLY_FAILED_CONFLICT

    return target.status_container.add(
        TauntStatus(
            target=target,
            source=source,
            source_skill=source_skill,
            duration=duration,
        )
    )
```

```python
def select_normal_attack_primary_target(attacker):
    confusion = attacker.status_container.get_operational("CONFUSION")
    if confusion is not None:
        return confusion_selector(attacker)

    taunt = attacker.status_container.get("TAUNT")
    if taunt is not None:
        if taunt.state == ACTIVE and taunt.source.is_alive():
            return taunt.source

    return default_enemy_selector(attacker)
```

状态压制：

```text
first suppressor added
→ ACTIVE → SUPPRESSED

last suppressor removed
→ SUPPRESSED → ACTIVE

expire / cleanse from ACTIVE or SUPPRESSED
→ REMOVED terminal
```

---

## 17. Forbidden Implementations

以下实现违反冻结合同：

```text
1. 用单 bool isTaunted 替代实例生命周期
2. source death 时 remove Taunt
3. source dead 空挂时允许新 Taunt 覆盖
4. Insight 仅在普攻阶段做 runtime filter
5. 用单 suppressed bool 丢失多压制源
6. Confusion 把 Taunt lifecycle 改成 SUPPRESSED
7. ActionStart 缓存本回合 Taunt target
8. Combo 第二刀复用第一刀 target
9. Guard 后抹掉 IntendedTarget provenance
10. dead EventTarget 的 Assault 动态重索敌
11. cleansed/expired Taunt 被旧 sourceSkill 自动补挂
12. 裸 TurnStart 前置 duration-- 造成 1 回合 off-by-one
13. 为 TAUNT 增加无证据的强度覆盖层
```

---

## 18. Required Test Matrix

最低实现验收必须覆盖原研究报告 T01-T26，至少包括：

```text
single Taunt redirect
same-type conflict / no refresh
dead-source stale slot
Insight application immunity
Insight suppression / resume
multi-suppressor last-release semantics
suppressed expiry / cleanse terminal removal
Confusion selector preemption without suppression
Disarm permission gate before Taunt
Combo per-hit JIT re-evaluation
source death between hits
action-phase Insight/source-death JIT boundary
ActiveSkill unaffected
Counter unaffected
Cleave secondary targets unaffected
Guard after Taunt
Assault inherits post-Guard target
dead Assault EventTarget no retarget
source stun/disarm/silence does not disable old Taunt
instant active-skill Taunt survives later source silence
1/2/4-turn unified target-action duration model
```

---

## 19. Freeze Boundary

以下不属于本冻结记录继续扩展的问题：

```text
CONFUSION 自身完整目标池与生命周期
COMBO 自身完整 transition matrix / permission semantics
通用控制状态 duration 框架
所有控制状态的统一覆盖等级
GUARD 自身多来源规则
ASSAULT 全套发动与概率时序
```

TAUNT 后续只有在出现：

```text
新官方规则
新直接反例
客户端规则版本变化
冻结实现与真实战报发生可复现偏差
```

时才允许重新开启。

---

## 20. Final Freeze Declaration

```text
690106 TAUNT / 嘲讽
RESEARCH: COMPLETE
FINAL CONSISTENCY AUDIT: PASS
CORE MECHANICS: FROZEN
IMPLEMENTATION CONTRACT: FROZEN
NEXT REQUIRED STATE RESEARCH: 690103 CONFUSION
```

自 `2026-09-13` 起，本文作为 Stage 9 TAUNT 正式冻结基线。
