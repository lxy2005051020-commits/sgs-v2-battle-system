from __future__ import annotations

from dataclasses import dataclass

from .enums import BattlePhase


_AUTO_EXPIRE_PHASES = frozenset(
    {
        BattlePhase.ROUND_START.value,
        BattlePhase.ROUND_END.value,
    }
)

_PHASE_ORDER = {
    "NOT_STARTED": -1,
    BattlePhase.PRE_BATTLE.value: 0,
    BattlePhase.ROUND_START.value: 1,
    BattlePhase.ACTION_ORDER.value: 2,
    BattlePhase.UNIT_ACTION_START.value: 3,
    BattlePhase.UNIT_ACTION.value: 4,
    BattlePhase.UNIT_ACTION_END.value: 5,
    BattlePhase.ROUND_END.value: 6,
    BattlePhase.BATTLE_END.value: 7,
}


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
        if self.source_id == "":
            raise ValueError("source_id cannot be empty when provided")
        if self.source_skill_id == "":
            raise ValueError("source_skill_id cannot be empty when provided")
        if self.applied_round < 0:
            raise ValueError("applied_round must be >= 0")
        if not self.applied_phase:
            raise ValueError("applied_phase cannot be empty")

        has_expires_round = self.expires_round is not None
        has_expires_phase = self.expires_phase is not None
        if has_expires_round != has_expires_phase:
            raise ValueError(
                "expires_round and expires_phase must both be set or both be None"
            )

        if self.expires_round is None:
            return

        if self.expires_round < 1:
            raise ValueError("expires_round must be >= 1")
        if self.expires_round < self.applied_round:
            raise ValueError("expires_round must be >= applied_round")
        if self.expires_phase not in _AUTO_EXPIRE_PHASES:
            raise ValueError(
                "expires_phase must be ROUND_START or ROUND_END"
            )

        # 同回合过期时，过期节点必须位于施加节点之后，否则 Engine 已经
        # 不可能再次到达该自动过期节点，实例会永久残留在 Registry 中。
        if self.expires_round == self.applied_round:
            try:
                applied_phase_order = _PHASE_ORDER[self.applied_phase]
            except KeyError as exc:
                raise ValueError(
                    f"unknown applied_phase for expiration validation: {self.applied_phase}"
                ) from exc

            expires_phase_order = _PHASE_ORDER[self.expires_phase]
            if expires_phase_order <= applied_phase_order:
                raise ValueError(
                    "expiration anchor must be a future lifecycle node"
                )
