# CONFUSION Contract Audit

Status ID: `690103`  
Mechanism: `CONFUSION / 混乱`  
Audit Type: `Stage 9 Frozen Contract Independent Review`  
Audit Date: `2026-09-13`

> 本审计不重新从零研究混乱机制。审计目标仅为确认现有冻结合同的权威来源、内部闭环、跨冻结合同一致性、Stage 8 兼容性与 Stage 9 设计准入状态。

---

## 1. Repository Baseline

本轮读取的 exact `main` baseline：

```text
sgs-v2-battle-system
83a7a44374399efed01dacc1e869b724089201c4

sgs-state-mechanics-research
9d86e54c407913ff020bafacf8196085780b99c6
```

主战斗仓 Stage 9 正式入口：

```text
stages/stage9/
```

Stage 8 冻结参照：

```text
stages/stage8/STAGE8_FREEZE_RECORD.md
stages/stage8/STAGE8_DESIGN_FREEZE.md
```

Stage 8 已明确冻结，并明确将：

```text
confusion
taunt
guard / target redirect
combo
reaction queue
cleave
counterattack
share / split
chain
```

留在 Stage 9 或后续阶段，不属于 Stage 8 Damage Pipeline 内部职责。

### 1.1 AUTHORITATIVE_SOURCE_MAP

本轮在开始 CONFUSION 审计前，对九个 Stage 9 核心机制建立如下 P0 源映射：

| Mechanism | Current P0 authoritative source | Mirror / secondary P0 note | Blob SHA |
|---|---|---|---|
| `690103 CONFUSION` | `stages/stage9/research/core_arbitration_v2/confusion/MECHANISM_CONTRACT.md` | 与状态仓 `states/control/confusion/MECHANISM_CONTRACT.md` byte-level 一致 | `a7fb21cb5bf0afad8d3cb4d5e32fea464414c259` |
| `690106 TAUNT` | `stages/stage9/research/core_arbitration_v2/STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md` | P1: `STAGE9_TAUNT_FINAL_CONSISTENCY_AUDIT.md` | `d3c370a2f693a03ff4f435e8750678264348fc0d` |
| `690098 GUARD` | `stages/stage9/STATE_690098_GUARD_MECHANISM_CONTRACT.md` | 与状态仓 `states/functional/guard/MECHANISM_CONTRACT.md` byte-level 一致 | `a496d3e006b3945cf97cd431e0d0d9162aec8653` |
| `690081 COMBO` | 状态仓 `states/functional/combo/MECHANISM_CONTRACT.md` | 主战斗仓当前未发现等价最新 P0 镜像合同 | `2cc1f658a223a334e386a0251dcc45205047b547` |
| `690084 CLEAVE` | `stages/stage9/research/core_arbitration_v2/STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` | 最新专项 Freeze Record | `e1a70b82afc1246b9ecdb506d823deb85cb18f7a` |
| `690097 CHAIN_LINK` | `stages/stage9/research/core_arbitration_v2/STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md` | 最新专项 Freeze Record | `4764c3ebebd525f74ab76f54694733c217eaaa90` |
| `690087 DAMAGE_SHARE` | `stages/stage9/research/core_arbitration_v2/STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md` | 状态仓另有 `states/functional/damage_share/MECHANISM_CONTRACT.md`；语义同步关系留待该机制独立审计 | `012ba3a4b68f5e44fb1f6381a1ebddd2d48209f3` |
| `690086 DISTRIBUTION` | `stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md` | 最新专项 Freeze Record | `c1df3fe35a80bd9ee22024b88e156cc75c92f60b` |
| `690085 COUNTERATTACK` | `stages/stage9/research/core_arbitration_v2/STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md` | 最新专项 Freeze Record | `5db49f4a9fa7088d9d980b50e75194a994119cc9` |

该表仅建立权威入口，不替代后续八个机制自己的独立合同审计。

---

## 2. Authoritative Freeze Source

### 2.1 P0 Contract

CONFUSION 当前正式合同：

```text
主战斗仓：
stages/stage9/research/core_arbitration_v2/confusion/MECHANISM_CONTRACT.md

状态研究仓：
states/control/confusion/MECHANISM_CONTRACT.md
```

两文件：

```text
blob SHA = a7fb21cb5bf0afad8d3cb4d5e32fea464414c259
```

因此为 **byte-level identical mirror**，不存在跨仓正文漂移。

状态研究仓合同冻结 commit：

```text
89a00645ce042f7bcf6bb88f4ff4a12b04f36dc5
docs: freeze 690103 confusion mechanism contract
```

主战斗仓当前正式路径的最近 commit 为阶段目录重构：

```text
83a7a44374399efed01dacc1e869b724089201c4
chore: organize stage artifacts into dedicated stage folders
```

该 commit 明确为路径迁移/资料重构，不改变合同 blob 内容。

### 2.2 P1 Freeze Audit

两仓对应：

```text
FREEZE_AUDIT.md
blob SHA = a1866e4f66e2ae3c1b7cdbf8bc1ee56e38e0320a
```

同样 byte-level 一致。

状态研究仓 Freeze Audit commit：

```text
9c650e5c4e9d16779fbc7ba3d858ca8374fd8ca0
docs: add 690103 confusion freeze audit
```

其原审计结论：

```text
PASS / FROZEN
BLOCKER = 0
MAJOR = 0
Implementation-blocking unresolved = 0
```

### 2.3 Authority Decision

```text
AUTHORITATIVE CONTRACT
= MECHANISM_CONTRACT.md @ blob a7fb21cb...

AUTHORITATIVE FREEZE AUDIT
= FREEZE_AUDIT.md @ blob a1866e4f...
```

两仓镜像不是冲突版本。

---

## 3. Superseded / Stale Sources

### 3.1 Superseded skeleton

状态研究仓：

```text
states/control/minimum_usable/690103_CONFUSION.md
```

仅为历史 `MINIMUM_USABLE` skeleton，优先级低于现有 P0/P1，不能覆盖正式合同。

状态：

```text
SUPERSEDED
```

### 3.2 `core_arbitration_v2/README.md`

当前仍写：

```text
Next Core Research Target:
690103 CONFUSION
```

并在“仍待研究 / 审计”中继续列出：

```text
690103 CONFUSION core mechanics research
690081 COMBO core mechanics research
```

但两者已有正式 FROZEN contract。

状态：

```text
STALE / DOC_DRIFT
```

### 3.3 `STAGE9_EVIDENCE_MATRIX_V2.md`

与 CONFUSION 直接相关的历史项仍使用低级别状态：

```text
EM-01 混乱 × 嘲讽：历史 A；仍受提取器最终审计约束
EM-26 混乱即时判定：历史 A
```

这些不能覆盖后续 CONFUSION P0 合同与 P1 Freeze Audit。

状态：

```text
STALE FOR FREEZE STATUS
VALID AS HISTORICAL EVIDENCE TRACE
```

### 3.4 R2 / R6 / R7

- R2 已修订为“TargetSelector preemption != lifecycle suppression”，与 P0 合同一致。
- R6 的“其他控制状态更强覆盖未知”不能覆盖 CONFUSION 已冻结的 single-instance hard reject。
- R7 关于官方 PRNG 不可观察的限制仍成立；但 CONFUSION 后续 P0 已冻结“保留原 Selection Strategy”，不能再用旧统计不确定性降低合同状态。

### 3.5 Duplicate / Mirror classification

```text
CONFUSION main contract ↔ state-research contract
= DUPLICATE MIRROR / BYTE-IDENTICAL / CONSISTENT

CONFUSION main Freeze Audit ↔ state-research Freeze Audit
= DUPLICATE MIRROR / BYTE-IDENTICAL / CONSISTENT
```

不是冲突副本。

---

## 4. State Kernel Audit

冻结 kernel：

```text
CONFUSION
= TargetSelector Side-Constraint Suppressor
```

精确语义：

```text
REMOVE:
  Side Predicate only

PRESERVE:
  Alive Constraint
  Self Include / Exclude
  Target Count
  Identity Predicate
  Attribute Predicate
  Relationship Anchor
  Ordering Rule
  Random Sampling Rule
  Skill-specific Predicate
```

因此：

```text
CONFUSION
!= RandomTargetOverride
!= TargetPoolRebuilder
!= IgnoreAllTargetRules
```

### Kernel consistency

- 随机单体：扩大合法池后继承原等权随机单体策略；不增加“先随机阵营”层。
- 随机多体：保留原 Target Count 与无放回抽样；不增加阵营配额。
- 排序/极值：只移除阵营谓词，继续执行原 ArgMin / ArgMax / Sorting。
- 固定关系锚点：`source.team.commander` 一类关系语义不是普通 Side Predicate，不受混乱改写。
- Self eligibility：由原 Selector 决定；混乱本身既不新增 self，也不删除 self。

Result：

```text
PASS
```

---

## 5. Lifecycle Audit

| Lifecycle Item | Frozen behavior | Audit |
|---|---|---|
| Apply | 免疫 Gate 通过后创建实例，并立即对后续 JIT Target Selection 可见 | PASS |
| Active | 成功创建后立即 ACTIVE | PASS |
| Duration | `OWNER ACTION WINDOW` 计时 | PASS |
| Tick | `Owner Action Window End` 消耗 `remainingTurns -= 1` | PASS |
| Refresh | 不允许 | PASS |
| Reject | 只要旧实例物理存在，新混乱 Hard Reject；`remainingTurns == 0` 仍拒绝 | PASS |
| Replace | 不允许 | PASS |
| Suppress | 合同未建立 CONFUSION 自身 `SUPPRESSED` 生命周期 | N/A |
| Resume | 无 CONFUSION `SUPPRESSED` 状态，因此无 Resume | N/A |
| Purge | 成功净化时立即物理删除；同一 Action Window 后续选择立即恢复正常 | PASS |
| Expire | 下一次 `Owner Action Start` 检查 `remainingTurns <= 0` 后物理删除，再进入行动逻辑 | PASS |
| Source Death | 来源死亡不删除、不禁用、不改剩余时间；来源仅保留 provenance | PASS |
| Holder Death | 一般死亡规则与后续 COMBO Frozen actor-death exception 存在正式合同冲突，见 §10 | **BLOCKER** |
| Battle End | 随 Battle Runtime / state container 整体销毁；合同无独立战斗中规则 | N/A / GLOBAL |

除 Holder Death 交叉边界外，生命周期内部闭环完整。

---

## 6. Trigger Audit

冻结触发语义：

```text
Trigger Event
= EACH ACTUAL TARGET SELECTION

Trigger Timing
= JIT at TargetSelector resolution

Trigger Owner
= current actor / CONFUSION holder performing that selection

Trigger Target
= selector candidate legality layer; no pre-bound target is required

Trigger Frequency
= PER ACTUAL TARGET SELECTION

Snapshot vs Live Read
= LIVE READ / NO SNAPSHOT
```

明确不是：

```text
PER ACTION
PER ROUND
PER SKILL START
PER PREPARATION START
PER DAMAGE INSTANCE
```

准备型战法：

```text
Prepare Start
→ no target snapshot

Actual Resolve
→ new TargetSelector call
→ JIT current CONFUSION
```

已经完成的 Target Selection 不被后续状态变化追溯重写。

Result：

```text
PASS
```

---

## 7. Target Identity Audit

Stage 9 当前目标身份必须区分：

```text
pre_redirect_target
post_redirect_attack_target
damage_recipient(s)
derived_target
```

CONFUSION 所在阶段：

```text
Target Selection
→ CONFUSION may modify candidate legality
→ pre_redirect_target / originalTarget determined

Post-selection Target Resolution
→ GUARD may redirect
→ post_redirect_attack_target / actualTarget determined

Damage settlement
→ SHARE / DISTRIBUTION may expand damage_recipient(s)

Derived mechanisms
→ CLEAVE / COUNTER / CHAIN use their own frozen target semantics
```

### Important self-target edge

CONFUSION 保留普通攻击原有 `EXCLUDE_SELF`，因此它本身不会让标准普攻 Selector 直接选自己。

但：

```text
CONFUSION selects friendly holder B
→ B has GUARD provider == attacker A
→ GUARD redirects actualTarget to A
```

此时出现 `attacker == post_redirect_attack_target` 并不违反 CONFUSION self rule，因为 self-target 是后置 Guard 重定向产生，不是 CONFUSION Selector 直接选择。

与 R2 / GUARD contract 一致。

Result：

```text
PASS
```

---

## 8. Damage / Resolution Pipeline Audit

CONFUSION 自身不创建 Damage Instance，不定义伤害公式，不创建派生扣兵。其职责止于 Target Selection legality。

| Pipeline Stage | CONFUSION contract result |
|---|---|
| Formula | INHERITED |
| Crit | INHERITED |
| Weakness | INHERITED |
| Damage Modifier | INHERITED |
| Evasion | INHERITED |
| Resistance / Barrier | INHERITED |
| Share | INHERITED after final actual damage target is established |
| Distribution | INHERITED after final actual damage target is established |
| Chain | INHERITED from resulting legal Damage Instance |
| FirstAid | INHERITED |
| Counter | INHERITED from `ON_NORMAL_ATTACK_RECEIVED` of final actual attack target |
| Lifesteal | INHERITED by resulting damage kind |
| StrategyRecovery | INHERITED by resulting damage kind |
| Troop Loss | INHERITED |
| Damage Statistics | INHERITED |

关键约束：

```text
CONFUSION must not re-run, skip, or duplicate Stage 8 damage stages.
CONFUSION only changes who enters downstream target / attack resolution.
```

Result：

```text
PASS
```

---

## 9. Reaction / Recursion Audit

CONFUSION 不是 Damage / Reaction source，因此不存在类似：

```text
CONFUSION → CONFUSION damage recursion
```

的递归路径。

其关键递归边界是“是否产生新的 Target Selection”：

```text
new TargetSelector call
→ JIT CONFUSION applies

parent target inheritance / locked actualTarget
→ no new selector
→ CONFUSION does not re-run
```

### Cross with standard NormalAttack / Combo

COMBO #2 是新的标准 `NormalAttackInstance`：

```text
NormalAttack #2
→ new Target Selection
→ CONFUSION JIT re-evaluated
```

这与 CONFUSION 的 `PER ACTUAL TARGET SELECTION` 合同一致。

但若 actor 在自己的 open Action 中已经死亡，现有两个 P0 合同对“状态是否已被清空 / Action 是否仍继续”冲突，见 §10。

### R4 compatibility

R4 中 Cleave / Chain / Share / Counter 的 permission matrix 不被 CONFUSION 改写。CONFUSION 只影响上游目标选择，不赋予任何派生伤害新的递归资格。

Result：

```text
PASS, EXCEPT death-cross-state blocker in §10
```

---

## 10. Death / Termination Audit

### 10.1 Source death

CONFUSION P0：

```text
source dies
→ existing CONFUSION remains
→ remainingTurns unchanged
→ source provenance retained
```

与状态托管模型一致。

Result：`PASS`。

### 10.2 Ordinary holder / target death

CONFUSION `MECHANISM_CONTRACT.md` §3.11 与 Strong Invariant `I-07` 当前写为：

```text
TARGET_DEATH
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_STATE_RESOLUTION
→ ABORT_REMAINING_ACTION
→ REJECT_FUTURE_STATE_APPLICATION
```

其 P1 `FREEZE_AUDIT.md` §5.9 也按这一通用 hard-termination baseline 判定 PASS。

对于非“当前行动者自身已经打开 Action”的普通死亡场景，该规则可与项目死亡基线兼容。

### 10.3 Newer COMBO FROZEN actor-death exception

更晚冻结的 `690081 COMBO / 连击` P0 合同，commit：

```text
10226e9afa627eadfc447cb8b0ee5613a15eadc5
docs(combo): freeze 690081 combo mechanism contract
```

明确冻结：

```text
ACTOR_DEATH_DURING_OWN_OPEN_ACTION
→ 当前 cfg 175 → cfg 733 Action 不被提前截断
→ existing StatusSlot 不即时清空
→ reject new status application to dead actor
→ current action may continue producing external effects
→ actor removed from future scheduling
```

并有专门边界：

```text
第一击反应链中 actor 死亡
→ 仍可进入 Combo Checkpoint
→ 仍可 cfg 230
→ 仍可执行第二次标准普通攻击
```

### 10.4 Direct frozen-contract collision

两个正式 P0 合同在以下交集产生不同语义：

```text
actor holds CONFUSION
+
actor is in own already-open Action
+
NormalAttack #1 reaction kills actor
+
COMBO allows NormalAttack #2 to continue
+
NormalAttack #2 needs a fresh Target Selection
```

CONFUSION 当前合同字面执行：

```text
death
→ CLEAR_ALL_STATES
→ ABORT_REMAINING_ACTION
```

则：

```text
NormalAttack #2 cannot exist
or CONFUSION is no longer present for its selector
```

COMBO 当前合同执行：

```text
death
→ keep current Action alive
→ keep existing StatusSlot physically present
→ NormalAttack #2 can exist
```

但当前正式资料没有在 CONFUSION P0 中显式冻结：

```text
死亡但仍处于 own-open-action 的 actor
其既有 CONFUSION 在后续 Target Selection 是否仍 operational
```

这会直接改变第二击合法候选池和目标结果。

因此这不是 README/INDEX 级漂移，而是：

```text
TWO FORMAL FROZEN CONTRACTS OVERLAP WITH DIFFERENT TERMINATION SEMANTICS
```

### 10.5 Severity

依据 Stage 9 本轮审计分级规则：

```text
BLOCKER
```

原因：两个 P0 FROZEN 合同直接冲突，且交集会导致不同战斗结果。

### 10.6 Required narrow reopen scope

只允许重新打开以下狭窄问题：

```text
CONFUSED_ACTOR_DEATH_DURING_OWN_OPEN_ACTION
```

需要最终冻结：

```text
1. CONFUSION §3.11 / I-07 是否显式排除 actor-death-during-own-open-action；
2. existing CONFUSION slot 在该 open Action 的剩余 Target Selection 中是否仍 operational；
3. Action End 后死亡实体的 CONFUSION 如何进入静默作废 / runtime cleanup。
```

不需要重开：

```text
Side Predicate kernel
Duration model
Reapplication
Purge
Source death
Prepared skill JIT
Confusion × Taunt
Confusion × Guard
Random single / multi selector semantics
```

也不应重新扫描全部战报。仅在现有 Combo 死亡证据不能回答“Confusion operationality”时，才需要针对该交集做定向证据补充。

---

## 11. RNG / Determinism Audit

P0 冻结的可观察行为：

```text
CONFUSION modifies candidate legality only.
Selection Strategy is preserved.
```

因此：

```text
original selector = equal-weight random single
→ confusion expands legal pool
→ same equal-weight random single strategy

original selector = without-replacement random multi
→ same without-replacement strategy

original selector = ArgMin / ArgMax / sorted
→ no RNG added by CONFUSION
```

工程 RNG 合同：

```text
CONFUSION itself must not add an extra camp roll.
Only the underlying selector consumes project RandomSystem according to its own contract.
```

禁止宣称：

```text
官方内部必定调用 PRNG X 次
官方 seed / stream / call count 已被还原
```

官方内部 PRNG 仍为 `UNKNOWN`；这不影响 CONFUSION 外部冻结语义。

Result：

```text
PASS
```

---

## 12. Provenance Audit

必须区分三层：

### A. 原始战报直接字段

原生日志只提供平铺事件字段，例如：

```text
cfg_id
args
args_raw
desc
full_desc
not_show
key
```

### B. 事件流重构

以下关系来自时序/定界符重构，不是官方字段：

```text
parent relationship
root action relationship
Target Selection causal chain
```

### C. 模拟器工程字段

CONFUSION 合同中的：

```text
TargetSelector
SidePredicate
ActionWindow
active_states
originalTarget
actualTarget
pre_redirect_target
post_redirect_attack_target
```

均为项目工程术语。

合同开头已经明确不宣称这些是官方源码类名/字段名。

Result：

```text
PASS
```

---

## 13. Cross-Mechanism Consistency

| Cross Item | Verdict | Reason |
|---|---|---|
| `CONFUSION × TAUNT` | `CONSISTENT` | 两个 P0 均冻结 `ConfusionTargetSelector > TauntTargetSelector > DefaultTargetSelector`；混乱是 selector shadowing，不把 TauntInstance 切成 SUPPRESSED |
| `CONFUSION × GUARD` | `CONSISTENT` | CONFUSION 决定 `originalTarget / pre_redirect_target`；GUARD 位于后置 Target Resolution，可改写 `actualTarget / post_redirect_attack_target` |
| `CONFUSION × COMBO` | `CONFLICT` | 存活 actor 的每击 JIT 语义一致；但 actor 在 own-open-action 中死亡时，CONFUSION hard-clear/abort 与后冻结 COMBO keep-action/keep-status-slot 规则冲突 |
| `CONFUSION × CLEAVE` | `NOT APPLICABLE` | Cleave 使用已锁定的普通攻击实际目标作为派生锚点；不创建新的 CONFUSION selector 规则 |
| `CONFUSION × CHAIN_LINK` | `NOT APPLICABLE` | Chain 为 Damage Instance 后派生反馈，不重新进入 attacker TargetSelector |
| `CONFUSION × DAMAGE_SHARE` | `NOT APPLICABLE` | Share 在 final actual damage target 后做 damage partition，不回读 original side selector |
| `CONFUSION × DISTRIBUTION` | `NOT APPLICABLE` | Distribution 属于 Damage Instance 内部 partition；不重开 CONFUSION selection |
| `CONFUSION × COUNTERATTACK` | `CONSISTENT` | Counter 由最终实际承受普通攻击的实体触发，对 original attacker 产生反击；Confusion 不改写 Counter target |

Cross-state result：

```text
1 CONFLICT
3 CONSISTENT
4 NOT APPLICABLE
0 UNKNOWN
```

---

## 14. Stage8 Compatibility

CONFUSION 属于：

```text
A. Stage8 之前
= Target Selection / action orchestration layer
```

Stage 8 `STAGE8_DESIGN_FREEZE.md` 已明确：

```text
Stage 8 must not implement confusion / taunt / guard / target redirect / combo
```

因此正确适配方式为：

```text
Stage 9 TargetSelector / action orchestration
→ determine target identities
→ build downstream DamageRequest using resolved runtime participants
→ enter unchanged Stage 8 Damage Pipeline
```

CONFUSION 不要求：

```text
修改 DamageSystem.calculate
修改 Stage 8 formula topology
让 DamageModifierSystem 参与目标选择
让 EventBus 反向驱动伤害规则
```

结论：

```text
FORMAL STAGE8 REOPEN REQUIRED = NO
```

当前 BLOCKER 仅属于 Stage 9 跨状态死亡合同协调，不是 Stage 8 freeze-breaking defect。

---

## 15. Documentation Drift

### 15.1 CONFUSION direct drift

| File | Stale statement | Correct status | Repair needed |
|---|---|---|---|
| `stages/stage9/research/core_arbitration_v2/README.md` | `Next Core Research Target = 690103 CONFUSION` | CONFUSION 已有 P0 contract + P1 Freeze Audit；本次独立审计仅发现死亡交叉 blocker | YES |
| `stages/stage9/research/core_arbitration_v2/README.md` | “仍待研究”继续列 CONFUSION / COMBO | 两者都已有 FROZEN contract | YES |
| `STAGE9_EVIDENCE_MATRIX_V2.md` EM-01 | 混乱×嘲讽仍受提取器最终审计约束 | 已被 CONFUSION + TAUNT P0 双重冻结 | YES |
| `STAGE9_EVIDENCE_MATRIX_V2.md` EM-26 | 混乱即时判定仅标“历史 A” | P0 已冻结 `EACH ACTUAL TARGET SELECTION / JIT` | YES |
| 状态仓 `README.md` | “当前第一个研究对象 = COMBO” | COMBO 已 FROZEN；CONFUSION 也已 FROZEN | YES |
| 状态仓 `README.md` Target Death | 仍只写无条件 Hard Termination | 状态仓 `STATE_MECHANICS_INDEX.md` 已追加 Combo actor-death scope correction | YES |

### 15.2 Baseline-wide drift detected before this audit

以下不是 CONFUSION 机制 blocker，但已在本轮预扫描中确认，应在对应机制独立审计时处理：

| File | Current stale state | Newer authority |
|---|---|---|
| `STATE_MECHANICS_INDEX.md` | TAUNT = `MINIMUM_USABLE` | TAUNT Freeze Record = FROZEN |
| `STATE_MECHANICS_INDEX.md` | CLEAVE = `MINIMUM_USABLE` | Cleave Freeze Record = FROZEN |
| `STATE_MECHANICS_INDEX.md` | COUNTERATTACK = `MINIMUM_USABLE` | Counterattack Freeze Record = FROZEN |
| `STATE_MECHANICS_INDEX.md` | DISTRIBUTION = `MINIMUM_USABLE` | Distribution Freeze Record = FROZEN |
| `STATE_MECHANICS_INDEX.md` | CHAIN_LINK = `MINIMUM_USABLE` | Chain Freeze Record = FROZEN |
| `STAGE9_EVIDENCE_MATRIX_V2.md` EM-11 | Counter → Counter = PENDING | Counterattack Freeze = BLOCKED / FROZEN |
| `STAGE9_EVIDENCE_MATRIX_V2.md` Share rows/current status | Share math / death / “NEXT RESEARCH” remain historical | Damage Share Freeze Record = FROZEN |
| `STAGE9_EVIDENCE_MATRIX_V2.md` EM-25 | Combo remains historical B+/strong | COMBO P0 contract = FROZEN |

### 15.3 Duplicate contract status

```text
CONFUSION main ↔ state research
= BYTE-IDENTICAL MIRROR
= NO CONFLICT

GUARD main ↔ state research
= BYTE-IDENTICAL MIRROR
= NO CONFLICT

DAMAGE_SHARE main Freeze Record ↔ state contract
= both P0-class sources exist
= semantic-level reconciliation deferred to DAMAGE_SHARE dedicated audit
```

### 15.4 Main-repo COMBO sync gap

主战斗仓当前未发现状态仓最新：

```text
states/functional/combo/MECHANISM_CONTRACT.md
```

的等价 P0 正式镜像文件；同时主仓 `core_arbitration_v2/README.md` 仍把 COMBO 列为待研究。

判定：

```text
DOC_DRIFT / CROSS-REPO SYNC GAP
```

不等于 COMBO 机制未冻结。

---

## 16. Findings

### BLOCKER — CFS9-B01

**CONFUSION holder-death hard termination 与更新的 COMBO actor-death-during-own-open-action FROZEN exception 直接冲突。**

冲突范围：

```text
CONFUSION §3.11
CONFUSION Strong Invariant I-07
CONFUSION FREEZE_AUDIT §5.9

vs

COMBO §18 / §19 actor death contract
```

影响：

```text
死亡 actor 是否继续当前 Action
existing CONFUSION 是否仍在状态槽
后续 Combo NormalAttack #2 Target Selection 是否继续应用 CONFUSION
```

该差异会改变合法候选池与实际攻击目标，因此属于战斗结果级冲突。

要求：

```text
NARROW REOPEN REQUIRED
```

仅重新冻结死亡交集，不重做 CONFUSION 全机制研究。

### DOC_DRIFT — CFS9-D01

`core_arbitration_v2/README.md` 仍把 CONFUSION / COMBO 写为待研究。

### DOC_DRIFT — CFS9-D02

`STAGE9_EVIDENCE_MATRIX_V2.md` 的 CONFUSION 相关行仍停留在历史证据等级，未同步 P0/P1 冻结状态。

### DOC_DRIFT — CFS9-D03

状态研究仓根 `README.md` 的研究对象与 Target Death 通用基线落后于最新合同/索引。

### DOC_DRIFT — CFS9-D04

主战斗仓缺少最新 COMBO P0 合同镜像，且 Stage 9 README 体系未同步其 FROZEN 状态。

### HARDENING

无影响 Stage 9 设计语义的 CONFUSION hardening finding。

### Severity Summary

```text
BLOCKER   = 1
MAJOR     = 0
MINOR     = 0
DOC_DRIFT = 4
HARDENING = 0
```

---

## 17. Final Verdict

```text
VERDICT = REOPEN REQUIRED
```

原因严格限定为：

```text
两个正式 FROZEN P0 合同
在 ACTOR_DEATH_DURING_OWN_OPEN_ACTION 交集上存在直接冲突
```

这不是：

```text
CONFUSION kernel 未研究清楚
TargetSelector 规则不确定
Taunt / Guard 顺序未知
Stage8 无法兼容
README 状态落后
```

因此不得重新扫描全部战报、不得推翻 CONFUSION 已冻结的其他 15+ 条核心规则。

### Reopen boundary

只需要关闭：

```text
CONFUSED_ACTOR_DEATH_DURING_OWN_OPEN_ACTION
```

并在完成后同步修订：

```text
1. CONFUSION MECHANISM_CONTRACT §3.11
2. Strong Invariant I-07
3. CONFUSION FREEZE_AUDIT §5.9 / cross-contract section
4. core_arbitration_v2 README / Evidence Matrix
5. 状态研究仓对应 byte-identical mirror
```

在该 blocker 正式关闭前：

```text
690103 CONFUSION
NOT ADMITTED AS CONTRACT-READY FOR STAGE9 DESIGN
```

但除该死亡交集外：

```text
State Kernel        = READY
Lifecycle           = READY except death overlap
Trigger             = READY
Target Identity     = READY
Damage Boundary     = READY
Taunt Interaction   = READY
Guard Interaction   = READY
RNG Boundary        = READY
Provenance          = READY
Stage8 Compatibility= READY
```
