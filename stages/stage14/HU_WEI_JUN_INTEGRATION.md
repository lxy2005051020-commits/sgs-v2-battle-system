# 虎卫军接入

日期：2026-10-05。状态：IMPLEMENTED / USER_PROVISIONAL_MODEL / AUDIT_PASS / PR_READY。
基线：当前远程 main `bde8cff`（青州兵已合入）。工作区：`stage14-hu-wei-jun`。

## 行为和参数

- PRE_BATTLE 将全队盾兵绑定为虎卫军身份；由实际持有者槽位提供效果。
- 以普攻经 Guard 重定向后的实际目标判定是否攻击主将；主将即将受普攻前触发。
- 存活副将按 DEPUTY_1、DEPUTY_2 顺序，先加 12 武力，再对攻击者造成兵刃反击。
- 每队每回合一次；副将各自最多叠加五次武力（最高 +60），满层后仍造成反击。
- 原攻击者被击败或战斗终止时取消原普攻；已准入反应批次按既有 finalization 合同排空，死亡目标记录零损失。
- 持有者禁用、阵亡或被威慑抑制时不触发；未触发不占当回合预算。
- 典韦或许褚为阵容主将时，其自身统率 +25。

用户已明确选择增加伤害率百分点，并修正满级上限为 40%、每损失 250 兵力增加 1%：

```text
Loss_i = max(0, EntryTroops_i - CurrentTroops_i)
Bonus_i = min(floor(Loss_i / 250), 40) / 100
Coefficient_i = 0.72 + Bonus_i  # 最高 1.12
```

损兵按副将各自 PRE_BATTLE 入场兵力与当前兵力差读取。**治疗后增幅回落已由项目所有者明确确认并进入 Research 合同**；具体 250 兵/+1pp/+40pp 仍是可替换的 USER_PROVISIONAL_MODEL。
只增加这一次虎卫军反击的伤害率，不修改副将所有伤害。兵刃公式、随机数、整数化、分担、吸血继续由现有系统处理。

Research authority：`MC-STAGE14-HUWEI-PROVISIONAL-01`，已通过 Research PR #14 合入 main（`1befa30990a7a12899bb4cc2fddf65395da2c634`）。
基础描述来源仍保留 `TROOP_SKILL_CATALOG.md` 虎卫军候选行。
该目录将 `20154` 标为推断 ID；这里沿用目录编号，不宣称已核实客户端 canonical ID。
目录记载统率 +25，但未提供可核实等级曲线；本次保留 +25，不自行扩大为 +50。
普攻重定向后判定、存活副将顺序、反应批次排空及净损兵口径都是工程解释，尚未用真实战报冻结。

## 组件和所有权

```text
hu_wei_jun.py / TroopSkillConfig / TROOP_SKILL_REGISTRY
  TEAM_COMMANDER -> ApplyStateSkillEffectSpec(TeamPreAttackReactionParams)
  supplemental TEAM_COMMANDER -> AttributeBonusParams(defense, 25)
ReactingTargetResolutionSystem
  canonical TargetResolutionSystem.resolve -> TeamPreAttackReactionSupport
  StateEffectivenessPolicy + ProviderNode -> round budget in state parameters
  StateLifecycleSystem -> AttributeBonusParams(attack, 12 * stacks)
  FutureAdmissionGate(COUNTER_BATCH) -> existing finalization reaction capability
  ExecutionRight -> DamageInstanceCoordinator(COUNTER) -> existing settlement
  surviving actor/target -> original NormalAttackSystem
```

新增通用模块 `pre_attack_reaction.py`；单战法模块只声明参数。
未改 Engine、NormalAttackSystem、TargetResolutionSystem、CounterSystem、伤害公式、TroopSystem、PendingWork 或 EventBus。
BattleSystems 通过 TargetResolutionSystem 子类适配器组合普攻前同步反应，不订阅 EventBus 执行玩法。
遵循项目真实兵种注册入口，无额外 autodiscovery 或虚构 register_skill API。

## 验证

定向测试涵盖公式 249/250/9750/10000 边界、上限、独立兵力、治疗回落、触发顺序、
武力五层、每回合一次、禁用/威慑/阵亡、攻击者死亡、统领属性及非法兵种准入。
真实 Engine 示例与冻结 owner 审计见 `huwei_evidence/`。
本地与远端验证结果见 `huwei_evidence/verification.json`；独立审计见 `HU_WEI_JUN_RUNTIME_AUDIT.md`。当前允许进入 Battle PR 审核，尚未合入 main。
