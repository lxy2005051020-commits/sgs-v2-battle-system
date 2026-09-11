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

candidate_reports = [f for f, tags in index.items() if any(t in tags for t in ['fan_ji', 'hou_fa', 'qi_ling'])]

counter_after_assault_cases = []

for r_name in candidate_reports[:3000]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    attack_starts = [i for i, e in enumerate(events) if e['cfg_id'] == 9]
    for a_idx_pos, start_i in enumerate(attack_starts):
        end_i = attack_starts[a_idx_pos + 1] if a_idx_pos + 1 < len(attack_starts) else min(len(events), start_i + 30)
        for k in range(start_i + 1, end_i):
            if events[k]['cfg_id'] in [733, 723]:
                end_i = k
                break
        
        window = events[start_i:end_i]
        counter_indices = [start_i + p for p, ev in enumerate(window) if '反击' in ev['desc']]
        assault_indices = [start_i + p for p, ev in enumerate(window) if ev['cfg_id'] == 7 and any(sk in ev['desc'] for sk in assault_skills)]
        
        if counter_indices and assault_indices:
            cnt_first = min(counter_indices)
            a_first = min(assault_indices)
            if a_first < cnt_first:
                counter_after_assault_cases.append({
                    'report': r_name,
                    'start_idx': start_i,
                    'cnt_first': cnt_first,
                    'a_first': a_first,
                    'window': [{'idx': start_i + p, 'cfg': ev['cfg_id'], 'desc': ev['desc']} for p, ev in enumerate(window)]
                })

print(f"Found {len(counter_after_assault_cases)} cases where Assault occurred before Counter:")
for c in counter_after_assault_cases:
    print(f"\n=== Report: {c['report']} (Assault @ {c['a_first']}, Counter @ {c['cnt_first']}) ===")
    for ev in c['window']:
        mark = ">>> " if ev['idx'] in [c['a_first'], c['cnt_first']] else "    "
        print(f"{mark}[{ev['idx']:3d}] cfg:{str(ev['cfg']):>4} | {ev['desc']}")
