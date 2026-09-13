#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_cleave_state_lifecycle.py

Stage 9 Contract Closure - RF-P07 Cleave State Lifecycle Extractor (Track A)
Focuses on:
  - Apply: 「群攻」效果已施加
  - Reapply / Refresh: 「群攻」效果已刷新
  - Expire / Remove: 「群攻」效果已消失
  - Multi-source Cleave coexistence on same holder (e.g. 槊血纵横 + 瞋目横矛)
  - Multi-source execution order comparator (Skill slot order)
  - Ratio binding semantics (Permanent vs Temporary)
  - Suppression (Disarm / Silence / Stun)
  - Holder death / Source death

Outputs:
  CLEAVE_STATE_EVIDENCE.json
"""

import os
import re
import json
import time
from concurrent.futures import ProcessPoolExecutor

JSON_DIR = r"D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON"
DESKTOP_DIR = r"C:\Users\34187\Desktop\antigravity工作文件"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "CLEAVE_STATE_EVIDENCE.json")

p_apply = re.compile(r'\[(.*?)\](?:的|身上的)?「群攻」效果已施加')
p_refresh = re.compile(r'\[(.*?)\](?:的|身上的)?「群攻」效果已刷新')
p_expire = re.compile(r'\[(.*?)\](?:的|身上的)?「群攻」效果已消失')
p_skill_cast = re.compile(r'发动战法【(.*?)】')
p_cleave_exec = re.compile(r'\[(.*?)\]执行来自【(.*?)】的「群攻」效果')
p_attack = re.compile(r'对\[(.*?)\]发动普通攻击')

def scan_lifecycle_single_file(fpath):
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for ev in g.get('data', {}).get('events', []):
            raw_desc = ev.get('event', {}).get('full_desc') or ev.get('event', {}).get('desc') or ''
            clean_desc = re.sub(r'<[^>]+>', '', raw_desc).strip()
            if clean_desc:
                events.append({
                    'cfg_id': ev.get('event', {}).get('cfg_id'),
                    'desc': clean_desc
                })

    n = len(events)
    applies = []
    refreshes = []
    expires = []
    multi_source_attacks = []

    # Map skills active on actors
    for i, ev in enumerate(events):
        d = ev['desc']
        m_app = p_apply.search(d)
        if m_app:
            # find skill cast before
            skill = None
            for k in range(max(0, i-5), i):
                m_sk = p_skill_cast.search(events[k]['desc'])
                if m_sk:
                    skill = m_sk.group(1)
            applies.append({'unit': m_app.group(1), 'skill': skill, 'event_idx': i})

        m_ref = p_refresh.search(d)
        if m_ref:
            skill = None
            for k in range(max(0, i-5), i):
                m_sk = p_skill_cast.search(events[k]['desc'])
                if m_sk:
                    skill = m_sk.group(1)
            refreshes.append({'unit': m_ref.group(1), 'skill': skill, 'event_idx': i})

        m_exp = p_expire.search(d)
        if m_exp:
            expires.append({'unit': m_exp.group(1), 'event_idx': i})

        # Check multi-source cleave in a single normal attack
        m_atk = p_attack.search(d)
        if m_atk:
            cleaves_in_window = []
            for k in range(i+1, min(n, i+30)):
                if p_attack.search(events[k]['desc']) or '开始行动' in events[k]['desc']:
                    break
                m_clv = p_cleave_exec.search(events[k]['desc'])
                if m_clv:
                    cleaves_in_window.append({
                        'unit': m_clv.group(1),
                        'skill': m_clv.group(2),
                        'event_idx': k
                    })
            if len(cleaves_in_window) >= 2:
                # Distinct skills?
                skills = [c['skill'] for c in cleaves_in_window]
                if len(set(skills)) >= 2:
                    multi_source_attacks.append({
                        'attack_idx': i,
                        'cleaves': cleaves_in_window
                    })

    return {
        'file': os.path.basename(fpath),
        'applies': applies,
        'refreshes': refreshes,
        'expires': expires,
        'multi_source_attacks': multi_source_attacks
    }

def main():
    start_time = time.time()
    print("=== Stage 9 RF-P07 Track A: Cleave State Lifecycle Extractor ===")

    files = [os.path.join(JSON_DIR, f) for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    print(f"Scanning {len(files)} files...")

    all_results = []
    workers = min(12, os.cpu_count() or 4)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for res in executor.map(scan_lifecycle_single_file, files, chunksize=200):
            if res:
                if res['applies'] or res['refreshes'] or res['expires'] or res['multi_source_attacks']:
                    all_results.append(res)

    total_applies = sum(len(r['applies']) for r in all_results)
    total_refreshes = sum(len(r['refreshes']) for r in all_results)
    total_expires = sum(len(r['expires']) for r in all_results)
    total_multi_source = sum(len(r['multi_source_attacks']) for r in all_results)

    print(f"Extraction finished in {time.time() - start_time:.2f}s")
    print(f"Total Apply events:       {total_applies}")
    print(f"Total Refresh events:     {total_refreshes}")
    print(f"Total Expire events:      {total_expires}")
    print(f"Total Multi-source Cleave instances: {total_multi_source}")

    # Inspect pairwise order of multi-source cleave
    pairwise_orders = {}
    for r in all_results:
        for msa in r['multi_source_attacks']:
            skills = tuple(c['skill'] for c in msa['cleaves'])
            pairwise_orders[skills] = pairwise_orders.get(skills, 0) + 1

    print("\nPairwise Execution Order of Multi-Source Cleave:")
    for pair, count in sorted(pairwise_orders.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {' -> '.join(pair)}: {count} times")

    data_to_save = {
        'metadata': {
            'total_files_scanned': len(files),
            'total_applies': total_applies,
            'total_refreshes': total_refreshes,
            'total_expires': total_expires,
            'total_multi_source_attacks': total_multi_source
        },
        'pairwise_execution_orders': {str(k): v for k, v in pairwise_orders.items()},
        'refresh_samples': [r for r in all_results if r['refreshes']][:20],
        'multi_source_samples': [r for r in all_results if r['multi_source_attacks']][:20]
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
