"""Typed received-recovery contributions through the existing modifier seam.

RecoverySystem remains the sole owner of rounding, prevention and capacity.
"""
from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .equipment_effectiveness import (
    EquipmentEffectivenessBoundaryError, EquipmentEffectivenessPolicy,
    EquipmentEffectivenessStatus,
)
from .recovery_system import RecoveryModifierContribution, RecoveryModifierProvider, RecoveryRequest
from .stage9_integerization import ExactRatio
from .state_effectiveness import StateEffectivenessPolicy
from .state_runtime_params import StateRuntimeParams


RECEIVED_RECOVERY_BONUS_STATE_ID = "runtime_received_recovery_bonus"


@dataclass(frozen=True, slots=True)
class ReceivedRecoveryBonusParams(StateRuntimeParams):
    rate: ExactRatio

    def __post_init__(self) -> None:
        if not isinstance(self.rate, ExactRatio):
            raise TypeError("rate must be ExactRatio")
        if self.rate.numerator < 0:
            raise ValueError("received recovery bonus must be nonnegative")


class ReceivedRecoveryModifierProvider:
    """Add target deltas to an existing final recovery-modifier ratio.

An equipment-owned contribution must be gated independently, so suppression
of equipment cannot suppress unrelated state contributions. With no effective
target bonus, preserve the caller's original contribution and its policy.
"""
    def __init__(self, policy: StateEffectivenessPolicy,
                 base_provider: RecoveryModifierProvider | None = None,
                 equipment_policy: EquipmentEffectivenessPolicy | None = None) -> None:
        if base_provider is not None and not callable(base_provider):
            raise TypeError("base_provider must be callable or None")
        self._policy = policy
        self._base = base_provider
        self._equipment = equipment_policy

    def __call__(self, context: BattleContext, request: RecoveryRequest) -> ExactRatio | RecoveryModifierContribution:
        base = ExactRatio(1) if self._base is None else self._base(context, request)
        states = self._policy.effective_instances(context, request.target_id, RECEIVED_RECOVERY_BONUS_STATE_ID)
        if not states:
            return base
        ratio = base.ratio if isinstance(base, RecoveryModifierContribution) else base
        if not isinstance(ratio, ExactRatio):
            raise TypeError("recovery modifier provider must return ExactRatio or RecoveryModifierContribution")
        if ratio.numerator < 0:
            raise ValueError("recovery modifier ratio must be nonnegative")
        if isinstance(base, RecoveryModifierContribution) and base.equipment_contribution_ref is not None:
            if self._equipment is None:
                raise RuntimeError("equipment-owned recovery modifier has no effectiveness policy")
            decision = self._equipment.evaluate_contribution(context, base.equipment_contribution_ref)
            if decision.status is EquipmentEffectivenessStatus.UNSUPPORTED_BOUNDARY:
                raise EquipmentEffectivenessBoundaryError("unsupported equipment recovery-modifier boundary")
            if not decision.effective:
                ratio = ExactRatio(1)
        for state in states:
            params = state.runtime_params
            if not isinstance(params, ReceivedRecoveryBonusParams):
                raise TypeError("received recovery bonus requires ReceivedRecoveryBonusParams")
            rate = params.rate
            ratio = ExactRatio(ratio.numerator * rate.denominator + rate.numerator * ratio.denominator,
                               ratio.denominator * rate.denominator)
        return ratio
