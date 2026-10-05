# Stage14 · Concrete Skill Integration

> Status: **ACTIVE / MAINLINE GATE OPEN / 8 BOUNDED-FROZEN + 2 USER-PROVISIONAL INTEGRATIONS**

Stage14 在 Stage13 冻结的 Core Gameplay Engine 上进行具体战法接入。

## Current mainline state

~~~text
STAGE13_FINAL_EXIT_AUDIT = PASS
CORE_GAMEPLAY_ENGINE     = FROZEN
SKILL_RUNTIME_READINESS  = READY
STAGE14 MAINLINE GATE    = OPEN

TROOP SKILLS IN MAIN     = 10
USER-PROVISIONAL ADDITIONS = 20153 QING_ZHOU_BING / 20154 HU_WEI_JUN
~~~

当前已进入 main：

| Skill ID | 战法 | 状态 |
|---|---|---|
| 20097 | 西凉铁骑 | MERGED / CI PASS |
| 20075 | 白马义从 | MERGED / CI PASS |
| 20098 | 虎豹骑 | MERGED / CI PASS |
| 20100 | 无当飞军 | MERGED / CI PASS |
| 20096 | 陷阵营 | MERGED / CI PASS |
| 20099 | 白毦兵 | MERGED / CI PASS |
| 20125 | 大戟士 | MERGED / CI PASS |
| 20095 | 藤甲兵 | MERGED / CI PASS |
| 20153 | 青州兵 | USER_PROVISIONAL_MODEL / CAO_CAO_PLACEHOLDER; [PR #52](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/52) |
| 20154 (推断) | 虎卫军 | USER_PROVISIONAL_MODEL / HEALING_ROLLBACK_FROZEN; [PR #53](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/53) |

最终批次审计见 [Batch01-04 Mainline Audit](BATCH01_04_MAINLINE_AUDIT.md)。

## Research authority

Canonical Research contracts:

- [MC-STAGE14-TROOP-FOUNDATION-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)
- [MC-STAGE14-TROOP-BATCH01-04-BASELINE-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/STAGE14_BATCH01_04_BASELINE_FREEZE.md)
- [Troop question ledger](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_QUESTION_LEDGER.md)
- [MC-STAGE14-HUWEI-PROVISIONAL-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/01_Skills/%E8%99%8E%E5%8D%AB%E5%86%9B/HU_WEI_JUN_PROVISIONAL_CONTRACT.md)

Shared frozen rules:

~~~text
special troop conversion = PRE_BATTLE
special troop restraint  = inherit base troop family
PRE_BATTLE visibility    = later skills read prior applied mutations
provider                 = holder-bound skill instance
temporary invalidation   != provider death
~~~

Batch01-04 使用 bounded freeze：

~~~text
confirmed baseline behavior  = FROZEN
explicit unresolved extension = OPEN / DEFERRED
~~~

因此，公孙瓒/曹纯/高顺等仍未关闭的缩放或细时序问题不会因为 Runtime 已进入 main 而被反向解释成“已实证”。

## Mainline audit result

~~~text
Research PR #10  = MERGED
Battle PR #46    = MERGED / merged-main CI SUCCESS
Battle PR #47    = MERGED / merged-main CI SUCCESS
Battle PR #48    = MERGED / merged-main CI SUCCESS
Battle PR #49    = MERGED / merged-main CI SUCCESS

Final pytest       = 1951 passed
Stage13-D1 audit   = PASS
Frozen owner drift = NONE DETECTED
~~~

## Reusable Stage14 seams now available

当前兵种战法接入已经形成以下复用能力：

- PRE_BATTLE troop admission / special troop conversion；
- typed Attribute Modifier；
- ACTIVE / ASSAULT activation-rate modifier；
- one-shot scheduled skill application；
- DOT 与来源有效性组合门控；
- First Aid / Recovery 复用；
- normal-attack followup；
- inherited actual-target followup；
- probabilistic combo adapter；
- incoming weapon-damage reduction provider；
- state-application reaction / associated-state lifecycle。

这些是 Runtime seam，不自动证明未来具体战法的玩法规则。

## Preserved open boundaries

仍明确保持 OPEN / DEFERRED：

- 白马义从公孙瓒速度缩放和“四回合”精确作用范围；
- 虎豹骑曹纯统领额外缩放；
- 陷阵营高顺统领统率缩放；
- 无当飞军开场中毒与其它首回合效果的更细相对顺序；
- 白毦兵 / 大戟士相对其它普攻派生效果的更细顺序及 lineage；
- 藤甲兵效果自身的特殊净化 / 免疫分类；
- 未进入 bounded Research freeze 的其它兵种战法机制。

## Mainline policy

青州兵（20153）新增接入采用用户授权的暂定模型，详见
[青州兵接入说明](QING_ZHOU_BING_INTEGRATION.md)。
`D/10`加在基础治疗量层，属性项为武力；曹操统领额外加成为空白占位。
该模型不计入上方八个已冻结兵种的实证冻结结果。

新的具体战法或机制家族进入 main 仍必须满足：

~~~text
GAME TRUTH / RESEARCH CONTRACT
-> RUNTIME REQUIREMENT MAP
-> IMPLEMENTATION
-> SKILL-SPECIFIC REGRESSION
-> FULL REGRESSION / DEMO
-> INDEPENDENT RUNTIME AUDIT
-> PR CI
-> MAINLINE MERGE
-> MERGED-MAIN CI
~~~

Battle code is not gameplay evidence.

用户明确授权的暂定模型可在Research独立合同中保留开放边界后接入；同样必须通过Runtime回归、独立审计和CI。
该接入不自动升级为客户端实证冻结，也不改写既有bounded freeze。青州兵与虎卫军均属于用户授权的暂定模型通道；虎卫军“治疗后增伤回落”已经单独由项目所有者确认并冻结。
