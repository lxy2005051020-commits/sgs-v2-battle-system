# Stage12 Shared Foundation Design Question Ledger

Date: 2026-09-27. Scope: SF-0, first-round design questions, **NOT DESIGN FREEZE**.
Authority and code baseline: [Reconnaissance](STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md).

Statuses describe closure of a design question, not mechanism Research Freeze:

- CLOSED_BY_EXISTING_ARCHITECTURE: existing canonical owner resolves the stated question.
- DESIGN_REQUIRED: evidence is sufficient, but interface/composition decision remains.
- CONTRACT_DEPENDENT: bounded or external contract boundary must be preserved/qualified.
- CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED: the shared architecture is frozen, while named mechanism-specific evidence boundaries remain explicitly bounded/unsupported.
- BLOCKED: a concrete incompatible authority prevents closure without explicit resolution.
- CLOSED_BY_AUTHORITY_MIGRATION: a later canonical authority explicitly supersedes the conflicting historical rule.
- CLOSED_BY_SCOPED_SUPERSESSION: the exact affected historical scope is named and unaffected frozen scope is preserved.
- CLOSED_BY_SHARED_FOUNDATION_DESIGN: the representation needed by downstream Shared Foundation design is fixed; this is not Runtime Freeze.
- CLOSED_BY_PROVENANCE_QUALIFICATION: cross-contract outcome and evidence provenance are both explicitly preserved.

## 1. Mandatory question ledger

| ID | Question / evidence | Status | Candidate owner and required next decision | Dependencies / acceptance discriminator |
|---|---|---|---|---|
| DQ-SF-01 | Who admits incoming state? Lifecycle.apply mutates, Stage11 policy only checks conflict | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `StateAdmissionPolicy.evaluate_candidate` is the pure target-admission owner. Source RNG/candidate generation precedes admission; admission precedes contract-relevant conflict; Lifecycle remains the only writer. | 02,03,14,22; typed rejection allocates no generation, changes no old instance/timer/binding, emits no applied/removed pair and does not abort legal sibling effects |
| DQ-SF-02 | Who answers effective state across Stage9/11/12? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `StateEffectivenessPolicy` is the single canonical owner for current gameplay authority of a resident state. Registry remains storage; Lifecycle remains writer; Stage9/11 delegate shared truth while retaining domain arbitration. | 05,08,15,20; suppressed Insight cannot suppress protected controls; removed instances are not query results |
| DQ-SF-03 | How represent Resident / Effective / Suppressed / Removed? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Residency is a Registry fact; `StateEffectivenessDecision` is returned only for resident instances and distinguishes EFFECTIVE / SUPPRESSED / INACTIVE with stable typed blockers. Removal is absence from Registry, never a decision status. | 02,08; independent causes compose; final cause removal resumes only still-live instances; suppression never pauses lifecycle by default |
| DQ-SF-04 | Minimal SkillType, preparation characteristic, and ProviderCategory? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | SkillDefinition metadata: SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION/TALENT + PreparationMode NONE/REQUIRED; PREPARATION_ACTIVE = ACTIVE+REQUIRED; NORMAL_ATTACK remains operation; equipment special remains separate ProviderCategory; TALENT was added by the 690107 Runtime Freeze corrective audit solely as a FALSE_REPORT negative discriminator | See STAGE12_SKILLTYPE_PROVIDER_IDENTITY_DESIGN.md; legacy compatibility default RD-SF-001; no execution chain |
| DQ-SF-05 | Stable provider identity and enumeration? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Typed ProviderRef union: SkillProviderRef(owner_id, slot, skill_id) + EquipmentProviderRef(owner_id, provider_key); Registry resolves skill key and expected ID; deterministic enumeration RD-SF-002 | 04,21; same skill on two owners/slots distinct; slot 0 valid; serialization/replay; missing vs mismatch explicit |
| DQ-SF-06 | Skill permission API and canonical admission point? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | SkillPermissionPolicy is the canonical holder-level permission owner. SkillOperationAdmissionCoordinator composes ProviderValidityPolicy + SkillPermissionPolicy before observable activation/RNG; already-admitted continuation is not re-admitted. | 04,08,12,13; Exhaustion denies only new ACTIVE admission; Normal Attack outside domain; standard ASSAULT not denied by Exhaustion; skip-preparation stays ACTIVE |
| DQ-SF-07 | Preparation interruption port and state ownership? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | PreparationInterruptionPort is the minimal Stage12-facing protocol; the future Stage15 preparation owner stores progress. EffectivenessTransitionCoordinator synchronously issues holder-wide ACTIVE or selected-Provider requests on relevant effectiveness/validity transitions. | 05,06,08,20; interruption occurs before later gameplay, old progress never resumes, Fake port is testable, production placeholder cannot imply contract completion |
| DQ-SF-08 | Provider validity query and dependency propagation? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `ProviderValidityPolicy.evaluate(context, ProviderRef)` owns current Provider validity after identity resolution. Statuses: VALID / SUPPRESSED / BASELINE_DISABLED / MISSING / IDENTITY_MISMATCH. Independent suppression causes are derived; live state dependencies are explicit `ProviderDependency`, never inferred from provenance. | 02,04,05,20,21; Provider/Holder separation; final cause removal resumes future-only behavior; no missed-trigger replay |
| DQ-SF-09 | Target Operation model? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `TargetOperation` is the explicit fresh Skill-target query value object; `SkillTargetPolicy` is the canonical operation-local eligibility/constraint owner; `TargetSystem` remains raw candidate/RNG primitive owner and Normal Attack remains separate. | See STAGE12_TARGET_OPERATION_POLICY_DESIGN.md; relation ENEMY/ALLY/SELF, SINGLE/CHOOSE_N/FIXED_ALL, selector boundary, TargetOperationId, provenance, Provocation and Capture mappings frozen; implementation pending |
| DQ-SF-10 | What creates a new target operation? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | The skill/effect operation producer explicitly declares `NEW_QUERY`; only that declaration allocates a new `TargetOperationId` and re-enters target policy. INHERITED / DERIVED / LOCKED continuations reuse the prior resolution identity and are not automatically rechecked. | 09,12,23; same-target multi-hit = one operation; explicit independent re-query = distinct operation; delayed/locked Capture work remains DQ-SF-23 |
| DQ-SF-11 | Minimal equipment effectiveness abstraction? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | EquipmentEffectivenessPolicy.evaluate_contribution is the sole final truth for a concrete EquipmentContributionRef; generic ProviderValidityPolicy is an input, while Attribute/Damage/Recovery/Trigger owners keep domain calculation. | See STAGE12_EQUIPMENT_EFFECTIVENESS_DESIGN.md; stable EquipmentProviderRef + contribution kind/key, object retained, multi-reason suppression, explicit remote dependency, no replay/reinitialize; FalseReport untested equipment and Capture reactive/damage stay bounded/unsupported; queued micro-order remains DQ-SF-23 |
| DQ-SF-12 | Who consumes RNG, when and for what? | CLOSED_BY_SHARED_FOUNDATION_DESIGN / AUDIT_GOVERNANCE_CORRECTED | BattleContext.random/RandomSystem is the sole RNG service; real random decisions remain domain-owned. Pure policies, transition coordination and ExecutionRight evaluation are zero-RNG. Source-generation RNG, Skill activation, target selection, Intimidation binding/refresh, RecoveryOpportunity and equipment-trigger draw points and rejection paths are frozen. EXHAUSTION denied-ACTIVE pre-RNG placement is explicitly governed by RD-SF-004. | See STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md; PD-INS-001 source parity preserved; denied EXHAUSTION ACTIVE uses RD-SF-004 and consumes no activation/target RNG; other denied Provider/Recovery/Equipment paths retain their mapped governance; Provocation CHOOSE_N micro-order and Intimidation weights remain DEFERRED/UNSUPPORTED boundaries |
| DQ-SF-13 | Minimal events and explicit decisions? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | EventBus remains fact recording/dispatch only. Pure queries emit nothing; domain owners publish only canonical outcomes after decision/commit. State suppression/resume and finalized application rejection receive explicit future fact vocabulary; Provider transitions remain internal by default; existing ACTION_BLOCKED / DAMAGE_PREVENTED / RECOVERY_PREVENTED stay domain-owned. | See STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md; rejection uses one future STATE_APPLICATION_REJECTED fact with ADMISSION/CONFLICT discriminator; repeated query/same-state transition emits nothing; failed transaction emits no committed-state event; target policy no-op never fabricates forced-target facts |
| DQ-SF-14 | Which runtime defaults are required and where recorded? | CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED / AUDIT_GOVERNANCE_CORRECTED | Runtime Default governance is frozen: only behavior Runtime must deterministically choose now may become PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN; rejectable/deferable unknowns remain UNSUPPORTED_BOUNDARY or DEFERRED. Current Battle-owned set is RD-SF-001/002/003/004; PD-INS-001/002 remain inherited research-side approved project defaults. | See STAGE12_RUNTIME_DEFAULT_LEDGER.md and STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md; Round 11 adds RD-SF-004 because 690101 leaves denied-ACTIVE hidden activation RNG unobservable; all other named unknowns retain explicit governance classification and reopen triggers |
| DQ-SF-15 | How migrate actual 690089 PARTIAL? | CLOSED_BY_AUTHORITY_MIGRATION | STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md establishes later Insight v0.4 authority and explicit future test replacement; identity/lifecycle/Taunt scope preserved | 02,16; implementation still pending, but authority blocker is closed |
| DQ-SF-16 | Stage11 and older frozen regression boundary? | CLOSED_BY_SCOPED_SUPERSESSION | P0-CFS-P93-01/P93-B01 superseded only for existing Confusion remaining operational after later effective Insight; all enumerated unaffected Stage9 rules preserved; Stage11 Reopen Required NO | 15,24; any future clock contradiction requires a separately proven scoped reopen |
| DQ-SF-17 | BattleSystems wiring and compatibility paths? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | BattleSystems constructs one canonical Shared Foundation graph while BattleContext retains the sole per-battle StateRegistry / SkillRuntimeRegistry / RandomSystem / EventBus resources. Shared policies/coordinators are explicit production injections; DependencyEvaluationSupport breaks evaluation cycles without becoming a gameplay owner or service locator. | See STAGE12_SHARED_FOUNDATION_COMPOSITION_AND_TEST_ARCHITECTURE.md; Stage9/11 share one StateEffectivenessPolicy, Skill/Recovery share ProviderValidityPolicy, equipment consumers share EquipmentEffectivenessPolicy, and production fallback owner construction is forbidden. |
| DQ-SF-18 | Test architecture and model discriminators? | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Four-layer architecture: Shared Foundation unit/wiring/static tests; seven state contract suites; cross-state + Stage11 regressions; full-suite/demo/CI. Contract Rule → Owner → Method/Seam → Test → Evidence Class → Default → Status traceability is mandatory. | See STAGE12_SHARED_FOUNDATION_COMPOSITION_AND_TEST_ARCHITECTURE.md and STAGE12_RUNTIME_TEST_MATRIX.md; FALSE_REPORT >=30, PROVOCATION >=25, INTIMIDATION >=21 retained; unsupported boundaries require explicit failure tests; DQ-SF-26 remains independent audit. |

## 2. Additional questions required by code and contracts

| ID | Question | Status | Owner / next decision | Acceptance boundary |
|---|---|---|---|---|
| DQ-SF-19 | Capture composite action/damage/recovery/target permission | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Capture supplies state-derived rule facts only. ActionSystem, Damage domain admission/execution seam, ProviderValidityPolicy, RecoverySystem, SkillTargetPolicy, EquipmentEffectivenessPolicy and StateLifecycleSystem remain final domain owners. | Counter damage denied while attached Active DOT continues; current actor is distinct from origin provider/source; verified friendly SINGLE/CHOOSE_N exclusion, recovery-zero and equipment-attribute scope preserved; no Capture God Object |
| DQ-SF-20 | Cyclic dependencies and immediate transitions | CLOSED_BY_SHARED_FOUNDATION_DESIGN | Evaluation uses an explicit consumer→prerequisite dependency graph with per-evaluation memoization and cycle detection. `EffectivenessTransitionCoordinator` is a non-authoritative propagation coordinator. Cycles are unsupported: raise `DependencyCycleError`, produce no guessed allow/deny truth, and require topology validation before committing dependency-changing transitions. | No fixed point; reverse dependency closure drives synchronous re-evaluation; cycle path explicit; no replay; no Runtime Default needed because no gameplay fallback is chosen |
| DQ-SF-21 | Existing JIT source-gate migration and slot 0 | CLOSED_BY_SHARED_FOUNDATION_DESIGN / AUDIT_SCOPE_CLARIFIED | RecoveryOpportunitySystem Gate 4 must construct SkillProviderRef with explicit slot-is-not-None semantics and expected skill_id, then delegate current validity to ProviderValidityPolicy. SkillResolver admission must stop treating runtime.enabled as complete truth. TriggerSystem provenance merge must also preserve a valid source_skill_slot == 0 with explicit is-not-None precedence; that provenance repair does not create ProviderDependency or a new liveness gate. | INHERENT=0/1/2 same identity path; MISSING / IDENTITY_MISMATCH / BASELINE_DISABLED / SUPPRESSED reject mapped JIT opportunities before owned RNG; TriggerSystem slot-0 provenance cannot fall through to instance slot; attribution-only source_ref does not gain liveness |
| DQ-SF-22 | Application result, refresh transaction, binding atomicity | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `StateConflictPolicy` + immutable `StateApplicationTransaction` + non-writing coordinator prepare CREATE/REFRESH/REPLACE/REJECT; only Lifecycle commits. REFRESH keeps instance_id and creates a new application generation. | All fallible validation precedes commit; old Intimidation binding/timer stay authoritative until commit; resume preserves binding/generation/timer; legacy ValueError surface retained for old callers |
| DQ-SF-23 | Admitted/queued work vs JIT recheck | CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED | Domain-specific operation identity carries an ExecutionRightSpec with per-dimension SNAPSHOT_AT_ADMISSION / RECHECK_AT_EXECUTION / NOT_APPLICABLE / UNSUPPORTED_BOUNDARY. Existing FutureAdmissionGate remains future-branch/battle-finalization authority; existing ExecutionRightSystem is extended only as shared execution-right infrastructure, never as a gameplay-domain God Object. | New != admitted; queued/attached/locked retain identity; Exhaustion admitted Active permission is stable; Recovery Provider validity can JIT; Capture Q16/Q44/Q45 and Sabotage B-SAB-07 remain explicit bounded modes, not silent defaults |
| DQ-SF-24 | Clock continuation during suppression | CLOSED_BY_SHARED_FOUNDATION_DESIGN | `StateLifecycleSystem` owns physical lifetime; explicit clock domains separate round/holder-action/phase lifetime from behavioral block/use counters and provider/source counters. Stage12 uses typed lifetime metadata instead of entering Stage10 merely via duration_rounds/lifecycle_window. | suppression never pauses physical lifetime; STUN block consumption requires an actually blocked opportunity; Intimidation may expire while ineffective; RD-SF-003 fixes same-envelope settlement ordering |
| DQ-SF-25 | Cleanse eligibility, strength, reapplication and source death | CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED | `StateRemovalPolicy.evaluate_removal` owns gameplay removal eligibility; `StateLifecycleSystem.remove` remains the authorized physical primitive. Natural expiry/defeat/teardown are infrastructure, not ordinary cleanse. | Capture ordinary cleanse rejected; Intimidation generic cleanse rejected but specialized removal bounded; FR/SAB removal classes stay evidence-scoped; source death never implies global cleanup; reapplication unknowns remain unsupported, not invented |
| DQ-SF-26 | Design Freeze audit owner and gate | CLOSED_BY_INDEPENDENT_DESIGN_AUDIT | Round 11 independent audit attacked all seven contracts, owner graph, wiring, defaults, boundaries, regressions and test architecture. Two MAJOR and two MINOR documentation/governance defects were corrected without gameplay implementation or design-owner reopen; unresolved BLOCKER/MAJOR = 0. | Authority: STAGE12_SHARED_FOUNDATION_INDEPENDENT_DESIGN_AUDIT.md; Shared Foundation Design Freeze = PASS; Stage12 Runtime Frozen remains 0/7; Stage13/14/15 remain inactive |
| DQ-SF-27 | Physical state write and RNG service ownership | CLOSED_BY_EXISTING_ARCHITECTURE | StateLifecycleSystem writes; StateRegistry stores; BattleContext.random is sole random source; EventBus records | Consumers delegate/query; no second lifecycle, no direct random.*, no permission decisions in event handlers |
| DQ-SF-28 | Intimidation × Insight evidence labels across contracts | CLOSED_BY_PROVENANCE_QUALIFICATION | Runtime uses Intimidation §§5,11 as positive authority while Insight retains SPECIAL_CASE_SUPPORTED / DIRECT_OVERLAP_UNOBSERVED provenance; Research files are not rewritten | Ordinary Insight non-rejection is usable without falsely claiming direct Insight-corpus observation |

## 3. Default candidates and preserved non-claims

Round 2 started STAGE12_RUNTIME_DEFAULT_LEDGER.md with RD-SF-001 and RD-SF-002.
Round 4 adds RD-SF-003 for same-envelope lifecycle settlement ordering.
No Intimidation weighting, empty-pool behavior, unsupported reapplication rule, or unknown removal class is silently selected.
Future choices must use the same fields and the labels PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN.

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


## 5. SF Round 3 closure — State Effectiveness / Provider Validity / Dependency Composition

Authority record: [STAGE12_STATE_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN.md](STAGE12_STATE_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN.md)

Closed in `STAGE12_SF_ROUND3_EFFECTIVENESS_PROVIDER_VALIDITY_DESIGN`:

- DQ-SF-02 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-03 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-08 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-20 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

Frozen design facts:

1. `StateEffectivenessPolicy` is the only canonical answer to whether a resident state currently owns its gameplay authority.
2. `ProviderValidityPolicy` is the only canonical answer to current Provider validity; Provider identity remains owned by its registry/resolver.
3. `StateRegistry` answers residency only. `StateLifecycleSystem` remains the only physical state writer.
4. Removed instances are not represented as an effectiveness enum member. Querying a removed/non-resident instance is an explicit not-resident error/boundary.
5. Canonical suppression composition is derived/query-time, using stable value-object causes. Target/provider objects do not own a mutable list of suppressors.
6. State/provider dependencies are explicit. `EffectSourceRef` remains attribution and never becomes liveness dependency by implication.
7. State lifetime continues while suppressed unless a specific future contract explicitly freezes a pause rule.
8. Multiple independent causes compose as set semantics. Removing one cause cannot resume authority while another blocker remains.
9. `EffectivenessTransitionCoordinator` coordinates dependent decision changes and synchronous transition notifications but owns no storage, permission, damage, target, recovery, RNG, or EventBus truth.
10. Dependency cycles are not solved by fixed point. They raise `DependencyCycleError`; no silent ALLOW/DENY fallback exists.
11. Stage9 and Stage11 effective-state readers migrate by delegation; their domain-specific arbitration remains local.
12. No Stage11 reopen is required by this design round.
13. No gameplay implementation is authorized or performed here.

Shared Foundation Design Freeze remains NOT YET.
Stage12 Runtime Frozen remains 0 / 7.
Stage13 Active remains NO.

## 6. SF Round 4 closure — State Admission / Lifecycle Transaction / Clock / Removal

Authority record: [STAGE12_STATE_LIFECYCLE_TRANSACTION_DESIGN.md](STAGE12_STATE_LIFECYCLE_TRANSACTION_DESIGN.md)

Closed/frozen in `STAGE12_SF_ROUND4_STATE_LIFECYCLE_TRANSACTION_DESIGN`:

- DQ-SF-01 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-22 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-24 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-25 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED.

Frozen shared facts:

1. `StateAdmissionPolicy` is the sole pure admission owner; source candidate-generation RNG precedes it.
2. Admission precedes contract-relevant same-state conflict. A rejected candidate has zero physical side effects.
3. `StateConflictPolicy` may return CREATE / REFRESH / REPLACE / REJECT_CONFLICT / UNSUPPORTED_BOUNDARY; same-state does not universally mean refresh.
4. REFRESH preserves physical `instance_id` but advances to a new `application_generation_id`.
5. Intimidation's old binding remains authoritative until a successful refresh commit; resume never rerolls.
6. `StateLifecycleSystem` remains the only physical writer and physical clock owner.
7. Stage12 lifetime metadata must not enter Stage10 persistence merely because a duration exists.
8. suppression does not pause physical lifetime, while behavioral block/use counters consume only their actual qualifying opportunities.
9. `StateRemovalPolicy` owns gameplay removal eligibility; cleanse resistance is not hidden inside `Lifecycle.remove()`.
10. source death is not a global state-removal operation.
11. RD-SF-003 freezes the project-only same-envelope expiry/removal settlement order.
12. no Stage12 gameplay implementation was authorized.

Current 28-question disposition after Round 4:

- 12 DESIGN_REQUIRED
- 2 CONTRACT_DEPENDENT
- 1 CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
- 0 BLOCKED
- 1 CLOSED_BY_EXISTING_ARCHITECTURE
- 9 CLOSED_BY_SHARED_FOUNDATION_DESIGN
- 1 CLOSED_BY_AUTHORITY_MIGRATION
- 1 CLOSED_BY_SCOPED_SUPERSESSION
- 1 CLOSED_BY_PROVENANCE_QUALIFICATION

Shared Foundation Design Freeze remains **NOT PASSED**.

NEXT: DQ-SF-06 / DQ-SF-07 / DQ-SF-21 — Skill Permission + Preparation Interruption + Existing JIT Provider Gate Migration.


## 7. SF Round 5 closure — Skill Permission / Preparation Interruption / JIT Provider Gate

Authority record: [STAGE12_SKILL_PERMISSION_PREPARATION_PROVIDER_GATE_DESIGN.md](STAGE12_SKILL_PERMISSION_PREPARATION_PROVIDER_GATE_DESIGN.md)

Closed in STAGE12_SF_ROUND5_SKILL_PERMISSION_PREPARATION_PROVIDER_GATE_DESIGN:

- DQ-SF-06 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-07 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.
- DQ-SF-21 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

Frozen shared facts:

1. SkillPermissionPolicy owns holder-level permission only; it never mutates SkillRuntime, consumes RNG, selects targets or decides Provider validity.
2. ProviderValidityPolicy remains the only owner of ProviderRef current validity.
3. SkillOperationAdmissionCoordinator is a thin composition seam, not a new gameplay owner. It resolves identity, evaluates Provider validity and holder permission, and admits only after all blockers are known.
4. Exhaustion denies only a real new ACTIVE admission. Normal Attack is outside the policy; standard ASSAULT is not denied merely by Exhaustion.
5. Already-admitted Active work is not rolled back by a later Exhaustion transition. Child effects are not automatically new admissions.
6. Skip-preparation does not change SkillType; ACTIVE + skipped preparation is still subject to Exhaustion.
7. PreparationInterruptionPort is a Stage12-facing protocol only. Stage12 does not own preparation progress or a scheduler.
8. Exhaustion entering EFFECTIVE synchronously requests holder-wide interruption of current ACTIVE preparations.
9. Intimidation causing the selected Provider to transition VALID -> SUPPRESSED synchronously requests interruption only for that selected Provider when it is a preparation Active.
10. Interruption is destructive with respect to the old preparation instance: later state/provider resume never restores old progress.
11. RecoveryOpportunitySystem Gate 4 is the first concrete JIT migration target. SkillSlot.INHERENT == 0 is valid and must use explicit is-not-None semantics.
12. Query-gated recovery must validate expected skill_id; MISSING, IDENTITY_MISMATCH, BASELINE_DISABLED and SUPPRESSED all reject before recovery probability RNG.
13. EffectSourceRef provenance alone never creates ProviderDependency.
14. The existing TriggerSystem source_skill_slot truthiness fallback is recorded as a separate identity/provenance hygiene hazard; it is not silently reclassified as a Provider liveness gate.
15. No Stage12 gameplay implementation was authorized in this round.

Current 28-question disposition after Round 5:

- 9 DESIGN_REQUIRED
- 2 CONTRACT_DEPENDENT
- 1 CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
- 0 BLOCKED
- 1 CLOSED_BY_EXISTING_ARCHITECTURE
- 12 CLOSED_BY_SHARED_FOUNDATION_DESIGN
- 1 CLOSED_BY_AUTHORITY_MIGRATION
- 1 CLOSED_BY_SCOPED_SUPERSESSION
- 1 CLOSED_BY_PROVENANCE_QUALIFICATION

Shared Foundation Design Freeze remains **NOT PASSED**.
Stage12 Runtime Frozen remains **0 / 7**.
Stage13 / Stage14 / Stage15 Active remain **NO**.

NEXT: DQ-SF-09 / DQ-SF-10 — Skill Target Operation / Provocation / Capture Target Eligibility Design.


## SF Round 6 closure — Target Operation / Target Policy — 2026-09-27

Authority record:
- STAGE12_TARGET_OPERATION_POLICY_DESIGN.md

Round 6 closes DQ-SF-09 and DQ-SF-10 at Shared Foundation design level only.

Frozen downstream representation:

~~~text
ProviderValidity / SkillPermission admission
→ producer explicitly declares NEW_QUERY
→ TargetOperationId + TargetOperation
→ TargetSystem raw candidates
→ operation-local eligibility
→ SkillTargetPolicy constraints
→ selector (sole target-sampling RNG owner)
→ TargetSelectionResult
→ inherited / derived / locked continuations carry provenance
~~~

Key closure facts:

- Relation = ENEMY / ALLY / SELF; ANY is not introduced without a current contract need.
- Cardinality = SINGLE / CHOOSE_N / FIXED_ALL; CHOOSE_N carries an explicit requested N.
- TargetOperationId is typed value identity, never Python object identity and never a gameplay ordering key.
- only producer-declared NEW_QUERY creates a new operation and can re-evaluate Provocation;
- inherited, derived and locked reuse do not create an implicit query;
- same-target multi-hit is one target operation; explicit multi-query produces distinct operation IDs;
- SkillTargetPolicy is pure and consumes zero RNG;
- Provocation applies only to eligible fresh enemy-directed Skill operations and never owns Normal Attack;
- Provocation SINGLE forces an admissible Source, CHOOSE_N preserves N and requires Source once, FIXED_ALL preserves the all-target set;
- Capture excludes captured holders only from the verified friendly SINGLE / CHOOSE_N target-eligibility scope;
- Capture does not mutate TargetSystem.allies(), create a global untargetable flag, or replace RecoverySystem's recovery denial;
- Capture ALL_ALLIES and delayed/already-locked friendly work remain explicit bounded boundaries;
- exact Provocation CHOOSE_N RNG micro-order, insufficient-candidate micro-policy and multi-source precedence remain bounded for DQ-SF-12 / DQ-SF-14 rather than becoming silent defaults.

Round 6 adds no gameplay implementation and no production tests.
Stage11 Reopen Required = NO.


## 5. SF Round 7 closure — equipment effectiveness

DQ-SF-11 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

Authority:
- STAGE12_EQUIPMENT_EFFECTIVENESS_DESIGN.md

Frozen Shared Foundation facts:

- EquipmentProviderRef(owner_id, provider_key) remains stable equipment Provider identity.
- EquipmentContributionRef(provider_ref, contribution_key, kind) is the concrete contribution identity.
- Kinds: ATTRIBUTE / DAMAGE_MODIFIER / RECOVERY_MODIFIER / TRIGGER / SCHEDULED_TRIGGER / LIVE_EFFECT.
- ProviderValidityPolicy supplies generic Provider validity; EquipmentEffectivenessPolicy owns final contribution truth.
- Status preserves EFFECTIVE / SUPPRESSED / BASELINE_DISABLED / MISSING / IDENTITY_MISMATCH / UNSUPPORTED_BOUNDARY.
- SABOTAGE is owner-wide across its tested contribution scope; only EFFECTIVE Sabotage contributes a cause.
- FALSE_REPORT equipment behavior remains tested-persistent-special scoped.
- CAPTURE equipment behavior remains verified-attribute scoped; reactive/damage remains Q63 bounded.
- Attribute is query-time; damage/recovery are domain-collection filters; tested scheduled due windows use execution-time JIT gating.
- Remote live effects require explicit EquipmentContributionDependency; attribution alone is insufficient.
- suppression never means unequip/delete; resume never means reinitialize/replay.
- independent causes compose as a set.
- EquipmentEffectivenessPolicy consumes zero RNG and never reorders domain contributions.

Preserved mechanism-specific debt:
- DQ-SF-23 / B-SAB-07 queued/in-flight micro-order;
- FalseReport B-U04 untested equipment special subtypes;
- Capture Q63 equipment reactive/damage special;
- Sabotage B-SAB-09 dynamic equipment-change / empty-equipment semantics where a gameplay answer would be required.

These are evidence boundaries, not an open owner/architecture question.

## 6. SF Round 8 closure — Capture composite execution and admitted/queued/JIT boundary

DQ-SF-19 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

DQ-SF-23 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED.

Authority:
- STAGE12_CAPTURE_COMPOSITE_EXECUTION_DESIGN.md

Frozen Shared Foundation facts:

- CAPTURE is a Composite State, not a universal runtime owner.
- Natural Action denial belongs to ActionSystem. Capture denial is upstream of NormalAttack operation creation; it creates no NormalAttack targeting or RNG.
- CAPTURE and STUN are not represented by a first-if-wins chain. Action blocking is two-phase: non-consuming eligibility denial first, then consumable Stage11 action blockers. CAPTURE denial therefore does not consume a STUN block.
- Damage work carries an explicit work category and current actor identity. source_id / historical provenance is never sufficient to decide CAPTURE actor permission.
- Minimum damage categories: NEW_ACTOR_DRIVEN_DAMAGE, COUNTER_DAMAGE, ATTACHED_EXISTING_DOT, FREE_PROXY_DAMAGE, ALREADY_CREATED_DAMAGE_REQUEST, OTHER_BOUNDED.
- New actor-driven damage and Counter damage are denied by the Damage domain when the current actor is captured.
- Previously attached Active-origin DOT is admitted continuation. CAPTURE actor permission is NOT_APPLICABLE to that continuation; any explicit Provider dependency remains independently governed.
- A free proxy actor is judged by the proxy's current actor identity, not by an historical captured origin Provider.
- CAPTURE damage denial is admission/execution-right semantics and must remain distinct from WEAKNESS legal-zero output semantics.
- Provider-linked PASSIVE / COMMAND validity remains ProviderValidityPolicy-owned.
- Received recovery remains RecoverySystem-owned. CAPTURE participates in the prevention phase after recovery modifier/second CEIL and before troop restoration/capacity; HEALING_BLOCK and CAPTURE can coexist as internal causes without changing arithmetic order.
- Friendly target exclusion remains SkillTargetPolicy-owned and does not become a global targetable flag.
- Equipment attribute suppression remains EquipmentEffectivenessPolicy-owned; CAPTURE Q63 reactive/damage equipment remains bounded.
- Physical CAPTURE lifetime/removal remains StateLifecycleSystem-owned; source death does not synthesize cleanup.
- Work lifecycle distinguishes NEW, ADMITTED, QUEUED, ATTACHED, EXECUTING and SETTLED. TARGET_LOCKED is an orthogonal target-provenance qualifier that may coexist with queued work.
- No UniversalWorkId is introduced. Existing domain IDs remain identity; shared metadata only describes execution-right dimensions.
- ExecutionRightSpec modes are per dimension: SNAPSHOT_AT_ADMISSION, RECHECK_AT_EXECUTION, NOT_APPLICABLE, UNSUPPORTED_BOUNDARY.
- Dimensions are ACTOR_PERMISSION, PROVIDER_VALIDITY, TARGET_ELIGIBILITY, EQUIPMENT_CONTRIBUTION and STATE_EFFECTIVENESS.
- No universal JIT and no universal snapshot rule is allowed.
- A failed execution-time recheck skips/denies the current execution opportunity. It does not requeue and does not replay after later resume unless a mechanism contract explicitly says otherwise.
- Existing FutureAdmissionGate remains the Stage9 future-branch admission authority and is not repurposed into a current-state permission engine.
- Existing ExecutionRightSystem retains its RuleIntent/liveness invariants and may host shared mechanical execution-right evaluation later; domain-specific truth still delegates to canonical domain owners.
- Q16 already-created DamageRequest = UNSUPPORTED_BOUNDARY for actor-permission recheck policy.
- Q44 delayed friendly work = UNSUPPORTED_BOUNDARY for target/provider/actor recheck dimensions not already frozen.
- Q45 already-locked friendly target = UNSUPPORTED_BOUNDARY; LOCKED never silently becomes NEW_QUERY.
- B-SAB-07 collected/queued equipment work remains UNSUPPORTED_BOUNDARY outside the already frozen scheduled due-window case.
- No new PROJECT_RUNTIME_DEFAULT is required in Round 8.

Stage11 Reopen Required = NO.
Gameplay implementation = NONE.
Stage12 Runtime Frozen = 0 / 7.


## 7. SF Round 9 closure — RNG / Event / Runtime Default governance

DQ-SF-12 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

DQ-SF-13 = CLOSED_BY_SHARED_FOUNDATION_DESIGN.

DQ-SF-14 = CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED.

Authority:
- STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md

Frozen Shared Foundation facts:

- BattleContext.random / RandomSystem is the only RNG service. Gameplay owners authorize actual random decisions; policies do not become PRNG owners.
- StateAdmissionPolicy, StateEffectivenessPolicy, StateConflictPolicy, ProviderValidityPolicy, SkillPermissionPolicy, SkillOperationAdmissionCoordinator, SkillTargetPolicy, EquipmentEffectivenessPolicy, StateRemovalPolicy, EffectivenessTransitionCoordinator and ExecutionRight evaluation consume zero RNG.
- PD-INS-001 remains global Stage12 RNG law for protected-control generation: preserve the source control's normal proc RNG before Insight admission, while deterministic sources gain no synthetic draw.
- Provider-invalid or holder-permission-denied Skill operations consume no activation RNG and create no target-selection opportunity.
- TargetSystem / selector remains the target-sampling RNG owner. Forced legal singleton and all-candidate results consume zero target RNG.
- Intimidation rejected before admission consumes zero binding RNG. Successful refresh authorizes a new binding selection even if the selected Provider value is unchanged. Resume retains binding and consumes zero binding RNG.
- Provider-dependent RecoveryOpportunity validity is checked before recovery probability RNG. Equipment contribution JIT denial precedes any trigger-owned downstream RNG.
- ExecutionRight evaluation is zero RNG; a denied JIT opportunity consumes no downstream work RNG unless a source contract explicitly freezes source RNG before rejection.
- deterministic replay is governed at ordered RandomSystem decision/API operations, not hidden CPython PRNG bit consumption.
- Provocation CHOOSE_N exact RNG micro-order, Intimidation exact weights and other named bounded RNG edges remain explicit DEFERRED / UNSUPPORTED boundaries.
- Query is not Event. Repeated policy queries emit no EventBus facts.
- EventBus remains non-authoritative. The deciding domain owner publishes only after canonical decision/commit.
- future public state effectiveness vocabulary requires STATE_SUPPRESSED / STATE_RESUMED for contract-observable transitions; repeated SUPPRESSED -> SUPPRESSED emits nothing.
- ProviderValidityChanged remains internal by default; no generic Provider suppression event is created merely for debugging.
- finalized state rejection uses one future STATE_APPLICATION_REJECTED fact with rejection_stage = ADMISSION | CONFLICT; policies themselves publish nothing.
- actual blocked Skill operation and actual preparation interruption may have dedicated future facts; absent attempt / NOT_PREPARING emits nothing.
- ACTION_BLOCKED stays ActionSystem-owned; DAMAGE_PREVENTED stays Damage-owned; RECOVERY_PREVENTED stays RecoverySystem-owned.
- Capture + HealingBlock may retain multiple internal recovery causes while exposing one compatibility public RECOVERY_PREVENTED primary reason; this is event representation, not gameplay default.
- target constraint evaluation does not imply TARGET_FORCED. Round 9 does not require a generic target-forced EventType.
- successful mutation event order is decision -> physical commit -> dependency recompute -> internal transition ports -> public facts.
- failed transaction emits no false STATE_APPLIED / STATE_REFRESHED or transition facts.
- Runtime Default governance freezes UNKNOWN != DEFAULT. Runtime-rejectable/deferable unknowns remain boundaries; only mandatory deterministic choices enter the ledger.
- Battle-owned Runtime Defaults remain RD-SF-001 / RD-SF-002 / RD-SF-003. New Round 9 Runtime Defaults = NONE.
- PD-INS-001 / PD-INS-002 remain inherited approved project defaults with original provenance; Battle documentation may not launder them into empirical claims.
- Round 9 governance risks are RNG drift, event duplication/phantom facts and default laundering; mitigations are owner-level RNG tests, event idempotence/post-commit tests and provenance audits.

Stage11 Reopen Required = NO.
Research repository changes = NONE.
Gameplay implementation = NONE.
Stage12 Runtime Frozen = 0 / 7.
Stage13/14/15 Active = NO.

NEXT:
- DQ-SF-17 Composition Wiring
- DQ-SF-18 Final Test Architecture
- then DQ-SF-26 Independent Design Audit


## 8. SF Round 10 closure — Composition Wiring + Final Test Architecture

Authority record:
- STAGE12_SHARED_FOUNDATION_COMPOSITION_AND_TEST_ARCHITECTURE.md

Round 10 closes DQ-SF-17 and DQ-SF-18 by Shared Foundation design. BattleContext remains the sole per-battle owner of StateRegistry, SkillRuntimeRegistry, RandomSystem and EventBus; BattleSystems constructs one Shared Foundation policy/coordinator graph and injects it explicitly. Production fallback canonical-owner construction is forbidden.

The final test architecture is four-layered and every frozen contract claim must trace through canonical owner, method/seam, concrete future test, evidence class and default provenance. Unsupported boundaries require explicit negative/failure tests rather than silent gameplay answers.

Round 10 adds no Runtime Default and no gameplay implementation.

~~~text
DQ-SF-17 CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-18 CLOSED_BY_SHARED_FOUNDATION_DESIGN
DQ-SF-26 DESIGN_REQUIRED

Shared Foundation Design Freeze = NOT YET
Stage12 Runtime Frozen = 0 / 7
Stage11 Reopen Required = NO
Stage13 / Stage14 / Stage15 Active = NO
NEXT = DQ-SF-26 Independent Design Audit
~~~

## 9. SF Round 11 closure — Independent Design Audit

Authority record:
- `STAGE12_SHARED_FOUNDATION_INDEPENDENT_DESIGN_AUDIT.md`

Audit-driven corrections:
- `SF-AUD-11-001`: EXHAUSTION denied-ACTIVE pre-RNG choice is now `RD-SF-004`, not an unledgered architecture-only choice.
- `SF-AUD-11-002`: TriggerSystem slot-0 provenance truthiness is a formal DQ-SF-21 migration obligation, not optional future hygiene.
- `SF-AUD-11-003`: top-level cross-state test matrix now includes FalseReport-source × Provocation.
- `SF-AUD-11-004`: top-level legacy regression matrix now includes INSIGHT × CONFUSION authority migration.

```text
DQ-SF-26 = CLOSED_BY_INDEPENDENT_DESIGN_AUDIT
STAGE12_SHARED_FOUNDATION_DESIGN_FREEZE = PASS
Stage11 Reopen Required = NO
Stage12 Runtime Frozen = 0 / 7
Stage13 / Stage14 / Stage15 Active = NO
Gameplay Implementation = NONE
```
