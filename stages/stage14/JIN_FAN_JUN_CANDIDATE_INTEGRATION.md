# 锦帆军候选接入（20152）

日期：2026-10-05。状态：**CANDIDATE / RESEARCH FORMULAS OPEN / PRODUCTION ADMISSION CLOSED**。

Runtime 基线：`d88e7cd`（最新远端 main）；Research 基线：`5102703`。
独立分支：`stage14-jin-fan-jun`。未改变既有八个兵种的主线冻结状态。

## 文本与版本

以[官方 2026-04-29 更新公告](https://community.lingxigames.com/m/s1/strategy_detail/16363)为当前文本来源。
满级基础触发概率45%，溃逃标称伤害率64%（受武力影响），持续两回合；
已有溃逃时追加110%兵刃伤害，并恢复该伤害量的30%。甘宁统领新增最高属性影响触发概率，友军会心为6%。

Research Catalog 的3%会心来自等级/版本混用，不作为满级实现依据。
官方文本未给出两项缩放公式。用户本轮明确确认两项公式均尚未确认。
不得把64%当作完整武力缩放公式，也不得将甘宁分支退化为固定45%。

## 组件映射

```text
TroopSkillConfig / TROOP_SKILL_REGISTRY（现有注册入口，无 autodiscovery API）
  PRE_BATTLE -> BOW / JIN_FAN_JUN identity
  FIXED_ALL_TEAM -> ApplyStateSkillEffectSpec(runtime_normal_attack_followup)
    NormalAttackFollowupParams(probability=.45, INHERIT_ACTUAL_TARGET)
      TargetStateBranchFollowup(state_id=rout, duration=2)
        target has effective rout -> DamageSkillEffectSpec(WEAPON, 1.10)
          -> RecoverySystem(30% of this followup's actual primary target loss, CEIL)
        otherwise -> ContinuousDamageBasisProducer
          -> StateLifecycleSystem.calculate_lifecycle_window
          -> ApplyStateEffect(rout, frozen formula facts)
```

复用普攻命中 permit、SkillResolver 准入/概率、实际目标继承、DamageInstanceCoordinator、
冻结 DOT 来源事实、行动开始机会、禁疗/伤兵容量/治疗修正，以及战斗结束清理。
通用扩展仅增加 `TargetStateBranchFollowup` 与现有 followup port 的组合逻辑。
`BattleSystems` 仅增加现有 owner 的依赖注入。

持有者/槽位保留在全队已安装的 followup 状态上；物理攻击者提供伤害属性并接收恢复。
新溃逃以物理攻击者记录来源，**不伪造该武将持有锦帆军的战法槽位**。
复用现有 DOT `always_active` 持续执行合同；后续若具体战法证据要求不同来源门控，须另行研究。

## 默认准入与未确认边界

`create_jin_fan_jun_runtime()` 可创建候选 runtime，注册入口能查到20152。
正式 `admit_and_install_troop_skill()` 在动态定义解析阶段抛出明确 `NotImplementedError`：
身份转换、状态安装及 runtime 注册均不发生。甘宁主将有单独的双公式缺失说明。
甘宁6%会心尚未安装，须在其概率公式和友军目标范围确认后组合接入。

以下仍为 OPEN，代码/测试不构成玩法证明：

- 溃逃伤害率的武力缩放公式及属性来源、读取时点；
- 甘宁触发概率的最高属性公式、属性来源、读取时点和上下限；
- 甘宁“友军”的精确目标范围；
- 普攻派生效果相对顺序，溃逃存在判定是否读取被抑制的状态；
- 30%恢复采用结算量/实际损失/分担量的哪种基数，以及取整方法；
- 锦帆军来源、既有溃逃来源、DOT来源阵亡/失效的特定交互。

当前通用恢复 adapter 明确使用“本次追加伤害的主目标实际损失 + CEIL”，并经过禁疗和容量 owner。
它是测试中的候选策略，不是已经冻结的锦帆军规则；不能自动套用倒戈/攻心的分担合同。

## 验证方式

`tests/test_stage14_troop_jin_fan_jun.py` 仅在测试内替换注册配置并注入合成系数`.64`，
验证组件接线、两分支、不同攻击者、实际目标、两次行动机会、快照、概率失败、
控制/威慑/停用、副将 provider 阵亡继承、禁疗、真实 Engine 自动安装/最终清理。
测试绕过 Research 准入门只用于验证候选行为，生产入口保留 fail-closed。

```powershell
D:\模拟系统\sgs-v2-battle-system\.venv\Scripts\python.exe -m pytest tests/test_stage14_troop_jin_fan_jun.py tests/test_stage14_troop_batch03.py -q
D:\模拟系统\sgs-v2-battle-system\.venv\Scripts\python.exe -m pytest -q
```

不提交主线合并或发布；公式及具体交互合同确认后，才可解除准入门并进入 Stage14 主线验证流程。

本轮全量回归：**1978 passed**（41.32秒）；锦帆军新增27项候选测试。
尚未进行独立 Runtime 审计、PR CI 或 merged-main CI，因此不标记 MERGED / FROZEN。
