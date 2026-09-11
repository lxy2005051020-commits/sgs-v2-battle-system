import os
import json
import re
from collections import defaultdict

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

# Pairs to check:
# 1. Counter -> Counter (A counters B -> does B counter A?)
# 2. Counter -> Share (A counters B -> does B's teammate share Counter damage?)
# 3. Counter -> Chain (A counters B -> does B trigger Chain feedback?)
# 4. Counter -> FirstAid (A counters B -> does B trigger FirstAid?)
# 5. Counter -> Lifesteal (A counters B -> does A get lifesteal from Counter?)
# 6. Cleave -> Counter (A cleaves Sub -> does Sub counter A?)
# 7. Cleave -> Share (A cleaves Sub -> does Sub's teammate share Cleave damage?)
# 8. Cleave -> Chain (A cleaves Sub -> does Sub trigger Chain feedback?)
# 9. Cleave -> FirstAid (A cleaves Sub -> does Sub trigger FirstAid?)
# 10. Chain -> Counter (Chain hits Sub -> does Sub counter Chain source?)
# 11. Chain -> Share (Chain hits Sub -> does Sub's teammate share Chain damage?)
# 12. Chain -> Chain (Chain hits Sub -> does Sub trigger secondary Chain feedback?)
# 13. Chain -> FirstAid (Chain hits Sub -> does Sub trigger FirstAid?)
# 14. Share -> Share (Sharer takes damage -> does Sharer get shared?)
# 15. Share -> Chain (Sharer takes damage -> does Sharer trigger Chain feedback?)
# 16. Share -> FirstAid (Sharer takes damage -> does Sharer trigger FirstAid?)
# 17. Combo Hit 2 -> Cleave
# 18. Combo Hit 2 -> Counter
# 19. Combo Hit 2 -> Assault
# 20. Combo Hit 2 -> Share
# 21. Combo Hit 2 -> Chain

results = defaultdict(int)
sample_evidence = defaultdict(list)

# Scan reports
for r_name in list(index.keys())[:2500]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    for i, e in enumerate(events):
        desc = e['desc']
        cid = e['cfg_id']
        
        # Counter event: [A]由于[B]【Skill】的「反击」效果，损失了兵力
        if '「反击」效果' in desc and '损失了兵力' in desc:
            # check next 6 events for reactions to Counter
            window = events[i+1:min(len(events), i+7)]
            for ev in window:
                wdesc = ev['desc']
                if '「反击」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Counter_to_Counter'] += 1
                if '「分担」效果' in wdesc:
                    results['Counter_to_Share'] += 1
                    if len(sample_evidence['Counter_to_Share']) < 3:
                        sample_evidence['Counter_to_Share'].append((r_name, i, [x['desc'] for x in window]))
                if '「铁索连环」效果' in wdesc:
                    results['Counter_to_Chain'] += 1
                    if len(sample_evidence['Counter_to_Chain']) < 3:
                        sample_evidence['Counter_to_Chain'].append((r_name, i, [x['desc'] for x in window]))
                if '「急救」效果' in wdesc:
                    results['Counter_to_FirstAid'] += 1
                    if len(sample_evidence['Counter_to_FirstAid']) < 3:
                        sample_evidence['Counter_to_FirstAid'].append((r_name, i, [x['desc'] for x in window]))
                if ('倒戈' in wdesc or '攻心' in wdesc) and '恢复了兵力' in wdesc:
                    results['Counter_to_Lifesteal'] += 1
                    if len(sample_evidence['Counter_to_Lifesteal']) < 3:
                        sample_evidence['Counter_to_Lifesteal'].append((r_name, i, [x['desc'] for x in window]))
                        
        # Cleave event: [Sub]由于[Attacker]【Skill】的「群攻」效果，损失了兵力
        if '「群攻」效果' in desc and '损失了兵力' in desc:
            window = events[i+1:min(len(events), i+7)]
            for ev in window:
                wdesc = ev['desc']
                if '「反击」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Cleave_to_Counter'] += 1
                if '「分担」效果' in wdesc:
                    results['Cleave_to_Share'] += 1
                    if len(sample_evidence['Cleave_to_Share']) < 3:
                        sample_evidence['Cleave_to_Share'].append((r_name, i, [x['desc'] for x in window]))
                if '「铁索连环」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Cleave_to_Chain'] += 1
                    if len(sample_evidence['Cleave_to_Chain']) < 3:
                        sample_evidence['Cleave_to_Chain'].append((r_name, i, [x['desc'] for x in window]))
                if '「急救」效果' in wdesc:
                    results['Cleave_to_FirstAid'] += 1
                    if len(sample_evidence['Cleave_to_FirstAid']) < 3:
                        sample_evidence['Cleave_to_FirstAid'].append((r_name, i, [x['desc'] for x in window]))

        # Chain event: [Sub]由于[Attacker]【Skill】的「铁索连环」效果，损失了兵力
        if '「铁索连环」效果' in desc and '损失了兵力' in desc:
            window = events[i+1:min(len(events), i+7)]
            for ev in window:
                wdesc = ev['desc']
                if '「反击」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Chain_to_Counter'] += 1
                if '「分担」效果' in wdesc:
                    results['Chain_to_Share'] += 1
                if '「铁索连环」效果' in wdesc and '执行来自' in wdesc:
                    results['Chain_to_Chain'] += 1
                if '「急救」效果' in wdesc:
                    results['Chain_to_FirstAid'] += 1
                    if len(sample_evidence['Chain_to_FirstAid']) < 3:
                        sample_evidence['Chain_to_FirstAid'].append((r_name, i, [x['desc'] for x in window]))

        # Share event: [Sharer]由于[Attacker]【Skill】的「分担」效果，损失了兵力
        if '「分担」效果' in desc and '损失了兵力' in desc:
            window = events[i+1:min(len(events), i+7)]
            for ev in window:
                wdesc = ev['desc']
                if '「分担」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Share_to_Share'] += 1
                if '「铁索连环」效果' in wdesc and '损失了兵力' in wdesc:
                    results['Share_to_Chain'] += 1
                if '「急救」效果' in wdesc:
                    results['Share_to_FirstAid'] += 1
                    if len(sample_evidence['Share_to_FirstAid']) < 3:
                        sample_evidence['Share_to_FirstAid'].append((r_name, i, [x['desc'] for x in window]))

print("\n--- Cross-Family Recursion Counts ---")
for k, v in sorted(results.items()):
    print(f"{k:25s}: {v:5d}")

out_path = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r7_recursion_matrix_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'counts': dict(results),
        'samples': {k: [list(item) for item in v] for k, v in sample_evidence.items()}
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
