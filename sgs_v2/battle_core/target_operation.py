from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .operation_identity import TargetOperationId
from .provider_identity import SkillProviderRef


class TargetRelation(str, Enum):
    ENEMY = "ENEMY"
    ALLY = "ALLY"
    SELF = "SELF"


class TargetCardinality(str, Enum):
    SINGLE = "SINGLE"
    CHOOSE_N = "CHOOSE_N"
    FIXED_ALL = "FIXED_ALL"


class TargetSelectorKind(str, Enum):
    RANDOM = "RANDOM"
    DETERMINISTIC = "DETERMINISTIC"
    EXPLICIT = "EXPLICIT"


class TargetQueryMode(str, Enum):
    NEW_QUERY = "NEW_QUERY"
    INHERIT_RESOLVED = "INHERIT_RESOLVED"
    DERIVE_FROM_RESOLVED = "DERIVE_FROM_RESOLVED"
    LOCK_RESOLVED = "LOCK_RESOLVED"


class TargetSelectionProvenance(str, Enum):
    FRESH_SELECTED = "FRESH_SELECTED"
    INHERITED = "INHERITED"
    DERIVED = "DERIVED"
    LOCKED = "LOCKED"


class TargetOperationDomain(str, Enum):
    SKILL = "SKILL"


class TargetPurpose(str, Enum):
    HOSTILE = "HOSTILE"
    FRIENDLY_SUPPORT = "FRIENDLY_SUPPORT"
    SELF = "SELF"


@dataclass(frozen=True, slots=True)
class TargetEligibilityContext:
    domain: TargetOperationDomain
    purpose: TargetPurpose
    restriction_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.domain, TargetOperationDomain):
            raise TypeError("domain must be a TargetOperationDomain")
        if not isinstance(self.purpose, TargetPurpose):
            raise TypeError("purpose must be a TargetPurpose")
        keys = tuple(self.restriction_keys)
        if any(not isinstance(item, str) or not item.strip() for item in keys):
            raise ValueError("restriction_keys must contain non-empty strings")
        object.__setattr__(self, "restriction_keys", keys)


@dataclass(frozen=True, slots=True)
class TargetOperation:
    operation_id: TargetOperationId
    actor_id: str
    producer_ref: SkillProviderRef
    admitted_operation_key: str
    relation: TargetRelation
    cardinality: TargetCardinality
    selector_kind: TargetSelectorKind
    eligibility_context: TargetEligibilityContext
    requested_count: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, TargetOperationId):
            raise TypeError("operation_id must be a TargetOperationId")
        if not isinstance(self.actor_id, str) or not self.actor_id.strip():
            raise ValueError("actor_id cannot be empty or whitespace")
        if not isinstance(self.producer_ref, SkillProviderRef):
            raise TypeError("producer_ref must be a SkillProviderRef")
        if self.producer_ref.owner_id != self.actor_id:
            raise ValueError("producer_ref owner must match actor_id")
        if not isinstance(self.admitted_operation_key, str) or not self.admitted_operation_key.strip():
            raise ValueError("admitted_operation_key cannot be empty or whitespace")
        if not isinstance(self.relation, TargetRelation):
            raise TypeError("relation must be a TargetRelation")
        if not isinstance(self.cardinality, TargetCardinality):
            raise TypeError("cardinality must be a TargetCardinality")
        if not isinstance(self.selector_kind, TargetSelectorKind):
            raise TypeError("selector_kind must be a TargetSelectorKind")
        if not isinstance(self.eligibility_context, TargetEligibilityContext):
            raise TypeError("eligibility_context must be a TargetEligibilityContext")

        if self.cardinality is TargetCardinality.CHOOSE_N:
            if isinstance(self.requested_count, bool) or not isinstance(self.requested_count, int):
                raise TypeError("CHOOSE_N requested_count must be an int")
            if self.requested_count <= 0:
                raise ValueError("CHOOSE_N requested_count must be > 0")
        elif self.cardinality is TargetCardinality.SINGLE:
            if self.requested_count not in (None, 1):
                raise ValueError("SINGLE requested_count must be None or 1")
        elif self.requested_count is not None:
            raise ValueError("FIXED_ALL does not carry requested_count")


@dataclass(frozen=True, slots=True)
class TargetSelectionResult:
    operation_id: TargetOperationId
    target_ids: tuple[str, ...]
    provenance: TargetSelectionProvenance

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, TargetOperationId):
            raise TypeError("operation_id must be a TargetOperationId")
        if not isinstance(self.provenance, TargetSelectionProvenance):
            raise TypeError("provenance must be a TargetSelectionProvenance")
        target_ids = tuple(self.target_ids)
        if any(not isinstance(item, str) or not item.strip() for item in target_ids):
            raise ValueError("target_ids must contain non-empty strings")
        if len(set(target_ids)) != len(target_ids):
            raise ValueError("target_ids cannot contain duplicates")
        object.__setattr__(self, "target_ids", target_ids)


class TargetOperationProducer:
    """Creates only explicit NEW_QUERY operations; continuation reuses prior identity."""

    __slots__ = ()

    @staticmethod
    def new_query(
        context: BattleContext,
        *,
        actor_id: str,
        producer_ref: SkillProviderRef,
        admitted_operation_key: str,
        relation: TargetRelation,
        cardinality: TargetCardinality,
        selector_kind: TargetSelectorKind,
        eligibility_context: TargetEligibilityContext,
        requested_count: int | None = None,
        query_mode: TargetQueryMode = TargetQueryMode.NEW_QUERY,
    ) -> TargetOperation:
        if not isinstance(context, BattleContext):
            raise TypeError("context must be a BattleContext")
        if query_mode is not TargetQueryMode.NEW_QUERY:
            raise ValueError("only NEW_QUERY may create a TargetOperation")
        return TargetOperation(
            operation_id=context.id_allocator.allocate_target_operation_id(),
            actor_id=actor_id,
            producer_ref=producer_ref,
            admitted_operation_key=admitted_operation_key,
            relation=relation,
            cardinality=cardinality,
            selector_kind=selector_kind,
            eligibility_context=eligibility_context,
            requested_count=requested_count,
        )

    @staticmethod
    def continue_from(
        previous: TargetSelectionResult,
        query_mode: TargetQueryMode,
        *,
        target_ids: tuple[str, ...] | None = None,
    ) -> TargetSelectionResult:
        if not isinstance(previous, TargetSelectionResult):
            raise TypeError("previous must be a TargetSelectionResult")
        mapping = {
            TargetQueryMode.INHERIT_RESOLVED: TargetSelectionProvenance.INHERITED,
            TargetQueryMode.DERIVE_FROM_RESOLVED: TargetSelectionProvenance.DERIVED,
            TargetQueryMode.LOCK_RESOLVED: TargetSelectionProvenance.LOCKED,
        }
        try:
            provenance = mapping[query_mode]
        except KeyError as exc:
            raise ValueError("NEW_QUERY requires a fresh TargetOperation") from exc
        return TargetSelectionResult(
            operation_id=previous.operation_id,
            target_ids=previous.target_ids if target_ids is None else tuple(target_ids),
            provenance=provenance,
        )
