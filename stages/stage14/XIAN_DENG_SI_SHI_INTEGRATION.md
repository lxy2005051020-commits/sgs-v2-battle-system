# 先登死士接入

日期：2026-10-06。状态：MERGED_MAIN / USER_FIT_MODEL / GAMEPLAY_DETAILS_OPEN / CI_PASS。
Runtime 基线：远程 main `a46e513`，独立工作区 `D:/模拟系统/stage14-xian-deng-si-shi`。
Research authority 已通过 PR #15 合入 main（`fe70f349c5952c78dc4c0b8d80aa1d9cf768c54b`）。Battle PR #55 已合并至 main（`cfaf3ffaac3646aff7e7e69713a0b0b3064ef24b`）；merged-main CI `37346440394 / SUCCESS`。独立 Runtime 审计见 `XIAN_DENG_SI_SHI_RUNTIME_AUDIT.md`。

## 依据与授权

Research authority：`MC-STAGE14-XIANDENG-USER-FIT-01`，Research merge `fe70f349c5952c78dc4c0b8d80aa1d9cf768c54b`。
描述来源：`Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_CATALOG.md` 先登死士行。
目录中的 `20246` 是推断编号，本次沿用，不宣称已核实客户端 canonical ID。
该行提供弓兵、全队遇袭免疫、受伤后按兵力比例分支、满级 21 统率或主动发动率 -3 个百分点、
持续 2 回合、常规 4 层/麹义统领 5 层。
当前描述外部交叉参考：[先登死士资料页](https://junshipt.cn/t/xiandengsishi.html)。
这份描述与用户拟合公式不构成真实客户端整数化或事件顺序的冻结证据。

用户在本次聊天明确提供下列公式，并随后选择 **x 使用战斗开始时的统率**。
本次按 PRE_BATTLE 安装时 AttributeSystem 的携带者最终统率捕获一次；状态中保留
`source_attribute_at_application`、`scaling_model_key=XIANDENG_USER_OPENING_COMMAND_FIT_V1`。
之后偷取、削减、增益和治疗均不改变捕获的发动率/单次偷取量。
PRE_BATTLE 内不同来源的安装先后仍可能影响该快照；“所有开局效果完成后再统一快照”未确认。

```text
steal(x) = min(31, ROUND_HALF_UP(21 * (1 + x/1300)))
P(x) = 0.60 + 0.035 * x/100                  x <= 500
     = 0.775 + 0.06 * (x-500)/100            500 < x < 800
     = 0.95                                 x >= 800
```

仅实现推荐比例模型；口算模型 `21+x/65` 不与它混用。
四舍五入是已告知用户的工程口径，未核实客户端 half-tie 规则。
比例模型四舍五入后约在 `x=588.095238...` 达到 31；不能把口头“620~650”另设为门槛。
图片分段式在 800 左侧趋近 95.5%，800 时为 95%，原样保留。
示例：x=0 时 60%/21，x=500 时 77.5%/29，x=600 时 83.5%/31，x=800 时 95%/31。

## 运行时组件与行为

```text
xian_deng_si_shi.py / TroopSkillConfig / TROOP_SKILL_REGISTRY
  FIXED_ALL_TEAM
    ApplyStateSkillEffectSpec(SelectiveStateImmunityParams(ambush))
    ApplyStateSkillEffectSpec(DamageReceivedReactionParams(frozen P, frozen steal))
DamageReceivedReactionPort -> existing DamageAftermathPort
  effective marker + canonical living ProviderNode + deterministic RNG
  post-hit troop ratio comparison, actual physical damage source retained
  lower ratio -> paired BoundedAttributeBonusParams(defense, -Y/+Y)
  equal/higher ratio -> BoundedActivationRateBonusParams(ACTIVE, -0.03)
  StateAdmissionPolicy / StateConflictPolicy -> StateApplicationCoordinator
  StateLifecycleSystem -> independent timed layers, capped at 4/5
```

新增通用模块：`damage_received_reaction.py`、`selective_state_immunity.py`。
扩展现有通用属性/发动率修饰为可限层贡献；保留既有普通修饰的冲突语义。
`DamageAftermathFact` 新增可选 `source_unit_id`：普通伤害从 DamageResult 取得，溅射从现有 lineage 取得；
旧构造兼容，来源缺失时不猜攻击者。EventBus 只记录既有状态应用/到期事实，不驱动玩法。
战法模块只声明参数。注册沿用真实兵种 registry，没有引入仓库不存在的 register_skill/autodiscovery。

遇袭：标准 StateCandidate 准入拒绝；旧 lifecycle 入口可能保留物理实例，效果读取时抑制。
免疫没有附带洞察或其它控制免疫。携带者禁用、死亡、威慑抑制时不新触发。
成功伤害事件编号在各持有者 marker 内记录；重复投递不重复抽样/叠层。
偷取两端在写入前共同预检，不因一端满层而只提交另一端。
不直接修改基础属性、兵力、伤害公式、正常攻击选择、PendingWork 或 Engine。

## 尚未经过战报冻结的工程口径

- 仅正实际损兵、目标和攻击者均存活且敌对时触发；规避、零损兵、死亡目标不抽样。
- 受伤比例使用结算后的兵力 / max_troops，先判定分支，再交回现有急救处理。
- 2 回合按 round_calendar 实现：r 回合施加，r+2 ROUND_START 到期；每层独立到期，不整体刷新。
- 满层时不替换最早层、不刷新旧层。层数按同一携带者/槽位、目标、属性维度和分支组计数。
  偷取的敌方削减端与我方增加端各自限层，任一端无容量就不提交该次偷取。
- 不同受伤武将对同一个攻击者的削减贡献共用目标端层数；偷取与主动概率分支分别限层。
  与其它技能的修饰仍独立相加。真实跨武将/跨分支层数规则尚未确认。
- DOT、反击、突击、溅射使用现有损兵后的 aftermath；分享、分摊、连环真反馈等直接损兵
  没有新造额外受伤入口，暂不声称支持其触发语义。
- 与急救、吸血、其它受伤效果的更细顺序、死亡来源持续伤害、携带者死亡后的已提交层行为未冻结。
- 麹义/麴义/麯义与目录“鞠义”视为同一统领名称别名；仅阵容主将享有 5 层条件。

## 验证

最终本地专项 `59 passed`，全量 `2077 passed`，清洁进程 registry 检查通过。
固定 seed=42 的完整 Engine 示例运行 5 回合，313 条事件，结束后剩余状态 0。
在本工作区执行 `python scripts/verify_stage14_xian_deng_si_shi.py` 可复现验证并生成证据文件。

验证结果和真实 Engine 事件见 `xiandeng_evidence/verification.json`、`demo_events.json`。
定向测试覆盖公式边界、开局属性修饰进入快照、后续属性不重算、实际普攻/主动/突击/DOT/反击/溅射入口、
兵力百分比而非绝对兵力、相等分支、两端等额、4/5 层、到期恢复、重复事件、随机失败、
跨战斗隔离、禁用/威慑/死亡、遇袭标准与旧入口、非法兵种与重复安装、完整 Engine 清理。
本地测试通过证明当前模型的代码行为，不证明 OPEN 口径等于游戏真实规则。
