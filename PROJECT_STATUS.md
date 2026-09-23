# 三国志战略版战斗模拟器 V2 · 当前项目状态

> 本文件维护当前项目状态与后续主线。跨仓库 40 状态总表见 [CANONICAL_STATE_PLANNING_MATRIX.md](CANONICAL_STATE_PLANNING_MATRIX.md)。

## 1. 已完成阶段

```text
Stage 1  基础运行模型                           ✅
Stage 2  BattleSystem                          ✅ FROZEN
Stage 3  BattleState                           ✅
Stage 4  官方状态代表接入                       ✅ FROZEN（工程阶段）
Stage 5  Effect                                ✅ FROZEN
Stage 6  Skill Runtime                         ✅ FROZEN（基础能力）
Stage 7  Trigger / Recovery                    ✅ FROZEN
Stage 8  Damage Pipeline                       ✅ FROZEN
Stage 9  Cross-Mechanism Runtime Orchestration ✅ FROZEN
Stage 10 Persistent State Runtime Integration ✅ FROZEN / main integrated
```

Stage10 main integration commit：

`30f623f9efed20b5a82044b51519db1af6da86d3`

当前 `main` 的生产与测试子树仍等于 Stage10 冻结 pin：

```text
sgs_v2 = 05511f7576b10efc9664e4e70d9dad88d364966a
tests  = 122ffd68f1aac06ce353572fd3568aa54d19b5dd
```

## 2. 当前统一完成度

```text
Official States                 = 40
Research FROZEN                 = 24
Runtime FROZEN TO CONTRACT      = 16
Strict Complete                 = 16
```

严格完成：

```text
Research FROZEN
AND
Runtime FROZEN TO CONTRACT
```

已严格完成 16 个：

```text
连击 / 群攻 / 反击 / 分担
铁索连环 / 援护 / 混乱 / 嘲讽
灼烧 / 水攻 / 中毒 / 溃逃
沙暴 / 叛逃 / 急救 / 休整
```

## 3. 当前路线 authority

Project Stage authority：

- [POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md](POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md)
- [CANONICAL_STATE_PLANNING_MATRIX.md](CANONICAL_STATE_PLANNING_MATRIX.md)

Research maturity / mechanism authority：

`lxy2005051020-commits/sgs-state-mechanics-research`

Project Stage 与 Research Wave 是两个层次。Research Wave 可以重排，不能静默修改 Project Stage 编号。

## 4. Stage11 · ACTIVE

定义：

```text
官方状态补全（一）
Canonical Scope = 17
```

范围：

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

当前研究状态：

```text
Research FROZEN = 8
Research non-FROZEN / debt = 9
Runtime FROZEN = 0
```

已 Research FROZEN：

```text
690082 EVASION
690083 RESISTANCE
690092 SURE_HIT
690093 BREAK_FORMATION
690070 CRITICAL
690069 STRATEGY_CRITICAL
690094 LIFE_STEAL
690095 STRATEGY_LIFE_STEAL
```

全部 8 个 Runtime 当前仍为 `NOT_INTEGRATED`。

特殊项：

```text
690099 警戒 = RESEARCH OPEN / EVIDENCE BLOCKED OR DEFERRED
690221 看破 = RESEARCH OPEN / EVIDENCE BLOCKED OR DEFERRED
690086 分摊 = DSTS9-B02 research debt
```

690069 奇谋、690095 攻心保持 **PROJECT-FROZEN MIRROR CONTRACT** 标记，不与独立同规模实证冻结混淆。

### Stage11 当前工程授权边界

允许：

```text
Research closure
Mechanism authority bridge
Runtime Integration Design
Independent Design Audit
Design Freeze
```

尚不授权：

```text
Overall Stage11 production implementation
Stage12 activation
Stage13 skill runtime
```

## 5. Stage12 · PLANNING ONLY

Canonical scope = 7：

```text
690089 洞察
690101 计穷
690107 伪报
690108 挑拨
690109 破坏
690110 捕获
690222 威慑
```

定位：

```text
统一控制权限
战法类别认识
目标权限
复合控制
最小装备权限
```

Stage12 仍然不正式执行具体战法。

## 6. Stage13+

```text
Stage13 = 突击战法运行时
Stage14 = 普通主动战法
Stage15 = 准备战法
Stage16+ = 被动 / 指挥 / 阵法 / 兵种等
```

Stage13 在 Stage11 / Stage12 状态出口门槛满足前不得启动。

## 7. Research Wave mapping

```text
Project Stage11
  Research Wave 2 = 伤害 / 命中 / 恢复
  Research Wave 3 = 行动 / 顺序 / 控制
  Research Debt   = 690086 分摊

Project Stage12
  Research Wave 4 = 技能权限 / 目标控制
  Research Wave 5 = 装备 / 复合控制
```

旧 Research 文档把 Wave 3/4/5 写成 Project Stage12/13/14 的做法已被纠正为 ROADMAP DRIFT，不构成正式 Replan。

## 8. 当前下一步

Research side：
继续关闭 Stage11 未完成研究、证据阻塞与 DSTS9-B02 债务。

Runtime side：
对 8 个 Research-FROZEN 状态进入：

```text
Runtime Integration Design
→ Independent Design Audit
→ Design Freeze
→ Implementation
```

不得跨过设计冻结直接施工。
