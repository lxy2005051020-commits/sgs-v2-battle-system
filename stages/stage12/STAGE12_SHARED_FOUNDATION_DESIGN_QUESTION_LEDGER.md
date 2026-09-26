# Stage12 Shared Foundation Design Question Ledger

Date: 2026-09-27. Scope: SF-0, first-round design questions, **NOT DESIGN FREEZE**.
Authority and code baseline: [Reconnaissance](STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md).

Statuses describe closure of a design question, not mechanism Research Freeze:

- CLOSED_BY_EXISTING_ARCHITECTURE: existing canonical owner resolves the stated question.
- DESIGN_REQUIRED: evidence is sufficient, but interface/composition decision remains.
- CONTRACT_DEPENDENT: bounded or external contract boundary must be preserved/qualified.
- BLOCKED: a concrete incompatible authority prevents closure without explicit resolution.
- CLOSED_BY_AUTHORITY_MIGRATION: a later canonical authority explicitly supersedes the conflicting historical rule.
- CLOSED_BY_SCOPED_SUPERSESSION: the exact affected historical scope is named and unaffected frozen scope is preserved.
- CLOSED_BY_SHARED_FOUNDATION_DESIGN: the representation needed by downstream Shared Foundation design is fixed; this is not Runtime Freeze.
- CLOSED_BY_PROVENANCE_QUALIFICATION: cross-contract outcome and evidence provenance are both explicitly preserved.

## 1. Mandatory question ledger

| ID | Question / evidence | Status | Candidate owner and required next decision | Dependencies / acceptance discriminator |
|---|---|---|---|---|
| DQ-SF-01 | Who admits incoming state? Lifecycle.apply mutates, Stage11 policy only checks conflict | DESIGN_REQUIRED | State admission policy queried by Lifecycle; define validation vs immunity vs conflict order; mutation only Lifecycle | 02,03,14,22; rejection changes no old instance/timer and emits no applied/removed pair; source RNG preserved |
| DQ-SF-02 | Who answers effective state across Stage9/11/12? | DESIGN_REQUIRED | Shared StateEffectivenessPolicy candidate; Stage9/11 delegate common truth while retaining domain arbitration | 05,08,15,20; suppressed Insight cannot suppress Taunt; no policy in Registry |
| DQ-SF-03 | How represent Resident / Effective / Suppressed / Removed? | DESIGN_REQUIRED | Residency from Registry; minimal typed decision with reason(s), state/provider identity only when useful; operation-inadmissible distinct | 02,08; removal of one reason cannot restore while another remains; expired state never resumes |
| DQ-SF-04 | Minimal SkillType, preparation characteristic, and ProviderCategory? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | SkillDefinition metadata: SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION + PreparationMode NONE/REQUIRED; PREPARATION_ACTIVE = ACTIVE+REQUIRED; NORMAL_ATTACK remains operation; equipment special remains separate ProviderCategory | See STAGE12_SKILLTYPE_PROVIDER_IDENTITY_DESIGN.md; legacy compatibility default RD-SF-001; no execution chain |
| DQ-SF-05 | Stable provider identity and enumeration? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Typed ProviderRef union: SkillProviderRef(owner_id, slot, skill_id) + EquipmentProviderRef(owner_id, provider_key); Registry resolves skill key and expected ID; deterministic enumeration RD-SF-002 | 04,21; same skill on two owners/slots distinct; slot 0 valid; serialization/replay; missing vs mismatch explicit |
| DQ-SF-06 | Skill permission API and canonical admission point? | DESIGN_REQUIRED | SkillPermissionPolicy.can_admit candidate, invoked by explicit operation admission before observable activation; do not recheck activated child chain as new skill | 04,08,12,13; one holder-level Exhaustion block, no-active silent, Basic/Assault unaffected; no Stage14 loop |
| DQ-SF-07 | Preparation interruption port and state ownership? | DESIGN_REQUIRED | Future preparation owner stores progress; Stage12 requests unit-wide Active or selected Provider interruption through a minimal injected port; define no-op/fake and synchronously triggered transitions | 05,06,08,20; effective Exhaustion interrupts now, selected Intimidation interrupts only that provider, no missed progress replay; no Stage15 scheduler |
| DQ-SF-08 | Provider validity query and dependency propagation? | DESIGN_REQUIRED | ProviderValidityPolicy.evaluate candidate; compose baseline enabled and independent suppression causes; ongoing dependencies explicit, never infer all from source_id | 02,04,05,20,21; A suppressed/B holder vs B suppressed/A effective; final cause removal only resumes future live behavior |
| DQ-SF-09 | Target Operation model? | DESIGN_REQUIRED | TargetSystem primitives + Skill target policy seam; model relation, cardinality, selector, legal context and target provenance as separate dimensions | 04,05,10; single/random/deterministic/Choose-N/Fixed-All, friendly/healing/self; closed Duel admissibility |
| DQ-SF-10 | What creates a new target operation? | DESIGN_REQUIRED | SkillResolver/explicit operation producer declares fresh independent query; inherited/derived targets carry prior resolution identity and no implicit recheck | 09,12,23; locked multihit vs independent multi-query; source inclusion never reduces N |
| DQ-SF-11 | Minimal equipment effectiveness abstraction? | DESIGN_REQUIRED | New minimal EquipmentEffectivenessPolicy; existing AttributeSystem/DamageRuleProvider/RecoveryModifierProvider/TriggerSystem consume owner-bound contributions | 05,08,20; static attributes, damage/recovery modifiers, deterministic/scheduled trigger, local/remote live effects, object retained/no replay |
| DQ-SF-12 | Who consumes RNG, when and for what? | DESIGN_REQUIRED | RNG owner already closed: context.random/RandomSystem. Source operation owns application probability, selector owns target sampling, accepted Intimidation binding owns selection; signatures/ordering/defaults unresolved | 01,06,09,14,22; PD-INS-001 parity; refresh actual reroll vs same result; resume zero reroll; rejected immunity no binding selection |
| DQ-SF-13 | Minimal events and explicit decisions? | DESIGN_REQUIRED | Domain owners publish after decision; reuse ACTION_BLOCKED/RECOVERY_PREVENTED where truthful; evaluate rejection and transition facts, don't emit on every query | 01,03,06,07,20; duplicate read produces no repeated transition; Provocation execution not automatically TARGET_FORCED |
| DQ-SF-14 | Which runtime defaults are required and where recorded? | CONTRACT_DEPENDENT | Runtime Default Ledger required before choices are frozen; carry exact research labels and section IDs; inherit PD-INS-001/002 verbatim in substance | All DQs; every necessary unsupported choice gets reason, chosen value, scope, reopen trigger, tests; no silent default |
| DQ-SF-15 | How migrate actual 690089 PARTIAL? | CLOSED_BY_AUTHORITY_MIGRATION | STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md establishes later Insight v0.4 authority and explicit future test replacement; identity/lifecycle/Taunt scope preserved | 02,16; implementation still pending, but authority blocker is closed |
| DQ-SF-16 | Stage11 and older frozen regression boundary? | CLOSED_BY_SCOPED_SUPERSESSION | P0-CFS-P93-01/P93-B01 superseded only for existing Confusion remaining operational after later effective Insight; all enumerated unaffected Stage9 rules preserved; Stage11 Reopen Required NO | 15,24; any future clock contradiction requires a separately proven scoped reopen |
| DQ-SF-17 | BattleSystems wiring and compatibility paths? | DESIGN_REQUIRED | Composition root constructs one shared dependency graph, injects consumers and ports; legacy standalone constructors must not create second policy truth | 02,05,08,20; same policy instance for production consumers, explicit dependency failure, no EventBus backdoor |
| DQ-SF-18 | Test architecture and model discriminators? | DESIGN_REQUIRED | Foundation tests + seven state files + cross-state suite; current 913 tests are baseline, not Stage12 coverage | All DQs; exact contract sections→future test cases; 30/25/21 minima retained; AST owner/RNG scans; independent design audit later |

## 2. Additional questions required by code and contracts

| ID | Question | Status | Owner / next decision | Acceptance boundary |
|---|---|---|---|---|
| DQ-SF-19 | Capture composite action/damage/recovery/target permission | DESIGN_REQUIRED | ActionSystem, DamageSystem stack, RecoverySystem, target policy, ProviderValidityPolicy own separate decisions; decide result topology and concurrent reason reporting | Counter blocked vs attached Active DOT continues; free proxy actor remains legal; friendly single/2-target excluded; self recovery arrives but zero; equipment attributes only proven scope |
| DQ-SF-20 | Cyclic dependencies and immediate transitions | DESIGN_REQUIRED | Shared effective/provider query graph must define bounded evaluation and synchronous transition application; detect cycles rather than recurse indefinitely or invent fixed-point truth | Example source-provider suppression→Intimidation ineffective→selected Provider resumes→provider-derived Insight changes; overlapping causes stable; no replay; cycle fallback requires ledger if needed |
| DQ-SF-21 | Existing JIT source-gate migration and slot 0 | DESIGN_REQUIRED | Identity obligation is fixed by DQ-SF-05: explicit slot is-not-None, expected skill ID validation, missing/mismatch distinction; implementation must delegate current effectiveness to ProviderValidityPolicy | INHERENT=0 lookup, mismatch, missing, suppression and no-RNG rejection remain implementation discriminators |
| DQ-SF-22 | Application result, refresh transaction, binding atomicity | DESIGN_REQUIRED | Lifecycle sole physical writer; admission/conflict decisions pure where possible; binding resolver consumes RNG only after allowed path | No half-released old binding on failure; refresh selects one, resume preserves binding; direct refresh cannot bypass policy; old API ValueError vs rejected outcome adapter explicit |
| DQ-SF-23 | Admitted/queued work vs JIT recheck | CONTRACT_DEPENDENT | Owning operation + execution-right system preserve admission identity; distinguish new operation from continuation | Exhaustion in-flight Active no rollback; Stage9 Counter admitted-entry invariant; Capture Q16/Q44/Q45 and Sabotage B-SAB-07 remain bounded until default/authority disposition |
| DQ-SF-24 | Clock continuation during suppression | DESIGN_REQUIRED | Lifecycle physical mutation; explicit clock semantics and Stage11 maintenance delegation; never route all Stage12 durations through Stage10 detector | STUN block counter versus lifetime; FalseReport representative holder-action timeline; Intimidation suspended expiry; no clock pause; incompatible legacy expectation triggers scoped review |
| DQ-SF-25 | Cleanse eligibility, strength, reapplication and source death | CONTRACT_DEPENDENT | Removal-selection policy separate from Lifecycle.remove primitive; per-contract inputs; source-dependent flags cannot be universal | Capture ordinary cleanse resistant; Intimidation tested generic removal fails, specialized unknown; FR/SAB equal no refresh; Capture/Provocation/Intimidation multi-source labels preserved |
| DQ-SF-26 | Design Freeze audit owner and gate | DESIGN_REQUIRED | Independent audit after full design, with seven contracts, concrete API mapping, defaults, tests and risk register; no freeze audit claim in SF-0 | 17 requested audit checks; no blocking owner/conflict, no Stage13+ leakage; architecture freeze distinct from 0/7 Runtime |
| DQ-SF-27 | Physical state write and RNG service ownership | CLOSED_BY_EXISTING_ARCHITECTURE | StateLifecycleSystem writes; StateRegistry stores; BattleContext.random is sole random source; EventBus records | Consumers delegate/query; no second lifecycle, no direct random.*, no permission decisions in event handlers |
| DQ-SF-28 | Intimidation × Insight evidence labels across contracts | CLOSED_BY_PROVENANCE_QUALIFICATION | Runtime uses Intimidation §§5,11 as positive authority while Insight retains SPECIAL_CASE_SUPPORTED / DIRECT_OVERLAP_UNOBSERVED provenance; Research files are not rewritten | Ordinary Insight non-rejection is usable without falsely claiming direct Insight-corpus observation |

## 3. Default candidates and preserved non-claims

Round 2 has started STAGE12_RUNTIME_DEFAULT_LEDGER.md with only two defaults that are actually required now:
RD-SF-001 legacy SkillDefinition classification compatibility and RD-SF-002 deterministic loaded Skill Provider enumeration.
No Intimidation weighting or empty-pool default is selected. Future choices must use the same fields and the labels
PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN.

| Authority | Already governed or unresolved items to carry into design |
|---|---|
| Insight §§6,10,24 | Inherit PD-INS-001 and PD-INS-002; B-INS-01/02/08 stay project defaults; B-INS-05 Intimidation provenance; B-INS-06 provider death and B-INS-07 exotic proxy dependencies |
| Exhaustion §18 | B-EXH-01 RNG, 02 candidate/admission node, 03 same-action reopening, 04 exotic independent admission, 05 unavailable native 100% discriminator |
| FalseReport §17 | B-U01 stronger/weaker, 02 unseen immunity, 03 special scenario, 04 untested equipment; tested equipment list is not a universal category |
| Provocation §23 | BU-P01 RNG, 02 Choose-N slots, 03 environment, 04 rare source invalidity, 05 already-selected timing, 06 multisource/reapply, 07 immunity, 08 other fixed contexts, 09 insufficient count, 10 allegiance, 11 same-window order |
| Intimidation §§5,16,18 | Selection weights unproven; empty eligible pool/ordering must be considered; BU-01 source death, 02 permanent removal, 03 multisource, 04 transfer, 05 extension, 06 specialized removal, 07 equipment, 08 bingshu, 09 version provenance, 10 refresh while source invalid; source counter stays SOURCE_SKILL_SCOPE |
| Sabotage §18 | B-SAB-01 genuine counters, 02 stronger/multisource, 03 internal representation, 04 exotic remote topology, 05 removal classes, 06 cross-state overlap, 07 JIT/queued/order timing, 08 death/source lifecycle, 09 empty equipment/change; §14 counter preservation is safety default, not observed fact |
| Capture §23 | Q16 created damage, Q23 detached passive state, Q34 Emergency Aid, Q42 ALL_ALLIES, Q44 delayed/Q45 locked friendly work, Q63 equipment damage, Q70–74 state reapply/multisource, Q78 death cleanup, hidden universal damage gate non-claim |

For each item, later design must choose **inherit / explicit default / unsupported boundary /
delegate to named contract**. It need not invent behavior for every unimplemented future mechanic.
Unsupported boundary failures must be explicit; silent ALLOW or global suppression is not closure.

## 4. Test architecture work package (planned, not implemented)

| Proposed test file | Concrete discriminator cases to map |
|---|---|
| `tests/test_stage12_state_admission.py` | `test_reject_preserves_old_instance_and_timer`, `test_control_proc_rng_precedes_insight_admission`, `test_rejected_child_does_not_abort_siblings`, `test_suppressed_insight_still_occupies_slot` |
| `tests/test_stage12_state_effectiveness.py` | `test_resident_suppressed_removed_distinct`, `test_remove_one_reason_does_not_resume`, `test_expired_suppressed_control_never_revives`, `test_provider_resume_recomputes_insight_protection` |
| `tests/test_stage12_skill_permission.py` | `test_exhaustion_active_denied_basic_assault_allowed`, `test_no_active_candidate_is_silent`, `test_already_activated_chain_not_rolled_back`, `test_preparing_interrupt_is_immediate`, `test_intimidation_interrupts_only_selected_provider` |
| `tests/test_stage12_provider_validity.py` | `test_provider_and_holder_mirror`, `test_inherent_slot_zero_is_valid_key`, `test_expected_skill_id_mismatch`, `test_source_resume_keeps_intimidation_binding`, `test_cyclic_dependency_is_explicit_boundary` |
| `tests/test_stage12_target_policy.py` | `test_single_replacement`, `test_choose_n_preserves_count`, `test_fixed_all_preserved`, `test_inherited_no_recheck_independent_recheck`, `test_duel_source_inadmissible_not_forced`, `test_confusion_preempts_provocation` |
| `tests/test_stage12_equipment_effectiveness.py` | `test_static_modifier_suppression_symmetric_restore`, `test_damage_recovery_contributions_follow_owner`, `test_scheduled_window_not_replayed`, `test_remote_holder_does_not_disable_external_owner`, `test_equipment_object_and_live_effect_retained` |
| `tests/test_stage12_capture_composition.py` | `test_counter_blocked_attached_active_dot_continues`, `test_free_proxy_actor_not_original_provider`, `test_friendly_single_choose_two_excluded_self_recovery_zero`, `test_capture_removed_other_suppressor_remains` |
| `tests/test_stage12_rng_and_wiring.py` | `test_same_seed_same_binding`, `test_refresh_rerolls_even_if_same_result`, `test_resume_does_not_reroll`, `test_single_canonical_policy_injection`; rejected binding path consumes no selection draw, source proc path governed separately |
| `tests/test_stage12_cross_state.py` | Parametrized exact pairs below; independent reason removal in both orders; normative vs project-default expectations labeled separately |

Required Stage12 pairs: Insight × Exhaustion/FalseReport/Provocation/Intimidation/Sabotage/Capture;
Exhaustion × Provocation/FalseReport/Intimidation/Capture;
FalseReport × Intimidation/Sabotage/Capture;
Provocation × Confusion/Taunt/Capture; Intimidation × Capture; Sabotage × Capture.
Also preserve tested FalseReport-source × Provocation dependency even though it is absent from
the minimum pair list.

Required legacy pairs: STUN/WEAKNESS/HEALING_BLOCK × CAPTURE;
DISARM/STUN × INSIGHT; CONFUSION/TAUNT × PROVOCATION;
Damage/Recovery Pipeline × CAPTURE. Add INSIGHT × CONFUSION as the AR-SF-01 discriminator.
Foundation cases do not replace seven state contract suites or the full 913-test regression.
Methods listed here are proposed future case names, not passing tests.

## 5. Exit and next task

Round 2 authority and identity design is complete for its assigned scope. There are 28 tracked questions:
- 19 DESIGN_REQUIRED
- 3 CONTRACT_DEPENDENT
- 0 BLOCKED
- 1 CLOSED_BY_EXISTING_ARCHITECTURE
- 2 CLOSED_BY_SHARED_FOUNDATION_DESIGN
- 1 CLOSED_BY_AUTHORITY_MIGRATION
- 1 CLOSED_BY_SCOPED_SUPERSESSION
- 1 CLOSED_BY_PROVENANCE_QUALIFICATION

AR-SF-01 is closed by explicit authority migration. AR-SF-02 provenance is qualified.
DQ-SF-04/05/15/16/28 are closed under the statuses above.
Shared Foundation Design Freeze remains NOT PASSED.

NEXT: DQ-SF-02 / DQ-SF-03 / DQ-SF-08 / DQ-SF-20:
State Effectiveness + Suppression Composition + Provider Validity + Dependency Cycle Design.
