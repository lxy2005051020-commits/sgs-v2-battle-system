#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_battle_end_chain.py

Stage 9 Contract Closure - RF-P04 / Chain Anchor Extractor:
Investigates Chain link traversal when a commander dies during traversal:
1. Does the traversal continue to remaining linked slots?
2. Does victory (cfg 157) wait until traversal completion?

Scans the full 32,999 battle corpus in D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON.
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'BATTLE_END_CHAIN_EVIDENCE.json')

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
    try:
        with open(path, encoding='utf-8') as fp:
            data = json.load(fp)
    except:
        return []

    heroes = extract_lineup_positions(data.get('lineup', {}))
    groups = data.get('detail', {}).get('groups', [])
    res = []

    for g_idx, g in enumerate(groups):
        evs = g.get('data', {}).get('events', [])
        clean_events = []
        for e in evs:
            ev = e.get('event', {})
            cid = ev.get('cfg_id')
            if cid is None: continue
            raw = ev.get('full_desc') or ev.get('desc') or ''
            clean = re.sub(r'<[^<]+?>', '', raw)
            clean_events.append((cid, clean, raw))

        # Look for Chain triggers:
        # e.g. [xxx]执行来自【铁索连环】的「铁索连环」效果
        # or [yyy]由于[xxx]【铁索连环】的伤害，损失了兵力...
        for idx, (cid, desc, raw) in enumerate(clean_events):
            if "「铁索连环」效果" in desc or "【铁索连环】的伤害" in desc:
                # Found Chain event. Check if this is the start of a chain sequence
                chain_events = []
                commander_death_idx = None
                commander_name = None
                victory_idx = None

                # Scan local window of chain propagation
                for fwd_idx in range(idx, min(len(clean_events), idx + 20)):
                    fcid, fdesc, fraw = clean_events[fwd_idx]
                    if fcid == 723: break # next action
                    if "【铁索连环】" in fdesc or "「铁索连环」" in fdesc:
                        chain_events.append((fwd_idx, fcid, fdesc))
                    if fcid == 163 and "兵力为0" in fdesc:
                        m_d = re.search(r'\[(.*?)\]兵力为0', fdesc)
                        if m_d:
                            victim = m_d.group(1)
                            if heroes.get(victim) == 1:
                                commander_death_idx = fwd_idx
                                commander_name = victim
                    if fcid == 157:
                        victory_idx = fwd_idx
                        break

                if commander_death_idx and len(chain_events) >= 2:
                    # Check if there were chain events after commander death
                    events_after_comm_death = [c for c in chain_events if c[0] > commander_death_idx]
                    res.append({
                        'file': filename,
                        'group': g_idx,
                        'commander_name': commander_name,
                        'commander_death_idx': commander_death_idx,
                        'total_chain_events': len(chain_events),
                        'chain_events_after_commander_death': len(events_after_comm_death),
                        'after_events': [c[2] for c in events_after_comm_death],
                        'victory_idx': victory_idx,
                        'victory_after_chain_complete': (victory_idx is not None and (not events_after_comm_death or victory_idx > events_after_comm_death[-1][0]))
                    })
    return res

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Scanning {total_files} files for Chain commander death...")

    start_time = time.time()
    all_results = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        count = 0
        for fut in as_completed(futures):
            count += 1
            if count % 5000 == 0 or count == total_files:
                print(f"Scanned {count}/{total_files} files...")
            r = fut.result()
            if r:
                all_results.extend(r)

    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.2f}s. Found {len(all_results)} Chain commander death cases.")

    continuation_cases = [c for c in all_results if c['chain_events_after_commander_death'] > 0]

    stats = {
        'total_files': total_files,
        'total_chain_commander_death_cases': len(all_results),
        'chain_continued_after_commander_death': len(continuation_cases)
    }

    print("\nCHAIN FINALIZATION STATS:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    out = {
        'stats': stats,
        'continuation_cases': continuation_cases,
        'sample_cases': all_results[:20]
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f"Saved Chain evidence to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
