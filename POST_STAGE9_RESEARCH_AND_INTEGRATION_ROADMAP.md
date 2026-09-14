# Post-Stage9 · 官方状态研究与 Runtime Integration 路线图

> 状态：`CURRENT POST-STAGE9 ROADMAP`
>
> 日期：2026-09-14
>
> 本文件是 Stage9 FROZEN 之后的当前项目级路线权威。根目录旧 `PROJECT_ROADMAP.md` 保留为历史规划快照，不再作为 Stage10+ 的当前路线 authority。

## 1. 重新定义“状态完成”

今后不得把“代码中已有行为”直接等同于“官方状态已经完成”。

唯一严格完成标准：

```text
专项机制研究
→ Research FROZEN
→ Runtime Integration Design
→ Production Implementation
→ Cross-mechanism Regression
→ Independent Final Audit
→ Runtime FROZEN TO CONTRACT
```

只有同时满足：

```text
Research FROZEN
AND
Runtime FROZEN TO CONTRACT
```

才计入官方状态最终完成数。

## 2. 当前基线

官方具体 BattleState：40。

严格完成：8。

```text
combo
cleave
counterattack
damage_share
chain_link
guard
confusion
taunt
```

尚未彻底完成：32。

`damage_split / 分摊` 为特殊项：Stage9 Runtime 已按明确项目默认冻结，但 `DSTS9-B02` 仍为 empirical OPEN / UNOBSERVED，因此不计入最终 40/40 完成数。

状态研究当前 authority：

```text
lxy2005051020-commits/sgs-state-mechanics-research
├─ RESEARCH_ROADMAP_V2.md
├─ STATE_COMPLETION_MATRIX.md
└─ STATE_MECHANICS_INDEX.md
```

## 3. Stage10：Persistent State Runtime Integration

Stage10 的任务不再定义为“高级控制七状态”。

Stage10 当前规划：

```text
8 个已研究冻结的持续性状态
→ 正式 Runtime Integration
→ 交叉机制审计
→ Runtime Freeze
```

目标：

```text
690072 灼烧 BURN
690073 水攻 FLOOD
690074 中毒 POISON
690075 溃逃 ROUT
690076 沙暴 SANDSTORM
690077 叛逃 REBELLION
690078 急救 FIRST_AID
690079 休整 RECUPERATION
```

Stage10 必须尊重：

```text
Stage7 Trigger / Recovery = FROZEN
Stage8 Damage Pipeline = FROZEN
Stage9 Runtime Orchestration = FROZEN
```

因此 Stage10 应以“适配现有冻结机制合同”为核心，而不是重新定义 Stage7/8/9 所有权。

Stage10 当前仍处于：

```text
RESEARCH / DESIGN / BOUNDARY DEFINITION
PRODUCTION IMPLEMENTATION = NOT AUTHORIZED
```

## 4. Stage11：Damage / Hit / Recovery Derived States

候选范围：

```text
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

这些状态不得直接从旧 `MINIMUM_USABLE` 接入 production。

流程：

```text
Research authority cleanup
→ 专项研究
→ Research Freeze
→ Stage11 Design
→ Runtime Integration
```

Stage8 Damage Pipeline 只允许通过正式 extension point 扩展，不允许 silent semantic change。

## 5. Stage12：Basic Action / Order / Control Re-Research

范围：

```text
先攻
遇袭
缴械
虚弱
禁疗
震慑
```

这些状态已有的旧 Stage4/7 行为只视为：

```text
SKELETON / REPRESENTATIVE ENGINEERING BEHAVIOR
```

不视为状态机制已经研究冻结。

Stage12 必须重新建立正式证据链与 Mechanism Contract，再审计旧 Runtime 是否与新 authority 一致。

## 6. Stage13：Advanced Skill Authority & Target Control

范围：

```text
洞察
计穷
伪报
挑拨
威慑
```

预计新增或正式化的通用能力：

```text
StateApplicationPolicy
SkillTaxonomy
SkillAuthoritySystem
SourceAuthorityPolicy
SkillTargetResolution
control immunity / bypass
skill suppression / restoration
```

原则：状态贡献事实，统一 policy system 解释事实。禁止把控制效果扩散成 UnitRuntime / SkillRuntime 上的一堆专用 bool。

## 7. Stage14：Equipment & Composite Control

范围：

```text
破坏
捕获
```

预计能力：

```text
Minimal EquipmentRuntime
EquipmentAuthorityPolicy
Composite Control Policy
```

捕获必须通过统一权限系统组合行动、伤害、技能、恢复与目标限制，不得复制多个系统的私有 special-case。

## 8. Stage15：40/40 State Finalization

目标：

```text
关闭 DISTRIBUTION DSTS9-B02 或形成正式终态决议
清零真实研究债务
清理 MINIMUM_USABLE current-authority 漂移
40 状态 completion matrix 全量审计
跨状态组合回归
全量 State Runtime Freeze
```

最终验收：

```text
40 / 40 Research FROZEN
40 / 40 Runtime FROZEN TO CONTRACT
```

在此之前不得宣称“官方状态系统全部完成”。

## 9. 架构重构安排

状态完善期间允许进行必要的语义扩展，但不建议同时进行大规模目录搬迁。

推荐：

```text
Stage10-15 状态语义完善
→ State Runtime Program FROZEN
→ 独立 Architecture Modularization Stage
→ NO GAMEPLAY CHANGE
→ NO SEMANTIC CHANGE
```

如果某个状态必须依赖新抽象，例如 SkillAuthority 或 EquipmentRuntime，应在对应阶段最小化新增并进行独立设计审计。

## 10. 每阶段统一 Gate

```text
Research authority
↓
Evidence gap audit
↓
Mechanism Contract / Freeze Record
↓
STAGEX.md
↓
Independent Design Audit
↓
Implementation Authorization
↓
Implementation
↓
pytest / demo / CI
↓
Cross-mechanism Regression
↓
Independent Final Audit
↓
FROZEN
```

任何阶段不得因为“看起来简单”跳过 Research Freeze 或 Design Audit。
