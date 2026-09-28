# Stage12 Runtime Test Matrix Skeleton

> Status: **SHARED FOUNDATION COMPLETE / 690089 + 690101 + 690107 + 690108 + 690222 RUNTIME FROZEN / STAGE12 RUNTIME 5 OF 7 / NEXT 690109 SABOTAGE**  
> Historical entry baseline: **913 passed / demo PASS** at Battle SHA `b4c27511824001210f781bf8e750c74c9107da72`.  
> Current 690222 independent freeze checkpoint: **1483 passed / demo PASS** at audit-test SHA `0b3e5d62b1c2e25e4b2177ccfa5dd456819ddc96`, PR CI `36374443142`.

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
FalseReport-source × Provocation
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
INSIGHT × CONFUSION
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


## SF Round 6 planned discriminator suite

Status: **DESIGN_FROZEN / NOT IMPLEMENTED**.

### Provocation target policy

~~~text
test_provocation_single_forces_source
test_provocation_choose_n_includes_source_and_preserves_n
test_provocation_fixed_all_preserves_all
test_source_already_selected_no_duplicate
test_friendly_operation_not_redirected
test_self_operation_not_redirected
test_normal_attack_not_redirected
test_confusion_preempts_provocation
test_exhaustion_blocked_skill_creates_no_target_operation
test_provider_invalid_skill_creates_no_target_operation
test_policy_cannot_force_illegal_source
~~~

### Query granularity / provenance

~~~text
test_inherited_target_not_rechecked
test_derived_target_not_rechecked_without_explicit_new_query
test_independent_second_query_rechecks_provocation
test_multi_hit_same_target_one_operation
test_multi_query_creates_distinct_operation_ids
test_target_operation_producer_must_explicitly_mark_new_query
test_target_operation_id_is_value_identity_not_object_identity
~~~

### Capture target eligibility

~~~text
test_captured_holder_excluded_from_friendly_single
test_captured_holder_excluded_from_verified_friendly_choose_n
test_capture_does_not_remove_enemy_targetability
test_capture_does_not_mutate_global_allies_query
test_self_recovery_not_reimplemented_as_target_exclusion
test_all_allies_boundary_remains_explicit
test_locked_delayed_friendly_target_remains_DQ_SF_23_boundary
test_friendly_single_empty_after_capture_maps_to_no_legal_target
test_choose_n_insufficient_pool_does_not_silently_claim_min_count_contract
~~~

### Architecture / RNG ownership

~~~text
test_target_policy_consumes_zero_rng
test_selector_remains_rng_owner
test_normal_attack_target_resolution_unchanged_without_stage12_skill_operation
test_fixed_all_target_policy_does_not_add_rng
test_source_already_selected_does_not_add_policy_rng
test_target_resolution_id_not_reused_as_skill_target_operation_id
~~~

These are future production-test names/obligations. Round 6 adds no executable test code and changes no existing Stage9/11 assertions.


## SF Round 7 planned discriminator suite

Status: DESIGN_FROZEN / NOT IMPLEMENTED.

### Equipment identity / retention

~~~text
test_equipment_provider_ref_is_stable_value_identity
test_equipment_contribution_ref_is_serializable
test_equipment_provider_is_not_skill_provider
test_sabotage_does_not_remove_equipment_provider
test_resume_uses_same_equipment_provider_identity
test_zero_equipment_contributions_is_safe
~~~

### Static attributes / Insight x Sabotage

~~~text
test_equipment_attribute_active_before_sabotage
test_sabotage_suppresses_equipment_attribute_without_mutating_base_stat
test_insight_suppresses_sabotage_and_same_attribute_resumes
test_insight_end_reactivates_same_sabotage_and_attribute_suppresses_again
test_sabotage_end_restores_attribute_without_cumulative_drift
~~~

### Damage / recovery modifiers

~~~text
test_sabotage_excludes_equipment_damage_modifier_per_request
test_damage_modifier_order_key_unchanged_by_equipment_filter
test_settled_damage_never_rolls_back
test_sabotage_excludes_equipment_recovery_modifier
test_recovery_second_ceil_owner_unchanged
test_healing_block_order_unchanged_without_stage12_equipment_cause
test_past_recovery_not_replayed_on_resume
~~~

### Trigger / scheduled trigger

~~~text
test_equipment_trigger_fires_before_sabotage
test_equipment_trigger_window_skipped_while_sabotaged
test_equipment_trigger_fires_on_future_window_after_resume
test_skipped_trigger_window_never_replays
test_scheduled_due_window_suppressed_at_execution
test_scheduled_resume_does_not_backfill
test_collected_then_queued_trigger_remains_DQ_SF_23_boundary
~~~

### Remote live effect / dependency

~~~text
test_remote_equipment_effect_requires_explicit_contribution_dependency
test_owner_equipment_suppression_makes_remote_effect_ineffective
test_remote_holder_unrelated_provider_unaffected
test_remote_effect_resume_uses_same_live_effect
test_remote_effect_expired_while_suppressed_never_resurrects
test_effect_source_ref_alone_does_not_create_equipment_dependency
~~~

### Evidence-scope guards / multi-reason

~~~text
test_false_report_tested_equipment_special_is_suppressed
test_false_report_untested_equipment_category_is_explicit_boundary
test_capture_verified_equipment_attribute_is_suppressed
test_capture_equipment_reactive_damage_is_explicit_boundary
test_sabotage_plus_false_report_remove_sabotage_still_suppressed
test_sabotage_plus_false_report_reverse_removal_order
test_capture_plus_sabotage_remove_capture_still_suppressed
test_final_known_cause_removed_with_unresolved_boundary_does_not_silently_allow
test_final_cause_removal_resumes_future_only
~~~

### No replay / no reinitialize / RNG

~~~text
test_resume_does_not_rerun_equipment_setup
test_resume_does_not_reregister_trigger_as_new
test_resume_does_not_reroll_equipment_rng
test_resume_does_not_recreate_remote_live_effect
test_already_settled_damage_and_recovery_unchanged
test_equipment_effectiveness_policy_consumes_zero_rng
test_equipment_contribution_registry_consumes_zero_rng
test_equipment_policy_does_not_emit_event_on_query
~~~

### Architecture / Stage11 regression

~~~text
test_equipment_policy_is_filter_not_domain_calculator
test_equipment_policy_does_not_reorder_damage_modifiers
test_equipment_policy_does_not_own_recovery_ceil
test_no_equipment_inventory_or_slot_runtime_required_for_policy
test_no_stage11_behavior_changes_without_stage12_equipment_cause
test_existing_attribute_damage_recovery_trigger_paths_unchanged_without_equipment_adapter
~~~

These are future production-test obligations only. Round 7 changes zero executable test code and zero gameplay code.

## SF Round 8 planned discriminator suite

Status: DESIGN_FROZEN / NOT IMPLEMENTED.

### Capture Action

~~~text
test_capture_blocks_natural_action
test_capture_block_does_not_consume_stun_block
test_capture_action_denial_creates_no_normal_attack
test_capture_action_denial_creates_no_normal_attack_target_rng
test_capture_removal_allows_future_action_no_replay
~~~

### Damage / Counter / DOT

~~~text
test_capture_blocks_new_actor_driven_damage
test_capture_blocks_counter_damage
test_capture_does_not_block_existing_active_dot
test_free_proxy_damage_not_blocked_by_historical_captured_origin
test_source_id_not_equal_current_actor
test_weakness_and_capture_remain_distinct_damage_semantics
test_counter_batch_admission_not_retroactively_deleted_by_capture
test_capture_damage_denial_admits_no_damage_instance
~~~

### Provider

~~~text
test_capture_suppresses_passive_command_provider
test_capture_source_death_does_not_restore_provider
test_capture_removal_resumes_provider_future_only
test_capture_provider_resume_does_not_replay_trigger
~~~

### Recovery

~~~text
test_capture_received_recovery_zero
test_capture_plus_healing_block_preserves_canonical_recovery_pipeline
test_capture_and_healing_block_can_coexist_as_internal_causes
test_recovery_modifier_second_ceil_precedes_capture_prevention
test_capture_recovery_prevention_precedes_troop_restore_capacity
test_capture_removal_does_not_replay_missed_recovery
test_capture_self_recovery_not_reimplemented_as_target_exclusion
~~~

### Target / locked work

~~~text
test_capture_excludes_verified_friendly_new_query
test_locked_friendly_target_carries_explicit_recheck_boundary
test_locked_target_boundary_does_not_allocate_new_target_operation_id
test_delayed_friendly_work_carries_per_dimension_recheck_spec
~~~

### Execution-right lifecycle

~~~text
test_new_work_and_admitted_work_are_distinct
test_admitted_work_keeps_domain_identity_when_queued
test_attached_work_is_continuation_not_automatic_new_actor_admission
test_target_locked_is_orthogonal_to_queue_state
test_already_admitted_active_permission_not_rechecked_by_exhaustion
test_execution_right_dimensions_can_mix_snapshot_and_jit
test_provider_jit_failure_does_not_requeue
test_execution_jit_failure_does_not_replay_after_resume
test_bounded_damage_request_policy_is_explicit
test_bounded_locked_target_policy_is_explicit
test_bounded_sabotage_queued_policy_is_explicit
test_no_universal_jit_recheck
test_no_universal_snapshot
~~~

### Architecture / ownership

~~~text
test_capture_has_no_universal_runtime_owner
test_domain_owners_remain_canonical
test_future_admission_gate_is_not_capture_permission_owner
test_execution_right_spec_is_rng_free
test_execution_right_system_preserves_stage10_persistent_work_invariant
test_event_bus_does_not_decide_execution_right
test_damage_work_metadata_separates_actor_provider_source_holder_and_target
test_no_universal_work_id_required
~~~

These are future production-test obligations only. Round 8 changes zero executable test code and zero gameplay code.


## SF Round 9 planned RNG / Event / Default governance suite

Status: DESIGN_FROZEN / NOT IMPLEMENTED.

These are future production-test obligations. Round 9 adds zero executable test code.

### RNG ownership / zero-consumption

~~~text
test_insight_rejection_preserves_source_control_rng_parity
test_deterministic_control_under_insight_adds_no_rng
test_state_admission_policy_consumes_zero_rng
test_state_effectiveness_policy_consumes_zero_rng
test_state_conflict_policy_consumes_zero_rng
test_provider_validity_policy_consumes_zero_rng
test_skill_permission_policy_consumes_zero_rng
test_skill_operation_admission_coordinator_consumes_zero_rng
test_skill_target_policy_consumes_zero_rng
test_equipment_effectiveness_policy_consumes_zero_rng
test_state_removal_policy_consumes_zero_rng
test_effectiveness_transition_coordinator_consumes_zero_rng
test_execution_right_evaluation_consumes_zero_rng
test_provider_invalid_skill_consumes_no_activation_rng
test_skill_permission_denied_consumes_no_activation_rng
test_denied_skill_creates_no_target_rng
test_forced_single_provocation_adds_no_target_rng
test_all_candidates_target_selection_adds_no_target_rng
test_intimidation_rejected_before_binding_consumes_no_binding_rng
test_intimidation_refresh_performs_one_authorized_binding_selection
test_intimidation_refresh_same_provider_still_counts_as_selection
test_intimidation_resume_consumes_zero_binding_rng
test_provider_invalid_recovery_consumes_zero_recovery_rng
test_suppressed_equipment_trigger_consumes_zero_downstream_rng
test_execution_right_denial_consumes_zero_downstream_rng
~~~

The Intimidation tests count one binding-selection operation at the RandomSystem service seam.
They do not assert hidden random.Random bit consumption.

### Deterministic replay / trace

~~~text
test_same_seed_same_stage12_rng_trace
test_same_input_same_admission_decisions_same_rng_owner_sequence
test_rejected_path_does_not_shift_later_rng_trace
test_resume_path_does_not_shift_later_rng_trace
test_policy_query_repetition_does_not_shift_rng_trace
~~~

Test instrumentation may wrap/fake the existing RandomSystem seam.
Do not change production RNG semantics merely to expose a trace.

### Provocation BU-P02 governed RNG topology / remaining bounded guards

RD-SF-005 executable discriminators:

~~~text
test_choose_n_required_target_preserves_n
test_choose_n_required_target_exactly_once
test_choose_n_required_target_rng_owner_is_target_system
test_choose_n_policy_consumes_zero_rng
test_choose_n_new_query_replay_deterministic
test_choose_n_subsequent_rng_stream_stable
test_choose_n_n_equals_one_zero_target_draw_if_required_fills_slot
test_inherited_result_does_not_reselect
test_derived_result_does_not_reselect
test_locked_result_does_not_reselect
test_required_target_reserved_before_random_fill
test_random_fill_excludes_required_target
test_random_fill_count_is_n_minus_required_count
test_no_post_selector_replacement
~~~

Still-bounded governance guards:

~~~text
test_provocation_insufficient_candidates_marked_unsupported
test_provocation_multisource_precedence_marked_unsupported
test_intimidation_weights_not_claimed_uniform
test_intimidation_empty_pool_marked_unsupported
test_rd_sf_002_does_not_define_intimidation_weights
~~~

RD-SF-005 tests assert the simulator's explicit project topology, not hidden original-game truth. BU-P09 / BU-P06 and Intimidation unknowns remain boundaries.

### Query vs Event

~~~text
test_repeated_effectiveness_query_emits_no_event
test_repeated_provider_query_emits_no_event
test_repeated_skill_permission_query_emits_no_event
test_repeated_target_policy_query_emits_no_event
test_repeated_equipment_policy_query_emits_no_event
test_execution_right_query_emits_no_event
~~~

### State transition facts

~~~text
test_state_suppressed_transition_emits_once_if_public
test_state_resume_transition_emits_once_if_public
test_suppressed_to_suppressed_emits_no_event
test_resumed_to_resumed_emits_no_event
test_state_suppression_event_occurs_after_dependency_commit
test_state_resume_requires_physical_state_still_present
~~~

### Provider internal transition boundary

~~~text
test_provider_query_emits_no_event
test_provider_internal_transition_does_not_require_public_provider_event
test_provider_resume_does_not_replay_missed_behavior
~~~

### Application rejection facts

~~~text
test_insight_admission_rejection_uses_application_rejected_admission_stage
test_insight_reapplication_conflict_uses_application_rejected_conflict_stage
test_admission_reject_event_distinct_from_conflict_reject_by_payload
test_rejected_candidate_emits_no_state_applied
test_rejected_candidate_emits_no_state_refreshed
test_failed_binding_validation_emits_no_committed_state_event
test_cycle_validation_failure_emits_no_committed_state_event
~~~

### Skill / preparation event facts

~~~text
test_actual_exhaustion_blocked_active_attempt_may_emit_skill_operation_blocked
test_no_active_attempt_no_exhaustion_block_event
test_actual_preparing_interruption_may_emit_preparation_interrupted
test_not_preparing_no_interruption_event
test_interruption_event_occurs_after_preparation_transition
~~~

### Domain event ownership

~~~text
test_capture_action_block_event_owned_by_action_system
test_capture_state_handler_does_not_duplicate_action_blocked
test_capture_damage_prevention_event_owned_by_damage_domain
test_capture_damage_denial_is_not_weakness_legal_zero_event
test_capture_recovery_prevention_event_owned_by_recovery_system
test_capture_plus_healing_block_emits_one_recovery_prevented
test_capture_plus_healing_block_keeps_multiple_internal_causes
test_capture_plus_healing_block_public_primary_reason_preserves_healing_ban_compatibility
~~~

### Target event non-fabrication

~~~text
test_target_policy_query_emits_no_target_event
test_provocation_fixed_all_noop_emits_no_false_forced_target_event
test_provocation_source_already_present_no_duplicate_force_event
test_target_change_event_if_added_is_owned_by_target_resolution_not_policy_query
~~~

### Transaction ordering / idempotence

~~~text
test_state_applied_event_occurs_after_physical_commit
test_state_refreshed_event_occurs_after_refresh_commit
test_transition_event_occurs_after_dependency_recompute
test_failed_transaction_emits_no_applied_or_refreshed_event
test_same_decision_without_transition_emits_no_transition_event
test_event_bus_listener_cannot_be_permission_owner
~~~

### Runtime Default governance

~~~text
test_rd_sf_001_has_required_provenance_and_deterministic_test
test_rd_sf_002_has_required_provenance_and_deterministic_test
test_rd_sf_003_has_required_provenance_and_deterministic_test
test_rd_sf_004_exhaustion_denied_active_rng_placement_has_project_default_provenance
test_rd_sf_005_provocation_choose_n_reserve_first_has_project_default_provenance
test_pd_ins_001_retains_inherited_project_default_label
test_pd_ins_002_retains_inherited_project_default_label
test_no_unledgered_project_runtime_default
test_bounded_unknown_not_automatically_runtime_default
test_round9_adds_no_new_runtime_default
~~~

### Static architecture scans

~~~text
test_no_direct_random_module_use_outside_random_system_infrastructure
test_policy_classes_do_not_consume_battle_context_random
test_event_bus_handlers_do_not_own_permission_decisions
test_all_runtime_defaults_referenced_in_ledger
test_project_runtime_default_comments_have_ledger_ids_or_inherited_default_ids
test_no_stage13_stage14_stage15_gameplay_in_round9
~~~

### Round 9 test-design verdict

~~~text
RNG decision-point coverage = DESIGNED
zero-RNG policy coverage = DESIGNED
replay trace coverage = DESIGNED
event query/transition/ordering/idempotence coverage = DESIGNED
runtime-default provenance coverage = DESIGNED
executable Stage12 Round 9 tests added = 0
gameplay code changed = 0
~~~


## SF Round 10 final test architecture

Authority: STAGE12_SHARED_FOUNDATION_COMPOSITION_AND_TEST_ARCHITECTURE.md

### Layer 1 — Shared Foundation

~~~text
tests/test_stage12_state_admission.py
tests/test_stage12_state_lifecycle_transaction.py
tests/test_stage12_state_effectiveness.py
tests/test_stage12_provider_validity.py
tests/test_stage12_skill_permission.py
tests/test_stage12_target_policy.py
tests/test_stage12_equipment_effectiveness.py
tests/test_stage12_execution_rights.py
tests/test_stage12_rng_governance.py
tests/test_stage12_event_governance.py
tests/test_stage12_wiring.py
tests/test_stage12_architecture_static.py
~~~

### Layer 2 — Seven-state contract suites

~~~text
tests/test_stage12_690089_insight.py
tests/test_stage12_690101_exhaustion.py
tests/test_stage12_690107_false_report.py
tests/test_stage12_690108_provocation.py
tests/test_stage12_690222_intimidation.py
tests/test_stage12_690109_sabotage.py
tests/test_stage12_690110_capture.py
~~~

Minimums remain: FALSE_REPORT >= 30, PROVOCATION >= 25, INTIMIDATION >= 21. The other four states use complete contract-obligation coverage with no invented numeric floor.

### Layer 3 — Cross-state and Stage11 regression

~~~text
tests/test_stage12_cross_state.py
tests/test_stage12_stage11_regressions.py
~~~

Required Stage12 matrix additionally includes FalseReport-source × Provocation as the existing dependency discriminator.

Required Stage11/legacy matrix includes:
STUN × CAPTURE; WEAKNESS × CAPTURE; HEALING_BLOCK × CAPTURE;
CONFUSION × PROVOCATION; TAUNT × PROVOCATION; DISARM × INSIGHT;
STUN × INSIGHT; Damage Pipeline × CAPTURE; Recovery Pipeline × CAPTURE;
INSIGHT × CONFUSION as the AR-SF-01 authority-migration discriminator.

### Layer 4 — Whole-system acceptance

~~~text
full pytest
demo
deterministic replay / RNG trace
static architecture audit
CI
~~~

### Wiring identity tests

~~~text
test_battle_systems_uses_single_state_effectiveness_policy
test_battle_systems_uses_single_provider_validity_policy
test_stage9_stage11_share_same_effective_truth
test_skill_and_recovery_share_same_provider_validity
test_equipment_consumers_share_same_equipment_policy
test_dependency_support_is_shared_and_cycle_safe
test_event_bus_is_shared_but_not_authority
test_production_path_has_no_shared_policy_fallback
test_explicit_test_factory_builds_one_coherent_graph
~~~

### Legacy constructor migration tests

~~~text
test_production_stage9_requires_injected_state_effectiveness_policy
test_production_stage11_requires_injected_state_effectiveness_policy
test_production_skill_resolver_requires_admission_and_target_policies
test_production_recovery_opportunity_uses_injected_provider_validity
test_non_production_fixture_factory_is_explicit
test_fixture_factory_does_not_create_per_consumer_policy_instances
~~~

### Semantic static audits

Use AST/class/call analysis instead of brittle raw-string bans.

~~~text
test_no_shared_policy_constructor_inside_production_consumer
test_state_registry_mutation_is_lifecycle_authorized
test_no_direct_random_module_gameplay_calls
test_no_duplicate_random_system_construction
test_event_handlers_do_not_own_permission
test_no_stage12_state_id_ladder_duplicated_across_consumers
test_no_source_skill_slot_truthiness_gate
test_trigger_system_preserves_inherent_slot_zero_in_provenance_merge
test_no_provider_attribution_dependency_inference
test_no_unledgered_project_runtime_default
test_no_stage13_stage14_stage15_gameplay_leakage
~~~

### Unsupported-boundary tests

~~~text
test_intimidation_empty_pool_is_explicit_boundary
test_intimidation_weights_require_declared_distribution
test_provocation_insufficient_candidates_not_silently_defaulted
test_provocation_multisource_not_silently_defaulted
test_sabotage_unproven_queued_mode_is_explicit_boundary
test_capture_unproven_execution_right_mode_is_explicit_boundary
~~~

### No-regression oracle

For battles without Stage12 states/new metadata: outcome unchanged; event order unchanged; RNG consumption unchanged; canonical owner count unchanged; provenance unchanged; Stage9/10/11 frozen behavior unchanged.

~~~text
four-layer architecture = COMPLETE
seven-state file layout = COMPLETE
cross-state matrix = COMPLETE
Stage11 regression matrix = COMPLETE
wiring/static audit matrix = COMPLETE
contract-to-test traceability = COMPLETE BY DESIGN
unsupported-boundary test policy = COMPLETE
executable Stage12 Round 10 tests added = 0
gameplay code changed = 0

DQ-SF-18 = CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-26 = PENDING
~~~

## Round 11 independent-audit test correction

`AUDIT-DRIVEN CORRECTION`

The duplicated summary matrices at the top of this document now match the Round 10 Layer-3 authority:
- FalseReport-source × Provocation is mandatory.
- INSIGHT × CONFUSION is mandatory as the AR-SF-01 migration discriminator.

RD-SF-004 receives explicit default-provenance and denied-path RNG tests. TriggerSystem receives a targeted slot-0 provenance discriminator in addition to the broad static truthiness audit.

Contract minimums remain unchanged:
- FALSE_REPORT >= 30
- PROVOCATION >= 25
- INTIMIDATION >= 21


## BU-P02 Runtime Governance executable suite — 2026-09-27

```text
tests/test_stage12_690108_bu_p02_runtime_governance.py
```

Scope:

- generic required-target CHOOSE_N selector semantics only;
- reserve-first discriminator;
- policy zero-RNG and TargetSystem RNG ownership;
- supported draw/no-draw topology;
- replay and downstream RNG-stream stability;
- continuation no-reselection;
- no 690108 gameplay adapter registration.

This suite closes the executable gate for RD-SF-005 without implementing PROVOCATION gameplay.


## 690108 Gameplay Integration executable checkpoint — 2026-09-28

```text
tests/test_stage12_690108_provocation.py
```

This is the production Gameplay Integration suite, separate from the BU-P02 governance suite. It covers effective truth, SINGLE, CHOOSE_N under RD-SF-005, FIXED_ALL, source admissibility, fresh-query reevaluation, immutable continuation results, INSIGHT, EXHAUSTION, FALSE_REPORT-source ProviderDependency, attribution negatives, Confusion arbitration metadata, Taunt/NormalAttack separation, source death, event/RNG ownership, production producer mapping, legacy compatibility and static architecture guards.

Validated whole-suite checkpoint:

```text
baseline = 1314 passed
final code/test checkpoint = 1359 passed
delta = +45 test nodes
PROVOCATION minimum = >= 25
demo = PASS
CI = 36333059532 / success
```

Runtime Freeze is not claimed by this integration checkpoint.


## 690108 PROVOCATION Independent Runtime Freeze Audit — 2026-09-28

Executable audit file: `tests/test_stage12_690108_provocation_runtime_freeze_audit.py`.

```text
Independent freeze-audit tests = 33 passed
690108 integration + freeze-audit = 78 passed
RD-SF-005 dedicated regression = 15 passed
Stage9 regression = 427 passed
Stage10 regression = 145 passed
Stage11 regression = 12 passed
690089 regression = 52 passed
690101 regression = 58 passed
690107 regression = 54 passed
Shared Foundation regression = 222 passed
Full pytest = 1392 passed
Demo = PASS
Fresh audit CI = 36334810169 / success
Audit code/test SHA = e0f9e0c24a4c379918c3b9389a67dcfea138ac13
```

Coverage includes NEW_QUERY-only freshness, immutable resolved history, legal Source filtering, SINGLE/CHOOSE_N/FIXED_ALL, exact RD-SF-005 sample topology/downstream RNG state, all five production producer mappings, NormalAttack/Taunt/Confusion separation, INSIGHT/EXHAUSTION/FALSE_REPORT interactions, explicit ProviderDependency versus attribution, source death/lifetime/resume, event silence, canonical wiring, BU-P06 and BU-P09 unsupported-boundary preservation, and Stage12 leakage guards.

Freeze authority: `STAGE12_690108_PROVOCATION_RUNTIME_FREEZE_AUDIT.md`.


## 690222 binding-selection governance suite — 2026-09-28

Executable governance specification:

```text
tests/test_stage12_690222_binding_selection_governance.py
```

Coverage:

- RD-SF-006 provenance is PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN;
- RD-SF-002 stable Provider ordering;
- loaded identity pool is not silently replaced by ProviderValidity filtering;
- one candidate -> deterministic / zero binding RNG;
- multiple candidates -> exactly one canonical RandomSystem.choice;
- same seed + same pool -> same binding;
- downstream RNG stream position is stable;
- rejected application and Gangyi rejection own zero binding RNG by governance contract;
- successful REFRESH performs a new selection;
- same-provider REFRESH is legal and still a new selection operation;
- RESUME retains binding and consumes zero binding RNG;
- empty pool remains UNSUPPORTED_BOUNDARY;
- TALENT remains unsupported/not frozen for 690222 eligibility;
- all supplied candidates are reachable across a deterministic seed set.

This suite is an executable governance specification only. It does not claim that 690222 gameplay has been integrated.


Governance validation: `36369968103 / success / 1409 passed / demo PASS`.
Baseline before RD-SF-006 governance was 1392 passed; net new governance tests = 17.


## 690222 INTIMIDATION Independent Runtime Freeze Audit — 2026-09-28

Executable audit file: `tests/test_stage12_690222_intimidation_runtime_freeze_audit.py`.

```text
Independent freeze-audit tests = 30 passed
Full pytest = 1483 passed
Demo = PASS
Push CI = 36374423908 / success
PR CI = 36374443142 / success
Audit test SHA = 0b3e5d62b1c2e25e4b2177ccfa5dd456819ddc96
Stage12 Runtime Frozen = 5 / 7
NEXT = 690109 SABOTAGE Runtime Integration
```

Coverage independently attacks RD-SF-002 ordering, RD-SF-006 call topology and downstream RNG state, rejected CREATE/Gangyi zero-RNG, full Provider identity, CREATE/REFRESH/RESUME, refresh rollback and dependency-cycle preflight, exact PROVIDER preparation interruption, Insight/FalseReport/Exhaustion/Provocation composition, attribution-vs-dependency, Formation/TALENT/NormalAttack negatives, generic/specialized removal boundaries, source-death non-definition, lifetime, same-envelope settlement, event silence, canonical wiring and TROOP Provider suppression.

TROOP executable Provider identity/binding/suppression is covered. The absence of a separate concrete TROOP execution consumer is a non-blocking audit note; any future TROOP consumer must query canonical ProviderValidity.

Freeze authority: `STAGE12_690222_INTIMIDATION_RUNTIME_FREEZE_AUDIT.md`.
