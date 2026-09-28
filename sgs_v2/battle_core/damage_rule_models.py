from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .damage_formula_context import DamageDefensePolicy
from .enums import DamageSourceType, DamageType
from .numeric_validation import validate_probability


def _validate_nonempty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace")


def _validate_enum(value: object, enum_type: type[Enum], field_name: str) -> None:
    if not isinstance(value, enum_type):
        raise TypeError(f"{field_name} must be a {enum_type.__name__}")


def _canonicalize_enum_scope(
    value: object,
    enum_type: type[Enum],
    field_name: str,
) -> frozenset | None:
    if value is None:
        return None
    try:
        canonical = frozenset(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{field_name} must be an iterable of {enum_type.__name__}") from exc
    for item in canonical:
        _validate_enum(item, enum_type, f"{field_name} item")
    return canonical


def _validate_canonical_enum_scope(
    value: object,
    enum_type: type[Enum],
    field_name: str,
    *,
    allow_none: bool,
) -> None:
    if value is None:
        if allow_none:
            return
        raise TypeError(f"{field_name} must be a frozenset of {enum_type.__name__}")
    if type(value) is not frozenset:
        raise TypeError(f"{field_name} must be a frozenset of {enum_type.__name__}")
    for item in value:
        _validate_enum(item, enum_type, f"{field_name} item")


class DamageRuleFamily(str, Enum):
    PREVENTION = "PREVENTION"
    HIT = "HIT"
    FORMULA_POLICY = "FORMULA_POLICY"
    MODIFIER = "MODIFIER"


@dataclass(frozen=True, slots=True)
class RuleContributionSource:
    owner_id: str | None
    applied_by_unit_id: str | None
    source_skill_id: str | None
    source_state_id: str | None
    source_state_instance_id: str | None
    origin_key: str

    def __post_init__(self) -> None:
        for field_name in (
            "owner_id",
            "applied_by_unit_id",
            "source_skill_id",
            "source_state_id",
            "source_state_instance_id",
        ):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be a non-empty str when provided")
        if not isinstance(self.origin_key, str) or not self.origin_key.strip():
            raise ValueError("origin_key must be a non-empty str")
        if (self.source_state_id is None) != (self.source_state_instance_id is None):
            raise ValueError(
                "source_state_id and source_state_instance_id must both be set or both be None"
            )


class DamagePreventionRuleKind(str, Enum):
    SOURCE_CANNOT_DEAL_DAMAGE = "SOURCE_CANNOT_DEAL_DAMAGE"
    GENERIC_PREVENTION = "GENERIC_PREVENTION"


@dataclass(frozen=True, slots=True)
class DamagePreventionContribution:
    kind: DamagePreventionRuleKind
    source: RuleContributionSource
    order_key: str

    def __post_init__(self) -> None:
        self.validate_runtime_contract()

    def validate_runtime_contract(self) -> None:
        _validate_enum(self.kind, DamagePreventionRuleKind, "kind")
        if not isinstance(self.source, RuleContributionSource):
            raise TypeError("source must be a RuleContributionSource")
        _validate_nonempty_string(self.order_key, "order_key")


class HitPreventionCategory(str, Enum):
    IMMUNITY_LIKE = "IMMUNITY_LIKE"
    EVASION_LIKE = "EVASION_LIKE"


class HitRuleKind(str, Enum):
    DETERMINISTIC_PREVENTION = "DETERMINISTIC_PREVENTION"
    PROBABILISTIC_PREVENTION = "PROBABILISTIC_PREVENTION"
    BYPASS = "BYPASS"


@dataclass(frozen=True, slots=True)
class HitRuleContribution:
    kind: HitRuleKind
    source: RuleContributionSource
    order_key: str
    category: HitPreventionCategory | None = None
    probability: float = 1.0
    bypass_categories: frozenset[HitPreventionCategory] = field(default_factory=frozenset)
    damage_types: frozenset[DamageType] | None = None
    source_types: frozenset[DamageSourceType] | None = None

    def __post_init__(self) -> None:
        try:
            bypass_categories = frozenset(self.bypass_categories)
        except TypeError as exc:
            raise TypeError(
                "bypass_categories must be an iterable of HitPreventionCategory"
            ) from exc
        damage_types = _canonicalize_enum_scope(
            self.damage_types,
            DamageType,
            "damage_types",
        )
        source_types = _canonicalize_enum_scope(
            self.source_types,
            DamageSourceType,
            "source_types",
        )
        object.__setattr__(self, "bypass_categories", bypass_categories)
        object.__setattr__(self, "damage_types", damage_types)
        object.__setattr__(self, "source_types", source_types)

        probability = validate_probability(self.probability)
        object.__setattr__(self, "probability", probability)
        self.validate_runtime_contract()

    def validate_runtime_contract(self) -> None:
        _validate_enum(self.kind, HitRuleKind, "kind")
        if not isinstance(self.source, RuleContributionSource):
            raise TypeError("source must be a RuleContributionSource")
        _validate_nonempty_string(self.order_key, "order_key")
        if self.category is not None:
            _validate_enum(self.category, HitPreventionCategory, "category")
        _validate_canonical_enum_scope(
            self.bypass_categories,
            HitPreventionCategory,
            "bypass_categories",
            allow_none=False,
        )
        _validate_canonical_enum_scope(
            self.damage_types,
            DamageType,
            "damage_types",
            allow_none=True,
        )
        _validate_canonical_enum_scope(
            self.source_types,
            DamageSourceType,
            "source_types",
            allow_none=True,
        )
        probability = validate_probability(self.probability)

        if self.kind is HitRuleKind.BYPASS:
            if not self.bypass_categories:
                raise ValueError("BYPASS contribution requires bypass_categories")
            if self.category is not None:
                raise ValueError("BYPASS contribution cannot define category")
        else:
            if self.category is None:
                raise ValueError("prevention contribution requires category")
            if self.bypass_categories:
                raise ValueError("prevention contribution cannot define bypass_categories")

        if self.kind is HitRuleKind.DETERMINISTIC_PREVENTION and probability != 1.0:
            raise ValueError("deterministic prevention probability must be 1")

    def applies_to(self, damage_type: DamageType, source_type: DamageSourceType) -> bool:
        return (
            (self.damage_types is None or damage_type in self.damage_types)
            and (self.source_types is None or source_type in self.source_types)
        )


@dataclass(frozen=True, slots=True)
class DamageFormulaPolicyContribution:
    defense_policy: DamageDefensePolicy
    source: RuleContributionSource
    order_key: str
    damage_types: frozenset[DamageType] | None = None
    source_types: frozenset[DamageSourceType] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "damage_types",
            _canonicalize_enum_scope(self.damage_types, DamageType, "damage_types"),
        )
        object.__setattr__(
            self,
            "source_types",
            _canonicalize_enum_scope(
                self.source_types,
                DamageSourceType,
                "source_types",
            ),
        )
        self.validate_runtime_contract()

    def validate_runtime_contract(self) -> None:
        _validate_enum(self.defense_policy, DamageDefensePolicy, "defense_policy")
        if not isinstance(self.source, RuleContributionSource):
            raise TypeError("source must be a RuleContributionSource")
        _validate_nonempty_string(self.order_key, "order_key")
        _validate_canonical_enum_scope(
            self.damage_types,
            DamageType,
            "damage_types",
            allow_none=True,
        )
        _validate_canonical_enum_scope(
            self.source_types,
            DamageSourceType,
            "source_types",
            allow_none=True,
        )

    def applies_to(self, damage_type: DamageType, source_type: DamageSourceType) -> bool:
        return (
            (self.damage_types is None or damage_type in self.damage_types)
            and (self.source_types is None or source_type in self.source_types)
        )
