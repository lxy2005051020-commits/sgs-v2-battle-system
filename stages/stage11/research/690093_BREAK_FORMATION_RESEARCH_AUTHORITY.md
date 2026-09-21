# 690093 BREAK_FORMATION / 破阵 — Stage11 Research Authority Bridge

Status: RESEARCH_FROZEN / RUNTIME_NOT_INTEGRATED  
Date: 2026-09-21

## 1. Purpose

本文件只负责把 Battle 仓库 Stage11 规划与外部 690093「破阵」FROZEN research authority 连接起来。

Battle 仓库不得复制维护第二份 current mechanism authority，也不得用当前 Runtime 代码反向证明游戏机制。

正式研究 authority：

- Repository: lxy2005051020-commits/sgs-state-mechanics-research
- Contract: states/functional/break_formation/MECHANISM_CONTRACT.md
- Research Ledger: states/functional/break_formation/RESEARCH_QUESTION_LEDGER.md
- Freeze Audit: states/functional/break_formation/FREEZE_AUDIT.md
- Frozen research head: 65c335688718453dfe264f9796cb14bde17d11a7
- Freeze date: 2026-09-21

## 2. Current Battle-Repo Status

```text
Research: FROZEN
Runtime: NOT_INTEGRATED
Strict Completion: NO
Stage owner: Stage11
Production implementation: NOT AUTHORIZED BY THIS BRIDGE
```

本桥接仅同步研究权威与 Runtime 准入状态，不代表 690093 已在 production runtime 中实现。

## 3. Frozen Behavior Summary

Stage11 设计必须消费以下外部合同：

- Break 是 Source-Local Defense Bypass Policy，不是 target-global debuff；
- Direct WEAPON 的 relevant defense = target DEF；
- Direct STRATEGY 按统一工程合同的 relevant defense = target INT；
- 有效 Break 使当前 Direct Damage 的 relevant defensive contribution 在可观察精度内被绕过；
- Break 不修改 target DEF / INT，也不留下供其他攻击者共享的 hidden broken-defense state；
- Break 不绕过 independent Weapon / Strategy / Generic Damage Reduction；
- 正常 Direct Damage 反映 Damage 前已经生效的 current relevant defense；
- Weapon / Strategy DOT 的 Break Policy 在 Application 时绑定，不得扩张成 Full Damage Snapshot；
- Cleave / Chain 属于 Parent-derived damage，Break 收益通过 ParentDamage 数值传播，不在 derived target 上重新跑 relevant-defense + Break；
- existing equal-or-stronger Break 会拒绝 incoming equal/weaker Break application；reject 不刷新、不延长、不接管 source attribution；
- incoming strictly stronger Break 的 replace/reject 行为仍为 UNKNOWN / NOT OBSERVED；
- Counterattack family evidence 保持 SUPPORTED，不得升级为 HIGH_CONFIDENCE；
- Immediate Active Strategy 的独立 empirical evidence 保持 UNKNOWN / UNOBSERVABLE；Runtime 由统一 Direct Damage engineering contract 收口。

## 4. Runtime Integration Constraints

Stage11 实现禁止：

- 把 Break 实现成修改 target DEF / INT 的全局破防 Debuff；
- 把 “bypass relevant defensive contribution” 写成已经证实 effective DEF/INT = 0；
- 让 Break 绕过百分比 Damage Reduction；
- 在 Cleave / Chain secondary node 重新执行 Break + defense calculation；
- 把 DOT Application-bound Break policy 写成完整 damage snapshot；
- 把 Q3 Direct Strategy 工程统一规则伪装成独立战报 HIGH_CONFIDENCE；
- 把 Q6 Counterattack SUPPORTED 擅自升级；
- 把任何 incoming Break 都无条件拒绝；
- 把内部实现假定为 Boolean / Mutex / unique-slot official fact；
- 因为 Stage8 已有 IGNORE_RELEVANT_TARGET_DEFENSE 能力就倒推官方机制。

## 5. Integration Direction

Stage11 后续设计应优先复用既有 Damage Pipeline 的正式 defense-policy 扩展点，而不是新增第二套破阵伤害公式。

推荐运行时责任边界：

```text
State runtime
-> owns Break lifecycle / provenance / application conflict

Damage runtime
-> interprets Break as relevant-defense policy for eligible Direct Damage

Persistent state runtime
-> stores application-bound Break policy required by frozen contract

Derived damage runtime
-> preserves Cleave / Chain parent-derived topology
```

任何实现发现与外部 FROZEN contract 冲突时，必须显式 Reopen 研究，不得静默修改冻结语义。
