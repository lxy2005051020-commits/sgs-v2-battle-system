from pathlib import Path
import os
import json
import re
from collections import Counter, defaultdict

INDEX_PATH = str(Path(__file__).resolve().parent / 'stage9_index.json')
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

# Scan 2000 reports for cfg 23 (conflict/rejected), cfg 24 (overwritten), cfg 25 (refreshed)
status_events = defaultdict(Counter)

sample_reports = list(index.keys())[:3000]
print(f"Scanning 3000 reports for cfg 23, 24, 25...")

for r_name in sample_reports:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    for e in events:
        cid = e['cfg_id']
        if cid in [23, 24, 25]:
            status_events[cid][e['desc'][:50]] += 1

print("\n--- Summary of Status Conflict Events ---")
for cid in [23, 24, 25]:
    total_cnt = sum(status_events[cid].values())
    print(f"cfg_id {cid} total occurrences: {total_cnt}")
    for desc, cnt in status_events[cid].most_common(10):
        print(f"   [{cnt:4d}] {desc}")

out_path = str(Path(__file__).resolve().parent / 'r9_status_conflict_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'cfg_23': status_events[23].most_common(30),
        'cfg_24': status_events[24].most_common(30),
        'cfg_25': status_events[25].most_common(30),
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
