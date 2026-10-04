# Strategy Damage Formula Runtime Implementation

Owner: `sgs_v2/battle_core/strategy_damage_formula.py::StrategyBaseDamageFormula`; `DamageType.STRATEGY` routes here through `DamageSystem`. Source/target final intelligence comes from `AttributeSystem.get_intelligence`; missing intelligence raises an error rather than substituting another attribute.

The class reuses the weapon base implementation's current-troop lookup, level scaling, restraint/morale, CEIL ownership and battle `RandomSystem` calls. Runtime table: `data/normal_attack/troop_function_table_1_10000.csv`; valid troops 1..10000. `DamageSystem` applies the request coefficient after base calculation; `TroopSystem.apply_damage` commits actual capped loss. This is a code mapping; gameplay derivation and model limits belong to the pinned Research authority.


Research Authority:
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Commit: 95e7fe78430d623c0240e9615f5f054515a90ce9
Path: formulas/STRATEGY_DAMAGE_FORMULA_V1.md
Status: CANDIDATE / IMPLEMENTATION BASELINE
