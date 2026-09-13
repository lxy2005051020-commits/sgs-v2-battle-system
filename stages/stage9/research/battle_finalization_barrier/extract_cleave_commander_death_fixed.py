#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_cleave_commander_death_fixed.py

Searches all 32,999 battle files for:
1. Commander is a secondary target in Cleave.
2. Commander REACHES 0 TROOPS (cfg 163 / loss reduces currentTroops to 0).
3. Evaluates:
   - Does the remaining secondary target (deputy) in the same Cleave effect still execute?
   - Does a second Cleave source (e.g. 瞋目横矛 following 槊血纵横) execute?
   - Does collateral damage (cfg 209) execute?
   - When does victory (cfg 157) occur?
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'CLEAVE_COMMANDER_DEATH_EVIDENCE.json')

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

def check_file(f):
    path = os.path.join(JSON_DIR, f)
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
        clean = []
        for e in evs:
            ev = e.get('event', {})
            cid = ev.get('cfg_id')
            if cid is None: continue
            raw = ev.get('full_desc') or ev.get('desc') or ''
            c = re.sub(r'<[^<]+?>', '', raw)
            clean.append((cid, c))

        for idx, (cid, desc) in enumerate(clean):
            if '「群攻」效果' in desc and '损失了兵力' in desc:
                m = re.search(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「群攻」效果，损失了兵力(\d+)（(\d+)）', desc)
                if m:
                    target = m.group(1)
                    actor = m.group(2)
                    skill = m.group(3)
                    loss = int(m.group(4))
                    rem = int(m.group(5))
                    pos = heroes.get(target, 0)
                    if rem == 0 and pos == 1:
                        # Commander reached 0 troops from Cleave!
                        # Check subsequent events up to next action
                        fwd = []
                        remaining_cleave = []
                        for fwd_idx in range(idx + 1, min(len(clean), idx + 25)):
                            fcid, fdesc = clean[fwd_idx]
                            if fcid == 723: break # next action
                            fwd.append((fcid, fdesc))
                            if '「群攻」效果' in fdesc and '损失了兵力' in fdesc:
                                remaining_cleave.append((fcid, fdesc))
                            if fcid == 157: break

                        res.append({
                            'file': f,
                            'group': g_idx,
                            'actor': actor,
                            'commander': target,
                            'skill': skill,
                            'loss': loss,
                            'events_after_death': fwd,
                            'remaining_cleave_hits': remaining_cleave,
                            'remaining_cleave_count': len(remaining_cleave),
                            'has_victory_157': any(x[0] == 157 for x in fwd),
                            'has_collateral_209': any(x[0] == 209 for x in fwd)
                        })
    return res

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    print(f"Scanning {len(files)} files for Cleave killing commander...")

    start_time = time.time()
    hits = []
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {executor.submit(check_file, f): f for f in files}
        count = 0
        for fut in as_completed(futures):
            count += 1
            if count % 5000 == 0 or count == len(files):
                print(f"Scanned {count}/{len(files)} files...")
            r = fut.result()
            if r:
                hits.extend(r)

    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.2f}s. Total lethal Cleave commander cases: {len(hits)}")

    has_remaining = [h for h in hits if h['remaining_cleave_count'] > 0]
    print(f"Cases where subsequent Cleave hit occurred after commander death: {len(has_remaining)}")

    stats = {
        'total_files': len(files),
        'total_lethal_cleave_commander_cases': len(hits),
        'cases_with_subsequent_cleave_hits': len(has_remaining)
    }

    out = {
        'stats': stats,
        'cases': hits
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f"Saved results to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
