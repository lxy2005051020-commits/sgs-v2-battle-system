# 虎卫军（20154 provisional）Runtime Independent Audit

> Date: 2026-10-05  
> Audit target: `stage14-hu-wei-jun` @ `a9c8b64a9b34875bdb98d34b5b5b8e476f0208ec`  
> Research authority: `MC-STAGE14-HUWEI-PROVISIONAL-01`  
> Research merge: `1befa30990a7a12899bb4cc2fddf65395da2c634`  
> Verdict: **PASS / USER-PROVISIONAL MAINLINE-READY**

## 1. Research gate

Research main 已发布：

```text
MC-STAGE14-HUWEI-PROVISIONAL-01
= USER_PROVISIONAL_MODEL / RUNTIME_BASELINE_ENABLED / NOT_EMPIRICALLY_FROZEN

Healing rollback
= FROZEN / OWNER-CONFIRMED

Loss model
= every 250 net lost troops +1pp
= capped at +40pp
= USER_PROVISIONAL / REPLACEABLE
```

Catalog 候选文本中的“最多提高20%”保留为来源记录。当前 +40pp 暂定模型由项目所有者授权，不伪称已经从该 Catalog 文本或 Runtime 测试实证得到。

## 2. Contract conformance

### Admission / identity

PASS：

- SHIELD -> HU_WEI_JUN；
- PRE_BATTLE 继续复用 TroopSkillConfig / troop admission；
- Provider 保留实际携带者与战法槽位；
- 非盾兵原子拒绝，不产生特殊兵种身份残留。

### Trigger

PASS：

- canonical TargetResolution 完成后读取 post-redirect actual target；
- 只有实际目标为队伍 COMMANDER 时才触发；
- 每队每回合最多 1 次；
- 未满足条件、Provider 无效、威慑抑制或无存活副将时不消耗触发预算；
- 两名存活副将按阵容位置顺序执行。

### Attribute stack

PASS：

- 每名副将每次合法触发先获得 +12 武力；
- 每名副将独立计数；
- 最多 5 层，即最高 +60；
- 满层后仍允许后续合法虎卫军反击；
- 属性通过既有 Attribute Modifier 状态接入，不直接改 Unit 基础 attack。

### Counter damage

PASS：

- 满级基础反击系数 0.72；
- 当前暂定损兵模型：
  `Bonus = min(floor(max(0, EntryTroops-CurrentTroops)/250), 40)/100`；
- 最终系数 `0.72 + Bonus`，当前暂定最高 1.12；
- 只作用于本次虎卫军反击；
- 伤害进入既有 ExecutionRight -> DamageInstanceCoordinator -> DamageSystem / settlement owner。

### Healing rollback

PASS：

当前实现每次触发即时读取：

```text
Loss = max(0, EntryTroops - CurrentTroops)
```

因此治疗后 CurrentTroops 上升时 Bonus 自动回落。

定向测试已经覆盖：

```text
CurrentTroops 9200 -> higher loss bonus
heal to 9800
-> next-round coefficient returns to lower value
```

这与 owner-confirmed 合同一致；未实现历史累计损兵或不可逆峰值缓存。

### Commander supplement

PASS：

- 典韦或许褚为 COMMANDER 时，仅该主将获得 defense +25；
- 其它武将不获得该统率加成；
- 未自行推导等级曲线。

## 3. Architecture / frozen owner audit

PASS：

该分支相对 `main@bde8cff` 没有修改：

- `normal_attack_system.py`；
- `target_system.py`；
- DamageSystem；
- DamageInstanceCoordinator；
- DamageResolutionSystem；
- DamageModifierSystem；
- RecoverySystem；
- StateLifecycleSystem；
- RandomSystem；
- TroopSystem；
- TriggerSystem；
- BattleFinalizationCoordinator。

新增通用 seam 为：

```text
pre_attack_reaction.py
  ReactingTargetResolutionSystem
    -> canonical TargetResolutionSystem.resolve()
    -> TeamPreAttackReactionSupport.react()
    -> FutureAdmissionGate(COUNTER_BATCH)
    -> existing ExecutionRight
    -> existing DamageInstanceCoordinator
```

BattleSystems 只负责组合/注入；没有 EventBus gameplay listener，也没有第二套 NormalAttackSystem、CounterSystem 或 DamageSystem。

Stage13-D1 frozen-owner audit：PASS。

## 4. Runtime boundaries preserved

以下不因本次 PASS 升级为 Gameplay Truth：

- canonical client skill ID 20154 仍为 Catalog 推断；
- 官方真实损兵缩放公式与上限仍 OPEN；
- Catalog 20% 与用户暂定 +40pp 的差异仍待实证；
- Guard / 其它 BEFORE_NORMAL_ATTACK 效果之间的更细官方微时序仍 OPEN；
- 当前 post-redirect reaction timing、两副将顺序与 finalization drain 属于 Runtime 可替换解释。

“治疗后回落”不在上述 OPEN 中，已由项目所有者明确关闭。

## 5. Regression evidence

远端分支 CI：

```text
GitHub Actions = 37337145447 / SUCCESS
Focused tests  = 22 passed
Full pytest     = 2018 passed
Stage13-D1      = 11 passed
Engine demo     = PASS
diff-check      = PASS
```

## 6. Verdict

```text
HUWEI_RESEARCH_GATE        = PASS
HUWEI_CONTRACT_CONFORMANCE = PASS
HUWEI_HEALING_ROLLBACK     = PASS
HUWEI_OWNER_INTEGRITY      = PASS
HUWEI_REGRESSION           = PASS
HUWEI_OPEN_BOUNDARIES      = PRESERVED

HUWEI_RUNTIME_AUDIT        = PASS
MAINLINE_READINESS         = READY_WITH_USER_PROVISIONAL_MODEL
```
