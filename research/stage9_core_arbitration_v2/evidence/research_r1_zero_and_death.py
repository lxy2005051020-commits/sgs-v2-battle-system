import os
import json
import re

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

assault_skills = {'暴戾无仁', '手起刀落', '百骑劫营', '一骑当千', '弯弓饮羽', '当锋摧决', '暗藏玄机', '矢志不移', '兵锋', '克敌制胜', '鬼神霆威', '勇者得前'}

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

# Check:
# 1. Zero damage (虚弱: cfg 117 / 损失了兵力0) -> Does Cleave trigger? Does Counter trigger? Does Assault trigger?
# 2. Barrier (抵御: cfg 22) -> Does Cleave trigger? Does Counter trigger? Does Assault trigger?
# 3. Dodge (规避: 规避了本次攻击 / 成功规避) -> Does Cleave trigger? Does Counter trigger? Does Assault trigger?
# 4. Attacker dies in Counter (cfg 163 / 无法再战) -> Does Assault execute? Does Combo execute?

results = {
    'zero_damage_cleave': [],
    'zero_damage_counter': [],
    'zero_damage_assault': [],
    'barrier_cleave': [],
    'barrier_counter': [],
    'barrier_assault': [],
    'dodge_counter': [],
    'dodge_assault': [],
    'attacker_killed_by_counter': []
}

# Scan candidate reports
reports_to_scan = [f for f, tags in index.items() if any(t in tags for t in ['xu_ruo', 'di_yu', 'gui_bi', 'fan_ji', 'hou_fa'])]
print(f"Scanning {len(reports_to_scan)} reports for zero/barrier/dodge/death edge cases...")

for r_name in reports_to_scan[:3500]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    attack_starts = [i for i, e in enumerate(events) if e['cfg_id'] == 9]
    for a_idx_pos, start_i in enumerate(attack_starts):
        end_i = attack_starts[a_idx_pos + 1] if a_idx_pos + 1 < len(attack_starts) else min(len(events), start_i + 35)
        for k in range(start_i + 1, end_i):
            if events[k]['cfg_id'] in [733, 723]:
                end_i = k
                break
        
        window = events[start_i:end_i]
        
        # Check normal attack hit characteristics
        is_zero_dmg = any('损失了兵力0' in ev['desc'] for ev in window if ev['cfg_id'] == 28)
        is_barrier = any('抵御' in ev['desc'] and '消失' in ev['desc'] for ev in window)
        is_dodge = any('规避' in ev['desc'] and ('成功' in ev['desc'] or '由于「规避」' in ev['desc']) for ev in window)
        
        has_cleave = any('群攻' in ev['desc'] for ev in window)
        has_counter = any(('后发制人' in ev['desc'] or '气凌三军' in ev['desc']) and '反击' in ev['desc'] for ev in window)
        has_assault = any(ev['cfg_id'] == 7 and any(sk in ev['desc'] for sk in assault_skills) for ev in window)
        
        # Zero damage
        if is_zero_dmg:
            if has_cleave:
                results['zero_damage_cleave'].append((r_name, start_i))
            if has_counter:
                results['zero_damage_counter'].append((r_name, start_i))
            if has_assault:
                results['zero_damage_assault'].append((r_name, start_i))
                
        # Barrier
        if is_barrier:
            if has_cleave:
                results['barrier_cleave'].append((r_name, start_i))
            if has_counter:
                results['barrier_counter'].append((r_name, start_i))
            if has_assault:
                results['barrier_assault'].append((r_name, start_i))
                
        # Dodge
        if is_dodge:
            if has_counter:
                results['dodge_counter'].append((r_name, start_i))
            if has_assault:
                results['dodge_assault'].append((r_name, start_i))
                
        # Attacker killed by counter
        for p, ev in enumerate(window):
            if ('后发制人' in ev['desc'] or '气凌三军' in ev['desc']) and '反击' in ev['desc']:
                # check if attacker died right after
                sub_window = window[p:p+6]
                if any(x['cfg_id'] == 163 or '无法再战' in x['desc'] for x in sub_window):
                    results['attacker_killed_by_counter'].append({
                        'report': r_name,
                        'start_idx': start_i,
                        'events': [{'idx': start_i + q, 'cfg': x['cfg_id'], 'desc': x['desc']} for q, x in enumerate(window)]
                    })

print("\n--- Edge Case Search Results ---")
for k, v in results.items():
    if k != 'attacker_killed_by_counter':
        print(f"{k:25s}: {len(v)} cases found")
    else:
        print(f"{k:25s}: {len(v)} cases found")

if results['attacker_killed_by_counter']:
    print(f"\nSample Attacker Killed by Counter:")
    s = results['attacker_killed_by_counter'][0]
    for ev in s['events']:
        print(f"  [{ev['idx']:3d}] cfg:{str(ev['cfg']):>4} | {ev['desc']}")

out_file = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r1_edge_cases.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump({
        'summary': {k: len(v) for k, v in results.items()},
        'attacker_killed_sample': results['attacker_killed_by_counter'][:3],
        'zero_damage_assault_sample': results['zero_damage_assault'][:5],
        'barrier_assault_sample': results['barrier_assault'][:5],
        'barrier_counter_sample': results['barrier_counter'][:5],
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_file)
