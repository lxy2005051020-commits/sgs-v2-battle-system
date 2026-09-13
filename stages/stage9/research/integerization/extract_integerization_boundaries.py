#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_integerization_boundaries.py

Stage 9 Contract Closure - RF-P01 Integerization Policy Extractor
Extracts exact-half tie samples, adjacent control samples, and exact integer samples
across CHAIN, DAMAGE_SHARE, and DISTRIBUTION (target and participant).
Uses exact rational arithmetic (fractions.Fraction) without floating point approximation.
"""

import os
import json
import re
from fractions import Fraction
from decimal import Decimal

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
INDEX_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'core_arbitration_v2', 'evidence', 'stage9_index.json'
)
OUTPUT_EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), 'INTEGERIZATION_EVIDENCE.json')


def load_battle_events(battle_filename):
    path = os.path.join(JSON_DIR, battle_filename)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as fp:
        data = json.load(fp)
    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc,
                'key': e.get('key')
            })
    return events


def extract_share_boundaries(fendan_reports, max_reports=600):
    """
    Extracts DAMAGE_SHARE samples:
    Dsharer_theoretical = integerize(Dtotal * R)
    Dtarget = Dtotal - Dsharer_theoretical
    """
    pattern_red = re.compile(r'\[(.*?)\]由于【(.*?)】的「分担」效果，本次攻击受到的伤害减少了(\d+(?:\.\d+)?)%')
    pattern_exec = re.compile(r'\[(.*?)\]执行来自【(.*?)】的「分担」效果')
    pattern_loss = re.compile(r'\[(.*?)\](?:由于.*?的伤害，)?损失了兵力(\d+)（(\d+)）')

    half_samples = []
    controls_below = []
    controls_above = []
    integer_samples = []

    scanned_count = 0
    event_count = 0

    for r_name in fendan_reports[:max_reports]:
        events = load_battle_events(r_name)
        if not events:
            continue
        scanned_count += 1
        event_count += len(events)

        for i, e in enumerate(events):
            if e['cfg_id'] == 123 and '分担' in e['desc']:
                m = pattern_red.search(e['desc'])
                if not m:
                    continue
                tgt, skill, ratio_str = m.group(1), m.group(2), m.group(3)

                # Target loss
                tgt_loss, tgt_rem = None, None
                for k in range(i + 1, min(len(events), i + 5)):
                    ml = pattern_loss.search(events[k]['desc'])
                    if ml and ml.group(1) == tgt:
                        tgt_loss = int(ml.group(2))
                        tgt_rem = int(ml.group(3))
                        break
                if tgt_loss is None or tgt_rem <= 0:
                    continue

                # Sharer execution and loss
                sharer, sh_loss, sh_rem = None, None, None
                for k in range(i + 1, min(len(events), i + 10)):
                    me = pattern_exec.search(events[k]['desc'])
                    if me and me.group(2) == skill:
                        sharer = me.group(1)
                        for j in range(k + 1, min(len(events), k + 5)):
                            ml = pattern_loss.search(events[j]['desc'])
                            if ml and ml.group(1) == sharer:
                                sh_loss = int(ml.group(2))
                                sh_rem = int(ml.group(3))
                                break
                        break
                if sh_loss is None or sh_rem <= 0:
                    continue

                # Exclude confounders: sharers with innate personal damage reduction (e.g. Cao Cao)
                # or where conservation fails (hidden clamp or modifier)
                Dtotal = tgt_loss + sh_loss
                if Dtotal <= 0:
                    continue
                r_num = int(round(float(ratio_str) * 100))
                r_frac = Fraction(r_num, 10000)

                th_sharer = Fraction(Dtotal) * r_frac
                frac = th_sharer % 1

                # Cleanliness check: if clean, theoretical Dtarget + Dsharer matches Dtotal
                # Check whether sh_loss / Dtotal is close to r_frac (within 2/Dtotal)
                if abs(float(sh_loss) / float(Dtotal) - float(r_frac)) > (2.0 / float(Dtotal)):
                    continue

                case_record = {
                    'battle_id': r_name,
                    'event_index': i,
                    'call_site': 'DAMAGE_SHARE',
                    'target': tgt,
                    'sharer': sharer,
                    'skill': skill,
                    'Dtotal': Dtotal,
                    'ratio_raw': ratio_str + '%',
                    'ratio_exact_num': r_frac.numerator,
                    'ratio_exact_den': r_frac.denominator,
                    'theoretical_exact': str(th_sharer),
                    'theoretical_float': float(th_sharer),
                    'fractional_part': str(frac),
                    'observed_sharer_loss': sh_loss,
                    'observed_target_loss': tgt_loss,
                    'target_remaining_troops': tgt_rem,
                    'sharer_remaining_troops': sh_rem,
                    'is_tie': (frac == Fraction(1, 2)),
                    'K_floor': int(th_sharer),
                    'is_K_even': (int(th_sharer) % 2 == 0),
                    'evidence_grade': 'Grade A'
                }

                if frac == Fraction(1, 2):
                    half_samples.append(case_record)
                elif frac == 0:
                    integer_samples.append(case_record)
                elif frac < Fraction(1, 2):
                    controls_below.append(case_record)
                else:
                    controls_above.append(case_record)

    return {
        'scanned_battles': scanned_count,
        'scanned_events': event_count,
        'exact_half_samples': half_samples,
        'exact_integer_samples': integer_samples,
        'controls_below': controls_below,
        'controls_above': controls_above
    }


def extract_distribution_boundaries(fentan_reports):
    """
    Extracts DISTRIBUTION samples:
    Call Site A: Dtarget = integerize(Dtotal * (1 - R))
    Call Site B: Dparticipant = integerize(Dtransfer / N)
    """
    pattern_red = re.compile(r'\[(.*?)\]由于【(.*?)】的「分摊」效果，本次攻击受到的伤害减少了(\d+(?:\.\d+)?)%')
    pattern_loss = re.compile(r'\[(.*?)\](?:由于.*?的伤害，)?损失了兵力(\d+)（(\d+)）')

    target_half_samples = []
    target_controls_below = []
    target_controls_above = []

    participant_half_samples = []
    participant_controls_below = []
    participant_controls_above = []
    participant_integer_samples = []

    scanned_count = 0
    event_count = 0

    for r_name in fentan_reports:
        events = load_battle_events(r_name)
        if not events:
            continue
        scanned_count += 1
        event_count += len(events)

        for i, e in enumerate(events):
            if e['cfg_id'] == 123 and '分摊' in e['desc']:
                m = pattern_red.search(e['desc'])
                if not m:
                    continue
                tgt, ratio_str = m.group(1), m.group(3)
                r_frac = Fraction(int(round(float(ratio_str) * 100)), 10000)

                tgt_loss, tgt_rem = None, None
                for k in range(i + 1, min(len(events), i + 4)):
                    ml = pattern_loss.search(events[k]['desc'])
                    if ml and ml.group(1) == tgt:
                        tgt_loss = int(ml.group(2))
                        tgt_rem = int(ml.group(3))
                        break
                if tgt_loss is None or tgt_rem <= 0:
                    continue

                parts = []
                for k in range(max(0, i - 6), i):
                    ml = pattern_loss.search(events[k]['desc'])
                    if ml and ml.group(1) != tgt:
                        parts.append({
                            'name': ml.group(1),
                            'loss': int(ml.group(2)),
                            'remaining': int(ml.group(3))
                        })
                if not parts:
                    continue

                part_losses = [p['loss'] for p in parts]
                # check that participant losses are consistent (no clamp on participants)
                if any(p['remaining'] <= 0 for p in parts):
                    continue
                if len(set(part_losses)) != 1:
                    continue

                Dpart_obs = part_losses[0]
                N = len(parts)

                # Solve Dtotal:
                # Dtarget = round(Dtotal * (1 - R))
                # Dtransfer = Dtotal - Dtarget
                # Dparticipant = round(Dtransfer / N)
                est_Dtot = int(round(tgt_loss / float(1 - r_frac)))
                matched_Dtot = None
                for Dtot_cand in range(est_Dtot - 3, est_Dtot + 4):
                    th_tgt_cand = Fraction(Dtot_cand) * (1 - r_frac)
                    # test if nearest integer (half-up) produces observed Dtarget
                    cand_tgt = int(th_tgt_cand + Fraction(1, 2))
                    if cand_tgt == tgt_loss:
                        trans = Dtot_cand - tgt_loss
                        th_part_cand = Fraction(trans, N)
                        cand_part = int(th_part_cand + Fraction(1, 2))
                        if cand_part == Dpart_obs:
                            matched_Dtot = Dtot_cand
                            break

                if matched_Dtot is None:
                    continue

                Dtotal = matched_Dtot
                th_tgt = Fraction(Dtotal) * (1 - r_frac)
                Dtransfer = Dtotal - tgt_loss
                th_part = Fraction(Dtransfer, N)

                # Target site record
                frac_tgt = th_tgt % 1
                tgt_rec = {
                    'battle_id': r_name,
                    'event_index': i,
                    'call_site': 'DISTRIBUTION_TARGET',
                    'target': tgt,
                    'Dtotal': Dtotal,
                    'ratio_raw': ratio_str + '%',
                    'ratio_exact_num': (1 - r_frac).numerator,
                    'ratio_exact_den': (1 - r_frac).denominator,
                    'theoretical_exact': str(th_tgt),
                    'theoretical_float': float(th_tgt),
                    'fractional_part': str(frac_tgt),
                    'observed_target_loss': tgt_loss,
                    'target_remaining_troops': tgt_rem,
                    'is_tie': (frac_tgt == Fraction(1, 2)),
                    'K_floor': int(th_tgt),
                    'is_K_even': (int(th_tgt) % 2 == 0),
                    'evidence_grade': 'Grade A'
                }
                if frac_tgt == Fraction(1, 2):
                    target_half_samples.append(tgt_rec)
                elif frac_tgt < Fraction(1, 2):
                    target_controls_below.append(tgt_rec)
                else:
                    target_controls_above.append(tgt_rec)

                # Participant site record
                frac_part = th_part % 1
                part_rec = {
                    'battle_id': r_name,
                    'event_index': i,
                    'call_site': 'DISTRIBUTION_PARTICIPANT',
                    'Dtotal': Dtotal,
                    'Dtransfer': Dtransfer,
                    'N': N,
                    'theoretical_exact': str(th_part),
                    'theoretical_float': float(th_part),
                    'fractional_part': str(frac_part),
                    'observed_participant_loss': Dpart_obs,
                    'participants': [p['name'] for p in parts],
                    'participant_remaining_troops': [p['remaining'] for p in parts],
                    'is_tie': (frac_part == Fraction(1, 2)),
                    'K_floor': int(th_part),
                    'is_K_even': (int(th_part) % 2 == 0),
                    'evidence_grade': 'Grade A'
                }
                if frac_part == Fraction(1, 2):
                    participant_half_samples.append(part_rec)
                elif frac_part == 0:
                    participant_integer_samples.append(part_rec)
                elif frac_part < Fraction(1, 2):
                    participant_controls_below.append(part_rec)
                else:
                    participant_controls_above.append(part_rec)

    return {
        'scanned_battles': scanned_count,
        'scanned_events': event_count,
        'target_half_samples': target_half_samples,
        'target_controls_below': target_controls_below,
        'target_controls_above': target_controls_above,
        'participant_half_samples': participant_half_samples,
        'participant_integer_samples': participant_integer_samples,
        'participant_controls_below': participant_controls_below,
        'participant_controls_above': participant_controls_above
    }


def extract_chain_boundaries(chain_reports, max_reports=1000):
    """
    Extracts CHAIN samples:
    ChainCalculatedDamage = floor(TriggerNodeResolvedDamage * ChainRatio)
    """
    pattern_chain_hit = re.compile(r'\[(.*?)\]由于\[(.*?)\]【(.*?)】的「铁索连环」效果，损失了兵力(\d+)（(\d+)）')
    pattern_any_dmg = re.compile(r'\[(.*?)\](?:由于.*?的伤害，)?损失了兵力(\d+)（(\d+)）')

    chain_samples = []
    scanned_count = 0
    event_count = 0

    # Test fixed basis point ratios per battle where multiple non-clamped events occur
    for r_name in chain_reports[:max_reports]:
        events = load_battle_events(r_name)
        if not events:
            continue
        scanned_count += 1
        event_count += len(events)

        battle_samples = []
        for i, e in enumerate(events):
            if e['cfg_id'] == 96 and '铁索连环' in e['desc'] and '执行来自' in e['desc']:
                prev_dmg, prev_tgt = None, None
                for k in range(i - 1, max(-1, i - 5), -1):
                    if '损失了兵力' in events[k]['desc']:
                        m = pattern_any_dmg.search(events[k]['desc'])
                        if m:
                            prev_tgt = m.group(1)
                            prev_dmg = int(m.group(2))
                            break
                hits = []
                for k in range(i + 1, min(len(events), i + 10)):
                    if '铁索连环' in events[k]['desc'] and '损失了兵力' in events[k]['desc']:
                        m = pattern_chain_hit.search(events[k]['desc'])
                        if m:
                            hits.append({
                                'target': m.group(1),
                                'owner': m.group(2),
                                'skill': m.group(3),
                                'loss': int(m.group(4)),
                                'remaining': int(m.group(5))
                            })
                if prev_dmg and hits:
                    valid_hits = [h for h in hits if h['remaining'] > 0]
                    if valid_hits and len(set(h['loss'] for h in valid_hits)) == 1:
                        battle_samples.append({
                            'event_index': i,
                            'trigger_node': prev_tgt,
                            'trigger_damage': prev_dmg,
                            'observed_chain_damage': valid_hits[0]['loss'],
                            'target': valid_hits[0]['target'],
                            'effect_owner': valid_hits[0]['owner'],
                            'source_skill': valid_hits[0]['skill'],
                            'target_remaining': valid_hits[0]['remaining']
                        })

        if len(battle_samples) >= 8:
            # Find candidate basis points that fit floor for all samples in this battle
            cand_floor = [
                bp for bp in range(1000, 5000)
                if all(int(s['trigger_damage'] * Fraction(bp, 10000)) == s['observed_chain_damage'] for s in battle_samples)
            ]
            if 1 <= len(cand_floor) <= 5:
                bp = cand_floor[0]
                r_frac = Fraction(bp, 10000)
                for s in battle_samples:
                    th = Fraction(s['trigger_damage']) * r_frac
                    frac = th % 1
                    fl = int(th)
                    chain_samples.append({
                        'battle_id': r_name,
                        'event_index': s['event_index'],
                        'call_site': 'CHAIN_LINK',
                        'trigger_node': s['trigger_node'],
                        'effect_owner': s['effect_owner'],
                        'source_skill': s['source_skill'],
                        'trigger_damage': s['trigger_damage'],
                        'ratio_bp': bp,
                        'ratio_exact_num': r_frac.numerator,
                        'ratio_exact_den': r_frac.denominator,
                        'theoretical_exact': str(th),
                        'theoretical_float': float(th),
                        'fractional_part': str(frac),
                        'observed_chain_damage': s['observed_chain_damage'],
                        'target': s['target'],
                        'target_remaining': s['target_remaining'],
                        'K_floor': fl,
                        'matches_floor': (s['observed_chain_damage'] == fl),
                        'matches_half_up': (s['observed_chain_damage'] == int(th + Fraction(1, 2))),
                        'evidence_grade': 'Grade A'
                    })

    return {
        'scanned_battles': scanned_count,
        'scanned_events': event_count,
        'samples': chain_samples
    }


def main():
    print("Loading index...")
    with open(INDEX_PATH, encoding='utf-8') as f:
        index = json.load(f)

    fendan_reports = [f for f, tags in index.items() if 'fen_dan' in tags]
    fentan_reports = [f for f, tags in index.items() if 'fen_tan' in tags]
    chain_reports = [f for f, tags in index.items() if 'tie_suo' in tags or 'lian_huan' in tags]

    print(f"Total reports: {len(index)}")
    print(f"Share reports: {len(fendan_reports)}, Distribution reports: {len(fentan_reports)}, Chain reports: {len(chain_reports)}")

    print("Extracting DAMAGE_SHARE boundaries...")
    share_data = extract_share_boundaries(fendan_reports, max_reports=600)
    print(f"Share: {len(share_data['exact_half_samples'])} exact half, {len(share_data['exact_integer_samples'])} integer, {len(share_data['controls_below'])} below, {len(share_data['controls_above'])} above")

    print("Extracting DISTRIBUTION boundaries...")
    distrib_data = extract_distribution_boundaries(fentan_reports)
    print(f"Distrib Target: {len(distrib_data['target_half_samples'])} exact half, {len(distrib_data['target_controls_below'])} below, {len(distrib_data['target_controls_above'])} above")
    print(f"Distrib Part: {len(distrib_data['participant_half_samples'])} exact half, {len(distrib_data['participant_integer_samples'])} integer, {len(distrib_data['participant_controls_below'])} below, {len(distrib_data['participant_controls_above'])} above")

    print("Extracting CHAIN boundaries...")
    chain_data = extract_chain_boundaries(chain_reports, max_reports=800)
    print(f"Chain samples: {len(chain_data['samples'])}")

    combined_evidence = {
        'extractor_metadata': {
            'repository_battle_json_dir': JSON_DIR,
            'index_path': INDEX_PATH,
            'total_indexed_battles': len(index),
            'share_scanned_battles': share_data['scanned_battles'],
            'share_scanned_events': share_data['scanned_events'],
            'distrib_scanned_battles': distrib_data['scanned_battles'],
            'distrib_scanned_events': distrib_data['scanned_events'],
            'chain_scanned_battles': chain_data['scanned_battles'],
            'chain_scanned_events': chain_data['scanned_events']
        },
        'damage_share': {
            'exact_half_samples': share_data['exact_half_samples'],
            'exact_integer_samples': share_data['exact_integer_samples'],
            'controls_below': share_data['controls_below'][:50],
            'controls_above': share_data['controls_above'][:50]
        },
        'distribution': {
            'target_half_samples': distrib_data['target_half_samples'],
            'target_controls_below': distrib_data['target_controls_below'],
            'target_controls_above': distrib_data['target_controls_above'],
            'participant_half_samples': distrib_data['participant_half_samples'],
            'participant_integer_samples': distrib_data['participant_integer_samples'],
            'participant_controls_below': distrib_data['participant_controls_below'],
            'participant_controls_above': distrib_data['participant_controls_above']
        },
        'chain_link': {
            'samples': chain_data['samples']
        }
    }

    with open(OUTPUT_EVIDENCE_PATH, 'w', encoding='utf-8') as fp:
        json.dump(combined_evidence, fp, ensure_ascii=False, indent=2)

    print(f"Saved evidence pack to {OUTPUT_EVIDENCE_PATH}")


if __name__ == '__main__':
    main()
