# Stage 7 Evidence Matrix

> 施工基线：`main@7a07765315e0be94c6b2f741901974016b02d5ac`
>
> 本矩阵是 Stage 7 production trigger mapping 的硬 Gate。只有 `PASS_STAGE7` 才允许在 Stage 7 生产规则中接入。`DEFER` 表示当前证据不足或明确依赖后续阶段，不允许用经验补全。

## 判定规则

```text
PASS_STAGE7
= 当前证据足以冻结单实例 Stage 7 基础行为

DEFER
= 仍存在会改变单实例基础行为的关键 UNKNOWN，或明确依赖后续 reaction/modifier pipeline
```

以下未知项允许继续保留，不阻断 synthetic 基础设施施工：

```text
同名 stacking
refresh
最高值覆盖
同源 / 异源竞争
```

但必须保持：

```text
多实例 deterministic execution
≠ 官方 stacking 规则
```

## Evidence Matrix

| state_id | trigger node evidence | runtime params | source attribution | known stacking behavior | known refresh behavior | known formula / damage type | unknowns | implementation verdict |
|---|---|---|---|---|---|---|---|---|
| `burn` | 官方状态目录：`每回合持续对武将部队造成伤害`，可支持“每回合”语义，但未单独证明 Stage 7 的精确结算节点 | 需要周期伤害参数，但当前资料未冻结 coefficient 来源 | `StateInstance.source_id / source_skill_id / state_id / instance_id` 可提供完整工程 provenance | UNKNOWN | UNKNOWN | 伤害类型 UNKNOWN；基础公式/系数语义 UNKNOWN | 精确 tick 节点、damage type、coefficient/公式语义、来源死亡后的属性读取 | `DEFER` |
| `flood` | 官方状态目录：`拥有该状态的武将行动时将受到伤害`，支持行动时语义 | 需要周期伤害参数，但当前资料未冻结 coefficient 来源 | 同上 | UNKNOWN | UNKNOWN | 伤害类型 UNKNOWN；基础公式/系数语义 UNKNOWN | 精确行动节点、damage type、coefficient/公式语义 | `DEFER` |
| `poison` | 官方状态目录：`拥有该状态的武将行动时将受到伤害` | 需要周期伤害参数，但当前资料未冻结 coefficient 来源 | 同上 | UNKNOWN | UNKNOWN | 伤害类型 UNKNOWN；基础公式/系数语义 UNKNOWN | 精确行动节点、damage type、coefficient/公式语义 | `DEFER` |
| `rout` | 官方状态目录：`拥有该状态的武将行动时将受到伤害` | 需要周期伤害参数，但当前资料未冻结 coefficient 来源 | 同上 | UNKNOWN | UNKNOWN | 伤害类型 UNKNOWN；基础公式/系数语义 UNKNOWN | 精确行动节点、damage type、coefficient/公式语义 | `DEFER` |
| `sandstorm` | 官方状态目录：`拥有该状态的武将行动时将受到伤害` | 需要周期伤害参数，但当前资料未冻结 coefficient 来源 | 同上 | UNKNOWN | UNKNOWN | 伤害类型 UNKNOWN；基础公式/系数语义 UNKNOWN | 精确行动节点、damage type、coefficient/公式语义 | `DEFER` |
| `recuperation` | 官方状态目录：`每回合恢复一次兵力`，支持每回合语义，但未证明 Stage 7 精确结算节点 | 需要 `amount`，当前资料没有可冻结的工程来源 | `StateInstance` 可提供完整 provenance | UNKNOWN | UNKNOWN | 非伤害；恢复 amount 来源 UNKNOWN | 精确 tick 节点、恢复 amount 的工程来源 | `DEFER` |
| `rebellion` | 官方状态目录：`每回合...造成伤害` | 周期伤害参数尚不足 | `StateInstance` 可提供 provenance | UNKNOWN | UNKNOWN | 明确含“无视防御”，但当前 Stage 7 没有正式 Damage Modifier / ignore-defense pipeline | 无视防御的正式 pipeline 位置；damage type/coefficient | `DEFER` |
| `first_aid` | 官方状态目录：`受到伤害时恢复兵力` | 恢复公式未冻结 | `StateInstance` 可提供 provenance | UNKNOWN | UNKNOWN | AFTER_DAMAGE reaction 语义；恢复公式 UNKNOWN | reaction queue、精确恢复公式、事件顺序 | `DEFER` |
| `weapon_lifesteal` | 官方状态目录：`造成兵刃伤害时，根据伤害量恢复自身一定兵力` | 恢复比例/amount 语义未冻结 | `StateInstance` 可提供 provenance | UNKNOWN | UNKNOWN | 依赖伤害后恢复；requested vs actual damage UNKNOWN | AFTER_DAMAGE queue、恢复基数、比例语义 | `DEFER` |
| `strategy_lifesteal` | 官方状态目录：`造成谋略伤害时，根据伤害量恢复自身一定兵力` | 恢复比例/amount 语义未冻结 | `StateInstance` 可提供 provenance | UNKNOWN | UNKNOWN | 依赖伤害后恢复；requested vs actual damage UNKNOWN | AFTER_DAMAGE queue、恢复基数、比例语义 | `DEFER` |
| `healing_ban` | 官方状态目录：`无法恢复兵力`；Stage 7 规划明确将其放在 RecoverySystem policy | 无额外 runtime params | 阻止原因来自目标现存 `healing_ban`；恢复请求自身 provenance 独立保留 | 本阶段无需解决 | 本阶段无需解决 | 非伤害；policy 明确为恢复结算阻止 | 完整跨 reaction 交互留待后续阶段，但不影响 Stage 7 单次 RecoveryRequest 裁决 | `PASS_STAGE7` |

## Stage 7 production mapping 结论

本阶段允许实际接入的官方状态：

```text
healing_ban
```

本阶段禁止加入 production Trigger mapping：

```text
burn
flood
poison
rout
sandstorm
recuperation
rebellion
first_aid
weapon_lifesteal
strategy_lifesteal
```

因此 Stage 7 的 RuleHook / Trigger / Recovery 基础设施测试使用 synthetic `StateDefinition` / `StateInstance`。Synthetic 状态只证明强类型 hook、确定性 ordering、Effect 路由和 provenance 能工作，不宣称任何官方周期状态已经实现。

## Evidence sources

仓库内证据来源：

```text
STAGE7.md
PROJECT_STATUS.md
stages/stage6/STAGE6_FINAL_AUDIT.md
sgs_v2/battle_core/official_state_catalog.py
research/official_state_catalog_v1/OFFICIAL_STATE_CATALOG_V1.md
research/state_catalog_v1/STATE_CATALOG_V1.md
```
