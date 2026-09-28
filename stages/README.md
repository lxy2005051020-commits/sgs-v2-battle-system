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
- [Stage 12：官方状态补全（二）— RUNTIME FROZEN / COMPLETE](stage12/README.md)
- [Stage 13：游戏底层机制完备化 — ACTIVE / ENTRY GATE PASS](stage13/README.md)

## 2. 当前阶段

```text
Stage 8  = FROZEN
Stage 9  = FROZEN
Stage10  = FROZEN / MAIN INTEGRATION COMPLETE
Stage11  = RUNTIME FROZEN / POST-FREEZE ACCEPTED
Stage12  = RUNTIME FROZEN / COMPLETE
Stage13  = CORE GAMEPLAY MECHANISM COMPLETION / ACTIVE / ENTRY GATE PASS
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
Stage12 Complete = YES
```

Research Freeze and Runtime Freeze remain separate governance states. Stage12 has passed its Final Completion / Freeze Audit and is closed. The next project owner is Stage13 Core Gameplay Mechanism Completion.

## 6. Project Stage 与 Research Wave

```text
Project Stage11
  Research Wave 2 = 伤害 / 命中 / 恢复
  Research Wave 3 = 行动 / 顺序 / 控制
  Research Debt   = 690086 分摊

Project Stage12
  Research Wave 4 = 技能权限 / 目标控制
  Research Wave 5 = 装备 / 复合控制

Project Stage13 = 游戏底层机制完备化 / Core Gameplay Mechanism Completion
Project Stage14+ = 战法系统 / Skill System
                  exact subtype staging deferred until Stage13 exit audit
```

Research Wave 是研究顺序，不得覆盖项目阶段编号。

## 7. Current next action

```text
STAGE13_B1_WOUNDED_TROOP_AND_RECOVERABLE_CAPACITY_RESEARCH
→ B1 wound/recoverable-capacity research
→ B2 damage increase/reduction mechanics research
→ B3 recovery/treatment formula research
→ Stage13-C residual state mechanism closure
```

Stage13 Readiness = READY. Stage13 Active = YES. Stage13-A inventory is complete; the current foundational-research amendment governs execution.

## STAGE12_FINAL_COMPLETION_STAGE_INDEX — 2026-09-28

Stage12 Runtime = FROZEN; Stage12 Complete = YES; FINAL_40_STATE_RUNTIME_AUDIT = PASS; GOVERNANCE_SYNC = PASS.
Research remains 39/40 and Strict Complete 39/40 because 690086 DSTS9-B02 remains OPEN / UNOBSERVED.
Stage13 Readiness = READY; Stage13 Active = NO.
Fresh merged-main CI `36389096961`: 1667 passed / demo PASS.


## STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN — 2026-09-28

The old `Stage13 Assault → Stage14 Active → Stage15 Preparation` sequence is superseded.

```text
Stage13 = Core Gameplay Mechanism Completion
Stage14+ = Skill System
```

Stage13 completes and freezes the game-engine substrate before large-scale skill runtime integration.
Assault remains a future skill-system workstream and is intentionally moved behind the Stage13 engine-completion gate.

Authority: [Stage13 Replan](stage13/STAGE13_CORE_GAMEPLAY_MECHANISM_REPLAN.md).


## STAGE13_INVENTORY_ACTIVATION — 2026-09-28

~~~text
STAGE13_CORE_GAMEPLAY_MECHANISM_INVENTORY_AUDIT = PASS
CORE_GAMEPLAY_MECHANISM_INVENTORY               = COMPLETE
Stage13 Active                                   = YES
Stage13-A                                        = COMPLETE
NEXT                                             = STAGE13_B1_WOUNDED_TROOP_AND_RECOVERABLE_CAPACITY_RESEARCH
~~~

The Stage13 index and ledgers are under stages/stage13/. No gameplay implementation was added by the activation audit.


## STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN — 2026-09-28

The current execution order is B1 wounded/recoverable capacity, B2 damage increase/reduction mechanics, B3 recovery/treatment formula mechanics, then Stage13-C residual state-debt closure.

Authority: [Stage13 Foundational Research Priority Replan](stage13/STAGE13_FOUNDATIONAL_RESEARCH_PRIORITY_REPLAN.md).
