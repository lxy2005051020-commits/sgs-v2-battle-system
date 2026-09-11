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

events = load_events('战报_1068460_pid1063452.json')
for i, e in enumerate(events):
    if '铁索连环' in e['desc'] and '损失了兵力243' in e['desc']:
        start = max(0, i - 5)
        end = min(len(events), i + 10)
        print(f"=== Chain diff in 1068460 around {i} ===")
        for j in range(start, end):
            print(f"[{j:3d}] cfg:{str(events[j]['cfg_id']):>4} | {events[j]['desc']}")
        break
