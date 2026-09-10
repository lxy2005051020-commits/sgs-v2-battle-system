# Stage 8 Build Prompt · Damage Rule / Hit Resolution / Modifier Pipeline

你现在要继续维护我的项目：

```text
三国志战略版战斗模拟器 V2
```

GitHub 仓库：

```text
lxy2005051020-commits/sgs-v2-battle-system
```

目标：按照已经 `DESIGN FROZEN` 的 Stage 8 合同完成正式施工，并把实现推进到“可进入独立实现审计”的状态。

本次是 **Stage 8 production implementation**，不是重新设计 Stage 8，也不是研究官方状态机制。

---

# 1. 必须先读取当前真实仓库

开始任何修改前，直接读取 GitHub 当前最新 `main`，不要根据旧聊天、旧 Prompt 或记忆猜测仓库状态。

必须先确认：

```text
actual main HEAD
working target branch
PROJECT_STATUS.md
PROJECT_ROADMAP.md
```

然后完整读取 Stage 8 canonical artifacts：

```text
stages/stage8/README.md
stages/stage8/STAGE8.md
stages/stage8/STAGE8_DESIGN_FREEZE.md
stages/stage8/STAGE8_EVIDENCE_MATRIX.md
stages/stage8/STAGE8_BUILD_PROMPT.md
```

如果实际仓库尚未完成上述目录迁移，则先以当前 `main` 上等价 Stage 8 frozen artifacts 为准，不得因此自行重写设计。

还必须读取当前 production 关键文件，至少包括：

```text
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/weapon_damage_formula.py
sgs_v2/battle_core/strategy_damage_formula.py
sgs_v2/battle_core/attribute_system.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/context.py
sgs_v2/battle_core/random_system.py
sgs_v2/battle_core/troop_system.py
sgs_v2/battle_core/events.py

sgs_v2/battle_core/state_definition.py
sgs_v2/battle_core/state_instance.py
sgs_v2/battle_core/state_registry.py
sgs_v2/battle_core/state_runtime_params.py
sgs_v2/battle_core/official_state_catalog.py

sgs_v2/battle_core/effects.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/trigger_system.py
sgs_v2/battle_core/rule_hook_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/normal_attack_system.py
```

同时检查现有 tests，尤其是：

```text
tests/test_stage4_states.py
tests/test_damage_resolution_system.py
tests/test_normal_attack_damage_resolution.py
tests/test_weapon_damage_formula.py
tests/test_strategy_damage_formula.py
tests/test_battle_systems.py
tests/test_stage7_architecture.py
tests/test_stage7_provenance.py
tests/test_state_registry.py
tests/test_state_runtime_params.py
```

施工前先执行当前基线：

```text
python -m pytest -q
python demo.py
```

记录：

```text
main exact HEAD
pytest baseline
demo baseline
```

如果基线已经失败，先判断失败是否与 Stage 8 无关；不得把既有失败偷偷算成自己的 Stage 8 成果，也不得在不理解原因的情况下顺手“修一切”。

---

# 2. 分支要求

不要直接在 `main` 上施工 production code。

推荐施工分支：

```text
stage8-damage-pipeline
```

如果该分支已经存在：

```text
先读取其最新 HEAD 和与 main 的差异
```

不得覆盖未知工作。

如果不存在，则从当前最新 `main` 创建。

所有 Stage 8 production 实现、测试和施工状态更新都进入该分支，最终经独立实现审计后再决定是否合并。

---

# 3. Frozen architecture，不得重新设计

Stage 8 的唯一理论伤害主链已经冻结：

```text
DamageRequest
↓
participant validation
↓
StateDamageRuleProvider / DamageRuleCollection
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
DamageFormulaPolicySystem
↓
Frozen Base Damage Formula
↓
coefficient scaling
↓
DamageModifierSystem
↓
finalization
↓
DamageResult + DamagePipelineTrace
↓
DamageResolutionSystem
↓
TroopSystem.apply_damage
```

必须保持：

```text
DamageSystem.calculate()
= 理论伤害唯一入口

DamageResolutionSystem
= 理论结果 → troop mutation → battle fact 的唯一协调层

TroopSystem
= 唯一兵力写入口

runtime StateRegistry
= context.states

runtime RNG
= context.random

EventBus
= fact bus
≠ damage rule engine
```

禁止建立第二套 Damage path。

禁止任何 Stage 8 resolver 直接扣兵。

禁止任何 Stage 8 calculation layer 直接 publish battle fact。

禁止任何 Stage 8 system 使用 Python `random`。

---

# 4. Evidence Gate 是硬门

施工前读取：

```text
stages/stage8/STAGE8_EVIDENCE_MATRIX.md
```

当前 production mapping 原则必须严格执行：

```text
weakness
→ PASS_STAGE8
→ 允许做既有行为的架构迁移
```

以下官方状态在 Evidence Matrix 仍为 `DEFER` 时：

```text
evasion
barrier
sure_hit
defense_pierce
vigilance
critical
strategy_critical
damage_reduction_pierce
rebellion
```

必须满足：

```text
可以为 generic infrastructure 写 synthetic tests
可以定义通用 typed models
不得建立真实 official production binding
不得把 synthetic semantics 写成官方规则
不得因为官方文本“看起来够明确”就擅自升级 verdict
```

如果施工过程中发现新的官方机制证据：

```text
不要在本次施工里顺手改 Evidence verdict
```

先记录为 audit note，交回机制研究 / Evidence Gate 流程。

---

# 5. 第一施工块：typed Damage Rule 模型

优先建立 Stage 8 typed contracts，再接行为。

建议文件可按 frozen design 拆分，例如：

```text
sgs_v2/battle_core/damage_rule_models.py
sgs_v2/battle_core/damage_rule_provider.py
sgs_v2/battle_core/damage_state_rule_bindings.py
```

具体文件名允许做小幅工程调整，但不得改变职责边界。

至少实现以下概念：

```text
DamageRuleFamily
RuleContributionSource
DamageRuleCollection
StateRuleBinding
StateDamageRuleProvider
```

`DamageRuleFamily` 至少支持：

```text
PREVENTION
HIT
FORMULA_POLICY
MODIFIER
```

`RuleContributionSource` 必须明确区分：

```text
owner_id
applied_by_unit_id
source_skill_id
source_state_id
source_state_instance_id
origin_key
```

不得把 modifier/state provenance 再叫成一个含义模糊的 `source_id`。

从 `StateInstance` 映射时必须保持：

```text
owner_id                 = StateInstance.owner_id
applied_by_unit_id       = StateInstance.source_id
source_skill_id          = StateInstance.source_skill_id
source_state_id          = StateInstance.state_id
source_state_instance_id = StateInstance.instance_id
```

State provenance pair 继续保持 Stage 7 不变量：

```text
source_state_id
source_state_instance_id
```

必须同时存在或同时为空。

---

# 6. StateDamageRuleProvider / Binding

实现：

```text
StateInstance
↓
StateDamageRuleProvider
↓
StateRuleBinding / family adapter
↓
immutable DamageRuleCollection
```

要求：

```text
context.states
= 唯一 StateRegistry runtime truth
```

Provider：

```text
只读 StateRegistry
不消耗 RNG
不修改 StateRegistry
不修改 troops
不发布 Event
```

同一次 `DamageSystem.calculate()` 只形成一次规则快照。

必须确定性排序：

```text
StateInstance
→ stable instance_id/order_key
```

如果存在 `provider_key / order_key`：

```text
必须启动期或注册期检测重复 key
```

不要让重复 key 在生产运行到一半才制造“排序虽然稳定，但不知道谁是谁”的哲学问题。

核心 resolver：

```text
DamagePreventionSystem
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
```

不得识别：

```text
OfficialStateId
具体 official state_id
```

具体状态身份只允许集中在独立 binding / adapter 层。

synthetic state 也必须通过同一 provider/binding contract 进入测试，不允许测试后门。

---

# 7. participant validation

项目已确认：

```text
武将死亡后状态清空
后续不再参与结算
0 troops = dead
```

因此在任何：

```text
rule discovery
prevention
hit
formula
RNG
modifier
Event
```

之前验证：

```text
source 存在且 troops > 0
target 存在且 troops > 0
```

非法参与者：

```text
抛明确 domain-level exception
不返回 prevented=True
不消耗 RNG
不发布 DAMAGE_PREVENTED / DAMAGE_DEALT
不进入基础公式
不修改 troops
```

不要让 `F(N)` 的范围异常替你承担生命周期规则。

---

# 8. DamagePreventionSystem

实现正式：

```text
DamagePreventionSystem
DamagePermissionResult
DamageAllowedResult
DamagePreventedResult
DamagePreventionReason
```

Stage 8 production 至少迁移已有：

```text
weakness
```

但是核心 `DamagePreventionSystem` 不得硬编码 weakness ID。

weakness 必须通过 binding/provider 转换为 typed prevention contribution。

迁移后保持所有旧行为：

```text
source 有 weakness
→ base_damage = 0
→ scaled_damage = 0
→ final_damage = 0
→ prevented = True
→ prevented_by_state_id == "weakness"
→ 不调用基础伤害公式
→ 不消耗基础公式 RNG
→ 不扣兵
```

必须保留 Stage 4 event order：

```text
NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

删除 `DamageSystem` 中旧的 weakness 第二套 hardcode，不能新旧两套同时存在。

---

# 9. HitResolutionSystem

实现通用 typed infrastructure：

```text
HitResolutionSystem
HitResolutionResult
HitAllowedResult
HitPreventedResult
HitPreventionReason
```

必须支持 synthetic 测试：

```text
deterministic barrier-like prevention
probabilistic evasion-like contribution
sure-hit-like bypass contribution
```

但如果 Evidence Matrix 仍为 DEFER：

```text
不得创建 evasion / barrier / sure_hit 官方 production binding
```

Hit trace 应支持：

```text
contributors
decisive_source / decisive contribution（如适用）
```

为未来非线性多实例规则保留 typed 表达，但不要发明其官方 stacking 算法。

Stage 8 engineering order 依 STAGE8.md 执行，并明确这是 deterministic engineering behavior，不得改写成官方客户端顺序。

---

# 10. Probability helper 与 RNG

所有 Stage 8 概率统一走最小 helper / utility，语义必须为：

```text
p == 0
→ False
→ 不调用 context.random

p == 1
→ True
→ 不调用 context.random

0 < p < 1
→ context.random.chance(p)
```

输入 probability 必须：

```text
拒绝 bool
finite
0 <= p <= 1
```

不要修改 `RandomSystem.chance()` 的既有全局行为来实现 Stage 8 短路。

Stage 8 caller/helper 自己短路。

wrong DamageType / wrong scope 时必须先 filter：

```text
不适用
→ 不 roll RNG
```

---

# 11. Formula Policy

实现：

```text
DamageFormulaPolicySystem
DamageDefensePolicy
DamageFormulaContext
```

至少：

```text
DamageDefensePolicy.NORMAL
DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
```

Base formula 的签名只允许做向后兼容 keyword-only 扩展：

```text
calculate(
    context,
    source,
    target,
    *,
    formula_context: DamageFormulaContext | None = None,
)
```

旧调用：

```text
calculate(context, source, target)
```

必须继续有效，并严格等价于：

```text
NORMAL
```

`IGNORE_RELEVANT_TARGET_DEFENSE` 只允许：

```text
WEAPON
→ target defense contribution = 0

STRATEGY
→ target intelligence defensive contribution = 0
```

不得改变：

```text
source attack/intelligence
F(N)
source/target level
兵种克制
士气
random percent
low damage floor
```

严禁：

```text
calculate_ignore_defense()
复制第二套公式
临时 mutate UnitRuntime
临时替换 AttributeSystem provider
ignore_defense: bool
ignore_intelligence: bool
```

当前 `defense_pierce` / `rebellion` 若仍为 DEFER：

```text
只测试 synthetic formula-policy contribution
不建立官方 binding
```

---

# 12. Base Formula Freeze

Weapon / Strategy 基础伤害数学实现属于冻结资产。

Stage 8 施工只允许为公式增加 typed policy 输入点。

必须建立 differential tests：

```text
same battle input
same RNG seed
old three-argument NORMAL behavior
==
new formula_context NORMAL behavior
```

不仅比较最终 damage，还要验证：

```text
RNG consumption position / count 不漂移
```

基础公式内部原有：

```text
random percent
low damage floor
```

顺序不得改变。

---

# 13. coefficient

继续冻结：

```text
base_damage
↓
coefficient
↓
scaled_damage
↓
DamageModifierSystem
```

Stage 8 不重新解释 coefficient。

不得把 modifier 放到 coefficient 前，除非 frozen STAGE8.md 明确如此。

---

# 14. DamageModifierSystem

实现：

```text
DamageModifierSystem
DamageModifierContribution
AppliedDamageModifier
DamageModifierKind
DamageModifierOperation
DamageModifierPhase
DamageModifierResult
```

必须保持三个轴分离：

```text
kind
= 规则语义

operation
= 数学操作

phase
= 执行时点
```

Stage 8 v1 最小 operation：

```text
MULTIPLY_FACTOR
```

但 contribution schema 必须是 typed operation model，不得只保存一个无语义 `multiplier`。

最小 kind 依 frozen STAGE8.md 实现，至少能区分：

```text
CRITICAL_MULTIPLIER
OUTGOING_INCREASE
OUTGOING_REDUCTION
INCOMING_INCREASE
INCOMING_REDUCTION
SINGLE_HIT_ADJUSTMENT
```

最小 phase：

```text
CRITICAL
OUTGOING
INCOMING
SINGLE_HIT
```

不要重新加入没有 Stage 8 consumer 的：

```text
FINAL
```

phase ordering 必须按 frozen engineering order 执行，并保持可测试确定性。

同 phase：

```text
稳定 order_key
StateInstance instance_id
```

不得依赖 dict/set 偶然顺序。

---

# 15. Damage Reduction Pierce infrastructure

generic infrastructure 必须能够识别：

```text
INCOMING_REDUCTION
```

并使 synthetic pierce 只影响 reduction operand / effective reduction。

不得影响：

```text
INCOMING_INCREASE
CRITICAL
formula defense
```

trace 应至少能表达：

```text
original_operand
effective_operand
pierce contributor
affected reduction contributor
```

真实：

```text
damage_reduction_pierce / 看破
```

如果 Evidence Matrix 仍为 DEFER：

```text
不得 production bind
```

不要自行决定：

```text
多 reduction 如何聚合
多 pierce 如何聚合
按 contribution pierce 还是 aggregate pierce
rounding
cap
```

---

# 16. Vigilance infrastructure

保留：

```text
SINGLE_HIT
```

modifier insertion point。

synthetic test 可以验证单次伤害调整。

但 Stage 8 不允许：

```text
consume state
扣次数
remove state
enqueue follow-up effect
```

真实 `vigilance` 在 Evidence Matrix 为 DEFER 时不得 production bind。

状态消费属于未来机制确认 / 后续阶段边界。

---

# 17. Critical infrastructure

Stage 8 可实现 generic critical-like modifier infrastructure，并用 synthetic binding 测试：

```text
WEAPON-only critical-like contribution
STRATEGY-only strategy-critical-like contribution
probability filtering
2.0 multiplier synthetic/known semantic support
```

但真实：

```text
critical
strategy_critical
```

在 Evidence Matrix 仍为 DEFER 时不得 official production bind。

必须测试：

```text
wrong DamageType
→ no RNG

p=0 / p=1
→ no RNG

0<p<1
→ exactly intended RNG roll
```

不要发明多个会心来源如何合并。

---

# 18. Finalization

继续保持：

```text
explicit prevented
→ final_damage = 0

non-prevented valid damage
→ max(1, int(modified_damage))
```

但 Stage 8 numeric contract 要保证：

```text
NaN
inf
invalid negative output
```

不会一路跑到 `int()` 才爆炸。

如果某个 operation 理论上可以产生非法负值：

```text
在 modifier boundary 明确 reject
```

不得靠 `max(1, ...)` 把非法中间态悄悄洗白。

---

# 19. Public numeric validation ownership

这是 DESIGN FREEZE 的规范补充，必须实施。

所有进入 Damage Pipeline 的 public numeric boundary：

```text
在 calculation / RNG / modifier / Event / troop mutation 前完成验证
```

至少检查：

```text
DamageRequest.coefficient
DamageEffect.coefficient
probability runtime params
modifier operand
modifier output
pierce rate / reduction rate 等 Stage8 typed params
```

统一要求：

```text
reject bool
reject NaN
reject +inf / -inf
range explicit
```

`coefficient` 至少：

```text
finite
>= 0
```

不要依赖 Python 隐式转换异常作为 validator。

---

# 20. Pipeline Trace

实现强类型：

```text
DamagePipelineTrace
StageEvaluationStatus
```

`StageEvaluationStatus` 至少：

```text
EXECUTED
NOT_EVALUATED
```

不要再让裸 `None` 独立承担 stage execution state。

每个主要阶段 trace 必须满足：

```text
status == EXECUTED
→ 对应 result 存在

status == NOT_EVALUATED
→ earlier short-circuit 导致该阶段未执行
→ 对应 result 为 None
```

典型：

```text
weakness
prevention = EXECUTED
hit        = NOT_EVALUATED
formula    = NOT_EVALUATED
modifier   = NOT_EVALUATED
```

Hit prevented：

```text
prevention = EXECUTED
hit        = EXECUTED
formula    = NOT_EVALUATED
modifier   = NOT_EVALUATED
```

normal damage：

```text
all relevant stages = EXECUTED
```

`DamageResult` 新字段只能追加到现有字段尾部。

不得破坏 Stage 7 positional compatibility。

legacy 手动构造 `DamageResult` 可以保留兼容默认值，但正式 `DamageSystem.calculate()` Stage 8 路径必须产生符合 frozen contract 的 trace。

---

# 21. DamageSystem constructor compatibility

当前公开构造必须保持兼容。

允许增加 Stage 8 collaborators / rule services，但必须满足：

```text
旧 DamageSystem(AttributeSystem(), ...)
仍可构造
```

如果使用：

```text
rule_services=None
```

其语义必须是：

```text
创建默认完整 Stage8 collaborators
```

绝不能表示：

```text
disable Stage8
legacy bypass
```

`BattleSystems` canonical construction 与 manual DamageSystem construction 在同样 context/request 下必须使用相同 pipeline 语义。

不要 constructor-inject 第二套 battle-local：

```text
RandomSystem
StateRegistry
```

runtime truth 永远来自 context。

---

# 22. Event ownership

以下全部禁止 publish battle fact：

```text
DamageRuleProvider
StateDamageRuleProvider
DamagePreventionSystem
HitResolutionSystem
DamageFormulaPolicySystem
DamageModifierSystem
DamageSystem.calculate()
```

唯一事实发布仍由：

```text
DamageResolutionSystem.apply_result()
```

负责：

```text
DAMAGE_PREVENTED
DAMAGE_DEALT
UNIT_DEFEATED
```

如果 Stage 8 需要增加事实字段：

```text
从 DamagePipelineTrace 序列化 summary
```

不得通过 calculation-time EventBus callback 驱动规则。

必须保持：

```text
NORMAL_ATTACK
→ DAMAGE_PREVENTED
```

和：

```text
NORMAL_ATTACK
→ DAMAGE_DEALT
```

既有顺序。

---

# 23. Stage 8 / Stage 9 红线

本次绝对不实现：

```text
Reaction Queue
AFTER_DAMAGE
first_aid
weapon_lifesteal
strategy_lifesteal
counterattack
cleave
damage_split
damage_share
chain_link
guard
target redirect
taunt
confusion
combo
```

`DamageModifierSystem` 只允许：

```text
calculate
transform
trace
```

不得：

```text
consume state
remove state
restore troops
create secondary DamageRequest
enqueue reaction
publish Event
```

不要把 Stage 9 为了“以后方便”提前做一半。半套 reaction architecture 往往比没有更难处理。

---

# 24. Stage 8 / 后续控制系统红线

本次也不实现：

```text
insight
silence
false_report
provoke
capture
intimidation
equipment disable
skill enable/disable policy
万能 action rule engine
```

Stage 8 provider 只服务 Damage Pipeline，不得长成全游戏万能 RuleProvider。

---

# 25. 推荐新增文件

在不违反 frozen contract 的前提下，优先考虑：

```text
sgs_v2/battle_core/damage_rule_models.py
sgs_v2/battle_core/damage_rule_provider.py
sgs_v2/battle_core/damage_state_rule_bindings.py
sgs_v2/battle_core/damage_prevention_system.py
sgs_v2/battle_core/hit_resolution_system.py
sgs_v2/battle_core/damage_formula_policy_system.py
sgs_v2/battle_core/damage_formula_context.py
sgs_v2/battle_core/damage_modifier_system.py
sgs_v2/battle_core/damage_modifiers.py
sgs_v2/battle_core/stage8_state_params.py
```

允许合理合并“小而只被一个地方使用”的 model 文件，禁止为了追求文件数量照抄清单。

但是不要把不同职责重新塞回一个巨型：

```text
damage_rules.py
```

然后让它同时负责 provider、RNG、formula、modifier、event。

---

# 26. 允许修改的既有文件

预计至少可能涉及：

```text
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/damage_resolution_system.py
sgs_v2/battle_core/weapon_damage_formula.py
sgs_v2/battle_core/strategy_damage_formula.py
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/events.py
sgs_v2/battle_core/__init__.py
```

如果需要修改其他 production 文件：

```text
必须说明原因
必须证明属于 Stage8 frozen scope
```

不得顺手重构 Stage 1～7 与本阶段无关代码。

---

# 27. 必须新增的测试类别

至少新增并完整覆盖：

```text
1. StateRuleBinding / Provider
2. synthetic state 走正式 provider contract
3. weakness architecture migration exact behavior
4. DamagePreventionSystem
5. HitResolution synthetic rules
6. Formula Policy
7. NORMAL exact differential
8. formula RNG consumption equivalence
9. DamageModifier typed operation / phase / ordering
10. synthetic critical-like DamageType + RNG filtering
11. synthetic reduction-pierce isolation
12. finalization
13. DamagePipelineTrace short circuit
14. multi-contributor trace
15. provenance 三方语义
16. manual / canonical DamageSystem equivalence
17. Stage8 calculation systems no Event publish
18. NORMAL_ATTACK event-order regression
19. dead source / dead target / 0 troops
20. bool / NaN / inf / negative numeric domain
21. DEFER official state has no production binding
22. Stage 1～7 full regression
```

---

# 28. Architecture tests

Architecture tests 只保护静态结构红线，例如：

```text
core resolver 不 import / reference OfficialStateId
Stage8 resolver 不 import DamageResolutionSystem
Stage8 resolver 不 import TroopSystem
Stage8 resolver 不 import EffectExecutor
Stage8 calculation layer 不使用 EventBus publish
禁止 Python random import
禁止 direct troops assignment
DEFER official state 不存在 production binding
```

尽量用 AST / import inspection，而不是脆弱字符串匹配。

但是这些运行时语义必须用 behavior tests：

```text
RNG count / order
weakness no formula call
manual/canonical equivalence
event order
formula NORMAL equivalence
provenance
trace short circuit
modifier ordering
```

不要用“源码里没出现某个字符串”来证明数学正确。

---

# 29. Evidence Matrix automated guard

增加一个最小自动检查，至少保证：

```text
verdict ∈ {PASS_STAGE8, DEFER}
```

并通过 code/test contract 保证：

```text
DEFER official state
→ no production binding
```

不要让 Evidence 文档和 production mapping 静悄悄分叉。

---

# 30. Stage folder convention

Stage 8 的阶段资料必须继续统一放在：

```text
stages/stage8/
```

施工期间若新增 Stage 8 文档，例如：

```text
IMPLEMENTATION_NOTES.md
IMPLEMENTATION_AUDIT.md
FINAL_AUDIT.md
```

也放入该目录。

不要再在仓库根目录新增：

```text
STAGE8_xxx.md
```

production code 和 tests 不放进 stage 文件夹，继续按源码职责组织：

```text
sgs_v2/
tests/
```

---

# 31. 施工顺序

推荐严格按以下顺序推进：

```text
A. baseline verification
B. typed rule models
C. StateRuleBinding / Provider / immutable collection
D. participant validation
E. DamagePrevention + weakness migration
F. HitResolution synthetic infrastructure
G. FormulaContext / FormulaPolicy + frozen formula integration
H. coefficient regression
I. Modifier typed model + deterministic phases
J. synthetic critical / reduction / pierce infrastructure
K. DamagePipelineTrace + DamageResult append-only extension
L. DamageSystem orchestration
M. BattleSystems canonical wiring
N. Event payload trace summary（如需要）
O. numeric hardening
P. architecture tests
Q. full Stage8 behavior tests
R. Stage 1～7 regression
S. demo
T. branch CI
```

每完成一个大块就运行相关测试，不要堆到最后才一次性发现三十个失败并开始猜是哪一层的问题。

---

# 32. 完成条件

Stage 8 施工完成、可以进入独立实现审计，必须同时满足：

```text
[ ] Frozen design 未被擅自改变
[ ] DamageSystem 仍为唯一 theoretical damage entry
[ ] DamageResolutionSystem 仍为 troop/event coordinator
[ ] TroopSystem 仍为唯一 troop mutation entry
[ ] context.states 为唯一 runtime StateRegistry
[ ] context.random 为唯一 battle RNG
[ ] EventBus 未成为 rule engine

[ ] StateDamageRuleProvider / Binding 正式存在
[ ] core resolver 不识别 official state IDs
[ ] synthetic state 使用同一正式 provider path
[ ] immutable per-request DamageRuleCollection
[ ] deterministic ordering

[ ] weakness 从 DamageSystem hardcode 迁移到正式 PREVENTION contribution
[ ] weakness Stage4 observables 完全兼容
[ ] weakness prevented 时不进入 base formula / RNG

[ ] HitResolution generic infrastructure 完成
[ ] DEFER hit states 无 official production binding

[ ] DamageFormulaContext / Policy 完成
[ ] NORMAL 与 Stage7 exact-equivalent
[ ] Frozen formula 只增加受控 target defensive input policy
[ ] 无第二套 formula

[ ] coefficient 位置未改变

[ ] DamageModifier typed kind / operation / phase 完成
[ ] deterministic modifier order 完成
[ ] reduction-pierce generic isolation 可验证
[ ] vigilance single-hit insertion point 可验证
[ ] DEFER modifier states 无 official production binding

[ ] DamagePipelineTrace 强类型
[ ] StageEvaluationStatus 明确
[ ] DamageResult 新字段仅尾部追加
[ ] positional compatibility 保持

[ ] public numeric boundary reject bool / NaN / inf / illegal ranges
[ ] dead participants fail-fast before RNG/Event

[ ] Stage8 calculation systems 不 publish Event
[ ] NORMAL_ATTACK event order 保持

[ ] Evidence Matrix guard 存在
[ ] DEFER official states 无 production binding

[ ] Stage 1～7 regression 全绿
[ ] python -m pytest -q success
[ ] python demo.py success
[ ] branch GitHub Actions success（若 workflow 可用）
```

---

# 33. 不得提前宣称 FROZEN

施工完成后只允许把 Stage 8 状态更新为类似：

```text
IMPLEMENTATION COMPLETE / PENDING INDEPENDENT AUDIT
```

不得自行写：

```text
Stage 8 FROZEN
```

因为还需要：

```text
独立实现审计
→ 修复 findings
→ re-audit
→ FINAL_AUDIT
→ merge main
→ main exact-head pytest/demo/CI
→ PROJECT_STATUS final update
```

设计冻结和实现封版不是同一件事。请不要因为测试绿了就给自己颁毕业证。

---

# 34. 如果发现 frozen design 真正不可实现

如果施工中发现以下级别的问题：

```text
需要改变 pipeline topology
需要改变 formula policy 语义
需要改变 provider/binding contract
需要改变 modifier schema 的核心语义
需要引入第二套 runtime RNG/Registry
需要改变 Event ownership
需要侵入 Stage9 才能完成 Stage8
```

不得私自重新设计并继续施工。

必须：

```text
停止该冲突部分的实现
保留已经安全完成的工作
输出 DESIGN REOPEN BLOCKER
明确说明：
- frozen contract
- 实际冲突
- 最小需要重新审计的设计点
```

但对于：

```text
文件命名
helper 拆分
局部 class placement
测试 fixture
纯实现细节
```

自行选择最小、清晰、符合 frozen architecture 的方案，不要把普通工程选择伪装成设计危机。

---

# 35. 最终交付报告

施工完成后必须输出：

```text
# Stage 8 Implementation Report

## 1. Baseline
- starting main SHA
- implementation branch
- starting pytest/demo result

## 2. Implemented Architecture
- new systems
- pipeline order
- provider/binding structure
- formula integration
- modifier model
- trace model

## 3. Frozen Contract Compliance
逐项说明是否符合 STAGE8.md

## 4. Official Production Mapping
明确列出：
PASS_STAGE8 bindings
DEFER states with no binding

## 5. Compatibility
- DamageResult positional compatibility
- DamageSystem constructor compatibility
- Stage1-7 boundaries

## 6. RNG / Event / Troop Boundaries

## 7. Tests Added

## 8. Verification
- pytest exact result
- demo result
- CI result

## 9. Changed Files

## 10. Remaining Risks / Accepted Hardening

## 11. Audit Readiness
READY FOR INDEPENDENT IMPLEMENTATION AUDIT
或
NOT READY
```

必须提供真实 commit SHA。

不得只写“已完成”。

---

# 36. 最终目标

本次施工的目标不是把所有官方状态都塞进 Stage 8。

真正目标是把：

```text
StateInstance
↓
typed contribution discovery
↓
Prevention
↓
Hit Resolution
↓
Formula Policy
↓
Frozen Base Formula
↓
coefficient
↓
typed Modifier
↓
Finalization
↓
DamageResult + Trace
↓
DamageResolution
↓
TroopSystem
```

变成真实、唯一、稳定、确定、可测试的 production pipeline。

如果最后得到的只是：

```text
几个新文件
+
更多 if state_id
+
更多 bool
+
更多 Event callback
```

则本次 Stage 8 施工视为失败，即使 pytest 恰巧是绿色。
