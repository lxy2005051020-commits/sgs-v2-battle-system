from pathlib import Path
import os
import json
import re

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

# Check reports with yuan_hu + lian_ji
candidate_reports = [f for f, tags in index.items() if 'yuan_hu' in tags and 'lian_ji' in tags]
print(f"Scanning {len(candidate_reports)} reports with yuan_hu + lian_ji...")

combo_rescue_cases = []

for r_name in candidate_reports:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    # find turns with combo (cfg 230 连击)
    for i, e in enumerate(events):
        if e['cfg_id'] == 230 and '连击' in e['desc']:
            # look 15 before and 15 after for normal attack and 援护
            start_w = max(0, i - 15)
            end_w = min(len(events), i + 20)
            window = events[start_w:end_w]
            
            # check if 援护 occurred before combo and/or after combo
            before_combo_rescue = any(x['cfg_id'] == 143 for x in events[start_w:i])
            after_combo_rescue = any(x['cfg_id'] == 143 for x in events[i:end_w])
            
            if before_combo_rescue or after_combo_rescue:
                combo_rescue_cases.append({
                    'report': r_name,
                    'combo_idx': i,
                    'before_rescue': before_combo_rescue,
                    'after_rescue': after_combo_rescue,
                    'slice': [{'idx': start_w + p, 'cfg': x['cfg_id'], 'desc': x['desc']} for p, x in enumerate(window)]
                })

print(f"Found {len(combo_rescue_cases)} combo + rescue cases!")
b_and_a = [c for c in combo_rescue_cases if c['before_rescue'] and c['after_rescue']]
b_only = [c for c in combo_rescue_cases if c['before_rescue'] and not c['after_rescue']]
a_only = [c for c in combo_rescue_cases if not c['before_rescue'] and c['after_rescue']]
print(f"Both hit 1 & hit 2 rescued: {len(b_and_a)}")
print(f"Hit 1 rescued only: {len(b_only)}")
print(f"Hit 2 rescued only: {len(a_only)}")

out_path = str(Path(__file__).resolve().parent / 'r2_combo_rescue_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'both_count': len(b_and_a),
        'hit1_only_count': len(b_only),
        'hit2_only_count': len(a_only),
        'samples': combo_rescue_cases[:5]
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
