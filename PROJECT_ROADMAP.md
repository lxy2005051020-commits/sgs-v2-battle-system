> Gameplay Research status is MIRROR ONLY. Research truth and evidence: [pinned Research authority](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/RESEARCH_AUTHORITY_INDEX.md). This document owns Runtime/project progress.

# 项目路线

> Current authority: 2026-10-04

历史阶段计划已由当前 Stage13 路线取代。旧路线仍可从 Git 历史追溯，不再保留为当前树中的执行权威。

## 已完成主线

```text
Stage1-8   基础战斗 / Effect / Skill Runtime 基础 / Trigger / Damage
Stage9     跨机制编排
Stage10    持续状态
Stage11    官方状态补全（一）
Stage12    官方状态补全（二） / 40-state Runtime closure
Stage13-B  基础机制公式补全
Stage13-C  残余状态机制关闭
Stage13-D1 PendingWork foundation
```

上述已完成或冻结部分只做回归维护，除非出现正式 reopen authority。

## 当前主线

```text
Stage13
  -> reconcile remaining core capability boundaries
  -> close only true core blockers
  -> whole-battle deterministic replay / exit audit
  -> Core Gameplay Engine = FROZEN
  -> Skill Runtime Readiness = READY

Stage14+
  -> concrete Skill System integration
```

原则：

```text
REUSE -> EXTEND -> COMPOSE
real gameplay requirement -> minimal extension
no generic subsystem merely to satisfy an old roadmap label
```

Stage13 当前权威入口：[stages/stage13/README.md](stages/stage13/README.md)

## Stage14 阵法转段裁决（2026-10-12）

- 兵种战法主线已注册 15/16；**象兵 DEFERRED**，保留 [准备清单](stages/stage14/XIANG_BING_PREPARATION.md)，不作为阵法的前置阻塞。
- 下一目标为 **阵法战法 FORMATION**，仍属于 Stage14+ 具体战法接入路线下的 F0 子阶段，暂不凭空宣布 Stage15 冻结。
- 先完成 Research F0 证据与合同，Battle F0 完成准备阶段 type ordering / 队伍阵法准入设计与回归。
- 第一只 pilot 候选：锋矢阵（当前不声明其数值、时长、限制条件已冻结）。
- 后续指挥战法基于统一 PRE_BATTLE 编排接入，不为阵法造第二套 Engine。

[FORMATION F0 Runtime Readiness](stages/stage14/FORMATION_F0_RUNTIME_READINESS.md)
