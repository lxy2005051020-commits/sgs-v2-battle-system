from dataclasses import dataclass
from .unit_identity import BattleUnitRef, UnitRegistry
from .state_tracker import StateTracker

@dataclass
class CandidatePoolResult:
    attacker: BattleUnitRef
    candidate_count: int | None    # None indicates UNKNOWN
    candidates: list[BattleUnitRef]
    forced_target_reason: str | None # 'CONFUSION', 'TAUNT', or None
    is_known: bool
    unknown_reason: str | None = None


class TargetPoolManager:
    def __init__(self, registry: UnitRegistry):
        self.registry = registry
        # Track death event index: canonical_id -> event_idx
        self._death_events: dict[str, int] = {}

    def mark_dead(self, unit: BattleUnitRef, event_idx: int = 0):
        if unit.canonical_id not in self._death_events:
            self._death_events[unit.canonical_id] = event_idx

    def is_alive(self, unit: BattleUnitRef, event_idx: int | None = None) -> bool:
        if unit.canonical_id not in self._death_events:
            return True
        if event_idx is None:
            return False
        return event_idx < self._death_events[unit.canonical_id]

    def get_living_units(self, camp: str | None = None, event_idx: int | None = None) -> list[BattleUnitRef]:
        if camp:
            units = self.registry.units.get(camp, [])
        else:
            units = self.registry.all_units
        return [u for u in units if self.is_alive(u, event_idx)]

    def resolve_candidate_pool(self, attacker: BattleUnitRef, event_idx: int, state_tracker: StateTracker) -> CandidatePoolResult:
        # Check if attacker is alive at event_idx
        if not self.is_alive(attacker, event_idx):
            return CandidatePoolResult(
                attacker=attacker,
                candidate_count=None,
                candidates=[],
                forced_target_reason=None,
                is_known=False,
                unknown_reason="ATTACKER_DEAD"
            )

        # Check special states on attacker at event_idx
        is_confused = state_tracker.is_state_active(attacker, 'CONFUSION', event_idx)
        taunt_state = state_tracker.get_active_state(attacker, 'TAUNT', event_idx)

        # Rule 1: Confusion overrides Taunt
        if is_confused:
            # All living units on battlefield except attacker
            pool = [u for u in self.get_living_units(event_idx=event_idx) if not u.same_unit(attacker)]
            return CandidatePoolResult(
                attacker=attacker,
                candidate_count=len(pool),
                candidates=pool,
                forced_target_reason='CONFUSION',
                is_known=True
            )

        # Rule 2: Taunt locks target to taunter
        if taunt_state and taunt_state.source:
            taunter = taunt_state.source
            if self.is_alive(taunter, event_idx):
                return CandidatePoolResult(
                    attacker=attacker,
                    candidate_count=1,
                    candidates=[taunter],
                    forced_target_reason='TAUNT',
                    is_known=True
                )
            # If taunter is dead, fall through to normal enemies

        # Rule 3: Normal opposing team living units
        enemy_camp = 'enemy' if attacker.camp == 'my' else 'my'
        if self.registry.has_duplicate_names(enemy_camp):
            return CandidatePoolResult(
                attacker=attacker,
                candidate_count=None,
                candidates=[],
                forced_target_reason=None,
                is_known=False,
                unknown_reason="DUPLICATE_CAMP_UNIT_NAMES"
            )

        enemy_units = self.get_living_units(enemy_camp, event_idx=event_idx)

        if not enemy_units:
            return CandidatePoolResult(
                attacker=attacker,
                candidate_count=None,
                candidates=[],
                forced_target_reason=None,
                is_known=False,
                unknown_reason="NO_LIVING_ENEMIES"
            )

        return CandidatePoolResult(
            attacker=attacker,
            candidate_count=len(enemy_units),
            candidates=enemy_units,
            forced_target_reason=None,
            is_known=True
        )
