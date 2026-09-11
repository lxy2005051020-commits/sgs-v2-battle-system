import os
import json
import re
import sys

# Ensure lib is accessible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

from evidence.lib.battle_parser import BattleParser
from evidence.lib.unit_identity import BattleUnitRef

INDEX_PATH = os.path.join(BASE_DIR, 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

both_files = [f for f, tags in index.items() if 'hun_luan' in tags and 'chao_feng' in tags]
print(f"BF-01 Full Candidate Files: {len(both_files)}")

parser = BattleParser(JSON_DIR)

eligible_cases = []
excluded_counts = {
    'identity_ambiguous': 0,
    'state_lifetime_ambiguous': 0,
    'taunt_source_unknown': 0,
    'action_ambiguous': 0
}

processed_reports = 0

for idx_f, fname in enumerate(both_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        continue
    processed_reports += 1

    # Check each normal attack
    for atk in pb.normal_attacks:
        # Check if attacker has both CONFUSION and TAUNT active at declare_event_idx
        has_conf = pb.state_tracker.is_state_active(atk.actor, 'CONFUSION', atk.declare_event_idx)
        taunt_st = pb.state_tracker.get_active_state(atk.actor, 'TAUNT', atk.declare_event_idx)

        if has_conf and taunt_st is not None:
            # Check exclusions
            if not taunt_st.source:
                excluded_counts['taunt_source_unknown'] += 1
                continue

            # Ensure attacker and target identities are unambiguous
            if not atk.actor or not atk.intended_target:
                excluded_counts['identity_ambiguous'] += 1
                continue

            # Check if this attack was a guard redirect duplicate (INV-05)
            if atk.is_guard_redirected and atk.guard_event_idx is not None and atk.guard_event_idx < atk.declare_event_idx:
                # Handled cleanly inside NormalAttack
                pass

            taunter = taunt_st.source
            target = atk.intended_target
            is_taunt_source = target.same_unit(taunter)

            eligible_cases.append({
                'battle_file': fname,
                'event_index': atk.declare_event_idx,
                'attacker_id': atk.actor.canonical_id,
                'attacker_name': atk.actor.display_name,
                'attacker_camp': atk.actor.camp,
                'taunt_source_id': taunter.canonical_id,
                'taunt_source_name': taunter.display_name,
                'selected_target_id': target.canonical_id,
                'selected_target_name': target.display_name,
                'selected_target_camp': target.camp,
                'target_eq_taunt': is_taunt_source
            })

print(f"\n--- BF-01 Confusion x Taunt Re-extraction Results ---")
print(f"Processed Reports: {processed_reports}")
print(f"Total Eligible Cases: {len(eligible_cases)}")
target_eq = [c for c in eligible_cases if c['target_eq_taunt']]
target_ne = [c for c in eligible_cases if not c['target_eq_taunt']]
print(f"Target == Taunt Source: {len(target_eq)} ({len(target_eq)/len(eligible_cases)*100:.2f}%)")
print(f"Target != Taunt Source: {len(target_ne)} ({len(target_ne)/len(eligible_cases)*100:.2f}%)")
print(f"Excluded counts: {excluded_counts}")

out_path = os.path.join(BASE_DIR, 'r11_confusion_taunt_data.json')
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump({
        'metadata': {
            'extractor': 'run_bf01_reextraction.py',
            'candidate_reports': len(both_files),
            'processed_reports': processed_reports,
            'eligible_cases': len(eligible_cases),
            'target_eq_taunt': len(target_eq),
            'target_ne_taunt': len(target_ne),
            'excluded_counts': excluded_counts
        },
        'cases': eligible_cases
    }, fp, ensure_ascii=False, indent=2)

print(f"Saved re-extracted data to {out_path}")
