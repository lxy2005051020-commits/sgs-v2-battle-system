# 三国志战略版战斗模拟器 V2 · 当前阶段状态

> 本文件只维护“当前阶段状态、封版提交和验证基线”。长期阶段规划仍以 `PROJECT_ROADMAP.md` 为准。
>
> 当 `PROJECT_ROADMAP.md` 的历史状态快照与本文件冲突时，仅在“当前阶段是否完成 / FROZEN”这一问题上以本文件和对应 `STAGEX_FINAL_AUDIT.md` 为准。

---

# 当前状态

```text
Stage 1 基础运行模型       ✅ 回归稳定
Stage 2 BattleSystem      ✅ FROZEN
Stage 3 BattleState       ✅ 稳定
Stage 4 官方状态接入       ✅ FROZEN
Stage 5 Effect            ✅ FROZEN
Stage 6 Skill Runtime     ✅ FROZEN
Stage 7 Trigger/Recovery  📝 规划已修订，待第二轮设计复审
Stage 8+                  ⏳ 尚未开始
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

正式审计：

```text
STAGE4_FINAL_AUDIT.md
```

---

# Stage 5 封版基线

最终施工分支验证提交：

```text
33f0885fe8201955b12cd6cee00facc20984fe26
```

验证：

```text
pytest -q
→ 105 passed

python demo.py
→ success

GitHub Actions
→ success
```

正式施工文档：

```text
STAGE5.md
```

最终审计：

```text
STAGE5_FINAL_AUDIT.md
```

当前状态：

```text
✅ FROZEN
```

---

# Stage 6 封版基线

正式施工文档：

```text
STAGE6.md
```

最终独立审计：

```text
STAGE6_FINAL_AUDIT.md
```

第二轮独立最终审计结论：

```text
BLOCKER   = 0
MAJOR     = 0
MINOR     = 1
HARDENING = 2

VERDICT = READY TO MERGE
```

最终审计文件进入施工分支后的验证 HEAD：

```text
0ab4a37ee7ec5d995a26804d6946c3d932ab879f
```

对应验证：

```text
pytest -q
→ 151 passed

python demo.py
→ success

GitHub Actions
→ success
```

Stage 6 正式合并 PR：

```text
PR #4
Stage 6: Skill Runtime final merge
```

Stage 6 进入 main 的封版提交：

```text
6c0b1c22b2178405324c30577869ab960d4b139e
```

该 main exact HEAD 的 GitHub Actions：

```text
workflow run:
33902680345

status:
completed

conclusion:
success

Run tests:
success

Run demo smoke test:
success
```

因此 `STAGE6.md` 规定的最终封版条件已经满足：

```text
Stage 6 implementation
+
STAGE6_FINAL_AUDIT.md
进入 main
+
该 main exact HEAD GitHub Actions success
=
Stage 6 FROZEN
```

当前状态：

```text
✅ FROZEN
```

---

# Stage 7 当前规划

正式规划文档：

```text
STAGE7.md
```

初始规划同步提交：

```text
495b5239b1ae0691b9479511d79831d7bfb826de
```

第一轮独立设计审计基线：

```text
e9a5f118e887ddada6401c1590738cac87791f1a
```

第一轮设计审计结论：

```text
BLOCKER   = 0
MAJOR     = 4
MINOR     = 2
HARDENING = 2

VERDICT = NOT READY FOR STAGE 7 BUILD
```

规划修订提交：

```text
d2b686595a43294b622359574a24422cd1d83329
```

本次规划修订已补齐：

```text
1. source_skill_id / source_state_id / source_state_instance_id provenance 全链
2. RecoverEffect / RecoveryRequest / TroopSystem.restore 恢复输入类型安全
3. Hook atomic batch + batch 后 Victory check
4. UNIT_ACTION_START 击杀 actor 后的完整 UNIT_ACTION_END lifecycle
5. RecoveryResolvedResult / RecoveryPreventedResult 联合类型
6. actual_recovery == 0 的事件语义
7. RuleHook round / actor 输入一致性验证
8. 官方状态 evidence matrix 的 PASS_STAGE7 / DEFER 硬 gate
```

Stage 7 当前目标：

```text
Explicit Rule Hook
→ TriggerSystem
→ ordered Effect(s)
→ RuleHookSystem
→ EffectExecutor

RecoverEffect
→ RecoverySystem
→ TroopSystem
```

并新增来源审计链：

```text
StateInstance
→ source_skill_id
→ source_state_id
→ source_state_instance_id
→ Effect / Request / Result / Event
```

Stage 7 第一版重点：

```text
RuleHook 强类型合同
TriggerSystem
RuleHookSystem
RecoverySystem
RecoverEffect 正式恢复执行
恢复事实事件
ROUND_START / UNIT_ACTION_START 最小 hook
周期 Damage / Recovery StateRuntimeParams
Hook atomic batch
State provenance
```

基于当前架构与证据，Stage 7 不强行一次实现旧 Roadmap 中全部 11 个候选状态。

当前正式规划：

```text
可进入 Stage 7 evidence gate：
burn / flood / poison / rout / sandstorm / recuperation

可直接进入 Stage 7 Recovery policy：
healing_ban

明确 DEFER：
rebellion
→ 需要 Stage 8 Damage Pipeline 的无视防御合同

first_aid / weapon_lifesteal / strategy_lifesteal
→ 需要 AFTER_DAMAGE reaction / queue 设计
```

Stage 7 当前状态：

```text
📝 PLAN REVISED
PENDING SECOND DESIGN AUDIT
NOT IMPLEMENTED
NOT FROZEN
```

下一步必须先：

```text
第二轮独立 Stage 7 设计复审
```

只有复审达到：

```text
BLOCKER = 0
MAJOR = 0
```

才建立：

```text
prompts/STAGE7_BUILD_PROMPT.md
```

然后进入独立施工分支。

---

# 下一阶段动作

当前不得直接开始 Stage 8，也不得跳过 Stage 7 第二轮设计复审直接施工。

Stage 7 正确流程：

```text
STAGE7.md
→ 第一轮独立设计审计
→ 修订 STAGE7.md
→ 第二轮独立设计复审
→ STAGE7_BUILD_PROMPT.md
→ Stage 7 施工
→ pytest / demo / CI
→ 最终独立审计
→ merge main
→ main CI success
→ Stage 7 FROZEN
```
