import os
import json
import re

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

# Check the Counter_to_Counter matches:
# True recursion: A counters B -> B counters A.
# Non-recursion: A counters B with Skill 1 -> A counters B with Skill 2.
pattern_cnt = re.compile(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「反击」效果，损失了兵力')

true_counter_recursion = []
multi_counter_same_actor = []

for r_name in list(index.keys())[:2500]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    for i, e in enumerate(events):
        m1 = pattern_cnt.search(e['desc'])
        if m1:
            victim1, attacker1, skill1 = m1.group(1), m1.group(2), m1.group(3)
            # check next events
            for k in range(i+1, min(len(events), i+8)):
                m2 = pattern_cnt.search(events[k]['desc'])
                if m2:
                    victim2, attacker2, skill2 = m2.group(1), m2.group(2), m2.group(3)
                    # Check who attacked whom:
                    if attacker2 == victim1 and victim2 == attacker1:
                        # B countered A back!
                        true_counter_recursion.append((r_name, i, k, e['desc'], events[k]['desc']))
                    elif attacker2 == attacker1:
                        # Same attacker countered again with another skill!
                        multi_counter_same_actor.append((r_name, i, k, e['desc'], events[k]['desc']))

print(f"True Counter Recursion (B counters A back): {len(true_counter_recursion)}")
print(f"Multi Counter by same actor (Skill 1 + Skill 2): {len(multi_counter_same_actor)}")

if true_counter_recursion:
    print("\n--- True Counter Recursion cases ---")
    for c in true_counter_recursion:
        print(c)

if multi_counter_same_actor:
    print("\n--- Multi Counter samples ---")
    for c in multi_counter_same_actor[:5]:
        print(f"Report: {c[0]} \n  Hit 1: {c[3]}\n  Hit 2: {c[4]}")

# Now check Chain_to_Chain:
# True recursion: Chain feedback damage to Target B causes Target B to trigger Chain feedback to Target C!
# Non-recursion: Main damage to A triggers Chain feedback to B, and THEN triggers Chain feedback to C!
pattern_chain_exec = re.compile(r'\[(.*?)\]执行来自【(.*?)】的「铁索连环」效果')
chain_recursion = []
chain_broadcast = []

for r_name in list(index.keys())[:1500]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    for i, e in enumerate(events):
        m1 = pattern_chain_exec.search(e['desc'])
        if m1:
            src1 = m1.group(1)
            # look in next 10 events if any other unit executes chain
            for k in range(i+1, min(len(events), i+12)):
                if events[k]['cfg_id'] in [9, 723, 733]:
                    break
                m2 = pattern_chain_exec.search(events[k]['desc'])
                if m2 and k != i:
                    src2 = m2.group(1)
                    chain_recursion.append((r_name, i, k, e['desc'], events[k]['desc']))

print(f"\nChain Exec -> Another Chain Exec in same window: {len(chain_recursion)}")
if chain_recursion:
    print("Sample Chain Execs:")
    for c in chain_recursion[:3]:
        print(f"Report: {c[0]} @ {c[1]},{c[2]}: \n  1: {c[3]}\n  2: {c[4]}")
