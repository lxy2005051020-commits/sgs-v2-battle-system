# Stage13 Whole-Battle Deterministic Replay Audit

> Date: 2026-10-05  
> Baseline Commit: `0002408eb661d7f93da82514cfae9f93d1d8827b`  
> Suite: `tests/test_stage13_whole_battle_replay_audit.py`  
> Python Environment: Python 3.11.15  
> Replay Audit Verdict: **PASS**  

---

## 1. Audit Scope & Methodology

A primary Exit Gate requirement for Stage13 Freeze is verifying whole-battle deterministic replay. The simulator must prove:
1. **Case A (Same-Seed Reproducibility)**: Given identical lineup, stats, loadout, and PRNG seed, N >= 20 independent executions produce identical results and event traces.
2. **Case B (Seed-Driven Divergence)**: Altering the PRNG seed produces divergent battle trajectories strictly attributable to authorized random decision points, and each seed trajectory is 100% reproducible.
3. **Case C (Zero-RNG Fast Paths)**: Deterministic execution paths (such as rate 0.0, rate 1.0, disabled providers, single targets) do not consume PRNG draws.

---

## 2. Replay Audit Results

### Case A: Same-Seed Duplicate Execution (N = 25 runs)

- **Input Seed**: `20260904`
- **Lineup**: 4 units (A-Team Commander, A-Team Deputy, B-Team Commander, B-Team Deputy)
- **Rounds**: 8 Max Rounds
- **Runs Executed**: 25 independent battle engine runs
- **Canonical Projection Hash**:
  ```text
  885dade34fb28b8b297e7020043cff0181f527fa56bde4c51bece6007b6b538d
  ```
- **Comparison Metric**: Canonical projection covering winner, end reason, rounds completed, final troops, and full ordered EventBus event history.
- **Result**:
  ```text
  Run  0 - 24: 100% Match (0 Divergences across 25 runs)
  Verdict: PASS
  ```

---

### Case B: Seed-Change Divergence & Attribution

- **Seeds Tested**: `[101, 202, 303, 404, 505, 606, 707, 808]`
- **Divergence Verification**:
  - Across 8 distinct seeds, each produced an authorized divergent combat trajectory with unique projection hashes and battle results.
  - Re-executing each seed reproduced its exact projection hash with 0 drift.
  - Differences were strictly verified to originate from authorized PRNG decision points in `RandomSystem`. No memory address, dict iteration order, or UUID randomness affected execution.
- **Verdict**: **PASS**

---

### Case C: Zero-RNG Fast Paths

- **Test Points**:
  1. `activation_rate = 0.0` Skill: Pre-checked and aborted with **0** PRNG draws.
  2. `enabled = False` Skill Runtime: Pre-checked and denied with **0** PRNG draws.
  3. `activation_rate = 1.0` + Deterministic Target: Resolved with **0** PRNG draws.
- **Result**:
  ```text
  Zero-draw fast paths verified.
  Verdict: PASS
  ```

---

## 3. Replay Conclusion

The battle simulation engine exhibits strict, bit-exact determinism under canonical projection. All requirements of G13-018 and RG13-002/003/009 are completely satisfied.
