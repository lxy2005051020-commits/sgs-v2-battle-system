from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeAlias

from .provider_identity import EquipmentProviderRef, ProviderRef, SkillProviderRef


@dataclass(frozen=True, slots=True)
class StateNode:
    instance_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.instance_id, str) or not self.instance_id.strip():
            raise ValueError("instance_id cannot be empty or whitespace")


@dataclass(frozen=True, slots=True)
class ProviderNode:
    provider_ref: ProviderRef

    def __post_init__(self) -> None:
        if not isinstance(self.provider_ref, (SkillProviderRef, EquipmentProviderRef)):
            raise TypeError("provider_ref must be a typed ProviderRef")


DependencyNode: TypeAlias = StateNode | ProviderNode
NodeEvaluator = Callable[[Any, DependencyNode, "_EvaluationSession"], Any]


class DependencyCycleError(RuntimeError):
    def __init__(self, cycle_path: tuple[DependencyNode, ...]) -> None:
        self.cycle_path = tuple(cycle_path)
        rendered = " -> ".join(repr(node) for node in self.cycle_path)
        super().__init__(f"dependency cycle detected: {rendered}")


class DependencyEvaluationSupport:
    """Battle-scoped dependency topology, memoization and cycle infrastructure."""

    __slots__ = (
        "_prerequisites",
        "_dependents",
        "_state_evaluator",
        "_provider_evaluator",
        "_evaluators_bound",
    )

    def __init__(self) -> None:
        self._prerequisites: dict[DependencyNode, set[DependencyNode]] = {}
        self._dependents: dict[DependencyNode, set[DependencyNode]] = {}
        self._state_evaluator: NodeEvaluator | None = None
        self._provider_evaluator: NodeEvaluator | None = None
        self._evaluators_bound = False

    @staticmethod
    def _sort_nodes(nodes) -> tuple[DependencyNode, ...]:
        return tuple(sorted(nodes, key=repr))

    def prerequisites(self, node: DependencyNode) -> tuple[DependencyNode, ...]:
        return self._sort_nodes(self._prerequisites.get(node, ()))

    def dependents(self, node: DependencyNode) -> tuple[DependencyNode, ...]:
        return self._sort_nodes(self._dependents.get(node, ()))

    @staticmethod
    def _find_path_in(
        graph: dict[DependencyNode, set[DependencyNode]],
        start: DependencyNode,
        target: DependencyNode,
    ) -> tuple[DependencyNode, ...] | None:
        visiting: set[DependencyNode] = set()

        def walk(node: DependencyNode) -> tuple[DependencyNode, ...] | None:
            if node == target:
                return (node,)
            if node in visiting:
                return None
            visiting.add(node)
            try:
                for prerequisite in sorted(graph.get(node, ()), key=repr):
                    suffix = walk(prerequisite)
                    if suffix is not None:
                        return (node, *suffix)
            finally:
                visiting.remove(node)
            return None

        return walk(start)

    def add_dependency(
        self,
        consumer: DependencyNode,
        prerequisite: DependencyNode,
    ) -> bool:
        existing = self._prerequisites.get(consumer, set())
        if prerequisite in existing:
            return False

        path = self._find_path_in(self._prerequisites, prerequisite, consumer)
        if path is not None:
            raise DependencyCycleError((consumer, *path))

        self._prerequisites.setdefault(consumer, set()).add(prerequisite)
        self._dependents.setdefault(prerequisite, set()).add(consumer)
        return True

    def replace_dependencies(
        self,
        consumer: DependencyNode,
        prerequisites,
    ) -> None:
        proposed_prerequisites = {
            node: set(values) for node, values in self._prerequisites.items()
        }
        proposed_dependents = {
            node: set(values) for node, values in self._dependents.items()
        }

        for old in proposed_prerequisites.get(consumer, set()):
            dependents = proposed_dependents.get(old)
            if dependents is not None:
                dependents.discard(consumer)
                if not dependents:
                    proposed_dependents.pop(old, None)

        new_values = set(prerequisites)
        if new_values:
            proposed_prerequisites[consumer] = new_values
        else:
            proposed_prerequisites.pop(consumer, None)

        for prerequisite in new_values:
            proposed_dependents.setdefault(prerequisite, set()).add(consumer)

        self._validate_graph(proposed_prerequisites)
        self._prerequisites = proposed_prerequisites
        self._dependents = proposed_dependents

    @staticmethod
    def _validate_graph(graph: dict[DependencyNode, set[DependencyNode]]) -> None:
        done: set[DependencyNode] = set()
        stack: list[DependencyNode] = []
        visiting: set[DependencyNode] = set()

        def visit(node: DependencyNode) -> None:
            if node in done:
                return
            if node in visiting:
                start = stack.index(node)
                raise DependencyCycleError(tuple(stack[start:] + [node]))
            visiting.add(node)
            stack.append(node)
            try:
                for prerequisite in sorted(graph.get(node, ()), key=repr):
                    visit(prerequisite)
            finally:
                stack.pop()
                visiting.remove(node)
            done.add(node)

        all_nodes = set(graph)
        for values in graph.values():
            all_nodes.update(values)
        for node in sorted(all_nodes, key=repr):
            visit(node)

    def validate_acyclic(self) -> None:
        self._validate_graph(self._prerequisites)

    def _prepare_dependency_replacements(
        self,
        replacements,
        *,
        remove_nodes=(),
    ) -> tuple[
        dict[DependencyNode, set[DependencyNode]],
        dict[DependencyNode, set[DependencyNode]],
    ]:
        """Build and validate one atomic prospective dependency topology."""
        proposed = {
            node: set(values) for node, values in self._prerequisites.items()
        }
        removed = set(remove_nodes)
        for node in removed:
            proposed.pop(node, None)
        for node, values in tuple(proposed.items()):
            new_values = set(values) - removed
            if new_values:
                proposed[node] = new_values
            else:
                proposed.pop(node, None)

        normalized = tuple(
            (consumer, set(prerequisites))
            for consumer, prerequisites in replacements
        )
        seen_consumers: set[DependencyNode] = set()
        for consumer, prerequisites in normalized:
            if consumer in seen_consumers:
                raise ValueError(
                    "dependency replacement consumers must be unique in one atomic update"
                )
            seen_consumers.add(consumer)
            proposed.pop(consumer, None)
            if prerequisites:
                proposed[consumer] = set(prerequisites)

        self._validate_graph(proposed)

        proposed_dependents: dict[DependencyNode, set[DependencyNode]] = {}
        for consumer, prerequisites in proposed.items():
            for prerequisite in prerequisites:
                proposed_dependents.setdefault(prerequisite, set()).add(consumer)
        return proposed, proposed_dependents

    def validate_dependency_replacements(
        self,
        replacements,
        *,
        remove_nodes=(),
    ) -> None:
        """Validate multiple dependency replacements as one pre-commit graph delta."""
        self._prepare_dependency_replacements(
            replacements,
            remove_nodes=remove_nodes,
        )

    def replace_dependencies_many(
        self,
        replacements,
        *,
        remove_nodes=(),
    ) -> None:
        """Commit a previously-validatable dependency topology update atomically."""
        proposed, proposed_dependents = self._prepare_dependency_replacements(
            replacements,
            remove_nodes=remove_nodes,
        )
        self._prerequisites = proposed
        self._dependents = proposed_dependents

    def validate_dependency_replacement(
        self,
        consumer: DependencyNode,
        prerequisites,
        *,
        remove_nodes=(),
    ) -> None:
        """Validate a prospective topology change without mutating the live graph."""
        self.validate_dependency_replacements(
            ((consumer, tuple(prerequisites)),),
            remove_nodes=remove_nodes,
        )

    def remove_node(self, node: DependencyNode) -> None:
        """Remove one physical dependency node and every edge touching it."""
        prerequisites = self._prerequisites.pop(node, set())
        for prerequisite in prerequisites:
            dependents = self._dependents.get(prerequisite)
            if dependents is not None:
                dependents.discard(node)
                if not dependents:
                    self._dependents.pop(prerequisite, None)

        dependents = self._dependents.pop(node, set())
        for dependent in dependents:
            values = self._prerequisites.get(dependent)
            if values is not None:
                values.discard(node)
                if not values:
                    self._prerequisites.pop(dependent, None)

    def affected_closure_many(
        self,
        prerequisites,
    ) -> tuple[DependencyNode, ...]:
        seen: set[DependencyNode] = set()
        queue: list[DependencyNode] = []
        for prerequisite in sorted(set(prerequisites), key=repr):
            if prerequisite not in seen:
                seen.add(prerequisite)
                queue.append(prerequisite)
        while queue:
            node = queue.pop(0)
            for dependent in self.dependents(node):
                if dependent in seen:
                    continue
                seen.add(dependent)
                queue.append(dependent)
        return self._sort_nodes(seen)

    def affected_closure(self, prerequisite: DependencyNode) -> tuple[DependencyNode, ...]:
        seen: set[DependencyNode] = {prerequisite}
        queue: list[DependencyNode] = [prerequisite]
        while queue:
            node = queue.pop(0)
            for dependent in self.dependents(node):
                if dependent in seen:
                    continue
                seen.add(dependent)
                queue.append(dependent)
        return self._sort_nodes(seen)

    def bind_evaluators(
        self,
        *,
        state_evaluator: NodeEvaluator,
        provider_evaluator: NodeEvaluator,
    ) -> None:
        if self._evaluators_bound:
            raise RuntimeError("DependencyEvaluationSupport evaluators are already bound")
        if not callable(state_evaluator) or not callable(provider_evaluator):
            raise TypeError("evaluators must be callable")
        self._state_evaluator = state_evaluator
        self._provider_evaluator = provider_evaluator
        self._evaluators_bound = True

    def evaluate(self, context: Any, node: DependencyNode) -> Any:
        if not self._evaluators_bound:
            raise RuntimeError("DependencyEvaluationSupport evaluators are not bound")
        return _EvaluationSession(self, context).evaluate(node)


class _EvaluationSession:
    __slots__ = ("_support", "_context", "_memo", "_visiting")

    def __init__(self, support: DependencyEvaluationSupport, context: Any) -> None:
        self._support = support
        self._context = context
        self._memo: dict[DependencyNode, Any] = {}
        self._visiting: list[DependencyNode] = []

    def evaluate(self, node: DependencyNode) -> Any:
        if node in self._memo:
            return self._memo[node]
        if node in self._visiting:
            start = self._visiting.index(node)
            raise DependencyCycleError(tuple(self._visiting[start:] + [node]))

        self._visiting.append(node)
        try:
            if isinstance(node, StateNode):
                evaluator = self._support._state_evaluator
            elif isinstance(node, ProviderNode):
                evaluator = self._support._provider_evaluator
            else:
                raise TypeError(f"unsupported dependency node: {type(node)}")
            if evaluator is None:
                raise RuntimeError("required dependency evaluator is not bound")
            result = evaluator(self._context, node, self)
            self._memo[node] = result
            return result
        finally:
            self._visiting.pop()

    def prerequisite_decisions(
        self,
        node: DependencyNode,
    ) -> tuple[tuple[DependencyNode, Any], ...]:
        return tuple(
            (prerequisite, self.evaluate(prerequisite))
            for prerequisite in self._support.prerequisites(node)
        )
