# Stage13-D1 PendingWork Runtime Design

Date: 2026-10-04. Provenance: ENGINEERING_POLICY, subordinate to frozen mechanism contracts.
Baseline Runtime main: `b3b20e42f17262bf866448505b6895525dd19248`.
Baseline Research main: `f7b646876c976c8cdfb8ebb5c5a9ce11b909906a`.

## Existing delayed work inventory (completed before implementation)

| Existing mechanism | Current owner | Timing model | Snapshot/JIT model | Cancellation model | Reusable? | Must migrate? | Must preserve? |
|---|---|---|---|---|---|---|---|
| Continuous/DOT | TriggerSystem, ContinuousDamageBasisProducer, DamageInstanceCoordinator | holder action-start, StateLifecycle window | frozen source basis; live target defense/advancement/troops | state eligibility, frozen ExecutionRight | yes, effect dispatch | no | formula, RNG, event order |
| Periodic damage/recovery fixtures | TriggerSystem, EffectExecutor | typed round/action hooks | params / domain request | state lifetime and rule intent rights | yes | no | existing fixtures |
| Recuperation | RecoveryOpportunitySystem, TreatmentFormulaSystem, RecoverySystem | holder action-start | application potency snapshot; live HealingBlock/wounded/missing tail | state/generation validity, target checks | yes, adapter proof | no | all frozen semantics |
| Sabotage scheduled equipment opportunity | EquipmentEffectivenessPolicy, ExecutionRightSupport | caller-owned opportunity | scheduled contribution rechecked at execution | suppress/deny, no replay | yes | no | no invented Sabotage queue |
| Preparation minimal runtime | PreparationStateOwner, PreparationInterruptionPort | PREPARING storage only | admitted operation/provider identity | typed interruption | identity only | no | full preparation execution unsupported |
| Round/action hooks | RuleHookSystem, TriggerSystem | engine macro checkpoints | intent collection then execution rights | typed intent denial | yes | no | existing hooks run first |
| State lifetime | StateLifetimeSpec, StateLifecycleSystem | phase expiry/action-start counters | generation snapshot / live residence | physical remove/expire/defeat | yes, validity query | no | NOT arbitrary work lifetime |
| ExecutionRightSpec | ExecutionRightSupport | snapshot admission / execution recheck | actor/provider/target/equipment/state dimensions | typed denial/unsupported | yes | no | one permission owner |
| Operation identity/lineage | OperationIdAllocator, OperationLineage | per-battle stable allocation | historical attribution | no ordering authority | extend | no | IDs NEVER priority comparators |
| Finalization barrier | BattleFinalizationCoordinator | six legacy barriers, admitted transaction drain | victory latch != finalized | no future admission after latch | yes | no | pending storage never blocks exit |
| FutureAdmissionGate | FutureAdmissionGate | RUNNING-only future admission | coordinator termination state | latch denies new work | extend separate D1 query | no | exactly six Stage9 branch kinds unchanged |
| Provider validity | ProviderValidityPolicy | live evaluation | typed Skill/EquipmentProviderRef | invalid provider denial | yes | no | attribution != dependency |
| Target validity | ExecutionTargetEligibilityPolicy | live mechanism adapters | locked identity, live eligibility | deny/unsupported | yes | no | no inferred relation rules |
| Source-dependent states | StateEffectivenessPolicy, DependencyEvaluationSupport | dependency evaluation | state/provider nodes | suppressed/removed per contract | yes | no | no duplicate graph |

## Minimal architecture decision

REUSE -> EXTEND -> COMPOSE. PendingWorkRegistry stores immutable records per BattleContext;
PendingWorkSystem alone creates, selects, transitions, dispatches and cancels them.
OperationIdAllocator allocates PendingWorkId and minimal Skill/Effect/Recovery operation IDs;
OperationLineage receives optional parent references including StateApplicationGenerationId.
Existing ID counters and random stream are untouched. Dispatch trace records child operation lineage.

Timing supports specified round/phase (ROUND_START, UNIT_ACTION_START, ROUND_END),
next occurrence of a phase, holder next action-start, and explicit one-shot future trigger.
The engine dispatches AFTER existing hooks/lifetime settlement and BEFORE the matching
finalization barrier. Empty registry has zero events/RNG and no gameplay effect.
Signals are synchronous typed calls, not EventBus subscriptions. Exact points missed by
the clock expire without catch-up. Next occurrence means strictly after creation.

Lifetime ONE_SHOT / UNTIL_EXECUTED / UNTIL_ROUND are implemented. REPEAT_N_TIMES
is a typed RESERVED seam rejected before storage: D1 deliberately freezes only one-shot
execution; it does not claim a repeat scheduler or UsageBudget implementation.
UNTIL_ROUND is inclusive through that round; expiry occurs on the next timing point.

States: PENDING -> EXECUTING -> COMPLETED; PENDING -> CANCELLED/EXPIRED.
Dispatcher exception: EXECUTING -> CANCELLED (DISPATCH_FAILED), rethrow, never retry;
partial gameplay is NOT rolled back. Terminal records cannot transition or replay.

Source policy is typed: independent historical source or source-required-alive.
Provider/target/equipment/state admission and recheck reuse ExecutionRightSpec.
SNAPSHOT_AT_ADMISSION is actually evaluated at creation, not blindly trusted.
TARGET_MUST_REMAIN_ALIVE adds a physical alive requirement; relation/eligibility
continues to belong to ExecutionTargetEligibilityPolicy with explicit operation kind.
Failed validity = CANCELLED; elapsed deadline/missed point = EXPIRED.

Snapshot values are recursively immutable data, copied/frozen at creation. Declared
LIVE_AT_EXECUTION keys use registered pure read adapters at dispatch, never at creation.
Mechanism contracts choose dimensions; scheduler contains no formula or targeting math.
Opaque gameplay objects/callables are excluded from payloads. Mechanism dispatch adapters
close over existing immutable descriptors and delegate effects to existing owners.

FutureAdmissionGate's D1 query authorizes only RUNNING, additionally respecting context.ended.
Check before creation, before each due-work execution and after validity/live-read adapters.
Stored work is never an admitted Damage/Action transaction or finalization barrier.
Victory latch cancels remaining future work; a synchronously dispatched effect's already
admitted domain transaction drains according to its frozen coordinator. No post-battle override.

Due order: explicit per-registry creation_sequence, not ID value, dict order, or RNG.
Due set is captured once; work created inside dispatch waits for a later timing occurrence.
Reentrant dispatch is rejected. One context binds one system/registry; cross-battle use is rejected.

## Adapter proof and boundaries

Opt-in Recuperation adapter delegates the existing RecoveryOpportunity unchanged to its owner.
It does not migrate automatic state ticks. Compare baseline and adapter on two equal seeded
contexts: RNG continuation, domain event order and payloads, recovery result, troops/wounds.
Work lifecycle/lineage facts are retained in a separate typed registry trace, preserving
the existing gameplay EventBus trace. Snapshot/JIT field selection remains mechanism-owned.

D2 frequency/budgets; D3 composition; D4 attribute/modifier provenance; D5 RNG trace;
G whole-battle replay remain open. No new tactics, recovery formulas or full preparation.
