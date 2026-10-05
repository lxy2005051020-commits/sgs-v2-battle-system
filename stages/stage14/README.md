# Stage14 · Concrete Skill Integration

藤甲兵满级统率减伤与独立“藤甲兵效果”已在本地独立分支实现并验证。
持续时间与原灼烧同步，成功净化原灼烧会连带移除藤甲兵效果；未合并 main。见 [藤甲兵实现说明](TENG_JIA_BING_REDUCTION.md)。

> Status: **ACTIVE / MAINLINE GATE OPEN**

Stage14 begins concrete skill integration on top of the frozen Stage13 core gameplay engine.

## Entry gate

```text
STAGE13_FINAL_EXIT_AUDIT = PASS
CORE_GAMEPLAY_ENGINE     = FROZEN
SKILL_RUNTIME_READINESS  = READY
STAGE14 MAINLINE GATE    = OPEN
```

Stage14 no longer waits on the Stage13 exit gate.

## Research foundation

Canonical Research authority:

- [MC-STAGE14-TROOP-FOUNDATION-01](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)
- [Troop question ledger](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_QUESTION_LEDGER.md)

Frozen shared rules:

```text
special troop conversion = PRE_BATTLE
special troop restraint  = inherit base troop family
PRE_BATTLE visibility    = later skills read prior applied mutations
provider                 = holder-bound skill instance
temporary invalidation   != provider death
```

## Mainline policy

A concrete skill or mechanism-family batch may enter `main` only when its own gates pass:

```text
selected skill/family Research Contract         = CLOSED/FROZEN
runtime seam mapping                             = REVIEWED
implementation                                   = COMPLETE
skill-specific regression                        = PASS
full regression / demo                           = PASS
independent runtime audit                        = PASS
PR CI                                            = PASS
```

Future functionality must extend existing canonical owners where possible. A concrete skill must not invent gameplay truth from Battle code.

## First pilot: 西凉铁骑

西凉铁骑 is the first Stage14 vertical pilot.

Current Research status:

```text
BASE_XILIANG_MECHANISM_CONTRACT = FROZEN
MATENG_COMMANDER_SCALING        = FROZEN
```

`西凉铁骑` Runtime 已通过 Battle PR #42 正式合并进入 `main`。

The pilot exercises:

```text
SkillType.TROOP
-> PRE_BATTLE special troop conversion
-> base-family restraint inheritance
-> team-wide temporary crit state
-> current PRE_BATTLE AttributeSystem speed read
-> Ma Teng commander scaling
-> provider identity / invalidation lifecycle
-> duration expiry
-> BattleEngine automatic PRE_BATTLE wiring
```

It intentionally avoids unresolved storage/battery families represented by 象兵、飞熊军、丹阳兵.

### Mainline result

```text
Battle PR #42        = MERGED
Merge SHA            = 3fcf19cafdbe457c704e2fda83aadaddcb7f476a
Merged-main CI       = 37273312132 / SUCCESS
Runtime Integration  = COMPLETE
```

西凉铁骑是 Stage14 第一只正式进入 `main` 的兵种战法。

## Batch policy after the pilot

Bulk TROOP integration is allowed only by mechanism family after the relevant shared contract is frozen.

Examples:

```text
simple/static troop skills
-> reusable Stage14 batch lane

trigger-driven troop skills
-> Trigger Family contract first
-> then batch integration

storage / delayed-settlement troop skills
-> Storage Family contract first
-> then integration
```

A skill that requires a new Core primitive leaves the batch lane and receives focused research/runtime review.

## Runtime rule

### Batch 02 implementation

无当飞军 + 陷阵营的满级分支已在 `stage14-troop-batch-02` 实现并通过本地验证，
依赖第一批分支。无当使用用户指定伤害率公式，王平主将扩展为敌军全体；
陷阵营高顺增强保持空白占位。此记录不表示已经进入 main。
详见 [Batch02](BATCH02_WUDANG_XIANZHEN.md) 与 [验证记录](batch02/VALIDATION.md)。

### Local batch 01 implementation

白马义从 + 虎豹骑的满级基础分支已在 `stage14-troop-batch-01` 本地完成并通过验证。
此条目仅描述该分支，不表示两个战法已进入 main。
用户指定统领属性缩放延期，保持空白占位。白马统领四回合的作用范围仍待确认。
实现、证据与门禁详见 [Batch01](BATCH01_BAIMA_HUBAO.md) 和
[验证记录](batch01/VALIDATION.md)。

Battle code is not evidence.

The integration sequence is:

```text
GAME TRUTH
-> SKILL CONTRACT
-> RUNTIME REQUIREMENT MAP
-> IMPLEMENTATION
-> REGRESSION
-> INDEPENDENT AUDIT
-> MAINLINE MERGE
```

## 第三批本地实现：白毦兵 + 大戟士

满级基础分支、陈到/张郃统领分支及概率连击已在 `stage14-troop-batch-03` 接入。
依赖第二批 PR #47；本批为草稿审阅，不宣称两个独立机制合同已冻结或进入 main。
专测 161 passed，全量 1905 passed，Stage13-D1 frozen owner 哈希检查通过。
来源、组件树、验证范围与待裁决项见 [BATCH03_BAIER_DAJI.md](BATCH03_BAIER_DAJI.md)
和 [batch03/VALIDATION.md](batch03/VALIDATION.md)。
