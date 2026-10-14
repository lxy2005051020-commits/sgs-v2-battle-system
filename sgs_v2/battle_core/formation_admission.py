from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .context import BattleContext
from .enums import BattlePhase, TroopType
from .provider_identity import SkillProviderRef
from .skill_definition import SkillDefinition, SkillType
from .skill_runtime import SkillRuntime, SkillSlot
from .unit import UnitRuntime


class FormationAdmissionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED_PHASE_ILLEGAL = "REJECTED_PHASE_ILLEGAL"
    REJECTED_ALREADY_INSTALLED = "REJECTED_ALREADY_INSTALLED"
    REJECTED_BASELINE_DISABLED = "REJECTED_BASELINE_DISABLED"
    REJECTED_NOT_FOUND = "REJECTED_NOT_FOUND"
    REJECTED_NOT_FORMATION = "REJECTED_NOT_FORMATION"
    REJECTED_INVALID_TROOP = "REJECTED_INVALID_TROOP"
    REJECTED_TEAM_FORMATION_EXCEEDED = "REJECTED_TEAM_FORMATION_EXCEEDED"
    REJECTED_PROVIDER_SLOT_CONFLICT = "REJECTED_PROVIDER_SLOT_CONFLICT"


class FormationAdmissionRejectedError(RuntimeError):
    """Raised when formation skill admission fails or team exceeds formation limit (RULE-03)."""

    def __init__(
        self,
        status: FormationAdmissionStatus,
        skill_id: str,
        owner_id: str,
        reason: str | None = None,
    ) -> None:
        super().__init__(
            f"Formation skill admission rejected: status={status}, skill_id={skill_id}, owner_id={owner_id}, reason={reason}"
        )
        self.status = status
        self.skill_id = skill_id
        self.owner_id = owner_id
        self.reason = reason


@dataclass(frozen=True, slots=True)
class FormationAdmissionResult:
    status: FormationAdmissionStatus
    skill_id: str
    owner_id: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class FormationSkillConfig:
    """Static metadata for registered canonical formation definitions (F0-I-A-01)."""

    skill_id: str
    name: str
    applicable_troops: tuple[TroopType, ...]
    definition_factory: Callable[[], SkillDefinition]
    requires_provider_slot: bool = False
    definition_resolver: Callable[[BattleContext, object, UnitRuntime], SkillDefinition] | None = None
    installer: Callable[[BattleContext, object, SkillRuntime], None] | None = None
    # Pure configuration check, also called before any opening passive effects.
    validator: Callable[[BattleContext, SkillRuntime], None] | None = None


# Canonical Formation Registry: keyed strictly by canonical skill_id
# Gameplay configurations register below; effects require an equipped runtime.
FORMATION_SKILL_REGISTRY: dict[str, FormationSkillConfig] = {}


def register_formation_skill_config(config: FormationSkillConfig) -> None:
    if not isinstance(config, FormationSkillConfig):
        raise TypeError(f"config must be a FormationSkillConfig, got {type(config)}")
    if not config.skill_id or not config.skill_id.strip():
        raise ValueError("skill_id cannot be empty")
    if config.skill_id in FORMATION_SKILL_REGISTRY:
        raise ValueError(f"formation skill id already registered: {config.skill_id}")
    FORMATION_SKILL_REGISTRY[config.skill_id] = config


def unregister_formation_skill_config(skill_id: str) -> None:
    FORMATION_SKILL_REGISTRY.pop(skill_id, None)


def validate_team_formation_limits(context: BattleContext) -> None:
    """Fail-closed on >1 carried FORMATION per team, including disabled runtimes (RULE-03)."""
    team_formations: dict[str, list[SkillRuntime]] = {}
    for rt in context.skill_runtimes.values():
        if rt.definition.skill_type == SkillType.FORMATION:
            owner = context.units.get(rt.owner_id)
            if owner is not None:
                team_formations.setdefault(owner.team_id, []).append(rt)

    for team_id, runtimes in team_formations.items():
        if len(runtimes) > 1:
            first_rt = runtimes[0]
            raise FormationAdmissionRejectedError(
                status=FormationAdmissionStatus.REJECTED_TEAM_FORMATION_EXCEEDED,
                skill_id=first_rt.definition.skill_id,
                owner_id=first_rt.owner_id,
                reason=f"Team {team_id} exceeds formation limit: {len(runtimes)} formations found (max 1 per team)",
            )


def validate_formation_admissions(context: BattleContext) -> None:
    """Validate *all* loaded formation configurations before any PRE_BATTLE effects.

    Global fail-closed preflight prevents passive skills (including random
    producers) from running when either side has an invalid formation.
    """
    validate_team_formation_limits(context)
    for runtime in context.skill_runtimes.values():
        if runtime.definition.skill_type != SkillType.FORMATION:
            continue
        result = _check_formation_admission(context, runtime)
        if result.status not in (
            FormationAdmissionStatus.SUCCESS,
            FormationAdmissionStatus.REJECTED_BASELINE_DISABLED,
        ):
            raise FormationAdmissionRejectedError(
                result.status, result.skill_id, result.owner_id, result.reason
            )


def _check_formation_admission(
    context: BattleContext,
    runtime: SkillRuntime,
) -> FormationAdmissionResult:
    """Pure preflight: no effects, runtime mutation, state mutation or RNG."""
    # 1. Phase Guard
    if context.current_phase != BattlePhase.PRE_BATTLE.value:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_PHASE_ILLEGAL,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"Formation skills can only be admitted during PRE_BATTLE phase, current phase is {context.current_phase}",
        )

    # 2. SkillType Guard
    if runtime.definition.skill_type != SkillType.FORMATION:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_NOT_FORMATION,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"Skill '{runtime.definition.skill_id}' is not of type FORMATION",
        )

    # 3. Enabled Guard
    if not runtime.enabled:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_BASELINE_DISABLED,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="baseline-disabled formation runtime is not admitted",
        )

    # 4. Owner existence
    owner = context.units.get(runtime.owner_id)
    if owner is None:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"owner unit '{runtime.owner_id}' not found in battle context",
        )

    # 5. Canonical Lookup
    cfg = FORMATION_SKILL_REGISTRY.get(runtime.definition.skill_id)
    if cfg is None:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"canonical formation skill '{runtime.definition.skill_id}' not found in registry",
        )

    if runtime.definition.name != cfg.name:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="runtime definition name does not match canonical formation registry",
        )

    # 6. Team Exclusivity (RULE-03)
    team_units = [u for u in context.units.values() if u.team_id == owner.team_id]
    team_unit_ids = {u.unit_id for u in team_units}
    team_formations = [
        rt for rt in context.skill_runtimes.values()
        if rt.definition.skill_type == SkillType.FORMATION
        and rt.enabled
        and rt.owner_id in team_unit_ids
    ]
    if len(team_formations) > 1:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_TEAM_FORMATION_EXCEEDED,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason=f"Team '{owner.team_id}' exceeds formation limit: {len(team_formations)} formations found",
        )

    # 7. Applicable Troop Compatibility
    if cfg.applicable_troops:
        for u in team_units:
            if u.troop_type not in cfg.applicable_troops:
                return FormationAdmissionResult(
                    status=FormationAdmissionStatus.REJECTED_INVALID_TROOP,
                    skill_id=runtime.definition.skill_id,
                    owner_id=runtime.owner_id,
                    reason=(
                        f"Team troop incompatibility: unit '{u.unit_id}' has troop type "
                        f"'{u.troop_type.value if u.troop_type else 'None'}', "
                        f"not in applicable troops {[t.value for t in cfg.applicable_troops]}"
                    ),
                )

    # 8. Slot consistency and mandatory provider provenance
    if runtime.skill_slot is None:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="formation installation requires canonical provider SkillSlot",
        )
    if runtime.skill_slot is not None:
        resident = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
        if resident is not None and resident is not runtime:
            return FormationAdmissionResult(
                status=FormationAdmissionStatus.REJECTED_PROVIDER_SLOT_CONFLICT,
                skill_id=runtime.definition.skill_id,
                owner_id=runtime.owner_id,
                reason="provider slot already belongs to another runtime",
            )

    installed = context.metadata.get("_stage14_installed_formation_keys")
    identity = (runtime.owner_id, runtime.skill_slot, runtime.definition.skill_id)
    if installed is not None and identity in installed:
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_ALREADY_INSTALLED,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="formation already installed in this battle",
        )

    if cfg.validator is not None:
        cfg.validator(context, runtime)

    return FormationAdmissionResult(
        status=FormationAdmissionStatus.SUCCESS,
        skill_id=runtime.definition.skill_id,
        owner_id=runtime.owner_id,
    )


def admit_and_install_formation_skill(
    context: BattleContext,
    systems: object,
    runtime: SkillRuntime,
) -> FormationAdmissionResult:
    """Universal formation admission preflight and installation seam (RULE-03, F0-I-A-02).

    Atomic admission:
    1. Phase Guard: only PRE_BATTLE permitted.
    2. SkillType Guard: must be SkillType.FORMATION.
    3. Baseline-disabled check.
    4. Canonical Registry lookup.
    5. Unit & Team Invariant check (applicable troop types, team formation exclusivity).
    6. Slot & Provider check.
    7. Resolve & execute effects via SkillResolver and EffectExecutor.
    8. Register with defeat cleanup if provider tracking is active.
    """
    # All admission checks remain side-effect free.
    check = _check_formation_admission(context, runtime)
    if check.status != FormationAdmissionStatus.SUCCESS:
        return check
    owner = context.get_unit(runtime.owner_id)
    cfg = FORMATION_SKILL_REGISTRY[runtime.definition.skill_id]

    # 9. Dynamic resolution if defined
    effective_definition = (
        cfg.definition_resolver(context, systems, owner)
        if cfg.definition_resolver is not None
        else cfg.definition_factory()
    )
    # Reject mismatched registry factories/resolvers before any mutation.
    if (effective_definition.skill_id != cfg.skill_id
            or effective_definition.skill_type != SkillType.FORMATION
            or effective_definition.name != cfg.name):
        return FormationAdmissionResult(
            status=FormationAdmissionStatus.REJECTED_NOT_FOUND,
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            reason="formation factory returned mismatched canonical identity",
        )

    effective_runtime = SkillRuntime(
        definition=effective_definition,
        owner_id=runtime.owner_id,
        skill_slot=runtime.skill_slot,
        enabled=runtime.enabled,
    )

    # 10. Register runtime in context if not yet present
    if runtime.skill_slot is not None:
        existing = context.skill_runtimes.get(runtime.owner_id, runtime.skill_slot)
        if existing is None:
            context.skill_runtimes.register(runtime)

    # 11. Role-aware gameplay uses a declared canonical lifecycle installer.
    # Synthetic/default formations preserve the existing SkillResolver route.
    if cfg.installer is not None:
        cfg.installer(context, systems, effective_runtime)
    elif hasattr(systems, "skill_resolver") and hasattr(systems, "effect_executor"):
        res = systems.skill_resolver.resolve(context, effective_runtime)
        for effect in res.effects:
            systems.effect_executor.execute(context, effect)

    # Idempotence guard is battle-scoped; SkillRuntimeRegistry remains the
    # authoritative instance store, this records only completed installations.
    installed = context.metadata.setdefault("_stage14_installed_formation_keys", set())
    installed.add((runtime.owner_id, runtime.skill_slot, runtime.definition.skill_id))

    return FormationAdmissionResult(
        status=FormationAdmissionStatus.SUCCESS,
        skill_id=runtime.definition.skill_id,
        owner_id=runtime.owner_id,
    )


# First production Formation skill (Stage14 F1). The registry is definition-only;
from .yu_lin_zhen import (YU_LIN_ZHEN_SKILL_ID, YU_LIN_ZHEN_NAME,
    YU_LIN_ZHEN_APPLICABLE_TROOPS, create_yu_lin_zhen_definition,
    install_yu_lin_zhen, validate_yu_lin_zhen)

register_formation_skill_config(FormationSkillConfig(
    YU_LIN_ZHEN_SKILL_ID, YU_LIN_ZHEN_NAME, YU_LIN_ZHEN_APPLICABLE_TROOPS,
    create_yu_lin_zhen_definition, requires_provider_slot=True,
    installer=install_yu_lin_zhen, validator=validate_yu_lin_zhen))

from .qian_long_zhen import (QIAN_LONG_ZHEN_SKILL_ID, QIAN_LONG_ZHEN_NAME,
    QIAN_LONG_ZHEN_APPLICABLE_TROOPS, create_qian_long_zhen_definition, install_qian_long_zhen)

register_formation_skill_config(FormationSkillConfig(
    QIAN_LONG_ZHEN_SKILL_ID, QIAN_LONG_ZHEN_NAME, QIAN_LONG_ZHEN_APPLICABLE_TROOPS,
    create_qian_long_zhen_definition, requires_provider_slot=True, installer=install_qian_long_zhen))

from .ji_xing_zhen import (
    JI_XING_ZHEN_SKILL_ID, JI_XING_ZHEN_NAME, JI_XING_ZHEN_APPLICABLE_TROOPS,
    create_ji_xing_zhen_definition, install_ji_xing_zhen,
)

register_formation_skill_config(FormationSkillConfig(
    skill_id=JI_XING_ZHEN_SKILL_ID, name=JI_XING_ZHEN_NAME,
    applicable_troops=JI_XING_ZHEN_APPLICABLE_TROOPS,
    definition_factory=create_ji_xing_zhen_definition,
    requires_provider_slot=True, installer=install_ji_xing_zhen,
))

# it does not install any effect unless a team actually equips Skill ID 20066.
from .feng_shi_zhen import (
    FENG_SHI_ZHEN_SKILL_ID,
    FENG_SHI_ZHEN_NAME,
    FENG_SHI_ZHEN_APPLICABLE_TROOPS,
    create_feng_shi_zhen_definition,
    install_feng_shi_zhen,
)

register_formation_skill_config(
    FormationSkillConfig(
        skill_id=FENG_SHI_ZHEN_SKILL_ID,
        name=FENG_SHI_ZHEN_NAME,
        applicable_troops=FENG_SHI_ZHEN_APPLICABLE_TROOPS,
        definition_factory=create_feng_shi_zhen_definition,
        requires_provider_slot=True,
        installer=install_feng_shi_zhen,
    )
)

from .wu_feng_zhen import (WU_FENG_ZHEN_SKILL_ID, WU_FENG_ZHEN_NAME,
    WU_FENG_ZHEN_APPLICABLE_TROOPS, create_wu_feng_zhen_definition, install_wu_feng_zhen)

register_formation_skill_config(FormationSkillConfig(
    WU_FENG_ZHEN_SKILL_ID, WU_FENG_ZHEN_NAME, WU_FENG_ZHEN_APPLICABLE_TROOPS,
    create_wu_feng_zhen_definition, requires_provider_slot=True, installer=install_wu_feng_zhen))
from .ba_men_jin_suo_zhen import (
    BA_MEN_JIN_SUO_ZHEN_SKILL_ID, BA_MEN_JIN_SUO_ZHEN_NAME,
    BA_MEN_APPLICABLE_TROOPS, create_ba_men_jin_suo_zhen_definition,
    install_ba_men_jin_suo_zhen,
)

register_formation_skill_config(FormationSkillConfig(
    skill_id=BA_MEN_JIN_SUO_ZHEN_SKILL_ID,
    name=BA_MEN_JIN_SUO_ZHEN_NAME,
    applicable_troops=BA_MEN_APPLICABLE_TROOPS,
    definition_factory=create_ba_men_jin_suo_zhen_definition,
    requires_provider_slot=True,
    installer=install_ba_men_jin_suo_zhen,
))
from .san_shi_zhen import (SAN_SHI_ZHEN_SKILL_ID, SAN_SHI_ZHEN_NAME,
    SAN_SHI_ZHEN_APPLICABLE_TROOPS, create_san_shi_zhen_definition, install_san_shi_zhen)

register_formation_skill_config(FormationSkillConfig(
    skill_id=SAN_SHI_ZHEN_SKILL_ID, name=SAN_SHI_ZHEN_NAME,
    applicable_troops=SAN_SHI_ZHEN_APPLICABLE_TROOPS,
    definition_factory=create_san_shi_zhen_definition,
    requires_provider_slot=True, installer=install_san_shi_zhen))

from .xing_yi_zhen import (XING_YI_ZHEN_SKILL_ID, XING_YI_ZHEN_NAME,
    XING_YI_ZHEN_APPLICABLE_TROOPS, create_xing_yi_zhen_definition, install_xing_yi_zhen)

register_formation_skill_config(FormationSkillConfig(
    skill_id=XING_YI_ZHEN_SKILL_ID, name=XING_YI_ZHEN_NAME,
    applicable_troops=XING_YI_ZHEN_APPLICABLE_TROOPS,
    definition_factory=create_xing_yi_zhen_definition,
    requires_provider_slot=True, installer=install_xing_yi_zhen))

from .yan_xing_zhen import (YAN_XING_ZHEN_SKILL_ID, YAN_XING_ZHEN_NAME,
    YAN_XING_ZHEN_APPLICABLE_TROOPS, create_yan_xing_zhen_definition,
    install_yan_xing_zhen, validate_yan_xing_zhen)

register_formation_skill_config(FormationSkillConfig(
    YAN_XING_ZHEN_SKILL_ID, YAN_XING_ZHEN_NAME, YAN_XING_ZHEN_APPLICABLE_TROOPS,
    create_yan_xing_zhen_definition, requires_provider_slot=True,
    installer=install_yan_xing_zhen, validator=validate_yan_xing_zhen))
