from __future__ import annotations

from .context import BattleContext
from .events import EventType
from .execution_right_system import ActionScope, ComboActionGrant, ComboGrantState
from .normal_attack_system import NormalAttackResult, NormalAttackSystem
from .official_state_catalog import OfficialStateId
from .stage9_state_runtime import Stage9StateRuntime
from .state_lifecycle_system import StateLifecycleSystem
from .unit import UnitRuntime


class ActionSystem:
    """处理一个单位的一次完整行动。"""

    def __init__(
        self,
        normal_attack_system: NormalAttackSystem,
        stage9_state_runtime: Stage9StateRuntime | None = None,
        state_lifecycle_system: StateLifecycleSystem | None = None,
    ) -> None:
        self._normal_attack = normal_attack_system
        self._stage9_state_runtime = stage9_state_runtime
        self._state_lifecycle_system = state_lifecycle_system

    def execute(
        self,
        context: BattleContext,
        actor: UnitRuntime,
        action_scope: ActionScope | None = None,
    ) -> NormalAttackResult | None:
        if not actor.is_alive:
            return None

        # Phase 9.6 / P96-B02: COMBO holder maintenance runs at ACTION_START before grant creation.
        # This decrements remaining_actions for finite buffs. STUN does NOT freeze Combo duration.
        if self._state_lifecycle_system is not None:
            self._state_lifecycle_system.process_combo_action_start(
                context=context,
                actor_id=actor.unit_id,
            )

        # Grant creation for active ActionScope
        if action_scope is not None and self._stage9_state_runtime is not None:
            op_combo = self._stage9_state_runtime.get_operational_combo(
                context=context,
                unit_id=actor.unit_id,
            )
            if op_combo is not None:
                source_skill_id = op_combo.source_skill_id
                if not source_skill_id or not isinstance(source_skill_id, str):
                    raise ValueError(
                        f"Operational COMBO instance {op_combo.instance_id} has invalid "
                        f"source_skill_id: {source_skill_id!r}"
                    )
                grant = ComboActionGrant(
                    action_id=action_scope.action_id,
                    granting_instance_id=op_combo.instance_id,
                    source_unit=op_combo.source_id or actor.unit_id,
                    source_skill=source_skill_id,
                    state=ComboGrantState.VALID,
                )
                action_scope.combo_grant = grant

        stun_state_id = OfficialStateId.STUN.value
        if context.states.has(owner_id=actor.unit_id, state_id=stun_state_id):
            context.event_bus.publish(
                event_type=EventType.ACTION_BLOCKED,
                phase=context.current_phase,
                round_no=context.current_round,
                actor_id=actor.unit_id,
                payload={
                    "action_type": "ALL",
                    "reason_state_id": stun_state_id,
                },
            )
            return None

        return self._normal_attack.execute(
            context=context,
            actor=actor,
            action_scope=action_scope,
        )

