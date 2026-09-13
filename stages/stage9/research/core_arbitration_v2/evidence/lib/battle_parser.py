import json
import os
import re
from dataclasses import dataclass
from .unit_identity import BattleUnitRef, UnitRegistry
from .state_tracker import StateTracker
from .target_pool import TargetPoolManager
from .action_segmenter import ActionSegmenter, NormalAttack, ComboPair

@dataclass
class ParsedBattle:
    battle_file: str
    registry: UnitRegistry
    pool_mgr: TargetPoolManager
    state_tracker: StateTracker
    normal_attacks: list[NormalAttack]
    combo_pairs: list[ComboPair]
    raw_events: list[dict]
    is_valid: bool
    parse_error: str | None = None


class BattleParser:
    def __init__(self, json_dir: str):
        self.json_dir = json_dir

    def parse_file(self, battle_file: str) -> ParsedBattle:
        fpath = os.path.join(self.json_dir, battle_file)
        if not os.path.exists(fpath):
            return ParsedBattle(
                battle_file=battle_file,
                registry=None,
                pool_mgr=None,
                state_tracker=None,
                normal_attacks=[],
                combo_pairs=[],
                raw_events=[],
                is_valid=False,
                parse_error="FILE_NOT_FOUND"
            )

        try:
            with open(fpath, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
        except Exception as ex:
            return ParsedBattle(
                battle_file=battle_file,
                registry=None,
                pool_mgr=None,
                state_tracker=None,
                normal_attacks=[],
                combo_pairs=[],
                raw_events=[],
                is_valid=False,
                parse_error=f"JSON_LOAD_ERROR: {str(ex)}"
            )

        lineup = data.get('lineup', {})
        registry = UnitRegistry(battle_file, lineup)
        pool_mgr = TargetPoolManager(registry)
        state_tracker = StateTracker(registry)

        # Flatten events with clean desc and index
        flat_events = []
        for g in data.get('detail', {}).get('groups', []):
            for e in g.get('data', {}).get('events', []):
                ev = e.get('event', {})
                raw_desc = ev.get('full_desc') or ev.get('desc') or ''
                clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
                flat_events.append({
                    'cfg_id': ev.get('cfg_id'),
                    'clean_desc': clean_desc,
                    'full_desc': raw_desc,
                    'args': ev.get('args', []),
                    'raw': ev
                })

        # Pass 1: State lifecycles and deaths
        current_skill_caster: BattleUnitRef | None = None
        current_skill_name: str | None = None

        for idx, ev in enumerate(flat_events):
            cid = ev['cfg_id']
            desc = ev['clean_desc']
            raw_desc = ev['full_desc']

            # Skill launch tracking: [X]发动战法【Y】
            m_cast = re.search(r'\[(.*?)\]发动战法【(.*?)】', desc)
            if m_cast:
                c_unit, _ = registry.resolve_from_event_text(m_cast.group(1), raw_desc)
                current_skill_caster = c_unit
                current_skill_name = m_cast.group(2)

            # Death tracking: cfg 163 or 无法再战
            if cid == 163 or '无法再战' in desc or '已经死亡' in desc:
                m_dead = re.search(r'\[(.*?)\]', desc)
                if m_dead:
                    d_unit, d_unambig = registry.resolve_from_event_text(m_dead.group(1), raw_desc)
                    if d_unit and d_unambig:
                        pool_mgr.mark_dead(d_unit, idx)
                        state_tracker.record_death(d_unit, idx)

            # State application
            for state_kw, state_type in StateTracker.STATE_KEYWORDS.items():
                if f'「{state_kw}」' in desc and ('已施加' in desc or '效果已施加' in desc or '执行来自' in desc):
                    m_tgt = re.search(r'\[(.*?)\]', desc)
                    if m_tgt:
                        tgt_unit, _ = registry.resolve_from_event_text(m_tgt.group(1), raw_desc)
                        if tgt_unit:
                            # Skill name
                            m_sk = re.search(r'【(.*?)】', desc)
                            sk_name = m_sk.group(1) if m_sk else current_skill_name
                            state_tracker._record_apply(
                                state_type=state_type,
                                owner=tgt_unit,
                                source=current_skill_caster,
                                skill=sk_name,
                                event_idx=idx
                            )

            # State removal / expiration
            for state_kw, state_type in StateTracker.STATE_KEYWORDS.items():
                if f'「{state_kw}」' in desc and ('已消失' in desc or '消失' in desc or '无效' in desc or '清除了' in desc or '恢复正常' in desc):
                    m_tgt = re.search(r'\[(.*?)\]', desc)
                    if m_tgt:
                        tgt_unit, _ = registry.resolve_from_event_text(m_tgt.group(1), raw_desc)
                        if tgt_unit:
                            state_tracker._record_expire(state_type, tgt_unit, idx)

        # Pass 2: Action segmentation and Combo extraction
        segmenter = ActionSegmenter(registry, pool_mgr, state_tracker)
        normal_attacks, combo_pairs = segmenter.segment_turns_and_actions(flat_events)

        return ParsedBattle(
            battle_file=battle_file,
            registry=registry,
            pool_mgr=pool_mgr,
            state_tracker=state_tracker,
            normal_attacks=normal_attacks,
            combo_pairs=combo_pairs,
            raw_events=flat_events,
            is_valid=True
        )
