from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .context import BattleContext
from .enums import BattlePhase
from .formation_admission import (
    FormationAdmissionRejectedError,
    FormationAdmissionStatus,
    admit_and_install_formation_skill,
    validate_team_formation_limits,
    validate_formation_admissions,
)
from .pre_battle_order import PreBattleOrderSystem
from .skill_definition import SkillType
from .skill_runtime import SkillRuntime
from .troop_admission import process_pre_battle_troop_skills

if TYPE_CHECKING:
    from .battle_systems import BattleSystems


# Hooks for Stage 14/15 extension without baking premature gameplay
PassiveSkillProcessor = Callable[[BattleContext, object], None]
CommandSkillProcessor = Callable[[BattleContext, object], None]

_CUSTOM_PASSIVE_PROCESSORS: list[PassiveSkillProcessor] = []
_CUSTOM_COMMAND_PROCESSORS: list[CommandSkillProcessor] = []


def register_pre_battle_passive_processor(processor: PassiveSkillProcessor) -> None:
    if not callable(processor):
        raise TypeError("processor must be callable")
    if processor not in _CUSTOM_PASSIVE_PROCESSORS:
        _CUSTOM_PASSIVE_PROCESSORS.append(processor)


def unregister_pre_battle_passive_processor(processor: PassiveSkillProcessor) -> None:
    if processor in _CUSTOM_PASSIVE_PROCESSORS:
        _CUSTOM_PASSIVE_PROCESSORS.remove(processor)


def register_pre_battle_command_processor(processor: CommandSkillProcessor) -> None:
    if not callable(processor):
        raise TypeError("processor must be callable")
    if processor not in _CUSTOM_COMMAND_PROCESSORS:
        _CUSTOM_COMMAND_PROCESSORS.append(processor)


def unregister_pre_battle_command_processor(processor: CommandSkillProcessor) -> None:
    if processor in _CUSTOM_COMMAND_PROCESSORS:
        _CUSTOM_COMMAND_PROCESSORS.remove(processor)


def process_pre_battle_passive_skills(context: BattleContext, systems: object) -> None:
    """Stage 1: PASSIVE skills execution (RULE-01).

    Executes enabled PASSIVE skills in deterministic pre-battle speed order.
    """
    order_system = PreBattleOrderSystem(systems.attribute_system)
    passive_owner_ids = {
        rt.owner_id for rt in context.skill_runtimes.values()
        if rt.definition.skill_type == SkillType.PASSIVE and rt.enabled
    }
    ordered_units = order_system.determine_order(
        context, units=[u for u in context.units.values() if u.unit_id in passive_owner_ids]
    )

    # Process by unit in order
    for unit in ordered_units:
        unit_passives = [
            rt for rt in context.skill_runtimes.values()
            if rt.owner_id == unit.unit_id
            and rt.definition.skill_type == SkillType.PASSIVE
            and rt.enabled
        ]
        # Resolve via standard skill resolver
        for rt in unit_passives:
            if hasattr(systems, "skill_resolver") and hasattr(systems, "effect_executor"):
                res = systems.skill_resolver.resolve(context, rt)
                for effect in res.effects:
                    systems.effect_executor.execute(context, effect)

    for processor in tuple(_CUSTOM_PASSIVE_PROCESSORS):
        processor(context, systems)


def process_pre_battle_formation_skills(context: BattleContext, systems: object) -> None:
    """Stage 2: FORMATION skills execution (RULE-01, RULE-03, RULE-04).

    1. Fail-closed global preflight: each team can have at most 1 enabled formation.
    2. Determine unit execution order using PreBattleOrderSystem (speed desc, attacker first).
    3. Admit and install each formation skill in order.
    """
    # RULE-03 Fail-closed team limit preflight
    validate_team_formation_limits(context)

    formation_runtimes = [
        rt for rt in context.skill_runtimes.values()
        if rt.definition.skill_type == SkillType.FORMATION and rt.enabled
    ]
    if not formation_runtimes:
        return

    # Order units owning formation skills by PreBattleOrderSystem
    order_system = PreBattleOrderSystem(systems.attribute_system)
    formation_owners = [
        context.get_unit(rt.owner_id) for rt in formation_runtimes
        if context.get_unit(rt.owner_id) is not None
    ]
    ordered_owners = order_system.determine_order(context, units=formation_owners)

    # Process in deterministic order
    for unit in ordered_owners:
        unit_formations = [
            rt for rt in formation_runtimes if rt.owner_id == unit.unit_id
        ]
        for rt in unit_formations:
            res = admit_and_install_formation_skill(context, systems, rt)
            if res.status != FormationAdmissionStatus.SUCCESS:
                raise FormationAdmissionRejectedError(
                    status=res.status,
                    skill_id=res.skill_id,
                    owner_id=res.owner_id,
                    reason=res.reason,
                )


def process_pre_battle_command_skills(context: BattleContext, systems: object) -> None:
    """Stage 4: COMMAND skills execution (RULE-01).

    Executes enabled COMMAND skills in deterministic pre-battle speed order.
    """
    order_system = PreBattleOrderSystem(systems.attribute_system)
    command_owner_ids = {
        rt.owner_id for rt in context.skill_runtimes.values()
        if rt.definition.skill_type == SkillType.COMMAND and rt.enabled
    }
    ordered_units = order_system.determine_order(
        context, units=[u for u in context.units.values() if u.unit_id in command_owner_ids]
    )

    for unit in ordered_units:
        unit_commands = [
            rt for rt in context.skill_runtimes.values()
            if rt.owner_id == unit.unit_id
            and rt.definition.skill_type == SkillType.COMMAND
            and rt.enabled
        ]
        for rt in unit_commands:
            if hasattr(systems, "skill_resolver") and hasattr(systems, "effect_executor"):
                res = systems.skill_resolver.resolve(context, rt)
                for effect in res.effects:
                    systems.effect_executor.execute(context, effect)

    for processor in tuple(_CUSTOM_COMMAND_PROCESSORS):
        processor(context, systems)


def run_pre_battle_preparation_phases(context: BattleContext, systems: object) -> None:
    """Orchestrate the 4-phase preparation sequence (RULE-01):
    PASSIVE -> FORMATION -> TROOP -> COMMAND
    """
    # Fail closed for the *entire* battle before PASSIVE or any RNG-consuming
    # setup can execute. Formation admission itself rechecks just-in-time.
    validate_formation_admissions(context)
    process_pre_battle_passive_skills(context, systems)
    process_pre_battle_formation_skills(context, systems)
    process_pre_battle_troop_skills(context, systems)
    process_pre_battle_command_skills(context, systems)
