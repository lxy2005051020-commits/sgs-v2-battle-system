#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_cleave_secondary_order.py

Stage 9 Contract Closure - RF-P07 Cleave Secondary Target Extractor (Track B)
Focuses on:
  - Exact Lineup Position mapping (pos 1 = Commander, pos 2 = Deputy 1, pos 3 = Deputy 2)
  - Secondary candidate pool: actualTarget exclusion, same-side alive teammates
  - Guard redirection: originalTarget eligibility as secondary target
  - Secondary ordering comparator across permutations:
      actualTarget pos 1 -> order of [2, 3]
      actualTarget pos 2 -> order of [1, 3]
      actualTarget pos 3 -> order of [1, 2]
  - JIT liveness revalidation: dead teammates skipped, count = alive count (up to 2)
  - Multi-source queue composition: EFFECT_MAJOR_ORDER vs TARGET_MAJOR_ORDER

Outputs:
  CLEAVE_TARGET_ORDER_EVIDENCE.json
"""

import os
import re
import json
import time
from concurrent.futures import ProcessPoolExecutor

JSON_DIR = r"D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "CLEAVE_TARGET_ORDER_EVIDENCE.json")

pattern_attack = re.compile(r'对\[(.*?)\]发动普通攻击')
pattern_guard = re.compile(r'\[(.*?)\]执行来自\[(.*?)\]的「援护」效果')
pattern_cleave_exec = re.compile(r'\[(.*?)\]执行来自【(.*?)】的「群攻」效果')
pattern_cleave_loss = re.compile(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「群攻」效果，损失了兵力(\d+)（(\d+)）')

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

def scan_order_single_file(fpath):
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None

    lineup = data.get('lineup')
    hero_pos = extract_lineup_positions(lineup) if lineup else {}
    if not hero_pos:
        return None

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for ev in g.get('data', {}).get('events', []):
            raw_desc = ev.get('event', {}).get('full_desc') or ev.get('event', {}).get('desc') or ''
            clean_desc = re.sub(r'<[^>]+>', '', raw_desc).strip()
            if clean_desc:
                events.append({
                    'desc': clean_desc,
                    'key': ev.get('key')
                })

    n = len(events)
    sequences = []
    guard_cases = []

    i = 0
    while i < n:
        m_atk = pattern_attack.search(events[i]['desc'])
        if not m_atk:
            i += 1
            continue

        original_target = m_atk.group(1)
        actual_target = original_target
        is_guarded = False
        guarder = None

        # Check if immediately guarded
        if i + 1 < n:
            m_gd = pattern_guard.search(events[i+1]['desc'])
            if m_gd and m_gd.group(1) == original_target:
                is_guarded = True
                guarder = m_gd.group(2)
                # Next attack event is on guarder
                if i + 2 < n:
                    m_atk2 = pattern_attack.search(events[i+2]['desc'])
                    if m_atk2:
                        actual_target = m_atk2.group(1)

        # Look for Cleave in action window
        cleaves_found = []
        k = i + 1
        while k < min(n, i + 35):
            desc = events[k]['desc']
            if pattern_attack.search(desc) and k > i + 2:
                break
            if '开始行动' in desc:
                break

            m_clv = pattern_cleave_exec.search(desc)
            if m_clv:
                clv_unit = m_clv.group(1)
                clv_skill = m_clv.group(2)
                sec_hits = []
                for j in range(k + 1, min(n, k + 15)):
                    d_sec = events[j]['desc']
                    if pattern_attack.search(d_sec) or '开始行动' in d_sec:
                        break
                    m_loss = pattern_cleave_loss.search(d_sec)
                    if m_loss and m_loss.group(3) == clv_skill:
                        tgt = m_loss.group(1)
                        sec_hits.append({
                            'target': tgt,
                            'pos': hero_pos.get(tgt),
                            'loss': int(m_loss.group(4)),
                            'rem': int(m_loss.group(5)),
                            'event_idx': j
                        })
                cleaves_found.append({
                    'unit': clv_unit,
                    'skill': clv_skill,
                    'event_idx': k,
                    'sec_hits': sec_hits
                })
            k += 1

        if cleaves_found:
            for clv in cleaves_found:
                hits = clv['sec_hits']
                if not hits:
                    continue
                hit_pos_list = [h['pos'] for h in hits if h['pos'] is not None]
                hit_names = [h['target'] for h in hits]

                # Check if actualTarget was excluded
                actual_target_excluded = (actual_target not in hit_names)

                # Check guard redirect case: originalTarget was hit by cleave?
                original_target_hit = (is_guarded and original_target in hit_names)
                if is_guarded:
                    guard_cases.append({
                        'file': os.path.basename(fpath),
                        'original_target': original_target,
                        'guarder': actual_target,
                        'original_target_hit_by_cleave': original_target_hit,
                        'secondary_hits': hit_names
                    })

                sequences.append({
                    'file': os.path.basename(fpath),
                    'actual_target': actual_target,
                    'actual_target_pos': hero_pos.get(actual_target),
                    'is_guarded': is_guarded,
                    'original_target': original_target,
                    'cleave_skill': clv['skill'],
                    'secondary_hits': hits,
                    'secondary_pos_list': hit_pos_list,
                    'actual_target_excluded': actual_target_excluded
                })

        i = k

    return {
        'file': os.path.basename(fpath),
        'sequences': sequences,
        'guard_cases': guard_cases
    }

def main():
    start_time = time.time()
    print("=== Stage 9 RF-P07 Track B: Cleave Secondary Target Extractor ===")

    files = [os.path.join(JSON_DIR, f) for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    print(f"Scanning {len(files)} files...")

    all_sequences = []
    all_guard_cases = []
    workers = min(12, os.cpu_count() or 4)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(scan_order_single_file, files, chunksize=200):
            if res:
                all_sequences.extend(res['sequences'])
                all_guard_cases.extend(res['guard_cases'])

    print(f"Extraction finished in {time.time() - start_time:.2f}s")
    print(f"Total Cleave attack sequences with pos extracted: {len(all_sequences)}")
    print(f"Total Guard redirect cases with Cleave: {len(all_guard_cases)}")

    # Analyze Ordering by actualTarget pos
    pos_order_stats = {
        1: {},  # actualTarget is pos 1 -> what are secondary pos orders?
        2: {},  # actualTarget is pos 2 -> what are secondary pos orders?
        3: {}   # actualTarget is pos 3 -> what are secondary pos orders?
    }

    actual_target_excluded_count = 0
    actual_target_included_count = 0

    for seq in all_sequences:
        at_pos = seq['actual_target_pos']
        pos_list = tuple(seq['secondary_pos_list'])
        if seq['actual_target_excluded']:
            actual_target_excluded_count += 1
        else:
            actual_target_included_count += 1

        if at_pos in pos_order_stats:
            pos_order_stats[at_pos][pos_list] = pos_order_stats[at_pos].get(pos_list, 0) + 1

    print("\n--- Secondary Target Ordering by Actual Target Position ---")
    for at_pos, orders in sorted(pos_order_stats.items()):
        print(f"\nActualTarget is POS {at_pos}:")
        for ord_tuple, cnt in sorted(orders.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  Secondary Order {ord_tuple}: {cnt} occurrences")

    # Guard cases analysis
    guard_orig_hit_count = sum(1 for gc in all_guard_cases if gc['original_target_hit_by_cleave'])
    print(f"\nGuard Cases Analysis:")
    print(f"  Total Guard cases: {len(all_guard_cases)}")
    print(f"  Original Target hit by Cleave as secondary: {guard_orig_hit_count} / {len(all_guard_cases)}")

    data_to_save = {
        'metadata': {
            'total_files_scanned': len(files),
            'total_sequences': len(all_sequences),
            'total_guard_cases': len(all_guard_cases),
            'actual_target_excluded_count': actual_target_excluded_count,
            'actual_target_included_count': actual_target_included_count,
            'guard_original_hit_count': guard_orig_hit_count
        },
        'pos_order_stats': {str(k): {str(p): c for p, c in v.items()} for k, v in pos_order_stats.items()},
        'guard_samples': all_guard_cases[:30],
        'sample_sequences': all_sequences[:50]
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    print(f"Saved evidence to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
