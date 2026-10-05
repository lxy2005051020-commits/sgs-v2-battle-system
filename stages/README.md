# Stages / 项目阶段索引

本目录只保留当前有用的阶段权威、冻结记录和必要兼容材料。历史施工过程可由 Git history 追溯。

| Stage | Scope | Status |
|---|---|---|
| 1 | 基础运行模型 | COMPLETE |
| 2 | BattleSystem | FROZEN |
| 3 | BattleState | COMPLETE |
| 4 | 官方状态代表接入 | FROZEN |
| 5 | Effect | FROZEN |
| 6 | Skill Runtime 基础 | FROZEN |
| 7 | Trigger / Recovery | FROZEN |
| 8 | Damage Pipeline | FROZEN |
| 9 | Cross-Mechanism Runtime Orchestration | FROZEN |
| 10 | Persistent State Runtime Integration | FROZEN |
| 11 | 官方状态补全（一） | RUNTIME FROZEN / POST-FREEZE ACCEPTED |
| 12 | 官方状态补全（二） | FROZEN / COMPLETE |
| 13 | Core Gameplay Mechanism Completion | COMPLETE / FROZEN |
| 14 | Concrete Skill Integration | ACTIVE / MAINLINE UNLOCKED |

## 当前统一状态

```text
Official States            = 40
Research FROZEN            = 40 / 40
Runtime FROZEN TO CONTRACT = 40 / 40
Strict Complete            = 40 / 40

Core Gameplay Engine       = FROZEN
Skill Runtime Readiness    = READY
Stage14 Mainline Gate      = OPEN
Stage14 Troop Foundation   = FROZEN in Research
First Troop Skill in main  = 西凉铁骑 (20097)
```

## 当前导航

- [Stage9](stage9/README.md)
- [Stage10](stage10/README.md)
- [Stage11](stage11/README.md)
- [Stage12](stage12/README.md)
- [Stage13](stage13/README.md)
- [Stage14](stage14/README.md)

Stage13 exit gate 已通过。Stage14 具体战法可在对应 Research Contract / Family Contract、Runtime Audit、回归与 PR CI 全部通过后进入 `main`；不再受未完成的 Stage13 gate 阻塞。
