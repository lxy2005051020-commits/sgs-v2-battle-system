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
