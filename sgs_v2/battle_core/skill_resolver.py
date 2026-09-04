from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .effects import ApplyStateEffect, DamageEffect, Effect
from .enums import DamageSourceType
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec,
    SkillEffectSpec,
    SkillTargetMode,
)
from .skill_runtime import SkillRuntime
from .target_system import TargetSystem
from .unit import UnitRuntime


class SkillResolutionStatus(str, Enum):
    DISABLED = "DISABLED"
    NO_VALID_TARGET = "NO_VALID_TARGET"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True, slots=True)
class SkillResolutionResult:
    """一次明确技能解析尝试的不可变结果。"""

    skill_id: str
    owner_id: str
    status: SkillResolutionStatus
    target_ids: tuple[str, ...]
    effects: tuple[Effect, ...]

    def __post_init__(self) -> None:
        if not self.skill_id:
            raise ValueError("skill_id cannot be empty")
        if not self.owner_id:
            raise ValueError("owner_id cannot be empty")

        target_ids = tuple(self.target_ids)
        effects = tuple(self.effects)
        object.__setattr__(self, "target_ids", target_ids)
        object.__setattr__(self, "effects", effects)

        if self.status is SkillResolutionStatus.RESOLVED:
            if not target_ids:
                raise ValueError("RESOLVED result must contain target_ids")
            if not effects:
                raise ValueError("RESOLVED result must contain effects")
        elif target_ids or effects:
            raise ValueError(
                f"{self.status.value} result must not contain targets or effects"
            )


class SkillResolver:
    """把一次显式技能解析转换成有序 Effect，不执行任何 Effect。"""

    def __init__(self, target_system: TargetSystem) -> None:
        self._target_system = target_system

    def resolve(
        self,
        context: BattleContext,
        runtime: SkillRuntime,
    ) -> SkillResolutionResult:
        definition = runtime.definition

        if not runtime.enabled:
            return self._empty_result(runtime, SkillResolutionStatus.DISABLED)

        owner = context.get_unit(runtime.owner_id)
        candidates = self._candidate_units(
            context,
            owner,
            definition.target_mode,
        )
        if not candidates:
            return self._empty_result(
                runtime,
                SkillResolutionStatus.NO_VALID_TARGET,
            )

        if definition.activation_rate == 0.0:
            return self._empty_result(
                runtime,
                SkillResolutionStatus.ACTIVATION_FAILED,
            )
        if (
            definition.activation_rate < 1.0
            and not context.random.chance(definition.activation_rate)
        ):
            return self._empty_result(
                runtime,
                SkillResolutionStatus.ACTIVATION_FAILED,
            )

        selected = self._select_targets(
            context,
            candidates,
            definition.target_mode,
        )
        target_ids = tuple(unit.unit_id for unit in selected)
        effects = tuple(
            self._build_effect(
                runtime=runtime,
                target=target,
                spec=spec,
            )
            for target in selected
            for spec in definition.effect_specs
        )

        return SkillResolutionResult(
            skill_id=definition.skill_id,
            owner_id=runtime.owner_id,
            status=SkillResolutionStatus.RESOLVED,
            target_ids=target_ids,
            effects=effects,
        )

    def _candidate_units(
        self,
        context: BattleContext,
        owner: UnitRuntime,
        target_mode: SkillTargetMode,
    ) -> list[UnitRuntime]:
        if target_mode is SkillTargetMode.SINGLE_RANDOM_ENEMY:
            return self._target_system.enemies(
                context,
                owner,
                alive_only=True,
            )
        raise ValueError(f"unsupported target mode: {target_mode}")

    def _select_targets(
        self,
        context: BattleContext,
        candidates: list[UnitRuntime],
        target_mode: SkillTargetMode,
    ) -> list[UnitRuntime]:
        if target_mode is SkillTargetMode.SINGLE_RANDOM_ENEMY:
            return self._target_system.random_units(
                context,
                candidates,
                count=1,
            )
        raise ValueError(f"unsupported target mode: {target_mode}")

    @staticmethod
    def _build_effect(
        *,
        runtime: SkillRuntime,
        target: UnitRuntime,
        spec: SkillEffectSpec,
    ) -> Effect:
        definition = runtime.definition
        if isinstance(spec, DamageSkillEffectSpec):
            return DamageEffect(
                source_id=runtime.owner_id,
                target_id=target.unit_id,
                damage_type=spec.damage_type,
                source_type=DamageSourceType.SKILL,
                coefficient=spec.coefficient,
                source_skill_id=definition.skill_id,
            )
        if isinstance(spec, ApplyStateSkillEffectSpec):
            return ApplyStateEffect(
                state_id=spec.state_id,
                owner_id=target.unit_id,
                source_id=runtime.owner_id,
                source_skill_id=definition.skill_id,
            )
        raise TypeError(f"unsupported skill effect spec: {type(spec).__name__}")

    @staticmethod
    def _empty_result(
        runtime: SkillRuntime,
        status: SkillResolutionStatus,
    ) -> SkillResolutionResult:
        return SkillResolutionResult(
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            status=status,
            target_ids=(),
            effects=(),
        )
