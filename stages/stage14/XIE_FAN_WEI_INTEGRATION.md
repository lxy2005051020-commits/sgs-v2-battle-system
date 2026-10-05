# 解烦卫 20248 接入

日期：2026-10-06。状态：`REMOTE_AUDIT_PASS / RESEARCH_GATE_PASS / PR_READY`。Runtime baseline `20e63d6`；Research authority 已更新至 `f4aea546537447067d29275e87da5bdcc8f65de8`。
分支 `stage14-xie-fan-wei`。按项目所有者要求同步至 GitHub，供审阅；不代表 Research 冻结或已合并主线。

## 描述与授权

满级参考描述来源：<https://junshipt.cn/t/jiefanwei.html>。
该来源为第三方战法目录，不标记为当前客户端原始证据。
本地 Research 治疗目录 `skill_catalog/fb1_base_lookup_pure_skill_catalog_v1.csv`
提供 ID 20248、治疗率 72%、武力/智力较高项；目录没有完整的触发合同。

Research authority：`MC-STAGE14-XIEFAN-01`。Catalog 中旧的 `30%→60%` 已修正为固定 `30%` 伤害分支概率；未抽中则进入治疗。

项目所有者本次明确：受武力和智力较高项影响的伤害，在武力更高时走兵刃、
智力更高时走谋略；治疗同样选较高属性。本实现把它做成通用选择组件，
不把所有“受属性影响”字样无条件改为伤害类型切换。

2026-10-06 项目所有者追加确认：保留 421 示例所用的两次 CEIL 计算；
归类为兵种战法且允许看破；武智相等选择武力；最快者战前固定，
速度相等按主将、第一副将、第二副将；伤害类型比较读取实时属性；
治疗来源暂设为实际普攻者；速度附加位置按当前实现；
普攻规避、抵御或零伤害仍触发；“未生效”仅指 30% 概率未抽中；
位于普攻相关后续结算之后的既有入口。
随后项目所有者明确：治疗使用当前属性；兵力读取时间本轮没有更改。

## 最终组件树

```text
TROOP / PRE_BATTLE / activation=1 / 无准备回合
  FIXED_ALL_TEAM
    ATTRIBUTE_BONUS(speed, +36)
    NORMAL_ATTACK_FOLLOWUP(BranchedNormalAttackFollowupParams)
      provider 与来源存活门控
      FastestTargetSystem: 战前固定最快者；并列按主将 -> 副将1 -> 副将2
      普通攻击后，单次 chance(.30)
        success -> 随机敌军单体
          普通 coefficient=.36；韩当为队伍主将时 coefficient=.72
          executor.force > executor.intelligence -> WEAPON(coefficient)
          executor.intelligence > executor.force -> STRATEGY(.36)
          executor.force == executor.intelligence -> WEAPON(.36)
          additive_damage = executor.final_speed * .40
          stage11_family = COMMAND_XIEFANWEI（兵种伤害 / 支持看破）
        failure -> 随机我军单体（包括自身与满兵成员）
          RecoverySkillEffectSpec
          nominal = CEIL(.72 * (F(executor.opening_troops) + max(executor.current_final_force, executor.current_final_intelligence)))
          modified = CEIL(nominal * RecoverySystem 的治疗修正)
          RecoverEffect / RecoverySystem: 修正、禁疗、伤兵容量
```

速度加成是状态修正，不改单位原始 speed。追加伤害由实际普攻者提供伤害属性、
当前兵力、速度与伤害归属；治疗采用实际普攻者来源、其 PRE_BATTLE 兵力与触发时最终武力／智力较高值。
携带者仍是战法 Provider，不因治疗来源改变而替换注册槽或依赖边。
固定最快者阵亡后不重新选人；仍由来源携带者的有效性与存活门控限制触发。

## 组件复用与扩展

复用 TroopSkillConfig / TROOP_SKILL_REGISTRY、技能解析与目标策略、
NormalAttackFollowupPort 的真实 permit 门控、状态依赖与有效性、
TreatmentFormulaSystem、EffectExecutor、RecoverySystem 以及完整伤害流水线。
该仓库不含技能自动扫描或 register_skill 接口，使用现有明确配置注册路径。

新增 `attribute_choice.py`：较高属性与伤害类型选择；
新增 `additive_damage.py`：AdditiveDamageRequest / AdditiveDamageSystem；
扩展现有 followup 参数表达速度条件与互斥恢复分支；
扩展 PriorityTargetSystem 的最高速度查询；
增加通用 RecoverySkillEffectSpec 与 RecoverEffect 修正策略输入。
新兵种模块只声明效果、实时属性读取策略及来源兵力快照。

AdditiveDamageSystem 在冻结计算器的 base × coefficient 接缝提供
base × coefficient + additive_damage，然后完整复用后续暴击、增减伤、
抵御、整数化与结算。内部数值适配只存在于本次 calculate 的 ContextVar 作用域，
结果里的 base_damage 恢复为普通数值；不会二次计算基础伤害或额外消耗 RNG。
普通请求与零附加值委托原路径。非零附加值仅支持 LIVE_RUNTIME。
所有 Stage13-D1 冻结 owner 文件和哈希清单均保持原样。

## 当前确认与剩余边界

- 已实现并测试用户指定的较高属性选择规则。
- 武力与智力相等时，治疗取共同数值；伤害选择兵刃。已确认。
- 最快者战前固定，并列按阵容位置决定；战中速度变化不更换触发者。已确认。
- 追加伤害的类型使用执行时较高属性；速度附加值使用执行时最终速度。
- 速度附加值目前放在 36% 基础伤害之后、下游暴击与增减伤之前；
  项目所有者已确认按此实现，尚无本次原始战报量化验证。
- 普攻规避、抵御或零伤害仍抽取分支；抽中伤害后被阻止不回退治疗。已确认。
- 普攻后时序复用既有 seam（现有群攻、连锁与反击结算之后，每次物理普攻均可进入）；
  位置已获项目所有者确认，细分多个普攻后效果之间的顺序仍未专项验证。
- 治疗两次取整已由项目所有者确认，421 示例作为回归用例；不再标记为待修复偏差。
- 治疗属性使用实际普攻者触发时的最终武力／智力较高值，包括当前属性状态修正；
  治疗兵力仍使用 PRE_BATTLE 快照。属性读取时间已由项目所有者确认，未新增治疗修正战前采集机制。
- 父普攻编号 / 根行动编号关联仍为空。第 3 项本轮只解释，没有修改冻结 coordinator 或以日志猜测关联。
- 独立 Runtime 审计已完成并 PASS，见 `XIE_FAN_WEI_RUNTIME_AUDIT.md`；Research contract、Catalog 概率冲突、韩当统领范围与 additive seam 均已关闭。
- 此分支同步至 GitHub 供审阅；不修改 Research 合同、不声明正式冻结，主线接入仍未完成。

## 验证

专项测试包括战前安装与注册、两类伤害、速度附加仅一次、实时伤害属性、
战前固定触发者、三种阵容优先级、实际普攻者实时治疗属性、战前兵力快照与归属、随机单体、
来源失效与阵亡、威慑、缴械、结束门控、禁疗与伤兵容量、两次取整 421、
看破兵种分类、规避／抵御／零伤害触发、附加输入验证与作用域隔离。
本轮专项：35 passed；全量：2112 passed（13.89s）。
Stage13-D1 与青州兵独立审计均 PASS；Registry 干净进程检查 PASS。
结果见下列验证证据。
干净进程中 Registry ID 20248 精确解析到声明 SKILL，无重复注册异常。
验证证据保存于工作目录之外：

- `D:/模拟系统/output/xie_fan_wei_pytest.txt`
- `D:/模拟系统/output/xie_fan_wei_demo.txt`
- `D:/模拟系统/output/xie_fan_wei_stage13_d1_audit.json`
- `D:/模拟系统/output/xie_fan_wei_qingzhou_audit.json`

此前尝试直接增加冻结 owner 字段被审计正确检出；最终方案恢复 owner，
以扩展组件提供能力，未放宽审计或更改预期哈希。

独立 Runtime 审计见 `XIE_FAN_WEI_RUNTIME_AUDIT.md`；Additive Damage 架构合同见 `XIE_FAN_ADDITIVE_DAMAGE_SEAM.md`。
韩当 COMMANDER 72% 分支已实现并有副将反例测试。当前父普攻 / root action lineage 继续 OPEN，不阻塞本轮 mainline。
