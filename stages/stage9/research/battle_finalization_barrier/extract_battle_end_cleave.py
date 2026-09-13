#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_battle_end_cleave.py

Stage 9 Contract Closure - RF-P04 / CLVS9-B04 Empirical Extractor:
Investigates Cleave behavior across unit death and battle finalization:
- Case A: Main target dies from main Normal Attack hit. Does Cleave execute on secondary targets?
- Case B: Attacker dies during Cleave downstream reaction. Does Cleave continue?
- Case C: Secondary target dies (re-verifying RF-P07: completed, JIT validates next).
- Case D: Secondary commander dies from Cleave. Do remaining planned secondaries execute? Do remaining Cleave sources execute?
- Case E: Chain / downstream reaction triggered by Cleave kills commander. Does Chain finish, and does remaining Cleave execute?

Scans the full 32,999 battle corpus in D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON.
"""

import os
import sys
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'BATTLE_END_CLEAVE_EVIDENCE.json')

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

        # Scan for NormalAttack triggering Cleave
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
                main_target = m.group(2)
                main_target_pos = positions.get(main_target, 0)

                # Look forward inside this NormalAttack resolution window
                # Collect main hit loss, cleave events, death events, chain events, victory events
                main_hit_loss = 0
                main_target_died = False
                cleave_events = [] # list of (idx, skill, target, loss, is_commander)
                attacker_died = False
                commander_died = False
                commander_death_source = None
                victory_event_found = False
                events_window = []

                for fwd_idx in range(idx + 1, len(clean_events)):
                    fev = clean_events[fwd_idx]
                    fcid = fev['cfg_id']
                    fdesc = fev['desc']

                    # Window ends at next action start or battle end
                    if fcid == 723:
                        break

                    events_window.append((fwd_idx, fcid, fdesc))

                    # Check main target damage
                    if fcid == 145 and f"[{main_target}]" in fdesc and "普通攻击" in fdesc:
                        m_l = re.search(r'损失了兵力(\d+)', fdesc)
                        if m_l:
                            main_hit_loss = int(m_l.group(1))

                    # Check main target death
                    if fcid == 163 and f"[{main_target}]" in fdesc and "兵力为0" in fdesc:
                        main_target_died = True
                        if main_target_pos == 1:
                            commander_died = True
                            commander_death_source = "MAIN_ATTACK"

                    # Check Cleave events:
                    # e.g. [马超]执行来自【槊血纵横】的「群攻」效果
                    # or [目标]由于[马超]【槊血纵横】的「群攻」效果，损失了兵力...
                    if "「群攻」效果" in fdesc:
                        m_clv = re.search(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「群攻」效果，损失了兵力(\d+)', fdesc)
                        if m_clv:
                            sec_target = m_clv.group(1)
                            clv_skill = m_clv.group(3)
                            clv_loss = int(m_clv.group(4))
                            sec_pos = positions.get(sec_target, 0)
                            cleave_events.append({
                                'idx': fwd_idx,
                                'skill': clv_skill,
                                'target': sec_target,
                                'target_pos': sec_pos,
                                'loss': clv_loss,
                                'is_commander': (sec_pos == 1)
                            })

                    # Check secondary death
                    if fcid == 163 and "兵力为0" in fdesc:
                        m_d = re.search(r'\[(.*?)\]兵力为0', fdesc)
                        if m_d:
                            dead_hero = m_d.group(1)
                            dead_pos = positions.get(dead_hero, 0)
                            if dead_hero == current_actor:
                                attacker_died = True
                            elif dead_pos == 1:
                                commander_died = True
                                if not commander_death_source:
                                    if cleave_events and cleave_events[-1]['target'] == dead_hero:
                                        commander_death_source = "CLEAVE_SECONDARY"
                                    elif "铁索连环" in fdesc or (fwd_idx > 0 and "铁索连环" in clean_events[fwd_idx-1]['desc']):
                                        commander_death_source = "CLEAVE_CHAIN"
                                    else:
                                        commander_death_source = "OTHER_DOWNSTREAM"

                    if fcid == 157:
                        victory_event_found = True
                        # If victory event reached, that closes the battle
                        break

                # Now evaluate the specific cases:
                # Case A: main target died from main attack, AND actor had Cleave active (or performed Cleave)
                if main_target_died and len(cleave_events) > 0:
                    results.append({
                        'case': 'CASE_A_MAIN_TARGET_LETHAL_CLEAVE_EXECUTES',
                        'file': filename,
                        'group_idx': g_idx,
                        'actor': current_actor,
                        'main_target': main_target,
                        'main_target_pos': main_target_pos,
                        'main_target_died': main_target_died,
                        'cleave_count': len(cleave_events),
                        'cleave_events': cleave_events,
                        'victory_found': victory_event_found
                    })

                # Case B: attacker died during Cleave downstream
                if attacker_died and len(cleave_events) > 0:
                    results.append({
                        'case': 'CASE_B_ATTACKER_DIES_DURING_CLEAVE',
                        'file': filename,
                        'group_idx': g_idx,
                        'actor': current_actor,
                        'cleave_events': cleave_events,
                        'victory_found': victory_event_found
                    })

                # Case D: Secondary commander dies from Cleave
                sec_commander_kills = [c for c in cleave_events if c['is_commander']]
                if sec_commander_kills:
                    # Check if there were subsequent events in the cleave sequence
                    first_comm_kill_idx = sec_commander_kills[0]['idx']
                    subsequent_cleave = [c for c in cleave_events if c['idx'] > first_comm_kill_idx]
                    results.append({
                        'case': 'CASE_D_SECONDARY_COMMANDER_DIES_FROM_CLEAVE',
                        'file': filename,
                        'group_idx': g_idx,
                        'actor': current_actor,
                        'cleave_events': cleave_events,
                        'commander_kill': sec_commander_kills[0],
                        'subsequent_cleave_count': len(subsequent_cleave),
                        'subsequent_cleave': subsequent_cleave,
                        'victory_found': victory_event_found
                    })

                # Case E: Cleave downstream reaction (e.g. Chain) kills commander
                if commander_death_source == "CLEAVE_CHAIN":
                    results.append({
                        'case': 'CASE_E_CLEAVE_CHAIN_KILLS_COMMANDER',
                        'file': filename,
                        'group_idx': g_idx,
                        'actor': current_actor,
                        'cleave_events': cleave_events,
                        'victory_found': victory_event_found
                    })

    return results

def main():
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Total files to scan for Cleave: {total_files}")
    
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
    print(f"Done in {elapsed:.2f}s. Total cleave death cases: {len(all_results)}")
    
    cases_a = [c for c in all_results if c['case'] == 'CASE_A_MAIN_TARGET_LETHAL_CLEAVE_EXECUTES']
    cases_b = [c for c in all_results if c['case'] == 'CASE_B_ATTACKER_DIES_DURING_CLEAVE']
    cases_d = [c for c in all_results if c['case'] == 'CASE_D_SECONDARY_COMMANDER_DIES_FROM_CLEAVE']
    cases_e = [c for c in all_results if c['case'] == 'CASE_E_CLEAVE_CHAIN_KILLS_COMMANDER']
    
    stats = {
        'total_files_scanned': total_files,
        'total_cases': len(all_results),
        'case_a_main_target_lethal_cleave_executes': len(cases_a),
        'case_b_attacker_dies_during_cleave': len(cases_b),
        'case_d_secondary_commander_dies_from_cleave': len(cases_d),
        'case_e_cleave_chain_kills_commander': len(cases_e),
    }
    
    print("\nCleave Summary Statistics:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    output_data = {
        'stats': stats,
        'cases_a_sample': cases_a[:50],
        'cases_b': cases_b,
        'cases_d': cases_d,
        'cases_e': cases_e
    }
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as fp:
        json.dump(output_data, fp, ensure_ascii=False, indent=2)
    print(f"Saved results to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
