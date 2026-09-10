from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, TYPE_CHECKING

from .damage_modifiers import DamageModifierContribution
from .damage_rule_models import (
    DamageFormulaPolicyContribution,
    DamagePreventionContribution,
    DamageRuleFamily,
    HitRuleContribution,
    RuleContributionSource,
)
from .state_instance import StateInstance

if TYPE_CHECKING:
    from .context import BattleContext
    from .damage_system import DamageRequest


RuleContribution = (
    DamagePreventionContribution
    | HitRuleContribution
    | DamageFormulaPolicyContribution
    | DamageModifierContribution
)
StateRuleBuilder = Callable[
    [StateInstance, RuleContributionSource, "DamageRequest"],
    RuleContribution | None,
]


@dataclass(frozen=True, slots=True)
class StateRuleAdapter:
    adapter_key: str
    family: DamageRuleFamily
    build: StateRuleBuilder

    def __post_init__(self) -> None:
        if not isinstance(self.adapter_key, str) or not self.adapter_key.strip():
            raise ValueError("adapter_key must be a non-empty str")
        if not callable(self.build):
            raise TypeError("build must be callable")


@dataclass(frozen=True, slots=True)
class StateRuleBinding:
    state_id: str
    adapters: tuple[StateRuleAdapter, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id must be a non-empty str")
        keys = [adapter.adapter_key for adapter in self.adapters]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate adapter_key in binding: {self.state_id}")


@dataclass(frozen=True, slots=True)
class DamageRuleCollection:
    prevention_contributions: tuple[DamagePreventionContribution, ...] = ()
    hit_contributions: tuple[HitRuleContribution, ...] = ()
    formula_policy_contributions: tuple[DamageFormulaPolicyContribution, ...] = ()
    modifier_contributions: tuple[DamageModifierContribution, ...] = ()


class DamageRuleProvider(Protocol):
    provider_key: str

    def collect(
        self,
        context: "BattleContext",
        request: "DamageRequest",
    ) -> DamageRuleCollection:
        ...


class StateDamageRuleProvider:
    """Read-only StateRegistry adapter for one immutable per-request rule snapshot."""

    provider_key = "state_damage_rules"

    def __init__(self, bindings: tuple[StateRuleBinding, ...]) -> None:
        state_ids = [binding.state_id for binding in bindings]
        if len(state_ids) != len(set(state_ids)):
            raise ValueError("duplicate state_id in StateDamageRuleProvider bindings")
        self._bindings = {binding.state_id: binding for binding in bindings}

    @property
    def bindings(self) -> tuple[StateRuleBinding, ...]:
        return tuple(self._bindings[state_id] for state_id in sorted(self._bindings))

    def collect(
        self,
        context: "BattleContext",
        request: "DamageRequest",
    ) -> DamageRuleCollection:
        instances_by_id = {
            instance.instance_id: instance
            for owner_id in {request.source_id, request.target_id}
            for instance in context.states.states_of(owner_id)
        }

        prevention: list[DamagePreventionContribution] = []
        hit: list[HitRuleContribution] = []
        formula_policy: list[DamageFormulaPolicyContribution] = []
        modifiers: list[DamageModifierContribution] = []

        for instance_id in sorted(instances_by_id):
            instance = instances_by_id[instance_id]
            binding = self._bindings.get(instance.state_id)
            if binding is None:
                continue

            for declaration_index, adapter in enumerate(binding.adapters):
                source = RuleContributionSource(
                    owner_id=instance.owner_id,
                    applied_by_unit_id=instance.source_id,
                    source_skill_id=instance.source_skill_id,
                    source_state_id=instance.state_id,
                    source_state_instance_id=instance.instance_id,
                    origin_key=(
                        f"{self.provider_key}:{instance.instance_id}:"
                        f"{declaration_index:04d}:{adapter.adapter_key}"
                    ),
                )
                contribution = adapter.build(instance, source, request)
                if contribution is None:
                    continue
                self._append_typed_contribution(
                    adapter.family,
                    contribution,
                    prevention,
                    hit,
                    formula_policy,
                    modifiers,
                )

        return DamageRuleCollection(
            prevention_contributions=tuple(prevention),
            hit_contributions=tuple(hit),
            formula_policy_contributions=tuple(formula_policy),
            modifier_contributions=tuple(modifiers),
        )

    @staticmethod
    def _append_typed_contribution(
        family: DamageRuleFamily,
        contribution: RuleContribution,
        prevention: list[DamagePreventionContribution],
        hit: list[HitRuleContribution],
        formula_policy: list[DamageFormulaPolicyContribution],
        modifiers: list[DamageModifierContribution],
    ) -> None:
        expected_type: type[object]
        destination: list[object]
        if family is DamageRuleFamily.PREVENTION:
            expected_type = DamagePreventionContribution
            destination = prevention
        elif family is DamageRuleFamily.HIT:
            expected_type = HitRuleContribution
            destination = hit
        elif family is DamageRuleFamily.FORMULA_POLICY:
            expected_type = DamageFormulaPolicyContribution
            destination = formula_policy
        elif family is DamageRuleFamily.MODIFIER:
            expected_type = DamageModifierContribution
            destination = modifiers
        else:
            raise ValueError(f"unsupported DamageRuleFamily: {family}")

        if not isinstance(contribution, expected_type):
            raise TypeError(
                f"adapter family {family.value} produced "
                f"{type(contribution).__name__}, expected {expected_type.__name__}"
            )
        destination.append(contribution)
