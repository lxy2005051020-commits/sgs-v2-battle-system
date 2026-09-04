# Stage 4 · 其余 35 个官方状态未来系统映射 V1

> 本文只记录 Stage 4 **未实现**的 35 个官方 BattleState 的未来主要系统归属。
> 语义基线仍为同目录 `OFFICIAL_STATE_CATALOG_V1.md` / `official_state_rules_v1.csv`。
> 本文不改变官方原文，也不提前实现 Effect、Trigger、Recovery、SkillRuntime 等后续阶段能力。

Stage 4 第一批已实现且因此不列入下表的 5 个状态：

```text
first_strike / 先攻
ambush / 遇袭
disarm / 缴械
stun / 震慑
weakness / 虚弱
```

## 未实现 35 状态映射

| state_id | 中文名称 | 官方分类 | Stage 4 状态 | 未来主要系统映射 | 映射理由 |
|---|---|---|---|---|---|
| `burn` | 灼烧 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 每回合持续伤害，需要周期效果触发与伤害请求生成。 |
| `flood` | 水攻 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 武将行动时触发伤害，需要行动节点效果触发。 |
| `poison` | 中毒 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 武将行动时触发伤害，需要行动节点效果触发。 |
| `rout` | 溃逃 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 武将行动时触发伤害，需要行动节点效果触发。 |
| `sandstorm` | 沙暴 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 武将行动时触发伤害，需要行动节点效果触发。 |
| `rebellion` | 叛逃 | 持续性状态 | DEFER | `DEFER_EFFECT_TRIGGER / PERIODIC_EFFECT` | 每回合伤害且无视防御，需要周期触发及后续特殊伤害规则。 |
| `first_aid` | 急救 | 持续性状态 | DEFER | `DEFER_RECOVERY_SYSTEM` | 受到伤害时恢复兵力，需要统一恢复结算与受伤触发。 |
| `recuperation` | 休整 | 持续性状态 | DEFER | `DEFER_RECOVERY_SYSTEM` | 每回合恢复兵力，需要周期恢复结算。 |
| `combo` | 连击 | 功能性状态 | DEFER | `DEFER_ACTION_REPEAT` | 每回合额外普通攻击，需要行动重复/追加行动规则。 |
| `evasion` | 规避 | 功能性状态 | DEFER | `DEFER_HIT_RESOLUTION` | 是否回避伤害属于命中/规避裁决层。 |
| `barrier` | 抵御 | 功能性状态 | DEFER | `DEFER_DAMAGE_PREVENTION` | 免疫伤害属于正式伤害阻止规则。 |
| `cleave` | 群攻 | 功能性状态 | DEFER | `DEFER_TRIGGER_SYSTEM` | 普攻命中后对同部队其他武将追加伤害，需要触发系统。 |
| `counterattack` | 反击 | 功能性状态 | DEFER | `DEFER_TRIGGER_SYSTEM` | 受到普通攻击后反向产生攻击，需要受击触发系统。 |
| `damage_split` | 分摊 | 功能性状态 | DEFER | `DEFER_DAMAGE_REDIRECT` | 多个目标分别承担部分伤害，需要统一伤害重定向/拆分。 |
| `damage_share` | 分担 | 功能性状态 | DEFER | `DEFER_DAMAGE_REDIRECT` | 其他单位替目标承担伤害，需要统一伤害重定向。 |
| `insight` | 洞察 | 功能性状态 | DEFER | `DEFER_STATE_APPLICATION_POLICY` | 免疫控制状态应在状态施加政策层决定，而非状态生命周期存储层。 |
| `sure_hit` | 必中 | 功能性状态 | DEFER | `DEFER_HIT_RESOLUTION` | 无视规避及抵御，需要命中/规避/抵御统一裁决。 |
| `defense_pierce` | 破阵 | 功能性状态 | DEFER | `DEFER_DAMAGE_MODIFIER` | 造成伤害时无视统率及智力，属于伤害计算修正。 |
| `weapon_lifesteal` | 倒戈 | 功能性状态 | DEFER | `DEFER_RECOVERY_SYSTEM` | 基于兵刃伤害量恢复自身，需要伤害后恢复结算。 |
| `strategy_lifesteal` | 攻心 | 功能性状态 | DEFER | `DEFER_RECOVERY_SYSTEM` | 基于谋略伤害量恢复自身，需要伤害后恢复结算。 |
| `chain_link` | 铁索连环 | 功能性状态 | DEFER | `DEFER_DAMAGE_REDIRECT` | 一个目标受伤反馈给其他目标，需要伤害传播/重定向。 |
| `guard` | 援护 | 功能性状态 | DEFER | `TARGET_REDIRECT / DEFER_DAMAGE_REDIRECT` | 为目标承担普通攻击，需要目标重定向并衔接伤害归属。 |
| `vigilance` | 警戒 | 功能性状态 | DEFER | `DEFER_DAMAGE_MODIFIER` | 减少单次受到伤害，属于受伤侧伤害修正。 |
| `silence` | 计穷 | 控制状态 | DEFER | `DEFER_SKILL_SYSTEM` | 禁止主动战法，需要主动战法系统存在后解释。 |
| `confusion` | 混乱 | 控制状态 | DEFER | `DEFER_TARGET_RESOLUTION` | 战法和普攻无差别选目标，需要统一目标解析规则。 |
| `healing_ban` | 禁疗 | 控制状态 | DEFER | `DEFER_RECOVERY_SYSTEM` | 无法恢复兵力，应由统一恢复系统阻止。 |
| `taunt` | 嘲讽 | 控制状态 | DEFER | `DEFER_TARGET_RESOLUTION` | 强迫普通攻击指向特定目标，属于目标解析。 |
| `false_report` | 伪报 | 控制状态 | DEFER | `DEFER_SKILL_SYSTEM` | 使指挥/被动战法失效，需要相应技能运行态与失效政策。 |
| `provoke` | 挑拨 | 控制状态 | DEFER | `DEFER_SKILL_SYSTEM` | 强迫战法选择自己，需要技能目标与施放系统。 |
| `equipment_disable` | 破坏 | 控制状态 | DEFER | `DEFER_EQUIPMENT_SYSTEM` | 使装备失效，需要装备运行态与效果来源系统。 |
| `capture` | 捕获 | 控制状态 | DEFER | `DEFER_COMPOSITE_CONTROL` | 同时包含禁行动、禁伤害、禁疗、技能失效与友方不可选中，是复合控制。 |
| `critical` | 会心 | 其他 | DEFER | `DEFER_DAMAGE_MODIFIER` | 概率双倍兵刃伤害，属于伤害修正与对应概率裁决。 |
| `strategy_critical` | 奇谋 | 其他 | DEFER | `DEFER_DAMAGE_MODIFIER` | 概率双倍谋略伤害，属于伤害修正与对应概率裁决。 |
| `damage_reduction_pierce` | 看破 | 其他 | DEFER | `DEFER_DAMAGE_MODIFIER` | 无视一定比例受到伤害降低，属于伤害修正链。 |
| `intimidation` | 威慑 | 其他 | DEFER | `DEFER_SKILL_SYSTEM` | 使目标一个战法失效且排除阵法，需要技能选择与失效系统。 |

## 完整性检查

```text
持续性状态未实现：8
功能性状态未实现：15  （17 - 先攻 - 遇袭）
控制状态未实现：8     （11 - 缴械 - 虚弱 - 震慑）
其他未实现：4

8 + 15 + 8 + 4 = 35
```

所有 35 个状态均有明确未来系统映射；不存在仅标记“以后处理”的条目。
