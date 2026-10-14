"""Transfers compose canonical owners under a user-approved non-scaling model."""
from dataclasses import replace, fields
from typing import TYPE_CHECKING
from .context import BattleContext
from .state_instance import StateInstance
from .provider_identity import SkillProviderRef
from .state_runtime_params import StateRuntimeParams
from .damage_rate_modifier import DAMAGE_RATE_STATE_ID, DamageRateParams, RoundDamageRateParams
from .feng_shi_zhen import FENG_SHI_ZHEN_MODIFIER_STATE_ID, FengShiZhenModifierParams
from .probabilistic_target_priority import TARGET_PRIORITY_STATE_ID, TargetPriorityParams
from .outgoing_damage_reduction import OUTGOING_DAMAGE_REDUCTION_STATE_ID, OutgoingDamageReductionParams
from .dependency_evaluation import StateNode, ProviderNode
from .state_effectiveness import StateEffectivenessContribution, InactivityCause, LocalRuleCauseRef
from .provider_validity import ProviderDependency
from .enums import BattlePhase
from .official_state_catalog import OFFICIAL_STATE_CATALOG, OfficialStateCategory
from .state_application import StateCandidate, StateApplicationResult
from .state_lifetime import StateLifetimeSpec
from .state_modifiers import (ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams,
    ACTIVATION_RATE_BONUS_STATE_ID, ActivationRateBonusParams,
    INCOMING_DAMAGE_REDUCTION_STATE_ID, IncomingDamageReductionParams)
from .state_removal import RemovalDecision, RemovalDecisionStatus, RemovalOperation
from .stage11_state_params import Stage11TimedFlagParams, DisarmStateParams, StunStateParams
from .stage9_state_params import TauntStateParams
from .stage10_state_params import ContinuousDamageStateParams, PersistentSourceSkillGate
from .state_generation import PersistentLifecycleWindow
from .numeric_validation import validate_probability
from .transferred_potency import TransferredFrozenDamageBasis
if TYPE_CHECKING:
    from .battle_systems import BattleSystems

NEGATIVE_STATE_IDS = frozenset(e.state_id.value for e in OFFICIAL_STATE_CATALOG
    if e.category is OfficialStateCategory.CONTROL) | frozenset((
        'burn', 'flood', 'poison', 'rout', 'sandstorm', 'rebellion', 'ambush', 'chain_link', 'intimidation'))


def is_negative_state(state: StateInstance, round_no: int | None = None) -> bool:
    p = state.runtime_params
    if state.state_id == DAMAGE_RATE_STATE_ID and isinstance(p, RoundDamageRateParams):
        outgoing, incoming = p.rates_at(state.applied_round if round_no is None else round_no)
        return outgoing < 0 or incoming > 0
    return (state.state_id in NEGATIVE_STATE_IDS
        or (state.state_id == ATTRIBUTE_BONUS_STATE_ID and isinstance(p, AttributeBonusParams) and p.amount < 0)
        or (state.state_id in (DAMAGE_RATE_STATE_ID, FENG_SHI_ZHEN_MODIFIER_STATE_ID)
            and isinstance(p, (DamageRateParams, FengShiZhenModifierParams))
            and (p.outgoing_rate < 0 or p.incoming_rate > 0))
        or (state.state_id == ACTIVATION_RATE_BONUS_STATE_ID and isinstance(p, ActivationRateBonusParams) and p.amount < 0)
        or (state.state_id == OUTGOING_DAMAGE_REDUCTION_STATE_ID
            and isinstance(p, OutgoingDamageReductionParams) and p.rate > 0))


def is_incoming_reduction(state: StateInstance, round_no: int | None = None) -> bool:
    p = state.runtime_params
    if state.state_id == DAMAGE_RATE_STATE_ID and isinstance(p, RoundDamageRateParams):
        return p.rates_at(state.applied_round if round_no is None else round_no)[1] < 0
    return ((state.state_id == INCOMING_DAMAGE_REDUCTION_STATE_ID
             and isinstance(p, IncomingDamageReductionParams) and p.rate > 0)
        or (state.state_id in (DAMAGE_RATE_STATE_ID, FENG_SHI_ZHEN_MODIFIER_STATE_ID)
            and isinstance(p, (DamageRateParams, FengShiZhenModifierParams)) and p.incoming_rate < 0)
        or (state.state_id == TARGET_PRIORITY_STATE_ID and isinstance(p,TargetPriorityParams)
            and bool(p.reduction_base or p.reduction_slope)))


def transfer_removal_adapter(context, operation, state):
    if (operation is RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE
            and state.instance_id in context.metadata.get('_state_transfer_removal_permits', ())):
        return RemovalDecision(RemovalDecisionStatus.ALLOW, operation, 'RUNTIME_TRANSFER_SOURCE_REMOVE')
    return None


def transfer_effectiveness_adapter(context, state, session):
    ref = context.metadata.get('state_transfer_providers', {}).get(state.instance_id)
    if ref is None:
        return StateEffectivenessContribution()
    runtime = context.skill_runtimes.get(ref.owner_id, ref.skill_slot)
    unit = context.units.get(ref.owner_id)
    if runtime is None or not runtime.enabled or runtime.definition.skill_id != ref.skill_id or unit is None or not unit.is_alive:
        return StateEffectivenessContribution(inactivity_causes=(InactivityCause(
            'TRANSFER_PROVIDER_UNAVAILABLE', LocalRuleCauseRef(state.instance_id)),))
    return StateEffectivenessContribution()


class StateTransferSupport:
    def __init__(self, systems: 'BattleSystems') -> None:
        self._systems = systems

    @staticmethod
    def split_params(state: StateInstance, *, reduction: bool, context: BattleContext | None = None,
                     systems: 'BattleSystems | None' = None) -> tuple[StateRuntimeParams, StateRuntimeParams | None]:
        p = state.runtime_params
        if isinstance(p, IncomingDamageReductionParams) and reduction:
            return p, None
        if isinstance(p, AttributeBonusParams) and not reduction and p.amount < 0:
            return AttributeBonusParams(p.attribute, p.amount), None
        if isinstance(p, ActivationRateBonusParams) and not reduction and p.amount < 0:
            return ActivationRateBonusParams(p.skill_type, p.amount, skill_slot=p.skill_slot), None
        if isinstance(p, OutgoingDamageReductionParams) and not reduction:
            return p, None
        if isinstance(p, TargetPriorityParams) and reduction:
            if context is None or systems is None:
                raise ValueError('live reduction transfer requires context and attribute owner')
            attribute = getattr(systems.attribute_system, 'get_'+p.reduction_attribute)(context, context.get_unit(state.owner_id))
            rate = validate_probability(p.reduction_base+p.reduction_slope*(attribute-p.reduction_reference), 'transfer reduction snapshot')
            return DamageRateParams(incoming_rate=-rate), replace(p, reduction_base=0., reduction_slope=0.)
        if isinstance(p, (DamageRateParams, FengShiZhenModifierParams)):
            outgoing, incoming = (p.rates_at(context.current_round if context is not None else state.applied_round)
                                 if isinstance(p, RoundDamageRateParams) else (p.outgoing_rate, p.incoming_rate))
            moved_in = incoming if (incoming < 0 if reduction else incoming > 0) else 0.
            moved_out = outgoing if not reduction and outgoing < 0 else 0.
            moved = DamageRateParams(moved_out, moved_in)
            if isinstance(p, RoundDamageRateParams):
                remaining = replace(p,
                    opening_rates=tuple((0. if moved_out and a < 0 else a,
                        0. if moved_in and b*moved_in > 0 else b) for a,b in p.opening_rates),
                    incoming_step=0. if moved_in > 0 else p.incoming_step)
                has_remainder = any(a or b for a,b in remaining.opening_rates) or remaining.outgoing_step or remaining.incoming_step
            else:
                remaining = replace(p, outgoing_rate=outgoing-moved_out, incoming_rate=incoming-moved_in)
                has_remainder = remaining.outgoing_rate or remaining.incoming_rate
            return moved, remaining if has_remainder else None
        if state.state_id in NEGATIVE_STATE_IDS:
            return p, None
        raise ValueError(f'state has no transferable negative/reduction params: {state.state_id}')

    @staticmethod
    def _new_state_id(state: StateInstance, params: StateRuntimeParams) -> str:
        return DAMAGE_RATE_STATE_ID if state.state_id in (FENG_SHI_ZHEN_MODIFIER_STATE_ID, TARGET_PRIORITY_STATE_ID) else state.state_id

    def _prepare(self, context: BattleContext, state: StateInstance, params: StateRuntimeParams,
                 provider: SkillProviderRef, identities: dict[str,str]) -> StateRuntimeParams:
        updates = {f.name: identities[getattr(params,f.name)] for f in fields(params)
            if f.name in ('parent_state_instance_id', 'prerequisite_state_id')
            and getattr(params,f.name) in identities}
        if isinstance(params, TauntStateParams):
            updates.update(taunt_target_id=provider.owner_id, suppressors=frozenset())
        if isinstance(params, (Stage11TimedFlagParams, DisarmStateParams)):
            updates.update(remaining_action_starts=None, source_dependent=False)
        elif isinstance(params, StunStateParams):
            updates.update(source_dependent=False)
        if isinstance(params, ContinuousDamageStateParams):
            if params.frozen_damage_basis is None:
                raise ValueError('continuous transfer requires an application-frozen potency')
            original_basis=params.frozen_damage_basis
            basis = TransferredFrozenDamageBasis(**{f.name:getattr(original_basis,f.name)
                for f in fields(original_basis) if f.name not in (
                    'source_unit_id','source_skill_id','source_skill_slot','source_state_id','historical_source')},
                source_unit_id=provider.owner_id,
                source_skill_id=provider.skill_id, source_skill_slot=provider.skill_slot,
                source_state_id=state.state_id, historical_source=None)
            updates.update(frozen_damage_basis=basis, application_generation_id=None,
                lifecycle_window=PersistentLifecycleWindow(context.current_phase, context.current_round,
                    context.current_round, context.current_round),
                source_skill_gate=PersistentSourceSkillGate.always_active())
        return replace(params, **updates) if updates else params

    def _candidate(self, context, state_id, owner_id, params, provider, provenance):
        return StateCandidate(state_id, owner_id, params, source_id=provider.owner_id,
            source_skill_id=provider.skill_id, source_skill_slot=provider.skill_slot,
            lifetime_spec=StateLifetimeSpec.explicit_phase_expiry(expires_round=context.current_round,
                expires_phase=BattlePhase.ROUND_END.value),
            provider_dependencies=(ProviderDependency(provider,'TRANSFER_PROVIDER'),), application_provenance=provenance)

    def _apply(self, context: BattleContext, candidate: StateCandidate) -> StateApplicationResult:
        return self._systems.state_application_coordinator.apply_candidate(context,candidate)

    def _remove(self, context, state):
        if not context.states.has_instance(state.instance_id):
            return
        context.metadata.setdefault('_state_transfer_removal_permits',set()).add(state.instance_id)
        result = self._systems.state_removal_coordinator.remove(context,
            operation=RemovalOperation.SCRIPTED_GAMEPLAY_REMOVE,instance_id=state.instance_id)
        if result.removed_instance is None:
            raise RuntimeError('approved transfer removal did not commit')

    def _remainder(self, context, state, params):
        s = self._systems
        dependencies = s.dependency_evaluation_support.prerequisites(StateNode(state.instance_id))
        result = s.state_application_coordinator.apply_candidate(context,StateCandidate(state.state_id,state.owner_id,params,
            source_id=state.source_id,source_skill_id=state.source_skill_id,source_skill_slot=state.source_skill_slot,
            lifetime_spec=state.lifetime_spec or (StateLifetimeSpec.explicit_phase_expiry(
                expires_round=state.expires_round,expires_phase=state.expires_phase) if state.expires_round else None),
            application_provenance='TRANSFER_REMAINDER:'+state.instance_id))
        if not result.committed:
            raise RuntimeError('transfer remainder did not commit')
        s.dependency_evaluation_support.replace_dependencies(StateNode(result.instance.instance_id),dependencies)

    def _children(self, context, root):
        s = self._systems
        states = {root.instance_id:root}
        pending = [root.instance_id]
        while pending:
            identity = pending.pop(0)
            direct = [context.states.get(n.instance_id) for n in s.dependency_evaluation_support.dependents(StateNode(identity))
                if isinstance(n,StateNode) and context.states.has_instance(n.instance_id)]
            direct += list(s.state_lifecycle_system.associated_states(context,identity))
            direct += [candidate for candidate in context.states.find()
                if getattr(candidate.runtime_params,'prerequisite_state_id',None)==identity
                or getattr(candidate.runtime_params,'parent_state_instance_id',None)==identity]
            for state in sorted(direct,key=lambda st:st.instance_id):
                if state.instance_id not in states:
                    states[state.instance_id]=state
                    pending.append(state.instance_id)
        remaining={k:v for k,v in states.items() if k!=root.instance_id}
        ordered=[]
        emitted={root.instance_id}
        while remaining:
            ready=[]
            for identity,state in remaining.items():
                parents={n.instance_id for n in s.dependency_evaluation_support.prerequisites(StateNode(identity))
                    if isinstance(n,StateNode) and n.instance_id in states}
                anchor=getattr(state.runtime_params,'parent_state_instance_id',None)
                if anchor in states:
                    parents.add(anchor)
                anchor=getattr(state.runtime_params,'prerequisite_state_id',None)
                if anchor in states:
                    parents.add(anchor)
                if parents <= emitted:
                    ready.append(identity)
            if not ready:
                raise ValueError('cyclic associated-state transfer graph')
            for identity in sorted(ready):
                ordered.append(remaining.pop(identity))
                emitted.add(identity)
        return ordered

    @staticmethod
    def _dimension(params):
        if isinstance(params, ActivationRateBonusParams):
            return (params.skill_type, params.skill_slot)
        return getattr(params,'attribute',getattr(params,'damage_type',None))

    @classmethod
    def _matches(cls, resident, incoming):
        if cls._dimension(resident)!=cls._dimension(incoming):
            return False
        if ((isinstance(resident,AttributeBonusParams) and isinstance(incoming,AttributeBonusParams))
                or (isinstance(resident,ActivationRateBonusParams) and isinstance(incoming,ActivationRateBonusParams))):
            return resident.amount*incoming.amount > 0
        if isinstance(resident,DamageRateParams) and isinstance(incoming,DamageRateParams):
            return resident.outgoing_rate*incoming.outgoing_rate > 0 or resident.incoming_rate*incoming.incoming_rate > 0
        return True

    def transfer(self, context: BattleContext, state: StateInstance, target_id: str,
                 provider: SkillProviderRef, *, reduction: bool = False) -> dict[str,object]:
        s = self._systems
        if context.ended or s.finalization_coordinator.is_latched_or_finalized:
            return {'status':'BATTLE_ENDED'}
        resident=context.states.get(state.instance_id) if context.states.has_instance(state.instance_id) else None
        if resident is None:
            return {'status':'SOURCE_NOT_RESIDENT'}
        if resident.current_generation_id!=state.current_generation_id:
            return {'status':'SOURCE_GENERATION_CHANGED'}
        runtime=context.skill_runtimes.get(provider.owner_id,provider.skill_slot)
        holder=context.units.get(provider.owner_id)
        if (runtime is None or not runtime.enabled or runtime.definition.skill_id!=provider.skill_id
                or holder is None or not holder.is_alive):
            return {'status':'PROVIDER_UNAVAILABLE'}
        if target_id not in context.units or not context.units[target_id].is_alive:
            return {'status':'TARGET_UNAVAILABLE'}
        if target_id==state.owner_id:
            return {'status':'NO_DISTINCT_TARGET'}
        eligible = is_incoming_reduction(state,context.current_round) if reduction else is_negative_state(state,context.current_round)
        if not eligible:
            return {'status':'NO_ELIGIBLE_DIMENSION'}
        moved,remainder = self.split_params(state,reduction=reduction,context=context,systems=s)
        children = self._children(context,state) if remainder is None else []
        snapshots = {x.instance_id:s.dependency_evaluation_support.prerequisites(StateNode(x.instance_id)) for x in (state,*children)}
        # Validate every snapshot/schema and all target admissions before mutation.
        for original,params in [(state,moved)]+[(x,x.runtime_params) for x in children]:
            prepared = self._prepare(context,original,params,provider,{})
            candidate = self._candidate(context,self._new_state_id(original,prepared),
                target_id if original.owner_id==state.owner_id else original.owner_id, prepared,provider,'TRANSFER:'+original.instance_id)
            decision = s.state_admission_policy.evaluate_candidate(context,candidate)
            if not decision.allowed:
                return {'status':'REJECTED_ADMISSION','reason':decision.reason_rule_id}
        identities={}
        overwritten=[]
        context.metadata['_state_transfer_in_progress']=context.metadata.get('_state_transfer_in_progress',0)+1
        try:
            for original,params in [(state,moved)]+[(x,x.runtime_params) for x in children]:
                prepared = self._prepare(context,original,params,provider,identities)
                owner = target_id if original.owner_id==state.owner_id else original.owner_id
                sid = self._new_state_id(original,prepared)
                prior = [x for x in context.states.find(owner_id=owner,state_id=sid)
                    if self._matches(x.runtime_params,prepared)
                    and x.instance_id not in identities.values() and x.instance_id!=original.instance_id]
                old_children = [child for x in prior for child in s.state_lifecycle_system.associated_states(context,x.instance_id)]
                result=self._apply(context,self._candidate(context,sid,owner,prepared,provider,'TRANSFER:'+original.instance_id))
                if not result.committed:
                    return {'status':result.status.value,'reason':result.reason_rule_id}
                new=result.instance
                identities[original.instance_id]=new.instance_id
                context.metadata.setdefault('state_transfer_providers',{})[new.instance_id]=provider
                for old in prior:
                    if old.instance_id==new.instance_id:
                        for child in old_children:
                            self._remove(context,child)
                        continue
                    if type(old.runtime_params) is DamageRateParams and type(prepared) is DamageRateParams:
                        rest=replace(old.runtime_params,
                            outgoing_rate=0. if prepared.outgoing_rate*old.runtime_params.outgoing_rate > 0 else old.runtime_params.outgoing_rate,
                            incoming_rate=0. if prepared.incoming_rate*old.runtime_params.incoming_rate > 0 else old.runtime_params.incoming_rate)
                        if rest.outgoing_rate or rest.incoming_rate:
                            self._remainder(context,old,rest)
                            continue
                    self._remove(context,old)
                    overwritten.append(old.instance_id)
                for node in (() if original.instance_id==state.instance_id else snapshots[original.instance_id]):
                    if isinstance(node,StateNode):
                        rebound=StateNode(identities.get(node.instance_id,node.instance_id))
                        s.dependency_evaluation_support.add_dependency(StateNode(new.instance_id),rebound)
            if remainder is not None:
                self._remainder(context,state,remainder)
            else:
                for original in reversed(children):
                    self._remove(context,original)
                self._remove(context,state)
            return {'status':'TRANSFERRED','original_instance_id':state.instance_id,
                'original_generation_id':state.current_generation_id.value,
                'original_source_id':state.source_id,'original_skill_id':state.source_skill_id,
                'original_slot':int(state.source_skill_slot) if state.source_skill_slot is not None else None,
                'source_owner_id':state.owner_id,'target_id':target_id,
                'new_instance_id':identities[state.instance_id],'state_id':state.state_id,
                'identity_rebindings':identities,'overwritten_instance_ids':overwritten,
                'model':'USER_APPROVED_TRANSFER_WITHOUT_ATTRIBUTE_SCALING'}
        finally:
            context.metadata['_state_transfer_in_progress']-=1
            context.metadata.get('_state_transfer_removal_permits',set()).clear()
