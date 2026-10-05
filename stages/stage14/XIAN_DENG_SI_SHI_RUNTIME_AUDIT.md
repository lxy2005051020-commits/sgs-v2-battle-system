# 先登死士 Runtime Independent Audit

> Date: 2026-10-06  
> Audit target before audit-doc commits: `038b717725bf45fdc2a2f4e14ef97f6fda8786c3`  
> Research authority: `MC-STAGE14-XIANDENG-USER-FIT-01`  
> Research merge: `fe70f349c5952c78dc4c0b8d80aa1d9cf768c54b`  
> Verdict: **PASS / MAINLINE RELEASED**

## 1. Research gate

Research main 已发布用户拟合合同：

```text
Opening command snapshot = FROZEN / OWNER-CONFIRMED
Trigger formula          = USER_FIT / REPLACEABLE
Steal formula            = USER_FIT / REPLACEABLE
Active rate reduction    = BASELINE CLOSED
Stack cap                = 4 / Ju Yi commander 5
Ambush immunity          = BASELINE CLOSED

Independent layer expiry = OPEN / ENGINEERING_PROVISIONAL
Zero-loss trigger        = OPEN / ENGINEERING_PROVISIONAL
Fine aftermath order     = OPEN
Canonical skill id       = OPEN
```

Runtime 测试不得把 OPEN 项反向升级为 Gameplay Truth。

## 2. Opening command snapshot

PASS：

- `resolve_definition()` 在 PRE_BATTLE admission 时调用 `AttributeSystem.get_defense(context, owner)`；
- 触发概率与单次统率偷取量随后写入全队 reaction marker；
- 后续统率变化不会重新计算这两个值；
- 定向测试覆盖 PRE_BATTLE 属性修饰进入快照，以及安装后属性变化不重算。

## 3. Ambush immunity

PASS：

- 只保护 AMBUSH；不附带其它控制免疫；
- standard StateCandidate 在 admission 层被 selective immunity 拒绝；
- legacy lifecycle ingress 的物理 AMBUSH 状态在 effectiveness 层被抑制；
- Provider dependency/effectiveness 继续由现有 owner 判定；
- 没有在 EventBus 上建立玩法执行监听器。

Provider 死亡、禁用、威慑期间的完整免疫表现仍继承当前 Provider/effectiveness 解释，不升级为额外战法真相。

## 4. Damage received reaction

PASS：

- 新 `DamageReceivedReactionPort` 装饰已有 `DamageAftermathPort`；
- settled hit fact 读取 canonical damage_instance_id / source_unit_id / actual troop loss；
- 每个 marker 记录 processed_damage_ids，重复事实不重复抽 RNG；
- 概率抽取继续使用唯一 RandomSystem；
- 不重新选择攻击者或目标；
- 分支比较使用结算后兵力百分比的整数交叉乘法。

当前只对正实际损兵、敌对且双方存活的 settled hit 抽样。零损兵不触发是明确保留的工程暂定口径。

## 5. Attribute steal branch

PASS：

- 攻击者 defense 负修饰与受伤者 defense 正修饰使用相同 Steal(x)；
- 两端先共同 preflight；任一侧超 cap 时整体不提交，避免半次偷取；
- 不直接写 Unit 基础统率；
- 继续走 StateApplicationCoordinator / StateConflictPolicy / StateLifecycleSystem；
- timed layer 的 Provider dependency 保留来源身份。

## 6. ACTIVE activation-rate branch

PASS：

- equal-or-higher troop-ratio branch 对攻击者 ACTIVE 发动率 `-3pp`；
- ASSAULT 不受影响；
- 使用 existing activation-rate modifier；
- 4/5 层 cap 由 bounded modifier conflict seam 执行。

## 7. Bounded stacking

PASS AS IMPLEMENTATION / OPEN AS GAMEPLAY DETAIL：

- bounded modifier 对相同 Provider / stack_group / dimension 做 duplicate 与 cap 判定；
- 普通未限层 AttributeBonus / ActivationRateBonus 的既有 conflict 语义未被替换；
- 每层当前独立 2 回合到期，新层不刷新旧层；
- 满层不替换最早层。

后两项仍是 Research 明确 OPEN 的工程解释。

## 8. Damage aftermath source plumbing

PASS：

- `DamageAftermathFact` 仅新增可选 `source_unit_id`，旧调用保持兼容；
- factory 优先显式 source，否则读取已有 damage_result.source_id；
- cleave direct aftermath 只补传既有 request.source_id；
- 不修改 DamageSystem、DamageResolutionSystem 或伤害公式。

## 9. Frozen owner integrity

相对当前 main，分支没有直接改写：

- DamageSystem；
- DamageInstanceCoordinator；
- DamageResolutionSystem；
- DamageModifierSystem 的既有数学管线；
- RecoverySystem；
- TroopSystem；
- StateLifecycleSystem；
- RandomSystem；
- TargetSystem；
- TriggerSystem；
- BattleFinalizationCoordinator。

本轮对 `state_modifiers.py` 的变更是新增 typed bounded params 与 conflict adapter 分支；对既有普通 modifier 路径保留原语义。

## 10. Local validation evidence

```text
Focused tests = 59 passed
Full pytest   = 2077 passed
Engine demo   = PASS
Demo rounds   = 5
Demo events   = 313
Remaining states after finalization = 0
```

这些结果证明当前实现与当前合同一致，不证明 OPEN 口径等于官方真实规则。

## 11. Preserved OPEN boundaries

- 20246 是否为 canonical client skill id；
- 两个 USER_FIT 公式是否等于官方真实缩放；
- ROUND_HALF_UP 是否等于客户端 half-tie；
- 零实际损兵是否触发；
- 每层独立到期还是整体刷新；
- 满层时是否替换/刷新最早层；
- post-hit 比例比较相对急救/吸血等 aftermath 的精细顺序；
- DOT 来源死亡、Provider 死亡后既有层、分享/分摊/连环直接损兵的战法特异行为。

## 12. Audit verdict

```text
XIANDENG_RESEARCH_GATE          = PASS
XIANDENG_SNAPSHOT_CONFORMANCE   = PASS
XIANDENG_IMMUNITY_INTEGRATION   = PASS
XIANDENG_REACTION_INTEGRATION   = PASS
XIANDENG_STACKING_INTEGRATION   = PASS
XIANDENG_OWNER_INTEGRITY        = PASS
XIANDENG_OPEN_BOUNDARIES        = PRESERVED

XIANDENG_RUNTIME_AUDIT          = PASS
MAINLINE_READINESS              = PASS
```

## 13. Mainline release

```text
Research PR #15
= MERGED
Research merge
= fe70f349c5952c78dc4c0b8d80aa1d9cf768c54b

Battle PR #55
= MERGED
Battle merge
= cfaf3ffaac3646aff7e7e69713a0b0b3064ef24b

PR CI
= 37346322521 / SUCCESS
Full pytest
= 2077 passed
Stage13-D1
= 11 passed

Merged-main CI
= 37346440394 / SUCCESS
Full pytest
= 2077 passed
Stage13-D1
= 11 passed
```

```text
XIANDENG_MAINLINE_RELEASE = PASS
```
