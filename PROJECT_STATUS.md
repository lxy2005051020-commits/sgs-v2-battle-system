# 三国志战略版战斗模拟器 V2 · 当前阶段状态

> 本文件维护当前阶段状态、正式审计文件与封版验证基线。长期阶段规划仍以 `PROJECT_ROADMAP.md` 为准；具体阶段合同以对应 `STAGEX.md` 与 `STAGEX_FINAL_AUDIT.md` 为准。

---

# 当前状态

```text
Stage 1 基础运行模型       ✅ 回归稳定
Stage 2 BattleSystem      ✅ FROZEN
Stage 3 BattleState       ✅ 稳定
Stage 4 官方状态接入       ✅ FROZEN
Stage 5 Effect            ✅ FROZEN
Stage 6 Skill Runtime     ✅ FROZEN
Stage 7 Trigger/Recovery  ✅ FROZEN
Stage 8 Damage Pipeline   ✅ FROZEN
Stage 9+                  ⏳ NOT STARTED / READY FOR DESIGN
```

Stage 8 已完成 Final Audit、S8-RN-01 docs-only closure、main 合并、main exact-head pytest / demo / GitHub Actions / artifact provenance 与最终 freeze docs/status，因此正式进入 `FROZEN`。Stage 9 尚未开始，但现在可以按新的独立阶段合同进入设计流程。

---

# Stage 4 封版基线

```text
commit:
e4afe4d2b23645a3843f4943716caa0c3e424624

pytest -q:
80 passed

demo.py:
success

GitHub Actions:
success
```

正式审计：`stages/stage4/STAGE4_FINAL_AUDIT.md`

状态：`✅ FROZEN`

---

# Stage 5 封版基线

```text
final implementation verification:
33f0885fe8201955b12cd6cee00facc20984fe26

pytest -q:
105 passed

demo.py:
success

GitHub Actions:
success
```

正式施工文档：`stages/stage5/STAGE5.md`

正式审计：`stages/stage5/STAGE5_FINAL_AUDIT.md`

状态：`✅ FROZEN`

---

# Stage 6 封版基线

正式施工文档：`stages/stage6/STAGE6.md`

正式审计：`stages/stage6/STAGE6_FINAL_AUDIT.md`

最终审计结果：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 2
VERDICT   = READY TO MERGE
```

最终审计文件进入施工分支后的验证 HEAD：

`0ab4a37ee7ec5d995a26804d6946c3d932ab879f`

正式合并：

```text
PR #4
Stage 6: Skill Runtime final merge
```

进入 main 的封版提交：

`6c0b1c22b2178405324c30577869ab960d4b139e`

对应 main exact-head GitHub Actions：

```text
run_id:
33902680345

pytest / demo / workflow:
success
```

状态：`✅ FROZEN`

---

# Stage 7 封版基线

正式施工合同：`stages/stage7/STAGE7.md`

正式施工 Prompt：`stages/stage7/STAGE7_BUILD_PROMPT.md`

Evidence Matrix：`stages/stage7/STAGE7_EVIDENCE_MATRIX.md`

最终独立审计：`stages/stage7/STAGE7_FINAL_AUDIT.md`

## 最终审计结论

最终实现审计锁定 HEAD：

`a459ca876b034509b2d13ab725d65df50a070aa1`

独立最终审计结果：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 0
HARDENING = 1 (accepted, non-blocking)

VERDICT = READY TO MERGE
```

exact-head GitHub Actions：

```text
Run #112
run_id = 33910600065
pytest -q = 234 passed
demo.py = success
```

同一 exact HEAD 的审计 artifact 已在独立沙箱中验证 SHA-256 与 source SHA，并再次执行：

```text
Python 3.13.5
python -m pytest -q = 234 passed
python demo.py = success
```

## 最终审计文档进入分支

`stages/stage7/STAGE7_FINAL_AUDIT.md` 提交：

`b144e6f76272971dbd469502adbcddaed6747063`

该文档提交对应 PR workflow：

```text
Run #115
run_id = 33911399143
conclusion = success
```

## 正式合并

```text
PR #5
Stage 7: Trigger/Recovery final merge
```

Stage 7 implementation + final audit 进入 main 的 merge commit：

`199585c25b7db46d5c008fab46ab21fb7957ebb0`

该 main exact HEAD 对应 GitHub Actions：

```text
Run #116
run_id = 33911442223
checkout SHA = 199585c25b7db46d5c008fab46ab21fb7957ebb0
pytest -q = 234 passed
demo.py = success
workflow conclusion = success
```

因此 Stage 7 封版条件已经满足：

```text
Stage 7 implementation
+
stages/stage7/STAGE7_FINAL_AUDIT.md
进入 main
+
main exact HEAD pytest / demo / GitHub Actions success
+
PROJECT_STATUS.md 记录封版状态
=
Stage 7 FROZEN
```

当前状态：

```text
✅ FROZEN
```

## Stage 7 官方状态范围

Stage 7 production behavior 允许：

```text
healing_ban
```

继续 DEFER：

```text
burn
flood
poison
rout
sandstorm
recuperation
rebellion
first_aid
weapon_lifesteal
strategy_lifesteal
```

这些 DEFER 状态不得因为 Stage 7 基础设施已完成而被视为正式行为已实现。

---

# Stage 8 设计冻结、实现与封版基线

各阶段资料现已统一采用“一阶段一目录”组织；Stage 8 目录为：

`stages/stage8/`

目录规范：`stages/README.md`

Stage 8 主设计文档：

`stages/stage8/STAGE8.md`

Stage 8 设计冻结记录 / normative freeze-prep addendum：

`stages/stage8/STAGE8_DESIGN_FREEZE.md`

Stage 8 Evidence Matrix：

`stages/stage8/STAGE8_EVIDENCE_MATRIX.md`

Stage 8 正式施工 Prompt：

`stages/stage8/STAGE8_BUILD_PROMPT.md`

Stage 8 实现报告：

`stages/stage8/STAGE8_IMPLEMENTATION_REPORT.md`

Stage 8 正式 Final Audit：

`stages/stage8/STAGE8_FINAL_AUDIT.md`

Stage 8 最终封版证据：

`stages/stage8/STAGE8_FREEZE_RECORD.md`

旧路径与当前路径的对应关系见 `stages/PATH_MIGRATION.md`；阶段资料以各自的 `stages/stageN/` 目录为正式存放位置。

Stage 8 v1 设计提交：

```text
98b23726ab1d28e4c378e998314a4abe1a39e5b7
```

第一轮独立设计审计：

```text
BLOCKER   = 0
MAJOR     = 7
MINOR     = 6
HARDENING = 4
VERDICT   = REVISE BEFORE DESIGN FREEZE
```

Stage 8 v2 修订设计提交：

```text
c4c61b71f7054c9473245c6542eb3551cc76f663
```

第二轮独立设计复审：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 2
HARDENING = 3
VERDICT   = DESIGN READY
```

第二轮确认第一轮 `M-01 ~ M-07` 全部 CLOSED。

冻结记录提交：

```text
00957d4b939d01ee14f8a803778c6ed86f193c76
```

freeze-prep 正式关闭第二轮剩余两个 MINOR：

```text
1. public numeric boundary validation ownership
2. typed StageEvaluationStatus for DamagePipelineTrace
```

冻结后的 Stage 8 核心主链：

```text
DamageRequest
↓
participant validation
↓
StateDamageRuleProvider / binding adapter
↓
immutable DamageRuleCollection
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
DamageFormulaPolicySystem
↓
Frozen Base Formula
↓
coefficient
↓
DamageModifierSystem
↓
finalization
↓
DamageResult + DamagePipelineTrace
↓
DamageResolutionSystem
↓
TroopSystem
```

设计状态：

```text
✅ DESIGN FROZEN
```

## Stage 8 original implementation

施工分支：

```text
stage8-damage-pipeline
```

starting main exact HEAD：

```text
ec9b2fa8e2ca801632e3228c9727f612bf0d989a
```

starting main exact-head verification：

```text
Run #124
run_id = 34467373980
pytest -q = 234 passed in 0.96s
demo.py = success
workflow conclusion = success
```

核心 implementation + tests + Stage 8 independent-audit snapshot CI 配置验证 SHA：

```text
ea524e7b16bb9fa7372760f745336a94cecdfc29
```

对应 branch verification：

```text
Run #149
run_id = 34469417926
pytest -q = 261 passed in 1.18s
demo.py = success
Stage 8 audit artifact = success
```

独立实现审计 repair base：

```text
87fcd424cd25a96710ec297285b88206e84bb4ef
```

独立实现审计结论：

```text
BLOCKER   = 0
MAJOR     = 3
MINOR     = 1
HARDENING = 1
VERDICT   = FIX REQUIRED BEFORE FINAL AUDIT
```

## Stage 8 independent-audit findings repair

本轮只修复审计 findings，不改变 Stage 8 frozen design：

```text
S8-M-01  immutable rule snapshot / binding alias safety
S8-M-02  typed runtime boundaries + pre-RNG malformed operation rejection
S8-M-03  DamagePipelineTrace typed status/result invariants
S8-N-01  audit reproduction regression coverage
S8-H-01  applicable duplicate order_key construction-time guard
```

新增正式回归：

```text
tests/test_stage8_independent_audit_regressions.py
tests/test_stage8_second_reaudit_regressions.py
```

回归复现证据：

```text
旧 SHA 87fcd424... + 新 regression tests
→ 28 failed / 8 passed

修复代码 + 完整 suite（提交前本地 artifact 验证）
→ 297 passed

python demo.py
→ success
```

第二次独立复审重新打开了：

```text
S8-M-02  runtime scope 必须为 exact built-in frozenset，不能接受 frozenset subclass
S8-N-01  必须覆盖 noncanonical frozenset subclass / mutable semantic alias regression
S8-RN-01 PROJECT_STATUS 必须明确记录 SECOND INDEPENDENT RE-AUDIT
```

随后完成 findings repair、第三次 Independent Re-Audit 与 Stage 8 Final Audit，production findings 全部收束。

Third Independent Re-Audit / Final Audit approved implementation SHA：

```text
446ac5a9d4ae595dcc79abc3c03873cad22893f8
```

Final Audit 结论：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 0

S8-M-01 = CLOSED
S8-M-02 = CLOSED
S8-M-03 = CLOSED
S8-N-01 = CLOSED
S8-H-01 = CLOSED

S8-RN-01 = documentation / process only
Disposition = MUST FIX BEFORE MERGE

VERDICT = APPROVED FOR MERGE TO MAIN
```

Final Audit exact-head verification baseline：

```text
Run #161
run_id = 34497232784
head_sha = 446ac5a9d4ae595dcc79abc3c03873cad22893f8
pytest -q = 326 passed
demo.py = success
workflow conclusion = success
```

## Stage 8 post-Final-Audit docs closure

S8-RN-01 通过纯文档提交关闭：

```text
202647135f97db31e08b6ad1d917d7e5a8e6ce15
docs(stage8): close final-audit process finding
```

该 commit 的直接 parent 为 Final Audit approved SHA：

```text
446ac5a9d4ae595dcc79abc3c03873cad22893f8
```

仅修改：

```text
PROJECT_STATUS.md
stages/stage8/README.md
stages/stage8/STAGE8_FINAL_AUDIT.md
```

branch exact-head verification：

```text
Run #163
run_id = 34502709262
head_sha = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
pytest -q = 326 passed
demo.py = success
workflow conclusion = success
```

S8-RN-01：

```text
✅ CLOSED
```

## Stage 8 merge and main freeze verification

starting main：

```text
ec9b2fa8e2ca801632e3228c9727f612bf0d989a
```

最终 merge source：

```text
202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

merge 前 compare：

```text
ahead_by  = 37
behind_by = 0
```

因此采用 fast-forward 合并，`main` 直接前进到：

```text
202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

main exact-head GitHub Actions：

```text
Run #164
run_id = 34503212432
head_sha = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
Python = 3.11.16
pytest -q = 326 passed in 1.30s
demo.py = success
workflow conclusion = success
```

main exact-head audit artifact：

```text
name = stage8-independent-audit-202647135f97db31e08b6ad1d917d7e5a8e6ce15
Artifact ID = 10162718752
SHA-256 = ca4af39fe3c069f3b050416c1b52e136560e20270dd31a085d024fbd421ee531
AUDIT_SOURCE_SHA = 202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

因此 main 封版证据链成立：

```text
main exact HEAD
=
workflow head SHA
=
artifact source SHA
=
202647135f97db31e08b6ad1d917d7e5a8e6ce15
```

Stage 8 当前 Evidence Gate 保持不变：

```text
weakness                  PASS_STAGE8

evasion                   DEFER
barrier                   DEFER
sure_hit                   DEFER
defense_pierce            DEFER
vigilance                 DEFER
critical                  DEFER
strategy_critical         DEFER
damage_reduction_pierce   DEFER
rebellion                 DEFER
```

`weakness` 的 PASS 只用于迁移既有冻结行为；其余 DEFER 状态没有 official Stage 8 production binding。

Stage 8 封版条件：

```text
Final Audit PASSED
+
all blocking findings CLOSED
+
S8-RN-01 CLOSED before merge
+
verified merge source entered main
+
main exact-head pytest / demo / GitHub Actions PASS
+
main exact-head artifact provenance PASS
+
STAGE8_FREEZE_RECORD.md persisted
=
Stage 8 FROZEN
```

当前状态：

```text
✅ FROZEN
```

---

# 下一阶段动作

Stage 8 已正式 FROZEN。

下一阶段允许进入：

```text
Stage 9 design / evidence / boundary definition
```

Stage 9 必须作为新的独立阶段执行：

```text
需求与证据梳理
↓
STAGE9.md 设计
↓
独立设计审计
↓
DESIGN FROZEN
↓
施工
```

Stage 9 不得为了方便反向修改 Stage 8 frozen contracts。若未来发现真正的 Stage 8 freeze-breaking defect，必须走正式 reopen 流程，而不是把“顺手改一下”包装成下一阶段施工。
