from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeAlias

from .dependency_evaluation import (
    DependencyEvaluationSupport,
    DependencyNode,
    ProviderNode,
    StateNode,
)
from .provider_validity import ProviderValidityDecision, ProviderValidityPolicy
from .state_effectiveness import StateEffectivenessDecision, StateEffectivenessPolicy


@dataclass(frozen=True, slots=True)
class StateEffectivenessChanged:
    state_instance_id: str
    before: StateEffectivenessDecision
    after: StateEffectivenessDecision


@dataclass(frozen=True, slots=True)
class ProviderValidityChanged:
    provider_node: ProviderNode
    before: ProviderValidityDecision
    after: ProviderValidityDecision


EffectivenessTransition: TypeAlias = (
    StateEffectivenessChanged | ProviderValidityChanged
)
StateTransitionPort: TypeAlias = Callable[[object, StateEffectivenessChanged], None]
ProviderTransitionPort: TypeAlias = Callable[[object, ProviderValidityChanged], None]


@dataclass(frozen=True, slots=True)
class EffectivenessTransitionSnapshot:
    decisions: tuple[tuple[DependencyNode, object], ...]


class EffectivenessTransitionCoordinator:
    """Compares canonical decisions across one already-authorized mutation wave.

    It owns neither storage nor lifecycle mutation. Public queries do not call
    this coordinator; only committed mutation envelopes do.
    """

    __slots__ = (
        "_dependencies",
        "_state_policy",
        "_provider_policy",
        "_state_ports",
        "_state_public_fact_ports",
        "_provider_ports",
    )

    def __init__(
        self,
        *,
        dependencies: DependencyEvaluationSupport,
        state_policy: StateEffectivenessPolicy,
        provider_policy: ProviderValidityPolicy,
    ) -> None:
        if not isinstance(dependencies, DependencyEvaluationSupport):
            raise TypeError("dependencies must be DependencyEvaluationSupport")
        if not isinstance(state_policy, StateEffectivenessPolicy):
            raise TypeError("state_policy must be StateEffectivenessPolicy")
        if not isinstance(provider_policy, ProviderValidityPolicy):
            raise TypeError("provider_policy must be ProviderValidityPolicy")
        self._dependencies = dependencies
        self._state_policy = state_policy
        self._provider_policy = provider_policy
        self._state_ports: list[StateTransitionPort] = []
        self._state_public_fact_ports: list[StateTransitionPort] = []
        self._provider_ports: list[ProviderTransitionPort] = []

    @property
    def dependency_support(self) -> DependencyEvaluationSupport:
        return self._dependencies

    def register_state_transition_port(self, port: StateTransitionPort) -> None:
        if not callable(port):
            raise TypeError("port must be callable")
        if port not in self._state_ports:
            self._state_ports.append(port)

    def register_state_public_fact_port(self, port: StateTransitionPort) -> None:
        """Register post-internal-transition public fact publication."""
        if not callable(port):
            raise TypeError("port must be callable")
        if port not in self._state_public_fact_ports:
            self._state_public_fact_ports.append(port)

    def register_provider_transition_port(self, port: ProviderTransitionPort) -> None:
        if not callable(port):
            raise TypeError("port must be callable")
        if port not in self._provider_ports:
            self._provider_ports.append(port)

    def _evaluate_if_present(self, context, node: DependencyNode):
        if isinstance(node, StateNode):
            if not context.states.has_instance(node.instance_id):
                return None
            return self._state_policy.evaluate_state(
                context, context.states.get(node.instance_id)
            )
        if isinstance(node, ProviderNode):
            return self._provider_policy.evaluate_provider(
                context, node.provider_ref
            )
        raise TypeError(f"unsupported dependency node: {type(node)}")

    def capture(
        self,
        context,
        roots,
    ) -> EffectivenessTransitionSnapshot:
        closure = self._dependencies.affected_closure_many(tuple(roots))
        decisions: list[tuple[DependencyNode, object]] = []
        for node in closure:
            decision = self._evaluate_if_present(context, node)
            if decision is not None:
                decisions.append((node, decision))
        return EffectivenessTransitionSnapshot(tuple(decisions))

    def settle(
        self,
        context,
        before: EffectivenessTransitionSnapshot,
        roots,
    ) -> tuple[EffectivenessTransition, ...]:
        if not isinstance(before, EffectivenessTransitionSnapshot):
            raise TypeError("before must be EffectivenessTransitionSnapshot")

        previous = dict(before.decisions)
        closure = self._dependencies.affected_closure_many(tuple(roots))
        transitions: list[EffectivenessTransition] = []

        for node in closure:
            old = previous.get(node)
            if old is None:
                continue
            new = self._evaluate_if_present(context, node)
            if new is None:
                continue

            if isinstance(node, StateNode):
                if not isinstance(old, StateEffectivenessDecision) or not isinstance(
                    new, StateEffectivenessDecision
                ):
                    raise TypeError("state transition snapshot has invalid decision")
                if old.status is new.status:
                    continue
                transition = StateEffectivenessChanged(
                    state_instance_id=node.instance_id,
                    before=old,
                    after=new,
                )
                transitions.append(transition)
                for port in tuple(self._state_ports):
                    port(context, transition)
                for port in tuple(self._state_public_fact_ports):
                    port(context, transition)
                continue

            if isinstance(node, ProviderNode):
                if not isinstance(old, ProviderValidityDecision) or not isinstance(
                    new, ProviderValidityDecision
                ):
                    raise TypeError("provider transition snapshot has invalid decision")
                if old.status is new.status:
                    continue
                transition = ProviderValidityChanged(
                    provider_node=node,
                    before=old,
                    after=new,
                )
                transitions.append(transition)
                for port in tuple(self._provider_ports):
                    port(context, transition)
                continue

            raise TypeError(f"unsupported dependency node: {type(node)}")

        return tuple(transitions)

    def complete_removed_nodes(
        self,
        context,
        before: EffectivenessTransitionSnapshot,
        removed_nodes,
        *,
        additional_roots=(),
    ) -> tuple[EffectivenessTransition, ...]:
        removed = tuple(removed_nodes)
        roots = tuple(additional_roots)
        affected_before_cleanup = self._dependencies.affected_closure_many(
            (*removed, *roots)
        )
        for node in removed:
            self._dependencies.remove_node(node)
        return self.settle(
            context,
            before,
            (*affected_before_cleanup, *roots),
        )
