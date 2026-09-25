from __future__ import annotations

from dataclasses import dataclass

from .context import BattleContext
from .damage_partition_system import DamageShareTransactionPlan
from .enums import DamageType
from .operation_identity import OperationLineage
from .recovery_system import RecoveryRequest, RecoveryResult, RecoverySystem
from .stage11_state_params import LifeStealStateParams
from .stage11_state_runtime import Stage11StateRuntime


@dataclass(frozen=True, slots=True)
class AttackerRecoveryResolution:
    basis: int
    results: tuple[RecoveryResult, ...]


class Stage11AttackerRecoverySystem:
    """690094/690095 owner: actual troop-loss basis, per-source CEIL."""

    def __init__(
        self,
        recovery_system: RecoverySystem,
        state_runtime: Stage11StateRuntime,
    ) -> None:
        self._recovery = recovery_system
        self._states = state_runtime

    @staticmethod
    def _ceil_ratio(base: int, params: LifeStealStateParams) -> int:
        if base <= 0 or params.ratio.numerator == 0:
            return 0
        num = base * params.ratio.numerator
        den = params.ratio.denominator
        return (num + den - 1) // den

    def resolve_parent_damage(
        self,
        context: BattleContext,
        *,
        lineage: OperationLineage,
        damage_result,
        resolution,
        partition_plan,
        direct_losses: tuple,
    ) -> AttackerRecoveryResolution:
        source_id = lineage.physical_attacker
        if not source_id or source_id == damage_result.target_id:
            return AttackerRecoveryResolution(0, ())
        source = context.units.get(source_id)
        if source is None or not source.is_alive:
            return AttackerRecoveryResolution(0, ())

        basis = int(resolution.actual_target_troop_loss)
        if isinstance(partition_plan, DamageShareTransactionPlan):
            basis += sum(int(item.actual_loss) for item in direct_losses)
        # PROJECT_RUNTIME_DEFAULT: Distribution participant direct-loss is excluded
        # until 690094/690095 research explicitly authorizes that extension.

        results: list[RecoveryResult] = []
        for instance in self._states.lifesteal_instances(
            context, source_id, damage_result.damage_type
        ):
            params = instance.runtime_params
            assert isinstance(params, LifeStealStateParams)
            amount = self._ceil_ratio(basis, params)
            results.append(
                self._recovery.resolve(
                    context,
                    RecoveryRequest(
                        source_id=source_id,
                        target_id=source_id,
                        amount=amount,
                        source_skill_id=instance.source_skill_id,
                        source_state_id=instance.state_id,
                        source_state_instance_id=instance.instance_id,
                        source_generation_id=instance.current_generation_id,
                    ),
                )
            )
        return AttackerRecoveryResolution(basis, tuple(results))

    def resolve_cleave(
        self,
        context: BattleContext,
        recovery_fact,
    ) -> AttackerRecoveryResolution:
        fact = recovery_fact.primary_damage
        source_id = fact.lineage.physical_attacker
        if not source_id or source_id == fact.target_id:
            return AttackerRecoveryResolution(0, ())
        source = context.units.get(source_id)
        if source is None or not source.is_alive:
            return AttackerRecoveryResolution(0, ())

        # Cleave's frozen topology gives us the actual primary secondary-target
        # troop loss. Distribution external losses remain excluded by the same
        # project-runtime-default used for parent standard damage.
        basis = int(fact.actual_target_troop_loss)
        results: list[RecoveryResult] = []
        for instance in self._states.lifesteal_instances(
            context, source_id, fact.damage_type
        ):
            params = instance.runtime_params
            assert isinstance(params, LifeStealStateParams)
            amount = self._ceil_ratio(basis, params)
            results.append(
                self._recovery.resolve(
                    context,
                    RecoveryRequest(
                        source_id=source_id,
                        target_id=source_id,
                        amount=amount,
                        source_skill_id=instance.source_skill_id,
                        source_state_id=instance.state_id,
                        source_state_instance_id=instance.instance_id,
                        source_generation_id=instance.current_generation_id,
                    ),
                )
            )
        return AttackerRecoveryResolution(basis, tuple(results))
