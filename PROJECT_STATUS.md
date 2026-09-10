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
Stage 8 Damage Pipeline   ✅ DESIGN FROZEN / implementation 尚未开始
Stage 9+                  ⏳ 尚未施工
```

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

正式审计：`STAGE4_FINAL_AUDIT.md`

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

正式施工文档：`STAGE5.md`

正式审计：`STAGE5_FINAL_AUDIT.md`

状态：`✅ FROZEN`

---

# Stage 6 封版基线

正式施工文档：`STAGE6.md`

正式审计：`STAGE6_FINAL_AUDIT.md`

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

正式施工合同：`STAGE7.md`

正式施工 Prompt：`prompts/STAGE7_BUILD_PROMPT.md`

Evidence Matrix：`research/stage7_evidence_matrix/STAGE7_EVIDENCE_MATRIX.md`

最终独立审计：`STAGE7_FINAL_AUDIT.md`

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

`STAGE7_FINAL_AUDIT.md` 提交：

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
STAGE7_FINAL_AUDIT.md
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

# Stage 8 设计冻结基线

Stage 8 主设计文档：

`STAGE8.md`

Stage 8 Evidence Matrix：

`research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md`

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

设计冻结记录 / normative freeze-prep addendum：

`STAGE8_DESIGN_FREEZE.md`

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

注意：Stage 8 目前只是设计冻结，production implementation 尚未开始，因此不得将其写成完整 `Stage 8 FROZEN`。

Stage 8 当前 Evidence Gate：

```text
weakness                  PASS_STAGE8

evasion                   DEFER
barrier                   DEFER
sure_hit                  DEFER
defense_pierce            DEFER
vigilance                 DEFER
critical                  DEFER
strategy_critical         DEFER
damage_reduction_pierce   DEFER
rebellion                 DEFER
```

`weakness` 的 PASS 仅允许迁移既有冻结行为；其余 DEFER 状态不得出现 official production binding。

---

# 下一阶段动作

Stage 8 的设计审计阶段已经关闭。

下一步允许生成：

```text
prompts/STAGE8_BUILD_PROMPT.md
```

随后建立 Stage 8 implementation branch，并严格按照：

```text
STAGE8.md
+ STAGE8_DESIGN_FREEZE.md
+ research/stage8_evidence_matrix/STAGE8_EVIDENCE_MATRIX.md
```

进行施工。

施工完成后仍必须经过：

```text
pytest + demo + CI
→ 独立实现审计
→ 修复 / 再审计
→ STAGE8_FINAL_AUDIT.md
→ merge main
→ main exact-head CI
→ Stage 8 FROZEN
```
