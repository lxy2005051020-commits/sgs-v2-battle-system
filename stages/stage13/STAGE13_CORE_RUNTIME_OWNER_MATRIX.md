# Stage13 Core Runtime Owner Matrix

> Purpose: map each gameplay truth to exactly one canonical production owner before Stage13 architecture work.
>
> Baseline: Battle main 5ebe6d121d5bc55351b5e907bacf168ec38ce1b7

## 1. Owner rule

One gameplay truth gets one canonical owner. Adapters may translate, policies may contribute, and EventBus may publish committed facts, but none of them becomes a shadow owner.

## 2. Current canonical owners

| Truth | Canonical Owner | Supporting / Adapter Owners | Status | Stage13 Rule |
|---|---|---|---|---|
| Battle phase progression | BattleEngine | BattlePhase enum | CANONICAL | extend timing via typed opportunities, not event listeners |
| Battle termination state | BattleFinalizationCoordinator | VictorySystem / BattleEngine | CANONICAL | preserve termination permits/barriers |
| Unit identity / base runtime facts | UnitRuntime | BattleContext | CANONICAL | no Skill-local unit truth |
| Team membership / commander / lineup | UnitRuntime + BattleContext | LineupPosition | CANONICAL | no selector-local relation reconstruction |
| Troop mutation | TroopSystem | DamageResolutionSystem / RecoverySystem | CANONICAL | no direct troop writes in new effects |
| Wounded / recoverable capacity | UnitRuntime.wounded_troops + TroopSystem mutation rules | DamageResolutionSystem / RecoverySystem / BattleEngine round boundary | CANONICAL FOR STAGE13-B1 INTEGRATED SLICE | generation, consumption, decay and defeat cleanup remain centralized |
| Alive / defeated truth | UnitRuntime.is_alive | DefeatCleanupPort / VictorySystem | CANONICAL | defeat consumers query this truth; cleanup does not redefine it |
| Holder defeat cleanup | DefeatCleanupPort | StateLifecycleSystem / effectiveness transition | CANONICAL | source-death behavior remains separate |
| Primary action ordering | ActionOrderSystem | AttributeSystem / Stage11StateRuntime | CANONICAL | FIRST_STRIKE/SURPRISE rules remain frozen |
| Action-start / acted tracking | ActionProgressTracker | BattleEngine | CANONICAL | future frequency owner may consume, not duplicate |
| Natural action permission | CurrentActorPermissionPolicy / ActionSystem | Stage12 state adapters | CANONICAL | unsupported remains explicit |
| Normal attack orchestration | NormalAttackSystem | TargetResolutionSystem / DamageInstanceCoordinator | CANONICAL | do not build a second Skill-owned normal attack |
| Normal attack target arbitration | TargetResolutionSystem | TargetSystem / Stage9 state runtime | CANONICAL | taunt/confusion/guard order remains frozen |
| Generic target candidate sets | TargetSystem | SkillResolver producer layer | CANONICAL | future selectors consume candidate sets |
| Skill target operation identity/freshness | TargetOperation / TargetOperationProducer | SkillTargetPolicy | CANONICAL | preserve NEW_QUERY vs continuation semantics |
| Skill target constraints | SkillTargetPolicy | mechanism adapters | CANONICAL | policy consumes zero RNG |
| Random target sampling | TargetSystem -> RandomSystem | SkillResolver | CANONICAL | no policy-layer sampling |
| Battle PRNG service | RandomSystem through BattleContext.random | domain random-decision owners | CANONICAL | no second PRNG service |
| State physical storage | StateRegistry | StateLifecycleSystem | CANONICAL | registry is storage, lifecycle owns mutation |
| State physical lifecycle mutation | StateLifecycleSystem | StateApplicationCoordinator / StateRemovalCoordinator | CANONICAL | transaction path only |
| State admission | StateAdmissionPolicy | mechanism adapters | CANONICAL | pure decision; no mutation/RNG |
| State conflict/reapplication | StateConflictPolicy | mechanism adapters | CANONICAL | unsupported boundaries stay explicit |
| State current effectiveness | StateEffectivenessPolicy | dependency/effectiveness adapters | CANONICAL | state-specific runtime may query, not duplicate |
| State removal authorization | StateRemovalPolicy | StateRemovalCoordinator | CANONICAL | category removal must extend this owner |
| State application transaction | StateApplicationCoordinator | StateLifecycleSystem / DependencyEvaluationSupport | CANONICAL | preflight then atomic commit |
| State lifetime | StateLifetimeSpec / StateLifecycleSystem | PersistentLifecycleWindow | CANONICAL | not automatically generic work lifetime |
| State application generation | StateGenerationAllocator / StateGenerationSnapshot | StateLifecycleSystem | CANONICAL | snapshot belongs to a generation |
| Provider identity | SkillProviderRef / EquipmentProviderRef | Provider registry | CANONICAL | attribution is not dependency |
| Provider current validity | ProviderValidityPolicy | SkillRuntimeRegistry / Equipment registry | CANONICAL | no state-specific provider shadow owner |
| Equipment contribution identity | EquipmentContributionRegistry | EquipmentEffectivenessPolicy | CANONICAL | contribution and provider identity remain distinct |
| Equipment contribution effectiveness | EquipmentEffectivenessPolicy | domain contribution consumers | CANONICAL | domain math remains outside policy |
| Dependency graph | DependencyEvaluationSupport | StateEffectivenessPolicy / ProviderValidityPolicy | CANONICAL | StateNode + ProviderNode only until concrete need |
| Skill holder permission | SkillPermissionPolicy | state rule adapters | CANONICAL | permission is pre-RNG |
| Skill operation admission | SkillOperationAdmissionCoordinator | ProviderValidityPolicy + SkillPermissionPolicy | CANONICAL | metadata interoperability only in Stage13 |
| Preparation physical PREPARING record | PreparationStateOwner | PreparationInterruptionPort | CANONICAL / MINIMAL | not full preparation runtime |
| Damage formula / result calculation | DamageSystem | formula policies / AttributeSystem | CANONICAL | no Effect-owned damage math |
| Damage instance lifecycle | DamageInstanceCoordinator | OperationIdAllocator | CANONICAL | new damage families route here |
| Damage target settlement | DamageResolutionSystem | TroopSystem | CANONICAL | assigned vs actual loss stays typed |
| Damage partition plan | DamagePartitionCoordinator | Stage9 state runtime | CANONICAL | 690086 debt preserved |
| Damage hit/prevention | HitResolutionSystem / DamagePreventionSystem | rule provider | CANONICAL | no new family-specific bypass owner |
| Damage modifier resolution | DamageModifierSystem | typed contributions | CANONICAL / STAGE13-B2 EXTENDED | ordinary same-side increase/reduction pools are algebraic; cross-side composition remains multiplicative |
| Critical family state resolution | Stage11StateRuntime | DamageSystem | CANONICAL FOR FROZEN STATES | Stage13 must not generalize state IDs into DamageSystem |
| Damage aftermath fact | DamageAftermathSystem / DamageAftermathPort | DamageInstanceCoordinator | CANONICAL | opportunity consumers observe committed fact |
| Recovery settlement | RecoverySystem | TroopSystem | CANONICAL | second CEIL/healing block/capacity order preserved |\n| Ordinary treatment nominal formula | TreatmentFormulaSystem | RecoveryOpportunitySystem / RecoveryPotencyContext | CANONICAL FOR STAGE13-B3 CORE | Rate(F(N)+Attr), same-side algebraic pools, cross-side multiplication, independent red pool, CEIL; persistent inputs are application-time snapshots |
| Attacker damage-derived recovery basis | Stage11AttackerRecoverySystem | Damage aftermath/partition facts | CANONICAL FOR FROZEN STATES | generic work must not duplicate lifesteal math |
| Recovery opportunity admission | RecoveryOpportunitySystem | TriggerSystem / RuleHookSystem | CANONICAL FOR CURRENT FAMILIES | Stage13 may generalize descriptor, not settlement |
| Effect dispatch | EffectExecutor | domain owners | CANONICAL | executor routes; it does not own domain math |
| Round/action-start rule intent batching | TriggerSystem + RuleHookSystem | ExecutionRightSystem | CANONICAL FOR CURRENT HOOKS | broaden typed opportunity model, not EventBus authority |
| Rule-intent execution permission | ExecutionRightSystem / ExecutionRightSupport | CurrentActor/Provider/Target/Equipment/State policies | CANONICAL | extend dimensions only when required |
| Event publication | EventBus | production owners publish after commit | CANONICAL FACT CHANNEL | never admission/permission authority |
| Operation IDs / damage lineage | OperationIdAllocator / OperationLineage | domain coordinators | CANONICAL FOR CURRENT IDS | minimal extension for generic pending work |
| Attribute final read | AttributeSystem | state modifier provider / equipment contributions | CANONICAL BUT PARTIAL | Stage13 extends source/contribution model here |
| Replay result equality | no single canonical owner yet | RandomSystem + domain IDs + events/tests | GAP | Stage13-F must establish audit contract, not gameplay god object |

## 3. Shadow-owner audit

The Stage13-A scan found no reason to create alternative owners for:

- StateRegistry / StateLifecycleSystem;
- ProviderValidityPolicy;
- SkillPermissionPolicy;
- SkillTargetPolicy;
- EquipmentEffectivenessPolicy;
- DependencyEvaluationSupport;
- DamageSystem / DamageInstanceCoordinator / DamageResolutionSystem;
- RecoverySystem;
- TargetSystem / TargetResolutionSystem;
- RandomSystem;
- BattleFinalizationCoordinator.

Stage13 implementation must prefer REUSE -> EXTEND -> COMPOSE. NEW OWNER is reserved for a real unowned truth such as generic pending work or generic usage/frequency, and must remain single-purpose.

## 4. Known owner gaps

| Gap | Why existing owner is insufficient | Do not assign to |
|---|---|---|
| Generic gameplay opportunity registry / typed windows | RuleHook has only round/action-start; EventBus is facts-only | EventBus |
| Generic pending delayed/repeated work | State lifecycle owns StateInstance only | StateLifecycleSystem as universal scheduler |
| Generic usage/frequency budget | ActionProgressTracker is natural-action bookkeeping | SkillRuntime ad hoc counters |
| Generic work identity beyond current IDs | OperationLineage is damage/action-centric | one universal untyped UUID registry |
| Whole-battle replay trace | current tests observe pieces, not one replay contract | EventBus as gameplay authority |
| Attribute contribution source/stacking model | AttributeModifierProvider is opaque and equipment path is additive-only | individual skills writing UnitRuntime fields |

## 5. Owner freeze barrier

This matrix is inventory authority only. It does not freeze new owners. Any Stage13 owner addition or responsibility transfer requires:

1. architecture design;
2. independent architecture audit;
3. discriminating tests;
4. regression;
5. explicit freeze record.

Existing Stage1-12 canonical owners remain frozen unless an authority-driven reopen is explicitly declared.
