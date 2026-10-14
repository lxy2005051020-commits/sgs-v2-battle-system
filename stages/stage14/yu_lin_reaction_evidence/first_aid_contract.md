# 690078 FIRST_AID (急救) Official Mechanism Contract
# 《三国志·战略版》官方状态机制合同

Status ID: `690078`  
Official Name: `急救`  
Internal Name: `FIRST_AID`  
Category: `TRIGGERED_RECOVERY_STATE` (受击被动反应触发恢复状态)  
Family: `RECOVERY` (恢复效果家族)  
Contract Status: `✅ FROZEN`  
Frozen Date: `2026-09-06`  
Authoritative Sources: `[O + B + U]`  

---

## 1. Identity & Classification (状态标识与分类)

```yaml
Identity:
  Status_ID: 690078
  Official_Name: 急救
  Internal_Name: FIRST_AID
  Category: TRIGGERED_RECOVERY_STATE
  Family: RECOVERY
  Client_Text: "获得急救状态，受到伤害时有概率回复兵力"
  Evidence: "[O + B]"
  Confidence: CONFIRMED
```

---

## 2. Application & Instance Model (施加与实例模型)

```yaml
Application:
  Source_Skills:
    - 青囊 (20030, 指挥)
    - 陷阵营 (20096, 兵种)
    - 草船借箭 / 拓·草船借箭 (20143/20474/20539等, 主动)
    - 援救 (29613, 主动)
    - 国色天香 (20289, 主动)
    - 云聚影从 (20214, 指挥)
    - 运筹帷幄 (20504, 指挥)
    - 白马镇北 (26504, 指挥)
  Target_Entity: 友军单体 / 友军群体 / 自身
  Initial_Duration: 由施加技能显式定义 (如草船 2回合, 陷阵营 3回合, 青囊 4回合)
  Event_Protocol: cfg_21 (<Hero>的「急救」效果已施加)

Instance_Model:
  Limit: SINGLE_SHARED_INSTANCE (单个实体全局同一时刻最多维持 1 个有效急救状态)
  Same_Source_Reapplication: REFRESH_AND_OVERWRITE (重置持续时间并覆盖实例参数)
  Cross_Skill_Reapplication: REFRESH_AND_OVERWRITE (后施加战法完全取代旧战法来源、技能与参数)
  Field_Level_Refresh:
    Replace_Source_Unit: true
    Replace_Source_Skill: true
    Reset_Duration: true
    Replace_Probability_Context: true
    Replace_Potency_Model: true
    Replace_Attribute_Context: true
    Replace_Recovery_Modifier_Context: true (依据 [U])
  Evidence: "[B + U]"
  Confidence: CONFIRMED
```

---

## 3. Trigger Architecture & Frequency (触发架构与频次)

```yaml
Trigger:
  Trigger_Node: AFTER_DAMAGE_EVENT (紧随每次合格伤害事件兵力扣减后立即触发检定)
  Trigger_Frequency: PER_ELIGIBLE_DAMAGE_EVENT (无回合/行动次数上限; 观察到单回合最高触发 22 次)
  Round_Cap: NONE_OBSERVED (彻底排除单回合单次上限假说)
  Probability_Check: PER_EVENT_PROBABILITY_CHECK (每个合格伤害事件分别产生一次对应概率判定机会)
  Probability_Values:
    - 陷阵营: 40% (高顺受统率加成)
    - 青囊 / 援救: 50%
    - 国色天香: 60%
    - 草船借箭: 70%
    - 100% 来源: 依专属技能描述

Damage_Eligibility:
  Normal_Attack: ELIGIBLE (普通攻击伤害可触发)
  Active_Command_Skill_Damage: ELIGIBLE (主动/指挥物理与谋略伤害可触发)
  Continuous_Damage_Ticks: ELIGIBLE (灼烧, 水攻, 中毒, 溃逃, 沙暴, 叛逃 6 类跳伤均可触发)
  Multi_Hit_Damage: SEPARATE_OPPORTUNITY_PER_HIT (多段伤害每段独立产生合格触发检定机会)
  Pursuit_Counterattack: ELIGIBLE (突击与反击伤害可触发)
  Settled_Zero_Damage:
    Weakness_Zero: ELIGIBLE (攻击者虚弱致损失0，急救正常产生机会并可恢复已有伤兵 [B])
    Barrier_Zero: ELIGIBLE (抵御吸收致损失0，急救正常产生机会并可恢复已有伤兵 [B])
    Mitigation_Zero: ELIGIBLE (免伤防御叠加致损失0，急救正常产生机会 [B])
  Evasion_Miss: INELIGIBLE (规避未命中不构成伤害结算事件，零触发 [B])
  Trigger_Prerequisite: RESOLVED_DAMAGE_HIT (完成受击命中伤害管线结算，不要求实际扣兵必须大于0)
  Evidence: "[B]" (全量 80,396 次常规判定 + 438 例零损失定向判定样本)
  Confidence: CONFIRMED
```

---

## 4. Potency Architecture (恢复强度架构)

急救状态的恢复强度模型采取**施加期上下文锁定**与**触发期动态输入解耦**的混合架构：

```yaml
Potency_Architecture:

  Recovery_Model: SOURCE_SKILL_DEFINED
    Treatment_Rate_Based:
      Description: 恢复量基于施加者属性与战法治疗率计算 (如青囊, 陷阵营, 援救)
      Formula_Pattern: f(Treatment_Rate, Source_INT, Source_COMMAND)
    Damage_Ratio_Based:
      Description: 恢复量基于当次受击扣减伤害量的一定比例计算 (如草船借箭)
      Formula_Pattern: Triggering_Damage * Ratio(COMMAND)

  Application_Time_Inputs (LOCKED_AT_APPLICATION [B + U]):
    - Source Base Attributes:
        Gaoshun_COMMAND: LOCKED_AT_APPLICATION (CONFIRMED [B])
        Tested_INT_Skills: LOCKED_AT_APPLICATION (CONFIRMED [B])
        Other_Attributes: LOCKED_AT_APPLICATION (CONFIRMED [U])
    - Treatment Rate / Damage Ratio Parameter: LOCKED_AT_APPLICATION
    - Recovery Modifiers:
        Source_Side_Modifier: LOCKED_AT_APPLICATION (CONFIRMED [U])
        Target_Side_Modifier: LOCKED_AT_APPLICATION (CONFIRMED [U])
        State_Specific_Modifier: LOCKED_AT_APPLICATION (CONFIRMED [U], 如才辩机捷)
    Runtime_Changes_Recalculate: false (存续期间属性/修饰符起伏不追溯修改已有实例)

  Trigger_Time_Dynamic_Inputs (DYNAMIC_AT_RECOVERY_RESOLUTION [B]):
    - Triggering_Damage_Amount: 仅限草船借箭等伤害比例型战法，动态读取当次受击扣减量
    - Target_Alive: 必须存活，致命伤害立即硬终止，禁止墓地复活
    - Recovery_Cap: 动态受当前已损失兵力缺口截断 (min(potency, max_hp - current_hp))
    - Healing_Prevention: 处于禁疗状态时动态拦截，cfg_129 扣减恢复至 0
```

---


Runtime_Deactivation:
  Trigger_Mechanism: EXTERNAL_SYSTEM_DEACTIVATES_SOURCE_SKILL (由外部系统通过伪报或军心动摇等使来源技能失效，进而挂起关联状态，非急救主动监听)
  Source_Skill_Deactivation:
    COMMAND_Sourced: TEMPORARILY_DEACTIVATED (CONFIRMED [B], 见青囊战报_2202663: 来源华佗受伪报，友军急救触发 cfg_204 暂时失效，伪报解除触发 cfg_205 恢复)
    TROOP_Sourced: TEMPORARILY_DEACTIVATED (CONFIRMED [B], 见陷阵营战报_3458515: 来源刘备军心动摇，全体急救触发 cfg_204，军心动摇解除触发 cfg_205 恢复)
    ACTIVE_Sourced: NOT_APPLICABLE / NO_DISCRIMINATING_MECHANISM (主动战法如草船借箭、援救无在存续期使已施加状态中途失效的机制)
    EQUIPMENT_TRAIT_Sourced: UNRESOLVED_NON_BLOCKING
  State_Protocol:
    Temporary_Inactive_Event: cfg_204 (<Hero>的「急救」暂时失效)
    Resume_Event: cfg_205 (<Hero>的「急救」继续生效)
  During_Inactive:
    Probability_Check: SUPPRESSED (CONFIRMED [B], 暂时失效期间受击完全不产生 cfg_16 检定)
    Recovery_Execution: SUPPRESSED (CONFIRMED [B], 暂时失效期间受击完全不产生 cfg_96 恢复)
    Duration_Clock: CLOCK_CONTINUES (CONFIRMED [B], 青囊在第1回合失效、第2回合恢复后，依然在第4回合准时到期 cfg_22 移除，时钟未暂停或顺延)

## 5. Lifecycle, Death & Control Interactions (生命周期、死亡与控制交互)

```yaml
Lifecycle:
  Duration_Unit: N_ROUNDS
  Expiration_Node: 目标在第 N+1 回合行动开始窗口进行到期检查，到期派发 cfg_22

Death_Interactions:
  Source_Death: PERSISTS (施加者阵亡后，挂载在存活目标身上的急救持续生效至生命周期结束)
  Target_Death: HARD_TERMINATION (目标兵力归 0 阵亡时，状态机立即清理所有挂载急救，剩余事件中止)

Control_Interactions:
  Stun (震慑): DOES_NOT_SUPPRESS_FIRST_AID_TRIGGER (CONFIRMED [B], 4,757 例正常触发)
  Disarm (缴械): DOES_NOT_SUPPRESS_FIRST_AID_TRIGGER (CONFIRMED [B], 2,416 例正常触发)
  Silence (计穷): DOES_NOT_SUPPRESS_FIRST_AID_TRIGGER (CONFIRMED [B], 2,109 例正常触发)
  Confusion (混乱): DOES_NOT_SUPPRESS_FIRST_AID_TRIGGER (CONFIRMED [B], 2,968 例正常触发)
  Weakness (虚弱): DOES_NOT_SUPPRESS_FIRST_AID_TRIGGER (CONFIRMED [B], 1,760 例正常触发)

Removal_Interactions:
  Negative_Cleanse: DOES_NOT_REMOVE (净化/刮骨疗毒不移除正面急救增益)
  Positive_Dispel: UNRESOLVED_NON_BLOCKING (战报库中驱散仅移除属性标签，无急救被驱散直接用例)

State_Ordering:
  Resolution_Window: 同一伤害事件后触发窗口
  Policy: UNRESOLVED_NON_BLOCKING (不影响机制实现)
```

---

## 6. Formula Status (公式研究范围声明)

- **精准常数研究**: 草船借箭统率非线性映射常数、高顺统率增幅系数、微观整除与伪随机数发生器实现归类为 `FORMULA_RESEARCH_OUT_OF_SCOPE`。
- **机制充分性**: 上述非线性公式常数不影响急救状态机的触发拓扑、实例流转与时序管线，满足正式机制冻结标准。
