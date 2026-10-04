# Normal Attack Formula Runtime Implementation

Owner: `sgs_v2/battle_core/weapon_damage_formula.py::WeaponBaseDamageFormula`; called by `DamageSystem`. Inputs: current source troops, final attack/defense from `AttributeSystem`, source/target level, troop type and source morale; optional `DamageFormulaContext` controls relevant target-defense bypass.

The class loads `data/normal_attack/troop_function_table_1_10000.csv` once via the cached repository loader. It accepts exactly integer keys 1..10000 and nonnegative values; out-of-range troops raise `ValueError`, noninteger troops raise `TypeError`. There is no runtime segmented-formula fallback. The unused historical mid-table is Research provenance.

Pipeline: lookup and scaled attribute difference -> troop floor -> base CEIL -> restraint CEIL -> morale CEIL -> discrete random-percent CEIL -> random low-damage floor. Default integer ranges are 86..94 and 5..15, both through the battle's unique `RandomSystem`. `DamageSystem` owns coefficient/modifier processing; `TroopSystem` alone commits capped actual troop loss. Candidate fit, observations and limitations belong to Research.


Research Authority:
Repository: lxy2005051020-commits/sgs-state-mechanics-research
Commit: 95e7fe78430d623c0240e9615f5f054515a90ce9
Path: formulas/NORMAL_ATTACK_FORMULA_V1.md
Status: CANDIDATE / IMPLEMENTATION BASELINE
