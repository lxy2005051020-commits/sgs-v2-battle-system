from pathlib import Path
import os
import json
import re

INDEX_PATH = str(Path(__file__).resolve().parent / 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

chain_reports = [f for f, tags in index.items() if 'tie_suo' in tags or 'lian_huan' in tags]
print(f"Total reports with chain: {len(chain_reports)}")

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

# In an Iron Chain event:
# [MainTarget]执行来自【连环计】的「铁索连环」效果
# followed by:
# [Target1]由于[Attacker]【连环计】的「铁索连环」效果，损失了兵力 D1 (R1)
# [Target2]由于[Attacker]【连环计】的「铁索连环」效果，损失了兵力 D2 (R2)

pattern_chain_hit = re.compile(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「铁索连环」效果，损失了兵力(\d+)（(\d+)）')
pattern_any_dmg = re.compile(r'损失了兵力(\d+)（(\d+)）')

chain_data = []

for r_name in chain_reports[:1500]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    for i, e in enumerate(events):
        if e['cfg_id'] == 96 and '铁索连环' in e['desc'] and '执行来自' in e['desc']:
            # previous damage
            prev_dmg, prev_target = None, None
            for k in range(i-1, max(-1, i-5), -1):
                if '损失了兵力' in events[k]['desc']:
                    m = pattern_any_dmg.search(events[k]['desc'])
                    if m:
                        prev_dmg = int(m.group(1))
                        prev_target = events[k]['desc'].split(']')[0].replace('[', '')
                        break
            
            sub_hits = []
            for k in range(i+1, min(len(events), i+10)):
                if '铁索连环' in events[k]['desc'] and '损失了兵力' in events[k]['desc']:
                    m = pattern_chain_hit.search(events[k]['desc'])
                    if m:
                        sub_hits.append({
                            'target': m.group(1),
                            'damage': int(m.group(4)),
                            'remaining': int(m.group(5)),
                            'event_idx': k
                        })
                elif events[k]['cfg_id'] in [723, 733, 9, 7]:
                    break
            
            if len(sub_hits) >= 2:
                chain_data.append({
                    'report': r_name,
                    'event_idx': i,
                    'prev_target': prev_target,
                    'prev_damage': prev_dmg,
                    'sub_hits': sub_hits,
                    'same_damage': sub_hits[0]['damage'] == sub_hits[1]['damage'],
                    'ratio1': sub_hits[0]['damage'] / prev_dmg if prev_dmg else 0,
                    'ratio2': sub_hits[1]['damage'] / prev_dmg if prev_dmg else 0
                })

print(f"Total analyzed multi-target chain events: {len(chain_data)}")
same_cnt = sum(1 for c in chain_data if c['same_damage'])
diff_cnt = sum(1 for c in chain_data if not c['same_damage'])
print(f"Chain sub-targets took EXACT SAME damage: {same_cnt} ({same_cnt/len(chain_data)*100:.1f}%)" if chain_data else "0")
print(f"Chain sub-targets took DIFFERENT damage : {diff_cnt} ({diff_cnt/len(chain_data)*100:.1f}%)" if chain_data else "0")

print("\n--- Samples of DIFFERENT damage in Chain ---")
for c in [x for x in chain_data if not x['same_damage']][:5]:
    print(f"Report: {c['report']} Prev=[{c['prev_target']}: {c['prev_damage']}] -> Sub1=[{c['sub_hits'][0]['target']}: {c['sub_hits'][0]['damage']}], Sub2=[{c['sub_hits'][1]['target']}: {c['sub_hits'][1]['damage']}]")

out_path = str(Path(__file__).resolve().parent / 'r4_chain_damage_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(chain_data),
        'same_cnt': same_cnt,
        'diff_cnt': diff_cnt,
        'samples_diff': [x for x in chain_data if not x['same_damage']][:10],
        'samples_same': [x for x in chain_data if x['same_damage']][:10]
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
