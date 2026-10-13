# Stage14 F1 锋矢阵（20066）Gameplay Runtime 接入记录

> 阶段：Stage14 F1（阵法 Gameplay 第一项）  
> 战法：锋矢阵 / `SkillType.FORMATION` / Canonical ID `20066`  
> 合同来源：Research main [Feng Shi Zhen Research Contract](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/01_Skills/FENG_SHI_ZHEN_RESEARCH_CONTRACT.md) 和 [F1 Preintegration Handoff](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/F1_FENG_SHI_ZHEN_PREINTEGRATION_READINESS.md)。  
> 接入分支：`stage14-f1-feng-shi-zhen`，Battle PR #68 已合并；当前状态以第 6 节 mainline freeze 验收为准。  
> 用户 V1 实现规则：四阶段 `PASSIVE → FORMATION → TROOP → COMMAND`；来源携带者阵亡效果立即失效；同队最多一个阵法；同速跨队进攻方优先。

## 1. 满级数值（Lv10）

| 单位 | OUTGOING | INCOMING |
|---|---:|---:|
| 主将 | **+30%** | **+20%** |
| 副将 1 | -15% | -25% |
| 副将 2 | -15% | -25% |

以上分别适用于兵刃 `DamageType.WEAPON`、谋略 `DamageType.STRATEGY`，普通攻击与技能伤害均适用。受伤 `+20%` 是主将**承伤增加**，不可写成 -20%。客户端 26.70% / -22.20% 的实战观测只与 Lv8 线性拟合，非等级字段直接实测；本版本明确采用 Lv10 固定标准值，**尚未实现 1~9 级等级模型**。

骑兵／盾兵／枪兵可用，弓兵／器械禁止。阵容仅有 1 或 2 名武将时只给存在的合法席位挂载效果，不创造缺失副将。

## 2. Runtime 实现所有权

- `feng_shi_zhen.py`：提供 `create_feng_shi_zhen_definition()`、`install_feng_shi_zhen()`、`FengShiZhenDamageRuleProvider` 和强类型状态参数。
- `formation_admission.py`：只注册正式 F1 `20066`，保留 F0 的单队单阵法、槽位、兵种和失败零副作用前置检查。新加的 `FormationSkillConfig.installer` 用于合法的角色定向接入；无该字段的旧阵法仍由现有 Resolver 执行。
- `battle_systems.py`：在原 `IncomingDamageReductionProvider` 后组合包装标准 `DamageRuleProvider.collect`，不新建伤害求值器、不改变冻结的 `DamageModifierSystem.resolve_phases`。
- `StateLifecycleSystem.apply()`：每位存在的武将挂载 **一个**自带 `source_id + source_skill_id + source_skill_slot` 的持续状态，角色参数区分主副将。12 条客户端微日志不要求等同 12 个物理 Runtime 对象。
- `DependencyEvaluationSupport`：每个阵法状态节点绑定 `ProviderNode(SkillProviderRef)`；F0 原有 `DefeatCleanupPort.commit_defeat` 按 SkillRuntime 来源清理，对方或其他战法修饰保持独立。
- OUTGOING 与 INCOMING 是不同乘算层；**同一层内**的 INCREASE/REDUCTION 按 Stage13 代数和叠加，底层最小系数与防护、精确伤害求值仍由 Stage13 唯一 Owner 执行。
- 无需且不得更改 Stage13-D1 冻结文件或哈希清单。

## 3. 已验证范围

`tests/test_stage14_feng_shi_zhen.py` 专项覆盖：

- 官方 ID 和骑/盾/枪准入；弓/器械硬拒绝；非法配置在准备阶段全局预检时失败，零效果。
- 携带者处于主将/副将 1/副将 2 时，全队均按目标真实席位套用不同数值，来源含 SkillSlot。
- 两种伤害类型 × 普攻/技能来源；四方向 (主将 OUT +30 / IN +20、副将 OUT -15 / IN -25) 的标准 `DamageModifierSystem.resolve_phases()` 数值断言。
- 双军各一阵法：OUT 1.30 × IN 1.20 = 1.56，跨层乘算；同一 OUT 层 +30% 与 -33.44% 相加为 -3.44%。
- 携带者阵亡后下一次伤害不再使用锋矢贡献，跨目标来源状态消失，另一阵法不受影响，SkillRuntime 保留、重复清理安全。
- 单次安装与重复安装防护；1~3 人标准编队；真实 `BattleEngine.run()` PRE_BATTLE StateApplied 事件。
- 真实 `BattleSystems.damage_system.calculate()` 完整伤害流水线追踪，并对比来源阵亡前后修饰是否存在。

## 4. 本阶段明确未完成

- 锋矢阵战法等级 1~9 的动态数值、精确插值及显示舍入（Research 当前未直接提供等级字段证据）。
- 任何其他具体阵法的 Gameplay；象兵仍为 `DEFERRED`。
- 用户 V1 实现规则不能反向当作客户端全局时序或携带者阵亡机制已被实证的证明。

## 5. Freeze / Release Gate（接入前门禁，历史记录）

Battle PR #68 必须全量 pytest、Stage13-D1 独立冻结审计、青州兵独立审计、Demo、PR CI 通过；实际发布以 merged-main CI 再次通过为准。合并与通过之前只允许标记为 `IMPLEMENTED_CANDIDATE`，不能宣称 `MAINLINE_FROZEN`。

## 6. 正式 Mainline Freeze 结果（2026-10-13）

- Battle PR [#68](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/68) **MERGED**：`975b44e67f7d1bfbb6a46fd12be6895e3c8a7cb4`。
- [F1 merged-main Actions #38280765590](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38280765590) **SUCCESS**：`2267/2267` tests PASS、Demo PASS、Stage13-D1 frozen owner PASS（11 adversarial）、Qingzhou independent audit PASS。
- `F1_LV10_RUNTIME_MAINLINE=FROZEN_TO_USER_APPROVED_V1_CONTRACT`; `F1_GAMEPLAY_CLIENT_TRUTH=BOUNDED_CONFIRMED_WITH_OPEN_BOUNDARIES`。不要将本版本的用户规则或等级插值缺失伪装为全客户端实证。
- 该记录仅说明锋矢阵满级标准数值与来源生命周期已经实现，其他阵法、Lv1~9 等均不包括在此冻结范围。
