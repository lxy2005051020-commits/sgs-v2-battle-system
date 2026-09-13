#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_battle_end_normal_attack_deep.py

Deep analysis of all Normal Attack #1 battle-ending cases across the 32,999 corpus.
Specifically examines:
1. Does Combo Checkpoint (cfg 230) execute when Commander was killed by Attack #1?
2. Does Normal Attack #2 (cfg 9) EVER execute when Commander was killed by Attack #1?
3. What is the exact sequence of events between Commander UnitDeathFact (cfg 163) and Victory (cfg 157)?
4. What is the role of Commander Collateral Troop Loss (cfg 209)?
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'BATTLE_END_COMBO_DEEP_EVIDENCE.json')

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

        current_actor = None
        attacks_in_action = 0
        for idx, (cid, desc, raw) in enumerate(clean_events):
            if cid == 723:
                m = re.search(r'\[(.*?)\]', desc)
                current_actor = m.group(1) if m else None
                attacks_in_action = 0
            elif cid == 9 and current_actor:
                m = re.search(r'\[(.*?)\]对\[(.*?)\]发动普通攻击', desc)
                if m and m.group(1) == current_actor:
                    attacks_in_action += 1
                    target = m.group(2)
                    target_pos = heroes.get(target, 0)
                    is_target_commander = (target_pos == 1)

                    if attacks_in_action == 1:
                        target_died = False
                        fwd_events = []
                        for fwd_idx in range(idx + 1, len(clean_events)):
                            fcid, fdesc, fraw = clean_events[fwd_idx]
                            if fcid == 723: break
                            if fcid == 163 and f'[{target}]' in fdesc and '兵力为0' in fdesc:
                                target_died = True
                            if target_died:
                                fwd_events.append((fcid, fdesc))
                                if fcid == 157: break

                        if target_died and any(x[0] == 157 for x in fwd_events):
                            has_230 = any(fcid == 230 for fcid, _ in fwd_events)
                            has_9 = any(fcid == 9 for fcid, _ in fwd_events)
                            has_209 = any(fcid == 209 for fcid, _ in fwd_events)
                            res.append({
                                'file': filename,
                                'group': g_idx,
                                'actor': current_actor,
                                'target': target,
                                'target_pos': target_pos,
                                'is_commander': is_target_commander,
                                'has_cfg230': has_230,
                                'has_cfg9_second': has_9,
                                'has_cfg209_collateral': has_209,
                                'events_between_death_and_victory': [f"{c}: {d}" for c, d in fwd_events]
                            })
    return res

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Scanning {total_files} files for battle-ending Normal Attack #1...")

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
    print(f"Done in {elapsed:.2f}s. Found {len(all_results)} battle-ending #1 attack cases.")

    comm_kills = [c for c in all_results if c['is_commander']]
    dep_kills = [c for c in all_results if not c['is_commander']]

    comm_with_230 = [c for c in comm_kills if c['has_cfg230']]
    comm_with_9 = [c for c in comm_kills if c['has_cfg9_second']]

    dep_with_230 = [c for c in dep_kills if c['has_cfg230']]
    dep_with_9 = [c for c in dep_kills if c['has_cfg9_second']]

    stats = {
        'total_files': total_files,
        'total_battle_ending_attack1': len(all_results),
        'commander_kills': len(comm_kills),
        'commander_kills_with_cfg230': len(comm_with_230),
        'commander_kills_with_second_attack_cfg9': len(comm_with_9),
        'deputy_kills_ending_battle': len(dep_kills),
        'deputy_kills_with_cfg230': len(dep_with_230),
        'deputy_kills_with_second_attack_cfg9': len(dep_with_9),
    }

    print("\nDEEP COMBO FINALIZATION STATS:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    out = {
        'stats': stats,
        'commander_with_230_cases': comm_with_230,
        'commander_with_9_cases': comm_with_9,
        'deputy_with_230_cases': dep_with_230[:50],
        'sample_commander_kills': comm_kills[:20]
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f"Saved deep evidence to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
