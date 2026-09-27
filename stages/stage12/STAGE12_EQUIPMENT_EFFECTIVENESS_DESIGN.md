# Stage12 Equipment Effectiveness / Sabotage Provider Architecture Design

Date: 2026-09-27
Round: STAGE12_SF_ROUND7_EQUIPMENT_EFFECTIVENESS_DESIGN
Status: DESIGN FROZEN FOR DQ-SF-11; SHARED FOUNDATION NOT YET FROZEN
Gameplay implementation in this round: NONE

## 1. Repository and authority lock

Round 7 starts from:

- Battle main: 180f5142648ee74cfe60f747300e8c67c95187b9
- Research main: e18ae56a4db5662b87458dfa8fdff25dcdd8053b
- 690109 SABOTAGE: Research FROZEN / Contract v1.0-frozen
- 690107 FALSE_REPORT: Research FROZEN / Contract v1.0.1-frozen
- 690110 CAPTURE: Research FROZEN / Contract v1.0-frozen
- 690089 INSIGHT: Research FROZEN / Contract v0.4-frozen

This round is design/docs only. It does not implement SABOTAGE, an equipment runtime, equipment storage, equipment inventory/slots, or Stage13/14/15 gameplay.

## 2. Canonical invariant

~~~
Equipment exists
!=
Equipment contribution is currently effective
~~~

Transient suppression MUST NOT be represented as physical unequip, object deletion, slot clear, Provider removal, baseline-enabled mutation, reinstall, or setup replay.

The equipment object and Provider identity remain stable. Only the current authority of a concrete equipment-owned contribution changes.

## 3. Reused frozen Shared Foundation facts

1. EquipmentProviderRef(owner_id, provider_key) is stable typed Provider identity and is not SkillProviderRef.
2. ProviderValidityPolicy owns generic Provider validity after identity resolution.
3. Attribution is not dependency. EffectSourceRef alone never creates a live Provider dependency.
4. StateEffectivenessPolicy is the canonical source of whether resident SABOTAGE/CAPTURE/FALSE_REPORT currently owns gameplay authority.
5. Suppression causes compose as an independent set.
6. Resume is future-only and never rewinds settled facts or replays missed opportunities.
7. Existing domain owners retain arithmetic, ordering, scheduling and RNG.

## 4. Canonical owner topology

~~~
EquipmentContributionRegistry / read-only adapter
        |
        v
EquipmentProviderRef identity resolution
        |
        v
ProviderValidityPolicy
        |
        v
EquipmentEffectivenessPolicy
        |
        +--> AttributeSystem / AttributeModifierProvider
        +--> DamageRuleProvider
        +--> RecoveryModifierProvider
        +--> equipment trigger adapter / TriggerSystem path
        +--> explicit equipment-dependent live effects
~~~

There is exactly one final truth for a concrete equipment contribution:
EquipmentEffectivenessPolicy.evaluate_contribution(...).

Consumers do not choose between two validity booleans. Generic Provider validity is an input to the final equipment-contribution decision.

## 5. Equipment identity and contribution representation

### Provider identity

~~~
EquipmentProviderRef(
    owner_id,
    provider_key,
)
~~~

provider_key is stable, deterministic, serializable and battle-semantic. Python id(), object pointers, process hashes and call-stack identity are forbidden.

Equipment remains a distinct Provider category. It never receives fake SkillType, SkillSlot or skill_id metadata.

### Contribution kind

Minimum Stage12 taxonomy:

~~~
EquipmentContributionKind:
    ATTRIBUTE
    DAMAGE_MODIFIER
    RECOVERY_MODIFIER
    TRIGGER
    SCHEDULED_TRIGGER
    LIVE_EFFECT
~~~

This is deliberately not a full equipment-system taxonomy.

### Contribution reference

~~~
EquipmentContributionRef:
    provider_ref: EquipmentProviderRef
    contribution_key: str
    kind: EquipmentContributionKind
~~~

contribution_key is stable within the Provider. A simple adapter may reuse provider_key when one Provider exposes exactly one contribution. Multiple contributions require distinct stable keys. Domain-native order/source keys remain domain-owned.

The complete EquipmentContributionRef is the live-dependency identity.

## 6. Minimal EquipmentContributionRegistry

Stage12 needs only a read-only contribution adapter/registry capable of:

~~~
resolve(EquipmentContributionRef)
enumerate_for_owner(owner_id)
enumerate_for_domain(owner_id, kind)
~~~

It may resolve known contribution identity, expose baseline metadata, and enumerate current configured contribution records.

It does NOT own physical inventory, equip/unequip, slots, loadout mutation, attributes, damage math, recovery math, triggers, state lifecycle, or RNG.

No EquipmentInventorySystem, EquipmentSlotSystem, EquipmentRuntimeRegistry, or Stage12 equipment god object is created.

## 7. ProviderValidityPolicy vs EquipmentEffectivenessPolicy

Frozen responsibility split:

~~~
ProviderValidityPolicy:
    Is this stable EquipmentProviderRef generically present and valid?

EquipmentEffectivenessPolicy:
    May THIS resolved equipment-owned contribution participate in THIS domain now?
~~~

Generic Provider outcomes remain VALID / SUPPRESSED / BASELINE_DISABLED / MISSING / IDENTITY_MISMATCH.

Equipment contribution outcomes are:

~~~
EFFECTIVE
SUPPRESSED
BASELINE_DISABLED
MISSING
IDENTITY_MISMATCH
UNSUPPORTED_BOUNDARY
~~~

UNSUPPORTED_BOUNDARY is required so bounded research evidence is not silently converted to ALLOW or DENY.

## 8. Canonical API

Equivalent interface:

~~~
evaluate_contribution(
    context,
    contribution_ref: EquipmentContributionRef,
) -> EquipmentEffectivenessDecision
~~~

Minimum result:

~~~
EquipmentEffectivenessDecision:
    contribution_ref
    status
    suppression_causes
    boundary_reasons
~~~

is_effective(...) may exist only as a derivation of evaluate_contribution(...).

The policy consumes zero RNG, performs no mutation, owns no domain arithmetic, and emits no public event merely because it is queried.

## 9. Evaluation algorithm

~~~
1. resolve EquipmentContributionRef
2. resolve generic EquipmentProviderRef validity
3. propagate MISSING / IDENTITY_MISMATCH / BASELINE_DISABLED
4. derive all contract-authorized equipment suppression causes
5. preserve material evidence-scoped unsupported boundaries
6. if one or more known causes exist -> SUPPRESSED
7. else if unresolved boundary prevents a lawful answer -> UNSUPPORTED_BOUNDARY
8. else -> EFFECTIVE
~~~

Known suppression and a bounded unknown may coexist diagnostically. When the final known cause disappears, a remaining unresolved boundary becomes UNSUPPORTED_BOUNDARY, not guessed EFFECTIVE.

## 10. Multi-reason suppression

Equipment suppression causes are stable values keyed by rule and state-instance/application-generation identity. Cause order has no gameplay authority.

Forbidden mutable model:

~~~
equipment.enabled = False
remove_one_cause()
equipment.enabled = True
~~~

Required composition:

~~~
Sabotage + FalseReport-tested cause
-> SUPPRESSED

remove Sabotage
-> still SUPPRESSED

remove final cause
-> resume only if otherwise eligible
~~~

Reverse removal order produces the same net truth.

## 11. SABOTAGE mapping

690109 freezes target-owned tested equipment contribution suppression.

~~~
effective SABOTAGE on owner U
+
contribution.provider_ref.owner_id == U
+
contribution within frozen tested SABOTAGE scope
-> SABOTAGE suppression cause
~~~

This is owner-wide across the tested contribution scope, not a one-selected-equipment model.

Mapped tested kinds:
ATTRIBUTE, DAMAGE_MODIFIER, RECOVERY_MODIFIER, deterministic TRIGGER, SCHEDULED_TRIGGER, and tested provider-dependent LIVE_EFFECT.

Untested future topology remains bounded.

## 12. SABOTAGE x INSIGHT

Only EFFECTIVE Sabotage contributes the equipment cause.

~~~
contribution EFFECTIVE
-> Sabotage resident/effective
-> contribution SUPPRESSED

-> effective Insight suppresses Sabotage
-> same Sabotage remains resident
-> Sabotage equipment cause disappears
-> contribution resumes if no other cause

-> Insight ends
-> same still-live Sabotage becomes effective
-> contribution SUPPRESSED again

-> Sabotage ends
-> cause disappears
-> contribution resumes if otherwise eligible
~~~

No equipment object is removed, reinstalled or recreated.

## 13. FALSE_REPORT equipment boundary

690107 does not authorize blanket equipment suppression.

Effective FALSE_REPORT contributes an equipment cause only for the tested persistent Equipment Special scope recorded by the frozen contract.

Untested equipment special/category behavior is UNSUPPORTED_BOUNDARY, not blanket suppress and not blanket allow.

The tested specials remain equipment specials; they are not reclassified as PASSIVE or COMMAND.

## 14. CAPTURE equipment boundary

690110 directly freezes only tested equipment attribute contribution suppression/resume.

~~~
effective CAPTURE
+
kind == ATTRIBUTE
+
verified Capture equipment-attribute scope
-> Capture equipment suppression cause
~~~

Equipment reactive/damage special remains Q63 BOUNDED_UNKNOWN / INFERRED and maps to UNSUPPORTED_BOUNDARY.

Capture is not generalized into Sabotage-lite.

## 15. Static attribute integration

Current AttributeSystem._get is query-time and has no attribute-result cache.

Future seam:

~~~
AttributeSystem._get
-> composite AttributeModifierProvider
-> enumerate equipment ATTRIBUTE contributions
-> EquipmentEffectivenessPolicy
-> include EFFECTIVE contributions only
-> existing attribute calculation returns result
~~~

No UnitRuntime base stat is mutated. Do not subtract on suppression and add on resume.

Because current runtime has no attribute cache, Round 7 adds no cache invalidation owner/default. A future cache must invalidate on transition without becoming the truth owner.

## 16. Damage modifier integration

Current DamageRuleProvider.collect builds per-request contributions and domain ordering remains encoded by phase/order_key.

~~~
DamageRuleProvider.collect
-> equipment DAMAGE_MODIFIER adapter
-> EquipmentEffectivenessPolicy
-> include only EFFECTIVE
-> preserve original phase/order_key
-> existing DamageSystem owns calculation
~~~

EquipmentEffectivenessPolicy never reorders modifiers. SABOTAGE is never hard-coded into DamageSystem. Settled historical damage is never recalculated or rolled back.

## 17. Recovery modifier integration

RecoveryModifierProvider supplies ExactRatio and RecoverySystem owns the canonical second CEIL.

~~~
RecoveryModifierProvider/composite
-> enumerate RECOVERY_MODIFIER contributions
-> EquipmentEffectivenessPolicy filter
-> existing composition produces ExactRatio
-> RecoverySystem performs existing second CEIL
~~~

RecoverySystem contains no if-sabotage equipment branch. HealingBlock ordering and rounding stay unchanged. Settled recovery is not rolled back or replayed.

## 18. Deterministic trigger model

A deterministic equipment-trigger opportunity while the contribution is suppressed produces no gameplay behavior.

Authoritative gate:

~~~
trigger opportunity
-> EquipmentContributionRef
-> EquipmentEffectivenessPolicy
-> EFFECTIVE: trigger owner continues
-> SUPPRESSED: skip this opportunity
~~~

If collection and execution are atomic, one evaluation is sufficient. Collection-time filtering may be an optimization, never a second truth.

Collected-then-queued/in-flight work whose validity changes before execution remains DQ-SF-23 / B-SAB-07 unless the contract directly freezes that micro-slice.

## 19. Scheduled trigger model

690109 directly freezes the tested due-window result:

~~~
scheduled opportunity due while contribution suppressed
-> no execution
-> window is missed/consumed
-> no queue for restoration
-> next future legal scheduled window may work
~~~

A scheduled opportunity therefore carries stable EquipmentContributionRef and checks current effectiveness at the due/execution boundary.

The scheduled object need not be deleted. Creation-vs-execution micro-order outside the tested due-window evidence remains DQ-SF-23.

## 20. No replay / no reinitialize

Resume means only future eligibility.

It never:
- backfills missed triggers;
- merges missed windows into a restoration tick;
- reruns battle-start setup;
- re-registers a trigger as a new trigger merely to restore it;
- reapplies permanent initialization deltas;
- rerolls equipment RNG;
- recreates remote live effects;
- manufactures a new Provider identity;
- rolls back settled damage/recovery.

## 21. Remote live-effect model

Remote still-live behavior records explicit dependency:

~~~
EquipmentContributionDependency(
    contribution_ref: EquipmentContributionRef,
    rule_id,
)
~~~

Example:

~~~
Equipment Owner A -> contribution E -> live effect on Holder B
E becomes SUPPRESSED -> B's E-dependent effect temporarily ineffective
unrelated Provider/contribution on B -> unaffected
~~~

EffectSourceRef or provenance alone never creates this dependency.

The dependent effect's own lifetime continues. If it expires while suppressed, later resume cannot resurrect it.

## 22. Owner / Holder / Target separation

Equipment Owner, Effect Holder, and current Target are distinct identities.

Suppressing A's equipment does not suppress B's own equipment merely because B holds an A-owned effect. A holder-scoped state on B does not reach upstream Provider A without explicit contract authority/dependency.

## 23. Baseline vs current effectiveness

At least four facts remain separate:

~~~
physical/configured presence
baseline Provider enabled/eligible
generic Provider validity
concrete contribution effectiveness
~~~

Transient Stage12 suppression never overwrites baseline configuration.

## 24. Provider death, empty equipment and equipment change

Round 7 does not invent owner-dead => equipment-missing.

Liveness affects a contribution only through an explicit contract/dependency.

Zero matching equipment contributions is valid and must not crash.

B-SAB-09 dynamic equipment-change / empty-equipment state semantics remain bounded. No dynamic equipment system is built to answer them.

## 25. Contribution ordering

EquipmentEffectivenessPolicy is a filter, not an ordering authority.

Ordering stays with the Attribute modifier owner, DamageRuleProvider, Recovery modifier owner, and trigger/scheduler owner.

No equipment ordering Runtime Default is added.

## 26. RNG ownership

~~~
EquipmentEffectivenessPolicy RNG = 0
EquipmentContributionRegistry RNG = 0
~~~

If a future equipment trigger owns RNG, that RNG remains trigger-owned. A contractually skipped opportunity does not consume downstream trigger RNG.

Broader DQ-SF-12 ordering remains open.

## 27. Event governance

Policy queries emit no event.

Public equipment-suppressed/resumed event vocabulary remains DQ-SF-13. EventBus records already-decided facts and never decides contribution effectiveness.

## 28. Current Runtime seam audit

| Runtime | Current fact | Round 7 mapping |
|---|---|---|
| AttributeSystem._get | query-time modifier provider, no current cache | filter equipment attributes at query-time adapter |
| DamageRuleProvider.collect | per-request immutable collection | filter equipment damage contributions before collection result |
| RecoveryModifierProvider | injected ratio provider | filter equipment recovery contributions before aggregate ratio |
| RecoverySystem | owns second CEIL | unchanged |
| TriggerSystem | currently State-based intent collection | future equipment trigger adapter supplies contribution identity |
| EffectSourceRef | provenance only | never live equipment dependency |
| EffectExecutor | routes Effects to existing domain owners | unchanged |
| BattleSystems | composition root | future wiring under DQ-SF-17 only |

No production class changes in Round 7.

## 29. JIT / snapshot mapping

| Kind | Canonical effectiveness check | Boundary |
|---|---|---|
| ATTRIBUTE | query-time | symmetric suppress/resume without mutation |
| DAMAGE_MODIFIER | per damage-request collection | settled damage unchanged |
| RECOVERY_MODIFIER | per recovery-modifier collection | RecoverySystem keeps CEIL |
| TRIGGER | opportunity execution/admission | queued micro-slice remains DQ-SF-23 if unproven |
| SCHEDULED_TRIGGER | due/execution JIT | tested suppressed due window is missed/no replay |
| LIVE_EFFECT | live authority/use query via explicit dependency | lifetime continues while ineffective |

## 30. Stage11 regression boundary

Without a Stage12 equipment suppression cause:
- AttributeSystem behavior unchanged;
- DamageRuleProvider ordering unchanged;
- RecoveryModifierProvider and second CEIL unchanged;
- TriggerSystem State behavior unchanged;
- RNG stream unchanged;
- event order unchanged;
- Stage9/10/11 frozen behavior unchanged.

Stage11 Reopen Required = NO.

## 31. Required discriminator tests

Identity / retention:
- test_equipment_provider_ref_is_stable_value_identity
- test_equipment_contribution_ref_is_serializable
- test_equipment_provider_is_not_skill_provider
- test_sabotage_does_not_remove_equipment_provider
- test_resume_uses_same_equipment_provider_identity
- test_zero_equipment_contributions_is_safe

Attributes:
- test_sabotage_suppresses_equipment_attribute_without_mutating_base_stat
- test_insight_suppresses_sabotage_and_same_attribute_resumes
- test_insight_end_reactivates_same_sabotage_and_attribute_suppresses_again
- test_sabotage_end_restores_attribute_without_cumulative_drift

Damage / recovery:
- test_sabotage_excludes_equipment_damage_modifier_per_request
- test_damage_modifier_order_key_unchanged_by_equipment_filter
- test_settled_damage_never_rolls_back
- test_sabotage_excludes_equipment_recovery_modifier
- test_recovery_second_ceil_owner_unchanged
- test_past_recovery_not_replayed_on_resume

Trigger / schedule:
- test_equipment_trigger_window_skipped_while_sabotaged
- test_equipment_trigger_fires_on_future_window_after_resume
- test_skipped_trigger_window_never_replays
- test_scheduled_due_window_suppressed_at_execution
- test_scheduled_resume_does_not_backfill
- test_collected_then_queued_trigger_remains_DQ_SF_23_boundary

Remote dependency:
- test_remote_equipment_effect_requires_explicit_contribution_dependency
- test_owner_equipment_suppression_makes_remote_effect_ineffective
- test_remote_holder_unrelated_provider_unaffected
- test_remote_effect_resume_uses_same_live_effect
- test_remote_effect_expired_while_suppressed_never_resurrects
- test_effect_source_ref_alone_does_not_create_equipment_dependency

Evidence scope / composition:
- test_false_report_tested_equipment_special_is_suppressed
- test_false_report_untested_equipment_category_is_explicit_boundary
- test_capture_verified_equipment_attribute_is_suppressed
- test_capture_equipment_reactive_damage_is_explicit_boundary
- test_sabotage_plus_false_report_remove_sabotage_still_suppressed
- test_capture_plus_sabotage_remove_capture_still_suppressed
- test_final_known_cause_removed_with_unresolved_boundary_does_not_silently_allow
- test_final_cause_removal_resumes_future_only

Architecture / RNG:
- test_equipment_effectiveness_policy_consumes_zero_rng
- test_equipment_contribution_registry_consumes_zero_rng
- test_equipment_policy_does_not_emit_event_on_query
- test_equipment_policy_does_not_reorder_damage_modifiers
- test_equipment_policy_does_not_own_recovery_ceil
- test_no_equipment_inventory_or_slot_runtime_required_for_policy
- test_no_stage11_behavior_changes_without_stage12_equipment_cause

These are future production-test obligations only. Round 7 adds no executable test code.

## 32. Runtime defaults

New Runtime Defaults added in Round 7: NONE.

Contribution order remains domain-owned. DQ-SF-23 queued micro-order remains bounded. FalseReport untested equipment and Capture reactive/damage remain unsupported boundaries. No gameplay-facing equipment enumeration order/weighting or RNG default is invented.

RD-SF-001, RD-SF-002 and RD-SF-003 remain the complete Shared Foundation Runtime Default set.

## 33. DQ-SF-11 verdict

~~~
DQ-SF-11
= CLOSED_BY_SHARED_FOUNDATION_DESIGN
~~~

This closes the owner/representation/seam architecture only. It does not erase:
- Sabotage B-SAB-07 queued/JIT bounded micro-order;
- FalseReport B-U04 untested equipment categories;
- Capture Q63 reactive/damage equipment behavior;
- Sabotage B-SAB-09 dynamic equipment-change / empty-equipment debt.

## 34. Round 7 exit

~~~
EquipmentEffectivenessPolicy owner = FROZEN
EquipmentProviderRef identity = RETAINED
Equipment contribution model = FROZEN
suppression != unequip = FROZEN
resume != reinitialize = FROZEN
no replay = FROZEN
attribute seam = MAPPED
damage modifier seam = MAPPED
recovery modifier seam = MAPPED
trigger/scheduled seam = MAPPED
remote provider dependency = MAPPED
FalseReport equipment scope = PRESERVED
Capture equipment scope = PRESERVED
Sabotage tested equipment architecture = MAPPED
EquipmentEffectivenessPolicy RNG = 0
Stage11 Reopen Required = NO
Gameplay Implementation = NONE
Stage12 Runtime Frozen = 0 / 7
Stage13 Active = NO
Stage14 Active = NO
Stage15 Active = NO
~~~

Shared Foundation Design Freeze remains NOT YET.

## 35. Next design round

Priority: DQ-SF-19 / DQ-SF-23.

Theme: Capture Composite Execution + Admitted / Queued / JIT Recheck Boundary.

State Effectiveness, Provider Validity, Skill Permission, Target Policy and Equipment Effectiveness now have named canonical owners, so Capture can be the composite pressure test without creating a Capture god object.
