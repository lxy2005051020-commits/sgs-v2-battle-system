from dataclasses import dataclass, field
import re
from .unit_identity import BattleUnitRef, UnitRegistry
from .state_tracker import StateTracker
from .target_pool import TargetPoolManager

@dataclass
class NormalAttack:
    declare_event_idx: int
    actor: BattleUnitRef
    intended_target: BattleUnitRef
    resolved_target: BattleUnitRef
    is_guard_redirected: bool = False
    guard_event_idx: int | None = None
    target_survived: bool = True
    damage_event_indices: list[int] = field(default_factory=list)
    reactions: list[tuple[str, int, str]] = field(default_factory=list) # (kind, event_idx, desc)


@dataclass
class ComboPair:
    actor: BattleUnitRef
    checkpoint_idx: int
    hit1: NormalAttack
    hit2: NormalAttack
    candidate_count: int | None
    condition: str          # 'NORMAL', 'TAUNT', 'CONFUSION', 'OTHER_FORCED'
    target1_status: str     # 'SURVIVED' or 'DIED'
    pool_changed: bool
    same_target: bool


class ActionSegmenter:
    def __init__(self, registry: UnitRegistry, pool_mgr: TargetPoolManager, state_tracker: StateTracker):
        self.registry = registry
        self.pool_mgr = pool_mgr
        self.state_tracker = state_tracker

    def segment_turns_and_actions(self, events: list[dict]) -> tuple[list[NormalAttack], list[ComboPair]]:
        normal_attacks: list[NormalAttack] = []
        combo_pairs: list[ComboPair] = []

        current_turn_actor: BattleUnitRef | None = None
        turn_events: list[tuple[int, dict]] = []

        for idx, ev in enumerate(events):
            cid = ev.get('cfg_id')
            desc = ev.get('clean_desc', '')
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''

            # Turn start: cfg 723
            if cid == 723:
                turn_events = [(idx, ev)]
                actor_ref, _ = self.registry.resolve_from_event_text(desc, raw_desc)
                current_turn_actor = actor_ref
                continue

            # Turn end: cfg 733
            if cid == 733:
                turn_events.append((idx, ev))
                # Process attacks and combos in completed turn
                self._process_turn(turn_events, current_turn_actor, normal_attacks, combo_pairs)
                current_turn_actor = None
                turn_events = []
                continue

            if current_turn_actor is not None:
                turn_events.append((idx, ev))

        return normal_attacks, combo_pairs

    def _process_turn(self, turn_events: list[tuple[int, dict]], actor: BattleUnitRef | None,
                      all_attacks: list[NormalAttack], all_combos: list[ComboPair]):
        if not turn_events or not actor:
            return

        # Find pure NormalAttack declarations (cfg 9)
        # INV-05: A cfg 9 preceded by cfg 143 (or inside a guard block) is a redirect, NOT a new attack!
        attacks_in_turn: list[NormalAttack] = []
        i = 0
        while i < len(turn_events):
            ev_idx, ev = turn_events[i]
            cid = ev.get('cfg_id')
            desc = ev.get('clean_desc', '')
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''

            if cid == 9:
                # Check if this cfg 9 is a guard redirect duplicate (INV-05)
                is_redirect = False
                guard_idx = None
                if i > 0:
                    prev_idx, prev_ev = turn_events[i-1]
                    if prev_ev.get('cfg_id') == 143 or '「援护」' in prev_ev.get('clean_desc', ''):
                        is_redirect = True
                        guard_idx = prev_idx

                if is_redirect:
                    # Update previous attack's resolved_target if exists
                    if attacks_in_turn:
                        last_atk = attacks_in_turn[-1]
                        last_atk.is_guard_redirected = True
                        last_atk.guard_event_idx = guard_idx
                        # Extract redirected target
                        m_tgt = re.search(r'对\[(.*?)\]发动普通攻击', desc)
                        if m_tgt:
                            tgt_ref, _ = self.registry.resolve_from_event_text(m_tgt.group(1), raw_desc)
                            if tgt_ref:
                                last_atk.resolved_target = tgt_ref
                    i += 1
                    continue

                # Fresh pure attack declaration
                m_atk = re.search(r'\[(.*?)\]对\[(.*?)\]发动普通攻击', desc)
                if not m_atk:
                    # e.g. 对[Target]发动普通攻击
                    m_tgt = re.search(r'对\[(.*?)\]发动普通攻击', desc)
                    tgt_name = m_tgt.group(1) if m_tgt else None
                    atk_ref = actor
                    atk_unambig = True
                else:
                    atk_name, tgt_name = m_atk.group(1), m_atk.group(2)
                    atk_ref, atk_unambig = self.registry.resolve_from_event_text(atk_name, raw_desc)
                    if not atk_ref:
                        atk_ref = actor
                        atk_unambig = True

                tgt_ref = None
                tgt_unambig = False
                if tgt_name:
                    tgt_ref, tgt_unambig = self.registry.resolve_from_event_text(tgt_name, raw_desc)

                if atk_ref and tgt_ref and atk_unambig and tgt_unambig:
                    atk_obj = NormalAttack(
                        declare_event_idx=ev_idx,
                        actor=atk_ref,
                        intended_target=tgt_ref,
                        resolved_target=tgt_ref
                    )
                    # Collect inner damage and reactions up to next cfg 9 or turn end
                    attacks_in_turn.append(atk_obj)
                    all_attacks.append(atk_obj)
            i += 1

        # Check for Combo in turn (cfg 230 with 连击)
        combo_checkpoints = [
            (ev_idx, ev) for ev_idx, ev in turn_events
            if ev.get('cfg_id') == 230 and '连击' in ev.get('clean_desc', '')
        ]

        if combo_checkpoints and len(attacks_in_turn) >= 2:
            cb_idx, cb_ev = combo_checkpoints[0]
            hit1_candidates = [a for a in attacks_in_turn if a.declare_event_idx < cb_idx]
            hit2_candidates = [a for a in attacks_in_turn if a.declare_event_idx > cb_idx]

            if hit1_candidates and hit2_candidates:
                h1 = hit1_candidates[-1]
                h2 = hit2_candidates[0]

                # INV-06: Hit1.actor == Hit2.actor must hold
                if h1.actor.same_unit(h2.actor):
                    # Check candidate pool at h2
                    pool_res = self.pool_mgr.resolve_candidate_pool(h2.actor, h2.declare_event_idx, self.state_tracker)
                    
                    # Target 1 status at h2
                    tgt1_survived = self.pool_mgr.is_alive(h1.intended_target, h2.declare_event_idx)
                    tgt1_status = 'SURVIVED' if tgt1_survived else 'DIED'

                    # Condition
                    if pool_res.forced_target_reason == 'TAUNT':
                        cond = 'TAUNT'
                    elif pool_res.forced_target_reason == 'CONFUSION':
                        cond = 'CONFUSION'
                    else:
                        cond = 'NORMAL'

                    # Check if candidate pool changed between h1 and h2 (e.g. unit died during h1)
                    enemy_camp = 'enemy' if h1.actor.camp == 'my' else 'my'
                    living_h1 = len(self.pool_mgr.get_living_units(enemy_camp, h1.declare_event_idx))
                    living_h2 = len(self.pool_mgr.get_living_units(enemy_camp, h2.declare_event_idx))
                    pool_changed = (living_h1 != living_h2)

                    same_tgt = h1.intended_target.same_unit(h2.intended_target)

                    all_combos.append(ComboPair(
                        actor=h1.actor,
                        checkpoint_idx=cb_idx,
                        hit1=h1,
                        hit2=h2,
                        candidate_count=pool_res.candidate_count if pool_res.is_known else None,
                        condition=cond,
                        target1_status=tgt1_status,
                        pool_changed=pool_changed,
                        same_target=same_tgt
                    ))
