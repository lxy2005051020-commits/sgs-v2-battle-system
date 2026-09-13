import os
import json
import re
from collections import defaultdict

INDEX_PATH = r'stages/stage9/research/core_arbitration_v2/evidence/stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

# Reports with counter
counter_reports = [f for f, tags in index.items() if any(t in tags for t in ['fan_ji', 'hou_fa', 'qi_ling'])]
# Reports with chain
chain_reports = [f for f, tags in index.items() if 'tie_suo' in tags or 'lian_huan' in tags]
# Reports with share
share_reports = [f for f, tags in index.items() if 'fen_dan' in tags or 'lu_jiang' in tags]
# Reports with combo
combo_reports = [f for f, tags in index.items() if 'lian_ji' in tags]

print(f"Counter files: {len(counter_reports)}, Chain files: {len(chain_reports)}, Share files: {len(share_reports)}, Combo files: {len(combo_reports)}")

# 1. Counter -> Counter
# Eligible opportunity:
# Unit A attacks Unit B (normal attack).
# Unit B triggers Counter on A.
# DOES UNIT A HAVE AN ACTIVE COUNTER STATUS/SKILL (e.g. 后发制人, 气凌三军)?
# And is Unit A alive after B's counter?
# If yes, this is an ELIGIBLE OPPORTUNITY for Unit A to counter B's counter!
# Did Unit A counter B? (Check if A counters B in next 4 events)

c2c_source_events = 0
c2c_eligible = 0
c2c_triggered = 0
c2c_cases = []

for fname in counter_reports[:1500]:
    path = os.path.join(JSON_DIR, fname)
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
    except:
        continue

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc
            })

    # Track who has counter skill/status
    counter_units = set()
    for ev in events:
        desc = ev['desc']
        if any(sk in desc for sk in ['【后发制人】', '【气凌三军】', '【三里而还】']) and ('效果已施加' in desc or '发动战法' in desc or '执行来自' in desc):
            m = re.search(r'\[(.*?)\]', desc)
            if m:
                counter_units.add(m.group(1))

    # Scan for counter events:
    for i, ev in enumerate(events):
        desc = ev['desc']
        # e.g., [A]由于[B]【气凌三军】的「反击」效果，损失了兵力
        if '「反击」效果' in desc and '损失了兵力' in desc:
            c2c_source_events += 1
            m = re.search(r'\[(.*?)\]由于\[(.*?)\]', desc)
            if m:
                victim_of_counter = m.group(1) # A (the original attacker who is being countered)
                counterer = m.group(2)          # B (the counterer)

                # Did victim_of_counter have a counter skill?
                if victim_of_counter in counter_units:
                    # Is victim alive?
                    is_alive = True
                    # Check next 3 events for death
                    for next_e in events[i:min(len(events), i+4)]:
                        if f'[{victim_of_counter}]' in next_e['desc'] and ('无法再战' in next_e['desc'] or '兵力为0' in next_e['desc']):
                            is_alive = False
                            break
                    if is_alive:
                        c2c_eligible += 1
                        # Check if victim counters back
                        countered_back = False
                        for next_e in events[i+1:min(len(events), i+6)]:
                            if f'[{counterer}]由于[{victim_of_counter}]' in next_e['desc'] and '「反击」效果' in next_e['desc']:
                                countered_back = True
                                break
                        if countered_back:
                            c2c_triggered += 1
                        if len(c2c_cases) < 5:
                            c2c_cases.append({
                                'file': fname,
                                'victim': victim_of_counter,
                                'counterer': counterer,
                                'countered_back': countered_back
                            })

print(f"\nCounter -> Counter: Source events={c2c_source_events}, Eligible opportunities={c2c_eligible}, Triggered={c2c_triggered}")

# 2. Chain -> Chain
# Eligible opportunity:
# Unit A takes谋略伤害. Chain triggers, propagating to chained unit B.
# B is in Chain. Is there ANOTHER chained unit C alive?
# Chain damage is谋略伤害. If chain could trigger chain, B's hit would trigger propagation to C!
chain_source_events = 0
chain_eligible = 0
chain_triggered = 0

for fname in chain_reports[:1500]:
    path = os.path.join(JSON_DIR, fname)
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
    except:
        continue

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc
            })

    for i, ev in enumerate(events):
        desc = ev['desc']
        if '「铁索连环」效果' in desc and '损失了兵力' in desc:
            chain_source_events += 1
            # In iron chain, usually 2 or 3 units are chained.
            # If B takes chain damage, the other chained unit(s) exist.
            # Does this hit cause a secondary chain trigger?
            # Check next 4 events for '执行来自【连环计】的「铁索连环」效果'
            chain_eligible += 1
            for next_e in events[i+1:min(len(events), i+5)]:
                if '执行来自' in next_e['desc'] and '「铁索连环」效果' in next_e['desc']:
                    chain_triggered += 1
                    break

print(f"Chain -> Chain: Source events={chain_source_events}, Eligible opportunities={chain_eligible}, Triggered={chain_triggered}")

# 3. Share -> Share
# A takes damage. S1 takes share damage.
# Does S1 also have a share buff covering S1 (e.g. S2 sharing from S1)?
# In Sgs, share skills (严阵以待, 庐江上甲) specify "替友军承担X%伤害".
# Does S1 have another ally with share?
share_source_events = 0
share_eligible = 0
share_triggered = 0

for fname in share_reports[:1500]:
    path = os.path.join(JSON_DIR, fname)
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
    except:
        continue

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc
            })

    # Count how many heroes cast share
    sharers = set()
    for ev in events:
        desc = ev['desc']
        if any(sk in desc for sk in ['【严阵以待】', '【庐江上甲】']) and ('发动战法' in desc or '效果已施加' in desc):
            m = re.search(r'\[(.*?)\]', desc)
            if m:
                sharers.add(m.group(1))

    for i, ev in enumerate(events):
        desc = ev['desc']
        if '「分担」效果' in desc and '损失了兵力' in desc:
            share_source_events += 1
            # If there are >= 2 sharers on the same team, S1 could theoretically be shared by S2!
            if len(sharers) >= 2:
                share_eligible += 1
                for next_e in events[i+1:min(len(events), i+5)]:
                    if '「分担」效果' in next_e['desc'] and '损失了兵力' in next_e['desc']:
                        share_triggered += 1
                        break

print(f"Share -> Share: Source events={share_source_events}, Eligible opportunities={share_eligible}, Triggered={share_triggered}")

# 4. Combo Hit 2 -> Hit 3
combo_source_events = 0
combo_hit3_triggered = 0

for fname in combo_reports[:1500]:
    path = os.path.join(JSON_DIR, fname)
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
    except:
        continue

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc
            })

    # Find turns with combo
    i = 0
    while i < len(events):
        if events[i]['cfg_id'] == 230 and '连击' in events[i]['desc']:
            combo_source_events += 1
            # Check how many cfg 9 follow in this turn
            attacks = 0
            for j in range(i+1, min(len(events), i+40)):
                if events[j]['cfg_id'] in [723, 733]:
                    break
                if events[j]['cfg_id'] == 9:
                    attacks += 1
            if attacks >= 2: # means hit 2 + hit 3!
                combo_hit3_triggered += 1
        i += 1

print(f"Combo2 -> Combo3: Source combo events={combo_source_events}, Hit3 triggered={combo_hit3_triggered}")

out_data = {
    'c2c': {'source': c2c_source_events, 'eligible': c2c_eligible, 'triggered': c2c_triggered, 'cases': c2c_cases},
    'chain': {'source': chain_source_events, 'eligible': chain_eligible, 'triggered': chain_triggered},
    'share': {'source': share_source_events, 'eligible': share_eligible, 'triggered': share_triggered},
    'combo': {'source': combo_source_events, 'eligible': combo_source_events, 'triggered': combo_hit3_triggered}
}

with open('stages/stage9/research/core_arbitration_v2/evidence/r7_recursion_denominators.json', 'w', encoding='utf-8') as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)
print("Saved denominator data successfully.")
