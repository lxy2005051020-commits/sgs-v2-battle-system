# Stage12 Contract → Runtime Mapping Skeleton

> Status: **ALL SEVEN CONTRACT→RUNTIME INTEGRATIONS FROZEN / FINAL STAGE AUDIT PASS**nsion is mandatory before each state's implementation begins.

| State | Contract Rule Group | Runtime Owner / Hook Candidate | Required discriminator | Mapping Status |
|---|---|---|---|---|
| INSIGHT | protected-control incoming admission | Stage12 state-admission policy → StateLifecycleSystem.apply seam | protected control rejected vs FALSE_REPORT/INTIMIDATION/CAPTURE special boundaries | DESIGN_MAPPING |
| INSIGHT | existing protected control suppression | Stage12 effective-state read/policy | resident-but-suppressed vs physically removed | DESIGN_MAPPING |
| INSIGHT | resume after Insight ends | lifecycle + effective-state policy | resume if lifetime alive vs recreate/restart | DESIGN_MAPPING |
| INSIGHT | v0.4 protected taxonomy | canonical contract data/constants | SABOTAGE protected; CAPTURE not protected | DESIGN_MAPPING |
| EXHAUSTION | ACTIVE_SKILL permission | Stage12 skill-permission policy | Active blocked vs Basic Attack allowed | DESIGN_MAPPING |
| EXHAUSTION | preparation start/interruption | minimal preparation interoperability hook | existing PREPARING interrupted; no Stage15 runtime | DESIGN_MAPPING |
| EXHAUSTION | already-activated instance | admission boundary | in-flight activated skill not rolled back | DESIGN_MAPPING |
| FALSE_REPORT | admission exceptions | Stage12 state-admission policy | ordinary Insight does not reject | DESIGN_MAPPING |
| FALSE_REPORT | PASSIVE/COMMAND Provider suppression | provider-validity policy | Provider suppressed vs Holder-only model | DESIGN_MAPPING |
| FALSE_REPORT | tested equipment specials boundary | EquipmentEffectivenessPolicy evidence-scoped rule adapter | tested persistent equipment special suppressed; untested category remains UNSUPPORTED_BOUNDARY | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| FALSE_REPORT | restoration | provider-validity + lifecycle | future behavior resumes; no missed-trigger replay | DESIGN_MAPPING |
| PROVOCATION | eligible skill target operation/query | `SkillDefinition` → `SkillResolver` → `TargetOperation` → `SkillTargetPolicy` | fresh operation-level constraint vs blanket target overwrite | RUNTIME_FROZEN_TO_CONTRACT |
| PROVOCATION | Source admissibility | `SkillTargetPolicy` operation-local eligibility after raw candidates | admissible Source required; illegal/dead Source never forced and State is not physically removed | RUNTIME_FROZEN_TO_CONTRACT |
| PROVOCATION | Resident != Effective | `StateEffectivenessPolicy` | source death leaves state resident; Insight/Provider suppression does not remove | RUNTIME_FROZEN_TO_CONTRACT |
| PROVOCATION | Taunt/Confusion boundaries | `TargetResolutionSystem` remains Normal Attack owner; `SkillTargetPolicy` handles eligible Skill operations | Confusion-owned Skill target decision pre-empts Provocation via TargetEligibilityContext metadata; Taunt stays NormalAttack domain | RUNTIME_FROZEN_TO_CONTRACT |
| INTIMIDATION | single selected Provider binding | provider-validity policy + Stage12 params + RD-SF-006 selector governance | one provider disabled vs all skills disabled | GOVERNANCE_READY / GAMEPLAY_NOT_INTEGRATED |
| INTIMIDATION | refresh reroll | provider-validity policy + RandomSystem + RD-SF-006 | release old → exactly one reroll → no multi-disable stack | GOVERNANCE_READY / GAMEPLAY_NOT_INTEGRATED |
| INTIMIDATION | resume preserves binding | provider-validity + lifecycle + RD-SF-006 no-draw rule | resume does not reroll; lifetime continues | GOVERNANCE_READY / GAMEPLAY_NOT_INTEGRATED |
| INTIMIDATION | source-skill counter separation | source-skill boundary ledger | no counter/damage branch inside state core | DESIGN_MAPPING |
| SABOTAGE | equipment effectiveness suppression | EquipmentEffectivenessPolicy.evaluate_contribution | target-owned tested contribution suppressed vs physical unequip/delete | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| SABOTAGE | existing effects/remote ownership | explicit EquipmentContributionDependency -> EquipmentEffectivenessPolicy | Equipment Owner suppression affects dependent remote live effect; unrelated Holder Provider remains valid | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| SABOTAGE | restoration | EquipmentEffectivenessPolicy + existing lifecycle/domain owners | final-cause removal resumes future eligibility; no reinitialize/replay | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | natural action denial | ActionSystem two-phase action admission/block seam | effective Capture denies Natural Action before NormalAttack creation; Capture denial does not consume STUN | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | actor-driven new damage denial | Damage domain typed work admission/execution-right seam | current actor + work category distinguish new/counter damage from attached DOT/free proxy | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | PASSIVE/COMMAND invalidation | ProviderValidityPolicy | provider behavior suspended vs historical effect deletion; source death does not end established Capture | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | recovery to zero | RecoverySystem prevention phase | Capture + HealingBlock may coexist as causes after modifier/second CEIL; self targetability remains separate | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | friendly target exclusion | `SkillTargetPolicy` eligibility phase | verified friendly SINGLE / CHOOSE_N excludes captured holder; enemy targetability and raw allies query unchanged | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | restoration | composed domain owners + StateLifecycleSystem | RESUME / future-only; no missed action/counter/recovery/trigger replay | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |
| CAPTURE | source death independence | StateLifecycleSystem | established Capture remains; origin source alive is never a universal future-execution gate | DESIGN_FROZEN_FOUNDATION / NOT IMPLEMENTED |

## Completion rule

A row may move from `DESIGN_MAPPING` to `GREEN` only after:

```text
contract rule identified
→ canonical owner fixed
→ concrete method/hook named
→ positive test
→ negative test
→ discriminating test
→ required cross-state test
→ regression green
```

Bounded unknowns that require an engineering choice must be linked to `STAGE12_RUNTIME_DEFAULT_LEDGER.md` and labelled `PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN`.

## SF-0 mapping qualification — 2026-09-27

This remains a skeleton. [Reconnaissance](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/blob/f0339729a94685f1d1ae226e1975ad4298b7f81f/stages/stage12/STAGE12_SHARED_FOUNDATION_ARCHITECTURE_RECONNAISSANCE.md)
section 2 maps all seven current contracts to rule groups; the method-level completed design is future work.
INSIGHT existing-control suppression must include the AR-SF-01 legacy CONFUSION discriminator.
Provider validity must cover RecoveryOpportunitySystem's existing gate, not TriggerSystem alone.
Capture equipment attributes, ordinary-cleanse resistance, actor/proxy provenance, and queued-work
boundaries are tracked in DQ-SF-11/19/23/25 and must not disappear from the completed mapping.


## SF Round 2 frozen design bindings — 2026-09-27

These rows are DESIGN_FROZEN_FOUNDATION, not GREEN. GREEN still requires implementation and tests.

| Foundation item | Authority | Frozen design binding | Implementation status |
|---|---|---|---|
| Insight × existing Confusion | STAGE12_INSIGHT_CONFUSION_AUTHORITY_MIGRATION.md + Insight v0.4 §§3/4/7/8/21/22 | resident Confusion becomes ineffective under effective Insight; timer continues; surviving instance resumes; old P0-CFS-P93-01 claim narrowly superseded | NOT IMPLEMENTED |
| Skill taxonomy | DQ-SF-04 | SkillType ACTIVE/ASSAULT/PASSIVE/COMMAND/TROOP/FORMATION/TALENT; PreparationMode orthogonal; Normal Attack non-skill operation; equipment special separate ProviderCategory; TALENT is a FALSE_REPORT negative discriminator only | NOT IMPLEMENTED |
| Skill Provider identity | DQ-SF-05 | SkillProviderRef(owner_id, slot, skill_id); Registry resolves owner+slot and validates expected skill ID | NOT IMPLEMENTED |
| Equipment Provider identity | DQ-SF-05 / DQ-SF-11 boundary | EquipmentProviderRef(owner_id, provider_key) enters typed ProviderRef union without masquerading as Skill | DESIGN ONLY |
| Provider enumeration | RD-SF-002 | deterministic slot order 0/1/2 for identity enumeration; no implied Intimidation weighting | NOT IMPLEMENTED |
| Legacy SkillDefinition classification | RD-SF-001 | compatibility default ACTIVE + PreparationMode.NONE; new Stage12 definitions explicit | NOT IMPLEMENTED |
| Recovery source gate migration | DQ-SF-21 | RecoveryOpportunitySystem Gate 4 constructs SkillProviderRef with slot-is-not-None + expected skill_id, delegates to ProviderValidityPolicy, rejects all non-VALID statuses before probability RNG | DESIGN CLOSED / NOT IMPLEMENTED |
| Intimidation × Insight provenance | AR-SF-02 / DQ-SF-28 | use Intimidation §§5/11 as positive outcome authority; preserve Insight DIRECT_OVERLAP_UNOBSERVED evidence label | DESIGN AUTHORITY CLOSED |

Future mapping work must not move these rows to GREEN until code and discriminating tests exist.


## SF Round 3 frozen design bindings — effectiveness / Provider validity

These bindings are `DESIGN_FROZEN_FOUNDATION`, not GREEN.

| State / concern | Resident model | Effective dependency | Provider dependency | Suppression / authority target | Concrete shared hook |
|---|---|---|---|---|---|
| INSIGHT | physical StateInstance remains in Registry until Lifecycle removes it | suppressed if an explicit live Provider dependency is non-valid; otherwise effective subject to local lifecycle facts | explicit `ProviderDependency` only when the Insight contract/source requires live provider validity | protected-control StateEffectiveness decisions | `StateEffectivenessPolicy.evaluate_state` → protected-control rule |
| EXHAUSTION | resident timed control | effective unless independently suppressed/inactive; Insight can suppress existing Exhaustion | none inferred from source provenance | ACTIVE skill admission authority | shared state decision consumed later by SkillPermissionPolicy |
| FALSE_REPORT | resident control | own effectiveness is shared-state truth; ordinary Insight does not suppress it | none inferred globally | PASSIVE/COMMAND Provider validity; tested equipment boundary remains DQ-SF-11 | `ProviderValidityPolicy.evaluate_provider` |
| PROVOCATION | resident even when it cannot currently force a legal Source | shared policy may expose SOURCE_INADMISSIBLE/local inactivity; fine-grained operation admissibility remains DQ-SF-09 | none inferred globally | eligible skill target-operation authority only | state decision + future target policy |
| INTIMIDATION | resident control with stable selected ProviderRef binding | if Intimidation itself is ineffective, binding is preserved and produces no suppression | binding targets exactly one ProviderRef; any live dependency of Intimidation itself must be explicit | exactly selected Provider | state decision → ProviderValidityPolicy cause |
| SABOTAGE | resident protected control | Insight may suppress existing Sabotage under frozen protected-control rules | equipment linkage is explicit, not EffectSourceRef inference | tested equipment contributions/effects | StateEffectivenessPolicy; DQ-SF-11 equipment policy remains open |
| CAPTURE | resident control; source death does not remove established Capture | own current effectiveness from shared policy; ordinary Insight does not suppress Capture | none inferred from source survival | verified PASSIVE/COMMAND Providers; other composite restrictions remain domain-owned | ProviderValidityPolicy + later DQ-SF-19 consumers |

### Shared method-level migration map

| Existing method / consumer | Round 3 migration binding |
|---|---|
| Stage9StateRuntime.has_operational_insight | delegate to `StateEffectivenessPolicy.has_effective(owner, INSIGHT)` |
| Stage9StateRuntime.get_operational_confusion | resident read stays local; return only instance whose shared decision is EFFECTIVE |
| Stage9StateRuntime.get_taunt_suppressors | obtain effective Insight/shared suppression causes from StateEffectivenessPolicy; no `Registry.has(INSIGHT)` authority |
| Stage9StateRuntime.get_taunt_lifecycle_state / is_taunt_operational | shared state decision first; target/source domain checks remain Stage9 |
| Stage11StateRuntime.is_effective | thin delegate to StateEffectivenessPolicy |
| Stage11StateRuntime.effective_instances / has_effective | derive from delegated shared decisions |
| Stage11 remaining-use/source-dependent checks | migrate as local rule adapters consumed by StateEffectivenessPolicy; do not remain a second canonical truth |
| RecoveryOpportunitySystem JIT source skill gate | future DQ-SF-21 implementation resolves SkillProviderRef then delegates current validity to ProviderValidityPolicy before RNG |

No row is GREEN until production code and discriminating tests exist.

## SF Round 4 frozen lifecycle bindings — admission / transaction / clock / removal

These rows are `DESIGN_FROZEN_FOUNDATION`, not GREEN.

| State | Admission | Conflict / Refresh | Clock | Removal / Cleanse |
|---|---|---|---|---|
| INSIGHT | effective Insight is the admission blocker for protected incoming states; candidate rejection precedes their conflict path | PD-INS-002 rejects every incoming Insight while a canonical instance is PRESENT, including SUPPRESSED; no refresh/replace/backup | source-defined holder lifecycle; suppression never pauses | expiry/removal through Lifecycle; surviving protected controls re-evaluate after commit |
| EXHAUSTION | effective Insight rejects incoming Exhaustion | no universal reapplication rule added in Round 4 | physical lifetime continues while suppressed; skill-permission behavior remains DQ-SF-06 | evidence/source-lifecycle scoped; no new cleanse generalization |
| FALSE_REPORT | ordinary Insight does not reject; tested special protection may reject | equal-strength same/different-source reapply rejected with no refresh; stronger/weaker remains unsupported bounded | holder-relative action lifecycle | tested cleanse classes allowed; untested classes bounded; source death does not remove |
| PROVOCATION | effective Insight rejects incoming Provocation | multi-source/same-source reapply remains unsupported bounded | own resident lifetime continues when Source is inadmissible | Source death does not remove; normal later lifecycle ends state |
| INTIMIDATION | special protection resolves before Provider selection; ordinary Insight does not reject | successful supported repeat = REFRESH, same instance + new generation + newly selected binding; resume preserves binding/timer; multisource bounded | observed 1-round source scope; lifetime continues while ineffective | tested generic cleanse rejected; specialized removal bounded; expiry terminates state + binding |
| SABOTAGE | effective Insight / tested special protection reject before conflict | observed equal-or-stronger conflict rejects incoming; stronger different-source replacement remains bounded | physical lifetime continues under suppression | natural expiry + observed cleanse path supported; unseen removal classes bounded |
| CAPTURE | effective Insight does not reject verified Capture | state-core reapply/multisource Q70-Q74 remains unsupported; source skill owns alternate branch | verified provider supplies 2-round lifetime, not a universal State Core constant | ordinary cleanse rejected; source death does not remove established Capture |

### Shared transaction binding

```text
Candidate Generated
→ StateAdmissionPolicy
→ StateConflictPolicy
→ immutable StateApplicationTransaction
→ validate topology / preconditions
→ transaction-authorized RNG only
→ StateLifecycleSystem one physical commit
→ EffectivenessTransitionCoordinator affected closure
→ domain transition ports
→ committed observable facts
```

Generation rule:

- CREATE: new instance + new generation.
- REFRESH: same instance + new generation.
- REPLACE: new instance + new generation.
- REJECT: no candidate generation allocation and no mutation.

Removal rule:

- StateRemovalPolicy governs gameplay cleanse/removal selection.
- NATURAL_EXPIRY / OWNER_DEFEAT_CLEANUP / BATTLE_TEARDOWN are lifecycle infrastructure.
- source death is not a universal removal category.

RD-SF-003 fixes same-envelope due-removal batching before effectiveness/provider resume recomputation.


## SF Round 5 contract/runtime mapping — permission, preparation, JIT Provider gate

| Contract concern | Runtime mapping | Decision | Implementation state |
|---|---|---|---|
| EXHAUSTION blocks ACTIVE | SkillPermissionPolicy | deny only NEW_ADMISSION with SkillType.ACTIVE when Exhaustion is EFFECTIVE | DESIGN CLOSED / NOT IMPLEMENTED |
| EXHAUSTION does not block Normal Attack | NormalAttackSystem / ActionSystem remain outside SkillPermissionPolicy | no global action block | DESIGN CLOSED |
| EXHAUSTION does not block standard ASSAULT | SkillPermissionPolicy does not deny ASSAULT merely for Exhaustion | selected Assault can still be blocked by ProviderValidityPolicy | DESIGN CLOSED |
| skip preparation | SkillType remains ACTIVE; PreparationMode behavior does not change permission category | Exhaustion still denies | DESIGN CLOSED |
| already activated Active | admission identity retained by admitted work | no rollback and no child-effect re-admission | DESIGN CLOSED; broader DQ-SF-23 remains bounded |
| EXHAUSTION becomes EFFECTIVE during preparation | EffectivenessTransitionCoordinator -> PreparationInterruptionPort HOLDER_ACTIVE request | synchronous before later gameplay | DESIGN CLOSED / concrete preparation owner pending |
| INTIMIDATION selected preparation Provider | selected Provider VALID -> SUPPRESSED transition -> PreparationInterruptionPort PROVIDER request | only selected Provider interrupted | DESIGN CLOSED / concrete preparation owner pending |
| state/provider resume | policy becomes permissive/valid for future admission | old interrupted preparation never resumes | DESIGN CLOSED |
| RecoveryOpportunitySystem JIT source gate | evaluate_and_resolve Gate 4 | ProviderValidityPolicy replaces direct runtime.enabled truth; explicit slot 0 and expected skill id | DESIGN CLOSED / NOT IMPLEMENTED |
| EffectSourceRef only | attribution | no automatic ProviderDependency | DESIGN CLOSED |
| TriggerSystem frozen damage slot fallback | provenance identity construction | preserve basis.source_skill_slot when it is 0 via explicit is-not-None precedence; provenance only, never implicit ProviderDependency/liveness | AUDIT-DRIVEN MIGRATION OBLIGATION / NOT IMPLEMENTED |

Canonical new-skill topology:

~~~text
provider identity resolution
-> ProviderValidityPolicy
-> SkillPermissionPolicy
-> composed SkillOperationAdmissionDecision
-> observable activation / activation RNG / target RNG
~~~

The two policy reads may both be evaluated so that the composed internal decision retains all blockers. Any presentation ordering of blockers is diagnostic/serialization only and has no gameplay authority. Public event vocabulary is governed by Round 9: final domain owner publishes canonical facts; diagnostic blocker ordering has no gameplay authority.


## SF Round 6 frozen target-operation bindings

These rows are DESIGN_FROZEN_FOUNDATION, not GREEN.

| Concern | Frozen runtime mapping | Required observable discriminator | Preserved boundary |
|---|---|---|---|
| fresh Skill target query | producer creates a new TargetOperationId and TargetOperation only for explicit NEW_QUERY | independent second query gets a distinct ID | no call-stack/call-count inference |
| inherited target | reuse prior target result with INHERITED provenance | Provocation is not automatically rechecked | continuation is not a new query |
| derived target | derive from prior result with DERIVED provenance | no recheck unless producer explicitly starts a new query | adjacency/link derivation does not imply selection |
| locked target | reuse resolved/locked target with LOCKED provenance | later state changes do not silently create a target query | Capture delayed/locked final semantics remain DQ-SF-23 |
| Provocation SINGLE | required target = admissible Provocation Source; exact cardinality = 1 | final target is Source | Source inadmissible => no illegal force |
| Provocation CHOOSE_N | preserve N; Source appears exactly once; required Source reserves one slot; TargetSystem fills remaining slots from eligible-minus-required | Source included exactly once, N unchanged, required Source excluded from random population | BU-P02 empirical micro-order remains bounded; Runtime topology is governed by RD-SF-005 reserve-first; BU-P09 insufficient candidates remains unsupported |
| Provocation FIXED_ALL | preserve all eligible targets | operation does not collapse to one target | Source absent because illegal is not inserted |
| Capture friendly SINGLE | remove captured holder from eligible candidates | zero remaining candidates => NO_LEGAL_TARGET / existing SkillResolution NO_VALID_TARGET adapter | no fallback-self invention |
| Capture friendly CHOOSE_N | remove captured holder before selection | captured holder absent from verified multi-target selection | insufficient eligible count remains bounded, not inherited from TargetSystem truncation |
| Capture ALL_ALLIES | no generalized rule added | explicit boundary remains visible | Capture Q42 bounded |
| Capture self recovery | target eligibility does not simulate recovery denial | self target may remain resolved while RecoverySystem returns zero | RecoverySystem remains authority |
| Normal Attack | never routed through SkillTargetPolicy | Stage9 target-resolution regressions unchanged | Confusion / Taunt / Guard owner retained |

Canonical target subpipeline:

~~~text
Skill operation admitted
→ explicit NEW_QUERY
→ TargetOperation
→ TargetSystem raw candidate construction
→ operation-local legality / Capture eligibility
→ arbitration authority discriminator
→ Provocation constraint (when eligible)
→ selector
→ TargetSelectionResult
~~~

Round 6 does not freeze activation-RNG placement relative to pure candidate construction. It freezes only that denied skill admission creates no TargetOperation and consumes no target-selection RNG.


## SF Round 7 frozen equipment-effectiveness bindings

These rows are DESIGN_FROZEN_FOUNDATION, not GREEN.

| Concern | Frozen runtime mapping | Required discriminator | Preserved boundary |
|---|---|---|---|
| equipment identity | EquipmentProviderRef(owner_id, provider_key) | suppression/resume keeps same Provider identity | no pointer identity; Equipment != Skill |
| contribution identity | EquipmentContributionRef(provider_ref, contribution_key, kind) | same Provider can expose distinct contributions | no speculative full equipment model |
| generic provider validity | ProviderValidityPolicy | missing/mismatch/baseline-disabled typed | not a competing final equipment truth |
| final contribution truth | EquipmentEffectivenessPolicy.evaluate_contribution | one canonical decision | unsupported evidence explicit |
| SABOTAGE scope | effective Sabotage on owner contributes cause to tested owner-owned contributions | all tested owner contributions suppress; object remains | untested future topology bounded |
| Insight x Sabotage | StateEffectivenessPolicy controls whether resident Sabotage contributes cause | Insight removes Sabotage cause without removing state | no reapply on resume |
| FalseReport equipment | tested-persistent-special adapter | tested special suppresses | B-U04 untested = UNSUPPORTED_BOUNDARY |
| Capture equipment | verified ATTRIBUTE adapter | attribute contribution suppresses/resumes | Q63 reactive/damage = UNSUPPORTED_BOUNDARY |
| static attribute | query-time modifier adapter | no cumulative drift | no base-stat mutation |
| damage modifier | per-request DamageRuleProvider filter | phase/order_key unchanged | settled damage unchanged |
| recovery modifier | RecoveryModifierProvider filter before ExactRatio | second CEIL unchanged | no hard-coded Sabotage in RecoverySystem |
| deterministic trigger | JIT opportunity gate | suppressed window no behavior; future window works | queued micro-slice stays DQ-SF-23 if unproven |
| scheduled trigger | due/execution JIT | suppressed due window missed/no replay | other creation/execution topology bounded |
| remote live effect | explicit EquipmentContributionDependency | owner A suppression affects A-dependent effect on B only | EffectSourceRef alone insufficient |
| multi-reason | cause-set composition | remove one cause still suppressed | no mutable equipment.enabled truth |
| initialization | outside ongoing effectiveness | resume does not rerun setup/register/reroll | no replay/reinitialize |
| RNG | policy/registry = 0 RNG | query leaves RNG stream unchanged | trigger-owned RNG stays domain-owned |
| events | query emits none | duplicate query no event effect | Round 9 freezes post-decision/commit public facts; policy query remains event-free |

JIT mapping:
- ATTRIBUTE -> query-time
- DAMAGE_MODIFIER -> per damage-request collection
- RECOVERY_MODIFIER -> per recovery-modifier collection
- TRIGGER -> opportunity execution/admission
- SCHEDULED_TRIGGER -> due/execution JIT
- LIVE_EFFECT -> live authority/use query through explicit dependency

Round 7 does not close DQ-SF-23. The tested scheduled due-window outcome is frozen; broader admitted/queued/in-flight micro-order is the next design problem.

## SF Round 8 frozen Capture composite / execution-right bindings

These bindings close architecture only. They do not upgrade bounded Capture/Sabotage evidence.

### Work identity and lifecycle

Minimum shared lifecycle vocabulary:

~~~text
NEW
ADMITTED
QUEUED
ATTACHED
EXECUTING
SETTLED
~~~

TARGET_LOCKED is an orthogonal provenance qualifier and may coexist with QUEUED.

Identity remains domain-specific: ActionId, NormalAttackInstanceId, DamageInstanceId, RecoveryOpportunity identity, TargetOperationId, State application generation, Counter batch/entry identity, and equivalent future domain IDs. Round 8 creates no UniversalWorkId.

### ExecutionRightSpec

Each admitted work category declares a per-dimension mode:

~~~text
SNAPSHOT_AT_ADMISSION
RECHECK_AT_EXECUTION
NOT_APPLICABLE
UNSUPPORTED_BOUNDARY
~~~

Dimensions:

~~~text
ACTOR_PERMISSION
PROVIDER_VALIDITY
TARGET_ELIGIBILITY
EQUIPMENT_CONTRIBUTION
STATE_EFFECTIVENESS
~~~

The same work may snapshot one dimension and JIT another.

### Known anchors

| Work | Actor | Provider | Target | Equipment | State/effectiveness | Result |
|---|---|---|---|---|---|---|
| already-admitted Active under later EXHAUSTION | SNAPSHOT_AT_ADMISSION for Skill permission | contract-specific | contract-specific | N/A | contract-specific | no rollback / no re-admission |
| Provider-dependent RecoveryOpportunity | operation-specific | RECHECK_AT_EXECUTION | operation-specific | N/A | as dependency requires | Provider validity before recovery probability RNG |
| attached Active-origin DOT under later CAPTURE | NOT_APPLICABLE for Capture actor gate | only if explicit live dependency exists | existing attached target semantics | N/A | attachment lifecycle owner | tick continues |
| new actor-driven damage | RECHECK_AT_EXECUTION | source-specific if declared | target liveness per Damage owner | contribution-specific | current actor CAPTURE fact | deny when current actor captured |
| Counter local damage | RECHECK_AT_EXECUTION | source-specific if declared | existing Counter local target rules | contribution-specific | current counter actor CAPTURE fact | no counter damage; admitted batch not retroactively deleted |
| free proxy damage | RECHECK_AT_EXECUTION against proxy B | origin A remains provenance | domain target rules | contribution-specific | B current state | historical captured A does not block B merely by provenance |
| scheduled equipment due-window already frozen in Round 7 | operation-specific | ProviderValidity as declared | operation-specific | RECHECK_AT_EXECUTION | equipment contribution policy | suppressed due window skipped, no replay |

### Explicit bounded mappings

| Boundary | ExecutionRightSpec representation | Gameplay answer |
|---|---|---|
| Capture Q16 already-created DamageRequest | ACTOR_PERMISSION = UNSUPPORTED_BOUNDARY until authority/default resolves exact micro-slice | not chosen |
| Capture Q44 delayed friendly work | relevant actor/provider/target modes remain UNSUPPORTED_BOUNDARY unless separately frozen | not chosen |
| Capture Q45 already-locked friendly target | TARGET_ELIGIBILITY = UNSUPPORTED_BOUNDARY; LOCKED provenance retained | not chosen; never silently create NEW_QUERY |
| Sabotage B-SAB-07 collected/queued work | EQUIPMENT_CONTRIBUTION = UNSUPPORTED_BOUNDARY outside tested scheduled due-window | not chosen |

### Current runtime audit implications

- FutureAdmissionGate is battle-finalization/future-branch admission infrastructure. It does not currently decide CAPTURE actor permission and must not be overloaded into that role.
- ExecutionRightSystem already protects admitted persistent RuleIntent work from generic STUN suppression and uses current-only target rejection. Round 8 preserves those invariants.
- DamageRequest currently exposes source_id but no universal current_actor field. OperationLineage contains physical_attacker / physical_skill / credit_owner. Stage12 integration therefore requires typed work metadata; source_id cannot be promoted to universal actor truth.
- CounterSystem has an admitted CounterBatch and creates local DamageRequest per entry. CAPTURE must not retroactively delete the batch; the damage-domain seam denies the local damage opportunity.
- RecoverySystem currently performs modifier/second CEIL before HealingBlock and troop restore. CAPTURE joins prevention topology without moving the existing modifier/CEIL or restore/capacity owners.

### RNG and event boundaries

ExecutionRightSpec evaluation consumes zero RNG.

Where a frozen contract explicitly requires a JIT gate before owned RNG, that order is mandatory, e.g. Provider-dependent RecoveryOpportunity validity before recovery probability RNG. Round 9 closes final RNG signature/order governance; this JIT-before-owned-RNG rule is part of that closure.

Round 9 closes public event governance: ACTION_BLOCKED remains ActionSystem-owned, damage denial remains Damage-domain-owned, and recovery prevention remains RecoverySystem-owned. Round 8's deciding owner and internal reason topology are preserved.


## SF Round 9 frozen RNG / Event / Default mappings

Authority:
- STAGE12_RNG_EVENT_DEFAULT_GOVERNANCE.md

These mappings close Shared Foundation governance only. They do not implement a Stage12 state or convert bounded research into gameplay truth.

| State | RNG obligation | Event obligation | Runtime Default / provenance | Remaining unsupported or deferred boundary |
|---|---|---|---|---|
| INSIGHT | PD-INS-001: originating protected-control generation keeps its normal source proc RNG before admission; deterministic source adds no RNG; Insight policies are zero-RNG | incoming protected rejection becomes finalized state-application rejection at ADMISSION stage; existing protected-control cfg204/cfg205 maps to public state suppression/resume transitions after committed recompute | PD-INS-001 and PD-INS-002 are inherited APPROVED_PROJECT_DEFAULTs and retain Research provenance | exotic source/proxy boundaries remain contract-owned; no new Battle default |
| EXHAUSTION | SkillPermissionPolicy and admission coordinator are zero-RNG; denied ACTIVE new admission consumes zero activation and target RNG; already-admitted work is not re-admitted | actual blocked ACTIVE attempt may publish SKILL_OPERATION_BLOCKED; no attempt emits nothing; actual PREPARING interruption may publish PREPARATION_INTERRUPTED | no new default; pre-RNG denial is Shared Foundation architecture, not an empirical PRNG claim | hidden original-server blocked-attempt RNG remains empirically unobservable; Runtime architecture is fixed without laundering it into Research |
| FALSE_REPORT | Provider suppression queries are zero-RNG; any downstream Provider-dependent opportunity is rejected before its own RNG when validity is non-VALID | Provider suppression/resume is internal by default; public facts arise from actual dependent domain behavior, not every validity query | no new default | stronger/weaker B-U01 and untested equipment categories remain UNSUPPORTED_BOUNDARY |
| PROVOCATION | SkillTargetPolicy is zero-RNG; TargetSystem/selector owns sampling; SINGLE and required-filled/all-candidate cases use zero target RNG; supported RANDOM CHOOSE_N uses RD-SF-005 reserve-first and samples only the remaining slots | policy evaluation emits nothing; no generic TARGET_FORCED event is required; any future target-change fact may exist only after final resolved set actually changes | RD-SF-005 / PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN | BU-P02 research micro-order remains bounded; insufficient candidates BU-P09 and multi-source BU-P06 remain UNSUPPORTED_BOUNDARY |
| INTIMIDATION | rejected application consumes zero binding RNG; admitted initial application selects one eligible Provider; successful refresh authorizes a new selection; resume retains binding and uses zero selection RNG | public state apply/refresh/suppress/resume follows the canonical state event model; Provider validity transitions remain internal by default; preparation interruption event only for an actual transition | RD-SF-002 supplies deterministic enumeration only, not weights; no new Round 9 default | exact weights = DEFERRED; empty eligible pool = UNSUPPORTED_BOUNDARY; no uniform 1/N claim |
| SABOTAGE | EquipmentEffectivenessPolicy is zero-RNG; suppressed contribution skips trigger-owned downstream RNG; tested scheduled missed window is not replayed | equipment suppression/resume need not invent a generic Provider event; public domain events come from actual trigger/effect behavior; state suppression/resume uses public state transition facts only when contract-observable | no new default | B-SAB-02 stronger/multi-source and B-SAB-07 queued/JIT outside tested due-window remain UNSUPPORTED_BOUNDARY |
| CAPTURE | Action decision, Provider suppression, Recovery prevention, target eligibility and ExecutionRight evaluation are zero-RNG; Capture action denial creates no NormalAttack target RNG; denied damage/recovery/work consumes no downstream RNG at that denied seam | ActionSystem owns ACTION_BLOCKED; Damage domain owns DAMAGE_PREVENTED; RecoverySystem owns RECOVERY_PREVENTED; multiple internal recovery causes produce one compatibility public prevention fact; Provider transition internal by default | no new default | Q16/Q42/Q44/Q45/Q63/Q70-Q74 remain UNSUPPORTED_BOUNDARY; no silent JIT/snapshot/stack/target generalization |

### INSIGHT mapping details

~~~text
source child proc RNG, iff source defines one
-> control candidate
-> StateAdmissionPolicy
-> ADMISSION rejection if effective Insight protects candidate
~~~

No Insight query, rejection check, suppression check or resume check consumes RNG.

State suppression/resume events are emitted only for a real effective-state transition after the underlying state/dependency commit.
Incoming Insight reapplication rejection is CONFLICT-stage, not ADMISSION-stage.

### EXHAUSTION mapping details

~~~text
ProviderValidity
-> SkillPermission
-> final Skill admission
-> only then activation probability RNG
~~~

An EXHAUSTION-blocked ACTIVE attempt therefore consumes zero activation RNG in the Stage12 Runtime architecture.
Round 11 independent audit classifies that unobservable ordering choice under RD-SF-004 (PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN); this preserves the Research contract's hidden-server-RNG boundary instead of laundering the choice into research fact.

### FALSE_REPORT mapping details

FalseReport changes Provider validity, not random ownership.

~~~text
ProviderValidityPolicy.evaluate
= 0 RNG
= 0 public events as a query
~~~

If the resulting Provider transition invalidates a later opportunity, that owning opportunity skips its downstream RNG.
Stronger/weaker conflict remains outside this mapping.

### PROVOCATION mapping details

~~~text
TargetOperation
-> raw candidates
-> SkillTargetPolicy
-> TargetSystem / selector
~~~

SINGLE forced to one admissible Source is deterministic and adds no target draw.

For supported fresh RANDOM CHOOSE_N, RD-SF-005 now freezes the Runtime-only topology:

~~~text
reserve required Source
-> remove Source from remaining selector population
-> remaining_slots = N - 1
-> TargetSystem.random_units(remaining, count=remaining_slots)
-> no post-selector replacement
~~~

This is PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN. BU-P02 remains empirically bounded; BU-P09 insufficient candidates remains unsupported.

### INTIMIDATION mapping details

Initial successful admission:

~~~text
admission ALLOW
-> eligible Provider pool
-> binding selection operation
-> transaction commit
~~~

Refresh:

~~~text
refresh authorized
-> fresh binding selection operation
-> commit refreshed generation/binding
~~~

Resume:

~~~text
ineffective -> effective
-> reuse existing binding
-> zero binding selection RNG
~~~

A reroll that returns the same Provider is still a real selection operation.
Exact distribution remains unproven.

### SABOTAGE mapping details

EquipmentEffectivenessPolicy and contribution registry remain zero-RNG filters.
A deterministic scheduled due window suppressed by Sabotage is skipped and never replayed.
If a future trigger has its own probability, only the trigger owner may draw after contribution JIT ALLOW.

### CAPTURE mapping details

Natural Action denial:

~~~text
ActionSystem CAPTURE eligibility DENY
-> ACTION_BLOCKED fact
-> no NormalAttack operation
-> no target resolution
-> no target RNG
~~~

Damage denial:

~~~text
Damage execution-right DENY
-> DAMAGE_PREVENTED
-> no denied-work downstream calculation/RNG
~~~

Recovery:

~~~text
modifier / second CEIL
-> prevention cause evaluation
-> one RECOVERY_PREVENTED public fact when prevented
~~~

Capture + HealingBlock may coexist internally. Existing HealingBlock remains the compatibility primary public reason when both apply;
Capture-only prevention requires the future CAPTURE reason representation owned by RecoverySystem.

### Round 9 mapping invariants

- policy query never publishes an event merely because it was called;
- policy query never consumes RNG merely because it was called;
- a rejected/failed transaction does not emit applied/refreshed/transition facts;
- event publishing follows gameplay order and cannot define gameplay order;
- unsupported/deferred boundaries are not converted to PROJECT_RUNTIME_DEFAULT until Runtime truly must choose;
- Research remains read-only.


## SF Round 10 final Contract → Owner → Method → Test traceability

Method names for not-yet-implemented Shared Foundation types are design contracts, not claims that executable code exists.

| State / rule group | Canonical owner | Method / exact seam | Positive test | Negative / discriminator test | Evidence class | Default | Status |
|---|---|---|---|---|---|---|---|
| INSIGHT incoming protection | StateAdmissionPolicy | evaluate_candidate before conflict/Lifecycle | insight_rejects_incoming_protected_control | special boundaries not ordinary-rejected | RESEARCH_CONFIRMED | PD-INS-001 source RNG parity | TRACE_COMPLETE |
| INSIGHT existing suppression | StateEffectivenessPolicy | evaluate_state / effective_instances | insight_suppresses_existing_confusion | resident_suppressed_not_removed | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| INSIGHT resume | transition coordinator + effectiveness | affected-closure recompute after commit | remove_insight_resumes_live_control | expired_control_never_resumes | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| INSIGHT taxonomy | StateAdmissionPolicy rule adapter | protected-control classification | insight_sabotage_protected | insight_capture_not_protected | RESEARCH_CONFIRMED / provenance-qualified | NONE | TRACE_COMPLETE |
| EXHAUSTION Active permission | SkillPermissionPolicy | evaluate_operation in Skill admission coordinator | exhaustion_denies_active | allows_normal_attack_and_standard_assault | RESEARCH_CONFIRMED + PROJECT_RUNTIME_DEFAULT for hidden RNG placement | RD-SF-004 | TRACE_COMPLETE |
| EXHAUSTION preparation | transition coordinator → PreparationInterruptionPort | holder Active interruption request | effective_exhaustion_interrupts_preparation | suppressed_exhaustion_no_interrupt | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE_WITH_INTEGRATION_DEPENDENCY |
| EXHAUSTION admitted work | ExecutionRightSpec / Skill owner | SNAPSHOT_AT_ADMISSION permission | admitted_active_not_rolled_back | new_active_attempt_denied | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| FALSE_REPORT admission exception | StateAdmissionPolicy | evaluate_candidate | ordinary_insight_does_not_reject_fr | special_protection_still_applies | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| FALSE_REPORT Passive/Command | ProviderValidityPolicy | evaluate_provider | suppresses_passive_command_provider | unrelated_provider_remains_valid | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| FALSE_REPORT equipment scope | EquipmentEffectivenessPolicy | evaluate_contribution | tested_equipment_scope_follows_contract | untested_category_explicit_boundary | RESEARCH_CONFIRMED + UNSUPPORTED_BOUNDARY | NONE | TRACE_COMPLETE |
| FALSE_REPORT restore | ProviderValidityPolicy + transition | final-cause removal recompute | restore_provider_future_only | no_missed_trigger_replay | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| PROVOCATION target query | SkillTargetPolicy | TargetOperation eligibility/constraint | single_forces_source | noneligible_operation_unchanged | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| PROVOCATION source admissibility | SkillTargetPolicy | eligibility before selector | admissible_source_included | dead_inadmissible_source_not_forced_state_resident | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| PROVOCATION resident/effective | StateEffectivenessPolicy | evaluate_state | source_death_leaves_state_resident | ineffective_state_no_target_change | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| PROVOCATION Confusion/Taunt | SkillTargetPolicy + TargetResolutionSystem | separate Skill / NormalAttack paths | confusion_preempts_provocation | taunt_normal_attack_only | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| INTIMIDATION one binding | binding selector + ProviderValidityPolicy | select after admitted eligible pool | suppresses_exactly_one_provider | does_not_disable_all_skills | RESEARCH_CONFIRMED | RD-SF-002 enumeration only | TRACE_COMPLETE |
| INTIMIDATION refresh | selector + StateApplicationCoordinator | reroll before atomic REFRESH commit | refresh_one_authorized_selection | rejected_refresh_zero_binding_rng | RESEARCH_CONFIRMED | weights DEFERRED | TRACE_COMPLETE |
| INTIMIDATION resume | ProviderValidityPolicy + transition | reuse stored binding | resume_preserves_binding_timer | resume_zero_binding_rng | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| INTIMIDATION counter | source-skill owner | outside state core | state_core_no_counter_damage_branch | source_skill_scope_separate | SOURCE_SKILL_SCOPE | NONE | TRACE_COMPLETE |
| SABOTAGE suppression | EquipmentEffectivenessPolicy | evaluate_contribution JIT | suppresses_tested_contribution | equipment_object_remains | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| SABOTAGE remote effect | explicit EquipmentContributionDependency | live-effect use-time query | remote_effect_follows_owner_suppression | unrelated_holder_provider_valid | RESEARCH_CONFIRMED / INFERRED_BOUNDED | NONE | TRACE_COMPLETE |
| SABOTAGE restore | equipment policy + domain owner | final-cause removal future eligibility | resume_future_only | no_reinitialize_or_replay | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE natural action | ActionSystem | after maintenance, before STUN consume / NormalAttack | capture_denies_natural_action | capture_denial_does_not_consume_stun | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE damage | Damage work admission / DamageInstanceCoordinator | actor + work category + ExecutionRightSpec | blocks_verified_actor_damage | attached_active_dot_continues | RESEARCH_CONFIRMED + bounded cases | NONE | TRACE_COMPLETE |
| CAPTURE Passive/Command | ProviderValidityPolicy | evaluate_provider | suppresses_verified_provider | source_death_does_not_remove_capture | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE recovery | RecoverySystem | prevention after modifier/second CEIL | capture_prevents_recovery | healing_block_coexists_without_rounding_change | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE friendly target | SkillTargetPolicy | friendly SINGLE/CHOOSE_N eligibility | excludes_captured_friendly | enemy_and_raw_allies_unchanged | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE restore | composed domain owners + transition | future-only re-evaluation | removal_restores_future_permissions | no_missed_work_replay | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |
| CAPTURE source death | Lifecycle + effectiveness | no inferred source liveness | source_death_does_not_remove_capture | no_universal_origin_source_gate | RESEARCH_CONFIRMED | NONE | TRACE_COMPLETE |

Explicit boundaries are also test-mapped: Intimidation weights = DEFERRED; Intimidation empty pool, Provocation BU-P09/BU-P06, Sabotage B-SAB-07 and Capture Q16/Q44/Q45 = UNSUPPORTED_BOUNDARY where already ledgered. Their tests must fail/reject explicitly until evidence or an approved Runtime Default changes the boundary.

Round 10 owner TBD = 0; seam TBD = 0 for frozen claims; test-mapping TBD = 0 for frozen claims. Executable Stage12 implementation/tests remain future work.

## Round 11 independent-audit mapping amendment

`AUDIT-DRIVEN CORRECTION`

- `SF-AUD-11-001`: EXHAUSTION permission remains Research-confirmed; only the hidden blocked-attempt RNG placement is project-governed by RD-SF-004.
- `SF-AUD-11-002`: TriggerSystem's current `basis.source_skill_slot or instance.source_skill_slot` provenance merge is an explicit Stage12 migration obligation because `SkillSlot.INHERENT == 0` is valid. The repair must use explicit `is not None` precedence and must not turn provenance into Provider liveness.
- Owner/seam/test mapping TBD for frozen claims remains 0 after these corrections.


### PROVOCATION BU-P02 post-design governance note

The target-operation architecture did not change. RD-SF-005 only resolves the previously deferred implementation micro-order required by 690108 integration.

```text
NEW_QUERY
-> raw candidates
-> SkillTargetPolicy (0 RNG)
-> legal required Source
-> reserve required slot
-> TargetSystem fills remainder
-> TargetSelectionResult
```

Continuation modes reuse/derive/lock the prior result and do not re-enter this pipeline.

Selector-kind scope:

```text
RANDOM = RD-SF-005 governs BU-P02 random-call topology
DETERMINISTIC = generic required-slot architecture; no RNG semantics added
EXPLICIT = outside BU-P02 random topology; must be fully specified by its own boundary
```

Insufficient candidate behavior is intentionally not inherited from `TargetSystem.random_units()` truncation. BU-P09 remains `UNSUPPORTED_BOUNDARY`.


## 690108 production integration checkpoint — 2026-09-28

```text
SkillDefinition
-> SkillResolver
-> TargetOperation
-> SkillTargetPolicy
-> TargetSystem
-> TargetSelectionResult
```

Production mappings now cover SINGLE / CHOOSE_N / FIXED_ALL. CHOOSE_N uses RD-SF-005 reserve-first topology. `BU-P06` and `BU-P09` remain explicit unsupported boundaries. Validated checkpoint: `d420e8130dff1b3b9cc2545f0a832eccf58abd75`, CI `36333059532`, 1359 passed, demo PASS. Runtime Freeze remains pending independent audit.


## 690108 independent Runtime Freeze checkpoint — 2026-09-28

```text
690108 PROVOCATION Gameplay = IMPLEMENTED
690108 PROVOCATION Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit code/test SHA = e0f9e0c24a4c379918c3b9389a67dcfea138ac13
Fresh audit CI = 36334810169 / success / 1392 passed / demo PASS
RD-SF-005 = PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN
BU-P06 = UNSUPPORTED_BOUNDARY
BU-P09 = UNSUPPORTED_BOUNDARY
Stage12 Runtime Frozen = 4 / 7
NEXT = 690222 INTIMIDATION Runtime Integration
```

Authority: `STAGE12_690108_PROVOCATION_RUNTIME_FREEZE_AUDIT.md`.


## 690222 binding-selection governance mapping — 2026-09-28

```text
Frozen Research:
randomly select exactly one supported eligible Skill Provider
uniform/equal/1/N hidden weight = unproven

Runtime governance:
RD-SF-002 = stable Provider population order
RD-SF-006 = simulator-only uniform selection + RNG call topology
```

Mapping:

| Concern | Owner / seam | Current binding | Status |
|---|---|---|---|
| supported pool identity | SkillRuntimeRegistry / SkillProviderRef | loaded holder Providers; identity enumeration does not filter ProviderValidity | DESIGN FROZEN |
| type filtering | Intimidation adapter-to-be | ACTIVE incl. preparation, ASSAULT, PASSIVE, COMMAND, TROOP; FORMATION excluded; TALENT/Equipment/Bingshu unsupported | DESIGN FROZEN |
| stable pool order | RD-SF-002 | slot 0 -> 1 -> 2, skill_id tiebreaker | RUNTIME DEFAULT FROZEN |
| multi-candidate distribution | BattleContext.random / RandomSystem.choice | uniform over supplied stable supported pool, exactly one choice call | RD-SF-006 FROZEN |
| single-candidate selection | Intimidation selector-to-be | sole Provider, zero RNG | RD-SF-006 FROZEN |
| rejected application | admission/conflict owners | zero binding RNG | GOVERNANCE FROZEN |
| successful REFRESH | state application + selector-to-be | new binding decision; same Provider may be selected | GOVERNANCE FROZEN |
| RESUME | effectiveness transition | retain binding, zero RNG | GOVERNANCE FROZEN |
| empty pool | unsupported boundary | no gameplay answer invented | PRESERVED |
| production adapter | future 690222 integration | absent in this governance round | NOT INTEGRATED |


## 690222 production + independent Runtime Freeze checkpoint — 2026-09-28

```text
690222 INTIMIDATION Gameplay = IMPLEMENTED
690222 INTIMIDATION Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit test SHA = 0b3e5d62b1c2e25e4b2177ccfa5dd456819ddc96
Fresh audit PR CI = 36374443142 / success / 1483 passed / demo PASS
RD-SF-006 = PROJECT_RUNTIME_DEFAULT / NOT_EMPIRICALLY_FROZEN
TROOP consumer absence = NON_BLOCKING NOTE
Stage12 Runtime Frozen = 5 / 7
NEXT = 690109 SABOTAGE Runtime Integration
```

Current production mapping:

| Concern | Canonical owner / seam | Production binding | Freeze status |
|---|---|---|---|
| eligible Skill Provider identity | SkillRuntimeRegistry + SkillProviderRef | ACTIVE incl. preparation, ASSAULT, PASSIVE, COMMAND, TROOP | FROZEN TO CONTRACT |
| Formation | Intimidation eligible-pool adapter | filtered before binding RNG | FROZEN EXCLUSION |
| TALENT / Equipment / Bingshu | Intimidation boundary | not admitted into supported pool | UNSUPPORTED / NOT FROZEN |
| ordering | RD-SF-002 | slot 0 -> 1 -> 2 + skill_id tiebreaker | FROZEN |
| binding distribution/topology | BattleContext.random / RandomSystem | 1 candidate = 0 RNG; multi = exactly 1 choice | RD-SF-006 FROZEN PROJECT DEFAULT |
| CREATE | StateApplicationCoordinator + Intimidation augmentation | new binding decision | FROZEN TO CONTRACT |
| REFRESH | same physical instance + new generation | new binding decision / reroll | FROZEN TO CONTRACT |
| RESUME | effectiveness transition | retained binding / zero binding RNG | FROZEN TO CONTRACT |
| Provider suppression | ProviderValidityPolicy | selected Provider SUPPRESSED without runtime deletion/disable | FROZEN TO CONTRACT |
| preparation | PreparationStateOwner via PROVIDER scope | exact selected preparation interrupted | FROZEN TO CONTRACT |
| explicit dependency | DependencyEvaluationSupport | ProviderDependency only | FROZEN TO CONTRACT |
| source attribution only | attribution metadata | no inferred dependency | FROZEN NEGATIVE |
| source death / specialized removal / multi-source | preserved boundaries | no gameplay answer invented | UNSUPPORTED / BOUNDED |
| TROOP execution consumer | future domain consumer | no separate concrete consumer exists today | NON-BLOCKING NOTE; MUST consume ProviderValidity when introduced |

Authority: `STAGE12_690222_INTIMIDATION_RUNTIME_FREEZE_AUDIT.md`.


## 690109 SABOTAGE Runtime Freeze mapping — 2026-09-28

```text
Research Contract = v1.0-frozen
Gameplay = IMPLEMENTED
Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit test SHA = f698cb97b08596b3cea924a815991022cc2dfe7d
Audit-test push CI = 36380946005 / success / 1558 passed / demo PASS
Stage12 Runtime Frozen = 6 / 7
NEXT = 690110 CAPTURE Runtime Integration
```

Current production mapping:

| Concern | Canonical owner / seam | Production binding | Freeze status |
|---|---|---|---|
| target equipment identity | `EquipmentProviderRef` / registry | owner + provider_key remains resident | FROZEN TO CONTRACT |
| provider validity | `ProviderValidityPolicy` | effective Sabotage contributes typed suppression cause | FROZEN TO CONTRACT |
| contribution effectiveness | `EquipmentEffectivenessPolicy` | Attribute/Damage/Recovery/Trigger/Scheduled/LiveEffect consume shared truth | FROZEN TO CONTRACT |
| existing derived State | `ProviderDependency` + `StateEffectivenessPolicy` | explicit equipment Provider dependency only | FROZEN TO CONTRACT |
| remote ownership | equipment owner Provider identity | owner sabotaged suppresses remote dependent; holder sabotage alone does not | FROZEN TO CONTRACT |
| Insight | canonical 690089 admission + effectiveness graph | incoming reject; resident suppress/resume | FROZEN TO CONTRACT |
| Gangyi | Sabotage admission adapter + canonical equipment effectiveness | effective holder-level immunity | FROZEN TO CONTRACT |
| reapplication | `StateConflictPolicy` | supported resident reapplication rejects / no refresh | FROZEN TO CONTRACT |
| stronger/weaker | admission boundary | numeric strength mapping unsupported | B-SAB-02 PRESERVED |
| removal | `StateRemovalPolicy` | ordinary observed cleanse; specialized/scripted unsupported | FROZEN OBSERVED BOUNDARY |
| dynamic equipment | equipment effectiveness boundary | post-application new Provider/contribution surfaces unsupported in current consumers | B-SAB-09 PRESERVED |
| queued/in-flight work | `ExecutionRightSpec` / owning operation | tested scheduled JIT covered; broader micro-order unsupported | B-SAB-07 PRESERVED |

Freeze authority: `STAGE12_690109_SABOTAGE_RUNTIME_FREEZE_AUDIT.md`.


## 690110 CAPTURE Runtime Freeze mapping — 2026-09-28

```text
Research Contract = v1.0-frozen
Gameplay = IMPLEMENTED
Runtime = FROZEN TO CONTRACT
Independent Runtime Freeze Audit = PASS
Audit test commit = f1db21211ce7d01fc867bc8c26c94cb82f11af49
Independent adversarial tests = 33
Local full pytest = 1640 passed / demo PASS
Stage12 Runtime Frozen = 7 / 7
NEXT = Stage12 Final Completion / Freeze Audit
```

| Concern | Canonical owner / seam | Production binding | Freeze status |
|---|---|---|---|
| natural action | `ActionSystem` + CurrentActorPermissionPolicy | captured current actor denies NATURAL_ACTION before STUN consume / NormalAttack | FROZEN TO CONTRACT |
| new actor-driven damage | DamageExecutionRight / DamageInstanceCoordinator | actor RECHECK_AT_EXECUTION before DamageRequest/DamageInstance | FROZEN TO CONTRACT |
| counter damage | CounterSystem + DamageExecutionRight | opportunity retained, local damage denied | FROZEN TO CONTRACT |
| attached Active-origin DOT | typed ATTACHED_EXISTING_DOT work | actor permission NOT_APPLICABLE; continues | FROZEN TO CONTRACT |
| free proxy | typed current actor | historical captured source alone does not deny | FROZEN TO CONTRACT |
| Q16 already-created request | ExecutionRightSpec | explicit UNSUPPORTED_BOUNDARY | BOUNDED / PRESERVED |
| PASSIVE / COMMAND | ProviderValidityPolicy | suppressed without runtime deletion/disable | FROZEN TO CONTRACT |
| provider dependency | DependencyEvaluationSupport | explicit ProviderDependency only; attribution does not infer liveness | FROZEN TO CONTRACT |
| received recovery | RecoverySystem prevention | target remains targetable where legal; final recovery zero | FROZEN TO CONTRACT |
| friendly SINGLE / CHOOSE_N | SkillTargetPolicy before TargetSystem selector | captured ally excluded pre-RNG | FROZEN TO CONTRACT |
| ALL_ALLIES / delayed / locked | TargetOperation boundary | unsupported or immutable continuation; no guessed requery | BOUNDED / PRESERVED |
| equipment ATTRIBUTE | EquipmentEffectivenessPolicy | ATTRIBUTE contribution suppressed; Provider identity retained | FROZEN TO CONTRACT |
| equipment non-ATTRIBUTE | EquipmentEffectivenessPolicy | explicit unsupported boundary, not SABOTAGE alias | BOUNDED / PRESERVED |
| INSIGHT | StateAdmissionPolicy | ordinary Insight does not reject Capture | FROZEN NEGATIVE |
| ordinary cleanse | StateRemovalPolicy | rejected; same Capture remains | FROZEN TO CONTRACT |
| source death | StateLifecycleSystem | established Capture continues | FROZEN TO CONTRACT |
| reapplication / multisource | StateConflictPolicy | explicit unsupported boundary; no refresh/stack law invented | BOUNDED / PRESERVED |
| RNG / Event | canonical domain owners | adapter queries zero-RNG / no direct CAPTURE event publishing | FROZEN GOVERNANCE |

Authority: `STAGE12_690110_CAPTURE_RUNTIME_FREEZE_AUDIT.md`.

## STAGE12_FINAL_COMPLETION_MAPPING — 2026-09-28

All seven Stage12 contract→runtime mappings are implemented, independently frozen, and accepted by the stage-level audit.
Earlier DESIGN_MAPPING / NOT IMPLEMENTED cells are historical design-stage records.
Current authority is the seven integration/freeze documents plus `STAGE12_FINAL_COMPLETION_FREEZE_AUDIT.md`.
