from __future__ import annotations

from dataclasses import dataclass, field

from .damage_system import DamageRequest
from .enums import DamageSourceType, DamageType
from .state_runtime_params import EmptyStateRuntimeParams, StateRuntimeParams


@dataclass(frozen=True, slots=True)
class DamageEffect:
    source_id: str
    target_id: str
    damage_type: DamageType
    source_type: DamageSourceType
    coefficient: float = 1.0
    source_skill_id: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")

    def to_request(self) -> DamageRequest:
        return DamageRequest(
            source_id=self.source_id,
            target_id=self.target_id,
            damage_type=self.damage_type,
            source_type=self.source_type,
            coefficient=self.coefficient,
            source_skill_id=self.source_skill_id,
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
    """恢复意图合同。

    Stage 5 不执行恢复；未来 RecoverySystem 建立后再接入正式恢复政策。
    """

    source_id: str | None
    target_id: str
    amount: int
    source_skill_id: str | None = None

    def __post_init__(self) -> None:
        if self.source_id == "":
            raise ValueError("source_id cannot be empty when provided")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")
        if self.source_skill_id == "":
            raise ValueError("source_skill_id cannot be empty when provided")


Effect = DamageEffect | ApplyStateEffect | RemoveStateEffect | RecoverEffect
