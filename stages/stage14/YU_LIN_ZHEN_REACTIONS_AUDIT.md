# 鱼鳞阵基础值受击分支审计

2026-10-14；Runtime基线 `6b97b86aab597c73978b11c9118b7b227e09d654`；
Research主线合同 `d9d20e16c85355d7349bbb6df2b1b148d44292a4`。
审计采用代码审阅、不同fixture的行为测试、真实伤害/普攻及完整引擎验证、冻结owner哈希核对；
不声称第二位人工或独立代理审阅。

结论：本次用户批准的基础值范围可进入PR/CI合并门禁。
属性缩放与鱼鳞专项微时序仍未冻结；详见[接入记录](YU_LIN_ZHEN_REACTIONS.md)。

## 审阅发现和处理

- 新端口组合在既有aftermath之后；不替换伤害/恢复owner，不使用EventBus决定玩法。
- driver仅存声明参数，来源携带者、目标角色、槽位与driver generation明确分离。
  去重键含state instance/generation/damage instance，失败与重复抵御施加也不重复抽概率。
- 共享资格门控排除未命中、死亡、失效、非法来源及结束；保留零损失命中。
  满兵/禁疗仍按正式机会抽概率，然后由恢复owner处理结果。
- 抵御grant只在伤害结算后发生；因此不会倒过来挡住生成它的当前伤害。
  消费旧抵御后再获新抵御、第三回合获抵御跨第四回合保留均有真实DamageEffect验证。
- 已有抵御的新施加拒绝不覆盖/刷新；正式状态消费和冲突owner保持原实现。
- 治疗来源读取携带者反应时兵力，属性项0；红度及受治疗修饰仍通过既有公式/恢复owner，
  验证受治疗+20%只应用一次；禁疗、伤兵和当前缺口上限未绕过。
- 三个来源位置/三个槽位、双方阵法隔离和generation/战斗隔离有验证。
- 第一轮全量发现无driver时新端口增加一次共享资格查询；已修正为只在存在有效driver时查询。
  原Stage10“单一资格查询”回归和完整全量重新通过；未修改旧测试来绕开其断言。
- 仅新增通用after_damage_support组件、战法效果树和BattleSystems两行依赖组合。
  冻结伤害、扣兵、恢复、状态生命周期、execution-right、finalization owner哈希全部不变。

## 验证记录

- 专项/先登/阵法组合/Stage10受击管线：314 passed。
- 全量：2900 passed。
- Stage13-D1独立运行时和冻结owner审计：PASS。
- 青州兵、雁行阵独立运行时审计：PASS。
- demo及清洁进程canonical registry：PASS，9阵法。
- 四个确定性种子完整8回合引擎：PASS，窗口/目标/来源核验通过。
- git diff --check：PASS。

全部结果保存在 `yu_lin_reaction_evidence`。客户端实证不由工程测试替代。
没有鱼鳞专项合同的持续时限、反应微顺序及普通抵御来源死亡与阵法清理政策的区别，
均在接入记录显式标注；不将通用急救合同升级为鱼鳞专属实证。
最新PR head CI成功后方可合并，merged-main CI也需成功；实际SHA/CI状态以GitHub记录为准。
