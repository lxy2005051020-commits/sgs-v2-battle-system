# Stage14 · Concrete Skill Integration

## 当前阵法实现（2026-10-13）

canonical registry已包含 **5个具体阵法**。本次将三个本地完成阵法整合到已含锋矢阵、武锋阵的最新基线，公开完整代码、原始来源快照、用户规则、测试与待核实项。

| ID | 阵法 | 已实现范围 |
|---|---|---|
| 20066 | 锋矢阵 | Lv10；已有main接入 |
| 20025 | 八门金锁阵 | Lv1–10；用户指定智力缩放及发动时快照 |
| 20178 | 箕形阵 | Lv10；用户指定武力缩放 |
| 22012 | 三势阵 | Lv1–10；用户确认平局及旧效果清除规则 |
| 22031 | 武锋阵 | Lv10完整模型；低等级仅显式副将模式 |

[本次同步记录与组合验证](FORMATION_COMPLETED_SYNC.md)。接入完成不代表客户端机制实证冻结；形一阵、潜龙阵、鱼鳞阵仍未实现。

## Historical Formation F0/F1 snapshot (2026-10-13)

**Stage14 F0 research and formation foundation have merged to both main branches.**

- Research F0-R: [PR #18](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/pull/18) MERGED; main snapshot `abd654a907019a16a61adefee97663b25b073dd2`.
- Battle F0-I-A: [PR #66](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/66) MERGED; main snapshot `2238186848fee6c89a9e688174f2fe64d382c1a0`.
- Battle merged-main [CI #38278028436](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38278028436): SUCCESS, `2239 passed`, demo PASS, Stage13-D1 frozen audit PASS, Qingzhou audit PASS.
- `SkillType.FORMATION` now has a real `PRE_BATTLE` scheduler, canonical admission and team exclusivity guard, speed/attacker order and provenance-based provider-death cleanup. At the F1 snapshot **formation Gameplay = 1 (Feng Shi Zhen 20066)**, merged through Battle PR #68 and verified on main.
- Completed **Stage14 F1: Feng Shi Zhen (20066)**. [Research contract](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/01_Skills/FENG_SHI_ZHEN_RESEARCH_CONTRACT.md) and [F1 preintegration plan](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/F1_FENG_SHI_ZHEN_PREINTEGRATION_READINESS.md).
- `PASSIVE -> FORMATION -> TROOP -> COMMAND` is USER_APPROVED simulator V1 scheduling; client prebattle logs contain counterexamples to universal four-stage order.
- 阵法携带者阵亡后所属持续效果立即失效；每队最多一个阵法；同速双方进攻方优先。均为用户批准的实现规则，不能标注为实证游戏事实。
- F1 [PR #68](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/68) MERGED (`975b44e6`); [F1 merged-main Actions #38280765590](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38280765590) SUCCESS (2267 pytest, Stage13-D1/Qingzhou audits, demo). [Gameplay 接入说明](FENG_SHI_ZHEN_INTEGRATION.md)。Lv1~9 模型仍 OPEN，F1 当前仅 Lv10。
- 兵种战法维持 `15/16`，象兵 `DEFERRED`。[象兵暂缓清单](XIANG_BING_PREPARATION.md)

**Historical note:** 以下旧版 Stage14 批次测试计数、候选状态与原路线描述属于原批次审计快照，不代表当前 F0/F1 状态。当前 F1 正式合并的 [Gameplay 接入记录](FENG_SHI_ZHEN_INTEGRATION.md) 和 [merged-main CI](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38280765590) 为当时F1阶段的依据；当前五阵法状态以上方同步记录为准。F0历史状态以上文merged-main CI为准。参见 [F0 historical readiness and exit](FORMATION_F0_RUNTIME_READINESS.md)。

丹阳兵接入见[丹阳兵接入说明](DAN_YANG_BING_INTEGRATION.md)：
生成比例按用户确认的1.0倍实现；全体统率+36，谋略抵挡36%／陶谦40%，每回合衰减10%。
初次发布入口为[PR #63](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/63)。用户后续指定[在场武将平均分配、进一法](DAN_YANG_BING_ALLOCATION_CORRECTION.md)，现在每人独立持有兵池；实际扣兵口径及细时序仍待战报验证。下方计数包含已合并的丹阳兵。

飞熊军接入见 [飞熊军用户指定模型](FEI_XIONG_JUN_INTEGRATION.md)：
满级受治疗提升16%／董卓主将20%，累计实际恢复H，两个目标各在最终伤害追加H/10，伤害期间恢复计入下一次。
状态为 USER_SPECIFIED_FINAL_ADDITIVE_MODEL / NOT_GAMEPLAY_FROZEN；完整战斗可运行。合并审计见 [飞熊军合并审计](FEI_XIONG_JUN_MERGE_AUDIT.md)，发布入口为 [PR #62](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/62)。下方计数包含该PR合并后的飞熊军。

> Status: **ACTIVE / MAINLINE GATE OPEN / 10 BOUNDED-FROZEN + 4 USER-PROVISIONAL + 1 USER-FIT INTEGRATION**

Stage14 在 Stage13 冻结的 Core Gameplay Engine 上进行具体战法接入。

## Current mainline state

~~~text
STAGE13_FINAL_EXIT_AUDIT = PASS
CORE_GAMEPLAY_ENGINE     = FROZEN
SKILL_RUNTIME_READINESS  = READY
STAGE14 MAINLINE GATE    = OPEN

TROOP SKILLS IN MAIN     = 15
USER-PROVISIONAL ADDITIONS = 20153 QING_ZHOU_BING / 20154 HU_WEI_JUN / 20247 FEI_XIONG_JUN / 20245 DAN_YANG_BING
USER-FIT ADDITION          = 20246 XIAN_DENG_SI_SHI
NEW BOUNDED ADDITIONS      = 20248 XIE_FAN_WEI / 20152 JIN_FAN_JUN
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
| 20246 (推断) | 先登死士 | USER_FIT_MODEL / OPENING_COMMAND_SNAPSHOT_FROZEN / GAMEPLAY_DETAILS_OPEN; [PR #55](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/55) |
| 20248 (推断) | 解烦卫 | BOUNDED_FROZEN / HAN_DANG_72 / FINE_LINEAGE_OPEN; [PR #57](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/57) |
| 20152 | 锦帆军 | BOUNDED_FROZEN / FORMULA_PLACEHOLDERS; [PR #60](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/60) |

| 20247 (待客户端核对) | 飞熊军 | USER_SPECIFIED_FINAL_ADDITIVE_MODEL / NOT_GAMEPLAY_FROZEN; [PR #62](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/62) |
| 20245 (待客户端核对) | 丹阳兵 | USER_CONFIRMED_EQUAL_SPLIT_CEIL / GAMEPLAY_DETAILS_OPEN; [PR #63](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/63) |

最终批次审计见 [Batch01-04 Mainline Audit](BATCH01_04_MAINLINE_AUDIT.md)。

## Research authority

Canonical Research contracts:

- [MC-STAGE14-TROOP-FOUNDATION-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)
- [MC-STAGE14-TROOP-BATCH01-04-BASELINE-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/STAGE14_BATCH01_04_BASELINE_FREEZE.md)
- [Troop question ledger](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_QUESTION_LEDGER.md)
- [MC-STAGE14-HUWEI-PROVISIONAL-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/01_Skills/%E8%99%8E%E5%8D%AB%E5%86%9B/HU_WEI_JUN_PROVISIONAL_CONTRACT.md)
- [MC-STAGE14-XIANDENG-USER-FIT-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/01_Skills/%E5%85%88%E7%99%BB%E6%AD%BB%E5%A3%AB/XIAN_DENG_SI_SHI_USER_FIT_CONTRACT.md)
- [MC-STAGE14-XIEFAN-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/01_Skills/%E8%A7%A3%E7%83%A6%E5%8D%AB/XIE_FAN_WEI_MECHANISM_CONTRACT.md)
- [MC-STAGE14-JIN-FAN-JUN-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/01_Skills/%E9%94%A6%E5%B8%86%E5%86%9B/JIN_FAN_JUN_MECHANISM_CONTRACT.md)

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

先登死士（20246 推断编号）本地模型接入见
[先登死士接入说明](XIAN_DENG_SI_SHI_INTEGRATION.md)。
采用用户给定的比例偷取模型、分段概率和开局携带者统率快照；叠层/到期等细节仍 OPEN。
该条目是独立分支本地状态，不表示已合入 main 或通过远端 CI。

用户明确授权的暂定模型可在Research独立合同中保留开放边界后接入；同样必须通过Runtime回归、独立审计和CI。
该接入不自动升级为客户端实证冻结，也不改写既有 bounded freeze。青州兵与虎卫军属于用户授权的暂定模型通道；先登死士属于 USER_FIT 模型通道，其中“携带者开局统率快照”已经由项目所有者确认并冻结，而零伤害触发、独立层到期等细节继续 OPEN。
