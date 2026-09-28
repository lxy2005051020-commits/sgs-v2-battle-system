from pathlib import Path
import os
import json
import re
from collections import defaultdict

INDEX_PATH = str(Path(__file__).resolve().parent / 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

combo_reports = [f for f, tags in index.items() if 'lian_ji' in tags]
print(f"Total reports with combo: {len(combo_reports)}")

def load_events(report_name):
    path = os.path.join(JSON_DIR, report_name)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    events = []
    for g in data.get('detail', {}).get('groups', []):
        gkey = g.get('key')
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'group': gkey,
                'key': e.get('key'),
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc,
                'raw': ev
            })
    return events

# Stratification categories:
# (candidates_count, has_taunt, has_confusion, target1_died) -> list of bool(target2 == target1)
strata = defaultdict(list)
pattern_att = re.compile(r'\[(.*?)\]对\[(.*?)\]发动普通攻击')

sample_pairs = []

for r_name in combo_reports[:1200]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
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
        # Check if combo executed: cfg 230 and '连击'
        combo_indices = [p for p, ev in enumerate(t_events) if ev['cfg_id'] == 230 and '连击' in ev['desc']]
        if not combo_indices:
            continue
        
        # Find normal attacks (cfg 9)
        # Exclude aid redirected attacks (i.e. if preceded by cfg 143)
        pure_attacks = []
        for p, ev in enumerate(t_events):
            if ev['cfg_id'] == 9:
                if p > 0 and t_events[p-1]['cfg_id'] == 143:
                    continue # redirected hit
                m = pattern_att.search(ev['desc'])
                if m:
                    pure_attacks.append((p, m.group(1), m.group(2)))
        
        # If there are at least 2 pure normal attacks
        if len(pure_attacks) >= 2:
            cb_pos = combo_indices[0]
            # hit1 is attack before combo, hit2 is attack after combo
            hit1 = [a for a in pure_attacks if a[0] < cb_pos]
            hit2 = [a for a in pure_attacks if a[0] > cb_pos]
            if hit1 and hit2:
                h1_pos, att1, tgt1 = hit1[-1]
                h2_pos, att2, tgt2 = hit2[0]
                if att1 == att2:
                    # Check context:
                    # 1. Confusion: was attacker confused?
                    has_confusion = any('混乱' in x['desc'] for x in t_events[:h2_pos])
                    # 2. Taunt: was attacker taunted?
                    has_taunt = any('嘲讽' in x['desc'] and '执行来自' in x['desc'] for x in t_events[:h2_pos])
                    # 3. Did target1 die between h1 and h2?
                    target1_died = any((x['cfg_id'] == 163 or '无法再战' in x['desc']) and tgt1 in x['desc'] for x in t_events[h1_pos:h2_pos])
                    
                    # Estimate surviving candidates for attacker at h2:
                    # Look at surviving enemies
                    # In Three Kingdoms Tactics, default is 3 per team, minus deaths seen so far
                    # Let's count how many enemy units died before h2_pos
                    # For a cleaner stratification, let's group by:
                    # target1_died, has_taunt, has_confusion
                    same_target = (tgt1 == tgt2)
                    strata_key = (
                        "TAUNT" if has_taunt else ("CONFUSION" if has_confusion else "NORMAL"),
                        "DIED" if target1_died else "SURVIVED"
                    )
                    strata[strata_key].append(same_target)
                    if len(sample_pairs) < 1000:
                        sample_pairs.append({
                            'report': r_name,
                            'attacker': att1,
                            'tgt1': tgt1,
                            'tgt2': tgt2,
                            'same': same_target,
                            'key': strata_key
                        })

print("\n--- Stratified Combo Retargeting Results ---")
total_pairs = sum(len(v) for v in strata.values())
print(f"Total analyzed combo pairs: {total_pairs}")

for key, vals in sorted(strata.items()):
    same_c = sum(1 for x in vals if x)
    diff_c = sum(1 for x in vals if not x)
    p_same = same_c / len(vals) if vals else 0
    print(f"Stratum {str(key):30s}: Total={len(vals):4d} | Same={same_c:4d} ({p_same*100:5.2f}%), Diff={diff_c:4d} ({(1-p_same)*100:5.2f}%)")

out_path = str(Path(__file__).resolve().parent / 'r10_combo_stratified_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total': total_pairs,
        'strata': {str(k): {'total': len(v), 'same': sum(1 for x in v if x), 'diff': sum(1 for x in v if not x), 'p_same': sum(1 for x in v if x)/len(v) if v else 0} for k, v in strata.items()},
        'samples': sample_pairs[:20]
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
