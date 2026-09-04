from __future__ import annotations

from dataclasses import dataclass, field

from .damage_system import DamageRequest
from .enums import DamageSourceType, DamageType
from .recovery_system import RecoveryRequest
from .state_runtime_params import EmptyStateRuntimeParams, StateRuntimeParams


def _validate_optional_id(value: str | None, field_name: str) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str when provided")
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace when provided")


def _validate_state_provenance_pair(
    source_state_id: str | None,
    source_state_instance_id: str | None,
) -> None:
    if (source_state_id is None) != (source_state_instance_id is None):
        raise ValueError(
            "source_state_id and source_state_instance_id must both be set or both be None"
        )


@dataclass(frozen=True, slots=True)
class DamageEffect:
    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float = 1.0
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )

    def to_request(self) -> DamageRequest:
        return DamageRequest(
            source_id=self.source_id,
            target_id=self.target_id,
            damage_type=self.damage_type,
            source_type=self.source_type,
            coefficient=self.coefficient,
            source_skill_id=self.source_skill_id,
            source_state_id=self.source_state_id,
            source_state_instance_id=self.source_state_instance_id,
        )


@dataclass(frozen=True, slots=True)
class ApplyStateEffect:
    state_id: str
    owner_id: str
    source_id: str | None = None
    source_skill_id: str | None = None
    expires_round: int | None = None
    expires_phase: str | None = None
    runtime_params: StateRuntimeParams = field(
        default_factory=EmptyStateRuntimeParams
    )

    def __post_init__(self) -> None:
        if not self.state_id:
            raise ValueError("state_id cannot be empty")
        if not self.owner_id:
            raise ValueError("owner_id cannot be empty")
        if self.source_id == "":
            raise ValueError("source_id cannot be empty when provided")
        if self.source_skill_id == "":
            raise ValueError("source_skill_id cannot be empty when provided")


@dataclass(frozen=True, slots=True)
class RemoveStateEffect:
    instance_id: str

    def __post_init__(self) -> None:
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoverEffect:
    """Stage 7 正式恢复意图合同；Effect 本身保持纯数据、无副作用。"""

    source_id: str | None
    target_id: str
    amount: int
    source_skill_id: str | None = None
    source_state_id: str | None = None
    source_state_instance_id: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_id(self.source_id, "source_id")
        if not isinstance(self.target_id, str):
            raise TypeError("target_id must be a str")
        if not self.target_id.strip():
            raise ValueError("target_id cannot be empty or whitespace")
        _validate_optional_id(self.source_skill_id, "source_skill_id")
        _validate_optional_id(self.source_state_id, "source_state_id")
        _validate_optional_id(
            self.source_state_instance_id,
            "source_state_instance_id",
        )
        _validate_state_provenance_pair(
            self.source_state_id,
            self.source_state_instance_id,
        )
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("amount must be an int")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")

    def to_request(self) -> RecoveryRequest:
        return RecoveryRequest(
            source_id=self.source_id,
            target_id=self.target_id,
            amount=self.amount,
            source_skill_id=self.source_skill_id,
            source_state_id=self.source_state_id,
            source_state_instance_id=self.source_state_instance_id,
        )


Effect = DamageEffect | ApplyStateEffect | RemoveStateEffect | RecoverEffect
