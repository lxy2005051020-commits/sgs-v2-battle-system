# 鱼鳞阵接入记录

2026-10-13；独立分支 `stage14/yu-lin-zhen`；GitHub最新main核对基线
`4357a6b0a46f379945193c0e203a1373dd1c6e03`。
状态：`USER_APPROVED_PARTIAL / COMMAND_ONLY / FULL_MODEL_FAIL_CLOSED / NOT_GAMEPLAY_FROZEN`。
本记录随独立分支发布到GitHub供审查；发布不表示远端CI或main合并完成。

用户指令：“暂时先保留报错,先完成其他部分”。

## 用户指定暂缓项（2026-10-13）

后续指令：“暂时先不添加武力和统率加成这个,将其在github上标注出来”。
据此将以下属性缩放明确标记为 `DEFERRED_BY_USER / NOT_IMPLEMENTED`：

- 主将武力、统率对抵御和治疗触发概率的加成。
- 治疗率的统率缩放；其公式和读取时点仍未确定，继续保留缺失规则。

副将固定统率提升继续作为已实现部分（满级+55）。抵御、治疗受击分支继续未启用，
完整模式保留 `NotImplementedError`；25%基础概率和30%基础治疗率仅是静态来源值。
后续补齐上述缩放须取得明确规则，本次不填入推测公式。

## 来源与已实现范围

静态客户端ID `20836`，阵法，`arm_limit={}`。来源为2026-08-08静态快照，
十个等级完整原文、原始HTML、配置和源文件SHA256分别保存在
[原始行](yu_lin_evidence/static_levels.csv)与[来源清单](yu_lin_evidence/source_manifest.json)。
不将此快照描述为当前客户端实证机制。

正式注册到 `FORMATION_SKILL_REGISTRY`，复用每队唯一阵法、开场顺序及携带者阵亡清理。
可由主将或任何副将携带；属性目标始终为真实编队的两名副将，主将不获得此提升。
副将统率为固定加法修饰，不修改基础值，不随后续统率变化按比例重算。
要求完整存活三人编队及明确主副将位置。

| 等级 | 副将统率提升 | 静态基础触发概率（未执行） | 静态基础治疗率（未执行） |
|---|---|---|---|
| 1 | 27.5 | 12.5% | 15% |
| 2 | 30.6 | 13.9% | 16.7% |
| 3 | 33.6 | 15.3% | 18.3% |
| 4 | 36.7 | 16.7% | 20% |
| 5 | 39.7 | 18.1% | 21.7% |
| 6 | 42.8 | 19.4% | 23.3% |
| 7 | 45.8 | 20.8% | 25% |
| 8 | 48.9 | 22.2% | 26.7% |
| 9 | 51.9 | 23.6% | 28.3% |
| 10 | 55 | 25% | 30% |

## 入口与组件树

```python
from sgs_v2.battle_core import create_yu_lin_zhen_runtime

# 仅已确认统率部分，必须显式选择；不会产生抵御或治疗。
runtime = create_yu_lin_zhen_runtime("holder_id", level=10, command_only=True)

# 默认完整模式可构造、装备，但在正式开场/直接安装准入时明确报错。
full_runtime = create_yu_lin_zhen_runtime("holder_id")
```

```text
FormationSkillConfig / FORMATION_SKILL_REGISTRY[20836]
  PRE_BATTLE / 100% / 无准备回合 / 同队唯一阵法
  validator: canonical定义 + 模式 + 完整存活编队校验
  command_only=True
    TargetSystem.allies: 编队两名真实副将
    ApplyStateEffect: AttributeBonusParams("defense", exact_level_bonus)
    StateNode -> ProviderNode: 来源携带者/战法/槽位
    既有AttributeSystem / StateEffectivenessPolicy / 生命周期与阵亡清理
  默认完整模式
    NotImplementedError，发生在任何开场被动效果、状态安装或RNG消耗之前
```

新增公共能力为 `FormationSkillConfig.validator`：默认None保持既有阵法行为；
纯只读回调共用于全局开场预检和单个阵法安装准入，无战法ID分支。
没有另建注册系统；此仓库的canonical注册即正式发现路径，无类别自动扫描器。
新增战法模块 `yu_lin_zhen.py`，公开定义/runtime工厂由 `battle_core.__init__` 导出。
改动另涉及正式注册、阵法数量回归、专项测试和原始来源提取脚本。
未新增伤害、恢复、抵御计算器或修改冻结核心owner。

## 保留报错与未实现分支

完整模式缺少：主将武力和统率对触发概率的缩放公式、统率治疗缩放及治疗来源、
属性读取时点。因此本次不实现以下受击分支，基础概率与治疗率仅保留为来源数据：

- 第1–3回合副将受伤后概率获得1次抵御。
- 第5回合起主将受伤后概率获得治疗。

第4回合不在上述任一分支窗口。零伤害是否触发、抵御持续与叠加、治疗来源兵力与属性、
伤害后反应微顺序均待确认；不会沿用急救默认规则替代这些未确认项。
仅统率模式的battle metadata会明确记录 `mode`、两个 `omitted` 分支与缺失规则，
不能视为鱼鳞阵完整战斗效果已接入。

## 验证

专项与全量计数见[验证记录](yu_lin_evidence/verification_summary.txt)。
覆盖十级静态值、各携带位置、五基础兵种、来源槽位、无RNG消耗、非法定义/编队原子拒绝、
默认完整模式在直接安装/开场调度/引擎路径报错、disabled跳过、重复安装拒绝、
双方隔离、固定加法增量、状态移除、provider阵亡清理、引擎自动安装以及通用validator。
Stage13-D1冻结owner和青州兵独立审计、demo、清洁进程canonical注册核验结果亦保留在证据目录。
测试验证工程实现，不关闭客户端机制实证边界。
