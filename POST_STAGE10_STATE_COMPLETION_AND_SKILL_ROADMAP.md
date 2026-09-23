# 第十阶段后 · 官方状态补全与战法接入总路线

> 状态：**当前项目级路线权威**
>
> 初始建立：2026-09-16
>
> 双仓库路线统一：2026-09-23
>
> Canonical 40-state view: [CANONICAL_STATE_PLANNING_MATRIX.md](CANONICAL_STATE_PLANNING_MATRIX.md)

## 1. Authority Decision

本项目的 **Project Stage** 与研究仓库的 **Research Wave** 是两个不同层次：

```text
Project Stage
= 决定什么时候建设什么产品能力
= Battle repository authority

Research Wave
= 决定机制研究按什么依赖顺序推进
= Research repository authority
```

Research Wave 可以重新排序，但不得静默重编号 Project Stage。

本次跨仓库审计没有发现正式项目级 Replan 决议批准把原有：

```text
Stage11 = 17 states
Stage12 = 7 states
Stage13 = 突击战法
Stage14 = 普通主动
Stage15 = 准备战法
```

改成 Research repository 曾出现的 `10 / 6 / 5 / 2 / debt closure` 项目阶段编号。

因此后者统一解释为 Research Wave，原先把它们写成 Project Stage 的部分属于 **ROADMAP DRIFT**。

## 2. 当前统一完成度

官方具体状态：40。

```text
Research FROZEN            = 25 / 40
Runtime FROZEN TO CONTRACT = 16 / 40
Strict Complete            = 16 / 40
```

严格完成只认：

```text
Research FROZEN
+
Runtime FROZEN TO CONTRACT
```

Stage10 的 8 个持续状态已经完成正式 Runtime Integration、独立审计、Implementation Freeze 与 main integration，因此计入严格完成。

当前严格完成 16 个：

```text
连击 / 群攻 / 反击 / 分担
铁索连环 / 援护 / 混乱 / 嘲讽
灼烧 / 水攻 / 中毒 / 溃逃
沙暴 / 叛逃 / 急救 / 休整
```

## 3. Stage11 · 官方状态补全（一）

Canonical Scope = 17：

```text
690086 分摊
690090 先攻
690091 遇袭
690102 缴械
690104 虚弱
690105 禁疗
690111 震慑
690082 规避
690083 抵御
690092 必中
690093 破阵
690099 警戒
690070 会心
690069 奇谋
690221 看破
690094 倒戈
690095 攻心
```

当前：

```text
Stage11 Research FROZEN = 9
Stage11 Runtime FROZEN  = 0
Stage11 non-FROZEN/debt = 8
```

已 Research FROZEN：

```text
690082 规避 EVASION
690083 抵御 RESISTANCE
690092 必中 SURE_HIT
690093 破阵 BREAK_FORMATION
690070 会心 CRITICAL
690069 奇谋 STRATEGY_CRITICAL
690094 倒戈 LIFE_STEAL
690095 攻心 STRATEGY_LIFE_STEAL
690090 先攻 FIRST_STRIKE
```

九者均未 Runtime FROZEN；690090 保持 `SKELETON_ONLY`，其余既有 Research-FROZEN 状态保持当前 `NOT_INTEGRATED` 记录。

特殊治理状态：

```text
690099 警戒 = RESEARCH OPEN / EVIDENCE BLOCKED OR DEFERRED
690221 看破 = RESEARCH OPEN / EVIDENCE BLOCKED OR DEFERRED
690086 分摊 = DSTS9-B02 empirical debt
```

`DSTS9-B02` 必须继续写成：

```text
Empirical Status = OPEN / UNOBSERVED
Runtime Status   = CLOSED BY EXPLICIT PROJECT RUNTIME DEFAULT
```

不得缩写成“研究已关闭”。

690069 奇谋与 690095 攻心保持 **PROJECT-FROZEN MIRROR CONTRACT** 区分，不伪装成与 690070 会心 / 690094 倒戈相同规模的独立战报实证。

### Stage11 Research Wave

```text
Research Wave 2
= 伤害 / 命中 / 恢复
= 690082 / 690083 / 690092 / 690093 / 690099
  / 690070 / 690069 / 690221 / 690094 / 690095

Research Wave 3
= 行动 / 顺序 / 控制
= 690090 / 690091 / 690102 / 690104 / 690105 / 690111

Research Debt Closure
= 690086
```

以上全部仍属于 **Project Stage11**。

## 4. Stage12 · 官方状态补全（二）

Canonical Scope = 7：

```text
690089 洞察
690101 计穷
690107 伪报
690108 挑拨
690109 破坏
690110 捕获
690222 威慑
```

Stage12 定位：

```text
统一控制权限
战法类别认识
目标权限
复合控制
最小装备权限
```

Research-side mapping：

```text
Research Wave 4
= 690089 / 690101 / 690107 / 690108 / 690222

Research Wave 5
= 690109 / 690110
```

Stage12 允许建立最小、通用的战法类别与权限基础，但 **仍不正式接入具体战法执行链**。

如 Stage11 因证据阻塞存在未冻结状态，必须在项目决议允许的边界内继续关闭；Evidence Blocked 不等于自动改变 Project Stage ownership。

## 5. Stage13 · 突击战法运行时

Stage13 才正式进入具体战法执行。

目标：

```text
普通攻击产生突击机会
→ 已装备突击战法识别
→ 发动率
→ 目标处理
→ 效果执行
→ 现有 Damage / State / Recovery owner 结算
→ 死亡 / 战斗结束正确中止
```

不得因为 Research Wave 曾使用 “Stage13” 字样而提前启动。

## 6. Stage14 · 普通主动战法

```text
武将行动
→ 主动战法发现
→ 权限判定
→ 发动率
→ 目标选择
→ 效果执行
```

不包含准备一回合的主动战法。

## 7. Stage15 · 准备战法

```text
开始准备
→ 准备生命周期
→ 中断 / 控制 / 死亡处理
→ 下一合法时点正式发动
→ 目标与效果结算
```

## 8. Stage16+

后续按依赖进入：

```text
被动战法
指挥战法
阵法
兵种战法
属性增减 / 转移
更多触发族
真实武将与战法内容
```

## 9. Stage11 当前工程边界

当前项目仍处于 Stage11。

Research side：

```text
继续关闭 Stage11 未完成研究
保留 evidence-blocked 标记
关闭或正式处置 DSTS9-B02 research debt
```

Runtime side：

```text
9 个 Research-FROZEN 状态
→ Runtime Integration Design
→ Independent Design Audit
→ Design Freeze
→ Implementation
```

在 Design Freeze 前，不授权整体 Stage11 production implementation。

## 10. Stage11 Exit Gate

Stage11 结束至少要求：

```text
Stage11 范围内研究完成，或存在正式项目级处置决议
+
Runtime Integration 完成
+
回归通过
+
演示覆盖
+
独立审计
+
Implementation Freeze
```

在该 Gate 满足前：

```text
Stage12 = NOT ACTIVE
Stage13 = NOT ACTIVE
```

## 11. 唯一矩阵与跨仓库同步

Battle repository 的 [CANONICAL_STATE_PLANNING_MATRIX.md](CANONICAL_STATE_PLANNING_MATRIX.md) 是 Project Stage / Runtime 的跨仓库 canonical matrix。

Research repository 的 `STATE_COMPLETION_MATRIX.md` 是 research-side mirror，负责 Research Maturity / Mechanism Authority，并镜像 Project Stage 与 Runtime 状态。

两边不得再独立维护互相冲突的严格完成数或 Project Stage 编号。
