# Stage12 Runtime Default Ledger

Date: 2026-09-27
Status: CONTRACT_DEPENDENT_WITH_ARCHITECTURE_CLOSED / COMPLETE FOR CURRENTLY REQUIRED DETERMINISTIC CHOICES
Purpose: record only engineering choices that Runtime must make where Research does not freeze an original-game answer.

Every RD-SF entry in this ledger is PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN unless explicitly stated otherwise. Inherited Research-side approved project defaults retain their original IDs and provenance instead of being relabeled as Battle empirical facts.

This ledger is intentionally small. Round 2 does not pre-fill future unknowns merely to make the table look productive.

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
