import json
import math
from dataclasses import dataclass
from .action_segmenter import ComboPair

def compute_binomial_ci(n: int, k: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion"""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    margin = (z * math.sqrt((p * (1 - p) + (z**2) / (4 * n)) / n)) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return lower, upper


def verify_combo_invariants(combos: list[ComboPair]) -> dict:
    inv1_total = 0
    inv1_passed = 0
    inv1_failures = []

    inv2_total = 0
    inv2_passed = 0
    inv2_failures = []

    inv6_total = 0
    inv6_passed = 0
    inv6_failures = []

    for idx, c in enumerate(combos):
        # INV-06: Hit1.actor == Hit2.actor
        inv6_total += 1
        if c.hit1.actor.same_unit(c.hit2.actor):
            inv6_passed += 1
        else:
            inv6_failures.append((idx, c.actor.canonical_id))

        # INV-01: candidate_count == 1 AND target1 survives AND condition == 'NORMAL' AND not pool_changed -> same_target MUST be True
        if c.candidate_count == 1 and c.target1_status == 'SURVIVED' and c.condition == 'NORMAL' and not c.pool_changed:
            inv1_total += 1
            if c.same_target:
                inv1_passed += 1
            else:
                inv1_failures.append((idx, c.hit1.intended_target.canonical_id, c.hit2.intended_target.canonical_id))

        # INV-02: target1 marked DEAD -> target2 cannot be same runtime unit
        if c.target1_status == 'DIED':
            inv2_total += 1
            if not c.same_target:
                inv2_passed += 1
            else:
                inv2_failures.append((idx, c.hit1.intended_target.canonical_id, c.hit2.intended_target.canonical_id))

    return {
        'inv01_candidate1_same': {
            'total': inv1_total,
            'passed': inv1_passed,
            'pass_rate': (inv1_passed / inv1_total) if inv1_total > 0 else 1.0,
            'failures_sample': inv1_failures[:5]
        },
        'inv02_dead_retarget': {
            'total': inv2_total,
            'passed': inv2_passed,
            'pass_rate': (inv2_passed / inv2_total) if inv2_total > 0 else 1.0,
            'failures_sample': inv2_failures[:5]
        },
        'inv06_combo_actor_match': {
            'total': inv6_total,
            'passed': inv6_passed,
            'pass_rate': (inv6_passed / inv6_total) if inv6_total > 0 else 1.0,
            'failures_sample': inv6_failures[:5]
        }
    }
