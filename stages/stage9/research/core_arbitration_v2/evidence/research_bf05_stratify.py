import os
import json
import re
from collections import defaultdict

INDEX_PATH = r'stages/stage9/research/core_arbitration_v2/evidence/stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

combo_reports = [f for f, tags in index.items() if 'lian_ji' in tags]
print(f"Total reports with combo: {len(combo_reports)}")

# strata: (candidate_count, has_taunt, has_confusion, target1_survived) -> list of bool(target2 == target1)
strata = defaultdict(list)
pattern_att = re.compile(r'\[(.*?)\]对\[(.*?)\]发动普通攻击')

sample_pairs = []

for r_name in combo_reports[:1500]:
    path = os.path.join(JSON_DIR, r_name)
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        continue

    # Extract teams from lineup if available
    lineup = data.get('lineup', {})
    left_team = set()
    right_team = set()
    # Left team (camp 1 / attack)
    for u in lineup.get('attack', {}).get('heroes', []):
        if u.get('name'):
            left_team.add(u['name'])
    for u in lineup.get('defend', {}).get('heroes', []):
        if u.get('name'):
            right_team.add(u['name'])

    events = []
    for g in data.get('detail', {}).get('groups', []):
        gkey = g.get('key')
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc
            })

    # Track deaths throughout the battle to know who is alive at any point
    dead_units = set()
    
    # Segment by turn: between cfg 723 and cfg 733
    turns = []
    curr_turn = []
    for e in events:
        if e['cfg_id'] == 723:
            curr_turn = [e]
        elif e['cfg_id'] == 733:
            curr_turn.append(e)
            turns.append(curr_turn)
            curr_turn = []
        elif curr_turn:
            curr_turn.append(e)

    for t_events in turns:
        # Check deaths in this turn
        combo_indices = [p for p, ev in enumerate(t_events) if ev['cfg_id'] == 230 and '连击' in ev['desc']]
        if not combo_indices:
            # update dead units
            for ev in t_events:
                if ev['cfg_id'] == 163 or '无法再战' in ev['desc']:
                    m_d = re.search(r'\[(.*?)\]', ev['desc'])
                    if m_d:
                        dead_units.add(m_d.group(1))
            continue

        pure_attacks = []
        for p, ev in enumerate(t_events):
            if ev['cfg_id'] == 9:
                if p > 0 and t_events[p-1]['cfg_id'] == 143:
                    continue
                m = pattern_att.search(ev['desc'])
                if m:
                    pure_attacks.append((p, m.group(1), m.group(2)))

        if len(pure_attacks) >= 2:
            cb_pos = combo_indices[0]
            hit1 = [a for a in pure_attacks if a[0] < cb_pos]
            hit2 = [a for a in pure_attacks if a[0] > cb_pos]
            if hit1 and hit2:
                h1_pos, att1, tgt1 = hit1[-1]
                h2_pos, att2, tgt2 = hit2[0]
                if att1 == att2:
                    # Deaths up to h2_pos
                    turn_dead = set(dead_units)
                    for x in t_events[:h2_pos]:
                        if x['cfg_id'] == 163 or '无法再战' in x['desc']:
                            m_d = re.search(r'\[(.*?)\]', x['desc'])
                            if m_d:
                                turn_dead.add(m_d.group(1))

                    # Determine attacker team and opposing team
                    if att1 in left_team:
                        enemy_team = right_team
                    elif att1 in right_team:
                        enemy_team = left_team
                    else:
                        # Fallback: if tgt1 in right_team, att1 is left
                        if tgt1 in right_team:
                            enemy_team = right_team
                        elif tgt1 in left_team:
                            enemy_team = left_team
                        else:
                            enemy_team = set()

                    living_enemies = [e for e in enemy_team if e not in turn_dead]
                    cand_count = len(living_enemies)
                    if cand_count == 0:
                        # if lineup extraction was incomplete, estimate from default 3
                        cand_count = 3 - len([d for d in turn_dead if d != att1])
                        cand_count = max(1, min(3, cand_count))

                    has_confusion = any('混乱' in x['desc'] for x in t_events[:h2_pos])
                    has_taunt = any('嘲讽' in x['desc'] and '执行来自' in x['desc'] for x in t_events[:h2_pos])
                    target1_died = (tgt1 in turn_dead)
                    same_target = (tgt1 == tgt2)

                    strata_key = (
                        cand_count,
                        "TAUNT" if has_taunt else ("CONFUSION" if has_confusion else "NORMAL"),
                        "DIED" if target1_died else "SURVIVED"
                    )
                    strata[strata_key].append(same_target)
                    sample_pairs.append({
                        'report': r_name,
                        'cand_count': cand_count,
                        'key': str(strata_key),
                        'att': att1,
                        'tgt1': tgt1,
                        'tgt2': tgt2,
                        'same': same_target
                    })

        # update dead units after turn
        for ev in t_events:
            if ev['cfg_id'] == 163 or '无法再战' in ev['desc']:
                m_d = re.search(r'\[(.*?)\]', ev['desc'])
                if m_d:
                    dead_units.add(m_d.group(1))

print("\n--- Detailed Stratified Combo Retargeting Results ---")
print(f"Total analyzed combo pairs: {sum(len(v) for v in strata.values())}")
print(f"{'Candidates':12s} | {'Condition':10s} | {'Target1':10s} | {'N':6s} | {'Same':6s} | {'Diff':6s} | {'Observed P(same)':18s} | {'Expected P(same)':18s}")
print("-" * 95)

out_summary = {}

for key in sorted(strata.keys(), key=lambda x: (str(x[1]), str(x[2]), x[0])):
    vals = strata[key]
    cand, cond, tgt_stat = key
    n = len(vals)
    same_c = sum(1 for x in vals if x)
    diff_c = n - same_c
    p_obs = same_c / n if n > 0 else 0
    
    if cond == "TAUNT":
        exp = 1.0
    elif tgt_stat == "DIED":
        exp = 0.0
    elif cond == "CONFUSION":
        exp = 0.20 # approx 1 out of 5 surviving units
    elif cand == 1:
        exp = 1.0
    elif cand == 2:
        exp = 0.50
    elif cand == 3:
        exp = 0.3333
    else:
        exp = -1.0

    print(f"{cand:<12d} | {cond:10s} | {tgt_stat:10s} | {n:<6d} | {same_c:<6d} | {diff_c:<6d} | {p_obs*100:6.2f}%            | {exp*100:6.2f}%")
    out_summary[str(key)] = {
        'candidate_count': cand,
        'condition': cond,
        'target1_status': tgt_stat,
        'n': n,
        'same': same_c,
        'diff': diff_c,
        'p_observed': p_obs,
        'p_expected': exp
    }

out_path = r'stages/stage9/research/core_arbitration_v2/evidence/r10_combo_detailed_stratified.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'summary': out_summary,
        'total': sum(len(v) for v in strata.values()),
        'samples': sample_pairs[:30]
    }, f, ensure_ascii=False, indent=2)
print("Saved detailed results to", out_path)
