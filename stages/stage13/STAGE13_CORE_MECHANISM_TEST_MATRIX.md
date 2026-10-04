# Stage13 Core Mechanism Test Matrix

> Stage13-A test inventory.
>
> This file records current discriminating coverage and the tests Stage13 must add before Core Gameplay Engine freeze.

## 1. Baseline

Latest recorded merged-main validation before the Stage13 replan:

~~~text
pytest = 1667 passed
demo   = PASS
~~~

The Stage13 replan is documentation-only. No gameplay code was changed by activation/inventory work.

## 2. Existing coverage matrix

| Domain | Current high-value tests | What they already prove | Stage13 coverage verdict |
|---|---|---|---|
| Engine phases / hook barriers | test_stage7_engine_hooks.py | round expiry before hook, hook event order, lethal hook finalization, action lifecycle closure | PARTIAL: only current hook surfaces |
| EventBus non-authority | test_stage9_phase_9_8_architecture.py | combat completes with zero EventBus subscribers | SUFFICIENT for fact-only boundary |
| Action / target | test_stage9_phase_9_3_target_resolution.py, test_stage9_phase_9_6_normal_attack.py | confusion/taunt/guard order, fresh target resolution, no extra target RNG | STRONG for existing NA path |
| Target policy / Stage12 | test_stage12_shared_foundation_round*.py, test_stage12_690108_provocation.py, test_stage12_690110_capture.py | typed target operations, required/excluded targets, CHOOSE_N governance, friendly target controls | PARTIAL for generic selectors |
| Damage pipeline | test_stage8_damage_pipeline.py | deterministic modifier phases, prevention, critical rules, zero RNG fast paths, no calculation events | STRONG |
| Damage identity / settlement | test_stage9_phase_9_4_damage_instance.py, test_stage9_phase_9_4_typed_settlement.py | DamageInstance identity, permits, assigned vs actual settlement | STRONG |
| Cross-mechanism damage | test_stage9_phase_9_7_cleave_chain_counter.py, test_stage9_phase_9_8_full_integration.py | derived work, partition/reaction ordering, termination integration | STRONG for frozen families |
| Architecture ownership | test_stage9_phase_9_8_architecture.py | no duplicate physical state collections, sole composition root, no service locator, no import cycles | STRONG |
| Rule-intent execution right | test_stage10_phase3_rule_intent_execution_right.py | owner/target defeat, abort scopes, typed descriptor, mixed ordering | STRONG for current intents |
| State lifecycle/generation | test_stage10_phase2_lifecycle_generation.py, test_state_lifecycle.py | generation snapshots, expiry, refresh, action windows | STRONG for StateInstance |
| Continuous damage | test_stage10_phase4_continuous_damage_frozen_lane.py | application-frozen basis and periodic execution | STRONG for current DOT lane |
| Recovery opportunity | test_stage10_phase5_recovery_opportunity_system.py | FirstAid/Recuperation admission, fatal exclusion, RNG count, provider gating | STRONG for two current opportunity kinds |
| Damage aftermath | test_stage10_phase6_damage_aftermath_stage9.py | post-settlement facts route across Stage9 paths | STRONG |
| Recovery settlement | test_recovery_system.py, test_stage11_share_lifesteal_resolution.py | modifier second CEIL, healing ban, capacity, lifesteal basis | STRONG |
| Stage11 action/control/damage states | Stage11 freeze suite + adversarial audit | action order, controls, crit/pierce/lifesteal/alert frozen lanes | STRONG with explicit bounded unknowns |
| Stage12 Shared Foundation | test_stage12_shared_foundation_round1.py .. round4.py | state/provider/equipment/dependency/application/removal/execution-right owners | STRONG |
| Stage12 seven states | test_stage12_690089_*.py through test_stage12_690222_*.py | state-specific contract integration and independent freeze audits | STRONG |
| Owner uniqueness / RNG ownership | test_stage12_final_completion_audit.py | canonical owners unique, only canonical RNG, no god object, 690086 debt preserved | STRONG |
| Deterministic golden behavior | test_stage9_phase_9_8_golden_trace.py and seeded domain tests | current scoped traces stable | PARTIAL for Stage13 whole-battle replay |

## 3. Stage13 required new tests

| Test ID | Required discriminating test | Gap(s) | Must prove |
|---|---|---|---|
| T13-001 | inventory authority test | all | required Stage13 documents exist; Entry Gate status and preserved Stage12 debt are not silently changed |
| T13-002 | timing opportunity order | G13-001 | canonical opportunity sequence around round/action/damage/recovery/state commits; EventBus cannot own admission |
| T13-003 | opportunity rejection has no downstream work | G13-001/004 | denied opportunity emits no effect-owned RNG/target/work |
| T13-004 | generic target ranking determinism | G13-002 | selectors have explicit stable comparator and no hidden iteration-order dependence |
| T13-005 | target query freshness lineage | G13-002/015 | NEW_QUERY allocates new identity; inherited/derived/locked continuation retains lineage correctly |
| T13-006 | typed attribute contribution composition | G13-005 | base + state/skill/equipment/temp contributions resolve through one AttributeSystem owner with provenance |
| T13-007 | flat/percent phase ordering | G13-005/011 | modifier order is explicit and deterministic; no direct UnitRuntime mutation |
| T13-008 | attribute snapshot vs JIT discriminator | G13-006/016 | changing an attribute between admission and execution distinguishes modes correctly |
| T13-009 | RNG decision trace same-seed identity | G13-007/018 | same input/seed produces same ordered RandomSystem API decision trace |
| T13-010 | rejected paths zero-draw matrix | G13-007 | new policies preserve draw/no-draw contracts |
| T13-011 | Effect sequence ordering | G13-008/009 | effect A may change effect B legality according to declared sequence contract |
| T13-012 | Effect sequence abort/continue boundary | G13-009 | failure semantics are explicit; no accidental half-commit |
| T13-013 | delayed work identity and due-time execution | G13-010/012/015 | pending work retains stable lineage and fires only at its typed opportunity |
| T13-014 | repeated work per-execution target/RNG semantics | G13-010 | per-hit/per-operation behavior is explicit and deterministic |
| T13-015 | usage budget once-per-round / N-use | G13-013 | counters decrement exactly once at the declared commit point |
| T13-016 | pending work source defeat modes | G13-014/016 | CONTINUE / RECHECK / CANCEL-style modes, if adopted, differ without universal source-death cleanup |
| T13-017 | pending work target defeat mode | G13-014/016 | dead target skip/reselect/deny behavior follows typed spec and consumes correct RNG |
| T13-018 | dependency cycle atomicity with new work refs | G13-014/016 | proposed topology fails before mutation |
| T13-019 | category removal exactness | G13-017 | only authorized state categories are removed; unrelated states remain |
| T13-020 | 690221 newly frozen family lanes | G13-019 | implementation exactly follows focused research authority; unknown lanes still fail explicitly |
| T13-021 | full replay duplicate run | G13-018 | same input/seed -> same action order, operations, RNG trace, targets, damage, recovery, states, final troops |
| T13-022 | replay divergence on seed change | G13-018 | trace differences are attributable to authorized random decisions, not unstable iteration |
| T13-023 | no direct random outside RandomSystem | G13-007 | production AST/static audit remains green |
| T13-024 | no new shadow owner / god object | all architecture gaps | new code preserves single-owner matrix |
| T13-025 | Stage1-12 full regression | all | every frozen stage remains green after Stage13 implementation |
| T13-026 | demo | all | project demo remains PASS |

## 4. Current notable discriminators already present

Examples from the current suite that Stage13 must not lose:

- exact-speed ties consume no shuffle RNG;
- Damage calculation publishes no committed fact before settlement;
- dead source/target damage fails before RNG/event/rule discovery;
- FirstAid fatal damage cannot revive and consumes no recovery RNG;
- provider-invalid and permission-denied paths short-circuit before owned RNG;
- EffectExecutor does not own RNG, troop mutation, or StateRegistry mutation;
- EventBus subscribers are unnecessary for gameplay correctness;
- DamageInstance settlement permit is authentic and single-consume;
- state dependency replacements validate atomically before commit;
- 690086 research debt is asserted not to be laundered into complete.

## 5. Test gate progression

~~~text
Stage13-A Inventory
  -> T13-001

Stage13-C Governance / Research
  -> authority-specific discriminator tests

Stage13-D Architecture
  -> T13-002..019, T13-023..024 planned and independently audited

Stage13-E Implementation
  -> implement in dependency batches
  -> focused tests per batch
  -> Stage1-12 regression after each batch

Stage13-F Freeze
  -> T13-020..026
  -> whole-battle deterministic replay audit
  -> full pytest
  -> demo
~~~

A green full suite is necessary but not sufficient. The Stage13 exit gate additionally requires owner uniqueness, explicit governance provenance, zero unresolved implementation-required gaps, and independent freeze audit.

## Stage13-D1 executable test closure — 2026-10-04

| Required discriminator | Executable evidence | Result |
|---|---|---|
| T1 one-shot delay | test_t1_delay_exactly_once_and_no_terminal_replay | PASS |
| T2 independent source death / T3 required source | test_t2_t3_source_death_policy | PASS / COMPLETED vs CANCELLED |
| T4 provider invalidation | test_t4_live_provider_invalidation_zero_dispatch_zero_rng | PASS / slot 0 included |
| T5 target death | test_t5_target_death_cancels | PASS |
| T6 deterministic order | test_t6_order_is_explicit_sequence_not_lexical_ids_or_dictionary | PASS |
| T7 finalization barrier | test_t7_pending_never_holds_finalization_barrier_and_no_resurrection; independent same-batch and lethal-domain tests | PASS |
| T8 snapshot/JIT split | test_t8_snapshot_deep_freeze_and_live_read_split | PASS |
| Real mechanism adapter | test_real_recuperation_adapter_same_results_rng_and_entire_domain_event_trace; test_real_state_producer_recuperation_adapter_keeps_generation_events_and_rng | PASS |
| Independent adversarial ownership audit | tests/test_stage13_d1_adversarial_audit.py; scripts/audit_stage13_d1.py | 11 PASS / 21 frozen-owner hashes identical |

Focused: 48 PASS. Full: 1739 PASS. Demo: PASS. D1 does not satisfy Stage13-G whole-battle
replay or engine-exit readiness. See D1 freeze audit for the latest-main CI gate.
