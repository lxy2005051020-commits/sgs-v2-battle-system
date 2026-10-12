"""State-backed individual damage pools with equal team generation allocation.

Amounts live in a battle-scoped ledger keyed by state application generation.
No event callbacks or troop mutation: the pool intercepts the existing troop
settlement call only after its canonical settlement permit has been consumed.
"""
from contextvars import ContextVar
from dataclasses import dataclass, replace
from fractions import Fraction
from .context import BattleContext
from .state_instance import StateInstance
from .state_effectiveness import StateEffectivenessPolicy
from .damage_system import DamageResult

from .damage_resolution_system import DamageResolutionSystem
from .enums import DamageType
from .events import EventType
from .numeric_validation import validate_probability, validate_nonnegative_finite
from .rule_hooks import RoundStartHook
from .state_runtime_params import StateRuntimeParams
from .troop_system import TroopSystem
from .action_start_recovery_damage import AccumulatedRecoveryRuleHookSystem

TEMPORARY_DAMAGE_POOL_STATE_ID = "runtime_temporary_damage_pool"
POOL_LEDGER_KEY = "temporary_damage_pool_ledger"


@dataclass(frozen=True, slots=True)
class TemporaryDamagePoolParams(StateRuntimeParams):
    absorb_ratio: float
    generation_ratio: float = 1.0
    decay_ratio: float = .10
    generated_damage_type: DamageType = DamageType.WEAPON
    absorbed_damage_type: DamageType = DamageType.STRATEGY

    def __post_init__(self):
        for key in ("absorb_ratio", "decay_ratio"):
            object.__setattr__(self, key, validate_probability(getattr(self, key), key))
        object.__setattr__(self, "generation_ratio", validate_nonnegative_finite(self.generation_ratio, "generation_ratio"))
        for key in ("generated_damage_type", "absorbed_damage_type"):
            if not isinstance(getattr(self, key), DamageType):
                raise TypeError(f"{key} must be DamageType")


@dataclass(frozen=True, slots=True)
class TemporaryDamagePoolBalance:
    amount: int = 0
    updated_round: int = 0


def pool_key(state: StateInstance) -> str:
    return f"{state.instance_id}:{state.current_generation_id}"


def pool_balance(context: BattleContext, state: StateInstance) -> TemporaryDamagePoolBalance:
    return context.metadata.get(POOL_LEDGER_KEY, {}).get(pool_key(state), TemporaryDamagePoolBalance())


def _save(context, state, balance):
    context.metadata.setdefault(POOL_LEDGER_KEY, {})[pool_key(state)] = balance


class TemporaryDamagePoolSupport:
    def __init__(self, policy: StateEffectivenessPolicy) -> None:
        self.policy = policy

    def round_start(self, context: BattleContext, hook: RoundStartHook) -> None:
        if context.ended:
            return
        for owner in context.units.values():
            effective = {s.instance_id for s in self.policy.effective_instances(
                context, owner.unit_id, TEMPORARY_DAMAGE_POOL_STATE_ID)}
            for state in context.states.find(owner_id=owner.unit_id, state_id=TEMPORARY_DAMAGE_POOL_STATE_ID):
                if not owner.is_alive:
                    continue
                params = state.runtime_params
                old = pool_balance(context, state)
                if old.updated_round >= hook.round_no:
                    continue
                # Suppression pauses generation/use, but cannot pause elapsed decay.
                remaining = int(old.amount * (1 - Fraction(str(params.decay_ratio))))
                total = 0
                sequences = []
                if state.instance_id in effective:
                    for event in context.event_bus.history:
                        source = context.units.get(event.actor_id)
                        if (event.event_type is EventType.DAMAGE_DEALT
                                and event.round_no == hook.round_no - 1
                                and source is not None and source.team_id == owner.team_id
                                and event.payload["damage_type"] == params.generated_damage_type.value):
                            total += event.payload["damage"]
                            sequences.append(event.sequence)
                # Each living teammate receives its own ceil(total / alive_count).
                # Round the final quotient once, not total before division.
                living_count = sum(u.is_alive and u.team_id == owner.team_id
                    for u in context.units.values())
                share = total * Fraction(str(params.generation_ratio)) / living_count
                generated = -(-share.numerator // share.denominator)
                _save(context, state, TemporaryDamagePoolBalance(remaining + generated, hook.round_no))
                context.event_bus.publish(event_type=EventType.TEMPORARY_POOL_UPDATED,
                    phase=context.current_phase, round_no=context.current_round,
                    actor_id=state.source_id, target_id=owner.unit_id,
                    payload={"source_skill_id": state.source_skill_id, "state_instance_id": state.instance_id,
                        "operation": "ROUND_UPDATE", "pool_before": old.amount,
                        "decayed": old.amount - remaining, "generated": generated,
                        "pool_after": remaining + generated, "damage_event_sequences": sequences,
                        "team_damage_total": total, "living_teammate_count": living_count,
                        "generation_rounding": "CEIL_EQUAL_SHARE"})

    def absorb(self, context: BattleContext, damage: DamageResult, assigned: int) -> int:
        target = context.get_unit(damage.target_id)
        if not target.is_alive or assigned == 0:
            return 0
        states = self.policy.effective_instances(context, target.unit_id, TEMPORARY_DAMAGE_POOL_STATE_ID)
        absorbed = 0
        for state in states:
            params = state.runtime_params
            if damage.damage_type is not params.absorbed_damage_type:
                continue
            old = pool_balance(context, state)
            amount = min(old.amount, int((assigned - absorbed) * Fraction(str(params.absorb_ratio))))
            if amount == 0:
                continue
            _save(context, state, replace(old, amount=old.amount - amount))
            absorbed += amount
            context.event_bus.publish(event_type=EventType.TEMPORARY_POOL_UPDATED,
                phase=context.current_phase, round_no=context.current_round,
                actor_id=state.source_id, target_id=target.unit_id,
                payload={"source_skill_id": state.source_skill_id, "state_instance_id": state.instance_id,
                    "operation": "ABSORB", "pool_before": old.amount, "absorbed": amount,
                    "pool_after": old.amount - amount, "damage_source_id": damage.source_id,
                    "assigned_target_damage": assigned})
        return absorbed


class _PoolTroopSettlement(TroopSystem):
    """Delegate every troop write; only explicit damage settlements opt in."""
    def __init__(self, base, support):
        self.base, self.support = base, support
        self.scope = ContextVar("temporary_pool_settlement", default=None)

    def apply_damage(self, target, requested_damage):
        scope = self.scope.get()
        if scope is None:
            return self.base.apply_damage(target, requested_damage)
        context, damage = scope
        absorbed = self.support.absorb(context, damage, requested_damage)
        change = self.base.apply_damage(target, requested_damage - absorbed)
        return replace(change, requested_change=requested_damage)


class PoolDamageResolutionSystem(DamageResolutionSystem):
    def __init__(self, damage_system, troop_system, *, pool_support, **kwargs):
        self.pool_troops = _PoolTroopSettlement(troop_system, pool_support)
        super().__init__(damage_system, self.pool_troops, **kwargs)

    def settle(self, context, request, permit):
        token = self.pool_troops.scope.set((context, request.damage_result))
        try:
            return super().settle(context, request, permit)
        finally:
            self.pool_troops.scope.reset(token)


    def _settle_legacy(self, context, request):
        token = self.pool_troops.scope.set((context, request.damage_result))
        try:
            return super()._settle_legacy(context, request)
        finally:
            self.pool_troops.scope.reset(token)


class PoolRuleHookSystem(AccumulatedRecoveryRuleHookSystem):
    def __init__(self, trigger_system, effect_executor, support, *, pool_support):
        super().__init__(trigger_system, effect_executor, support)
        self.pool_support = pool_support

    def process(self, context, hook):
        if isinstance(hook, RoundStartHook):
            if hook.round_no != context.current_round:
                raise ValueError("hook.round_no must match context.current_round")
            self.pool_support.round_start(context, hook)
        return super().process(context, hook)

