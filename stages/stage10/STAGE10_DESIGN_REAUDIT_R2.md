# Stage10 Independent Design Re-Audit Round 2

> Project: 三国志战略版战斗模拟器 V2  
> Audit mode: `INDEPENDENT / ADVERSARIAL / REPOSITORY-DRIVEN`  
> Scope: Stage10 Architecture Design Draft V2 independent re-audit  
> Audit date: `2026-09-15`  
> Production implementation: `NOT AUTHORIZED`

---

## 0. Audit Metadata

### 0.1 Audited repository identity

Battle Runtime repository:

```text
lxy2005051020-commits/sgs-v2-battle-system
branch: stage10-persistent-state-research
Audited Battle HEAD: 3e9fb5903496a6d180b66c0f9bc8f2d8584ea87a
Audited tree: 562d7c2a8fd7db7960d46bbb849579d7555e3589
```

Audited design blobs:

```text
stages/stage10/STAGE10.md
blob: 15f771037dddd2ac0956af59403a9030cf039a7a

stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md
blob: 64cdb7d86c8bda5b9123b49afcb924db7e1fd485

stages/stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md
blob: 4c1e22eda97bdc0ef74ab6175a28672845771ddc
```

Gameplay Mechanism Authority repository:

```text
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
Audited Gameplay Authority HEAD: 61f2be7e87e6bfab1433657ee7f766ae0c53da9d
```

R1-C input baseline independently reconstructed as:

```text
2be2cfdd789ef9e035306fbb4c5fb40bf994a341
```

### 0.2 R1-C change-scope verification

Real compare:

```text
2be2cfdd789ef9e035306fbb4c5fb40bf994a341
...
3e9fb5903496a6d180b66c0f9bc8f2d8584ea87a
```

Independent compare inspection found no R1-C modification under:

```text
sgs_v2/**/*.py

tests/**

demo.py

.github/workflows/** / workflow/**
```

R1-C was therefore a design/authority-document repair pass. This audit does not accept that as evidence the design is correct; it establishes only that the repair did not silently alter the production baseline.

### 0.3 Documents and runtime read

The audit reread the complete current Stage10 design set, including:

```text
stages/stage10/STAGE10.md
stages/stage10/STAGE10_DESIGN_AUDIT.md
stages/stage10/STAGE10_AUTHORITY_GAP_TRIAGE.md
stages/stage10/STAGE10_TARGETED_RESEARCH_QUESTIONS.md
stages/stage10/STAGE10_RESEARCH_MATRIX.md
stages/stage10/STAGE10_RUNTIME_MAPPING.md
stages/stage10/STAGE10_OPEN_QUESTIONS.md
stages/stage10/README.md
```

and both compatibility addenda plus the original Stage7 / Stage8 / Stage9 design, hardening, regression, and freeze authorities.

The audit also traced the current runtime composition and execution path through the BattleEngine, context/composition root, rule-hook/trigger/effect path, state lifecycle/registry, DamageSystem and Stage8 formula/rule components, Stage9 DamageInstance/partition/direct-loss/finalization, recovery, skill runtime, Cleave, Chain, Counter, operation identity, execution-right, and EventBus code.

### 0.4 Baseline verification

Latest GitHub Actions run associated with the audited branch HEAD:

```text
run id: 34926838900
head_sha: 3e9fb5903496a6d180b66c0f9bc8f2d8584ea87a
conclusion: success
job id: 104246560254
```

Workflow log:

```text
pytest -q
→ 753 passed in 2.96s

python demo.py > /dev/null
→ PASS
```

Important CI identity note:

```text
PR workflow checkout ref:
04428e7c013f8f0d73fe77b8a2429e433f68546d

Audited branch HEAD:
3e9fb5903496a6d180b66c0f9bc8f2d8584ea87a
```

The run is a PR merge-ref validation, not an exact-head local checkout proof. The branch repair itself changed docs only, and the green run proves no baseline integration break in the PR merge snapshot. It does **not** prove Stage10 design correctness.

---

## 1. Executive Verdict

```text
Round 1 original findings reviewed:
BLOCKER = 7
MAJOR   = 6

Round 2 new findings:
BLOCKER   = 2
MAJOR     = 5
MINOR     = 3
HARDENING = 2

AUTHORITY SYNC VERDICT = FAIL / AUTHORITY NOT PINNED

VERDICT = FAIL / DESIGN REPAIR ROUND 2 REQUIRED
DESIGN FREEZE ELIGIBLE = NO
STAGE10 IMPLEMENTATION AUTHORIZED = NO
```

R1-C materially improved Stage10. The Stage7 compatibility seam, Stage8 frozen-input replay lane, PRE_BATTLE lifecycle arithmetic, defeat-cleanup ownership, battle-authoritative SkillRuntime registry, recovery RNG classification, typed RuleIntent hierarchy, and migration plan are mostly coherent and implementable.

The repaired design nevertheless fails the freeze gate for three independent reasons:

1. it changes a formally frozen Stage9 reaction/settlement ordering without performing the Stage9 formal reopen required by Stage9 itself;
2. it does not close the officially frozen FIRST_AID eligibility of `ASSAULT / pursuit` damage even though the current Stage9 recovery-permission matrix rejects that source type;
3. its zero-loss FIRST_AID closure is still not present in any discoverable official Gameplay Authority commit/branch, while Draft V2 labels those facts `GAMEPLAY FROZEN`.

The remaining MAJOR findings concern execution-right ownership, source-skill gate mapping, end-to-end generation provenance, and battle-end physical lifecycle closure.

---

## 2. Repository / Authority Synchronization Review

### 2.1 Current authority promotion state

Gameplay Authority `main` at `61f2be7e...` contains no checked-in Stage10 targeted-research package equivalent to:

```text
stage10/RECOVERY_RNG_EDGE_RESEARCH.md
stage10/FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH.md
```

Repository/commit search also found:

```text
FIRST_AID_ZERO_LOSS_ELIGIBILITY_RESEARCH → no repository result
"zero-loss" commit                        → no commit result
stage10 authority branch                  → no matching branch
```

The current official FIRST_AID contract remains:

```text
states/persistent/first_aid/MECHANISM_CONTRACT.md
blob: d0f45b60df9ff7ea18efe671c1faaf320cdb882d
Frozen Date: 2026-09-06
```

It freezes:

```text
AFTER_DAMAGE_EVENT
PER_ELIGIBLE_DAMAGE_EVENT
Normal Attack eligible
Active/Command damage eligible
Continuous Damage eligible
Multi-hit separate opportunity per hit
Pursuit/Counterattack eligible
fatal hit cannot recover a defeated target
```

but it does not pin the later targeted closure:

```text
weakness-zero → eligible
barrier-zero  → eligible
evasion/miss  → not eligible
full-troop opportunity must still exist
```

Draft V2 itself records that those files/contracts are absent from the official repository, then creates a separate classification category in which `project-owner supplied targeted-research closure` can be labeled `GAMEPLAY FROZEN`.

That classification is not consistent with the authority repository's own promotion discipline. The authority repository distinguishes mechanism research/freeze from simulator/runtime completion; Battle-repo summaries and task prompts do not become formal gameplay authority by declaration.

### 2.2 Authority case classification

For S10-TR-03 zero-loss FIRST_AID, current state is:

```text
Case C:
research conclusion exists in project-owner supplied closure / Battle docs
but no discoverable formal Gameplay Authority commit or branch contains it
```

The audit does **not** order a new battle-report research pass merely because promotion is missing. The correct immediate action is:

```text
AUTHORITY PROMOTION REQUIRED
```

The promotion package must contain the underlying evidence/research artifact and then update/refreeze the official FIRST_AID contract. If the alleged evidence artifact cannot actually be reconstructed or produced, the fact remains non-authoritative and only then would targeted research have to be re-established.

### 2.3 Required promotion content

Before Stage10 Design Freeze, official authority must pin at minimum:

```text
FIRST_AID resolved-hit zero-loss eligibility
weakness-zero eligibility
barrier-zero eligibility
evasion/miss exclusion
fatal-hit exclusion
zero-loss TREATMENT_AMOUNT behavior
zero-loss TRIGGER_DAMAGE_RATIO behavior
full-troop opportunity semantics, if classified as gameplay rather than simulator policy
```

The official hidden RNG question may remain:

```text
UNKNOWN / UNOBSERVABLE
```

The Battle runtime may retain its one-draw simulator policy as `ENGINEERING DETERMINISM`, but that policy must not be promoted as observed official PRNG behavior.

### 2.4 AUTHORITY SYNC VERDICT

```text
FAIL / AUTHORITY NOT PINNED
```

Reason:

```text
Stage10 Draft V2 depends on gameplay facts that are not currently present in the formal Gameplay Authority repository contract.
```

This alone blocks Design Freeze even if all architecture findings were otherwise repaired.

---

## 3. Round 1 Finding Closure Matrix

Independent closure, not the R1-C self-reported matrix:

| Original Finding | R1-C Claimed Repair | Independent Verification | Verdict |
|---|---|---|---|
| `S10-A-B01` Stage7 execute-all vs death hard termination | Stage7 addendum + abort tail | One-shot precollection remains; typed per-intent gate + owner-state tail abort is implementable | `CLOSED` |
| `S10-A-B02` Stage8 reopen only informal | Stage8 compatibility addendum | A real limited Stage8 reopen exists and defines the exact new lane | `CLOSED` |
| `S10-A-B03` FROZEN_APPLICATION ownership ambiguous | frozen-input replay matrix | Source facts, target facts, FormulaPolicy, modifiers, crit, RNG and trace are now uniquely assigned | `CLOSED` |
| `S10-A-B04` PRE_BATTLE off-by-one | separate PRE_BATTLE time domain | `first=1,last=N` is explicit and correct | `CLOSED` |
| `S10-A-B05` no authoritative defeat cleanup checkpoint | one DefeatCleanupPort | One typed synchronous cleanup owner/call contract is designed across destructive paths | `CLOSED` |
| `S10-A-B06` SkillRuntime lookup not authoritative | BattleContext registry | `(owner_id, SkillSlot)` registry + expected skill-id validation is sufficient under current loadout invariant | `CLOSED` |
| `S10-A-B07` hidden recovery RNG semantics exceed authority | official UNKNOWN + simulator policy | One-draw policy is honestly separated as engineering; current `RandomSystem.chance` can implement p=0/p=1 draw consumption | `CLOSED` |
| `S10-A-M01` refresh provenance spans generations | application-generation ID + snapshot | Internal pending-work isolation is repaired, but downstream request/result/event provenance can still drop generation identity | `PARTIALLY CLOSED` |
| `S10-A-M02` trace representation deferred | typed `frozen_application_trace` | One representation chosen; no fake EXECUTED state | `CLOSED` |
| `S10-A-M03` old synthetic params migration absent | explicit migration table | Official Stage10 path becomes singular; legacy params test-only | `CLOSED` |
| `S10-A-M04` RecoveryOpportunity hierarchy incomplete | sibling `RuleIntent` model | Ordered mixed-intent tuple and typed result union are closed | `CLOSED` |
| `S10-A-M05` EXTERNAL_LIFECYCLE ambiguous | external physical lifecycle only | Dynamic flag interpretation removed; lifecycle ownership meaning unique | `CLOSED` |
| `S10-A-M06` standard/Cleave aftermath divergent | shared DamageAftermathPort | Shared port is designed, but the repair silently rewrites frozen Stage9 Cleave ordering without a Stage9 reopen | `REGRESSED` |

Closure totals:

```text
CLOSED           = 11
PARTIALLY CLOSED = 1
STILL OPEN       = 0
REGRESSED        = 1
```

This distinction matters: all seven original Round 1 BLOCKERs are substantively answered, but the repair introduced new frozen-boundary conflicts. A repaired old finding does not grant immunity from creating a new one. Software architecture remains annoyingly indifferent to spreadsheet optimism.

---

## 4. Stage7 Compatibility Reopen Audit

### 4.1 Pre-collection atomicity

The addendum correctly preserves:

```text
RuleHook
→ one TriggerSystem collection pass
→ immutable ordered RuleIntent tuple
→ no recollect
→ no resort
→ no EventBus feedback loop
```

Current Stage7 runtime is still the original execute-all tuple comprehension, so implementation work is required, but the seam is real: `RuleHookSystem.process()` already owns the ordered collected tuple and dispatch point.

### 4.2 Death-abort scope

The addendum now yields a unique gameplay interpretation for the required example.

Given one collected hook:

```text
Effect A
Effect B
Effect C
```

Case 1: A kills the hook actor / state-resolution owner.

```text
A executes and causes synchronous defeat cleanup
→ owner execution right becomes denied
→ every remaining STATE_RESOLUTION intent for that owner is represented as ABORTED
→ B does not execute
→ C does not execute if C is also part of that owner's state-resolution tail
```

The targets of B/C do not rescue them. The hard boundary is the defeated state-resolution owner.

Case 2: A kills some other target X, not the hook actor/state owner.

```text
no universal hook-tail abort
→ B receives its own execution-right validation
→ if B targets dead X, B is denied/aborted for target-dead reason
→ C targeting an unrelated valid target may execute
```

Case 3: C is a genuinely unrelated non-state intent domain.

```text
Stage10 owner-state abort rule does not silently cancel it
→ it receives its own domain execution-right validation
```

This is sufficiently scoped and does not turn target death into a global cancellation primitive.

### 4.3 Ownership defect retained

One ownership ambiguity remains and is recorded as `S10-R2-M02`:

```text
STAGE10.md:
EffectExecutor validates execution right before each Effect

Stage7 addendum:
RuleHookSystem/orchestration obtains execution-right decision before every RuleIntent
```

The architecture must choose one authoritative RuleIntent gate or define an exact two-tier invariant. RecoveryOpportunity never passes through EffectExecutor, so the current wording cannot be treated as harmless duplication.

### 4.4 Stage7 verdict

```text
Compatibility concept: PASS
Death-abort scope: PASS
Precollection determinism: PASS
Execution-right unique owner: FAIL / MAJOR
```

---

## 5. Stage8 Compatibility Reopen Audit

The Stage8 addendum is a genuine narrow reopen, not merely a Stage10-local assertion.

It preserves the existing Stage8 pipeline and adds one authorized calculation basis:

```text
LIVE_RUNTIME
FROZEN_APPLICATION
```

The current live path remains unchanged. The frozen lane changes only the input provenance and selected application-time reusable facts required for authorized persistent damage.

No EventBus gameplay engine is introduced; `DamageSystem` remains the theoretical-damage owner, `DamageResolutionSystem` remains settlement owner, and `TroopSystem` remains mutation owner.

Stage8 evidence gates also remain intact. Evasion/Barrier may be represented as typed topology when an authorized producer exists, but Stage10 does not thereby create official production bindings for them.

Stage8 compatibility reopen verdict:

```text
PASS
```

subject to the separate Stage9 and authority findings in this audit.

---

## 6. FROZEN_APPLICATION Pipeline Audit

### 6.1 Per-layer audit

| Stage8 Layer | FROZEN_APPLICATION behavior | Owner | R2 Verdict |
|---|---|---|---|
| participant validation | historical source identity + live target; dead historical source allowed only on authorized lane | DamageSystem | unique |
| source validation | roster identity + state/generation provenance | typed historical-source contract | unique |
| target validation | current live target | DamageSystem | unique |
| prevention | dynamic | DamagePreventionSystem | unique |
| hit resolution | dynamic | HitResolutionSystem | unique |
| formula policy | reused application result | basis producer + DamageSystem consumer | unique |
| base formula | dynamic arithmetic using frozen source facts + current target facts | existing Weapon/Strategy formula family | unique |
| coefficient | frozen input | generation basis | unique |
| potency | frozen input where applicable | generation basis | unique |
| ordinary modifiers | frozen resolved ordered plan | application producer / DamageSystem replay consumer | unique |
| weakness | dynamic current gate | Stage8 prevention topology | unique |
| crit | frozen participation/context if authorized | generation basis | unique |
| RNG | base-formula RNG at tick; locked modifier/crit participation not rerolled | current context.random / existing formula | unique |
| defense policy | reused application FormulaPolicy result | DamageSystem/base formula | unique |
| final theoretical damage | calculated at tick | DamageSystem | unique |
| DamageResult | produced at tick | DamageSystem | unique |
| PipelineTrace | live tick trace + typed frozen-application trace | DamageSystem | unique |

### 6.2 Source-side formula facts

The current weapon/strategy formula families require source-side facts equivalent to:

```text
source troops
source relevant combat attribute (ATK or INT)
source level
source morale
source troop type
```

The Stage8 addendum explicitly closes these as application/refresh snapshots and leaves current target-side formula facts live.

Therefore:

```text
source attribute changes after application → do not recalculate old generation
target defense / target INT / target level / target troop type → live at tick unless policy says otherwise
```

### 6.3 Ordinary modifier plan

The repaired contract stores an application-resolved ordered semantic plan, not mutable provider objects. Required replay facts include the ordered operation/operand/scope/provenance and application-time participation decisions.

This avoids both unsafe dead-source provider lookup and a second modifier-discovery pass at tick.

### 6.4 Crit and RNG

Application/refresh time:

```text
crit participation/context, if an authorized crit contribution exists
→ locked into the generation basis
→ refresh rebuilds it for the new generation
```

Tick time:

```text
base-formula RNG
→ consumes current battle RNG through the existing formula path
```

There is therefore no contradiction between:

```text
application-time locked crit/modifier participation
```

and:

```text
tick-time base-formula RNG
```

They are distinct RNG/decision families.

### 6.5 REBELLION defense policy

For REBELLION:

```text
route = locked at application/refresh
formula_policy_result = IGNORE_RELEVANT_TARGET_DEFENSE
```

At tick, that reused policy is consumed by the actual base formula; the opposite route is not rediscovered and current source attributes are not reread.

Current target-side facts remain live except that the relevant defensive contribution is omitted by the reused formula policy.

### 6.6 Source-dead DOT scenario

Required scenario:

```text
Round1:
source applies BURN
source later dies

Round2:
target reaches ActionStart
```

R2 interpretation:

```text
DamageRequest source_id
→ historical source identity from generation snapshot

source UnitRuntime lookup
→ roster identity validation only
→ source alive is NOT required for FROZEN_APPLICATION

source attributes / source troops / level / morale / troop type
→ frozen generation basis

source states
→ only explicitly dynamic gate families are live-read
→ source Weakness is current/dynamic
→ because owner-death cleanup clears source-owned Weakness, a dead source has no stale Weakness instance

source skill runtime
→ not a generic DOT gate unless specific Gameplay Authority says so

ordinary modifier provider
→ not rediscovered
→ frozen semantic plan replayed

formula input
→ frozen source facts + current target facts + current tick base-formula RNG
```

This is consistent with the authority rule that source death does not generically cancel an already-created continuous-damage state.

### 6.7 FROZEN_APPLICATION verdict

```text
PASS / UNIQUE ENOUGH FOR IMPLEMENTATION
```

No new gameplay research is required for this lane itself.

---

## 7. Lifecycle / Expiration Audit

### 7.1 PRE_BATTLE timelines

For PRE_BATTLE application:

| N | first eligible | last eligible | opportunities | physical expiry |
|---:|---:|---:|---|---|
| 1 | R1 | R1 | R1 ActionStart | end of R1 owner ActionStart resolution window |
| 2 | R1 | R2 | R1, R2 | end of R2 owner ActionStart resolution window |
| 3 | R1 | R3 | R1, R2, R3 | end of R3 owner ActionStart resolution window |

No round-zero opportunity exists and no N+1 tick is created.

### 7.2 Combat-round application

Apply in round R before owner reaches ActionStart:

```text
first = R
last  = R + N - 1
```

Apply in round R after owner already reached ActionStart:

```text
first = R + 1
last  = R + N
```

No catch-up is created.

### 7.3 Refresh

Refresh before ActionStart in R:

```text
new generation
→ new source/provenance/potency snapshot
→ first eligible R
```

Refresh after ActionStart in R:

```text
new generation
→ first eligible R+1
```

Pending work created by an old generation keeps the old immutable generation snapshot.

### 7.4 Stun / action suppression

Current Engine reaches:

```text
UNIT_ACTION_START
→ publish UNIT_ACTION_STARTED
→ RuleHookSystem
```

before the later ActionSystem control-state suppression path.

Therefore a stunned unit still reaches the Stage10 persistent ActionStart timing. Stun may suppress the later normal action but does not refund or postpone the persistent-state opportunity window. This matches current authority for RECUPERATION and continuous states.

### 7.5 Duplicate ActionStart in same round

`ActionProgressTracker` is designed to make Stage10 persistent opportunity cardinality:

```text
max 1 / owner / combat round
```

A duplicate synthetic ActionStart cannot create a second Stage10 opportunity.

### 7.6 Owner death

Owner death may remove the state earlier through synchronous defeat cleanup. Future opportunities are denied and remaining owner-state resolution aborts.

### 7.7 Battle-end gap

Draft V2 does not define what happens when battle finalizes before a surviving owner's last eligible ActionStart is reached.

Current BattleEngine can finalize and return before a later surviving unit reaches its pending ActionStart, and there is no BattleEnd state-registry teardown in current runtime.

Therefore two conforming implementations can differ:

```text
A. leave physically attached finite states in BattleContext after finalization
B. synchronously clear/expire all remaining battle-scoped states at BattleEnd
```

Draft V2 claims there is no externally observable stale interval, but post-run `context.states` is still an inspectable runtime object.

This is `S10-R2-M05`.

### 7.8 ActionProgressTracker placement gap

Draft V2 says `mark_action_start` occurs after reaching the lifecycle node and before Stage10 opportunity collection, but it does not uniquely place it relative to the existing `UNIT_ACTION_STARTED` observation publication.

Because EventBus is observation-only, this is not currently a gameplay divergence, but the exact engine order should be frozen for reproducible traces. Recorded as `S10-R2-N01`.

---

## 8. Defeat Cleanup Audit

### 8.1 Ownership

Draft V2 now provides one conceptual authority:

```text
DefeatCleanupPort.commit_defeat(...)
```

with ownership split:

```text
TroopSystem
→ troop mutation only

destructive settlement owner
→ detect alive→dead edge
→ call DefeatCleanupPort

DefeatCleanupPort
→ coordinate synchronous defeat boundary

StateLifecycleSystem
→ physically remove all attached states

ExecutionRightSystem
→ deny subsequent owner/action/state execution
```

This is structurally coherent and avoids EventBus control flow.

### 8.2 Required destructive routes

The port is designed to cover:

```text
standard target settlement
periodic standard settlement
counter standard settlement
Share DirectTroopLoss
Distribution DirectTroopLoss
Cleave target settlement
Cleave partition direct loss
Chain restricted feedback
```

This is the correct scope.

### 8.3 Fatal FIRST_AID

Fatal settlement contract is explicit:

```text
troops → 0
→ defeat edge
→ synchronous cleanup
→ aftermath fact carries target_defeated=true
→ FIRST_AID predicate rejects
```

No resurrection prevention depends merely on the accidental absence of a state after cleanup. Fatal aftermath is directly ineligible.

### 8.4 Removal events

Chosen observation semantics:

```text
natural expiry
→ STATE_EXPIRED

defeat cleanup
→ STATE_REMOVED(removal_reason=OWNER_DEFEATED)
```

State removal order is deterministic by physical `instance_id`.

### 8.5 Defeat-cleanup verdict

```text
Single owner/checkpoint model: PASS
Event semantics: PASS
Fatal FIRST_AID boundary: PASS
Stage9 authorization of changed call sites/order: FAIL separately under S10-R2-B01
```

---

## 9. SkillRuntime / Source Lifecycle Audit

### 9.1 Registry key

Current `LoadedSkillSet` already enforces unique `SkillSlot` per owner.

Draft V2 registry:

```text
(owner_id, SkillSlot) -> SkillRuntime
```

plus:

```text
lookup(owner_id, slot, expected_skill_id)
```

is sufficient for the current battle loadout model. `skill_id` does not need to be part of the key as long as lookup validates the expected loaded skill identity.

Duplicate registration is correctly an error.

### 9.2 Source death

Source death:

```text
does not remove SkillRuntime registry identity
does not automatically set enabled=false
```

This is compatible with persistent-state source-death semantics and preserves the important distinction:

```text
source dead != source skill temporarily inactive
```

### 9.3 Battle-end ownership

No long-lived global SkillRuntime store is introduced. The registry is battle-scoped, so object-lifetime cleanup can occur with BattleContext disposal. A separate gameplay cleanup event is not required.

### 9.4 PersistentSourceSkillGate mapping gap

Draft V2 defines three modes:

```text
ALWAYS_ACTIVE
QUERY_SKILL_RUNTIME
EXTERNAL_LIFECYCLE
```

but it does not normatively map real state/source families to them.

Authority requires at least the following distinctions:

| State family/source | Authority behavior | Required gate interpretation |
|---|---|---|
| continuous damage, generic family | source death persists; no generic temporary-skill gate established by family baseline | do **not** invent QUERY_SKILL_RUNTIME globally |
| FIRST_AID from COMMAND/TROOP passive source | temporary source-skill inactivity suppresses probability/recovery; clock continues | `QUERY_SKILL_RUNTIME` |
| FIRST_AID from ACTIVE source | no mid-duration deactivation mechanism established | `ALWAYS_ACTIVE` for Stage10 opportunity gate |
| FIRST_AID unresolved equipment-trait source | unresolved | `DEFER`, not guessed |
| RECUPERATION from COMMAND passive source | temporary source-skill inactivity suppresses runtime execution; clock continues | `QUERY_SKILL_RUNTIME` |
| RECUPERATION from ACTIVE source | no mid-duration deactivation | `ALWAYS_ACTIVE` |
| RECUPERATION command-source death | associated state removed by external command-aura lifecycle | `EXTERNAL_LIFECYCLE` for that lifecycle ownership |

Without this mapping, two implementers can assign different gates and produce different recovery opportunities. This is `S10-R2-M03`.

---

## 10. Refresh Generation / Provenance Audit

### 10.1 Internal generation isolation

Draft V2 correctly distinguishes:

```text
StateInstance.instance_id
= physical container identity

StateApplicationGenerationId
= one successful application/refresh generation identity
```

Same-name refresh retains physical identity as an engineering decision but always allocates a new generation identity.

Pending work behavior is clear:

```text
G1 creates intent I1
I1 remains pending
refresh → G2
I1 executes
→ source provenance = G1
→ potency = G1
→ lifecycle snapshot = G1
→ no JIT read of G2 runtime_params
```

This closes the dangerous rebinding bug identified in Round 1.

### 10.2 Active gate for old pending work

For an already-collected G1 intent:

```text
generation data / potency / source identity / lifecycle
→ immutable G1 snapshot

source-skill enabled, where QUERY_SKILL_RUNTIME is authorized
→ JIT query of the G1 snapshot's source skill identity
```

Refresh to G2 does not cause I1 to query G2's source skill or potency.

### 10.3 End-to-end provenance gap

The design does not yet freeze a complete propagation matrix for `application_generation_id` through all externally relevant DTOs/results/events.

Current concrete runtime DTOs still primarily carry:

```text
source_state_id
source_state_instance_id
```

but a retained physical `instance_id` cannot distinguish pre-refresh G1 from post-refresh G2 history.

At minimum the final design must state whether generation identity is carried directly or through a mandatory nested typed carrier for each of:

```text
DamageEffect
DamageRequest
DamageSourceRef / EffectSourceRef / OperationLineage extension as applicable
DamageResult
DamageAftermathFact
RecoveryOpportunity
RecoveryRequest
RecoveryResult
recovery observation event payloads
PipelineTrace / frozen_application_trace
```

Concrete failure scenario:

```text
G1 FIRST_AID RecoveryOpportunity is collected
→ same physical state refreshes to G2
→ G1 opportunity later succeeds
→ RecoveryRequest / RecoveryResult records only physical instance_id
→ audit history falsely appears attributable to current G2
```

This is `S10-R2-M04`.

### 10.4 Same-node ordering

Retaining physical `instance_id` implies refresh does not move the state to a new physical ordering slot. That is a reasonable engineering policy, but the regression plan should explicitly freeze it:

```text
refresh retained instance_id
→ same-node relative ordering remains unchanged
```

Otherwise a future implementation could allocate a new storage/order token while still claiming to have retained semantic identity. Recorded under regression finding `S10-R2-N03`.

---

## 11. FIRST_AID Aftermath Audit

### 11.1 Typed aftermath fact

Draft V2's `DamageAftermathFact` is structurally sufficient to distinguish:

```text
RESOLVED_HIT + positive loss
RESOLVED_HIT + weakness-zero
RESOLVED_HIT + barrier-zero
NO_RESOLVED_HIT + evasion/miss
fatal resolved hit
```

The explicit rule:

```text
prevented: bool
```

is insufficient as an eligibility shortcut is correct.

This matters because current Stage8 Weakness is a Prevention-stage source rule while Evasion-like behavior is a Hit-stage topology. Both can end in zero settlement but have different FIRST_AID semantics under the targeted research closure.

### 11.2 Evidence Gate

Draft V2 correctly states that typed topology support for:

```text
EVASION
BARRIER
```

does not promote full official production state bindings. Current Stage8 Evidence Gate still defers those bindings.

No Stage10 evidence-gate overreach was found.

### 11.3 Fatal hit

Fatal hit reaches aftermath as:

```text
target_defeated=true
```

and creates no recovery opportunity. PASS.

### 11.4 Zero-loss eligibility

Architecture can represent the desired topology, but formal authority promotion remains missing. Therefore:

```text
Architecture topology = PASS
Gameplay-authority status = FAIL / NOT PINNED
```

### 11.5 Source/event family completeness

Draft V2 explicitly handles:

```text
NORMAL_ATTACK
ACTIVE_SKILL
PERIODIC_DAMAGE
multi-hit via separate DamageInstance
COUNTER
CLEAVE
CHAIN_TRUE_FEEDBACK = NO
SHARE_DIRECT_LOSS = NO
DISTRIBUTION_DIRECT_LOSS = NO
```

but omits the independent Stage9 source family:

```text
ASSAULT
```

This omission conflicts with the formal FIRST_AID contract and becomes `S10-R2-B02`.

### 11.6 Multi-hit

The formal authority requires one independent FIRST_AID opportunity per eligible hit. Stage10's regression contract must therefore enforce one aftermath fact/opportunity per actual settled hit segment, not merely assume a producer happens to allocate one DamageInstance per segment.

The current design's intended model is compatible, but the build must prove the producer representation rather than use the phrase `each DamageInstance` as a substitute for the gameplay rule.

---

## 12. Recovery Opportunity / RNG Policy Audit

### 12.1 Eligibility versus potency

Draft V2 correctly separates:

```text
opportunity eligibility
!=
recovery amount
```

For targeted zero-loss semantics:

```text
TREATMENT_AMOUNT
resolved zero-loss + existing missing troops
→ opportunity may recover > 0

TRIGGER_DAMAGE_RATIO
resolved zero-loss
→ opportunity exists
→ ActualTargetTroopLoss basis = 0
→ nominal amount = 0
```

No hidden `amount == 0 -> skip probability` shortcut is permitted.

### 12.2 Full-troop target

Full troops do not erase the opportunity:

```text
opportunity
→ probability policy
→ nominal amount
→ RecoveryRequest
→ RecoverySystem
→ TroopSystem.restore cap
→ RecoveryResolvedResult(actual=0)
```

The current RecoverySystem already supports a resolved zero-actual recovery result; it simply does not publish `TROOPS_RECOVERED` when actual change is zero.

### 12.3 Recovery RNG engineering policy

Simulator policy:

```text
Every ADMITTED RecoveryOpportunity
→ exactly one context.random.chance(probability)
```

including:

```text
p = 0
p = 1
recoverable_gap = 0
```

Current `RandomSystem.chance()` always obtains an underlying random value before comparing, so the engineering policy is implementable without a special new RNG primitive.

The design correctly classifies official hidden p=1/gap=0 draw consumption as unknown.

### 12.4 Admission gates

Semantically required pre-RNG gates are present:

```text
generation/lifecycle validity
target alive
source-skill active gate where applicable
aftermath eligibility where applicable
```

Then:

```text
probability draw
→ resolve nominal amount
→ RecoveryRequest
→ RecoverySystem healing-ban policy
→ TroopSystem cap
```

However, Draft V2 lists target-alive and source-skill checks in slightly different relative order in two sections. Since both are pure pre-admission checks today, this does not change gameplay, but the final contract should normalize one order for trace determinism. `S10-R2-N02`.

### 12.5 RNG verdict

```text
Official hidden RNG classification: PASS
Simulator deterministic policy: PASS
Current RandomSystem compatibility: PASS
Exact pre-gate trace ordering: MINOR repair
```

---

## 13. Stage9 Ordering Audit

Stage9 final freeze explicitly states that frozen runtime semantics cannot be silently changed and that later changes to settlement layers, reaction ordering, permission matrix, provenance, or public runtime contracts require formal Stage9 reopen/impact analysis.

R1-C created Stage7 and Stage8 compatibility addenda but no Stage9 compatibility addendum.

### NoPartition

Draft V2:

```text
target settlement
→ defeat cleanup if fatal
→ death/victory observation
→ DamageAftermathPort
→ FIRST_AID if eligible
→ existing callbacks/reactions
→ complete admitted DamageInstance
```

This is internally coherent, but inserting cleanup/aftermath into the frozen Stage9 settlement contract requires Stage9 compatibility authorization.

### Share

Draft V2:

```text
target settlement
→ if fatal: cleanup/death, discard pending sharer, no FIRST_AID
→ if survives: FIRST_AID target aftermath
→ sharer DirectTroopLoss
→ sharer defeat cleanup if needed
→ existing callbacks
```

Stage9 target-first Share arithmetic remains frozen; the pending sharer amount is already fixed by the partition plan, so FIRST_AID does not recalculate share arithmetic.

The ordering nevertheless becomes part of the frozen reaction/settlement contract and needs Stage9 reopen authority.

### Distribution

Draft V2 preserves frozen Stage9 local transaction ordering:

```text
participant DirectTroopLoss drain in fixed order
→ target settlement
→ target local aftermath/FIRST_AID
```

If a participant death latches victory:

```text
current Distribution transaction was already admitted
→ remaining transaction-local target settlement drains
→ target FIRST_AID aftermath is treated as local completion work
→ no unrelated future branch is newly admitted
```

This is compatible with the existing BattleFinalizationCoordinator distinction:

```text
VICTORY_LATCHED != FINALIZED
```

but the new aftermath component still requires formal Stage9 compatibility authorization.

### Cleave

Current frozen production code executes Cleave Share in the order:

```text
Cleave target settlement
→ target death/finalization observation
→ if target survives: Share DirectTroopLoss
→ resolved fact
→ dedicated cleave FIRST_AID callback
→ attacker recovery
→ other callbacks / deferred Chain timing
```

Draft V2 deliberately changes it to:

```text
Cleave target settlement
→ defeat cleanup
→ shared DamageAftermathPort
→ FIRST_AID
→ Share DirectTroopLoss
→ attacker recovery
→ callbacks
```

Draft V2 itself calls this an intentional closure of the Stage9 implementation asymmetry.

That is a material frozen reaction-order change, not merely constructor cleanup. Stage9's own formal reopen policy prohibits silently making this change from a later stage.

This is `S10-R2-B01`.

---

## 14. Dependency / Composition Audit

### 14.1 RuleIntent ordering

Model B is implementable:

```text
TriggerIntentBatch.ordered_intents
= tuple[Effect | RecoveryOpportunity, ...]
```

Example:

```text
Effect A
Recovery B
Effect C
```

RuleHookSystem can dispatch in exactly:

```text
A → B → C
```

without splitting the intents into separate lists. One typed result is retained per original intent.

### 14.2 DamageAftermath cycle analysis

Required runtime edge:

```text
DamageInstanceCoordinator
→ DamageAftermathSystem
→ TriggerSystem.collect_after_damage
→ RecoveryOpportunitySystem
→ RecoverySystem
→ TroopSystem
```

The dedicated after-damage collector is restricted to RecoveryOpportunity and cannot return ordinary DamageEffect/StateMutation work. Therefore there is no runtime edge:

```text
DamageAftermathSystem
→ EffectExecutor
→ DamageInstanceCoordinator
```

and no recursion cycle is required.

Neutral DTO modules can carry `DamageAftermathFact`, `RecoveryOpportunity`, and generation IDs without importing service implementations, so no type/import cycle is necessary either.

### 14.3 BattleSystems future construction order

Draft V2's proposed order is feasible:

```text
1. battle-scoped registries / trackers
2. low-level attribute/troop/state/execution systems
3. DefeatCleanupPort
4. RecoverySystem + RecoveryOpportunitySystem
5. Stage8 rule/formula/frozen-basis components
6. DamageResolution / DirectTroopLoss / partition / finalization
7. TriggerSystem
8. DamageAftermathSystem
9. DamageInstanceCoordinator
10. Cleave / Chain / Counter
11. EffectExecutor
12. RuleHookSystem
13. Action systems
14. BattleEngine
```

The existing Stage9 one-time typed `DamageResolutionSystem.bind_coordinator(...)` seam may be retained. No new service locator, circular lambda capture, or arbitrary hidden backpatch is required.

### 14.4 Composition verdict

```text
Constructor DAG: PASS
Runtime callback DAG: PASS
Type/import DAG: PASS
Mixed RuleIntent ordering: PASS
Hidden new late binding: none required
```

The architecture is constructible once the contract findings are repaired.

---

## 15. Migration / Evidence Gate Audit

### 15.1 Old synthetic params

Draft V2 now freezes a single official production path:

```text
PeriodicDamageStateParams
→ test-only legacy synthetic

PeriodicRecoveryStateParams
→ test-only legacy synthetic

ContinuousDamageStateParams / FirstAidStateParams / RecuperationStateParams
→ official Stage10 runtime path
```

Historical Stage7 tests may preserve the old synthetic path, but official state definitions may not use it after Stage10 build.

This closes Round1 migration ambiguity.

### 15.2 `cleave_first_aid`

The old dedicated Cleave callback is a migration target and must not coexist in final Stage10 production composition with the shared DamageAftermathPort.

The build must have one aftermath engine, not two “temporarily equivalent” engines that remain forever because deleting old code is apparently considered impolite.

### 15.3 Evidence Gate

Draft V2 does not authorize full production bindings for:

```text
EVASION
BARRIER
CRITICAL
STRATEGY_CRITICAL
DAMAGE_REDUCTION_PIERCE
positive dispel universal behavior
```

Typed topology support is not equivalent to official state promotion. PASS.

---

## 16. Regression Contract Audit

Draft V2 includes most of the repaired high-risk scenarios:

```text
PRE_BATTLE N=1 / N=2
before-action apply
after-action apply
refresh generation isolation
source-dead DOT
owner death mid-hook
weakness-zero / barrier-zero / evasion
zero-loss treatment / ratio
full-troop recovery
p=0 / p=1 / zero-gap RNG
Share / Distribution / Cleave
victory-latched local drain
LIVE_RUNTIME regression
FROZEN_APPLICATION source no-recalc
old generation pending intent
```

Mandatory additions before freeze/build:

```text
1. ASSAULT / pursuit damage → FIRST_AID eligible
2. refresh-retained physical instance_id preserves same-node order
3. battle finalizes before owner's pending last ActionStart → explicit state teardown/visibility behavior
4. G1 pending recovery after G2 refresh → RecoveryRequest/Result/event still identifies G1
5. mixed RuleIntent A → Recovery B → Effect C exact ordering
6. current-generation physical expiry must not accidentally remove a freshly refreshed replacement generation
```

The missing regression obligations are recorded as `S10-R2-N03`; the underlying ASSAULT/lifecycle/provenance defects carry higher severities separately.

---

## 17. Two-Implementer Test

| Topic | Would two independent implementers necessarily produce same observable behavior? | R2 result |
|---|---|---|
| Stage7 owner-death abort | YES, except execution-right owner wording | conditional PASS |
| PRE_BATTLE N=1 | YES | PASS |
| finite expiration at last ActionStart | YES during normal round progression | PASS |
| battle ends before last ActionStart | NO | FAIL / M05 |
| source-dead DOT | YES | PASS |
| REBELLION frozen route/defense | YES | PASS |
| refresh pending intent | YES internally | PASS |
| downstream generation audit provenance | NO | FAIL / M04 |
| FIRST_AID weakness-zero | architecture YES, authority not pinned | FAIL authority sync |
| FIRST_AID barrier-zero | architecture YES, authority not pinned | FAIL authority sync |
| FIRST_AID evasion | architecture YES, authority not pinned | FAIL authority sync |
| FIRST_AID full troops | simulator pipeline YES, authority classification still needs promotion if claimed gameplay | conditional |
| p=1 RNG | YES as engineering policy | PASS |
| p=0 RNG | YES as engineering policy | PASS |
| ASSAULT/pursuit FIRST_AID | NO / current frozen policy conflicts | FAIL / B02 |
| Share | design behavior unique | PASS subject Stage9 reopen |
| Distribution | design behavior unique | PASS subject Stage9 reopen |
| Cleave | NO between Stage9-frozen and Stage10-draft conforming implementations | FAIL / B01 |
| victory-latched admitted drain | YES | PASS |

Result:

```text
Two-Implementer Test = FAIL
```

---

## 18. New Findings

### BLOCKER

#### S10-R2-B01 — Draft V2 silently changes frozen Stage9 reaction ordering without formal Stage9 reopen

**ID:** `S10-R2-B01`  
**Severity:** `BLOCKER`

**Source location:**

```text
stages/stage9/STAGE9_DESIGN_FREEZE.md
stages/stage9/STAGE9_FREEZE_RECORD.md
stages/stage9/hardening/STAGE9_REGRESSION_CONTRACTS.md
stages/stage10/STAGE10.md §23-25 / §31-32
```

**Contract/code location:**

```text
sgs_v2/battle_core/damage_instance_coordinator.py
sgs_v2/battle_core/cleave_derived_damage_system.py
sgs_v2/battle_core/battle_finalization_coordinator.py
```

**Problem:**  
Stage9 formally freezes settlement layers, reaction ordering, permission matrix, finalization ownership, and the public runtime contract. It explicitly requires `DESIGN REOPEN → impact analysis → targeted audit → re-freeze` for a later semantic change. R1-C created Stage7 and Stage8 addenda but no Stage9 reopen. Draft V2 nevertheless changes Cleave Share/FirstAid ordering and inserts new synchronous cleanup/aftermath work into frozen Stage9 routes.

**Why it matters:**  
This is a direct frozen-authority conflict. A Stage9-conforming implementation and a Stage10-Draft-V2-conforming implementation can legally produce different reaction order.

**Concrete failure scenario:**

```text
Cleave secondary hits target T
T survives and has FIRST_AID
Share plan contains sharer S

Stage9 frozen runtime:
T settlement → S direct loss → FIRST_AID(T)

Draft V2:
T settlement → FIRST_AID(T) → S direct loss
```

Even if the Share amount was preplanned, death/finalization/event ordering and downstream reaction timing differ.

**Required repair:**  
Create a formal Stage9 → Stage10 limited compatibility reopen/addendum. Enumerate every affected Stage9 surface and exact new ordering for NoPartition, Share, Distribution, Cleave, direct-loss death cleanup, aftermath, callbacks, and finalization. Perform the required targeted Stage9 audit/re-freeze. Alternatively, change Stage10 to preserve the frozen Stage9 order exactly.

**Gameplay research required?** `NO` for the architecture authorization itself.  
**Authority sync required?** `NO`.

---

#### S10-R2-B02 — FIRST_AID ASSAULT / pursuit eligibility conflicts with frozen Stage9 recovery permission

**ID:** `S10-R2-B02`  
**Severity:** `BLOCKER`

**Source location:**

```text
Gameplay Authority:
states/persistent/first_aid/MECHANISM_CONTRACT.md §3 Damage_Eligibility

Stage10:
stages/stage10/STAGE10.md §33 FIRST_AID / aftermath source-family permissions
```

**Contract/code location:**

```text
sgs_v2/battle_core/operation_identity.py :: SourceType.ASSAULT
sgs_v2/battle_core/reaction_permission_policy.py :: can_trigger_recovery()
```

**Problem:**  
Official FIRST_AID authority freezes pursuit/counterattack damage as eligible. Stage9 has a distinct `SourceType.ASSAULT`, but the frozen `can_trigger_recovery()` allow-list currently includes NORMAL_ATTACK, ACTIVE_SKILL, PERIODIC_DAMAGE, CLEAVE, and COUNTER, not ASSAULT. Draft V2's source-family table also fails to name ASSAULT explicitly.

**Why it matters:**  
A conforming implementation that reuses the current Stage9 permission matrix will suppress an officially eligible FIRST_AID opportunity. This is observable wrong gameplay.

**Concrete failure scenario:**

```text
ASSAULT damage
→ target survives a resolved hit
→ target has operational FIRST_AID

Gameplay Authority:
independent FIRST_AID opportunity = YES

Current Stage9 recovery permission:
ASSAULT omitted → NO
```

**Required repair:**  
Include `ASSAULT` explicitly in the Stage10 aftermath source-family permission matrix and formally reopen the Stage9 permission matrix to authorize the change. Add a mandatory pursuit/ASSAULT FIRST_AID regression.

**Gameplay research required?** `NO`; current official authority already answers eligibility.  
**Authority sync required?** `NO`.

---

### MAJOR

#### S10-R2-M01 — Zero-loss FIRST_AID closure is not formally promoted into Gameplay Authority

**ID:** `S10-R2-M01`  
**Severity:** `MAJOR`

**Source location:**

```text
stages/stage10/STAGE10.md §0.1 / §2 / §15-19
Gameplay Authority main @ 61f2be7e...
states/persistent/first_aid/MECHANISM_CONTRACT.md
```

**Contract/code location:**  
Authority repository contract/promotion boundary.

**Problem:**  
Draft V2 labels weakness-zero, barrier-zero, evasion exclusion, and full-troop opportunity facts `GAMEPLAY FROZEN`, but no current official Gameplay Authority commit/branch contains the targeted research report or updated mechanism contract.

**Why it matters:**  
Stage10 Design Freeze would otherwise depend on chat/task/Battle-repo closure rather than repository-pinned mechanism authority.

**Concrete failure scenario:**  
A future maintainer reads only the official authority repository and the Battle runtime freeze artifacts. They encounter a FIRST_AID zero-loss behavior in production that cannot be traced to the official frozen mechanism contract.

**Required repair:**  
`AUTHORITY PROMOTION REQUIRED`: check in the evidence-backed targeted research and update/refreeze the official FIRST_AID mechanism contract with exact zero-loss topology. Preserve official hidden PRNG consumption as UNKNOWN if that is the evidence result.

**Gameplay research required?** `NO` as the immediate action if the existing evidence package is real and recoverable; this is promotion/synchronization.  
**Authority sync required?** `YES`.

---

#### S10-R2-M02 — Per-intent ExecutionRight owner is duplicated/ambiguous

**ID:** `S10-R2-M02`  
**Severity:** `MAJOR`

**Source location:**

```text
stages/stage10/STAGE10.md §4
stages/stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md §4 / §6
```

**Contract/code location:**

```text
sgs_v2/battle_core/rule_hook_system.py
sgs_v2/battle_core/effect_executor.py
sgs_v2/battle_core/execution_right_system.py
```

**Problem:**  
Stage10 says EffectExecutor validates execution right before each Effect, while the normative Stage7 addendum says RuleHookSystem/orchestration obtains the typed execution-right decision before every RuleIntent and owns abort/dispatch. RecoveryOpportunity does not pass through EffectExecutor.

**Why it matters:**  
The design does not have one unique owner for the hard boundary. Two implementations can double-check, check at different times, or let Effect and RecoveryOpportunity use different gates.

**Concrete failure scenario:**  
An owner dies after one intent. RuleHookSystem marks the next ordinary Effect allowed using one snapshot, then EffectExecutor performs a second differently-scoped query, while a sibling RecoveryOpportunity only receives the first query.

**Required repair:**  
Choose one normative model. Preferred minimal model: RuleHookSystem owns the per-RuleIntent execution-right gate and tail abort; EffectExecutor remains a router for an already-admitted ordinary Effect. If defense-in-depth validation remains in EffectExecutor, define it as invariant assertion with no independent gameplay decision.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

#### S10-R2-M03 — PersistentSourceSkillGate modes are defined but not mapped to real state/source families

**ID:** `S10-R2-M03`  
**Severity:** `MAJOR`

**Source location:**

```text
stages/stage10/STAGE10.md §12
Gameplay Authority FIRST_AID and RECUPERATION contracts
methodology/CONTINUOUS_DAMAGE_FAMILY_BASELINE.md
```

**Contract/code location:**  
Future `PersistentSourceSkillGate` / `RecoveryOpportunitySystem` construction and opportunity admission.

**Problem:**  
The enum meanings are closed, but no normative assignment table specifies which state/source skill uses `ALWAYS_ACTIVE`, `QUERY_SKILL_RUNTIME`, or `EXTERNAL_LIFECYCLE`.

**Why it matters:**  
Command/troop FIRST_AID and command RECUPERATION have frozen temporary-deactivation behavior, while active-sourced versions do not. Continuous damage has no generic source-skill deactivation authority. A generic implementation choice would invent or suppress gameplay.

**Concrete failure scenario:**  
Implementer A makes all FIRST_AID `QUERY_SKILL_RUNTIME`; implementer B makes only command/troop sources query it. An active-sourced FIRST_AID opportunity then differs when its source runtime flag changes for unrelated engineering reasons.

**Required repair:**  
Add an authority-cited mapping by state family and source-skill category. Explicitly defer unresolved equipment/unknown categories rather than guessing.

**Gameplay research required?** `NO` for the currently authoritative categories; unresolved categories may remain deferred.  
**Authority sync required?** `NO`.

---

#### S10-R2-M04 — Application generation provenance is not preserved through all required result/event carriers

**ID:** `S10-R2-M04`  
**Severity:** `MAJOR`

**Source location:**

```text
stages/stage10/STAGE10.md §13-14 / §15 / §29
```

**Contract/code location:**

```text
sgs_v2/battle_core/effects.py
sgs_v2/battle_core/damage_system.py
sgs_v2/battle_core/recovery_system.py
sgs_v2/battle_core/events.py
```

**Problem:**  
Draft V2 correctly snapshots generation inside pending work, but it does not freeze how generation identity survives transformation into DamageRequest/Result, RecoveryRequest/Result, and observation facts. Current DTOs mostly expose only physical `source_state_instance_id`.

**Why it matters:**  
Because refresh retains physical instance ID, instance ID alone cannot distinguish G1 from G2 after refresh. Historical audit/replay becomes ambiguous even if numerical gameplay happened to use the correct G1 snapshot.

**Concrete failure scenario:**

```text
G1 RecoveryOpportunity collected
→ physical instance refreshes to G2, same instance_id
→ G1 opportunity executes
→ RecoveryResult/event contains only instance_id
→ downstream history appears to belong to G2
```

**Required repair:**  
Add a normative generation-provenance propagation matrix. Every state-sourced Damage/Recovery request, result, aftermath fact, event fact, and trace must carry generation directly or through a mandatory immutable nested typed reference. Non-state routes may use `None`.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

#### S10-R2-M05 — Physical state lifetime is undefined when battle finalizes before the last eligible ActionStart

**ID:** `S10-R2-M05`  
**Severity:** `MAJOR`

**Source location:**

```text
stages/stage10/STAGE10.md §8-9 / §25
```

**Contract/code location:**

```text
sgs_v2/battle_core/engine.py
sgs_v2/battle_core/state_lifecycle_system.py
sgs_v2/battle_core/battle_finalization_coordinator.py
```

**Problem:**  
Physical expiry is defined only at completion of the owner's last eligible ActionStart window or earlier owner defeat. The design does not say what happens if battle finalizes first while the owner remains alive.

**Why it matters:**  
The BattleContext remains inspectable after `run()`. Without a terminal lifecycle rule, physically attached states can survive in the registry after battle, contradicting the design's claim of no observable stale/ghost interval.

**Concrete failure scenario:**  
Unit B has an N=2 state whose last window would be Round2 B ActionStart. Unit A kills the opposing commander at Round2 A ActionStart/Action and the battle finalizes before B's slot. B remains alive but its state never reaches the physical expiry node.

**Required repair:**  
Freeze one battle-end rule: either battle-scoped state registry is synchronously cleared by StateLifecycleSystem at a canonical finalization/BATTLE_END boundary with defined observation semantics, or the public contract explicitly makes post-finalization state registry non-queryable/non-semantic. The current design must not leave both choices valid.

**Gameplay research required?** `NO`; this is battle-runtime terminal ownership unless the project intends to reproduce post-battle removal logs.  
**Authority sync required?** `NO`.

---

### MINOR

#### S10-R2-N01 — ActionProgressTracker ordering relative to UNIT_ACTION_STARTED publication is not exact

**ID:** `S10-R2-N01`  
**Severity:** `MINOR`

**Source location:** `STAGE10.md §9`  
**Contract/code location:** `engine.py`

**Problem:**  
The tracker is before Stage10 collection but not uniquely ordered relative to the existing `UNIT_ACTION_STARTED` observation publish.

**Why it matters:**  
Gameplay is unaffected because EventBus is observation-only, but trace/audit ordering can differ.

**Concrete failure scenario:**  
Two implementations emit an observer snapshot around `UNIT_ACTION_STARTED`; one already reports `action_progress=started`, the other marks immediately after publication.

**Required repair:**  
Freeze exact engine order, preferably by naming the sequence around phase entry, event publication, tracker mark, RuleHookSystem, and control-state suppression.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

#### S10-R2-N02 — Recovery pre-RNG gate order is written inconsistently

**ID:** `S10-R2-N02`  
**Severity:** `MINOR`

**Source location:** `STAGE10.md §18 / §22`  
**Contract/code location:** future `RecoveryOpportunitySystem`

**Problem:**  
One section lists source-skill gate before target-survival validation; another lists target alive before source-skill lookup.

**Why it matters:**  
Both checks are pure today, so gameplay is the same, but trace failure reason and future side-effect hardening could diverge.

**Concrete failure scenario:**  
A stale opportunity has both a dead target and disabled source skill. Different implementations report different terminal admission reason.

**Required repair:**  
Freeze one exact pre-RNG gate sequence.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

#### S10-R2-N03 — Regression contract omits several newly critical invariants

**ID:** `S10-R2-N03`  
**Severity:** `MINOR`

**Source location:** `STAGE10.md §34`  
**Contract/code location:** future Stage10 regression suite

**Problem:**  
The regression list does not explicitly require ASSAULT FIRST_AID, battle-end state cleanup/visibility, generation round-trip through RecoveryRequest/Result/event, mixed RuleIntent A-B-C ordering, or same-node ordering preservation on retained-instance refresh.

**Why it matters:**  
These are precisely the seams where the repaired design extends older frozen runtime contracts.

**Concrete failure scenario:**  
Implementation passes the listed suite while silently dropping application generation from recovery events or changing state ordering after refresh.

**Required repair:**  
Add the missing regressions after the underlying BLOCKER/MAJOR contracts are repaired.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

### HARDENING

#### S10-R2-H01 — Add an exactly-once defeat-cleanup conformance spy across every destructive route

**ID:** `S10-R2-H01`  
**Severity:** `HARDENING`

**Source location:** Stage10 defeat-cleanup architecture  
**Contract/code location:** standard, direct loss, Cleave, Chain, Counter paths

**Problem:**  
A single port design can still be incorrectly wired twice or omitted on one edge during implementation.

**Why it matters:**  
Duplicate cleanup can publish duplicate removal facts; missing cleanup leaves ghost states.

**Concrete failure scenario:**  
Cleave direct loss calls DefeatCleanupPort in both resolver and coordinator after the same alive→dead edge.

**Required repair:**  
Conformance test each death-capable route with a spy asserting exactly one cleanup commit before subsequent defeated-owner work.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

#### S10-R2-H02 — Add frozen-lane instrumentation proving zero current-source formula/provider reads

**ID:** `S10-R2-H02`  
**Severity:** `HARDENING`

**Source location:** Stage8 compatibility addendum / FROZEN_APPLICATION  
**Contract/code location:** DamageSystem + frozen-basis producer/consumer

**Problem:**  
Golden numerical tests can miss accidental source-runtime reads when current source values happen to match snapshots.

**Why it matters:**  
A source-dead or source-mutated regression may otherwise reintroduce forbidden live recalculation.

**Concrete failure scenario:**  
Implementation uses frozen ATK but accidentally calls the current modifier provider again; test fixture has unchanged modifier and still passes.

**Required repair:**  
Use spies/poisoned current-source values/provider calls to assert the frozen lane never rediscoveries source formula facts or ordinary modifier providers.

**Gameplay research required?** `NO`.  
**Authority sync required?** `NO`.

---

## 19. Mandatory Repair Set

Stage10 Design Freeze remains blocked until the following are completed:

```text
R2-1  Formal Stage9 compatibility reopen/addendum
      - exact NoPartition / Share / Distribution / Cleave ordering
      - DefeatCleanup insertion
      - DamageAftermath insertion
      - finalization/local-drain relationship
      - targeted audit + re-freeze required by Stage9 policy

R2-2  Repair Stage9 FIRST_AID recovery permission for ASSAULT/pursuit
      - explicit SourceType.ASSAULT permission
      - formal permission-matrix reopen authorization
      - regression

R2-3  Promote targeted FIRST_AID zero-loss research into formal Gameplay Authority
      - evidence-backed research report
      - updated/refrozen FIRST_AID MECHANISM_CONTRACT
      - do not promote unknown PRNG consumption as official fact

R2-4  Choose one per-RuleIntent ExecutionRight owner

R2-5  Add state/source-specific PersistentSourceSkillGate mapping
      - COMMAND/TROOP vs ACTIVE vs EXTERNAL lifecycle
      - unresolved categories deferred

R2-6  Freeze end-to-end StateApplicationGenerationId propagation
      - damage request/result/trace/aftermath
      - recovery opportunity/request/result/events

R2-7  Freeze battle-end physical state lifecycle / post-finalization query semantics

R2-8  Normalize minor ordering and regression obligations
      - ActionProgressTracker exact point
      - pre-RNG gate sequence
      - ASSAULT, generation, battle-end, mixed-intent, same-node tests
```

No production code should be modified while repairing this design round. The next step is a design/authority repair round, not implementation.

---

## 20. Final Verdict

### Round 1 closure

```text
Original BLOCKER reviewed = 7
Original MAJOR reviewed   = 6

CLOSED           = 11
PARTIALLY CLOSED = 1
STILL OPEN       = 0
REGRESSED        = 1
```

### New Round 2 findings

```text
BLOCKER   = 2
MAJOR     = 5
MINOR     = 3
HARDENING = 2
```

### Authority synchronization

```text
FAIL / AUTHORITY NOT PINNED
```

### Final gate

```text
VERDICT = FAIL / DESIGN REPAIR ROUND 2 REQUIRED

Stage10 Design Freeze authorized = NO
Stage10 Build Prompt authorized   = NO
Stage10 implementation authorized = NO
PR merge authorized by this audit = NO
```

The repaired architecture is substantially closer to a buildable system, and the FROZEN_APPLICATION lane itself now survives the adversarial audit. That does not rescue the overall freeze gate: a later stage cannot silently rewrite Stage9's frozen reaction ordering, `ASSAULT` cannot vanish from an officially eligible FIRST_AID family, and project-owner closure cannot substitute for formal Gameplay Authority promotion.
