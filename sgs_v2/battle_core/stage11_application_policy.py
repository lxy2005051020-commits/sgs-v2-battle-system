from __future__ import annotations

from .official_state_catalog import OfficialStateId
from .state_runtime_params import EmptyStateRuntimeParams, StateRuntimeParams


_NONSTACKING = frozenset({
    OfficialStateId.BARRIER.value,
    OfficialStateId.FIRST_STRIKE.value,
    OfficialStateId.AMBUSH.value,
    OfficialStateId.SURE_HIT.value,
    OfficialStateId.DEFENSE_PIERCE.value,
    OfficialStateId.DISARM.value,
    OfficialStateId.WEAKNESS.value,
    OfficialStateId.HEALING_BAN.value,
    OfficialStateId.STUN.value,
})

_MUTABLE = frozenset({
    OfficialStateId.EVASION.value,
    OfficialStateId.BARRIER.value,
    OfficialStateId.FIRST_STRIKE.value,
    OfficialStateId.AMBUSH.value,
    OfficialStateId.SURE_HIT.value,
    OfficialStateId.DEFENSE_PIERCE.value,
    OfficialStateId.WEAPON_LIFESTEAL.value,
    OfficialStateId.STRATEGY_LIFESTEAL.value,
    OfficialStateId.VIGILANCE.value,
    OfficialStateId.DISARM.value,
    OfficialStateId.WEAKNESS.value,
    OfficialStateId.HEALING_BAN.value,
    OfficialStateId.STUN.value,
    OfficialStateId.CRITICAL.value,
    OfficialStateId.STRATEGY_CRITICAL.value,
    OfficialStateId.DAMAGE_REDUCTION_PIERCE.value,
})


def normalize_legacy_empty_params(
    state_id: str,
    expected_type: type[StateRuntimeParams],
    params: StateRuntimeParams,
) -> StateRuntimeParams:
    """Compatibility ingress for pre-Stage11 effects that carried Empty params.

    The state definition remains typed. Legacy callers that did not yet have a
    parameter payload receive the typed class' frozen default values.
    """
    if (
        state_id in _MUTABLE
        and isinstance(params, EmptyStateRuntimeParams)
        and expected_type is not EmptyStateRuntimeParams
    ):
        return expected_type()
    return params


def enforce_application_conflict(
    context,
    *,
    state_id: str,
    owner_id: str,
    actual_runtime_params: StateRuntimeParams,
) -> None:
    if state_id not in _NONSTACKING:
        return
    existing = context.states.find(owner_id=owner_id, state_id=state_id)
    if not existing:
        return
    if state_id == OfficialStateId.DEFENSE_PIERCE.value:
        incoming_strength = float(getattr(actual_runtime_params, "strength", 1.0))
        existing_strength = max(
            float(getattr(item.runtime_params, "strength", 1.0))
            for item in existing
        )
        if incoming_strength > existing_strength:
            raise ValueError(
                "690093 stronger replacement is an unresolved research boundary"
            )
    raise ValueError(
        f"Stage11 state '{state_id}' already exists on unit '{owner_id}'; "
        "incoming equal/equivalent application is rejected without refresh"
    )


def runtime_params_mutation_authorized(state_id: str) -> bool:
    return state_id in _MUTABLE
