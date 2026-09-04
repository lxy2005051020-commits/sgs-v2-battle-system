from __future__ import annotations

from dataclasses import dataclass

from .enums import BattlePhase


AUTO_EXPIRY_PHASES = frozenset(
    {
        BattlePhase.ROUND_START.value,
        BattlePhase.ROUND_END.value,
    }
)


@dataclass(frozen=True, slots=True)
class StateInstance:
    """一场具体战斗中真实存在的一次状态实例。"""

    instance_id: str
    state_id: str

    owner_id: str
    source_id: str | None
    source_skill_id: str | None

    applied_round: int
    applied_phase: str

    expires_round: int | None = None
    expires_phase: str | None = None

    def __post_init__(self) -> None:
        if not self.instance_id:
            raise ValueError("instance_id cannot be empty")
        if not self.state_id:
            raise ValueError("state_id cannot be empty")
        if not self.owner_id:
            raise ValueError("owner_id cannot be empty")
        if self.applied_round < 0:
            raise ValueError("applied_round must be >= 0")
        if not self.applied_phase:
            raise ValueError("applied_phase cannot be empty")

        self.validate_expiry(
            applied_round=self.applied_round,
            expires_round=self.expires_round,
            expires_phase=self.expires_phase,
        )

    @staticmethod
    def validate_expiry(
        *,
        applied_round: int,
        expires_round: int | None,
        expires_phase: str | None,
    ) -> None:
        if (expires_round is None) != (expires_phase is None):
            raise ValueError(
                "expires_round and expires_phase must either both be set or both be None"
            )
        if expires_round is None:
            return
        if expires_round < applied_round:
            raise ValueError("expires_round must be >= applied_round")
        if expires_phase not in AUTO_EXPIRY_PHASES:
            raise ValueError(
                "expires_phase must be ROUND_START or ROUND_END in Stage 3"
            )
