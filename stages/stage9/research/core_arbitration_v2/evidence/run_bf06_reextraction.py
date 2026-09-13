import os
import json
import re
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

from evidence.lib.battle_parser import BattleParser

INDEX_PATH = os.path.join(BASE_DIR, 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

counter_files = [f for f, tags in index.items() if any(t in tags for t in ['fan_ji', 'hou_fa', 'qi_ling'])]
chain_files = [f for f, tags in index.items() if 'tie_suo' in tags or 'lian_huan' in tags]
share_files = [f for f, tags in index.items() if 'fen_dan' in tags or 'lu_jiang' in tags]
combo_files = [f for f, tags in index.items() if 'lian_ji' in tags]

print(f"BF-06 Candidates: Counter={len(counter_files)}, Chain={len(chain_files)}, Share={len(share_files)}, Combo={len(combo_files)}")

parser = BattleParser(JSON_DIR)

# 1. Counter -> Counter
c2c_source = 0
c2c_eligible = 0
c2c_triggered = 0
c2c_excluded_reasons = defaultdict(int)

for idx_f, fname in enumerate(counter_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        continue

    events = pb.raw_events
    for i, ev in enumerate(events):
        desc = ev['clean_desc']
        raw_desc = ev['full_desc']
        # Counter event: [A]由于[B]【Skill】的「反击」效果，损失了兵力
        if '「反击」效果' in desc and '损失了兵力' in desc:
            c2c_source += 1
            # Extract victim (A) and counterer (B)
            m = re.search(r'\[(.*?)\]由于\[(.*?)\]', desc)
            if not m:
                c2c_excluded_reasons['PARSE_FAILED'] += 1
                continue

            victim_ref, _ = pb.registry.resolve_from_event_text(m.group(1), raw_desc)
            counterer_ref, _ = pb.registry.resolve_from_event_text(m.group(2), raw_desc)

            if not victim_ref or not counterer_ref:
                c2c_excluded_reasons['IDENTITY_AMBIGUOUS'] += 1
                continue

            # Check eligibility at event i:
            # 1. Is victim A still alive right after taking counter damage?
            # Check if victim died at or immediately following this hit
            victim_alive = pb.pool_mgr.is_alive(victim_ref, i)
            # Also check if death event on victim happens in next 2 events
            for next_e in events[i:min(len(events), i+3)]:
                if (next_e['cfg_id'] == 163 or '无法再战' in next_e['clean_desc']) and victim_ref.display_name in next_e['clean_desc']:
                    victim_alive = False
                    break

            if not victim_alive:
                c2c_excluded_reasons['VICTIM_DIED'] += 1
                continue

            # 2. Does victim A have active COUNTER state at event i?
            has_counter = pb.state_tracker.is_state_active(victim_ref, 'COUNTER', i)
            if not has_counter:
                c2c_excluded_reasons['VICTIM_NO_COUNTER_STATE'] += 1
                continue

            # ELIGIBLE!
            c2c_eligible += 1

            # Check if A counters B in next 4 events
            triggered = False
            for next_e in events[i+1:min(len(events), i+5)]:
                if next_e['cfg_id'] in [723, 733]:
                    break
                ndesc = next_e['clean_desc']
                if '「反击」效果' in ndesc and f'[{counterer_ref.display_name}]' in ndesc and f'[{victim_ref.display_name}]' in ndesc:
                    triggered = True
                    break

            if triggered:
                c2c_triggered += 1

print(f"\nCounter -> Counter:")
print(f"  Source: {c2c_source}, Eligible: {c2c_eligible}, Triggered: {c2c_triggered}")
print(f"  Excluded breakdown: {dict(c2c_excluded_reasons)}")

# 2. Chain -> Chain
chain_source = 0
chain_eligible = 0
chain_triggered = 0
chain_excluded_reasons = defaultdict(int)

for idx_f, fname in enumerate(chain_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        continue

    events = pb.raw_events
    for i, ev in enumerate(events):
        desc = ev['clean_desc']
        raw_desc = ev['full_desc']
        # Chain hit event: [B]由于[C]【连环计】的「铁索连环」效果，损失了兵力
        if '「铁索连环」效果' in desc and '损失了兵力' in desc:
            chain_source += 1
            m = re.search(r'\[(.*?)\]由于', desc)
            if not m:
                chain_excluded_reasons['PARSE_FAILED'] += 1
                continue
            victim_ref, _ = pb.registry.resolve_from_event_text(m.group(1), raw_desc)
            if not victim_ref:
                chain_excluded_reasons['IDENTITY_AMBIGUOUS'] += 1
                continue

            # Eligibility:
            # 1. B is alive
            if not pb.pool_mgr.is_alive(victim_ref, i):
                chain_excluded_reasons['VICTIM_DIED'] += 1
                continue

            # 2. B is in active CHAIN state
            if not pb.state_tracker.is_state_active(victim_ref, 'CHAIN', i):
                chain_excluded_reasons['VICTIM_NOT_CHAINED'] += 1
                continue

            # 3. There is at least 1 other living chained ally on B's camp
            other_chained_allies = [
                u for u in pb.pool_mgr.get_living_units(victim_ref.camp, i)
                if not u.same_unit(victim_ref) and pb.state_tracker.is_state_active(u, 'CHAIN', i)
            ]
            if not other_chained_allies:
                chain_excluded_reasons['NO_OTHER_CHAINED_ALLIES'] += 1
                continue

            chain_eligible += 1

            # Did this damage trigger a NEW recursive chain broadcast?
            # Note: A new broadcast would be [B]执行来自【连环计】的「铁索连环」效果
            # where B is the initiator of the feedback!
            # If the next event is [C]执行来自【连环计】 (where C was the original target of skill), that is SAME original broadcast!
            triggered = False
            for next_e in events[i+1:min(len(events), i+4)]:
                if next_e['cfg_id'] in [723, 733]:
                    break
                ndesc = next_e['clean_desc']
                if f'[{victim_ref.display_name}]执行来自' in ndesc and '「铁索连环」' in ndesc:
                    triggered = True
                    break
            if triggered:
                chain_triggered += 1

print(f"\nChain -> Chain:")
print(f"  Source: {chain_source}, Eligible: {chain_eligible}, Triggered: {chain_triggered}")
print(f"  Excluded breakdown: {dict(chain_excluded_reasons)}")

# 3. Share -> Share
share_source = 0
share_eligible = 0
share_triggered = 0
share_excluded_reasons = defaultdict(int)

for idx_f, fname in enumerate(share_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        continue

    events = pb.raw_events
    for i, ev in enumerate(events):
        desc = ev['clean_desc']
        raw_desc = ev['full_desc']
        if '「分担」效果' in desc and ('损失了兵力' in desc or ev['cfg_id'] == 28):
            # Check if this unit is the sharer taking share damage
            m = re.search(r'\[(.*?)\]', desc)
            if not m:
                continue
            sharer_ref, _ = pb.registry.resolve_from_event_text(m.group(1), raw_desc)
            if not sharer_ref:
                continue

            # Did this damage come from a share effect?
            # Check preceding 3 events for '执行来自...的分担效果'
            is_share_damage = any('「分担」' in prev_e['clean_desc'] and '执行来自' in prev_e['clean_desc'] for prev_e in events[max(0, i-3):i])
            if is_share_damage:
                share_source += 1
                # Is sharer_ref covered by a SECOND active share state from another teammate?
                # Look for share states where owner == sharer_ref, but source != sharer_ref
                share_st = pb.state_tracker.get_active_state(sharer_ref, 'SHARE', i)
                if share_st and share_st.source and not share_st.source.same_unit(sharer_ref) and pb.pool_mgr.is_alive(share_st.source, i):
                    share_eligible += 1
                    # Check if second share triggered
                    triggered = False
                    for next_e in events[i+1:min(len(events), i+4)]:
                        if '「分担」效果' in next_e['clean_desc'] and '损失了兵力' in next_e['clean_desc']:
                            triggered = True
                            break
                    if triggered:
                        share_triggered += 1
                else:
                    share_excluded_reasons['NO_SECOND_SHARER_COVERING_SHARER'] += 1

print(f"\nShare -> Share:")
print(f"  Source: {share_source}, Eligible: {share_eligible}, Triggered: {share_triggered}")
print(f"  Excluded breakdown: {dict(share_excluded_reasons)}")

# 4. Combo2 -> Combo3
combo_source = 0
combo_hit3_triggered = 0

for idx_f, fname in enumerate(combo_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        continue

    # Use ActionSegmenter's combo_pairs and turns
    for c in pb.combo_pairs:
        combo_source += 1
        # Check if in the same turn, after hit2, there is an additional NormalAttack by same actor
        # Check normal_attacks in pb
        atks_by_actor_after_hit2 = [
            a for a in pb.normal_attacks
            if a.actor.same_unit(c.actor) and a.declare_event_idx > c.hit2.declare_event_idx and not a.is_guard_redirected
        ]
        # Must be in same turn (before next turn start cfg 723)
        # Find next turn start after hit2
        next_turn_idx = 999999
        for ev_idx, ev in enumerate(pb.raw_events):
            if ev_idx > c.hit2.declare_event_idx and ev['cfg_id'] == 723:
                next_turn_idx = ev_idx
                break
        valid_hit3 = [a for a in atks_by_actor_after_hit2 if a.declare_event_idx < next_turn_idx]
        if valid_hit3:
            combo_hit3_triggered += 1

print(f"\nCombo2 -> Combo3:")
print(f"  Source Combos: {combo_source}, Hit3 Triggered: {combo_hit3_triggered}")

out_path = os.path.join(BASE_DIR, 'r7_recursion_denominators.json')
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump({
        'c2c': {
            'source': c2c_source,
            'eligible': c2c_eligible,
            'triggered': c2c_triggered,
            'status': 'BLOCKED' if c2c_eligible > 0 and c2c_triggered == 0 else ('NOT_OBSERVED' if c2c_eligible == 0 else 'ALLOWED'),
            'excluded_reasons': dict(c2c_excluded_reasons)
        },
        'chain': {
            'source': chain_source,
            'eligible': chain_eligible,
            'triggered': chain_triggered,
            'status': 'BLOCKED' if chain_eligible > 0 and chain_triggered == 0 else ('NOT_OBSERVED' if chain_eligible == 0 else 'ALLOWED'),
            'excluded_reasons': dict(chain_excluded_reasons)
        },
        'share': {
            'source': share_source,
            'eligible': share_eligible,
            'triggered': share_triggered,
            'status': 'BLOCKED' if share_eligible > 0 and share_triggered == 0 else ('NOT_OBSERVED' if share_eligible == 0 else 'ALLOWED'),
            'excluded_reasons': dict(share_excluded_reasons)
        },
        'combo': {
            'source': combo_source,
            'eligible': combo_source,
            'triggered': combo_hit3_triggered,
            'status': 'BLOCKED' if combo_hit3_triggered == 0 else 'ALLOWED'
        }
    }, fp, ensure_ascii=False, indent=2)

print(f"\nSaved recursion denominator data to {out_path}")
