from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    PHASE_ENTERED = "PHASE_ENTERED"
    BATTLE_STARTED = "BATTLE_STARTED"
    ROUND_STARTED = "ROUND_STARTED"
    ACTION_ORDER_DECIDED = "ACTION_ORDER_DECIDED"
    UNIT_ACTION_STARTED = "UNIT_ACTION_STARTED"
    NORMAL_ATTACK = "NORMAL_ATTACK"
    DAMAGE_DEALT = "DAMAGE_DEALT"
    UNIT_DEFEATED = "UNIT_DEFEATED"
    UNIT_ACTION_ENDED = "UNIT_ACTION_ENDED"
    ROUND_ENDED = "ROUND_ENDED"
    STATE_APPLIED = "STATE_APPLIED"
    STATE_REMOVED = "STATE_REMOVED"
    STATE_EXPIRED = "STATE_EXPIRED"
    BATTLE_ENDED = "BATTLE_ENDED"


@dataclass(frozen=True, slots=True)
class BattleEvent:
    sequence: int
    event_type: EventType
    phase: str
    round_no: int
    actor_id: str | None = None
    target_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[BattleEvent], None]


class EventBus:
    """
    阶段 1 的同步事件总线。

    约束：
    - EventBus 只记录/分发“已经发生”的事实。
    - EventBus 不反向决定战斗结果。
    - history 是 BattleReport 的原始事件源，正式 Report 层后续再接。
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._all_handlers: list[EventHandler] = []
        self._history: list[BattleEvent] = []
        self._sequence = 0

    @property
    def history(self) -> tuple[BattleEvent, ...]:
        return tuple(self._history)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._all_handlers.append(handler)

    def publish(
        self,
        *,
        event_type: EventType,
        phase: str,
        round_no: int,
        actor_id: str | None = None,
        target_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BattleEvent:
        self._sequence += 1
        event = BattleEvent(
            sequence=self._sequence,
            event_type=event_type,
            phase=phase,
            round_no=round_no,
            actor_id=actor_id,
            target_id=target_id,
            payload=dict(payload or {}),
        )
        self._history.append(event)

        for handler in tuple(self._all_handlers):
            handler(event)

        for handler in tuple(self._handlers.get(event_type, ())):
            handler(event)

        return event
