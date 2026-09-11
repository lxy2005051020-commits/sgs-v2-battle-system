import os
import json
import re

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
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

events = load_events('战报_2333048_pid2412307.json')
print("=== Inspecting 战报_2333048_pid2412307 around events 155-185 ===")
for i in range(155, 185):
    print(f"[{i:3d}] cfg:{str(events[i]['cfg_id']):>4} | {events[i]['desc']}")
