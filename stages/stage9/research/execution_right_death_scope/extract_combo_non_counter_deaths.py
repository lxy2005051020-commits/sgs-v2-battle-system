#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_combo_non_counter_deaths.py

Research extractor for Stage 9 RF-P03:
Classifies all action-death families occurring to an attacker during their own Normal Attack action,
distinguishing COUNTER_DAMAGE from reachable non-Counter death families (REFLECT_DAMAGE,
DERIVED_REACTION_DAMAGE, PASSIVE_FEEDBACK, SELF_COST, PERIODIC_DAMAGE, COMMANDER_COLLATERAL).

Evaluates whether any dead attacker ever reaches Assault, Combo Checkpoint (cfg 230),
or Normal Attack #2 (cfg 9).
"""

import os
import sys
import json
import re
from concurrent.futures import ProcessPoolExecutor, as_completed

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUTPUT_EVIDENCE_PATH = os.path.join(
    os.path.dirname(__file__), 'EXECUTION_RIGHT_EVIDENCE.json'
)

# Counter skill indicators
COUNTER_KEYWORDS = ['反击', '气凌三军', '千里驰援', '后发制人', '益其金鼓', '绝地反击']
# Passive reaction damage keywords (e.g. 刚烈, 古之恶来)
PASSIVE_REACTION_KEYWORDS = ['刚烈', '古之恶来', '勇烈持重']


def process_battle_file(filename):
    path = os.path.join(JSON_DIR, filename)
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, encoding='utf-8') as fp:
            data = json.load(fp)
    except Exception:
        return []
    
    results = []
    groups = data.get('detail', {}).get('groups', [])
    
    for g_idx, g in enumerate(groups):
        events = []
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc,
                'raw_desc': raw_desc,
                'key': e.get('key'),
                'send_user_id': ev.get('send_user_id'),
                'target_user_id': ev.get('target_user_id'),
                'skill_id': ev.get('skill_id')
            })
        
        # Scan for action start -> normal attack -> attacker death
        current_actor = None
        current_actor_colored = None
        in_normal_attack = False
        attack_events = []
        normal_attack_ev_idx = None
        
        for idx, ev in enumerate(events):
            cid = ev['cfg_id']
            desc = ev['desc']
            raw_desc = ev['raw_desc']
            
            if cid == 723:
                m = re.search(r'\[(.*?)\]\s*行动回合', desc)
                m_raw = re.search(r'(<font color=\'[^\']+\'>\[.*?\]</font>)\s*行动回合', raw_desc)
                if m:
                    current_actor = m.group(1)
                    current_actor_colored = m_raw.group(1) if m_raw else f'[{current_actor}]'
                else:
                    current_actor = None
                    current_actor_colored = None
                in_normal_attack = False
                attack_events = []
                normal_attack_ev_idx = None
                
            elif cid == 9 and current_actor:
                m = re.search(r'\[(.*?)\]对\[(.*?)\]发动普通攻击', desc)
                if m and m.group(1) == current_actor and (current_actor_colored is None or current_actor_colored in raw_desc):
                    in_normal_attack = True
                    attack_events = [(idx, cid, desc)]
                    normal_attack_ev_idx = idx
            
            elif in_normal_attack:
                attack_events.append((idx, cid, desc))
                
                # Check for death of the current actor (ensuring matching camp/color)
                is_actor_death = False
                if cid == 163 and '兵力为0' in desc:
                    if current_actor_colored and current_actor_colored in raw_desc:
                        is_actor_death = True
                    elif not current_actor_colored and f'[{current_actor}]' in desc:
                        is_actor_death = True
                
                if is_actor_death:
                    # Attacker died during normal attack!
                    death_idx = idx
                    
                    # Analyze cause of death from recent preceding events in this group
                    death_source_family = 'OTHER'
                    death_source = 'UNKNOWN'
                    
                    for p_idx in range(max(0, idx - 6), idx):
                        p_cid = events[p_idx]['cfg_id']
                        p_desc = events[p_idx]['desc']
                        
                        # Check for Counter
                        if p_cid in [28, 213, 214] or any(k in p_desc for k in COUNTER_KEYWORDS):
                            if '反击' in p_desc or any(k in p_desc for k in COUNTER_KEYWORDS):
                                death_source_family = 'COUNTER_DAMAGE'
                                death_source = p_desc
                                break
                        # Check for Passive Reaction (e.g. 刚烈)
                        elif any(k in p_desc for k in PASSIVE_REACTION_KEYWORDS):
                            death_source_family = 'DERIVED_REACTION_DAMAGE'
                            death_source = p_desc
                            break
                        # Check for Reflect
                        elif '反弹' in p_desc or '荆棘' in p_desc:
                            death_source_family = 'REFLECT_DAMAGE'
                            death_source = p_desc
                            break
                        # Check for Periodic
                        elif any(k in p_desc for k in ['灼烧', '中毒', '溃逃', '沙暴', '水攻', '叛逃']):
                            death_source_family = 'PERIODIC_DAMAGE'
                            death_source = p_desc
                            break
                        # Check for Self-cost
                        elif '自损' in p_desc or '献祭' in p_desc:
                            death_source_family = 'SELF_COST'
                            death_source = p_desc
                            break
                    
                    if death_source_family == 'OTHER':
                        # Fallback check immediate preceding damage
                        for p_idx in range(max(0, idx - 3), idx):
                            p_desc = events[p_idx]['desc']
                            if '反击' in p_desc:
                                death_source_family = 'COUNTER_DAMAGE'
                                death_source = p_desc
                                break
                    
                    # Check subsequent events in this action until 733 or group end
                    subseq_cids = []
                    has_cfg230 = False
                    has_second_cfg9 = False
                    has_assault = False
                    action_ended_cleanly = False
                    
                    for s_idx in range(idx + 1, len(events)):
                        s_cid = events[s_idx]['cfg_id']
                        s_desc = events[s_idx]['desc']
                        s_raw = events[s_idx]['raw_desc']
                        subseq_cids.append(s_cid)
                        
                        actor_matched = (current_actor_colored in s_raw) if current_actor_colored else (f'[{current_actor}]' in s_desc)
                        
                        if s_cid == 230 and actor_matched and '连击' in s_desc:
                            has_cfg230 = True
                        if s_cid == 9 and actor_matched:
                            has_second_cfg9 = True
                        if s_cid == 7 and ('突击' in s_desc or '追击' in s_desc):
                            has_assault = True
                        if s_cid == 733:
                            action_ended_cleanly = True
                            break
                    
                    # Check if actor had combo or combo buff active prior to this action
                    had_combo_indicator = False
                    for prev_ev in events[:idx]:
                        if any(k in prev_ev['desc'] for k in ['连击', '神射', '兵锋', '锦帆百翎']):
                            had_combo_indicator = True
                            break
                    
                    results.append({
                        'battle_file': filename,
                        'group_index': g_idx,
                        'actor': current_actor,
                        'normal_attack_event_index': normal_attack_ev_idx,
                        'death_event_index': death_idx,
                        'death_source_family': death_source_family,
                        'death_source': death_source,
                        'has_cfg230_after_death': has_cfg230,
                        'has_second_cfg9_after_death': has_second_cfg9,
                        'has_assault_after_death': has_assault,
                        'action_ended_cleanly': action_ended_cleanly,
                        'had_combo_indicator': had_combo_indicator,
                        'attack_event_count': len(attack_events),
                        'subsequent_cids_until_733': subseq_cids[:10]
                    })
                    
                    # Once dead, stop tracking this normal attack
                    in_normal_attack = False
                    attack_events = []
            
            elif cid == 733:
                in_normal_attack = False
                attack_events = []
                normal_attack_ev_idx = None
    
    return results


def main():
    print(f"Scanning battle files in {JSON_DIR}...")
    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    total_files = len(files)
    print(f"Total battle files to process: {total_files}")
    
    all_results = []
    
    # Process files in parallel batches
    batch_size = 2000
    with ProcessPoolExecutor(max_workers=8) as executor:
        for i in range(0, total_files, batch_size):
            batch = files[i:i + batch_size]
            futures = [executor.submit(process_battle_file, f) for f in batch]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    all_results.extend(res)
            print(f"Processed {min(i + batch_size, total_files)} / {total_files} files... Found {len(all_results)} attacker death cases.")
    
    # Analyze family breakdown
    family_counts = {}
    cfg230_counts = {}
    cfg9_counts = {}
    assault_counts = {}
    
    for r in all_results:
        fam = r['death_source_family']
        family_counts[fam] = family_counts.get(fam, 0) + 1
        if r['has_cfg230_after_death']:
            cfg230_counts[fam] = cfg230_counts.get(fam, 0) + 1
        if r['has_second_cfg9_after_death']:
            cfg9_counts[fam] = cfg9_counts.get(fam, 0) + 1
        if r['has_assault_after_death']:
            assault_counts[fam] = assault_counts.get(fam, 0) + 1
            
    anomalies = [r for r in all_results if r['has_cfg230_after_death'] or r['has_second_cfg9_after_death'] or r['has_assault_after_death']]
    
    summary = {
        'total_scanned_files': total_files,
        'total_attacker_death_cases': len(all_results),
        'family_breakdown': family_counts,
        'cfg230_executed_after_death_by_family': cfg230_counts,
        'second_cfg9_executed_after_death_by_family': cfg9_counts,
        'assault_executed_after_death_by_family': assault_counts,
        'anomalies': anomalies,
        'samples': all_results[:100]  # Store first 100 detailed samples
    }
    
    with open(OUTPUT_EVIDENCE_PATH, 'w', encoding='utf-8') as fp:
        json.dump(summary, fp, ensure_ascii=False, indent=2)
        
    print("\n================ EXTRACTION SUMMARY ================")
    print(f"Total Attacker Deaths in Normal Attack: {len(all_results)}")
    for fam, cnt in family_counts.items():
        print(f"  Family '{fam}': {cnt} cases")
        print(f"    cfg230 after death: {cfg230_counts.get(fam, 0)}")
        print(f"    2nd normal attack (cfg 9) after death: {cfg9_counts.get(fam, 0)}")
        print(f"    Assault after death: {assault_counts.get(fam, 0)}")
    print(f"Results written to {OUTPUT_EVIDENCE_PATH}")


if __name__ == '__main__':
    main()
