# Stage12 Runtime Test Matrix Skeleton

> Status: **SKELETON / ENTRY GATE OUTPUT**  
> Baseline: **913 passed / demo PASS** at Battle SHA `b4c27511824001210f781bf8e750c74c9107da72`.

| State / Foundation | Positive Case | Negative Case | Primary Discriminator | Cross-State Required | Minimum |
|---|---|---|---|---|---:|
| Shared State Admission | protected control rejected under effective Insight | unprotected/special-boundary state not rejected | reject candidate vs apply-then-delete | Insight × all explicit contract overlaps | contract-driven |
| Shared Resident/Effective | resident state can be temporarily ineffective | effective state acts normally | suppression vs removal | Insight/Provocation/provider suppression | contract-driven |
| Skill Permission | Exhaustion blocks ACTIVE_SKILL | Basic Attack and standard Assault remain eligible | permission block vs generic cannot-act | Insight × Exhaustion; Exhaustion × Capture | contract-driven |
| Provider Validity | targeted Provider becomes ineffective | unrelated Provider remains effective | Provider vs Holder | FalseReport × Intimidation × Capture | contract-driven |
| Target Policy | eligible Provocation query forces/includes Source | friendly/healing/self/inherited target not cross-forced | operation/query granularity | Confusion/Taunt/Insight/Exhaustion/FalseReport/Capture | contract-driven |
| Equipment Effectiveness | Sabotage disables tested equipment contribution | equipment object remains present | resume vs unequip/reinit | Insight × Sabotage; FalseReport × Sabotage; Sabotage × Capture | contract-driven |
| INSIGHT | protected application rejection + existing suppression/resume | FALSE_REPORT / INTIMIDATION / CAPTURE boundaries preserved | protected vs unprotected/special | Exhaustion, FalseReport, Provocation, Intimidation, Sabotage, Capture | per contract |
| EXHAUSTION | Active permission denied | legal Basic Attack remains | EXHAUSTION ≠ STUN | Insight, Provocation, FalseReport, Intimidation, Capture | per contract |
| FALSE_REPORT | Passive/Command Provider suppressed | Holder-only unrelated effect remains | Provider suppression vs deletion | Insight, Exhaustion, Intimidation, Capture, Sabotage | >= 30 |
| PROVOCATION | admissible Source forced in eligible operation | dead/inadmissible Source not forced | state remains resident after Source death | Confusion, Taunt, Insight, Exhaustion, FalseReport, Capture | >= 25 |
| INTIMIDATION | exactly one eligible Provider suppressed | all-skill suppression forbidden | refresh reroll vs resume-preserve-binding | Insight, Exhaustion, FalseReport, Capture | >= 21 |
| SABOTAGE | equipment contribution suppressed | no physical unequip/delete | resume vs reinitialize | Insight, FalseReport, Capture | per contract |
| CAPTURE | action/damage/provider/recovery/target restrictions | attached Active-origin DOT continues | composite owners vs universal boolean | Insight, Exhaustion, FalseReport, Provocation, Intimidation, Sabotage + Stage11 controls | per contract |

## Mandatory Stage12 cross-state matrix

```text
Insight × Exhaustion
Insight × FalseReport
Insight × Provocation
Insight × Intimidation
Insight × Sabotage
Insight × Capture

Exhaustion × Provocation
Exhaustion × FalseReport
Exhaustion × Intimidation
Exhaustion × Capture

FalseReport × Intimidation
FalseReport × Capture
FalseReport × Sabotage

Provocation × Confusion
Provocation × Taunt
Provocation × Capture

Intimidation × Capture
Sabotage × Capture
```

## Mandatory Stage11 × Stage12 regressions

```text
STUN × CAPTURE
WEAKNESS × CAPTURE
HEALING_BLOCK × CAPTURE
CONFUSION × PROVOCATION
TAUNT × PROVOCATION
DISARM × INSIGHT
STUN × INSIGHT
existing Damage Pipeline × CAPTURE
existing Recovery Pipeline × CAPTURE
```

## RNG obligations

For every randomized application, target selection, Intimidation binding or refresh reroll, tests must record:

- canonical RNG owner = `BattleContext.random`;
- exact decision point that consumes RNG;
- negative branches that must not consume RNG;
- deterministic replay under identical seed.

## Lifecycle obligations

Each state must test only contract-authorized boundaries among:

```text
application
effective timing
refresh / reapplication
same-source
different-source
removal
cleanse
expiry
holder death
source death
battle finalization
```

A `BOUNDED_UNKNOWN` must never become a normal-looking test assertion unless it is explicitly listed in the Runtime Default Ledger.

## SF-0 test-design input — 2026-09-27

Fresh baseline at `0c2983461e4f68a43bcb2851498c975e820592dc`: 913 passed / demo exit 0.
[Design Question Ledger section 4](STAGE12_SHARED_FOUNDATION_DESIGN_QUESTION_LEDGER.md) gives proposed
foundation test files, named discriminator cases and the full required cross-state pair set.
These are PLANNED, not implemented or passing Stage12 tests. Legacy P0-CFS-P93-01 conflicts with
Insight v0.4 and must retain its provenance until explicit supersession; do not weaken it for CI.
Add slot-0 Provider lookup, suppressed STUN clock and immediate-interruption transition cases.


## SF Round 3 planned discriminator suite

Status: DESIGN_FROZEN / NOT IMPLEMENTED.

### StateEffectivenessPolicy

```text
test_resident_effective_decision
test_resident_suppressed_decision_preserves_instance
test_removed_state_is_not_queryable_as_effectiveness
test_insight_suppresses_existing_confusion
test_insight_removal_resumes_same_live_confusion_instance
test_confusion_expired_while_suppressed_never_resurrects
test_suppressed_insight_does_not_protect_controls
test_insight_provider_resume_restores_protection_without_reapply
test_two_state_suppression_causes_remove_first_stays_suppressed
test_two_state_suppression_causes_remove_last_resumes
test_suppression_does_not_pause_lifecycle_clock
```

### ProviderValidityPolicy

```text
test_provider_exists_and_valid
test_provider_baseline_disabled_is_not_transient_suppression
test_provider_suppressed_preserves_enabled_baseline
test_provider_missing
test_provider_identity_mismatch
test_provider_a_suppressed_remote_holder_effect_becomes_inactive
test_unrelated_provider_on_holder_remains_valid
test_false_report_suppresses_passive_and_command_provider
test_intimidation_suppresses_only_selected_provider
test_intimidation_ineffective_preserves_binding_without_reroll
test_capture_suppresses_verified_passive_command_provider
test_two_provider_suppression_causes_remove_one_still_suppressed
test_final_provider_suppression_cause_removal_resumes_future_only
```

### Dependency propagation

```text
test_false_report_suppresses_insight_provider_then_confusion_resumes
test_false_report_end_restores_provider_then_same_insight_suppresses_confusion_again
test_dependency_propagation_does_not_reapply_state_or_reset_timer
test_dependency_propagation_does_not_replay_missed_trigger
test_source_death_without_explicit_dependency_does_not_invalidate_established_state
```

### Cycle / transition coordination

```text
test_simple_acyclic_dependency_evaluates_once_per_session
test_nested_dependency_propagates_in_reverse_dependency_order
test_duplicate_dependency_is_deduplicated
test_cycle_detected_with_explicit_cycle_path
test_cycle_never_recurses_until_python_recursion_error
test_cycle_produces_no_silent_allow_or_deny_decision
test_dependency_topology_cycle_validation_fails_before_transition_commit
test_query_repetition_emits_no_duplicate_transition_fact
test_effective_to_suppressed_and_suppressed_to_effective_transition_diff
```

### Migration regressions

```text
test_stage9_operational_insight_delegates_shared_policy
test_stage9_confusion_historical_p93_rule_replaced_by_round2_authority
test_stage9_taunt_target_arbitration_preserved
test_stage11_is_effective_delegates_shared_policy
test_stage11_effective_instances_order_preserved
test_stage11_remaining_uses_behavior_preserved_through_local_rule_adapter
```

Round 3 adds design coverage only. It adds zero production tests in this commit because gameplay implementation is explicitly forbidden.

## SF Round 4 planned discriminator suite

Status: **DESIGN_FROZEN / NOT IMPLEMENTED**.

### Admission

```text
test_insight_rejects_incoming_protected_control
test_rejected_candidate_never_becomes_resident
test_rejected_candidate_preserves_existing_state_exactly
test_source_rng_consumed_before_insight_admission_when_required
test_deterministic_control_adds_no_rng
test_rejected_child_does_not_abort_sibling_effect
```

### Conflict / refresh transaction

```text
test_insight_reapply_rejected_no_refresh
test_suppressed_insight_reapply_rejected_PD_INS_002
test_false_report_equal_reapply_no_refresh
test_refresh_transaction_is_atomic
test_intimidation_refresh_changes_binding_only_on_commit
test_intimidation_resume_preserves_binding_and_timer
test_refresh_keeps_instance_id_and_advances_generation
test_rejected_conflict_allocates_no_generation
```

### Clock

```text
test_suppressed_control_clock_continues
test_suppressed_control_expires_and_never_resumes
test_stun_suppression_does_not_consume_behavior_block
test_intimidation_can_expire_while_suppressed
test_false_report_expiry_restores_provider_future_only
test_stage12_lifetime_metadata_does_not_enter_stage10_persistence
test_same_envelope_due_state_does_not_transiently_resume
```

### Removal

```text
test_capture_rejects_ordinary_cleanse
test_intimidation_generic_removal_boundary
test_intimidation_specialized_removal_is_explicit_unsupported_boundary
test_source_death_does_not_remove_capture
test_source_death_does_not_remove_provocation
test_holder_defeat_cleanup_not_synthetic_expiry_cascade
test_remove_insight_resumes_live_control
test_remove_false_report_propagates_provider_resume
```

### Failure / compatibility

```text
test_cycle_validation_failure_commits_nothing
test_refresh_failure_preserves_old_instance
test_refresh_failure_preserves_old_binding
test_rejected_removal_preserves_instance_and_timer
test_legacy_apply_failure_adapter_preserved
```

Round 4 adds design coverage only. It changes zero production tests and zero gameplay code.


## SF Round 5 planned discriminator suite

Status: **DESIGN_FROZEN / NOT IMPLEMENTED**.

### Skill Permission

~~~text
test_exhaustion_denies_active
test_exhaustion_allows_normal_attack
test_exhaustion_does_not_deny_standard_assault
test_exhaustion_does_not_disable_passive_command
test_suppressed_exhaustion_allows_active
test_exhaustion_resume_denies_future_active
test_already_admitted_active_not_rolled_back
test_skip_preparation_does_not_bypass_exhaustion
test_no_active_attempt_emits_no_block
~~~

### Preparation interruption port

~~~text
test_effective_exhaustion_interrupts_all_current_active_preparations_for_holder
test_selected_intimidation_interrupts_only_selected_provider
test_unselected_provider_preparation_untouched
test_suppressed_exhaustion_does_not_interrupt
test_exhaustion_becomes_effective_after_insight_ends_interrupts_immediately
test_interrupted_preparation_does_not_resume
test_provider_resume_does_not_resume_preparation
test_not_preparing_is_noop
test_provider_not_matched_is_distinct_from_not_preparing
test_interruption_completes_before_later_gameplay_in_same_transition_wave
~~~

### JIT Provider gate migration

~~~text
test_slot_zero_provider_is_gated
test_slot_one_provider_is_gated
test_slot_two_provider_is_gated
test_expected_skill_id_mismatch_rejected
test_missing_provider_rejected
test_baseline_disabled_rejected
test_provider_suppressed_rejected
test_provider_gate_rejection_consumes_no_recovery_rng
test_provider_valid_path_preserves_existing_rng_behavior
test_attribution_only_effect_does_not_gain_provider_liveness
~~~

### Composition

~~~text
test_provider_valid_but_exhaustion_blocks_active
test_provider_suppressed_without_exhaustion_blocks_selected_skill
test_provider_and_exhaustion_blockers_do_not_change_allow_deny_by_evaluation_order
test_remove_intimidation_but_capture_remains_provider_suppressed
test_final_suppression_removed_provider_valid_but_exhaustion_still_blocks_active
test_provider_resume_never_auto_activates_skill
test_provider_resume_never_resumes_old_preparation
~~~

### Static / architecture audit

~~~text
test_skill_permission_policy_consumes_no_rng
test_provider_validity_policy_consumes_no_rng
test_recovery_gate_has_no_source_skill_slot_truthiness_check
test_skill_resolver_does_not_treat_runtime_enabled_as_complete_provider_truth
test_preparation_port_is_protocol_only_and_does_not_store_progress
test_event_handlers_do_not_decide_preparation_interruption
~~~

Round 5 changes zero production tests and zero gameplay code.
