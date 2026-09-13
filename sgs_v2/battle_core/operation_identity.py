from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


def _forbid_ordering(cls_name: str, op: str) -> None:
    raise TypeError(
        f"{cls_name} does not support comparison operator '{op}'. "
        "Operation and permit IDs cannot be used as gameplay ordering or priority comparators."
    )


@dataclass(frozen=True, slots=True, order=False)
class ActionId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("ActionId value must be a str")
        if not self.value.strip():
            raise ValueError("ActionId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("ActionId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("ActionId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("ActionId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("ActionId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class NormalAttackInstanceId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("NormalAttackInstanceId value must be a str")
        if not self.value.strip():
            raise ValueError("NormalAttackInstanceId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("NormalAttackInstanceId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("NormalAttackInstanceId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("NormalAttackInstanceId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("NormalAttackInstanceId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class TargetResolutionId:
    """TRACE_ONLY SUPPORTING ID: diagnostic/trace correlation only, not gameplay semantic identity."""
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("TargetResolutionId value must be a str")
        if not self.value.strip():
            raise ValueError("TargetResolutionId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("TargetResolutionId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("TargetResolutionId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("TargetResolutionId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("TargetResolutionId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DamageInstanceId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("DamageInstanceId value must be a str")
        if not self.value.strip():
            raise ValueError("DamageInstanceId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DamageInstanceId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class PartitionTransactionId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("PartitionTransactionId value must be a str")
        if not self.value.strip():
            raise ValueError("PartitionTransactionId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("PartitionTransactionId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("PartitionTransactionId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("PartitionTransactionId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("PartitionTransactionId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class ReactionBatchId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("ReactionBatchId value must be a str")
        if not self.value.strip():
            raise ValueError("ReactionBatchId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("ReactionBatchId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("ReactionBatchId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("ReactionBatchId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("ReactionBatchId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class CounterBatchEntryId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("CounterBatchEntryId value must be a str")
        if not self.value.strip():
            raise ValueError("CounterBatchEntryId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("CounterBatchEntryId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("CounterBatchEntryId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("CounterBatchEntryId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("CounterBatchEntryId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class CleaveEffectId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("CleaveEffectId value must be a str")
        if not self.value.strip():
            raise ValueError("CleaveEffectId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("CleaveEffectId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("CleaveEffectId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("CleaveEffectId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("CleaveEffectId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class ChainTraversalId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("ChainTraversalId value must be a str")
        if not self.value.strip():
            raise ValueError("ChainTraversalId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("ChainTraversalId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("ChainTraversalId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("ChainTraversalId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("ChainTraversalId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class DirectTroopLossId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("DirectTroopLossId value must be a str")
        if not self.value.strip():
            raise ValueError("DirectTroopLossId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("DirectTroopLossId", ">=")


@dataclass(frozen=True, slots=True, order=False)
class FinalizationId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("FinalizationId value must be a str")
        if not self.value.strip():
            raise ValueError("FinalizationId value cannot be empty or whitespace")

    def __str__(self) -> str:
        return self.value

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationId", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationId", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationId", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("FinalizationId", ">=")


class SourceType(str, Enum):
    NORMAL_ATTACK = "NORMAL_ATTACK"
    ACTIVE_SKILL = "ACTIVE_SKILL"
    ASSAULT = "ASSAULT"
    PERIODIC_DAMAGE = "PERIODIC_DAMAGE"
    CLEAVE = "CLEAVE"
    COUNTER = "COUNTER"
    CHAIN_TRUE_FEEDBACK = "CHAIN_TRUE_FEEDBACK"
    SHARE_DIRECT_LOSS = "SHARE_DIRECT_LOSS"
    DISTRIBUTION_DIRECT_LOSS = "DISTRIBUTION_DIRECT_LOSS"


@dataclass(frozen=True, slots=True, order=False)
class OperationLineage:
    root_action_id: ActionId | None
    parent_normal_attack_id: NormalAttackInstanceId | None
    parent_damage_instance_id: DamageInstanceId | None
    source_type: SourceType
    physical_attacker: str | None = None
    physical_skill: str | None = None
    credit_owner: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, SourceType):
            raise TypeError(f"source_type must be an instance of SourceType, got {type(self.source_type)}")
        if self.root_action_id is not None and not isinstance(self.root_action_id, ActionId):
            raise TypeError(f"root_action_id must be ActionId or None, got {type(self.root_action_id)}")
        if self.parent_normal_attack_id is not None and not isinstance(self.parent_normal_attack_id, NormalAttackInstanceId):
            raise TypeError(f"parent_normal_attack_id must be NormalAttackInstanceId or None, got {type(self.parent_normal_attack_id)}")
        if self.parent_damage_instance_id is not None and not isinstance(self.parent_damage_instance_id, DamageInstanceId):
            raise TypeError(f"parent_damage_instance_id must be DamageInstanceId or None, got {type(self.parent_damage_instance_id)}")
        if self.physical_attacker is not None:
            if not isinstance(self.physical_attacker, str) or not self.physical_attacker.strip():
                raise ValueError("physical_attacker cannot be empty or whitespace when provided")
        if self.physical_skill is not None:
            if not isinstance(self.physical_skill, str) or not self.physical_skill.strip():
                raise ValueError("physical_skill cannot be empty or whitespace when provided")
        if self.credit_owner is not None:
            if not isinstance(self.credit_owner, str) or not self.credit_owner.strip():
                raise ValueError("credit_owner cannot be empty or whitespace when provided")

    def __lt__(self, other: Any) -> bool:
        _forbid_ordering("OperationLineage", "<")

    def __le__(self, other: Any) -> bool:
        _forbid_ordering("OperationLineage", "<=")

    def __gt__(self, other: Any) -> bool:
        _forbid_ordering("OperationLineage", ">")

    def __ge__(self, other: Any) -> bool:
        _forbid_ordering("OperationLineage", ">=")


class OperationIdAllocator:
    """Per-battle deterministic monotonic sequence generator for Stage9 typed identities."""

    __slots__ = (
        "_action_seq",
        "_normal_attack_seq",
        "_target_resolution_seq",
        "_damage_instance_seq",
        "_partition_tx_seq",
        "_reaction_batch_seq",
        "_counter_entry_seq",
        "_cleave_effect_seq",
        "_chain_traversal_seq",
        "_direct_troop_loss_seq",
        "_finalization_seq",
        "_permit_seq",
    )

    def __init__(self) -> None:
        self._action_seq = 0
        self._normal_attack_seq = 0
        self._target_resolution_seq = 0
        self._damage_instance_seq = 0
        self._partition_tx_seq = 0
        self._reaction_batch_seq = 0
        self._counter_entry_seq = 0
        self._cleave_effect_seq = 0
        self._chain_traversal_seq = 0
        self._direct_troop_loss_seq = 0
        self._finalization_seq = 0
        self._permit_seq = 0

    def allocate_action_id(self) -> ActionId:
        self._action_seq += 1
        return ActionId(f"act_{self._action_seq}")

    def allocate_normal_attack_id(self) -> NormalAttackInstanceId:
        self._normal_attack_seq += 1
        return NormalAttackInstanceId(f"na_{self._normal_attack_seq}")

    def allocate_target_resolution_id(self) -> TargetResolutionId:
        self._target_resolution_seq += 1
        return TargetResolutionId(f"tr_{self._target_resolution_seq}")

    def allocate_damage_instance_id(self) -> DamageInstanceId:
        self._damage_instance_seq += 1
        return DamageInstanceId(f"dmg_{self._damage_instance_seq}")

    def allocate_partition_transaction_id(self) -> PartitionTransactionId:
        self._partition_tx_seq += 1
        return PartitionTransactionId(f"ptx_{self._partition_tx_seq}")

    def allocate_reaction_batch_id(self) -> ReactionBatchId:
        self._reaction_batch_seq += 1
        return ReactionBatchId(f"rxn_{self._reaction_batch_seq}")

    def allocate_counter_batch_entry_id(self) -> CounterBatchEntryId:
        self._counter_entry_seq += 1
        return CounterBatchEntryId(f"cbe_{self._counter_entry_seq}")

    def allocate_cleave_effect_id(self) -> CleaveEffectId:
        self._cleave_effect_seq += 1
        return CleaveEffectId(f"clv_{self._cleave_effect_seq}")

    def allocate_chain_traversal_id(self) -> ChainTraversalId:
        self._chain_traversal_seq += 1
        return ChainTraversalId(f"chn_{self._chain_traversal_seq}")

    def allocate_direct_troop_loss_id(self) -> DirectTroopLossId:
        self._direct_troop_loss_seq += 1
        return DirectTroopLossId(f"dtl_{self._direct_troop_loss_seq}")

    def allocate_finalization_id(self) -> FinalizationId:
        self._finalization_seq += 1
        return FinalizationId(f"fin_{self._finalization_seq}")

    def allocate_permit_id(self, prefix: str = "prm") -> str:
        self._permit_seq += 1
        return f"{prefix}_{self._permit_seq}"
