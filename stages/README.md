# Stages / 项目阶段索引

每个阶段的设计、研究、证据、审计、冻结和实施材料统一存放在 `stages/stageN/`。

## 1. 阶段导航

- [Stage 1：基础运行模型](stage1/README.md)
- [Stage 2：BattleSystem](stage2/README.md)
- [Stage 3：BattleState](stage3/README.md)
- [Stage 4：官方状态代表接入](stage4/README.md)
- [Stage 5：Effect](stage5/README.md)
- [Stage 6：Skill Runtime](stage6/README.md)
- [Stage 7：Trigger / Recovery](stage7/README.md)
- [Stage 8：Damage Pipeline — FROZEN](stage8/README.md)
- [Stage 9：Cross-Mechanism Runtime Orchestration — FROZEN](stage9/README.md)
- [Stage 10：Persistent State Runtime Integration — FROZEN](stage10/README.md)
- [Stage 11：官方状态补全（一）— RUNTIME FROZEN / POST-FREEZE ACCEPTED](stage11/README.md)
- [Stage 12：官方状态补全（二）— 7/7 RUNTIME FROZEN / FINAL COMPLETION AUDIT PENDING](stage12/README.md)

## 2. 当前阶段

```text
Stage 8  = FROZEN
Stage 9  = FROZEN
Stage10  = FROZEN / MAIN INTEGRATION COMPLETE
Stage11  = RUNTIME FROZEN / POST-FREEZE ACCEPTED
Stage12  = ACTIVE / RESEARCH COMPLETE / 7 OF 7 RUNTIME FROZEN / FINAL COMPLETION AUDIT PENDING
Stage13  = NOT ACTIVE
```

## 3. 当前统一状态数字

```text
Official States            = 40
Research FROZEN            = 39
Runtime FROZEN TO CONTRACT = 40
Strict Complete            = 39

Stage11 Scope              = 17
Stage11 Research FROZEN    = 16
Stage11 Runtime FROZEN     = 17

Stage12 Scope              = 7
Stage12 Research FROZEN    = 7
Stage12 Runtime FROZEN     = 7
```

Strict Complete requires both Research FROZEN and Runtime FROZEN TO CONTRACT.

## 4. Stage11 final authority

```text
Runtime Tested SHA         = ce42bc62cfb26f8ca0b448e74b26533604bb0505
Post-Freeze Acceptance SHA = 5a0a4164e7624c28eae2c7aa28f66061ef3c9313
Acceptance CI              = 36170063365 / 913 passed / demo PASS
B11-FRZ-001                = CLOSED
Stage11 Reopen Required    = NO
```

690086 Distribution remains a research-debt state governed by an explicit project runtime default, so it remains outside Strict Complete.

## 5. Stage12 research snapshot

Research FROZEN:

- 690089 INSIGHT
- 690101 EXHAUSTION
- 690107 FALSE_REPORT
- 690108 PROVOCATION
- 690222 INTIMIDATION
- 690109 SABOTAGE
- 690110 CAPTURE

Battle research mirrors:

- [690101 EXHAUSTION](stage12/STAGE12_690101_EXHAUSTION_RESEARCH_SYNC.md)
- [690107 FALSE_REPORT](stage12/STAGE12_690107_FALSE_REPORT_RESEARCH_SYNC.md)
- [690108 PROVOCATION](stage12/STAGE12_690108_PROVOCATION_RESEARCH_SYNC.md)

Research queue: COMPLETE.

```text
Stage12 Research = 7 / 7 FROZEN
Stage12 Gameplay Implementation = 7 / 7
Stage12 Runtime Frozen = 7 / 7
Stage12 Complete = NO
```

Research Freeze and Runtime Freeze remain separate governance states. Stage12 now awaits its stage-level Final Completion / Freeze Audit before any Stage13 activation decision.

## 6. Project Stage 与 Research Wave

```text
Project Stage11
  Research Wave 2 = 伤害 / 命中 / 恢复
  Research Wave 3 = 行动 / 顺序 / 控制
  Research Debt   = 690086 分摊

Project Stage12
  Research Wave 4 = 技能权限 / 目标控制
  Research Wave 5 = 装备 / 复合控制

Project Stage13 = 突击战法
Project Stage14 = 普通主动战法
Project Stage15 = 准备战法
```

Research Wave 是研究顺序，不得覆盖项目阶段编号。

## 7. Current next action

```text
Stage12 Final Completion / Freeze Audit
→ seven-state cross-state final regression
→ governance consistency confirmation
→ Stage12 completion decision
```

Stage13 remains NOT ACTIVE until that stage-level gate is explicitly closed.

## STAGE12_FINAL_AUDIT_CANDIDATE_STAGE_INDEX — 2026-09-28

Stage12 Research = 7/7 FROZEN; Gameplay = 7/7; Runtime Frozen To Contract = 7/7. Stage12 Final Completion Audit candidate is green locally (1667 passed + demo PASS) and awaits fresh merged-main CI before Stage12 Complete may become YES. Stage13 Active = NO.
