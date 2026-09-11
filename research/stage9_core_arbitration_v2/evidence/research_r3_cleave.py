import os
import json
import re

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

cleave_reports = [f for f, tags in index.items() if 'qun_gong' in tags or 'chen_mu' in tags]
print(f"Total reports with cleave: {len(cleave_reports)}")

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

# In a cleave event:
# [Attacker]执行来自【Skill】的「群攻」效果
# followed by:
# [Target1]由于[Attacker]【Skill】的「群攻」效果，损失了兵力 D1 (R1)
# [Target2]由于[Attacker]【Skill】的「群攻」效果，损失了兵力 D2 (R2)

pattern_cleave_hit = re.compile(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「群攻」效果，损失了兵力(\d+)（(\d+)）')
pattern_main_hit = re.compile(r'\[(.*?)\]损失了兵力(\d+)（(\d+)）')

cleave_events_data = []

for r_name in cleave_reports[:2000]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    for i, e in enumerate(events):
        if e['cfg_id'] == 96 and '群攻' in e['desc']:
            # Find the main normal attack damage before this
            main_target, main_damage = None, None
            for k in range(i-1, max(-1, i-6), -1):
                if events[k]['cfg_id'] == 28:
                    m = pattern_main_hit.search(events[k]['desc'])
                    if m:
                        main_target = m.group(1)
                        main_damage = int(m.group(2))
                        break
            
            # Find all sub-target cleave damage in the next 10 events
            sub_hits = []
            for k in range(i+1, min(len(events), i+12)):
                if '群攻' in events[k]['desc'] and '损失了兵力' in events[k]['desc']:
                    m = pattern_cleave_hit.search(events[k]['desc'])
                    if m:
                        sub_hits.append({
                            'target': m.group(1),
                            'damage': int(m.group(4)),
                            'remaining': int(m.group(5)),
                            'event_idx': k
                        })
                elif events[k]['cfg_id'] in [9, 733, 723]:
                    break
            
            if len(sub_hits) >= 2:
                cleave_events_data.append({
                    'report': r_name,
                    'event_idx': i,
                    'skill_desc': e['desc'],
                    'main_target': main_target,
                    'main_damage': main_damage,
                    'sub_hits': sub_hits,
                    'same_damage': sub_hits[0]['damage'] == sub_hits[1]['damage']
                })

print(f"Total analyzed cleave instances with 2+ sub-targets: {len(cleave_events_data)}")
same_cnt = sum(1 for c in cleave_events_data if c['same_damage'])
diff_cnt = sum(1 for c in cleave_events_data if not c['same_damage'])
print(f"Sub-targets took EXACT SAME damage: {same_cnt} ({same_cnt/len(cleave_events_data)*100:.1f}%)" if cleave_events_data else "0")
print(f"Sub-targets took DIFFERENT damage : {diff_cnt} ({diff_cnt/len(cleave_events_data)*100:.1f}%)" if cleave_events_data else "0")

# Print samples of same damage and diff damage
print("\n--- Samples of SAME damage ---")
for c in [x for x in cleave_events_data if x['same_damage']][:5]:
    print(f"Report: {c['report']} Main=[{c['main_target']}: {c['main_damage']}] -> Sub1=[{c['sub_hits'][0]['target']}: {c['sub_hits'][0]['damage']}], Sub2=[{c['sub_hits'][1]['target']}: {c['sub_hits'][1]['damage']}]")

print("\n--- Samples of DIFFERENT damage ---")
for c in [x for x in cleave_events_data if not x['same_damage']][:5]:
    print(f"Report: {c['report']} Main=[{c['main_target']}: {c['main_damage']}] -> Sub1=[{c['sub_hits'][0]['target']}: {c['sub_hits'][0]['damage']}], Sub2=[{c['sub_hits'][1]['target']}: {c['sub_hits'][1]['damage']}]")

out_path = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r3_cleave_damage_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(cleave_events_data),
        'same_cnt': same_cnt,
        'diff_cnt': diff_cnt,
        'same_samples': [x for x in cleave_events_data if x['same_damage']][:10],
        'diff_samples': [x for x in cleave_events_data if not x['same_damage']][:10]
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
