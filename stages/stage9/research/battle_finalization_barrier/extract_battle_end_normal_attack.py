#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_battle_end_normal_attack.py

Stage 9 Contract Closure - RF-P04 / CBS9-B03 Empirical Extractor:
Investigates whether Normal Attack #1 that kills the enemy commander (or last enemy)
and satisfies the victory condition EVER admits:
1. Assault skills
2. Combo Checkpoint (cfg 230)
3. Normal Attack #2 (cfg 9)

Scans the full 32,999 battle corpus in D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON.
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'BATTLE_END_COMBO_EVIDENCE.json')

COMBO_HEROES_AND_SKILLS = [
    '太史慈', '神射', '强攻', '兵锋', '乱武', '裸衣血战', '连击'
]

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
    
    # Check if combo occurred anywhere in battle for heroes
    combo_users = set()
    for g in groups:
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            cid = ev.get('cfg_id')
            raw = ev.get('full_desc') or ev.get('desc') or ''
            if cid == 230 or '获得1次额外普通攻击' in raw:
                m = re.search(r'\[(.*?)\]', raw)
                if m:
                    combo_users.add(m.group(1))

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
        
        current_actor = None
        action_normal_attacks = []
        in_action = False
        
        for idx, ev in enumerate(clean_events):
            cid = ev['cfg_id']
            desc = ev['desc']
            raw = ev['raw']
            
            if cid == 723:  # Action start
                m = re.search(r'\[(.*?)\]', desc)
                current_actor = m.group(1) if m else None
                action_normal_attacks = []
                in_action = True
            
            elif cid == 9 and in_action and current_actor:
                m = re.search(r'\[(.*?)\]对\[(.*?)\]发动普通攻击', desc)
                if m and m.group(1) == current_actor:
                    target = m.group(2)
                    attack_idx = len(action_normal_attacks) + 1
                    action_normal_attacks.append({
                        'attack_idx': attack_idx,
                        'event_idx': idx,
                        'target': target,
                        'target_pos': positions.get(target, 0)
                    })
                    
                    # Check forward window
                    lethal_victim = None
                    is_commander_death = False
                    victory_event_found = False
                    victory_event_idx = None
                    events_after_death = []
                    combo_checkpoint_found = False
                    second_attack_found = False
                    
                    for fwd_idx in range(idx + 1, len(clean_events)):
                        fev = clean_events[fwd_idx]
                        fcid = fev['cfg_id']
                        fdesc = fev['desc']
                        
                        if fcid == 723:
                            # Next action began
                            break
                        
                        if fcid == 163 and '兵力为0' in fdesc:
                            m_d = re.search(r'\[(.*?)\]兵力为0', fdesc)
                            if m_d and m_d.group(1) == target:
                                lethal_victim = target
                                if positions.get(target) == 1:
                                    is_commander_death = True
                        
                        if lethal_victim:
                            events_after_death.append((fcid, fdesc))
                            if fcid == 230:
                                combo_checkpoint_found = True
                            if fcid == 9:
                                second_attack_found = True
                            if fcid == 157:
                                victory_event_found = True
                                victory_event_idx = fwd_idx
                                break
                    
                    if lethal_victim and victory_event_found:
                        has_combo_potential = (
                            current_actor in combo_users or
                            any(k in current_actor for k in COMBO_HEROES_AND_SKILLS)
                        )
                        results.append({
                            'file': filename,
                            'group_idx': g_idx,
                            'actor': current_actor,
                            'attack_idx': attack_idx,
                            'victim': lethal_victim,
                            'victim_pos': positions.get(lethal_victim, 0),
                            'is_commander': is_commander_death,
                            'has_combo_potential': has_combo_potential,
                            'combo_checkpoint_found': combo_checkpoint_found,
                            'second_attack_found': second_attack_found,
                            'events_between_death_and_victory': [f"{cid}: {d}" for cid, d in events_after_death]
                        })
            
            elif cid == 157:  # Battle victory
                in_action = False

    return results

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Total files to scan: {total_files}")
    
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
    print(f"Done in {elapsed:.2f}s. Total battle-ending normal attack cases found: {len(all_results)}")
    
    total_cases = len(all_results)
    commander_cases = [c for c in all_results if c['is_commander']]
    first_attack_cases = [c for c in all_results if c['attack_idx'] == 1]
    first_attack_combo_potential = [c for c in first_attack_cases if c['has_combo_potential']]
    
    combo_checkpoints = [c for c in all_results if c['combo_checkpoint_found']]
    second_attacks = [c for c in all_results if c['second_attack_found']]
    
    stats = {
        'total_files_scanned': total_files,
        'total_battle_ending_normal_attacks': total_cases,
        'commander_kills': len(commander_cases),
        'first_attack_kills': len(first_attack_cases),
        'first_attack_with_combo_potential': len(first_attack_combo_potential),
        'combo_checkpoints_after_lethal_victory': len(combo_checkpoints),
        'second_attacks_after_lethal_victory': len(second_attacks),
    }
    
    print("\nSummary Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    output_data = {
        'stats': stats,
        'sample_cases': all_results[:100]
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(output_data, fp, ensure_ascii=False, indent=2)
    print(f"Saved results to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
