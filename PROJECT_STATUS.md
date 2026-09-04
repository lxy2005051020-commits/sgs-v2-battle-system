# 三国志战略版战斗模拟器 V2 · 当前阶段状态

> 本文件只维护“当前阶段状态、封版提交和验证基线”。长期阶段规划仍以 `PROJECT_ROADMAP.md` 为准。
>
> 当 `PROJECT_ROADMAP.md` 的历史状态快照与本文件冲突时，仅在“当前阶段是否完成 / FROZEN”这一问题上以本文件和对应 `STAGEX_FINAL_AUDIT.md` 为准。这样可以避免为了更新几行状态而重写整份长期路线图。

---

# 当前状态

```text
Stage 1 基础运行模型       ✅ 回归稳定
Stage 2 BattleSystem      ✅ FROZEN
Stage 3 BattleState       ✅ 稳定
Stage 4 官方状态接入       ✅ FROZEN
Stage 5 Effect            ✅ 最终审计完成，待本文所在提交 main CI success 后 FROZEN
Stage 6+                  ⏳ 尚未开始
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

# Stage 5 当前基线

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

Stage 5 FROZEN 的最终条件：

```text
STAGE5_FINAL_AUDIT.md 与本文件所在提交进入 main
+
该 main 提交 GitHub Actions success
```

条件满足后无需再次修改本文；Stage 5 状态自动视为：

```text
✅ FROZEN
```

---

# 下一阶段

Stage 5 FROZEN 后，下一阶段是：

```text
Stage 6
SkillDefinition
→ SkillRuntime
→ Effect
→ EffectExecutor
```

进入 Stage 6 前必须重新读取 `main` 最新代码，并先写正式 `STAGE6.md`，不能只按长期路线图直接施工。
