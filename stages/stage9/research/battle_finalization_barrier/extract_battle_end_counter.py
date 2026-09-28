#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_battle_end_counter.py

Stage 9 Contract Closure - RF-P04 / CTS9-H02 Empirical Extractor:
Investigates CounterAttack behavior when the original attacker (especially Commander)
is killed by Counter #1 (C1), and Counter #2 (C2) was already admitted into the CounterBatch.

Scans the full 32,999 battle corpus in D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON.
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'BATTLE_END_COUNTER_EVIDENCE.json')

COUNTER_SKILL_KEYWORDS = ['反击', '气凌三军', '千里驰援', '后发制人', '益其金鼓', '绝地反击']

def extract_lineup_positions(lineup):
    heroes = {}
    def walk(obj):
        if isinstance(obj, dict):
            if 'entries' in obj and isinstance(obj['entries'], list):
                d_entry = {e.get('key'): e.get('value') for e in obj['entries'] if isinstance(e, dict)}
                if 'pos' in d_entry and ('hero_name' in d_entry or 'name' in d_entry or 'hero_type' in d_entry):
                    name = d_entry.get('hero_name') or d_entry.get('name')
                    pos = d_entry.get('pos')
                    if name and pos in (1, 2, 3):
                        heroes[name] = int(pos)
                for e in obj['entries']:
                    walk(e)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(lineup)
    return heroes

def process_file(filename):
    path = os.path.join(JSON_DIR, filename)
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, encoding='utf-8') as fp:
            data = json.load(fp)
    except Exception:
        return []

    lineup = data.get('lineup', {})
    positions = extract_lineup_positions(lineup)

    groups = data.get('detail', {}).get('groups', [])
    if not groups:
        return []

    results = []

    for g_idx, g in enumerate(groups):
        events = g.get('data', {}).get('events', [])
        clean_events = []
        for e in events:
            ev = e.get('event', {})
            cid = ev.get('cfg_id')
            if cid is None:
                continue
            raw = ev.get('full_desc') or ev.get('desc') or ''
            clean = re.sub(r'<[^<]+?>', '', raw)
            clean_events.append({
                'cfg_id': cid,
                'desc': clean,
                'raw': raw,
                'args': ev.get('args', [])
            })

        # Scan for NormalAttack
        current_actor = None
        for idx, ev in enumerate(clean_events):
            cid = ev['cfg_id']
            desc = ev['desc']
            raw = ev['raw']

            if cid == 723:
                m = re.search(r'\[(.*?)\]', desc)
                current_actor = m.group(1) if m else None

            elif cid == 9 and current_actor:
                m = re.search(r'\[(.*?)\]对\[(.*?)\]发动普通攻击', desc)
                if not m or m.group(1) != current_actor:
                    continue
                actor_pos = positions.get(current_actor, 0)
                is_actor_commander = (actor_pos == 1)

                # Collect downstream counter events
                counter_events = []
                actor_died = False
                actor_death_idx = None
                victory_event_found = False

                for fwd_idx in range(idx + 1, len(clean_events)):
                    fev = clean_events[fwd_idx]
                    fcid = fev['cfg_id']
                    fdesc = fev['desc']

                    if fcid == 723:
                        break

                    # Check Counter execute
                    # e.g. [典韦]执行来自【古之恶来】的「反击」效果
                    # or [夏侯惇]执行来自【刚烈】的「反击」效果
                    is_counter = False
                    if "「反击」效果" in fdesc or any(k in fdesc for k in COUNTER_SKILL_KEYWORDS):
                        if "执行来自" in fdesc or "损失了兵力" in fdesc:
                            is_counter = True

                    if is_counter:
                        counter_events.append((fwd_idx, fcid, fdesc))

                    # Check actor death
                    if fcid == 163 and f"[{current_actor}]" in fdesc and "兵力为0" in fdesc:
                        actor_died = True
                        actor_death_idx = fwd_idx

                    if fcid == 157:
                        victory_event_found = True
                        break

                if actor_died and len(counter_events) >= 2:
                    # Counter killed actor with multiple counters
                    c_before_death = [c for c in counter_events if c[0] < actor_death_idx]
                    c_after_death = [c for c in counter_events if c[0] > actor_death_idx]
                    if c_before_death and c_after_death:
                        results.append({
                            'file': filename,
                            'group_idx': g_idx,
                            'actor': current_actor,
                            'actor_pos': actor_pos,
                            'is_actor_commander': is_actor_commander,
                            'actor_death_idx': actor_death_idx,
                            'counters_before_death': [c[2] for c in c_before_death],
                            'counters_after_death': [c[2] for c in c_after_death],
                            'victory_found': victory_event_found
                        })

    return results

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Total files to scan for Counter: {total_files}")
    
    start_time = time.time()
    all_results = []
    
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        count = 0
        for fut in as_completed(futures):
            count += 1
            if count % 5000 == 0 or count == total_files:
                print(f"Scanned {count}/{total_files} files (found {len(all_results)} cases)...")
            res = fut.result()
            if res:
                all_results.extend(res)
    
    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.2f}s. Total counter sibling cases: {len(all_results)}")
    
    commander_cases = [c for c in all_results if c['is_actor_commander']]
    
    stats = {
        'total_files_scanned': total_files,
        'total_sibling_counter_cases': len(all_results),
        'commander_attacker_cases': len(commander_cases)
    }
    
    print("\nCounter Summary Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    output_data = {
        'stats': stats,
        'cases': all_results
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(output_data, fp, ensure_ascii=False, indent=2)
    print(f"Saved results to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
