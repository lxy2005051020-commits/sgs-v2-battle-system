# 锦帆军接入（20152）

日期：2026-10-06。状态：**CURRENT_MAIN_REBASED / BOUNDED_IMPLEMENTED / FORMULA_PLACEHOLDERS / AUDIT_PASS**。

旧 Runtime 基线：`d88e7cd`；当前已重建到 `main@2e38f3a`。
Research authority：`MC-STAGE14-JIN-FAN-JUN-01`。
旧 PR #51 已关闭为 superseded；current-main 候选为 PR #59 / `stage14-jin-fan-jun-rebase-20261006`。

## Research 合同

项目所有者已确认：

- 普通攻击后基础触发概率：45%；
- 目标没有有效溃逃时施加 2 回合溃逃；
- 满级标称溃逃伤害率：64%，受武力影响；
- 溃逃武力缩放精确公式暂时使用显式 placeholder；
- 目标已经存在有效溃逃时，造成 110% 兵刃伤害；
- 恢复基数为本次 110% 追加兵刃伤害的**伤害量**，不是目标实际损失兵力；
- 恢复比例 30%，取整统一采用进一法；
- 甘宁统领时，最高属性影响触发概率的精确公式暂时使用显式 placeholder；
- 甘宁统领额外使**另外两名友军**会心 +6%，不包括甘宁本人。

Research 合同：
`MC-STAGE14-JIN-FAN-JUN-01 = BOUNDED_FROZEN`。

## Formula placeholder policy

当前真实缩放公式仍 OPEN，Runtime 不将占位值冒充真实公式：

```text
JIN_FAN_ROUT_SCALING_FORMULA = None
GAN_NING_TRIGGER_PROBABILITY_FORMULA = None

Rout coefficient placeholder = 0.64
Gan Ning trigger placeholder = 0.45
```

含义是：

- 非甘宁分支当前用 45% 基础触发；
- 甘宁主将分支在真实最高属性公式冻结前也暂用 45%；
- 溃逃 DOT 在真实武力缩放冻结前暂用 0.64；
- 两处均通过独立常量/函数表达，未来公式冻结后原位替换；
- 测试通过不等于 placeholder 升级成 Gameplay Truth。

## 组件映射

```text
TroopSkillConfig / TROOP_SKILL_REGISTRY
  PRE_BATTLE -> BOW / JIN_FAN_JUN identity
  FIXED_ALL_TEAM -> runtime_normal_attack_followup
    45% / 甘宁概率 placeholder
    -> inherit actual normal-attack target
       target has effective ROUT
       -> 110% WEAPON damage
       -> CEIL(settled followup damage amount * 30%)
       -> RecoverySystem
       otherwise
       -> ROUT duration 2
       -> coefficient placeholder 0.64
       -> ContinuousDamageBasisProducer

  甘宁 COMMANDER
  -> supplemental definition
  -> TEAM_NON_COMMANDERS
  -> CRITICAL +6%
  -> 甘宁本人不获得该加成
```

## Recovery basis

旧候选实现曾使用：

```text
actual_target_troop_loss
```

现已按项目确认修改为：

```text
FollowupDamageAmount
= DamageResolutionResult.assigned_target_damage
```

恢复量：

```text
RecoveryAmount = CEIL(FollowupDamageAmount * 30%)
```

随后进入已有 RecoverySystem，继续接受禁疗、伤兵容量、治疗修饰及最终结算规则。

这意味着恢复计算不因目标剩余兵力不足而把基数降为实际扣兵量。

## 甘宁会心目标

新增通用目标模式：

```text
SkillTargetMode.TEAM_NON_COMMANDERS
```

仅返回同队存活的非主将单位。

在标准三人队中：

```text
甘宁主将
├─ 甘宁：不获得 +6% 会心
├─ 副将1：+6% 会心
└─ 副将2：+6% 会心
```

会心继续复用官方状态 `690070 CRITICAL` 与既有状态/Provider 生命周期。

## 保留 OPEN 的问题

以下没有被 placeholder 偷偷关闭：

- 溃逃 64% 的真实武力缩放公式；
- 甘宁最高属性影响触发概率的真实公式；
- 两个公式的精确属性读取时点与可能上下限；
- 普攻派生效果相对顺序；
- suppressed 溃逃是否满足“已有溃逃”条件；
- 锦帆军 DOT 的具体来源失效/死亡战法特异行为。

## 验证目标

本分支测试需要覆盖：

- 正式 PRE_BATTLE 可以使用显式 placeholder 完成原子准入；
- 全队锦帆军身份与 followup provider 绑定；
- 无溃逃 -> DOT；
- 已有溃逃 -> 110% 兵刃伤害 + 30% 恢复；
- 恢复基数读取 `assigned_target_damage`；
- 恢复使用 CEIL；
- 甘宁主将只给两个 non-commanders +6% 会心；
- 甘宁本人无该会心；
- 目标继承、威慑/停用、来源死亡、禁疗、战斗最终清理；
- generic missing coefficient 仍 fail-closed。

## 发布边界

锦帆军已从“公式缺失导致 Production Admission CLOSED”切换为：

```text
BASE BEHAVIOR             = BOUNDED FROZEN
FORMULA PLACEHOLDERS      = AUTHORIZED
PRODUCTION ADMISSION      = ENABLED
RUNTIME IMPLEMENTATION    = COMPLETE CANDIDATE
MAINLINE MERGE            = READY AFTER FINAL PR-HEAD CI
```

真实公式未来应以 Research amendment 替换 placeholder，不重开已经冻结的恢复基数、取整和甘宁会心目标范围。


## Current-main compatibility

本轮不是把旧锦帆军分支直接 merge 到新主线，而是以最新 main 为底座重新移植。

```text
old PR #51
= CLOSED / SUPERSEDED

new PR #59
= CURRENT-MAIN PORT
= MERGEABLE
= 2141 PASSED
= STAGE13-D1 11 PASSED
```

关键兼容点：

- 保留解烦卫现有 branched followup；
- 锦帆军 target-state branch 与其并列存在；
- 当前 main 的 2114 项测试全部继续通过；
- 新增锦帆军 27 项测试后总计 2141 项通过。
