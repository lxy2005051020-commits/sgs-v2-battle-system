import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

from evidence.lib.battle_parser import BattleParser

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
DATA_PATH = os.path.join(BASE_DIR, 'r10_combo_detailed_stratified.json')

if not os.path.exists(DATA_PATH):
    print("r10_combo_detailed_stratified.json not yet generated. Waiting...")
    sys.exit(0)

with open(DATA_PATH, 'r', encoding='utf-8') as fp:
    data = json.load(fp)

spot_candidates = data.get('spot_check_candidates', {})
parser = BattleParser(JSON_DIR)

spot_check_results = []
mismatch_count = 0
total_checked = 0

print(f"=== Running Dual Verification Spot Checks across Categories ===")

for cat_name, cases in spot_candidates.items():
    print(f"\nCategory [{cat_name}]: Checking {len(cases)} cases...")
    for c in cases:
        total_checked += 1
        fname = c['file']
        pb = parser.parse_file(fname)
        if not pb.is_valid:
            mismatch_count += 1
            spot_check_results.append({
                'category': cat_name,
                'file': fname,
                'result': 'FAIL',
                'notes': 'Battle report invalid'
            })
            continue

        # Find combo pair
        target_cp = None
        for cp in pb.combo_pairs:
            if cp.checkpoint_idx == c['checkpoint']:
                target_cp = cp
                break

        if not target_cp:
            mismatch_count += 1
            spot_check_results.append({
                'category': cat_name,
                'file': fname,
                'result': 'FAIL',
                'notes': f"Checkpoint {c['checkpoint']} not found"
            })
            continue

        # Raw event validation
        events = pb.raw_events
        ev_hit1 = events[target_cp.hit1.declare_event_idx] if target_cp.hit1.declare_event_idx < len(events) else None
        ev_hit2 = events[target_cp.hit2.declare_event_idx] if target_cp.hit2.declare_event_idx < len(events) else None

        desc1 = ev_hit1['clean_desc'] if ev_hit1 else ""
        desc2 = ev_hit2['clean_desc'] if ev_hit2 else ""

        # Validate actors & targets in raw text
        actor_name = target_cp.actor.display_name
        tgt1_name = target_cp.hit1.intended_target.display_name
        tgt2_name = target_cp.hit2.intended_target.display_name

        check_actor = (f"[{actor_name}]" in desc1 and f"[{actor_name}]" in desc2)
        check_tgt1 = f"[{tgt1_name}]" in desc1
        check_tgt2 = f"[{tgt2_name}]" in desc2

        # Validate category condition
        cond_valid = True
        if cat_name == 'cand_1':
            cond_valid = (target_cp.candidate_count == 1 and target_cp.condition == 'NORMAL')
        elif cat_name == 'cand_2':
            cond_valid = (target_cp.candidate_count == 2 and target_cp.condition == 'NORMAL')
        elif cat_name == 'cand_3':
            cond_valid = (target_cp.candidate_count == 3 and target_cp.condition == 'NORMAL')
        elif cat_name == 'confusion':
            cond_valid = (target_cp.condition == 'CONFUSION')
        elif cat_name == 'taunt':
            cond_valid = (target_cp.condition == 'TAUNT')

        is_match = check_actor and check_tgt1 and check_tgt2 and cond_valid
        if not is_match:
            mismatch_count += 1

        spot_check_results.append({
            'category': cat_name,
            'file': fname,
            'actor': target_cp.actor.canonical_id,
            'tgt1': target_cp.hit1.intended_target.canonical_id,
            'tgt2': target_cp.hit2.intended_target.canonical_id,
            'candidate_count': target_cp.candidate_count,
            'condition': target_cp.condition,
            'same_target': target_cp.same_target,
            'checkpoint_idx': target_cp.checkpoint_idx,
            'hit1_event_idx': target_cp.hit1.declare_event_idx,
            'hit2_event_idx': target_cp.hit2.declare_event_idx,
            'raw_desc_hit1': desc1,
            'raw_desc_hit2': desc2,
            'verification': {
                'actor_match': check_actor,
                'tgt1_match': check_tgt1,
                'tgt2_match': check_tgt2,
                'condition_match': cond_valid
            },
            'result': 'PASS' if is_match else 'FAIL'
        })

print(f"\n==========================================")
print(f"Total Cases Checked: {total_checked}")
print(f"Mismatches: {mismatch_count}")
error_rate = mismatch_count / total_checked if total_checked > 0 else 0.0
print(f"Error Rate: {error_rate*100:.2f}%")
print(f"Verdict: {'PASS' if error_rate <= 0.02 else 'FAIL'}")
print(f"==========================================")

out_path = os.path.join(BASE_DIR, 'r10_combo_spot_check_report.json')
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump({
        'total_checked': total_checked,
        'mismatches': mismatch_count,
        'error_rate': error_rate,
        'verdict': 'PASS' if error_rate <= 0.02 else 'FAIL',
        'details': spot_check_results
    }, fp, ensure_ascii=False, indent=2)

print(f"Saved spot check report to {out_path}")
