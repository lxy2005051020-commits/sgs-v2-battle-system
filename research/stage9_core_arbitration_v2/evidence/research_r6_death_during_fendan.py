import os
import json
import re

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

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

# Find reports with both fen_dan and si_wang
candidate_reports = [f for f, tags in index.items() if 'fen_dan' in tags and 'si_wang' in tags]
print(f"Scanning {len(candidate_reports)} reports with fen_dan + si_wang...")

death_near_fendan = []

for r_name in candidate_reports[:1000]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    for i, e in enumerate(events):
        if e['cfg_id'] == 163 and '兵力为0，无法再战' in e['desc']:
            # look 10 before
            sub_w = events[max(0, i-10):i+1]
            if any('分担' in x['desc'] for x in sub_w):
                death_near_fendan.append({
                    'report': r_name,
                    'death_idx': i,
                    'events': [{'idx': max(0, i-10) + p, 'cfg': x['cfg_id'], 'desc': x['desc']} for p, x in enumerate(sub_w)]
                })

print(f"Found {len(death_near_fendan)} deaths near fen_dan!")
if death_near_fendan:
    for c in death_near_fendan[:5]:
        print(f"\n=== Report: {c['report']} at death event {c['death_idx']} ===")
        for ev in c['events']:
            print(f"  [{ev['idx']:3d}] cfg:{str(ev['cfg']):>4} | {ev['desc']}")

out_path = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r6_death_near_fendan.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(death_near_fendan[:20], f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
