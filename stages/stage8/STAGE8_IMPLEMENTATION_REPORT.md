# Stage 8 Implementation Report

状态：`IMPLEMENTATION COMPLETE / PENDING INDEPENDENT AUDIT`

本报告记录 Stage 8 production implementation 的施工结果。它不是 FINAL_AUDIT，也不将 Stage 8 宣称为 FROZEN。

## 1. Baseline

- starting main SHA: `ec9b2fa8e2ca801632e3228c9727f612bf0d989a`
- implementation branch: `stage8-damage-pipeline`
- main exact-head GitHub Actions Run #124 / run_id `34467373980`
- starting `pytest -q`: `234 passed in 0.96s`
- starting `demo.py`: success

施工前确认 Stage 8 canonical authority：

```text
stages/stage8/STAGE8.md
+ stages/stage8/STAGE8_DESIGN_FREEZE.md
+ stages/stage8/STAGE8_EVIDENCE_MATRIX.md
```

## 2. Implemented Architecture

唯一理论伤害主链已经实现为：

```text
DamageRequest
↓
participant validation
↓
StateDamageRuleProvider / immutable DamageRuleCollection
↓
DamagePreventionSystem
↓
HitResolutionSystem
↓
DamageFormulaPolicySystem
↓
Frozen Base Damage Formula
↓
coefficient scaling
↓
DamageModifierSystem
↓
finalization
↓
DamageResult + DamagePipelineTrace
↓
DamageResolutionSystem
↓
TroopSystem.apply_damage
```

新增 typed infrastructure：

```text
DamageRuleFamily
RuleContributionSource
DamageRuleCollection
StateRuleAdapter
StateRuleBinding
StateDamageRuleProvider

DamagePreventionSystem
DamagePermissionResult
DamageAllowedResult
DamagePreventedResult
DamagePreventionReason

HitResolutionSystem
HitResolutionResult
HitAllowedResult
HitPreventedResult
HitPreventionReason

DamageFormulaContext
DamageDefensePolicy
DamageFormulaPolicySystem
DamageFormulaPolicyResult

DamageModifierContribution
AppliedDamageModifier
DamageModifierKind
DamageModifierOperation
DamageModifierPhase
DamageModifierResult
DamageModifierSystem

DamagePipelineTrace
StageEvaluationStatus
```

State provenance 映射保持：

```text
owner_id                 = StateInstance.owner_id
applied_by_unit_id       = StateInstance.source_id
source_skill_id          = StateInstance.source_skill_id
source_state_id          = StateInstance.state_id
source_state_instance_id = StateInstance.instance_id
```

Provider 每个 `DamageSystem.calculate()` 只读取一次 `context.states` 并生成不可变规则快照；状态实例按稳定 `instance_id`，adapter 按声明顺序生成稳定 `origin_key/order_key`。

## 3. Frozen Contract Compliance

已保持以下冻结边界：

- `DamageSystem.calculate()` 仍是唯一 theoretical damage entry。
- `DamageResolutionSystem` 仍负责 theoretical result → troop mutation → battle fact。
- `TroopSystem` 仍是兵力实际写入口。
- `context.states` 是 Damage Pipeline 的唯一 runtime StateRegistry truth。
- `context.random` 是 Stage 8 概率与基础公式的唯一 battle RNG。
- EventBus 仍是 fact bus，不作为 damage rule engine。
- Stage 8 calculation/provider/resolver 不发布 battle fact，不扣兵，不触发 reaction。
- coefficient 仍位于 frozen base damage 与 modifier 之间。
- finalization 保持 explicit prevented → 0；其余有效伤害 → `max(1, int(modified_damage))`。
- 未引入 Stage 9 reaction queue、lifesteal、counterattack、cleave、damage share/split、guard、redirect 等行为。

未发现需要 DESIGN REOPEN 的 topology / policy / provider / modifier / Event ownership 冲突。

## 4. Official Production Mapping

当前唯一 `PASS_STAGE8` production binding：

```text
weakness
```

`weakness` 已从 `DamageSystem` 内部 hardcode 迁移为：

```text
StateInstance
→ StateDamageRuleProvider
→ typed PREVENTION contribution
→ DamagePreventionSystem
```

并保持旧 observable：

```text
base_damage = 0
scaled_damage = 0
final_damage = 0
prevented = True
prevented_by_state_id = "weakness"
base formula 不执行
formula RNG 不消费
```

以下 Evidence Matrix `DEFER` 状态没有 official production binding：

```text
evasion
barrier
sure_hit
defense_pierce
vigilance
critical
strategy_critical
damage_reduction_pierce
rebellion
```

它们只通过 synthetic state/binding 测试 generic infrastructure；synthetic engineering semantics 不视为官方机制结论。

## 5. Compatibility

- `DamageResult.pipeline_trace` 仅追加在既有字段尾部，Stage 7 positional constructor compatibility 保持。
- legacy 手动构造 `DamageResult` 可使用 `pipeline_trace=None`。
- `DamageSystem(AttributeSystem(), ...)` 旧构造继续有效。
- 新 collaborators 仅为 keyword-only；只有显式 `None` 才创建默认完整 Stage 8 collaborators，不存在 legacy bypass。
- `BattleSystems` canonical construction 与 manual `DamageSystem` 默认 pipeline 语义一致。
- Weapon / Strategy base formula 仅增加 keyword-only `formula_context`，旧三参数调用继续有效。
- Stage 1～7 regression 在完整 suite 中保持通过。

## 6. RNG / Event / Troop Boundaries

Probability helper：

```text
p == 0  → False，不调用 context.random
p == 1  → True，不调用 context.random
0<p<1   → context.random.chance(p)
```

scope / DamageType 先过滤后 roll，因此不适用规则不消费 RNG。

Weapon / Strategy `NORMAL` differential tests 验证旧三参数行为与显式 `DamageFormulaContext(NORMAL)` 的 damage 与 RNG count 等价。

参与者 validation 在 rule discovery / RNG / formula / modifier / Event 前执行：source/target 不存在或 troops <= 0 均抛 `InvalidDamageParticipantError`。

Stage 8 calculation layers不 publish Event；`DAMAGE_PREVENTED` / `DAMAGE_DEALT` / `UNIT_DEFEATED` 仍由 `DamageResolutionSystem.apply_result()` 发布；`NORMAL_ATTACK → DAMAGE_*` 顺序由既有回归测试继续保护。

## 7. Tests Added

新增：

```text
tests/test_stage8_damage_pipeline.py
tests/test_stage8_damage_pipeline_hardening.py
```

覆盖：

- StateRuleBinding / Provider / immutable snapshot / duplicate-key guard
- synthetic state 走正式 provider contract
- weakness architecture migration 与 no-formula/no-RNG short circuit
- deterministic / probabilistic hit prevention 与 bypass
- p=0 / p=1 / mid probability RNG contract
- Weapon / Strategy NORMAL differential 与 RNG equivalence
- synthetic formula policy
- typed modifier kind / operation / phase / deterministic ordering
- synthetic critical-like DamageType / RNG filtering
- reduction-pierce 只影响 INCOMING_REDUCTION effective operand
- SINGLE_HIT insertion point
- typed pipeline trace short circuit
- multi-contributor / decisive source trace
- provenance mapping
- manual / canonical DamageSystem equivalence
- no calculation-time Event publish
- normal attack event order
- dead source / target fail-fast
- bool / NaN / inf / negative numeric boundaries
- Evidence Matrix verdict / DEFER binding guard
- static architecture red lines

## 8. Verification

核心 implementation + tests + Stage 8 audit-snapshot CI 配置验证 SHA：

`ea524e7b16bb9fa7372760f745336a94cecdfc29`

对应 GitHub Actions：

```text
Run #149
run_id = 34469417926
checkout SHA = ea524e7b16bb9fa7372760f745336a94cecdfc29
pytest -q = 261 passed in 1.18s
demo.py = success
Stage 8 audit artifact = success
artifact name = stage8-independent-audit-ea524e7b16bb9fa7372760f745336a94cecdfc29
```

最终文档状态提交后仍需对新的 branch exact HEAD 再执行并记录 CI；该验证属于进入独立实现审计前的最后完整性检查。

## 9. Changed Files

Production / infrastructure：

```text
sgs_v2/battle_core/__init__.py
sgs_v2/battle_core/damage_formula_context.py
sgs_v2/battle_core/damage_formula_policy_system.py
sgs_v2/battle_core/damage_modifier_system.py
sgs_v2/battle_core/damage_modifiers.py
sgs_v2/battle_core/damage_pipeline_trace.py
sgs_v2/battle_core/damage_prevention_system.py
sgs_v2/battle_core/damage_probability.py
sgs_v2/battle_core/damage_rule_models.py
sgs_v2/battle_core/damage_rule_provider.py
sgs_v2/battle_core/damage_state_rule_bindings.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/hit_resolution_system.py
sgs_v2/battle_core/numeric_validation.py
sgs_v2/battle_core/stage8_state_params.py
sgs_v2/battle_core/strategy_damage_formula.py
sgs_v2/battle_core/weapon_damage_formula.py
```

Tests / CI / stage documentation：

```text
tests/test_stage8_damage_pipeline.py
tests/test_stage8_damage_pipeline_hardening.py
.github/workflows/tests.yml
stages/stage8/STAGE8_IMPLEMENTATION_REPORT.md
```

## 10. Remaining Risks / Accepted Hardening

- DEFER official states intentionally remain unbound; missing official behavior is an Evidence Gate boundary, not an implementation defect。
- Multiple reduction-pierce aggregation is intentionally rejected instead of guessed; official stacking / aggregation semantics remain deferred。
- State consumption / charge decrement / follow-up reaction behavior remains outside Stage 8。
- CI workflow still uses `actions/checkout@v4`, `setup-python@v5`, `upload-artifact@v4`; GitHub runner emits Node compatibility deprecation warnings, but current execution succeeds. This is repository CI maintenance hardening, not a Stage 8 correctness blocker。

## 11. Audit Readiness

```text
READY FOR INDEPENDENT IMPLEMENTATION AUDIT
```

这只表示 production implementation 已达到独立实现审计入口；Stage 8 仍不得标记为 FROZEN，后续仍需：

```text
independent implementation audit
→ findings fix
→ re-audit
→ STAGE8_FINAL_AUDIT.md
→ merge main
→ main exact-head pytest/demo/CI
→ final PROJECT_STATUS update
```
