from __future__ import annotations

from dataclasses import dataclass, replace

from .execution_right_system import FutureBranchKind
from .operation_identity import SourceType, CleaveEffectId, OperationLineage
from .enums import DamageType
from .stage9_integerization import ExactRatio
from .reaction_permission_policy import ReactionPermissionPolicy


@dataclass(frozen=True, slots=True, init=False)
class CleaveEffect:
    effect_id: CleaveEffectId
    lineage: OperationLineage
    damage_type: DamageType
    base_amount: int
    ratio: ExactRatio
    secondary_plan: tuple[str, ...]
    source_instance_id: str

    def __init__(self, *args, **kwargs):
        raise TypeError("Use CleaveSystem.create_effect with an authentic permit")


class CleaveSystem:
    def __init__(self, state_runtime, gate, derived_resolver):
        self._states = state_runtime
        self._gate = gate
        self._finalization = gate.coordinator
        self._derived = derived_resolver

    def create_effect(self, context, main, state, *, permit):
        self._finalization._validate_context(context)
        if not ReactionPermissionPolicy.can_trigger_cleave(main.lineage.source_type):
            raise ValueError("Only NORMAL_ATTACK can admit Cleave")
        # Slot validation precedes identity allocation; the factory cannot bypass it.
        effects = self._states.get_cleave_effects(context, main.lineage.physical_attacker)
        if not any(item is state for item in effects):
            raise ValueError("Cleave source must be the current authoritative state")
        self._gate.consume_permit(permit, FutureBranchKind.CLEAVE_EFFECT, str(main.lineage.parent_normal_attack_id))
        effect_id = context.id_allocator.allocate_cleave_effect_id()
        anchor = context.get_unit(main.target_id)
        plan = tuple(unit.unit_id for unit in sorted(context.units.values(), key=lambda unit: unit.lineup_position)
            if unit.team_id == anchor.team_id and unit.is_alive
            and unit.unit_id not in (main.target_id, main.lineage.physical_attacker))
        cap = object.__new__(CleaveEffect)
        values = dict(effect_id=effect_id,
            lineage=replace(main.lineage, source_type=SourceType.CLEAVE,
                parent_damage_instance_id=main.damage_instance_id, physical_skill=state.source_skill_id),
            damage_type=main.damage_type, base_amount=main.actual_target_troop_loss,
            ratio=state.runtime_params.ratio, secondary_plan=plan, source_instance_id=state.instance_id)
        for key, value in values.items():
            object.__setattr__(cap, key, value)
        self._finalization._register_reaction(context, effect_id, cap)
        return cap

    def execute(self, context, effect):
        self._finalization.start_reaction(context, effect.effect_id, effect)
        results = []
        try:
            for target_id in effect.secondary_plan:
                attacker = context.units.get(effect.lineage.physical_attacker)
                if attacker is None or not attacker.is_alive:
                    break
                target = context.units.get(target_id)
                if target is None or not target.is_alive:
                    continue
                request = self._derived._issue_request(context, effect, target_id)
                results.append(self._derived.resolve(context, effect, request))
            return tuple(results)
        finally:
            self._finalization.complete_reaction(context, effect.effect_id, effect)

    def resolve(self, context, main):
        self._finalization._validate_context(context)
        if not ReactionPermissionPolicy.can_trigger_cleave(main.lineage.source_type):
            return ()
        results = []
        for state in self._states.get_cleave_effects(context, main.lineage.physical_attacker):
            attacker = context.units.get(main.lineage.physical_attacker)
            if attacker is None or not attacker.is_alive:
                break
            if not any(item is state for item in self._states.get_cleave_effects(context, attacker.unit_id)):
                continue
            permit = self._gate.request_admission(FutureBranchKind.CLEAVE_EFFECT, str(main.lineage.parent_normal_attack_id))
            if permit is None:
                break
            effect = self.create_effect(context, main, state, permit=permit)
            results.extend(self.execute(context, effect))
        return tuple(results)
