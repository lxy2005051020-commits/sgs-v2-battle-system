from __future__ import annotations

from dataclasses import dataclass
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
    status: EffectExecutionStatus = EffectExecutionStatus.RESOLVED


@dataclass(frozen=True, slots=True)
class ApplyStateEffectResult:
    effect: ApplyStateEffect
    state_instance: StateInstance
    status: EffectExecutionStatus = EffectExecutionStatus.RESOLVED


@dataclass(frozen=True, slots=True)
class RemoveStateEffectResult:
    effect: RemoveStateEffect
    removed_state: StateInstance
    status: EffectExecutionStatus = EffectExecutionStatus.RESOLVED


@dataclass(frozen=True, slots=True)
class DeferredEffectResult:
    effect: RecoverEffect
    reason: str
    status: EffectExecutionStatus = EffectExecutionStatus.DEFERRED


EffectExecutionResult = (
    DamageEffectResult
    | ApplyStateEffectResult
    | RemoveStateEffectResult
    | DeferredEffectResult
)
