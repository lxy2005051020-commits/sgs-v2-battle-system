"""Opt-in transfer policies; ordinary application/removal contracts are unchanged."""
from .state_application import StateConflictPolicy, StateConflictDecision, ApplicationDisposition, StateCandidate, StateApplicationTransaction
from .context import BattleContext
from .state_instance import StateInstance
from .state_generation import StateApplicationGenerationId
from .state_removal import StateRemovalPolicy, RemovalDecision, RemovalDecisionStatus, RemovalOperation
from .state_application_reaction import ReactingStateApplicationCoordinator, ReactingStateLifecycleSystem
from .stage10_state_params import ContinuousDamageStateParams
from .transferred_potency import TransferredFrozenDamageBasis
from dataclasses import replace


class TransferStateLifecycle(ReactingStateLifecycleSystem):
    """Bind captured potency to the identity allocated by Shared Foundation.

    Preparation only: physical commit, allocation, publication and expiry still
    delegate to the canonical lifecycle. Ordinary state transactions are untouched.
    """
    def commit_application_transaction(self, context: BattleContext, transaction: StateApplicationTransaction) -> StateInstance:
        params=transaction.final_runtime_params
        if ((transaction.candidate.application_provenance or '').startswith('TRANSFER:')
                and isinstance(params,ContinuousDamageStateParams)):
            identity=transaction.planned_new_instance_id or transaction.expected_existing_instance_id
            basis=replace(params.frozen_damage_basis,
                application_generation_id=transaction.new_generation_id, physical_state_instance_id=identity)
            params=replace(params,application_generation_id=transaction.new_generation_id,frozen_damage_basis=basis)
            transaction=replace(transaction,final_runtime_params=params)
        return super().commit_application_transaction(context,transaction)

    def is_generation_eligible_at_action_start(self, context: BattleContext, instance: StateInstance,
            generation_id: StateApplicationGenerationId | None = None) -> bool:
        params=instance.runtime_params
        if (instance.lifecycle_window is None and isinstance(params,ContinuousDamageStateParams)
                and isinstance(params.frozen_damage_basis,TransferredFrozenDamageBasis)):
            instance=replace(instance,lifecycle_window=params.lifecycle_window)
        return super().is_generation_eligible_at_action_start(context,instance,generation_id)


class TransferConflictPolicy(StateConflictPolicy):
    def evaluate_conflict(self, context: BattleContext, candidate: StateCandidate,
            resident_matches: tuple[StateInstance, ...]) -> StateConflictDecision:
        provenance = candidate.application_provenance or ""
        if provenance.startswith("TRANSFER:") and context.metadata.get("_state_transfer_in_progress", 0):
            # Stage the new instance first. Only after a successful canonical
            # commit does the transfer remove/trim same-dimension residents.
            return StateConflictDecision(ApplicationDisposition.CREATE, "TRANSFER_USER_APPROVED_REPLACE")
        if provenance.startswith("TRANSFER_REMAINDER:") and context.metadata.get("_state_transfer_in_progress", 0):
            identity = provenance.split(":", 1)[1]
            if any(state.instance_id == identity for state in resident_matches):
                return StateConflictDecision(ApplicationDisposition.REFRESH,
                    "TRANSFER_PRESERVE_UNRELATED_DIMENSIONS", existing_instance_id=identity)
        return super().evaluate_conflict(context, candidate, resident_matches)


class TransferRemovalPolicy(StateRemovalPolicy):
    def evaluate_removal(self, context: BattleContext, operation: RemovalOperation,
            state_instance: StateInstance) -> RemovalDecision:
        if (operation is RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE
                and context.metadata.get("_state_transfer_in_progress", 0)
                and state_instance.instance_id in context.metadata.get("_state_transfer_removal_permits", ())):
            return RemovalDecision(RemovalDecisionStatus.ALLOW, operation, "TRANSFER_USER_APPROVED_SOURCE_REMOVE")
        return super().evaluate_removal(context, operation, state_instance)


class TransferApplicationCoordinator(ReactingStateApplicationCoordinator):
    def react(self, context: BattleContext, parent: StateInstance) -> None:
        # Transferring a captured state carries its existing associated children;
        # it must not manufacture a second application reaction during cloning.
        if context.metadata.get("_state_transfer_in_progress", 0):
            return
        return super().react(context, parent)
