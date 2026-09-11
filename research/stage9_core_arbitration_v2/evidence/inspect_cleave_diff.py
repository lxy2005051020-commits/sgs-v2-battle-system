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

# Inspect the 3 diff damage reports
diff_reports = ['战报_1068512_pid1063526.json', '战报_1104444_pid1099544.json', '战报_1104450_pid1099550.json']

for r_name in diff_reports:
    events = load_events(r_name)
    print(f"\n==========================================")
    print(f"=== Report: {r_name} ===")
    print(f"==========================================")
    for i, e in enumerate(events):
        if '群攻' in e['desc'] and e['cfg_id'] == 96:
            start = max(0, i - 4)
            end = min(len(events), i + 15)
            print(f"\n--- Cleave event at index {i} ---")
            for j in range(start, end):
                mark = ">>> " if j == i else "    "
                print(f"{mark}[{j:3d}] cfg:{str(events[j]['cfg_id']):>4} | {events[j]['desc']}")
