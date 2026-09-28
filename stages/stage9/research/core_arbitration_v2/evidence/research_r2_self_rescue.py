from pathlib import Path
import os
import json
import re

INDEX_PATH = str(Path(__file__).resolve().parent / 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

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

# 1. Inspect 战报_2137216_pid2201610.json
r_name = '战报_2137216_pid2201610.json'
events = load_events(r_name)
print(f"=== Inspecting {r_name} around events 140-170 ===")
for i in range(max(0, 140), min(len(events), 170)):
    print(f"[{i:3d}] cfg:{str(events[i]['cfg_id']):>4} | {events[i]['desc']}")

# 2. Search for any other cases where rescuer == attacker
# In normal attack: [A]对[B]发动普通攻击 -> [B]执行来自[C]的「援护」效果 -> [A]对[C]发动普通攻击
# If A == C, attacker attacked themselves!
with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

rescue_reports = [f for f, tags in index.items() if 'yuan_hu' in tags]
print(f"\nScanning {len(rescue_reports)} rescue reports for rescuer == attacker...")

self_rescue_cases = []
pattern_att = re.compile(r'\[(.*?)\]对\[(.*?)\]发动普通攻击')
pattern_aid = re.compile(r'\[(.*?)\]执行来自\[(.*?)\]的「援护」效果')

for r_name in rescue_reports:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    for i, e in enumerate(events):
        if e['cfg_id'] == 143:
            m_aid = pattern_aid.search(e['desc'])
            if m_aid:
                target_protected, rescuer = m_aid.group(1), m_aid.group(2)
                # find previous attack event
                attacker = None
                for k in range(i-1, max(-1, i-4), -1):
                    m_att = pattern_att.search(events[k]['desc'])
                    if m_att:
                        attacker = m_att.group(1)
                        break
                if attacker and attacker == rescuer:
                    self_rescue_cases.append({
                        'report': r_name,
                        'event_idx': i,
                        'attacker': attacker,
                        'rescuer': rescuer,
                        'target': target_protected,
                        'slice': [events[j]['desc'] for j in range(max(0, i-2), min(len(events), i+4))]
                    })

print(f"Found {len(self_rescue_cases)} self-rescue cases (attacker == rescuer)!")
for c in self_rescue_cases[:5]:
    print(f"\nReport: {c['report']}, Attacker={c['attacker']}, Rescuer={c['rescuer']}, Target={c['target']}")
    for s in c['slice']:
        print(f"  {s}")

out_path = str(Path(__file__).resolve().parent / 'r2_self_rescue_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(self_rescue_cases, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
