# 武锋阵接入记录

状态：`IMPLEMENTED_USER_SPECIFIED_MODEL / NOT_GAMEPLAY_FROZEN`，2026-10-13。
工作树 `D:\模拟系统\stage14-wu-feng-zhen`，分支 `stage14/wu-feng-zhen`。
基线为本次实时核对的 origin/main `74817c59325bcaf7fafd5fc67f40621174ec9d65`。

## 原文和确认规则

ID `22031`，类型 `FORMATION`，静态 `arm_limit={}`，沿用五种基础兵种准入。
满级原文：

> 我军三名武将兵种适性均不相同时，战斗前5回合，我军主将有80%几率优先成为敌军战法的目标，且使该战法对其造成的伤害降低30%（受主将统率影响）；战斗中，奇数回合使兵种适性较低的副将恢复我军单体兵力（治疗率184%）；偶数回合使兵种适性较高的副将造成伤害提高15%（可叠加）

[十级静态原文](wu_feng_evidence/static_levels.csv)、
[来源配置与SHA256](wu_feng_evidence/source_manifest.json)。
副将治疗/增伤数值逐级读取，不插值。

用户确认：

- 奇偶回合效果在**阵法携带者行动时**触发。
- 满级主将减伤 `rate = 0.30 + 0.001 * (实时统率 - 100)`。
  统率由 `AttributeSystem.get_defense`在每次正式伤害规则收集时读取；包含有效属性修饰。
  100/200/350统率对应30%/40%/55%，不读取携带副将的统率。
- 治疗由低适性副将执行，目标为**另外两名存活队友中随机一名，排除治疗副将自己**。
  默认完整runtime采用这条规则，拒绝武锋阵的最低兵力模型。

## 完整行为

战前要求完整存活三人、同一当前兵种及明确的 `troop_aptitude="S"/"A"/"B"/"C"`。
大小为S>A>B>C，不从姓名或面板属性推断。三人适性重复时合法装备但不安装效果；
适性未知时拒绝安装。角色在入场时确定。

主将概率优先状态前5回合有效，第6回合ROUND_START沿正式生命周期清除。
符合敌对新战法目标查询且主将为合法候选时，公共selector adapter执行一次80%判定；
成功使主将成为单体目标或进入Choose-N集合，余下目标仍由原selector选择。
Fixed-All保持全部目标并允许本次概率分支，不缩成主将单体。
已经占满目标数量的其他正式必选约束优先；目标排除和混乱仲裁保持原Owner。
没有合法主将候选、友方/自身操作、继承/派生既有目标均不新增优先概率判定。

成功判定产生不可变receipt，包含目标查询ID、敌方战法/槽位、主将、状态实例和代次、
回合与当前BattleContext作用域。该查询构造的主将直接伤害Effect携带receipt；
其他目标不携带。多段直接伤害共享一次判定，各段实时读取主将统率。
正式请求只有receipt匹配且原优先状态仍有效时才加入相应减伤。
未命中80%、普通攻击、没有该查询凭据的另一战法、持续伤害、其他目标、跨回合或
跨BattleContext请求均不获得这项减伤。移除状态、关闭runtime、携带者阵亡后失效。
这条路径不把主将增益伪装成常驻全伤害减免，也不修改基础伤害公式。

携带者行动时，普通行动前状态批次结算后执行副将支援，每回合去重：
奇数回合低适性副将执行治疗；偶数回合高适性副将增伤。
奇偶效果在第6回合以后继续。满级成功触发第2/4/6/8回合后累积15/30/45/60%。
同驱动旧增伤由RemoveStateEffect清除，再安装累计贡献；其他来源不受影响。
正式DamageModifierSystem负责同侧伤害池运算。

## 工程模型与实证边界

本次完成的是可运行、可检查的用户指定模型，不代表武锋阵完整客户端实证冻结。

- 概率判定置于纯SkillTargetPolicy之后、实际selector之前，成功查询每次仅消耗一次80%概率。
  该具体隐藏RNG时序、Fixed-All的概率减伤分支、与其他必选效果的优先关系是工程模型。
  [Provocation研究合同](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/states/control/provocation/MECHANISM_CONTRACT.md)
  提供群体目标不坍缩、继承目标不重选和减伤独立于挑拨状态的边界；本实现没有改写690108。
- 治疗使用触发时低适性副将兵力，属性项0，每进阶星2%的独立治疗系数。
  TreatmentFormulaSystem计算名义量，RecoverEffect交给正式恢复修饰、禁疗、伤兵容量和兵力Owner。
  具体读点和缩放仍为候选模型。
- 原文明示可叠加；这里按加算、持续至战斗结束实现。副将阵亡跳过其分支，不重新分配角色。
  这些细节保留为工程模型，未声称获得专门的五份原始战报逐事件冻结。
- 用户提供的是Lv10统率公式，未推导其他等级的统率斜率。完整模式支持Lv10，
  1–9级完整模式明确拒绝；其副将部分可显式 `deputies_only=True`运行，并在元数据标明缺失主将段。
- 公式算出减伤率不在[0,1]时明确拒绝，不自行发明封顶规则；如统率801得到100.1%。
- 现有基础ActionSystem默认处理普通攻击。真实主动战法调用者和已接入的新目标查询生产者
  经统一SkillResolver自动获得优先机制；未新增全游戏主动战法自动行动调度器。
  引擎专项通过显式技能行动port调用正式resolver/executor验证完整流程，保留默认Owner。

## 组件树及改动

```text
FORMATION_SKILL_REGISTRY[22031] / PRE_BATTLE / 100% / 无准备
  wu_feng_zhen.py: install_wu_feng_zhen
    适性条件与唯一编队 → EffectExecutor → StateLifecycleSystem → ProviderNode
    ApplyStateEffect(runtime_probabilistic_target_priority, 主将, 到期第6回合)
    ApplyStateEffect(runtime_periodic_team_support, 携带者)
SkillTargetPolicy(纯约束、无RNG)
  TargetPrioritySkillResolver(公共selector扩展)
    原候选/必选/排除 → 80%判定 → 原SkillResolver保持目标数量
    QueryBoundDamageEffect / TargetPriorityReceipt → QueryBoundDamageRequest
      QueryBoundReductionProvider → 实时AttributeSystem → 正式DamageModifierSystem
UnitActionStartHook(携带者) / 每回合一次
  PeriodicTeamSupportRuleHookSystem → 原普通状态批次 → PeriodicTeamSupport
    奇数：TargetOperationProducer → SkillTargetPolicy → TargetSystem(排除治疗者)
      TreatmentFormulaSystem → RecoverEffect → RecoverySystem → TroopSystem
    偶数：RemoveStateEffect(本驱动旧增伤) → ApplyStateEffect(累计DamageRateParams)
DamageRateModifierProvider → 正式DamageModifierSystem → 原DamageSystem
```

新增 `probabilistic_target_priority.py`、`periodic_team_support.py`及战法 `wu_feng_zhen.py`；
复用三势阵工作树的通用 `damage_rate_modifier.py`（当时尚未合入main）。
组合根 `battle_systems.py`接入；`formation_admission.py`唯一canonical注册；
`__init__.py`导出工厂；`unit.py`新增可选当前兵种适性和快照。
没有修改冻结SkillResolver、SkillTargetPolicy、DamageSystem、RecoverySystem、TroopSystem、
EffectExecutor、RuleHookSystem、TriggerSystem、BattleEngine或生命周期Owner。
ARCH-11审计改为AST识别实际构造调用，排除类声明误报，明确审计保留source_ref的通用Effect包装。

## 使用与证据

```python
from sgs_v2.battle_core import create_wu_feng_zhen_runtime

# 三名友军都明确填写当前兵种的troop_aptitude，并确保互不相同。
context.skill_runtimes.register(create_wu_feng_zhen_runtime("carrier_id"))
# 正式BattleEngine.run()战前安装；统一SkillResolver处理战法的新选人。
```

观察记录：`context.metadata['wu_feng_admissions']`、
`['target_priority_history']`、`['periodic_team_support_history']`。
治疗事件actor为低适性副将，阵法来源槽位沿驱动状态追溯。

[专项测试](wu_feng_evidence/focused_tests.txt)、
[全量回归](wu_feng_evidence/full_regression.txt)、
[Stage13-D1冻结审计](wu_feng_evidence/stage13_d1_audit.json)、
[青州兵兼容审计](wu_feng_evidence/qingzhou_audit.json)。
远端PR和CI状态由发布记录另行报告，本地测试不替代远端CI。

本次本地验证：专项 **62 passed**，全量 **2329 passed**；Stage13-D1冻结Owner哈希一致，
独立对抗审计 **PASS**；青州兵兼容审计 **PASS**；新进程canonical registry导入和
`git diff --check`通过。ARCH-11明确覆盖两个原始生产者及保留source_ref的查询包装。
