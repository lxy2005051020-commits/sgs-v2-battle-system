# 三国志战略版 V2 战斗系统

## 当前权威导航

- [当前项目状态](PROJECT_STATUS.md)
- [Canonical State Planning Matrix](CANONICAL_STATE_PLANNING_MATRIX.md)
- [第十阶段后总路线](POST_STAGE10_STATE_COMPLETION_AND_SKILL_ROADMAP.md)
- [Stage12](stages/stage12/README.md)
- [各阶段索引](stages/README.md)
- [跨阶段状态研究](research/README.md)

## 当前工程边界

    Stage8  = FROZEN
    Stage9  = FROZEN
    Stage10 = FROZEN
    Stage11 = RUNTIME FROZEN / POST-FREEZE ACCEPTED
    Stage12 = ACTIVATION GATE CLEARED / RESEARCH IN PROGRESS / PRODUCTION RUNTIME NOT ACTIVE
    Stage13 = NOT ACTIVE

Stage11 Runtime Tested SHA:
ce42bc62cfb26f8ca0b448e74b26533604bb0505

Stage11 Post-Freeze Acceptance SHA:
5a0a4164e7624c28eae2c7aa28f66061ef3c9313

Acceptance CI:
36170063365 / 913 passed / demo PASS

## 官方状态统一完成度

    Official States                 = 40
    Research FROZEN                 = 35 / 40
    Runtime FROZEN TO CONTRACT      = 33 / 40
    Strict Complete                 = 32 / 40

Strict Complete 仍严格要求：

    Research FROZEN
    +
    Runtime FROZEN TO CONTRACT

690086 Distribution 保留 research debt，因此虽然 Runtime frozen，仍不计 Strict Complete。

## Stage12 research snapshot

Stage12 canonical scope = 7.

Research FROZEN:
- 690089 INSIGHT
- 690101 EXHAUSTION
- 690107 FALSE_REPORT

690101 当前状态：
- Contract v0.2-frozen
- adversarial audit PASS
- freeze audit PASS
- 23,002 structured battle reports
- 18,487 observed EXHAUSTION executions
- TRUE_COUNTEREXAMPLE = 0
- Runtime NOT_INTEGRATED

690107 当前状态：
- Contract v1.0.1-frozen
- final adversarial falsification + coverage repair PASS
- Provider ownership / suppression / lifecycle / cleanse / cross-state contract frozen
- stronger-vs-weaker FR remains BOUNDED_UNKNOWN
- Runtime NOT_INTEGRATED
- Battle mirror: stages/stage12/STAGE12_690107_FALSE_REPORT_RESEARCH_SYNC.md

Remaining research:
- 690108 PROVOCATION
- 690222 INTIMIDATION
- 690109 SABOTAGE
- 690110 CAPTURE

## Stage sequencing

    Stage12 = remaining official states / permission & composite control
    Stage13 = Assault runtime
    Stage14 = ordinary Active runtime
    Stage15 = preparation runtime
    Stage16+ = Passive / Command / Formation / Troop etc.

Research Wave does not renumber Project Stage, and Research FROZEN does not imply Runtime FROZEN.
