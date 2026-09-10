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
        if not isinstance(self.family, DamageRuleFamily):
            raise TypeError("family must be a DamageRuleFamily")
        if not callable(self.build):
            raise TypeError("build must be callable")


@dataclass(frozen=True, slots=True)
class StateRuleBinding:
    state_id: str
    adapters: tuple[StateRuleAdapter, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id must be a non-empty str")
        try:
            adapters = tuple(self.adapters)
        except TypeError as exc:
            raise TypeError("adapters must be an iterable of StateRuleAdapter") from exc
        for adapter in adapters:
            if not isinstance(adapter, StateRuleAdapter):
                raise TypeError("adapters must contain only StateRuleAdapter values")
        object.__setattr__(self, "adapters", adapters)
        keys = [adapter.adapter_key for adapter in adapters]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate adapter_key in binding: {self.state_id}")


@dataclass(frozen=True, slots=True)
class DamageRuleCollection:
    prevention_contributions: tuple[DamagePreventionContribution, ...] = ()
    hit_contributions: tuple[HitRuleContribution, ...] = ()
    formula_policy_contributions: tuple[DamageFormulaPolicyContribution, ...] = ()
    modifier_contributions: tuple[DamageModifierContribution, ...] = ()

    def __post_init__(self) -> None:
        prevention = self._canonicalize(
            self.prevention_contributions,
            DamagePreventionContribution,
            "prevention_contributions",
        )
        hit = self._canonicalize(
            self.hit_contributions,
            HitRuleContribution,
            "hit_contributions",
        )
        formula_policy = self._canonicalize(
            self.formula_policy_contributions,
            DamageFormulaPolicyContribution,
            "formula_policy_contributions",
        )
        modifiers = self._canonicalize(
            self.modifier_contributions,
            DamageModifierContribution,
            "modifier_contributions",
        )

        self._reject_duplicate_order_keys(prevention, "PREVENTION")
        self._reject_duplicate_order_keys(hit, "HIT")
        self._reject_duplicate_order_keys(formula_policy, "FORMULA_POLICY")
        modifier_keys = [(item.phase, item.order_key) for item in modifiers]
        if len(modifier_keys) != len(set(modifier_keys)):
            raise ValueError("duplicate order_key in MODIFIER phase")

        object.__setattr__(self, "prevention_contributions", prevention)
        object.__setattr__(self, "hit_contributions", hit)
        object.__setattr__(self, "formula_policy_contributions", formula_policy)
        object.__setattr__(self, "modifier_contributions", modifiers)

    @staticmethod
    def _canonicalize(values: object, expected_type: type, field_name: str) -> tuple:
        try:
            canonical = tuple(values)  # type: ignore[arg-type]
        except TypeError as exc:
            raise TypeError(
                f"{field_name} must be an iterable of {expected_type.__name__}"
            ) from exc
        for value in canonical:
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"{field_name} must contain only {expected_type.__name__} values"
                )
        return canonical

    @staticmethod
    def _reject_duplicate_order_keys(values: tuple, family_name: str) -> None:
        keys = [item.order_key for item in values]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate order_key in {family_name} contributions")


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
        try:
            canonical_bindings = tuple(bindings)
        except TypeError as exc:
            raise TypeError("bindings must be an iterable of StateRuleBinding") from exc
        for binding in canonical_bindings:
            if not isinstance(binding, StateRuleBinding):
                raise TypeError("bindings must contain only StateRuleBinding values")
        state_ids = [binding.state_id for binding in canonical_bindings]
        if len(state_ids) != len(set(state_ids)):
            raise ValueError("duplicate state_id in StateDamageRuleProvider bindings")
        self._bindings = {
            binding.state_id: binding
            for binding in canonical_bindings
        }

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
            prevention_contributions=prevention,
            hit_contributions=hit,
            formula_policy_contributions=formula_policy,
            modifier_contributions=modifiers,
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
        if not isinstance(family, DamageRuleFamily):
            raise TypeError("family must be a DamageRuleFamily")
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
