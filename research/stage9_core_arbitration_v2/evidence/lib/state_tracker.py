from dataclasses import dataclass, field
import re
from .unit_identity import BattleUnitRef, UnitRegistry

@dataclass
class StateLifetime:
    state_type: str         # 'CONFUSION', 'TAUNT', 'GUARD', 'COUNTER', 'CHAIN', 'SHARE', 'COMBO'
    owner: BattleUnitRef
    source: BattleUnitRef | None = None
    source_skill: str | None = None
    apply_event_idx: int = 0
    expire_event_idx: int | None = None
    refresh_event_indices: list[int] = field(default_factory=list)
    terminated_by_death: bool = False

    def is_active_at(self, event_idx: int) -> bool:
        if event_idx < self.apply_event_idx:
            return False
        if self.expire_event_idx is not None and event_idx >= self.expire_event_idx:
            return False
        return True


class StateTracker:
    STATE_KEYWORDS = {
        '混乱': 'CONFUSION',
        '嘲讽': 'TAUNT',
        '援护': 'GUARD',
        '反击': 'COUNTER',
        '铁索连环': 'CHAIN',
        '分担': 'SHARE',
        '连击': 'COMBO'
    }

    COUNTER_SKILLS = {'后发制人', '气凌三军', '三里而还', '刚烈不屈', '益寿延年'}

    def __init__(self, registry: UnitRegistry):
        self.registry = registry
        # key: (unit_canonical_id, state_type) -> list of StateLifetime
        self.state_histories: dict[tuple[str, str], list[StateLifetime]] = {}
        # key: (unit_canonical_id, state_type) -> currently active StateLifetime | None
        self.active_states: dict[tuple[str, str], StateLifetime] = {}

    def _record_apply(self, state_type: str, owner: BattleUnitRef, source: BattleUnitRef | None, skill: str | None, event_idx: int):
        key = (owner.canonical_id, state_type)
        # If already active, close prior or add refresh
        if key in self.active_states:
            prior = self.active_states[key]
            prior.refresh_event_indices.append(event_idx)
            return

        lifetime = StateLifetime(
            state_type=state_type,
            owner=owner,
            source=source,
            source_skill=skill,
            apply_event_idx=event_idx
        )
        self.active_states[key] = lifetime
        self.state_histories.setdefault(key, []).append(lifetime)

    def _record_expire(self, state_type: str, owner: BattleUnitRef, event_idx: int, by_death: bool = False):
        key = (owner.canonical_id, state_type)
        if key in self.active_states:
            lifetime = self.active_states.pop(key)
            lifetime.expire_event_idx = event_idx
            lifetime.terminated_by_death = by_death

    def record_death(self, dead_unit: BattleUnitRef, event_idx: int):
        # 1. Close all states owned by dead unit
        for key in list(self.active_states.keys()):
            unit_id, st_type = key
            if unit_id == dead_unit.canonical_id:
                self._record_expire(st_type, dead_unit, event_idx, by_death=True)

        # 2. Close any states where dead unit was the source (e.g. Taunter died -> Taunt ends; Rescuer died -> Guard ends)
        for key in list(self.active_states.keys()):
            lifetime = self.active_states[key]
            if lifetime.source and lifetime.source.same_unit(dead_unit):
                self._record_expire(lifetime.state_type, lifetime.owner, event_idx, by_death=True)

    def is_state_active(self, unit: BattleUnitRef, state_type: str, event_idx: int) -> bool:
        key = (unit.canonical_id, state_type)
        histories = self.state_histories.get(key, [])
        for st in histories:
            if st.is_active_at(event_idx):
                return True
        return False

    def get_active_state(self, unit: BattleUnitRef, state_type: str, event_idx: int) -> StateLifetime | None:
        key = (unit.canonical_id, state_type)
        histories = self.state_histories.get(key, [])
        for st in histories:
            if st.is_active_at(event_idx):
                return st
        return None
