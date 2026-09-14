from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .operation_identity import NormalAttackInstanceId, TargetResolutionId
from .stage9_state_runtime import Stage9StateRuntime
from .target_system import TargetSystem
from .unit import UnitRuntime

if TYPE_CHECKING:
    from .context import BattleContext


class RedirectReason(str, Enum):
    NONE = "NONE"
    GUARD = "GUARD"


@dataclass(frozen=True, slots=True)
class TargetResolutionResult:
    """Immutable result of a single NormalAttack target resolution."""

    resolution_id: TargetResolutionId
    normal_attack_id: NormalAttackInstanceId
    intended_attack_target: str
    post_redirect_actual_target: str
    redirect_source: str | None
    redirect_reason: RedirectReason

    def __post_init__(self) -> None:
        if not isinstance(self.resolution_id, TargetResolutionId):
            raise TypeError(
                f"resolution_id must be a TargetResolutionId, got {type(self.resolution_id)}"
            )
        if not isinstance(self.normal_attack_id, NormalAttackInstanceId):
            raise TypeError(
                f"normal_attack_id must be a NormalAttackInstanceId, got {type(self.normal_attack_id)}"
            )
        if (
            not isinstance(self.intended_attack_target, str)
            or not self.intended_attack_target.strip()
        ):
            raise ValueError("intended_attack_target must be a non-empty str")
        if (
            not isinstance(self.post_redirect_actual_target, str)
            or not self.post_redirect_actual_target.strip()
        ):
            raise ValueError("post_redirect_actual_target must be a non-empty str")
        if not isinstance(self.redirect_reason, RedirectReason):
            raise TypeError(
                f"redirect_reason must be a RedirectReason, got {type(self.redirect_reason)}"
            )
        if self.redirect_source is not None:
            if (
                not isinstance(self.redirect_source, str)
                or not self.redirect_source.strip()
            ):
                raise ValueError("redirect_source must be a non-empty str when provided")

        if self.redirect_reason is RedirectReason.NONE:
            if self.redirect_source is not None:
                raise ValueError(
                    "redirect_source must be None when redirect_reason is NONE"
                )
            if self.intended_attack_target != self.post_redirect_actual_target:
                raise ValueError(
                    "intended_attack_target and post_redirect_actual_target must match when redirect_reason is NONE"
                )
        elif self.redirect_reason is RedirectReason.GUARD:
            if self.redirect_source is None:
                raise ValueError(
                    "redirect_source is required when redirect_reason is GUARD"
                )


class TargetResolutionSystem:
    """Orchestrates NormalAttack target resolution and arbitration.

    Pipeline:
      1. build live legal pool through TargetSystem
      2. camp / legality filtering
      3. Confusion selector arbitration
      4. else Taunt selector arbitration
      5. else default selector through TargetSystem/RandomSystem
      6. freeze intended_attack_target
      7. Guard redirect exactly once
      8. freeze post_redirect_actual_target
      9. return immutable TargetResolutionResult
    """

    def __init__(
        self,
        target_system: TargetSystem,
        state_runtime: Stage9StateRuntime,
    ) -> None:
        self._target_system = target_system
        self._state_runtime = state_runtime

    def resolve(
        self,
        context: BattleContext,
        attacker: UnitRuntime | str,
        *,
        normal_attack_id: NormalAttackInstanceId,
        resolution_id: TargetResolutionId | None = None,
    ) -> TargetResolutionResult | None:
        if normal_attack_id is None:
            raise TypeError("normal_attack_id is required and cannot be None")
        if not isinstance(normal_attack_id, NormalAttackInstanceId):
            raise TypeError(
                f"normal_attack_id must be a NormalAttackInstanceId, got {type(normal_attack_id)}"
            )

        attacker_unit = (
            attacker
            if isinstance(attacker, UnitRuntime)
            else context.get_unit(attacker)
        )
        attacker_id = attacker_unit.unit_id

        if resolution_id is None:
            resolution_id = context.id_allocator.allocate_target_resolution_id()

        # Step 1 & 2: build live legal pool and legality filtering
        # Confusion removes side constraint, but preserves alive and exclude self.
        # Precedence: Confusion > Taunt > default
        confusion = self._state_runtime.get_operational_confusion(context, attacker_id)
        intended_target_id: str | None = None

        if confusion is not None:
            # Step 3: Confusion selector arbitration
            # Candidates built using TargetSystem primitives: allies (excluding self) + enemies
            allies = self._target_system.allies(
                context, attacker_unit, alive_only=True, include_self=False
            )
            enemies = self._target_system.enemies(
                context, attacker_unit, alive_only=True
            )
            candidates = allies + enemies
            if not candidates:
                return None
            chosen = self._target_system.random_units(context, candidates, count=1)
            if not chosen:
                return None
            intended_target_id = chosen[0].unit_id
        else:
            # Step 4: Taunt selector arbitration
            taunt = self._state_runtime.get_operational_taunt(context, attacker_id)
            if taunt is not None:
                taunt_target_id = self._state_runtime.get_taunt_target_unit_id(taunt)
                if taunt_target_id is not None:
                    taunt_target_unit = context.get_unit(taunt_target_id)
                    if taunt_target_unit.is_alive and taunt_target_id != attacker_id:
                        intended_target_id = taunt_target_id

            # Step 5: Else default selector
            if intended_target_id is None:
                chosen_enemy = self._target_system.random_enemy(context, attacker_unit)
                if chosen_enemy is None:
                    return None
                intended_target_id = chosen_enemy.unit_id

        # Step 6: freeze intended_attack_target

        # Step 7: Guard redirect exactly once
        protector_id = self._state_runtime.get_guard_protector(
            context,
            intended_target_id,
            attacker_id=attacker_id,
        )

        if protector_id is not None and protector_id != intended_target_id:
            # Step 8: freeze post_redirect_actual_target with Guard redirect
            post_redirect_actual_target = protector_id
            redirect_source = protector_id
            redirect_reason = RedirectReason.GUARD
        else:
            post_redirect_actual_target = intended_target_id
            redirect_source = None
            redirect_reason = RedirectReason.NONE

        # Step 9: return immutable TargetResolutionResult
        return TargetResolutionResult(
            resolution_id=resolution_id,
            normal_attack_id=normal_attack_id,
            intended_attack_target=intended_target_id,
            post_redirect_actual_target=post_redirect_actual_target,
            redirect_source=redirect_source,
            redirect_reason=redirect_reason,
        )
