from pathlib import Path
import os
import json
import re

INDEX_PATH = str(Path(__file__).resolve().parent / 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

fentan_reports = [f for f, tags in index.items() if 'fen_tan' in tags]
print(f"Reports with fen_tan: {len(fentan_reports)}")

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

for r_name in fentan_reports:
    events = load_events(r_name)
    for i, e in enumerate(events):
        if '分摊' in e['desc']:
            print(f"Report: {r_name} | Event [{i:3d}] cfg:{str(e['cfg_id']):>4} | {e['desc']}")
