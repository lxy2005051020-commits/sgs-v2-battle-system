# 青州兵（20153）接入

日期：2026-10-05。状态：**IMPLEMENTED / USER_PROVISIONAL_MODEL / CAO_CAO_PLACEHOLDER**。

Runtime起点 `d88e7cd70ff3fd651228435d1e2a5dd623f5e946`。
Research起点 `6e71eb2`，本轮合同经[Research PR #13](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/pull/13)
进入main：`d8cc80ba1d297a701bb7025b47013bfcfdfd1748`。
[MC-STAGE14-QINGZHOU-PROVISIONAL-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/d8cc80ba1d297a701bb7025b47013bfcfdfd1748/Stage14_Troop_Skill_Research/01_Skills/%E9%9D%92%E5%B7%9E%E5%85%B5/QING_ZHOU_BING_PROVISIONAL_CONTRACT.md)。

## 行为与暂定公式

正式 `create_qing_zhou_bing_runtime(owner_id)` 通过兵种注册入口安装：

1. PRE_BATTLE将同队枪兵转为青州兵身份；反击状态的provider仍为持有者的战法槽位。
2. 现有目标选择器随机选同队两名存活武将，包含持有者；安装72%反击，至第3回合开始到期。
3. PendingWork在第3回合ROUND_START执行一次共享治疗；按当前兵力低到高，同兵力按阵容槽位排序。

```text
H_pool = CEIL((B(N) + D/10 + FORCE) × 1.8)
CAO_CAO_COMMANDER_ENHANCEMENT = None
```

用户确认：属性项使用武力；D/10暂定，且加在基础治疗量层；曹操额外统率加成为空白占位。
目前N与武力取持有者PRE_BATTLE最终属性快照；D取安装后前两回合敌军对我军全队造成的实际兵力损失。
这两项来源/统计口径，以及共享名义池、禁疗后不消耗分配、到期来源阵亡取消治疗，均明确标为工程暂定口径。
完整边界见Research合同；不声称机制已实证冻结。

已有兵力函数表原样复用。D/10保存精确分数，不提前截断，不加到最终治疗量层。
曹操分支仍使用基础行为，额外统率加成未实现。

## 组件与owner边界

```text
qing_zhou_bing.py（单战法声明）
  CHOOSE_N_RANDOM_TEAM(2)
    ApplyStateSkillEffectSpec(counterattack, ProviderGatedCounterParams(72%))
      -> existing CounterSystem / DamageInstanceCoordinator
  ScheduledTeamRecoverySpec
    -> PendingWorkSystem timing + provider recheck
    -> project_settled_enemy_team_loss（既成事实，只读，不订阅EventBus发动玩法）
    -> AdditiveTreatmentFormulaSystem（继承公式校验、表和治疗修正拓扑）
    -> PriorityTargetSystem / recoverable_capacity（只读分配）
    -> RecoverySystem / TroopSystem（恢复权限、禁疗、伤兵容量、最终兵力变更）
```

新通用接口位于 `additive_treatment_formula.py`、`scheduled_team_recovery.py`、
`priority_target_system.py`、`recovery_capacity.py`、`provider_gated_counter.py`。
常规治疗零加项路径仍直接交给冻结公式。未修改Engine、EventBus、PendingWork、伤害或恢复owner。
SkillResolver仅添加可含自身的群体目标意图；默认ALLY仍保持排除自身的行为。
未添加新autodiscovery机制；继续使用TroopSkillConfig/TROOP_SKILL_REGISTRY。

## 执行与验证

```powershell
python -m pytest tests/test_stage14_troop_qing_zhou_bing.py -q
python -m pytest -q
python demo.py
python scripts/demo_qingzhou.py --output stages/stage14/qingzhou_evidence/engine_demo.json
python scripts/audit_stage13_d1.py --output stages/stage14/qingzhou_evidence/stage13_d1_audit.json
```

示例记录伤害事件序号、D、D/10、来源兵力/武力、兵力函数值、治疗率、名义池和治疗顺序。
测试中的合成输入用来验证组件接线，不作为真实客户端公式证明。
少于两名存活队员时，按既有Stage12目标不足边界在任何身份/状态变更前明确拒绝。

本地最终验证及GitHub同步状态记录在 `qingzhou_evidence/verification.json`。

本地验证：青州兵针对性 **45 passed**；全量 **1996 passed**；两个demo PASS；
Stage13-D1冻结owner审计PASS；青州兵自动化独立事件链/分数oracle审计PASS。
Runtime同步经[Battle PR #52](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/52)。
GitHub实时合并与CI状态以该PR和精确commit的Actions为准。
