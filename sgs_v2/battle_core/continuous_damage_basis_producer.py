from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .attribute_system import AttributeSystem
from .damage_formula_context import DamageDefensePolicy, DamageFormulaContext
from .damage_formula_policy_system import DamageFormulaPolicyResult, DamageFormulaPolicySystem
from .damage_modifier_system import DamageModifierSystem
from .damage_modifiers import (
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
)
from .damage_probability import resolve_probability
from .damage_rule_provider import (
    DamageRuleProvider,
    StateDamageRuleProvider,
)
from .damage_state_rule_bindings import DEFAULT_STAGE8_STATE_RULE_BINDINGS
from .enums import DamageSourceType, DamageType, TroopType
from .official_state_catalog import OfficialStateId
from .skill_runtime import SkillSlot
from .stage10_state_params import (
    FrozenContinuousDamageBasis,
    FrozenDamageModifierEntry,
    FrozenSourceFormulaFacts,
    HistoricalDamageSourceRef,
)
from .state_generation import StateApplicationGenerationId

if TYPE_CHECKING:
    from .context import BattleContext


@dataclass(frozen=True, slots=True)
class ContinuousDamageApplicationRequest:
    """
    Request object for capturing immutable application-time facts for continuous damage states.
    """

    source_id: str
    target_id: str
    state_id: str
    application_generation_id: StateApplicationGenerationId
    coefficient: float = 1.0
    source_skill_id: str | None = None
    source_skill_slot: SkillSlot | None = None
    physical_state_instance_id: str | None = None


class ContinuousDamageBasisProducer:
    """
    Stage8 application-time producer capturing immutable continuous damage facts (STAGE8_ADDENDUM §5, STAGE10.md §29).
    Captures:
    - Route selection (REBELLION dynamically selects WEAPON vs STRATEGY by comparing ATK vs INT at capture time)
    - Formula policy (REBELLION locks IGNORE_RELEVANT_TARGET_DEFENSE; others NORMAL)
    - Source formula facts (source troops, combat attribute, level, morale, troop type)
    - Ordered ordinary modifier plan (probabilistic decisions evaluated once at application time)
    - Historical source reference
    """

    def __init__(
        self,
        attribute_system: AttributeSystem | None = None,
        *,
        rule_provider: DamageRuleProvider | None = None,
        formula_policy_system: DamageFormulaPolicySystem | None = None,
        modifier_system: DamageModifierSystem | None = None,
        stage11_state_runtime=None,
    ) -> None:
        self._attributes = attribute_system or AttributeSystem()
        self._rule_provider = (
            StateDamageRuleProvider(DEFAULT_STAGE8_STATE_RULE_BINDINGS)
            if rule_provider is None
            else rule_provider
        )
        self._formula_policy = (
            DamageFormulaPolicySystem()
            if formula_policy_system is None
            else formula_policy_system
        )
        self._modifiers = (
            DamageModifierSystem() if modifier_system is None else modifier_system
        )
        self._stage11 = stage11_state_runtime

    def capture(
        self,
        context: BattleContext,
        request: ContinuousDamageApplicationRequest,
    ) -> FrozenContinuousDamageBasis:
        source = context.get_unit(request.source_id)

        state_id_str = (
            request.state_id.value
            if isinstance(request.state_id, OfficialStateId)
            else str(request.state_id)
        )

        # 1. Route selection
        if state_id_str == OfficialStateId.ROUT.value:
            damage_type = DamageType.WEAPON
        elif state_id_str in (
            OfficialStateId.BURN.value,
            OfficialStateId.FLOOD.value,
            OfficialStateId.POISON.value,
            OfficialStateId.SANDSTORM.value,
        ):
            damage_type = DamageType.STRATEGY
        elif state_id_str == OfficialStateId.REBELLION.value:
            effective_atk = self._attributes.get_attack(context, source)
            effective_int = (
                self._attributes.get_intelligence(context, source)
                if source.intelligence is not None
                else 0.0
            )
            if effective_atk >= effective_int:
                damage_type = DamageType.WEAPON
            else:
                damage_type = DamageType.STRATEGY
        else:
            damage_type = DamageType.STRATEGY

        # 2. Formula policy
        if (
            state_id_str == OfficialStateId.REBELLION.value
            or (
                self._stage11 is not None
                and self._stage11.break_formation_active(context, request.source_id)
            )
        ):
            formula_policy_result = DamageFormulaPolicyResult(
                formula_context=DamageFormulaContext(
                    defense_policy=DamageDefensePolicy.IGNORE_RELEVANT_TARGET_DEFENSE
                ),
                contributors=(),
            )
        else:
            formula_policy_result = DamageFormulaPolicyResult(
                formula_context=DamageFormulaContext(
                    defense_policy=DamageDefensePolicy.NORMAL
                ),
                contributors=(),
            )

        # 3. Source-side formula facts
        if damage_type is DamageType.WEAPON:
            combat_attribute = self._attributes.get_attack(context, source)
        else:
            combat_attribute = (
                self._attributes.get_intelligence(context, source)
                if source.intelligence is not None
                else 0.0
            )

        source_formula_facts = FrozenSourceFormulaFacts(
            source_troops_at_application=source.troops,
            source_combat_attribute_at_application=float(combat_attribute),
            source_level_at_application=source.level,
            source_morale_at_application=source.morale,
            source_troop_type_at_application=source.troop_type,
        )

        # 4. Source-side ordinary modifier plan
        from .damage_system import DamageRequest

        dummy_request = DamageRequest(
            source_id=request.source_id,
            target_id=request.target_id,
            damage_type=damage_type,
            source_type=DamageSourceType.CONTINUOUS,
            coefficient=request.coefficient,
            source_skill_id=request.source_skill_id,
        )
        rules = self._rule_provider.collect(context, dummy_request)

        source_mods = [
            contrib
            for contrib in rules.modifier_contributions
            if contrib.applies_to(damage_type, DamageSourceType.CONTINUOUS)
            and (
                contrib.phase in (DamageModifierPhase.CRITICAL, DamageModifierPhase.OUTGOING)
                or (contrib.source.owner_id is not None and contrib.source.owner_id == request.source_id)
            )
        ]
        source_mods.sort(key=lambda c: (c.phase_order, c.order_key))

        locked_modifier_plan: list[FrozenDamageModifierEntry] = []
        for c in source_mods:
            # Consume probabilistic / crit decision once at application time (STAGE8_ADDENDUM §5.4)
            if resolve_probability(context, c.probability):
                locked_modifier_plan.append(
                    FrozenDamageModifierEntry(
                        kind=c.kind,
                        operation=c.operation,
                        operand=c.operand,
                        order_key=c.order_key,
                        phase=c.phase,
                        source=c.source,
                        admitted=True,
                    )
                )

        locked_crit_context = None
        if self._stage11 is not None:
            locked_crit_context = self._stage11.resolve_critical(
                context,
                source_id=request.source_id,
                damage_type=damage_type,
            )

        # 5. Historical source reference
        historical_source = HistoricalDamageSourceRef(
            source_unit_id=request.source_id,
            source_skill_id=request.source_skill_id,
            source_skill_slot=request.source_skill_slot,
            source_state_id=request.state_id,
            physical_state_instance_id=request.physical_state_instance_id,
            application_generation_id=request.application_generation_id,
        )

        return FrozenContinuousDamageBasis(
            application_generation_id=request.application_generation_id,
            source_unit_id=request.source_id,
            damage_type=damage_type,
            coefficient=request.coefficient,
            source_skill_id=request.source_skill_id,
            source_skill_slot=request.source_skill_slot,
            source_state_id=request.state_id,
            physical_state_instance_id=request.physical_state_instance_id,
            source_formula_facts=source_formula_facts,
            formula_policy_result=formula_policy_result,
            locked_modifier_plan=tuple(locked_modifier_plan),
            locked_crit_context=locked_crit_context,
            historical_source=historical_source,
        )
