# 解烦卫 Additive Damage Seam Runtime Contract

> Date: 2026-10-06  
> Scope: `Speed * 0.40` opt-in additive basis for 解烦卫  
> Architecture verdict: **APPROVED EXTENSION OF CANONICAL DamageSystem / NOT A SECOND OWNER**

## 1. Why this seam exists

解烦卫当前 Research 合同要求：

```text
PreModifierDamage
= BaseDamage * Coefficient + CurrentFinalSpeed * 0.40

then
-> critical / pierce / outgoing modifiers
-> incoming modifiers
-> prevention / integerization / settlement
```

现有 `DamageRequest.coefficient` 只表达 `BaseDamage * coefficient`，不能在不复制 DamageSystem 的前提下表达同一伤害实例里的额外加数。

## 2. Canonical owner rule

Stage13 Owner Matrix 仍保持：

```text
Damage formula / result calculation = DamageSystem
Damage instance lifecycle           = DamageInstanceCoordinator
Damage target settlement            = DamageResolutionSystem
```

本轮不修改这些所有权。

`AdditiveDamageSystem` 是 `DamageSystem` 子类，并且：

- 不重新实现完整 `calculate()` pipeline；
- 入口先设置单次请求作用域的 additive 值，然后调用 `super().calculate()`；
- 只覆盖 `_calculate_weapon_base_damage()` / `_calculate_strategy_base_damage()` 的返回数值包装；
- 包装数值只改变 canonical `base * coefficient` 这一次乘法，使结果成为 `base * coefficient + addition`；
- 后续所有 hit/prevention/critical/modifier/pierce/advancement/alert/final damage 逻辑继续由父类 `DamageSystem.calculate()` 执行；
- settlement 仍由 DamageInstanceCoordinator -> DamageResolutionSystem 执行。

因此：

```text
NEW DAMAGE OWNER = NO
CANONICAL OWNER  = DamageSystem family
EXTENSION MODE   = opt-in request adapter
```

## 3. Opt-in request boundary

`AdditiveDamageRequest` 扩展 `DamageRequest`，新增：

```text
additive_damage: float = 0.0
```

约束：

- 仅允许非负有限值；
- 非零 additive 只允许 `LIVE_RUNTIME`；
- 普通 `DamageRequest` 不携带 additive 语义；
- `DamageEffect(additive_damage=0)` 与旧普通伤害路径保持兼容。

## 4. No leakage

内部 additive 值通过 `ContextVar` 在单次 `calculate()` 中设置，并在 `finally` 中 reset。

因此：

- 当前伤害实例的 additive 不得影响下一次伤害；
- nested/parallel context 读取使用上下文隔离；
- 返回的 `DamageResult.base_damage` 会恢复为普通 `float`，不把内部 `_AdditiveBasis` 暴露给下游。

## 5. Formula boundary

只有以下运算被扩展：

```text
old:
scaled_damage = base_damage * coefficient

opt-in:
scaled_damage = base_damage * coefficient + additive_damage
```

以下全部不在 adapter 中重写：

- WeaponBaseDamageFormula；
- StrategyBaseDamageFormula；
- troop function；
- random percent / low-damage floor；
- troop restraint；
- morale；
- crit / 奇谋；
- weakness；
- outgoing/incoming modifier pooling；
- pierce / 看破；
- resistance/evasion；
- alert；
- final integerization；
- actual troop loss settlement。

## 6. Regression evidence requirement

因为 `BattleSystems.damage_system` 在此分支使用 `AdditiveDamageSystem`，全量测试实际上会让**所有既有普通伤害路径**经过该子类。

因此 mainline gate 要求同时满足：

1. additive 专项测试；
2. 旧普通 DamageRequest 零附加回归；
3. 全量 battle regression；
4. Stage13-D1 frozen-owner hash audit；
5. independent Runtime audit；
6. PR CI；
7. merged-main CI。

仅有 frozen-source hash PASS 不足以证明实例级扩展语义正确；必须同时依赖上述全量行为回归。

## 7. Current discriminating tests

当前解烦卫测试至少覆盖：

- `base * coefficient + speed*0.40` 只加一次；
- weapon / strategy 两类 damage；
- zero additive 保持旧 scaled damage；
- additive=57 且 coefficient=0 时只得到 57；
- additive 请求后普通请求不泄漏；
- weakness 仍可将 additive damage 归零；
- 看破 family 仍进入 Stage11 规则；
- 全量既有 damage/recovery/state 测试在该子类下运行。

## 8. Freeze / reopen rule

此 seam 只授权：

```text
BaseDamage * coefficient + one nonnegative additive basis
```

它不自动授权：

- 多项任意顺序 additive/multiplicative expression tree；
- additive 绕过暴击或减伤；
- frozen DOT additive；
- 对 DamageSystem 的新随机层；
- 技能自建 damage formula。

未来若需要上述能力，必须重新做 architecture amendment。

## 9. Verdict

```text
XIEFAN_ADDITIVE_SEAM_OWNER        = DamageSystem family
SECOND_DAMAGE_OWNER               = NO
OPT_IN_ONLY                       = YES
PLAIN_DAMAGE_COMPATIBILITY        = REQUIRED
CONTEXT_LEAKAGE                   = FORBIDDEN
DOWNSTREAM_PIPELINE_REUSE         = REQUIRED

XIEFAN_ADDITIVE_DAMAGE_SEAM       = APPROVED
```
