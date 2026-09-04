from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    DeferredEffectResult,
    EffectExecutionStatus,
    RecoverEffect,
    StateDefinition,
    StateRuntimeParams,
)


class UndeclaredParams(StateRuntimeParams):
    pass


def test_state_definition_rejects_non_dataclass_runtime_param_schema() -> None:
    with pytest.raises(TypeError, match="explicit dataclass"):
        StateDefinition(
            state_id="invalid-schema",
            name="非法参数结构",
            runtime_params_type=UndeclaredParams,
        )


def test_effect_result_status_cannot_be_overridden_by_caller() -> None:
    effect = RecoverEffect(
        source_id=None,
        target_id="b1",
        amount=100,
    )

    with pytest.raises(TypeError):
        DeferredEffectResult(
            effect=effect,
            reason="RECOVERY_SYSTEM_NOT_AVAILABLE",
            status=EffectExecutionStatus.RESOLVED,  # type: ignore[call-arg]
        )
