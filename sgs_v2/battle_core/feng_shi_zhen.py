"""Stage14 F1: Feng Shi Zhen (20066) at Lv10, state-backed damage modifiers.

The state lifecycle, effectiveness, damage pools and provider-death removal are
owned by the existing BattleSystems. This module does not implement a second
damage calculator. Client log observations and V1 user-approved rules remain
separate contracts in the Research repository.
"""
from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .damage_modifiers import (
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
)
from .damage_rule_models import RuleContributionSource
from .damage_rule_provider import DamageRuleCollection, DamageRuleProvider
from .dependency_evaluation import ProviderNode, StateNode
from .enums import DamageType, LineupPosition, TroopType
from .numeric_validation import validate_finite_number
from .provider_identity import SkillProviderRef
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    SkillDefinition,
    SkillTargetMode,
    SkillType,
)
from .skill_runtime import SkillRuntime, SkillSlot
from .state_definition import StateDefinition
from .state_effectiveness import StateEffectivenessPolicy
from .state_registry import StateRegistry
from .state_runtime_params import StateRuntimeParams

FENG_SHI_ZHEN_SKILL_ID = "20066"
FENG_SHI_ZHEN_NAME = "锋矢阵"
FENG_SHI_ZHEN_MODIFIER_STATE_ID = "runtime_feng_shi_zhen_modifier"
FENG_SHI_ZHEN_APPLICABLE_TROOPS = (
    TroopType.CAVALRY,
    TroopType.SHIELD,
    TroopType.SPEAR,
)


@dataclass(frozen=True, slots=True)
class FengShiZhenModifierParams(StateRuntimeParams):
    """Signed rates. +incoming means INCREASE damage taken, not reduction."""

    outgoing_rate: float
    incoming_rate: float

    def __post_init__(self) -> None:
        for name in ("outgoing_rate", "incoming_rate"):
            rate = validate_finite_number(getattr(self, name), name)
            if rate <= -1.0:
                raise ValueError(f"{name} must be greater than -1.0")
            object.__setattr__(self, name, rate)


FENG_SHI_ZHEN_STATE_DEFINITION = StateDefinition(
    FENG_SHI_ZHEN_MODIFIER_STATE_ID,
    "锋矢阵增减伤",
    runtime_params_type=FengShiZhenModifierParams,
)

COMMANDER_RATES = FengShiZhenModifierParams(0.30, 0.20)
DEPUTY_RATES = FengShiZhenModifierParams(-0.15, -0.25)


def create_feng_shi_zhen_definition() -> SkillDefinition:
    # Declarative placeholder: the role-specific installation seam is the
    # formation's single producer, NOT the generic single-target resolver.
    return SkillDefinition(
        skill_id=FENG_SHI_ZHEN_SKILL_ID,
        name=FENG_SHI_ZHEN_NAME,
        activation_rate=1.0,
        target_mode=SkillTargetMode.SELF,
        effect_specs=(ApplyStateSkillEffectSpec(FENG_SHI_ZHEN_MODIFIER_STATE_ID),),
        skill_type=SkillType.FORMATION,
    )


def create_feng_shi_zhen_runtime(
    owner_id: str, *, slot: SkillSlot
) -> SkillRuntime:
    """Load Feng Shi Zhen using a real canonical provider slot."""
    return SkillRuntime(
        create_feng_shi_zhen_definition(),
        owner_id=owner_id,
        skill_slot=slot,
    )


def register_feng_shi_zhen_state(registry: StateRegistry) -> None:
    try:
        current = registry.get_definition(FENG_SHI_ZHEN_MODIFIER_STATE_ID)
    except KeyError:
        registry.register_definition(FENG_SHI_ZHEN_STATE_DEFINITION)
    else:
        if current != FENG_SHI_ZHEN_STATE_DEFINITION:
            raise ValueError("incompatible Feng Shi Zhen state schema")


def install_feng_shi_zhen(
    context: BattleContext,
    systems: object,
    runtime: SkillRuntime,
) -> None:
    """Install one source-bound state per existing team member, once.

    Only invoked after the global formation admission preflight. A missing
    provider slot is rejected by F0. Lifecycle and graph mutation remain with
    the canonical owners, so a provider defeat removes all three contributions.
    """
    if runtime.definition.skill_id != FENG_SHI_ZHEN_SKILL_ID:
        raise ValueError("Feng Shi Zhen installer requires canonical skill ID")
    if runtime.skill_slot is None:
        raise ValueError("Feng Shi Zhen requires a provider skill slot")
    provider = context.get_unit(runtime.owner_id)
    team = sorted(
        (u for u in context.units.values() if u.team_id == provider.team_id),
        key=lambda u: u.lineup_position.value,
    )
    if not team or team[0].lineup_position is not LineupPosition.COMMANDER:
        raise ValueError("Feng Shi Zhen requires a legal team commander")
    # Validate all targets and duplicate applications before any modification.
    for unit in team:
        if unit.lineup_position not in (
            LineupPosition.COMMANDER,
            LineupPosition.DEPUTY_1,
            LineupPosition.DEPUTY_2,
        ):
            raise ValueError("Feng Shi Zhen requires a canonical lineup position")
        if any(
            state.source_id == runtime.owner_id
            and state.source_skill_id == FENG_SHI_ZHEN_SKILL_ID
            and state.source_skill_slot == runtime.skill_slot
            for state in context.states.find(
                owner_id=unit.unit_id, state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID
            )
        ):
            raise ValueError("Feng Shi Zhen effect already installed")

    register_feng_shi_zhen_state(context.states)
    provider_ref = SkillProviderRef(
        runtime.owner_id, runtime.skill_slot, FENG_SHI_ZHEN_SKILL_ID
    )
    for unit in team:
        rates = (
            COMMANDER_RATES
            if unit.lineup_position is LineupPosition.COMMANDER
            else DEPUTY_RATES
        )
        instance = systems.state_lifecycle_system.apply(
            context,
            state_id=FENG_SHI_ZHEN_MODIFIER_STATE_ID,
            owner_id=unit.unit_id,
            source_id=runtime.owner_id,
            source_skill_id=FENG_SHI_ZHEN_SKILL_ID,
            source_skill_slot=runtime.skill_slot,
            runtime_params=rates,
        )
        systems.dependency_evaluation_support.add_dependency(
            StateNode(instance.instance_id), ProviderNode(provider_ref)
        )


class FengShiZhenDamageRuleProvider:
    """Append typed state-backed contributions to the canonical damage rules."""

    provider_key = "feng_shi_zhen"

    def __init__(
        self,
        policy: StateEffectivenessPolicy,
        base_provider: DamageRuleProvider,
    ) -> None:
        self._policy = policy
        self._base = base_provider

    def collect(self, context, request) -> DamageRuleCollection:
        base = self._base.collect(context, request)
        modifiers = list(base.modifier_contributions)
        for target_id, phase, rate_attr in (
            (request.source_id, DamageModifierPhase.OUTGOING, "outgoing_rate"),
            (request.target_id, DamageModifierPhase.INCOMING, "incoming_rate"),
        ):
            for state in self._policy.effective_instances(
                context, target_id, FENG_SHI_ZHEN_MODIFIER_STATE_ID
            ):
                if state.source_skill_id != FENG_SHI_ZHEN_SKILL_ID:
                    continue
                params = state.runtime_params
                if not isinstance(params, FengShiZhenModifierParams):
                    raise TypeError("invalid Feng Shi Zhen runtime modifier params")
                rate = getattr(params, rate_attr)
                if rate == 0.0:
                    continue
                if phase is DamageModifierPhase.OUTGOING:
                    kind = (
                        DamageModifierKind.OUTGOING_INCREASE
                        if rate > 0
                        else DamageModifierKind.OUTGOING_REDUCTION
                    )
                else:
                    kind = (
                        DamageModifierKind.INCOMING_INCREASE
                        if rate > 0
                        else DamageModifierKind.INCOMING_REDUCTION
                    )
                origin = f"{self.provider_key}:{state.instance_id}:{phase.value}"
                modifiers.append(
                    DamageModifierContribution(
                        phase=phase,
                        kind=kind,
                        operation=DamageModifierOperation.MULTIPLY_FACTOR,
                        operand=1.0 + rate,
                        source=RuleContributionSource(
                            state.owner_id,
                            state.source_id,
                            state.source_skill_id,
                            state.state_id,
                            state.instance_id,
                            origin,
                        ),
                        order_key=origin,
                        damage_types=frozenset(
                            (DamageType.WEAPON, DamageType.STRATEGY)
                        ),
                    )
                )
        return DamageRuleCollection(
            base.prevention_contributions,
            base.hit_contributions,
            base.formula_policy_contributions,
            tuple(modifiers),
        )
