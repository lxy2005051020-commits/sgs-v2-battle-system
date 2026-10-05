# 锦帆军（20152）Runtime Independent Audit

> Date: 2026-10-05  
> Audit target: `stage14-jin-fan-jun` @ `055337f5d770e67ce51724dea06e40798150ec9d`  
> Research authority: `MC-STAGE14-JIN-FAN-JUN-01`  
> Verdict: **PASS / BOUNDED MAINLINE-READY**

## 1. Research gate

Research main 已存在并发布：

```text
MC-STAGE14-JIN-FAN-JUN-01 = BOUNDED_FROZEN
BASE BEHAVIOR             = FROZEN
RECOVERY BASIS            = FROZEN
RECOVERY ROUNDING         = FROZEN
GAN NING CRIT TARGETS     = FROZEN
Rout scaling formula      = PLACEHOLDER / OPEN
Gan Ning probability      = PLACEHOLDER / OPEN
```

Runtime 只允许实现上述 bounded contract。Placeholder 不得被解释为已实证公式。

## 2. Contract conformance

### Base trigger

PASS：

- BOW -> JIN_FAN_JUN；
- PRE_BATTLE 使用共享 TroopSkillConfig / admission；
- 全队安装普通攻击 followup；
- 基础触发率 45%；
- followup 继承本次普通攻击实际目标，不重新选目标。

### No-ROUT branch

PASS：

- 目标没有当前 effective ROUT 时施加 2 回合 ROUT；
- 当前系数显式使用 `JIN_FAN_ROUT_COEFFICIENT_PLACEHOLDER = 0.64`；
- `JIN_FAN_ROUT_SCALING_FORMULA = None` 明确保留真实武力缩放公式未冻结；
- DOT 伤害基础继续由 ContinuousDamageBasisProducer 捕获，不复制伤害公式。

### Existing-ROUT branch

PASS：

- 已有 effective ROUT 时不刷新锦帆军 ROUT；
- 造成 110% WEAPON followup damage；
- Recovery base 读取 `DamageResolutionResult.assigned_target_damage`；
- 不读取 `actual_target_troop_loss`；
- 30% 通过 ExactRatio(30,100) 计算；
- 使用整数进一：
  `(basis * numerator + denominator - 1) // denominator`；
- 随后进入已有 RecoverySystem，因此禁疗、伤兵容量、治疗修饰继续由原 owner 管辖。

### Gan Ning commander branch

PASS：

- 甘宁必须为队伍 COMMANDER；
- 真实“最高属性 -> 触发率”公式仍为 `None`；
- 当前 placeholder 为 45%；
- supplemental target mode 为 `TEAM_NON_COMMANDERS`；
- +6% CRITICAL 只施加给存活 non-commanders；
- 甘宁本人不获得该 +6%。

## 3. Owner / architecture audit

PASS：

本 PR 没有直接修改以下 Stage13 冻结 owner：

- DamageSystem；
- DamageInstanceCoordinator；
- DamageResolutionSystem；
- DamageModifierSystem；
- RecoverySystem；
- RecoveryOpportunitySystem；
- StateLifecycleSystem；
- RandomSystem；
- TroopSystem；
- TriggerSystem；
- BattleFinalizationCoordinator。

新增能力通过组合 seam 完成：

```text
NormalAttackFollowupPort
+ ContinuousDamageBasisProducer
+ StateLifecycleSystem
+ EffectExecutor
+ RecoverySystem
```

`BattleSystems` 只负责注入上述既有 owner。

`TEAM_NON_COMMANDERS` 是 target producer intent；它没有新建第二套 TargetSystem。

## 4. RNG / provenance / lifecycle

PASS：

- 每次合法普攻 followup 仍由 SkillResolver 使用唯一 RandomSystem 判定；
- 未额外创建隐藏概率抽取；
- followup provider provenance 保留原锦帆军携带者/槽位；
- 实际伤害与 ROUT 的伤害属性来源归当前普通攻击执行者；
- 不伪造队友持有锦帆军技能槽；
- Battle finalization 仍由既有 owner 清理。

## 5. Regression evidence

PR #51 head CI：

```text
GitHub Actions run = 37320506393
pytest             = 1978 passed
Stage13-D1 audit   = 11 passed
CI conclusion      = SUCCESS
```

当前 PR：Draft / mergeable。

## 6. Explicit non-claims

以下不是本次 PASS 的冻结结论：

1. ROUT 64% 的真实武力缩放公式；
2. 甘宁最高属性对 45% 触发率的真实公式；
3. 两个真实公式的精确属性读取时点与上限；
4. 锦帆军与其它 after-normal-attack 派生效果的精细相对顺序；
5. suppressed ROUT 是否仍应满足“已有溃逃”条件；
6. 锦帆军 ROUT 在来源失效/死亡时的战法特异行为。

当前 Runtime 对 5 使用 `effective_instances`，因此 suppressed ROUT 不进入“已有 ROUT”分支。
当前 ROUT 持续效果沿用 existing always-active persistent contract。
二者均属于当前可替换继承策略，不能因为 Runtime/测试通过而升级为 Gameplay Truth。

## 7. Audit verdict

```text
JINFAN_RESEARCH_GATE          = PASS
JINFAN_CONTRACT_CONFORMANCE   = PASS
JINFAN_OWNER_INTEGRITY        = PASS
JINFAN_RNG_INTEGRITY          = PASS
JINFAN_REGRESSION             = PASS
JINFAN_OPEN_BOUNDARIES        = PRESERVED

JINFAN_RUNTIME_AUDIT          = PASS
MAINLINE_READINESS            = READY_WITH_BOUNDED_PLACEHOLDERS
```

本审计不执行 mainline merge。正式合并时仍应要求 PR CI 与 merged-main CI 均为 SUCCESS。
