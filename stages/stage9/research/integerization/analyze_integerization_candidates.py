#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze_integerization_candidates.py

Analyzes INTEGERIZATION_EVIDENCE.json against candidate rounding policies:
- FLOOR
- CEIL
- TRUNCATE_TOWARD_ZERO
- ROUND_HALF_UP (ties upward)
- ROUND_HALF_EVEN (banker's rounding)

Generates Candidate Elimination Matrix for each of the four call sites:
1. CHAIN_INTEGERIZATION
2. SHARE_INTEGERIZATION
3. DISTRIBUTION_TARGET_INTEGERIZATION
4. DISTRIBUTION_PARTICIPANT_INTEGERIZATION
"""

import os
import json
from fractions import Fraction
import math

EVIDENCE_PATH = os.path.join(os.path.dirname(__file__), 'INTEGERIZATION_EVIDENCE.json')


def apply_policy(val_frac, policy_name):
    """
    Evaluates exact rational val_frac under policy_name.
    """
    n = val_frac.numerator
    d = val_frac.denominator

    if policy_name == 'FLOOR':
        return n // d
    elif policy_name == 'CEIL':
        return -((-n) // d)
    elif policy_name == 'TRUNCATE_TOWARD_ZERO':
        # For non-negative domain, truncate == floor
        if val_frac >= 0:
            return n // d
        else:
            return -((-n) // d)
    elif policy_name == 'ROUND_HALF_UP':
        # Nearest integer, half rounds towards +infinity (for >= 0)
        return (n * 2 + d) // (d * 2)
    elif policy_name == 'ROUND_HALF_EVEN':
        fl = n // d
        rem = val_frac - fl
        if rem < Fraction(1, 2):
            return fl
        elif rem > Fraction(1, 2):
            return fl + 1
        else:
            # tie: choose even
            return fl if (fl % 2 == 0) else fl + 1
    else:
        raise ValueError(f"Unknown policy {policy_name}")


def evaluate_dataset(samples, val_key, obs_key, call_site_name):
    policies = ['FLOOR', 'CEIL', 'TRUNCATE_TOWARD_ZERO', 'ROUND_HALF_UP', 'ROUND_HALF_EVEN']
    results = {}

    for pol in policies:
        results[pol] = {
            'total_tested': 0,
            'tie_tested': 0,
            'tie_fit': 0,
            'non_tie_tested': 0,
            'non_tie_fit': 0,
            'contradictions': 0,
            'contradiction_examples': []
        }

    for s in samples:
        val = Fraction(s[val_key])
        obs = int(s[obs_key])
        is_tie = (val % 1 == Fraction(1, 2))

        for pol in policies:
            pred = apply_policy(val, pol)
            res = results[pol]
            res['total_tested'] += 1
            if is_tie:
                res['tie_tested'] += 1
                if pred == obs:
                    res['tie_fit'] += 1
                else:
                    res['contradictions'] += 1
                    if len(res['contradiction_examples']) < 3:
                        res['contradiction_examples'].append({
                            'input': str(val),
                            'float': float(val),
                            'predicted': pred,
                            'observed': obs,
                            'source': s.get('battle_id', '')
                        })
            else:
                res['non_tie_tested'] += 1
                if pred == obs:
                    res['non_tie_fit'] += 1
                else:
                    res['contradictions'] += 1
                    if len(res['contradiction_examples']) < 3:
                        res['contradiction_examples'].append({
                            'input': str(val),
                            'float': float(val),
                            'predicted': pred,
                            'observed': obs,
                            'source': s.get('battle_id', '')
                        })

    return results


def main():
    if not os.path.exists(EVIDENCE_PATH):
        print(f"Error: {EVIDENCE_PATH} not found. Run extract_integerization_boundaries.py first.")
        return

    with open(EVIDENCE_PATH, encoding='utf-8') as fp:
        data = json.load(fp)

    print("=" * 80)
    print("STAGE 9 INTEGERIZATION CANDIDATE ELIMINATION ANALYSIS")
    print("=" * 80)

    # 1. DAMAGE_SHARE
    share_all = (
        data['damage_share']['exact_half_samples'] +
        data['damage_share']['exact_integer_samples'] +
        data['damage_share']['controls_below'] +
        data['damage_share']['controls_above']
    )
    res_share = evaluate_dataset(share_all, 'theoretical_exact', 'observed_sharer_loss', 'DAMAGE_SHARE')

    print("\n### 1. DAMAGE_SHARE Analysis")
    print(f"Total samples: {len(share_all)} (Ties: {len(data['damage_share']['exact_half_samples'])})")
    print(f"{'Policy':<22} | {'Non-tie fit':<14} | {'Tie fit':<10} | {'Contradictions':<14} | {'Verdict'}")
    print("-" * 75)
    for pol, r in res_share.items():
        verdict = "CONFIRMED FIT" if r['contradictions'] == 0 else "ELIMINATED"
        non_tie_str = f"{r['non_tie_fit']}/{r['non_tie_tested']}"
        tie_str = f"{r['tie_fit']}/{r['tie_tested']}"
        print(f"{pol:<22} | {non_tie_str:<14} | {tie_str:<10} | {r['contradictions']:<14} | {verdict}")

    # 2. DISTRIBUTION TARGET
    dtgt_all = (
        data['distribution']['target_half_samples'] +
        data['distribution']['target_controls_below'] +
        data['distribution']['target_controls_above']
    )
    res_dtgt = evaluate_dataset(dtgt_all, 'theoretical_exact', 'observed_target_loss', 'DISTRIBUTION_TARGET')

    print("\n### 2. DISTRIBUTION_TARGET Analysis")
    print(f"Total samples: {len(dtgt_all)} (Ties: {len(data['distribution']['target_half_samples'])})")
    print(f"{'Policy':<22} | {'Non-tie fit':<14} | {'Tie fit':<10} | {'Contradictions':<14} | {'Verdict'}")
    print("-" * 75)
    for pol, r in res_dtgt.items():
        verdict = "CONFIRMED FIT" if r['contradictions'] == 0 else "ELIMINATED"
        non_tie_str = f"{r['non_tie_fit']}/{r['non_tie_tested']}"
        tie_str = f"{r['tie_fit']}/{r['tie_tested']}"
        print(f"{pol:<22} | {non_tie_str:<14} | {tie_str:<10} | {r['contradictions']:<14} | {verdict}")

    # 3. DISTRIBUTION PARTICIPANT
    dpart_all = (
        data['distribution']['participant_half_samples'] +
        data['distribution']['participant_integer_samples'] +
        data['distribution']['participant_controls_below'] +
        data['distribution']['participant_controls_above']
    )
    res_dpart = evaluate_dataset(dpart_all, 'theoretical_exact', 'observed_participant_loss', 'DISTRIBUTION_PARTICIPANT')

    print("\n### 3. DISTRIBUTION_PARTICIPANT Analysis")
    print(f"Total samples: {len(dpart_all)} (Ties: {len(data['distribution']['participant_half_samples'])})")
    print(f"{'Policy':<22} | {'Non-tie fit':<14} | {'Tie fit':<10} | {'Contradictions':<14} | {'Verdict'}")
    print("-" * 75)
    for pol, r in res_dpart.items():
        verdict = "CONFIRMED FIT" if r['contradictions'] == 0 else "ELIMINATED"
        non_tie_str = f"{r['non_tie_fit']}/{r['non_tie_tested']}"
        tie_str = f"{r['tie_fit']}/{r['tie_tested']}"
        print(f"{pol:<22} | {non_tie_str:<14} | {tie_str:<10} | {r['contradictions']:<14} | {verdict}")

    # 4. CHAIN
    chain_all = data['chain_link']['samples']
    res_chain = evaluate_dataset(chain_all, 'theoretical_exact', 'observed_chain_damage', 'CHAIN_LINK')

    print("\n### 4. CHAIN_LINK Analysis")
    print(f"Total samples: {len(chain_all)}")
    print(f"{'Policy':<22} | {'Non-tie fit':<14} | {'Tie fit':<10} | {'Contradictions':<14} | {'Verdict'}")
    print("-" * 75)
    for pol, r in res_chain.items():
        verdict = "CONFIRMED FIT" if r['contradictions'] == 0 else "ELIMINATED"
        non_tie_str = f"{r['non_tie_fit']}/{r['non_tie_tested']}"
        tie_str = f"{r['tie_fit']}/{r['tie_tested']}"
        print(f"{pol:<22} | {non_tie_str:<14} | {tie_str:<10} | {r['contradictions']:<14} | {verdict}")


if __name__ == '__main__':
    main()
