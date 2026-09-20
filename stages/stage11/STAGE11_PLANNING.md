# 第十一阶段规划 · 官方状态补全（一）

> 状态：规划草案 / 研究冻结推进中  
> 目标：状态补全，不接入正式战法执行链

## 1. 阶段责任

第十一阶段只负责：

> 把现有底层系统已经能够承接、但官方状态机制尚未严格完成的状态，补到“研究冻结 + 运行时冻结到合同”的正式状态。

## 2. 候选状态

当前候选：

```text
分摊
先攻
遇袭
缴械
虚弱
禁疗
震慑
规避
抵御
必中
破阵
警戒
会心
奇谋
看破
倒戈
攻心
```

最终范围不得凭这份清单直接冻结，必须先完成状态完成度与所有者矩阵。

### 2.1 当前研究冻结进度

截至 `2026-09-20`：

```text
690082 规避 / EVASION
Research = FROZEN
Evidence Maturity = HIGH_CONFIDENCE
Runtime = NOT_INTEGRATED
Strict Completion = NO

690083 抵御 / RESISTANCE
Research = FROZEN
Evidence Maturity = HIGH_CONFIDENCE
Runtime = NOT_INTEGRATED
Strict Completion = NO

690092 必中 / SURE_HIT
Research = FROZEN
Evidence Maturity = HIGH_CONFIDENCE CORE + PROJECT-AUTHORIZED ELIGIBILITY RULE
Runtime = NOT_INTEGRATED
Strict Completion = NO
```

Battle 侧只保存研究权威桥接，不复制第二份机制正文：

- `stages/stage11/research/690082_EVASION_RESEARCH_AUTHORITY.md`
- `stages/stage11/research/690083_RESISTANCE_RESEARCH_AUTHORITY.md`
- `stages/stage11/research/690092_SURE_HIT_RESEARCH_AUTHORITY.md`

正式研究合同：

- repository: `lxy2005051020-commits/sgs-state-mechanics-research`
- EVASION path: `states/functional/evasion/MECHANISM_CONTRACT.md`
- EVASION frozen commit: `32341b548f2ef9f83335a5e47c6a650842d4d093`
- RESISTANCE path: `states/functional/resistance/MECHANISM_CONTRACT.md`
- RESISTANCE current corrected authority head: `5741751b2723243606d9e83be40c1df5b9395ab2`
- SURE_HIT path: `states/functional/sure_hit/MECHANISM_CONTRACT.md`
- SURE_HIT frozen research head: `313f1a71369683ca6eb8213a412c94506aa00372`

690082 / 690083 / 690092 后续只进入 Stage11 Runtime Integration，不再重复开展机制研究，除非出现正式 Reopen 证据。

## 3. 按运行时所有者分组

### 伤害与命中

```text
规避
抵御
必中
破阵
警戒
会心
奇谋
看破
虚弱
```

目标：复用第八阶段伤害流水线已经冻结的扩展点，不改写伤害系统核心所有权。

### 恢复

```text
禁疗
倒戈
攻心
```

目标：统一由恢复与伤害后处理体系解释，不在状态系统中复制恢复逻辑。

### 行动与顺序

```text
先攻
遇袭
缴械
震慑
```

目标：由行动顺序或行动权限系统解释状态事实。

### 旧研究债务

```text
分摊
```

目标：关闭现有运行时与机制研究之间的证据债务，使其可以进入严格完成统计。

## 4. 阶段开始前必须完成的审计

对剩余状态逐个记录：

```text
当前研究等级
当前运行时等级
真正运行时所有者
是否已有正式接口
是否已有旧骨架
是否需要重新研究
是否依赖战法权限
是否放入第十一阶段
是否放入第十二阶段
```

已经研究冻结的状态（当前为 690082 EVASION、690083 RESISTANCE、690092 SURE_HIT）不再列入“是否需要重新研究”的开放项，只记录其 Runtime Gap。

## 5. 实现原则

状态系统只负责状态生命周期。

不得出现：

```text
为了规避状态重写伤害系统
为了禁疗状态复制恢复逻辑
为了缴械状态在多个系统里散落专用布尔值
```

正确方式是把状态事实交给真正的规则所有者解释。

## 6. 研究门槛

每个状态必须先拥有足以支持实现的机制合同。

如果研究不够：

```text
先研究
再设计
再实现
```

禁止因为代码接口已经存在就把“最低可用研究”直接当作冻结真相。

690082、690083、690092 已通过该门槛，后续实现必须消费各自 FROZEN research authority。

## 7. 设计冻结门槛

第十一阶段正式设计至少必须确定：

```text
每个状态的唯一运行时所有者
触发时点
持续与刷新规则
冲突与覆盖规则
权限判定点
随机数使用边界
与第七至第十阶段的兼容关系
```

## 8. 实施退出门槛

第十一阶段结束时：

```text
阶段内全部状态研究已冻结
阶段内全部状态运行时实现完成
交叉机制回归通过
演示场景已覆盖代表组合
最终独立审计通过
实施冻结完成
```

并且不得破坏第七、八、九、十阶段冻结合同。

## 9. 演示要求

第十一阶段开始同步升级演示场景，至少增加：

```text
命中与规避
抵御与必中
破阵 / 看破
会心 / 奇谋
禁疗与恢复
倒戈 / 攻心
先攻 / 遇袭
缴械 / 震慑
```

演示不代替测试。

## 10. 明确不做

第十一阶段不做：

```text
突击战法正式运行时
普通主动战法
准备战法
被动战法
指挥战法
阵法
兵种战法
完整技能调度器
```

## 11. 当前下一步

研究侧继续关闭 Stage11 剩余状态；实现侧仍未授权整体施工。

当前已冻结研究资产：

```text
690082 EVASION
690083 RESISTANCE
690092 SURE_HIT
```

690092 已完成研究冻结，不再继续扩张 Sure-Hit 问题。Stage11 下一研究候选转为：

```text
690093 BREAK_FORMATION / 破阵
```

进入 690093 前仍需先读取其当前 research authority 并按独立状态流程开展，不得从 Sure-Hit 结论直接猜测破阵机制。
