from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .damage_resolution_system import DamageResolutionResult
from .effects import ApplyStateEffect, DamageEffect, RecoverEffect, RemoveStateEffect
from .state_instance import StateInstance


class EffectExecutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True, slots=True)
class DamageEffectResult:
    effect: DamageEffect
    resolution: DamageResolutionResult
    status: EffectExecutionStatus = field(
        default=EffectExecutionStatus.RESOLVED,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class ApplyStateEffectResult:
    effect: ApplyStateEffect
    state_instance: StateInstance
    status: EffectExecutionStatus = field(
        default=EffectExecutionStatus.RESOLVED,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class RemoveStateEffectResult:
    effect: RemoveStateEffect
    removed_state: StateInstance
    status: EffectExecutionStatus = field(
        default=EffectExecutionStatus.RESOLVED,
        init=False,
    )


@dataclass(frozen=True, slots=True)
class DeferredEffectResult:
    effect: RecoverEffect
    reason: str
    status: EffectExecutionStatus = field(
        default=EffectExecutionStatus.DEFERRED,
        init=False,
    )


EffectExecutionResult = (
    DamageEffectResult
    | ApplyStateEffectResult
    | RemoveStateEffectResult
    | DeferredEffectResult
)
