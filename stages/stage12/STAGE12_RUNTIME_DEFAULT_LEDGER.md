# Stage12 Runtime Default Ledger

Date: 2026-09-27
Status: CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED / COMPLETE FOR CURRENTLY REQUIRED DETERMINISTIC CHOICES
Purpose: record only engineering choices that Runtime must make where Research does not freeze an original-game answer.

Every RD-SF entry in this ledger is PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN unless explicitly stated otherwise. Inherited Research-side approved project defaults retain their original IDs and provenance instead of being relabeled as Battle empirical facts.

This ledger is intentionally small. Round 2 does not pre-fill future unknowns merely to make the table look productive.

Current Battle-owned Runtime Default set after 690222 binding governance resolution:

```text
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004
RD-SF-005
RD-SF-006
```

## RD-SF-001 — Legacy SkillDefinition classification compatibility

Mechanism: Shared Skill Taxonomy
Question: How should pre-Stage12 SkillDefinition instances be classified when the new metadata scaffold is introduced?
Research status: No historical-game claim. Existing Battle runtime currently routes SkillDefinition through an Active-skill-shaped SkillResolver.
Why Runtime must decide: adding mandatory classification without a migration rule would break existing constructors or silently change behavior.
Chosen Runtime default:

- legacy skill_type = ACTIVE
- legacy preparation_mode = NONE

Scope:

- compatibility for definitions created through the pre-Stage12 schema/API;
- newly authored Stage12 definitions should declare their classification explicitly.

Evidence classification:

PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN

Reopen trigger:

- discovery of an existing pre-Stage12 SkillDefinition that canonically represents a non-Active category;
- replacement of the legacy SkillResolver contract with a broader execution architecture.

Required tests:

- existing SkillDefinition behavior remains unchanged after schema scaffold;
- explicit non-Active metadata is not overwritten by the compatibility default.

## RD-SF-002 — Loaded Skill Provider enumeration order

Mechanism: Provider Identity / Enumeration
Question: What deterministic order does the registry expose for serializable loaded Skill Provider enumeration?
Research status: Intimidation proves eligible categories and random single selection, but does not prove server container order or selection weighting.
Why Runtime must decide: deterministic replay and serialization require stable enumeration independent of dict insertion history.
Chosen Runtime default:

Owner-local enumeration:
1. SkillSlot numeric order ascending: INHERENT 0, LEARNED_1 1, LEARNED_2 2.
2. skill_id as deterministic consistency tiebreaker.

If whole-battle enumeration is later needed, owner_id precedes slot in the canonical sort key.

Scope:

- identity enumeration only;
- does NOT define Intimidation selection weighting;
- does NOT prove uniform 1/N selection;
- does NOT decide empty eligible-pool behavior.

Evidence classification:

PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN

Reopen trigger:

- a later authoritative architecture establishes another canonical loadout order;
- Research exposes observable selection ordering that requires a different deterministic mapping.

Required tests:

- same registered providers enumerate identically regardless of insertion order;
- INHERENT slot 0 is retained and ordered before learned slots;
- duplicate owner/slot remains rejected.

## Explicitly not decided in Round 2

The following are not defaults yet:

- Intimidation uniform/equal selection probability.
- Intimidation empty eligible-pool behavior.
- Equipment/Bingshu eligibility for Intimidation.
- Provider-validity cycle fallback: no gameplay fallback is selected. Round 3 declares dependency cycles an explicit unsupported boundary that raises `DependencyCycleError`; this is not a PROJECT_RUNTIME_DEFAULT because no allow/deny value is invented.
- Any Stage13/14/15 execution behavior.

At the Round 2 checkpoint DQ-SF-14 remained CONTRACT_DEPENDENT / OPEN. Round 9 later finalizes the governance classification without retroactively inventing answers for these boundaries.


## SF Round 3 default disposition — 2026-09-27

New Runtime Defaults added: **NONE**.

Round 3 deliberately avoids three fake defaults:

1. Suppression-cause ordering is semantically a set. Implementations may sort stable serialization keys for deterministic output, but order has no gameplay authority and is not a server-behavior claim.
2. Dependency cycles have no guessed gameplay answer. Evaluation/topology validation raises `DependencyCycleError`; no fixed-point, ALLOW, DENY, or “last writer wins” fallback is chosen.
3. Source death has no universal Provider/state invalidation default. A liveness dependency exists only when a contract/runtime record explicitly declares it.

Therefore RD-SF-001 and RD-SF-002 remain the only Shared Foundation Runtime Defaults after Round 3.

## RD-SF-003 — Same-envelope lifecycle settlement ordering

Mechanism: Shared State Lifecycle / Effectiveness Transition  
Question: If a state and one of its suppression sources are both due to leave in the same lifecycle envelope, does Runtime expose a transient resume before the due state is removed?

Research status: Insight freezes only the observable boundary that expiry / suppression-source removal settles before later behavior depending on the resulting privilege. It does not prove hidden function-level micro-order for two states due in the same envelope.

Why Runtime must decide: transaction/transition architecture needs a deterministic order and must avoid a due-to-expire state briefly regaining gameplay authority merely because its suppressor is removed first.

Chosen Runtime default:

1. Snapshot the complete set of states due for physical expiry/removal at the current lifecycle settlement envelope.
2. Commit that due-removal set in deterministic `instance_id` order.
3. Only after the due-removal batch is complete, recompute the affected StateEffectiveness / ProviderValidity dependency closure.
4. Invoke synchronous transition ports and permit later gameplay behavior.
5. A state included in the due-removal snapshot cannot emit/own a transient resume in that envelope.

Scope:

- same-envelope lifecycle settlement ordering only;
- does not change a contract's duration;
- does not define server-internal call order;
- does not authorize removal classes that a contract leaves bounded;
- deterministic `instance_id` ordering is a project serialization/observation choice, not original-game evidence.

Evidence classification:

`PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`

Reopen trigger:

- model-separating evidence proves an observable transient resume in this exact same-envelope case;
- a later authoritative lifecycle contract freezes another externally visible order.

Required tests:

- state and suppressor both due in same envelope -> due state never transiently resumes;
- suppressor due but state remains live -> state resumes after due-removal batch;
- multiple due states settle deterministically without replay;
- no later gameplay behavior observes a pre-settlement privilege.

## SF Round 4 default disposition — 2026-09-27

New Runtime Defaults added: **RD-SF-003 only**.

No defaults are added for Provocation/Capture reapplication, Intimidation specialized removal/source death, FalseReport stronger/weaker conflict, Sabotage stronger different-source replacement, or unknown cleanse classes. Those remain explicit bounded/unsupported contract edges.


## SF Round 5 default disposition — 2026-09-27

New Runtime Defaults added: **NONE**.

Round 5 closes architecture without inventing original-game behavior:

1. Provider-invalid vs holder-permission blocker ordering is not gameplay semantics. A composed internal decision may serialize blockers deterministically, but public event vocabulary/primary-reason presentation remains DQ-SF-13 and is not a PROJECT_RUNTIME_DEFAULT here.
2. MISSING / IDENTITY_MISMATCH / BASELINE_DISABLED / SUPPRESSED are already canonical ProviderValidityPolicy outcomes, not guessed defaults. For an explicitly Provider-dependent JIT opportunity, every non-VALID outcome rejects that opportunity before its owned RNG.
3. A silent production NoopPreparationInterruptionPort is not adopted as a completion default. Before a concrete preparation owner exists, tests may use a Fake port; production composition may only use an explicit no-preparation placeholder under the invariant that PREPARING work cannot exist, and affected state Runtime Freeze may not claim the preparation contract complete.
4. Provider resume does not auto-activate or restore old preparation. This is contract-derived future-only semantics, not a project default.

Therefore RD-SF-001, RD-SF-002 and RD-SF-003 remain the complete Shared Foundation Runtime Default set after Round 5.


## SF Round 6 default disposition — 2026-09-27

New Runtime Defaults added: **NONE**.

Round 6 closes target architecture without converting bounded Provocation/Capture evidence into guessed gameplay:

1. Provocation CHOOSE_N freezes the observable target-set contract only: preserve N and include an admissible Source exactly once. Whether Runtime eventually implements that as reserve-Source-then-sample or sample-then-replace is intentionally not selected here because it can change the RNG stream; DQ-SF-12 / BU-P02 retains that decision.
2. Provocation insufficient-target behavior remains BU-P09 / bounded. The current TargetSystem.random_units() implementation truncates count to the candidate pool, but Round 6 explicitly does not promote that legacy helper behavior into the Stage12 CHOOSE_N contract.
3. Simultaneous multi-source Provocation / reapplication precedence remains BU-P06 / bounded. No latest-wins, lowest-id-wins or random-source rule is invented.
4. Capture ALL_ALLIES remains Q42 / bounded; verified friendly single/multi exclusion is not generalized to an all-allies contract.
5. Capture delayed/already-locked friendly work remains Q44/Q45 + DQ-SF-23; no JIT recheck default is invented.

Therefore RD-SF-001, RD-SF-002 and RD-SF-003 remain the complete Shared Foundation Runtime Default set after Round 6.


## SF Round 7 default disposition — 2026-09-27

New Runtime Defaults added: NONE.

1. Contribution ordering remains domain-owned; EquipmentEffectivenessPolicy only filters.
2. Tested SABOTAGE scheduled due-window behavior is contract-derived. Broader queued/in-flight micro-order remains DQ-SF-23 / B-SAB-07.
3. FALSE_REPORT untested equipment categories remain explicit UNSUPPORTED_BOUNDARY.
4. CAPTURE equipment reactive/damage remains Q63 UNSUPPORTED_BOUNDARY.
5. Dynamic equipment change / empty-equipment behavior remains bounded where not frozen.
6. Policy/registry consume zero RNG; no new RNG ordering/signature default is introduced.

RD-SF-001, RD-SF-002 and RD-SF-003 remain the complete Shared Foundation Runtime Default set after Round 7.


## SF Round 9 Runtime Default finalization — 2026-09-27

DQ-SF-14 verdict:

~~~text
CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
~~~

The architecture is closed because every currently known bounded/unknown candidate has an explicit governance category.
This does not mean every gameplay question has an answer.

### Governance invariant

~~~text
Research cannot determine
+
Runtime MUST choose deterministic behavior now
-> PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN

Runtime can reject or defer the unsupported path
-> UNSUPPORTED_BOUNDARY or NOT CURRENTLY IMPLEMENTED / DEFERRED
~~~

UNKNOWN is not a reason to manufacture a Default.

### Current Battle-owned Runtime Default set

~~~text
RD-SF-001
Legacy SkillDefinition classification compatibility

RD-SF-002
Loaded Skill Provider deterministic enumeration order

RD-SF-003
Same-envelope lifecycle settlement ordering
~~~

Round 9 adds:

~~~text
NEW RUNTIME DEFAULTS = NONE
~~~

RD-SF-001 / RD-SF-002 / RD-SF-003 remain the complete Battle-owned Shared Foundation Runtime Default set.

### Inherited Research-side approved project defaults

The following are authoritative project defaults already frozen by the INSIGHT Research contract.
They are referenced here but are not renumbered into RD-SF entries.

#### PD-INS-001 — Insight RNG consumption parity

Governance/provenance:

~~~text
INHERITED PROJECT DEFAULT
APPROVED_PROJECT_DEFAULT in 690089 INSIGHT contract
NOT an empirical claim about hidden server PRNG internals
~~~

Runtime substance:

~~~text
if originating protected-control generation normally owns a proc RNG:
    consume that normal source RNG
if the control is deterministic:
    consume no synthetic RNG
then:
    candidate -> Insight admission -> possible rejection
~~~

Round 9 consequence:
Insight does not skip normal source-generation RNG and does not add extra RNG.

Reopen trigger:
- audited 690089 contract amendment;
- direct model-separating evidence sufficient to change PD-INS-001;
- replacement of the project-wide RNG governance with higher authority.

Required tests:
- probabilistic protected-control source keeps RNG parity under Insight;
- deterministic protected-control source gains no draw.

#### PD-INS-002 — Insight reapplication saturation

Governance/provenance:

~~~text
INHERITED PROJECT DEFAULT
APPROVED_PROJECT_DEFAULT in 690089 INSIGHT contract
stronger replacement remains empirically unobserved
~~~

Runtime substance:
while one canonical Insight remains PRESENT, whether ACTIVE or SUPPRESSED, incoming Insight is rejected;
no stack, replacement, refresh, or backup queue is created.

Round 9 classification:
Insight stronger replacement is therefore not a new Battle Runtime Default. It is already governed by inherited PD-INS-002.

Reopen trigger:
- audited 690089 contract amendment;
- direct evidence proving a stronger-priority replacement rule;
- higher-authority cross-contract rule.

Required tests:
- ACTIVE Insight + incoming Insight rejects/no refresh;
- SUPPRESSED-but-PRESENT Insight + incoming Insight rejects/no replacement.

### Round 9 unresolved-candidate classification

| Candidate | Research/contract state | Governance category | Why no new Runtime Default now | Reopen / escalation trigger |
|---|---|---|---|---|
| Insight stronger replacement | UNOBSERVED | INHERITED PROJECT DEFAULT | PD-INS-002 already supplies the lawful deterministic project behavior | 690089 amendment / direct stronger-replacement evidence |
| Intimidation selection weights | exact weights unproven; uniform 1/N forbidden as research claim | NOT CURRENTLY IMPLEMENTED / DEFERRED | Stage12 design can defer the selector distribution choice until integration requires it | implementation cannot proceed without a distribution; then create a labeled default before code |
| Intimidation empty eligible pool | unproven | UNSUPPORTED_BOUNDARY | runtime can reject/surface unsupported instead of inventing state-application semantics | direct evidence or integration requirement with explicit default proposal |
| Provocation CHOOSE_N RNG micro-order | BU-P02 / hidden sequence unknown | NOT CURRENTLY IMPLEMENTED / DEFERRED | observable target-set contract is known while exact sampling topology can remain deferred | implementation requires reserve-first vs sample/replace; record selection topology and RNG consequences first |
| Provocation insufficient candidates | BU-P09 | UNSUPPORTED_BOUNDARY | legacy TargetSystem truncation is not promoted to Stage12 contract truth | direct evidence or mandatory implementation case |
| Provocation multi-source precedence | BU-P06 | UNSUPPORTED_BOUNDARY | no latest/earliest/random-source behavior is required for supported single-source path | direct evidence or mandatory overlap support |
| FalseReport stronger/weaker | B-U01 | UNSUPPORTED_BOUNDARY | supported equal-strength behavior does not require stronger replacement semantics | direct stronger/weaker evidence or mandatory implementation case |
| Sabotage stronger/multi-source | B-SAB-02 | UNSUPPORTED_BOUNDARY | supported cases do not require a guessed overlap model | direct overlap evidence or mandatory implementation case |
| Sabotage queued/JIT | B-SAB-07 | UNSUPPORTED_BOUNDARY | tested scheduled due-window already has a rule; broader queued/in-flight work can remain unsupported | owning-operation evidence/default becomes necessary |
| Capture Q16 already-created DamageRequest | bounded | UNSUPPORTED_BOUNDARY | ExecutionRightSpec can represent the unsupported micro-slice without choosing JIT/snapshot | direct evidence or mandatory support |
| Capture Q42 ALL_ALLIES | bounded | UNSUPPORTED_BOUNDARY | verified friendly SINGLE/CHOOSE_N path functions without generalizing ALL_ALLIES | direct Q42 evidence or mandatory support |
| Capture Q44 delayed friendly work | bounded | UNSUPPORTED_BOUNDARY | per-dimension execution-right spec can expose unsupported mode | direct evidence or mandatory delayed-work support |
| Capture Q45 already-locked friendly target | bounded | UNSUPPORTED_BOUNDARY | LOCKED provenance can remain unsupported without becoming NEW_QUERY | direct evidence or mandatory locked-target support |
| Capture multi-source/reapplication Q70-Q74 | SOURCE_SKILL_BOUNDED_UNKNOWN | UNSUPPORTED_BOUNDARY | State Core need not invent stack/refresh/replace semantics | direct evidence or mandatory multi-source support |
| Capture Q63 reactive/damage equipment | bounded | UNSUPPORTED_BOUNDARY | verified ATTRIBUTE contribution scope does not require reactive/damage generalization | direct Q63 evidence or mandatory support |

### Event representation is not automatically a Runtime Default

Round 9 chooses event-schema compatibility such as:

- one state-application rejection fact with an ADMISSION/CONFLICT discriminator;
- one RECOVERY_PREVENTED public fact with internal multiple causes and compatibility primary reason.

These are architecture/observation schema decisions when they do not alter gameplay outcome.
They do not enter this ledger merely because engineering must choose a payload shape.

### Provocation RNG/default coupling guard

If the deferred CHOOSE_N micro-order ever becomes mandatory, the future default entry must record together:

~~~text
Default ID
Mechanism / BU-P02
selection topology
RNG owner
RandomSystem API call topology
draw/no-draw rejection cases
replay consequences
scope
reopen trigger
tests
PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN
~~~

Writing only "reserve Source first" without its RNG consequences is insufficient governance.

### Default provenance guard

No implementation may leave a project-default behavior with only its behavior and delete the provenance label.

Required labels remain:

~~~text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
~~~

or the exact inherited Research project-default authority label.

This prevents a deterministic engineering choice from being mistaken later for official observed mechanics.

### Round 9 final ledger state

~~~text
Battle Runtime Defaults:
RD-SF-001
RD-SF-002
RD-SF-003

Inherited approved Research project defaults:
PD-INS-001
PD-INS-002

New Round 9 Battle Runtime Defaults:
NONE

DQ-SF-14:
CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED
~~~

## SF Round 11 Independent Design Audit — AUDIT-DRIVEN CORRECTION

The independent design audit found that the EXHAUSTION denied-ACTIVE RNG placement was already a deterministic Runtime choice but had been described only as architecture. The frozen 690101 contract explicitly leaves hidden blocked-attempt activation RNG unobservable and requires explicit project governance for any Runtime choice. That choice therefore needs a Runtime Default ID.

### RD-SF-004 — EXHAUSTION denied-ACTIVE activation-RNG placement

Mechanism: 690101 EXHAUSTION / Skill operation admission  
Question: When an otherwise eligible new ACTIVE operation is denied by effective EXHAUSTION, does Runtime consume that operation's activation-probability RNG or target-selection RNG before denial?

Research status: The 690101 frozen contract states that blocked-attempt hidden activation RNG consumption is UNOBSERVABLE and freezes neither mandatory consumption nor mandatory non-consumption.

Why Runtime must decide: deterministic replay requires one stable placement. The Shared Foundation SkillOperationAdmission topology already places ProviderValidity + SkillPermission + operation admission before activation RNG and target-operation creation.

Chosen Runtime default:

1. A NEW ACTIVE admission denied by effective EXHAUSTION consumes **zero activation RNG** for that denied operation.
2. It creates no TargetOperation and therefore consumes **zero target-selection RNG**.
3. The rule applies only to the denied new admission. Already-admitted work is not re-admitted and is governed by its frozen ExecutionRightSpec.
4. This default does not alter PD-INS-001 source-generation RNG parity, state-application RNG, Intimidation binding RNG, RecoveryOpportunity RNG, equipment-trigger RNG, or any other domain-owned draw.

Evidence classification: `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`

Reopen trigger:
- direct model-separating evidence for blocked EXHAUSTION attempts establishes observable RNG-stream consequences;
- a later authoritative skill-runtime contract fixes another ordering;
- the project-wide deterministic replay policy is superseded by higher authority.

Required tests:
- effective EXHAUSTION denied ACTIVE -> zero activation RNG;
- denied ACTIVE -> no TargetOperation and zero target RNG;
- suppressed/removed EXHAUSTION -> normal ACTIVE path reaches ordinary activation RNG;
- already-admitted ACTIVE is not re-admitted and gains no synthetic draw;
- identical seed + identical decisions replay identically.

### Round 11 current default set

```text
Battle Runtime Defaults:
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004

Inherited approved Research project defaults:
PD-INS-001
PD-INS-002
```

Earlier statements that Round 9 added no new Runtime Default remain historical Round 9 records. At the Round 11 checkpoint, the complete Battle-owned set was RD-SF-001 through RD-SF-004; BU-P02 governance later adds RD-SF-005.

Audit finding: `SF-AUD-11-001`  
Resolution: `CLOSED_BY_AUDIT_DRIVEN_CORRECTION`


## BU-P02 Runtime Governance Resolution — 2026-09-27

The 690108 PROVOCATION integration reached a point where BU-P02 could no longer remain deferred: CHOOSE_N must be implemented without laundering the hidden original-game slot/RNG micro-order into Research fact. The governance decision below closes only that simulator implementation gap. The 690108 Research contract remains FROZEN and BU-P02 remains empirically bounded.

### RD-SF-005 — PROVOCATION CHOOSE_N required-target reserve-first topology

Mechanism: 690108 PROVOCATION / CHOOSE_N required-target enforcement  
Question: For a supported fresh RANDOM CHOOSE_N(N) Skill target operation with one admissible Provocation Source that must appear exactly once, does Runtime reserve the required Source before sampling the remaining slots, or sample N first and replace a sampled target if the Source is absent?

Research status:

```text
BU-P02 exact hidden selection / RNG micro-order
= CLOSED_WITH_BOUNDED_UNKNOWN
```

The frozen observable rule is only:

```text
admissible Source
+ CHOOSE_N(N)
-> Source included exactly once
-> total cardinality N preserved
```

Why Runtime must decide: deterministic replay requires one stable random-call topology before 690108 gameplay integration can proceed. The existing Shared Foundation separates zero-RNG policy constraints from the canonical selector/TargetSystem RNG owner and already represents required targets as cardinality-consuming slots.

Chosen Runtime default:

1. **Reserve-first.** Deduplicated legal `required_target_ids` consume target-cardinality slots before the selector fills the remainder.
2. For the supported ordinary Provocation case, `required_count = 1` and `remaining_slots = N - 1`.
3. The required Source is removed from the selector population. The selector receives only `eligible - required`.
4. The final target list is `required + selector_fill`; there is no post-selector replacement/mutation step.
5. `SkillTargetPolicy` and the Provocation adapter consume zero RNG. Target sampling remains owned by `TargetSystem -> BattleContext.random / RandomSystem`.
6. The selector call is `TargetSystem.random_units(context, remaining, count=remaining_slots)`. For supported sufficient-candidate cases:
   - `remaining_slots == 0` -> zero `RandomSystem.sample` call;
   - `len(remaining) == remaining_slots` -> zero `RandomSystem.sample` call and deterministic all-candidate ordering through the existing TargetSystem rule;
   - `0 < remaining_slots < len(remaining)` -> exactly one `RandomSystem.sample(remaining, remaining_slots)` API call.
7. This default does **not** authorize the legacy truncation behavior when legal candidates are insufficient. BU-P09 remains `UNSUPPORTED_BOUNDARY` until separately governed or evidenced.
8. This default is scoped to `NEW_QUERY + CHOOSE_N + TargetSelectorKind.RANDOM` where the supported target operation has an admissible required Provocation Source. SINGLE and FIXED_ALL keep their already-frozen semantics.
9. DETERMINISTIC selectors continue to use the generic required-slot architecture but acquire no invented RNG semantics from RD-SF-005. EXPLICIT selection is outside this BU-P02 RNG default and must remain fully specified/validated by its own boundary.
10. `INHERIT_RESOLVED`, `DERIVE_FROM_RESOLVED`, and `LOCK_RESOLVED` never re-run this selection. A committed `TargetSelectionResult` remains historical fact.

Candidate comparison:

| Dimension | Reserve-first | Sample-then-replace |
|---|---|---|
| Shared Foundation topology | Reuses required-slot -> selector pipeline | Requires post-selector result mutation |
| RNG owner | TargetSystem remains sole target RNG owner | TargetSystem samples, then another layer must mutate |
| Policy RNG | 0 | 0 only if replacement victim is deterministic |
| Random population | `eligible - required` | full eligible pool |
| Random sample size | `N - required_count` | `N` |
| Secondary rule needed | none for supported single required Source | replacement-victim rule if Source absent |
| Replay contract | one explicit selector topology | extra mutation rule can alter replay semantics |
| Existing generic code | already matches | requires redesign/reopen pressure |
| Governance cost | minimal explicit default | creates a second unresolved micro-policy |

Decision rationale: reserve-first is adopted **not because the implementation happens to do it**, but because it preserves the frozen owner topology, introduces no new RNG owner, needs no post-resolution mutation rule, and yields the smallest deterministic replay contract consistent with the frozen observable target-set rule.

Evidence classification:

```text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
```

This decision does **not** claim empirical evidence for the game's hidden target-selection micro-order.

Replay consequence:

Given the same seed, battle state, `TargetOperation`, Provocation effectiveness, legal candidate order and required Source identity, Runtime must produce the same TargetSystem API-call topology, same final `TargetSelectionResult`, and same subsequent RNG stream position.

Reopen trigger:

- Tier-A/model-separating battle evidence or official-client evidence establishes a different observable CHOOSE_N micro-order;
- a stronger deterministic replay trace from authoritative runtime evidence distinguishes a different topology;
- a later higher-authority Shared Foundation redesign supersedes the required-target selector contract.

Required executable tests:

```text
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
```

Current Battle-owned Runtime Defaults after this resolution:

```text
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004
RD-SF-005
```

690108 Research remains FROZEN. BU-P02 empirical status remains bounded. RD-SF-005 exists only to give the simulator a deterministic, traceable and reversible implementation rule.


## 690222 Binding Selection Runtime Governance Resolution — 2026-09-28

The 690222 INTIMIDATION integration gate made selection weighting non-deferrable. Research freezes only that exactly one supported eligible Skill Provider is selected randomly and explicitly does not prove uniform/equal/1/N weighting. Runtime therefore records the smallest deterministic simulator rule without laundering it into Research fact.

### RD-SF-006 — INTIMIDATION uniform eligible-Provider binding selection

Mechanism: 690222 INTIMIDATION  
Question: When the already-constructed supported eligible Provider pool contains multiple candidates, what probability distribution and RandomSystem API topology does Runtime use for the one binding decision?

Research status:

```text
exactly one eligible skill is randomly selected
refresh performs selection again
uniform / equal / 1/N is not empirically proven
```

Chosen Runtime default:

1. Pool construction remains owned by the frozen Intimidation consumer boundary: loaded Skill Providers for the Holder, RD-SF-002 stable ordering, and supported SkillType-domain filtering.
2. Loaded enumeration does not itself filter ProviderValidity. BASELINE_DISABLED or already-SUPPRESSED identity remains loaded identity; this resolution does not invent a new validity-based denominator filter.
3. Supported families are ACTIVE (including PreparationMode.REQUIRED), ASSAULT, PASSIVE, COMMAND and TROOP.
4. FORMATION is excluded; NORMAL_ATTACK is outside the Skill Provider domain.
5. TALENT, EQUIPMENT and BINGSHU remain unsupported/not frozen for Intimidation eligibility.
6. If `eligible_count == 1`, select the sole Provider with **0 binding RNG**.
7. If `eligible_count >= 2`, select uniformly over the stable pool with exactly one `BattleContext.random.choice(pool)` / `RandomSystem.choice(pool)` API operation.
8. If `eligible_count == 0`, retain the existing `UNSUPPORTED_BOUNDARY`; RD-SF-006 does not invent rejection, no-binding, or fallback semantics.
9. Successful CREATE and successful REFRESH perform a binding decision under the same rule. REFRESH may select the same Provider again and still counts as a new binding decision.
10. RESUME retains the existing binding, application generation and lifetime progress and consumes **0 binding RNG**.
11. Admission/conflict rejection, including confirmed Gangyi rejection before binding selection, consumes **0 binding RNG**.
12. The binding selector does not import Python `random`, create a local RNG, use a hash mapping, shuffle the pool, or add a second random draw.

Evidence classification:

```text
PROJECT_RUNTIME_DEFAULT
NOT_EMPIRICALLY_FROZEN
```

This default does not claim the original game's hidden binding weights.

Why this default:

- it adds no unexplained slot/type/source weight parameters;
- it is symmetric when weight evidence is absent;
- it preserves RandomSystem as the sole RNG service;
- it uses RD-SF-002 stable population order;
- it has one explicit API-level replay decision for multi-candidate pools;
- it is easy to replace if stronger authority appears.

Rejected alternatives:

- slot-weighted distribution: no authority for weights;
- SkillType-weighted distribution: no authority for weights;
- source/rarity/history weighting: no authority and extra metadata;
- deterministic hash selection: bypasses canonical RandomSystem accounting.

Replay signature includes at least seed/current RNG state, Holder identity, application generation, stable supported eligible Provider list, Provider identities and RD-SF-006 provenance/version.

Reopen trigger:

- Tier-A model-separating battle evidence;
- official-client evidence;
- deterministic observation distinguishing uniform from weighted selection;
- higher-authority gameplay evidence;
- audited/frozen 690222 contract amendment;
- later Shared Foundation governance explicitly superseding RD-SF-006.

Required governance tests:

```text
test_binding_default_has_project_runtime_provenance
test_binding_default_not_empirical_claim
test_stable_provider_ordering_uses_rd_sf_002
test_single_candidate_selection
test_single_candidate_rng_call_topology
test_multiple_candidate_selection_uses_canonical_rng
test_same_seed_same_pool_same_binding
test_downstream_rng_stream_is_stable
test_rejected_application_consumes_zero_binding_rng
test_refresh_performs_new_binding_selection
test_refresh_can_select_same_provider_legitimately
test_resume_consumes_zero_binding_rng
test_resume_retains_binding
test_empty_pool_remains_unsupported
test_talent_boundary_remains_unsupported
test_all_candidates_reachable_across_deterministic_seed_set
test_loaded_provider_pool_is_not_provider_validity_filtering
```

Current Battle-owned Runtime Defaults after this resolution:

```text
RD-SF-001
RD-SF-002
RD-SF-003
RD-SF-004
RD-SF-005
RD-SF-006
```

690222 Research remains FROZEN. The uniform distribution exists only as a simulator Runtime Default. Gameplay remains NOT_INTEGRATED and Stage12 Runtime Frozen remains 4 / 7.

## STAGE12_FINAL_COMPLETION_DEFAULTS — 2026-09-28

Final provenance audit = PASS. RD-SF-001 through RD-SF-006 retain `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`.
No Runtime Default is promoted to Research Fact, Official Truth, or battle-report-confirmed truth by Stage12 completion.
