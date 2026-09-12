# Stage 9 嘲讽 / TAUNT 机制研究报告

Status ID: `690106`  
Official Name: `嘲讽`  
English Name: `TAUNT`  
Research Status: `RESEARCH_COMPLETE_PENDING_FINAL_FREEZE_AUDIT`

Research Consolidation Date: `2026-09-13`

本文件为 `sgs-v2-battle-system` Stage 9 嘲讽机制专项研究的收敛报告。其目标不是重复堆砌逐轮问答，而是把已经通过战报检索、连续日志切片与交叉边界验证确认的结论，整理为可直接指导模拟器实现与后续冻结审计的机制合同。

官方接口语义基线：

```text
state_id = taunt
Hint ID = 690106
官方分类 = 控制状态
官方原文 = 控制状态，强迫目标的普通攻击以自身为目标
```

> 当前结论：嘲讽机制探索已完成，不再继续无边界扩题。后续仅需对本文做最终一致性审计，通过后再改为 `FROZEN`。

---

## 1. 核心定义

嘲讽不是通用敌方目标重定向器，也不是对所有攻击行为生效的“仇恨系统”。

其正式语义为：

```text
TAUNT = NormalAttack Primary-Target Override
```

即：

> 当受控者创建一次主动普通攻击实例并进入目标解析阶段时，如果存在一个当前可执行的嘲讽实例，且没有更高优先级的目标选择机制抢占，则本次普通攻击的主目标被强制重定向为嘲讽来源武将。

嘲讽不直接改写主动战法、反击、群攻次级目标等独立目标选择器。

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
TargetResolution: JUST_IN_TIME
DurationClock: TARGET_ACTION_TIMELINE
Suppression: MULTI_SOURCE
ResearchStatus: COMPLETE_PENDING_FREEZE_AUDIT
```

关键不变量：

```text
同一单位同一时刻最多物理持有 1 个 TauntInstance。
TauntInstance 只要物理存在，就占用 TAUNT 槽位。
ACTIVE / SUPPRESSED / source dead 都不释放槽位。
只有 REMOVED 才释放槽位。
```

---

## 3. 状态施加准入管线

新嘲讽施加采用严格短路顺序：

```text
ApplyTauntRequest
→ Control Immunity Pre-Check
→ Same-Type Slot Conflict Check
→ Register TauntInstance
```

### 3.1 第一道：洞察免疫前置检查

若目标当前拥有有效洞察：

```text
[X]执行来自【...】的「洞察」效果
[X]由于「洞察」的效果，「嘲讽」对其无效
```

此时施加流程直接失败，不进入 TAUNT 槽位冲突检查。

因此即使旧嘲讽已经自然到期、槽位为空，只要洞察仍存在，新嘲讽依然会在免疫层直接失败。

### 3.2 第二道：TAUNT 槽位冲突检查

若没有洞察免疫，则检查目标是否已经物理持有 `TauntInstance`。

只要实例存在，无论其当前状态为何：

```text
ACTIVE
SUPPRESSED_BY_INSIGHT
SUPPRESSED_BY_SOURCE_SKILL
source dead but instance retained
```

新嘲讽均拒绝注册，并打印：

```text
[X]身上已存在同等或更强的「嘲讽」效果
```

### 3.3 无强度等级、无刷新、无覆盖

全游戏现有嘲讽均视为同一优先级：

```text
守而必固
江东猛虎
唇枪舌战
挑衅
固若金汤
等现有嘲讽来源
```

不存在“高级嘲讽覆盖低级嘲讽”。

持续时间长短、战法类型、来源属性都不构成更高优先级。

冻结候选规则：

```text
First-Come, First-Served
Strictly Mutually Exclusive
Non-Refreshable
Non-Overwriteable
```

---

## 4. TauntInstance 数据语义

推荐把嘲讽建模为独立状态实例，而不是简单 `isTaunted: bool`。

至少需要表达：

```text
TauntInstance
├─ target
├─ sourceUnit
├─ sourceSkill
├─ duration / expire target-turn boundary
├─ lifecycleState
├─ suppressors
└─ registration / removal identity
```

其中：

```text
lifecycleState ∈ { ACTIVE, SUPPRESSED, REMOVED }
```

来源武将存活性不应折叠进 `lifecycleState`：

```text
ACTIVE + source alive
ACTIVE + source dead
SUPPRESSED + source alive
SUPPRESSED + source dead
```

均为合法组合。

---

## 5. 生命周期与持续时间

### 5.1 持续时间绑定受控者自身行动时间轴

嘲讽持续时间不绑定：

```text
全局 Round 边界
施加者行动时间轴
实际成功普通攻击次数
```

而绑定：

```text
受控者 X 自身的 Action Turn / TurnStart 时间轴
```

所有已研究的 1 / 2 / 4 回合嘲讽均服从同一规则，无战法特例。

### 5.2 震慑不会暂停持续时间

只要轮到 X 的行动机会：

```text
X 行动回合
→ X 开始行动
→ 即使随后因震慑“无法行动”
```

该行动机会仍然消耗嘲讽生命周期。

所以嘲讽持续时间不是“成功执行行为才计时”。

### 5.3 SUPPRESSED 不冻结 Duration

无论嘲讽因洞察还是来源战法失效而暂时失效：

```text
remaining lifetime continues
```

若持续时间在压制期间先到期：

```text
SUPPRESSED
→ REMOVED
→ [X]的「嘲讽」效果已消失
```

不会先打印“继续生效”，也不会等压制解除。

### 5.4 到期结算与 off-by-one 要求

实现时禁止简单理解为：

```python
on_turn_start:
    remaining -= 1
    if remaining <= 0:
        remove()
```

因为已确认的 1 回合案例要求：状态施加后，受控者的下一次行动机会仍完整处于该嘲讽生命周期内；该行动机会即使被震慑跳过，也算生命周期消费，随后在对应后续 `TurnStart` 才自然消失。

更稳妥的实现方式是：

```text
expireAtTargetTurnOrdinal
```

或等价的“已消费目标行动窗口数”模型，而不是裸前置减一。

### 5.5 自然到期立即物理删除

当自然到期日志打印：

```text
[X]的「嘲讽」效果已消失
```

该瞬间即：

```text
StatusContainer.remove(TAUNT)
has_status(TAUNT) = false
TAUNT slot = FREE
```

不需要等待 X 整个行动结束。

同一行动后续时点或同回合稍后，新的嘲讽可以立即重新注册。

---

## 6. 压制模型：Multi-Suppressor State Pattern

嘲讽不是单布尔 `suppressed`，而应采用多来源压制集合：

```text
suppressors: Set<SuppressionReason>
```

当前已实证至少包括：

```text
INSIGHT
SOURCE_SKILL_DISABLED
```

### 6.1 ACTIVE → SUPPRESSED

当压制集合从空集变为非空：

```text
ACTIVE → SUPPRESSED
```

打印：

```text
[X]的「嘲讽」暂时失效
```

### 6.2 SUPPRESSED → ACTIVE

只有最后一个压制源解除、集合重新为空时：

```text
SUPPRESSED → ACTIVE
```

才打印：

```text
[X]的「嘲讽」继续生效
```

解除其中一个压制源，但集合仍非空时，不恢复、不打印恢复日志。

### 6.3 洞察是状态级压制源，同时也是新控制施加免疫源

已有嘲讽后获得洞察：

```text
洞察效果已施加
→ 嘲讽暂时失效
```

洞察恢复生效（例如常驻洞察战法从伪报中恢复）同样会立即压制已有控制状态。

洞察失效时，如果它是最后一个压制源：

```text
嘲讽继续生效
```

但在新嘲讽施加阶段，洞察还同时位于更前置的免疫层：

```text
洞察有效
→ 新嘲讽直接“对其无效”
→ 不进入 TAUNT 槽位检查
```

---

## 7. 来源战法失效与生命周期绑定

### 7.1 持续维持型来源战法

以【守而必固】等准备阶段一次性投递、但状态与来源战法维持关系仍存在的指挥/被动来源为例：

```text
sourceSkill 被伪报失能
→ 已生成 TauntInstance 加入 SOURCE_SKILL_DISABLED suppressor
→ 嘲讽暂时失效
```

来源战法恢复：

```text
remove SOURCE_SKILL_DISABLED
→ 若 suppressors 归零
→ 嘲讽继续生效
```

这属于已有实例的 `Suspend / Resume`，不是重新施加。

### 7.2 即时施加型主动战法

【唇枪舌战】【江东猛虎】【挑衅】等主动战法一旦成功创建并注册 TauntInstance：

```text
旧 TauntInstance 与来源武将之后是否被“计穷”解耦
```

来源武将后来被计穷，只阻止主动战法再次发动，不影响已经挂在目标身上的旧嘲讽。

### 7.3 来源战法不是持续轮询 Aura

【守而必固】等不是：

```text
if target no longer has taunt:
    reapply taunt
```

而是准备阶段一次性创建。

若嘲讽被净化物理删除：

```text
TauntInstance → REMOVED
```

即使来源战法仍有效，也不会自动重新挂回。

---

## 8. REMOVED 是永久终态

以下行为都会真正物理删除 TauntInstance：

```text
自然到期
净化 / 驱散
其他明确 RemoveStatus 行为
```

一旦进入：

```text
REMOVED
```

则：

```text
不可 Resume
不可 Recreate by old sourceSkill
TAUNT slot 立即释放
```

### 8.1 压制期间被净化

若：

```text
Taunt = SUPPRESSED_BY_SOURCE_SKILL
```

此时被净化：

```text
SUPPRESSED → REMOVED
```

之后来源战法恢复时，不再打印：

```text
嘲讽继续生效
```

也不会重新创建状态。

### 8.2 压制期间自然到期

同理：

```text
SUPPRESSED → REMOVED
```

后续洞察/伪报解除都不能让该状态“诈尸”。

---

## 9. 来源武将死亡

### 9.1 来源死亡不删除 TauntInstance

A 对 X 的嘲讽未到期时，如果 A 阵亡：

```text
X.StatusContainer 中 Taunt(A) 仍然存在
Duration 继续流逝
TAUNT 槽位继续被占用
```

不会反向清除状态。

### 9.2 来源死亡只使运行时重定向失效

每次普通攻击 JIT 索敌时：

```text
Taunt exists
→ source.is_alive() ?
→ false
→ 静默跳过 TauntTargetOverride
→ DefaultTargetSelector
```

不会尝试攻击死人，也不会打印：

```text
执行来自【...】的「嘲讽」效果
```

### 9.3 空挂嘲讽仍占槽

即使来源已经死亡：

```text
TauntInstance exists = true
```

因此其他来源尝试给 X 新上嘲讽，仍会得到：

```text
[X]身上已存在同等或更强的「嘲讽」效果
```

只有旧状态自然到期或被净化后才能释放槽位。

### 9.4 来源存活性与状态压制正交

即使嘲讽处于 `SUPPRESSED` 时来源死亡，之后压制解除：

```text
Status Layer 仍可发生 SUPPRESSED → ACTIVE
并打印“嘲讽继续生效”
```

但之后普通攻击运行时：

```text
source.is_alive() == false
→ 嘲讽仍然无法执行
```

因此：

```text
“继续生效” ≠ “下一次一定执行嘲讽”
```

---

## 10. 来源武将自身行动限制不影响已有嘲讽

只要来源 A 仍然存活，以下来源自身状态均不影响 X 身上的已有嘲讽：

```text
震慑
缴械
计穷
虚弱
```

这些只限制 A 自己：

```text
canAct
canNormalAttack
canCastActiveSkill
```

不改变 A 作为被攻击目标的合法性，也不自动禁用其已建立的嘲讽。

已实证样本中，孙坚处于震慑、无法行动时，周瑜仍正常执行来自【江东猛虎】的嘲讽并普通攻击孙坚。

---

## 11. 普通攻击执行管线

嘲讽不在 ActionStart 提前锁定目标，而是在每一个 `NormalAttackInstance` 进入目标解析时进行 JIT 判定。

推荐管线：

```text
NormalAttackInstance
→ Normal Attack Permission Check
→ JIT Target Resolution
    → Confusion selector
    → Taunt selector
    → Default selector
→ Interception / Guard
→ Final Actual Recipient
→ Hit / Damage
→ Downstream event chain
```

### 11.1 缴械前置于嘲讽

若受控者 X 当前被缴械：

```text
普通攻击资格检查失败
→ 无法普通攻击
→ 根本不进入目标选择
→ 不执行嘲讽
→ 不打印嘲讽执行日志
```

因此：

```text
CanNormalAttackCheck BEFORE TauntTargetOverride
```

### 11.2 JIT 状态读取

若 X 行动开始时仍有嘲讽，但主动战法阶段：

```text
获得洞察
净化删除嘲讽
或主动战法先击杀嘲讽来源
```

则随后普通攻击立即读取最新世界状态，嘲讽不再按旧快照执行。

---

## 12. 混乱与嘲讽：抢占，不是压制

混乱与嘲讽可以同时：

```text
Confusion = ACTIVE
Taunt = ACTIVE
```

混乱不是：

```text
Taunt Immunity
Taunt Suppressor
Taunt Conflict
```

它只在普通攻击目标解析阶段具有更高优先级：

```text
ConfusionTargetSelector
    >
TauntTargetSelector
    >
DefaultTargetSelector
```

因此混乱期间：

```text
执行混乱
→ 在混乱允许的全场存活目标池中随机索敌
→ 不继续执行嘲讽分支
```

即使随机结果恰好命中嘲讽来源，也只算混乱随机命中，不打印嘲讽执行日志。

混乱结束后：

```text
Taunt 并不是“继续生效”
```

因为它从未被压制；只是下一次普通攻击不再被 Confusion 分支抢占，于是重新获得 TargetSelector 执行机会。

先混乱、后施加嘲讽也能正常注册。

---

## 13. 连击：每次普通攻击实例独立重判嘲讽

连击的每一刀都是新的 `NormalAttackInstance`，不是复制第一刀结果。

所以：

```text
NormalAttack #1
→ 独立嘲讽 JIT 判定

Combo
→ NormalAttack #2
→ 再次独立嘲讽 JIT 判定
```

战报会严格打印两次嘲讽执行日志（只要两次都满足执行条件）。

### 13.1 第一刀击杀嘲讽来源

若第一刀击杀 A：

```text
第 2 刀重新读取 Taunt(A)
→ A 已死亡
→ 不打印嘲讽
→ 默认索敌其他存活敌军
```

### 13.2 援护者第一刀死亡后的第二刀

若：

```text
Taunt 锁定 A
C 援护 A
第一刀最终打 C
C 死亡
```

第二刀是新普通攻击实例：

```text
重新执行嘲讽
→ A 仍活
→ 再次锁定 A
→ C 已死，援护不再成立
→ 第二刀直接攻击 A
```

这与“突击继承第一刀事件目标”形成严格区分。

---

## 14. 嘲讽作用域边界

### 14.1 主动战法：不受嘲讽影响

受嘲讽武将的主动战法仍按战法原生 TargetSelector 自由选择合法目标。

典型战报：

```text
臧霸受孙坚嘲讽
【避实击虚】→ 主公
【落凤】→ 周瑜
随后：
执行【守而必固】的「嘲讽」效果
→ 普攻孙坚
```

正式结论：

```text
ActiveSkill TargetSelector does not read Taunt
```

### 14.2 反击：不受嘲讽影响

反击目标固定为触发反击的直接攻击者：

```text
CounterAttack.target = triggeringAttacker
```

即使反击者处于嘲讽，也不会重定向，不打印嘲讽执行日志。

### 14.3 群攻次级目标：不受嘲讽影响

嘲讽只锁定普通攻击主目标。

之后群攻：

```text
GroupAttackTargetSelector
→ 按群攻自身规则选择主目标以外的敌军
```

不会把群攻次级伤害重新拉回嘲讽来源，也不会阻止群攻。

### 14.4 单体突击：间接继承最终事件目标

单体突击不是被嘲讽直接改目标。

其 `EventTargetSelector` 消费的是普通攻击经过全部重定向/援护后的最终事件目标。

因此：

```text
Taunt → 先决定 IntendedTarget
Guard → 再决定 FinalAttackTarget
Assault → 继承 FinalAttackTarget
```

---

## 15. 援护与嘲讽

援护发生在嘲讽主目标选择之后。

若：

```text
A = 嘲讽来源
C = 援护 A
X = 受嘲讽攻击者
```

则：

```text
TauntTargetSelector
→ IntendedTarget = A

Guard / Interception
→ FinalAttackTarget = C

Damage
→ C 承受普通攻击
→ A 不承受该次伤害
```

因此至少需要区分：

```text
IntendedTarget
FinalAttackTarget / ActualRecipient
EventTarget
```

禁止用一个 `target` 字段把三层语义全部覆盖掉。

---

## 16. 援护后的单体突击

当普通攻击因援护从 A 转移给 C：

```text
EventTarget = C
```

随后【当锋摧决】【暴戾无仁】【弯弓饮羽】【折冲御侮】等单体突击的敌方单体效果全部作用于 C：

```text
damage → C
伪报 → C
混乱 → C
计穷 → C
属性降低 → C
```

独立目标选择器的己方效果（例如某战法给己方主将的效果）仍按自己的 Selector 运行。

### 16.1 Final EventTarget 在普攻中死亡

若 C 被普通攻击阶段击杀，随后突击概率发动成功：

```text
EventTargetSelector 仍绑定 C
→ C 已死亡
→ 突击空发
→ 不回退 A
→ 不重新随机索敌
```

战报可出现：

```text
发动战法【...】
【突击战法】的有效范围内没有目标
[C]已经死亡，无法获得「...」效果
```

因此：

```text
EventTargetSelector = event-context reference
not dynamic fallback selector
```

---

## 17. 状态日志语义

必须严格区分以下日志：

### 17.1 `效果已施加`

```text
TauntInstance successfully registered
```

### 17.2 `暂时失效`

```text
ACTIVE → SUPPRESSED
```

状态仍存在、仍占槽、Duration 继续流逝。

### 17.3 `继续生效`

```text
SUPPRESSED → ACTIVE
```

只表示最后一个状态级压制源解除。

不等价于：

```text
source still alive
next normal attack will definitely execute taunt
```

### 17.4 `执行来自【...】的「嘲讽」效果`

这是动作执行期日志，仅在本次 `NormalAttackInstance` 的 TauntTargetOverride 真正参与目标解析时产生。

以下场景虽然 TauntInstance 仍可存在，但不会打印该日志：

```text
受控者被缴械，未进入普攻索敌
来源死亡，JIT alive check 失败
Taunt 处于 SUPPRESSED
混乱分支更高优先级抢占
```

### 17.5 `效果已消失`

表示真正：

```text
StatusInstance → REMOVED
StatusContainer unregister
slot release
```

不是“暂时失效”的同义词。

---

## 18. 状态机

```text
                          add first suppressor
        ┌────────────────────────────────────────┐
        │                                        ▼
     ACTIVE  ◄────────────────────────────  SUPPRESSED
        │           remove last suppressor       │
        │                                        │
        │ expire / cleanse                       │ expire / cleanse
        ▼                                        ▼
                      REMOVED
                        │
                        └─ terminal / no resume / no recreate
```

来源死亡不在该生命周期状态机中切换 `ACTIVE/SUPPRESSED/REMOVED`，它属于动作执行期的独立 source-validity 维度。

混乱也不进入该状态机，它属于 TargetSelector 优先级维度。

---

## 19. 推荐实现合同

### 19.1 Apply Pipeline

```python

def apply_taunt(target, source, source_skill, duration):
    # 1. control immunity short-circuit
    if target.has_effective_insight():
        log_insight_execute(target)
        log_status_immune(target, "嘲讽")
        return APPLY_FAILED_IMMUNE

    # 2. unique-slot conflict
    if target.status_container.has_instance("TAUNT"):
        log_equal_or_stronger_conflict(target, "嘲讽")
        return APPLY_FAILED_CONFLICT

    # 3. register once
    status = TauntStatus(
        target=target,
        source=source,
        source_skill=source_skill,
        duration=duration,
    )
    target.status_container.add(status)
    log_status_applied(target, "嘲讽")
    return APPLY_SUCCESS
```

### 19.2 Multi-Suppressor

```python

def add_suppressor(status, reason):
    was_clear = not status.suppressors
    status.suppressors.add(reason)
    if was_clear and status.suppressors:
        status.state = SUPPRESSED
        log_temporarily_invalid(status)


def remove_suppressor(status, reason):
    was_suppressed = bool(status.suppressors)
    status.suppressors.discard(reason)
    if was_suppressed and not status.suppressors:
        status.state = ACTIVE
        log_resume(status)
```

### 19.3 Normal Attack Target Resolution

```python

def select_normal_attack_primary_target(attacker):
    # Permission checks occur before this function.

    confusion = attacker.status_container.get_operational("CONFUSION")
    if confusion is not None:
        log_confusion_execute(attacker, confusion)
        return confusion_selector(attacker)

    taunt = attacker.status_container.get("TAUNT")
    if taunt is not None:
        if taunt.state == ACTIVE and taunt.source.is_alive():
            log_taunt_execute(attacker, taunt)
            return taunt.source

    return default_enemy_selector(attacker)
```

在现行三战规则中，没有独立于死亡之外的“存活但不可被普通攻击选中”状态，因此：

```text
source.isValidNormalAttackTargetFor(attacker)
≡
source.is_alive()
```

工程上可以保留更语义化的接口，但现阶段不应凭空实现不存在的隐身/不可选中机制。

---

## 20. 禁止实现模式

以下实现均与实证冲突：

```text
1. 用单一 bool isTaunted 表达全部生命周期
2. 来源死亡时直接 remove 所有由其生成的嘲讽
3. Taunt.source dead 后允许新 Taunt 覆盖旧槽位
4. 洞察只做普通攻击阶段 runtime filter、却不压制已有控制状态
5. 用单一 suppressed bool，无法表达多压制源
6. 混乱通过把 Taunt 标为 SUPPRESSED 来实现
7. ActionStart 预先缓存本回合普通攻击目标
8. 连击第 2 刀复用第 1 刀已经解析出的目标
9. 援护后覆盖掉 IntendedTarget 历史语义
10. EventTarget 死亡后突击重新随机索敌或回退原目标
11. 净化后的指挥嘲讽自动被来源战法重新补挂
12. 简单 TurnStart 前置 duration-- 导致 1 回合嘲讽提前消失
13. 给现有 Taunt 人为设计未被战报支持的高低强度覆盖层级
```

---

## 21. 关键直接战报样本索引

以下为本轮讨论中反复用于裁决边界的关键样本。完整数据库不随仓库存储，文件名用于本地战报库复核。

### 21.1 洞察压制已有嘲讽

```text
完整战报JSON/战报_1506191_pid1503846.json
曹洪：
发动【鲁莽】
→ 洞察效果已施加
→ 嘲讽暂时失效
→ 普攻自由索敌夏侯渊
```

```text
完整战报JSON/战报_5128982_pid5765937.json
程秉：
发动【壮胆】
→ 洞察效果已施加
→ 嘲讽暂时失效
→ 普攻自由索敌袁绍
```

```text
完整战报JSON/战报_1506192_pid1503848.json
友军给潘璋施加洞察
→ 潘璋已有嘲讽立即暂时失效
→ 后续嘲讽在 SUPPRESSED 期间自然到期并直接“效果已消失”
```

### 21.2 洞察恢复 / 失效与控制状态对称切换

```text
反击战法战报/战报_1523679_pid1521633.json
赵云：
伪报结束 → 洞察继续生效 → 嘲讽暂时失效
再次伪报 → 洞察暂时失效 → 嘲讽继续生效
```

### 21.3 来源战法伪报级联

```text
战报_1516049_pid1513812.json
夏侯惇【守而必固】→ 周瑜嘲讽
夏侯惇受到【当锋摧决】伪报
→ 周瑜嘲讽暂时失效
伪报结束
→ 周瑜嘲讽继续生效
```

### 21.4 嘲讽不影响主动战法

```text
战报_1068312_pid1063329.json
臧霸受孙坚嘲讽：
【避实击虚】→ 主公
【落凤】→ 周瑜
随后普攻阶段执行嘲讽 → 孙坚
```

```text
战报_1068309_pid1063326.json
韩当受孙坚嘲讽：
【短兵相见】→ 周瑜
随后普攻阶段执行嘲讽 → 孙坚
```

### 21.5 来源自身震慑不影响已有嘲讽

```text
完整战报JSON/战报_1111713_pid1106985.json
孙坚因震慑无法行动
随后周瑜仍执行来自【江东猛虎】的嘲讽
→ 普攻孙坚
```

### 21.6 援护死亡 + 连击新普攻实例

```text
战报_5209589_pid5852099.json
第一次普攻 IntendedTarget = 纪灵
→ 关平援护成为实际承受者
→ 关平死亡
→ 连击第 2 刀重新创建普通攻击实例
→ 直接攻击仍存活的原目标纪灵
```

该样本与“连击每刀独立重判嘲讽”的独立证据共同构成新 NormalAttackInstance 模型。

---

## 22. 最小测试矩阵

正式实现前至少需要覆盖以下自动化测试。

| Case | 前置条件 | 预期 |
|---|---|---|
| T01 | 单一有效嘲讽 | 普攻强制来源 |
| T02 | 旧嘲讽存在，再施加新嘲讽 | 新嘲讽拒绝，不刷新 |
| T03 | 来源死亡，旧嘲讽未到期 | 普攻默认索敌；旧实例仍占槽 |
| T04 | 来源死亡后新嘲讽尝试 | 冲突拒绝 |
| T05 | 已有嘲讽后获得洞察 | `暂时失效` |
| T06 | 洞察结束且嘲讽未到期 | 最后压制源解除后 `继续生效` |
| T07 | 洞察期间新嘲讽 | 免疫层直接“对其无效” |
| T08 | 来源战法被伪报 | 已有衍生嘲讽 `暂时失效` |
| T09 | 双重压制 | 解除一个不恢复；最后一个解除才恢复 |
| T10 | SUPPRESSED 期间自然到期 | 直接 REMOVED，不 resume |
| T11 | SUPPRESSED 期间净化 | 直接 REMOVED，来源恢复不诈尸 |
| T12 | 混乱 + 嘲讽 | 混乱索敌优先；Taunt 仍 ACTIVE |
| T13 | 先混乱后嘲讽 | Taunt 正常注册 |
| T14 | 缴械 + 嘲讽 | 普攻资格失败，不执行嘲讽 |
| T15 | 连击 + 嘲讽 | 每刀独立执行嘲讽 JIT |
| T16 | 第一刀击杀嘲讽来源 | 第二刀默认索敌，不执行嘲讽 |
| T17 | 主动阶段获得洞察/净化 | 随后同次行动普攻自由索敌 |
| T18 | 主动阶段击杀嘲讽来源 | 随后普攻自由索敌 |
| T19 | 反击者处于嘲讽 | 反击仍打触发者，不执行嘲讽 |
| T20 | 群攻者处于嘲讽 | 主目标被锁；次级目标正常 |
| T21 | 嘲讽目标被援护 | 援护者成为 FinalAttackTarget |
| T22 | 援护后单体突击 | 突击继承援护者 |
| T23 | 援护者被普攻击杀后突击 | 突击空发，不重索敌 |
| T24 | 来源震慑/缴械/计穷 | 只要来源存活，已有嘲讽正常 |
| T25 | 即时主动嘲讽来源后续被计穷 | 已有 Taunt 不受影响 |
| T26 | 1/2/4 回合持续时间 | 均按 Target Turn 时间轴结算 |

---

## 23. 研究边界

以下问题不再归入“嘲讽本体研究”，应在对应机制专题独立研究：

```text
连击第一刀途中获得缴械后第二刀资格
通用普通攻击 Permission Pipeline 的全部细节
突击概率与发动顺序全集
援护自身多来源冲突
混乱自身的完整目标池规则
所有控制状态的通用 duration 实现
```

本报告只引用这些机制与嘲讽直接发生交互的已确认边界，不继续扩展其本体。

---

## 24. 最终研究结论

嘲讽可以收敛为以下工程公式：

```text
ApplyTaunt succeeds iff:
    no effective control immunity (Insight)
    AND no physical TauntInstance already occupies the slot

Taunt participates in a NormalAttackInstance iff:
    TauntInstance exists
    AND lifecycleState == ACTIVE
    AND sourceUnit.is_alive()
    AND NormalAttack permission checks already passed
    AND no higher-priority Confusion selector preempts target resolution

If participating:
    IntendedTarget = sourceUnit

Then:
    Guard / Interception may change FinalAttackTarget
    downstream EventTarget-based single-target Assault inherits FinalAttackTarget
```

生命周期公式：

```text
ACTIVE ↔ SUPPRESSED
    reversible while instance exists

ACTIVE / SUPPRESSED → REMOVED
    expiration or cleanse
    irreversible terminal state

source death
    does not remove instance
    only makes JIT Taunt execution fail

Confusion
    does not suppress instance
    only shadows Taunt in TargetSelector priority
```

当前研究已完成 40 项阶段性机制确认并完成收敛。

下一步仅进行：

```text
FINAL CONSISTENCY AUDIT
→ resolve any wording / implementation-contract inconsistency
→ mark FROZEN
→ optionally extract concise Stage 9 implementation contract
```
