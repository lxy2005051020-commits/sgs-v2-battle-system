import os
import json
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

from evidence.lib.battle_parser import BattleParser
from evidence.lib.evidence_utils import compute_binomial_ci, verify_combo_invariants

INDEX_PATH = os.path.join(BASE_DIR, 'stage9_index.json')
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

combo_files = [f for f, tags in index.items() if 'lian_ji' in tags]
print(f"BF-05 Full Candidate Files: {len(combo_files)}")

parser = BattleParser(JSON_DIR)

all_combos = []
processed_reports = 0
excluded_counts = {
    'parse_error': 0,
    'candidate_pool_unknown': 0
}

# Group: (candidate_count, condition, target1_status, pool_changed) -> list of bool(same_target)
strata = defaultdict(list)
spot_check_candidates = defaultdict(list)

for idx_f, fname in enumerate(combo_files):
    pb = parser.parse_file(fname)
    if not pb.is_valid:
        excluded_counts['parse_error'] += 1
        continue
    processed_reports += 1

    for c in pb.combo_pairs:
        all_combos.append(c)

        if c.candidate_count is None:
            excluded_counts['candidate_pool_unknown'] += 1
            cand_str = "UNKNOWN"
        else:
            cand_str = str(c.candidate_count)

        key = (
            cand_str,
            c.condition,
            c.target1_status,
            "POOL_CHANGED" if c.pool_changed else "POOL_STABLE"
        )
        strata[key].append(c.same_target)

        # Collect spot check candidates
        if c.condition == 'NORMAL' and c.target1_status == 'SURVIVED' and not c.pool_changed:
            if c.candidate_count in [1, 2, 3] and len(spot_check_candidates[f"cand_{c.candidate_count}"]) < 20:
                spot_check_candidates[f"cand_{c.candidate_count}"].append({
                    'file': fname,
                    'actor': c.actor.canonical_id,
                    'tgt1': c.hit1.intended_target.canonical_id,
                    'tgt2': c.hit2.intended_target.canonical_id,
                    'same': c.same_target,
                    'checkpoint': c.checkpoint_idx
                })
        elif c.condition == 'CONFUSION' and len(spot_check_candidates['confusion']) < 20:
            spot_check_candidates['confusion'].append({
                'file': fname,
                'actor': c.actor.canonical_id,
                'tgt1': c.hit1.intended_target.canonical_id,
                'tgt2': c.hit2.intended_target.canonical_id,
                'same': c.same_target,
                'checkpoint': c.checkpoint_idx
            })
        elif c.condition == 'TAUNT' and len(spot_check_candidates['taunt']) < 30:
            spot_check_candidates['taunt'].append({
                'file': fname,
                'actor': c.actor.canonical_id,
                'tgt1': c.hit1.intended_target.canonical_id,
                'tgt2': c.hit2.intended_target.canonical_id,
                'same': c.same_target,
                'checkpoint': c.checkpoint_idx
            })

print(f"\n--- BF-05 Stratified Re-extraction Results ---")
print(f"Processed Reports: {processed_reports}")
print(f"Total Combos Extracted: {len(all_combos)}")

inv_results = verify_combo_invariants(all_combos)
print(f"\n--- Sanity Invariants Verification ---")
for k, v in inv_results.items():
    print(f"{k:25s}: Total={v['total']:5d}, Passed={v['passed']:5d}, Rate={v['pass_rate']*100:.2f}%")

strata_summary = {}
print(f"\n{'Cand':7s} | {'Condition':10s} | {'Target1':10s} | {'Pool':12s} | {'N':6s} | {'Same':6s} | {'Diff':6s} | {'P(same)':8s} | {'95% CI':18s}")
print("-" * 95)

for key in sorted(strata.keys(), key=lambda x: (x[1], x[2], x[3], x[0])):
    vals = strata[key]
    n = len(vals)
    same = sum(1 for x in vals if x)
    diff = n - same
    p_same = same / n if n > 0 else 0.0
    ci_low, ci_high = compute_binomial_ci(n, same)

    cand, cond, tgt_stat, pool_st = key
    print(f"{cand:7s} | {cond:10s} | {tgt_stat:10s} | {pool_st:12s} | {n:6d} | {same:6d} | {diff:6d} | {p_same*100:6.2f}% | [{ci_low*100:5.2f}%, {ci_high*100:5.2f}%]")
    strata_summary[str(key)] = {
        'candidate_count': cand,
        'condition': cond,
        'target1_status': tgt_stat,
        'pool_state': pool_st,
        'n': n,
        'same': same,
        'diff': diff,
        'p_same': p_same,
        'ci_95': [ci_low, ci_high]
    }

out_path = os.path.join(BASE_DIR, 'r10_combo_detailed_stratified.json')
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump({
        'metadata': {
            'extractor': 'run_bf05_reextraction.py',
            'candidate_reports': len(combo_files),
            'processed_reports': processed_reports,
            'total_combos': len(all_combos),
            'invariants': inv_results,
            'excluded_counts': excluded_counts
        },
        'strata': strata_summary,
        'spot_check_candidates': spot_check_candidates
    }, fp, ensure_ascii=False, indent=2)

print(f"\nSaved re-extracted combo data to {out_path}")
