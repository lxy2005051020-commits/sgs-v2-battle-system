# 飞熊军：已知治疗部分接入

日期：2026-10-12。基线：远端 main `60ad790c83211c6e1597e63278eb85e79bc6a0b8`。

状态：**KNOWN_RECOVERY_SLICE / FULL_BATTLE_BLOCKED / NOT_GAMEPLAY_FROZEN**。
用户本次明确选择“先接入已明确部分，公式缺失时明确报错”。本分支不使用固定64%伤害替代累计治疗缩放，不生成不完整的全场战斗结果。

## 来源及证据边界

- [官方公告中的飞熊军评测（2023-11-30）](https://bbs.4399.cn/thread-view-tid-42385703)：说明全队16%治疗提升、治疗积累及两目标输出；没有可直接复现的精确缩放公式。
- [公开战法描述页](https://sanzhan.slgsim.com/zh-hans/tactics/)：满级16%，董卓统领20%，主将行动时60%概率攻击敌军2人，基础伤害率64%，触发后重置累计进度。该页为外部汇编，非客户端原始资源，不升级为实证冻结。
- 本地 Research `states/persistent/first_aid/ROUND3_RECOVERY_MODIFIER_TIMING_AUDIT.md` 与 `states/persistent/recuperation/RECOVERY_MODIFIER_DATA_GAP.md` 将飞熊军标为20247及目标端治疗增益；旧表中8%与公开满级16%不一致。本次只声明公开满级参数，不能将8%强制解释为已核实的等级数据。编号20247仍待客户端原始身份核对。

尚未读取并验证5份飞熊军原始战报。工程测试不构成真实游戏公式、时点或生命周期证明。

## 实现及组件树

```text
TroopSkillConfig(20247, CAVALRY -> FEI_XIONG_JUN)
  definition_factory -> SKILL（已知治疗规格）
  definition_resolver -> FeiXiongJunFormulaMissingError（开场预检，无状态/身份写入）

隔离验证专用 resolve_recovery_definition
  -> SkillDefinition(TROOP, FIXED_ALL_TEAM, activation=1.0)
  -> ApplyStateSkillEffectSpec(runtime_received_recovery_bonus)
     -> ReceivedRecoveryBonusParams(16/100 或董卓主将20/100)
     -> ReceivedRecoveryModifierProvider
     -> RecoverySystem(second CEIL / prevention / TroopSystem capacity)
```

持有者与主将判定分离：董卓为副将且仅持有战法，不享受主将20%参数。增益作用于治疗接收目标，不是治疗提供者。纯治疗验证复用公共 SkillResolver/EffectExecutor 和 Provider 依赖，不通过正式兵种准入，也不代表整场飞熊军可运行。

新增通用 `received_recovery_modifier.py`，仅提供类型化目标治疗增量与既有最终 Recovery Modifier ratio 的加法组合。取整、禁疗、目标死亡、伤兵容量均留在原 owner。装备增量独立检查 EquipmentEffectivenessPolicy；装备贡献失效时不抹除状态增量。没有此状态时原样返回原 provider 的贡献，保留原有装备门控。

`state_modifiers.py` 增加内部状态 schema 与既有防重复规则；`battle_systems.py` 只组合既有 RecoveryModifierProvider 接口。没有改动 BattleEngine、RecoverySystem、伤害公式、PendingWork 或冻结状态 owner。项目实际使用显式 `TROOP_SKILL_REGISTRY`，没有 `register_skill`/模块自动发现 API；沿用实际注册路径，未另建平行注册表。

已经施加的持久增量遵循既有 StateEffectivenessPolicy，不把修改 SkillRuntime.enabled 自动解释为状态删除。正式提供者死亡、威慑等飞熊军独有玩法仍 OPEN；当前正式准入被缺失公式拦截，不能拿隔离预览推断生命周期。

## 未实现边界

- 累计治疗量到伤害率的精确公式、上限、取整。
- 累计口径：理论治疗、修饰后治疗或实际恢复；溢出、禁疗、吸血、队外来源是否纳入。
- 主将行动时触发的精确相对顺序及触发权；累计快照与成功触发后重置时点。
- 同一触发两目标是否共享一次累计快照；伤害期间派生治疗属于本次还是下一次累计。
- 死亡、威慑、目标不足2人、战斗提前结束等边界。

60%/2人/64%仅为声明常量，未被接入真实触发路径。正式准入会在 PRE_BATTLE 动态预检期间明确报错，尚未进行兵种转换、状态施加或伤害结算。基础骑兵限定、队伍一致性、槽位、禁用等检查先由既有准入 owner 完成。

## 验证

专项测试：`tests/test_stage14_troop_fei_xiong_jun.py`。
可重放验证：`scripts/verify_fei_xiong_jun.py --output stages/stage14/feixiong_evidence/verification.json`。
其中100基础治疗对应116/120实际恢复，整场入口报错且兵力/身份不变。

专项回归、全套回归、Stage13-D1冻结 owner 检查、标准 demo、清洁进程注册核查结果存于 `feixiong_evidence/`。本文件和分支状态不表示已合入 main。

本地验证结果：专项 **29 passed**；全套 **2170 passed**；Stage13-D1 **PASS**（冻结 owner 哈希一致，11项独立对抗检查通过）；标准 demo **PASS**；清洁进程注册核查 **PASS**（20247为该模块CONFIG，factory与SKILL一致，14项注册包含本候选，不等于14个完整可用兵种）；`git diff --check` **PASS**。
