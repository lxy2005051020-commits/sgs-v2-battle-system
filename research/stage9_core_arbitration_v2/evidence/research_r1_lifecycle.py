import os
import json
import re
from collections import defaultdict, Counter

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

print(f"Total indexed reports: {len(index)}")

# Helper to load and parse events
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

# Scan for Normal Attack Windows:
# A normal attack starts at cfg_id == 9 (and is not an aid-redirected inner hit, or rather from cfg 9 to the next cfg 9 or cfg 733/723)
# Inside the attack window, identify:
# - main_damage: cfg 28
# - first_aid: '急救' in desc or cfg 16
# - lifesteal: '倒戈' in desc or '攻心' in desc
# - cleave: '群攻' in desc
# - counter: '反击' in desc
# - assault: assault skill activation (cfg 7 followed by 145/21, or assault keywords)
# - combo: '连击' in desc (cfg 230)
# - death: '无法再战' in desc (cfg 163)

candidate_reports = [f for f, tags in index.items() if any(t in tags for t in ['fan_ji', 'qun_gong', 'hou_fa', 'chen_mu', 'qi_ling'])]
print(f"Candidate reports with counter/cleave: {len(candidate_reports)}")

# Pairwise order counters:
# e.g., cleave_before_counter, counter_before_cleave, etc.
pair_stats = defaultdict(lambda: {'A_before_B': 0, 'B_before_A': 0, 'same_event': 0})
tri_reaction_cases = []
zero_damage_reaction_cases = []

assault_skills = {'暴戾无仁', '手起刀落', '百骑劫营', '一骑当千', '弯弓饮羽', '当锋摧决', '暗藏玄机', '矢志不移', '兵锋', '克敌制胜', '鬼神霆威', '勇者得前'}

for idx, r_name in enumerate(candidate_reports[:3000]):
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    # Segment into normal attacks
    # Look for normal attack start: cfg == 9
    attack_starts = [i for i, e in enumerate(events) if e['cfg_id'] == 9]
    for a_idx_pos, start_i in enumerate(attack_starts):
        # determine window end
        if a_idx_pos + 1 < len(attack_starts):
            end_i = attack_starts[a_idx_pos + 1]
        else:
            end_i = min(len(events), start_i + 30)
        
        # Check if between start_i and next there is a turn delimiter (733 / 723)
        for k in range(start_i + 1, end_i):
            if events[k]['cfg_id'] in [733, 723]:
                end_i = k
                break
        
        window = events[start_i:end_i]
        # Check reactions in this attack window
        dmg_indices = []
        aid_indices = []
        lifesteal_indices = []
        cleave_indices = []
        counter_indices = []
        assault_indices = []
        combo_indices = []
        death_indices = []
        
        for w_pos, ev in enumerate(window):
            abs_pos = start_i + w_pos
            cid = ev['cfg_id']
            desc = ev['desc']
            if cid == 28 or ('损失了兵力' in desc and cid not in [26, 145]):
                dmg_indices.append(abs_pos)
            if '急救' in desc:
                aid_indices.append(abs_pos)
            if '倒戈' in desc or '攻心' in desc or '恢复了兵力' in desc and any(k in desc for k in ['倒戈', '攻心']):
                lifesteal_indices.append(abs_pos)
            if '群攻' in desc:
                cleave_indices.append(abs_pos)
            if '反击' in desc:
                counter_indices.append(abs_pos)
            if cid == 7 and any(sk in desc for sk in assault_skills):
                assault_indices.append(abs_pos)
            if cid == 230 and '连击' in desc:
                combo_indices.append(abs_pos)
            if cid == 163 or '无法再战' in desc:
                death_indices.append(abs_pos)
        
        # Track pairs:
        # 1. Cleave vs Counter
        if cleave_indices and counter_indices:
            c_first = min(cleave_indices)
            cnt_first = min(counter_indices)
            if c_first < cnt_first:
                pair_stats['Cleave_vs_Counter']['A_before_B'] += 1
            elif cnt_first < c_first:
                pair_stats['Cleave_vs_Counter']['B_before_A'] += 1
            else:
                pair_stats['Cleave_vs_Counter']['same_event'] += 1
        
        # 2. Cleave vs Assault
        if cleave_indices and assault_indices:
            c_first = min(cleave_indices)
            a_first = min(assault_indices)
            if c_first < a_first:
                pair_stats['Cleave_vs_Assault']['A_before_B'] += 1
            elif a_first < c_first:
                pair_stats['Cleave_vs_Assault']['B_before_A'] += 1
            else:
                pair_stats['Cleave_vs_Assault']['same_event'] += 1
        
        # 3. Counter vs Assault
        if counter_indices and assault_indices:
            cnt_first = min(counter_indices)
            a_first = min(assault_indices)
            if cnt_first < a_first:
                pair_stats['Counter_vs_Assault']['A_before_B'] += 1
            elif a_first < cnt_first:
                pair_stats['Counter_vs_Assault']['B_before_A'] += 1
            else:
                pair_stats['Counter_vs_Assault']['same_event'] += 1
                
        # 4. Damage vs FirstAid
        if dmg_indices and aid_indices:
            d_first = min(dmg_indices)
            fa_first = min(aid_indices)
            if d_first < fa_first:
                pair_stats['Damage_vs_FirstAid']['A_before_B'] += 1
            elif fa_first < d_first:
                pair_stats['Damage_vs_FirstAid']['B_before_A'] += 1
                
        # 5. Counter vs Combo
        if counter_indices and combo_indices:
            cnt_first = min(counter_indices)
            cb_first = min(combo_indices)
            if cnt_first < cb_first:
                pair_stats['Counter_vs_Combo']['A_before_B'] += 1
            elif cb_first < cnt_first:
                pair_stats['Counter_vs_Combo']['B_before_A'] += 1
                
        # 6. Assault vs Combo
        if assault_indices and combo_indices:
            a_first = min(assault_indices)
            cb_first = min(combo_indices)
            if a_first < cb_first:
                pair_stats['Assault_vs_Combo']['A_before_B'] += 1
            elif cb_first < a_first:
                pair_stats['Assault_vs_Combo']['B_before_A'] += 1

        # Check for 3+ reactions: Cleave + Counter + Assault
        if cleave_indices and counter_indices and assault_indices:
            tri_reaction_cases.append({
                'report': r_name,
                'start_idx': start_i,
                'end_idx': end_i,
                'cleave': min(cleave_indices),
                'counter': min(counter_indices),
                'assault': min(assault_indices),
                'events': [{'idx': start_i + p, 'cfg': ev['cfg_id'], 'desc': ev['desc']} for p, ev in enumerate(window)]
            })

print("\n--- Pairwise Co-occurrence Matrix Results ---")
for pair, data in pair_stats.items():
    print(f"{pair:25s}: A_before_B={data['A_before_B']:5d}, B_before_A={data['B_before_A']:5d}, same={data['same_event']}")

print(f"\nTotal 3-reaction cases (Cleave + Counter + Assault): {len(tri_reaction_cases)}")
if tri_reaction_cases:
    sample = tri_reaction_cases[0]
    print(f"Sample 3-reaction report: {sample['report']} at event {sample['start_idx']}")
    for ev in sample['events']:
        print(f"  [{ev['idx']:3d}] cfg:{str(ev['cfg']):>4} | {ev['desc']}")

# Save results to evidence
out_path = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r1_lifecycle_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'pair_stats': dict(pair_stats),
        'tri_cases_count': len(tri_reaction_cases),
        'tri_cases_sample': tri_reaction_cases[:5] if tri_reaction_cases else []
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
