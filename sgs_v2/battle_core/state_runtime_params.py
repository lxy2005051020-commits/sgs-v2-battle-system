from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StateRuntimeParams:
    """状态运行参数的类型安全基类。

    Stage 5 只冻结参数合同，不提前定义全部真实状态参数语义。
    未来具体参数类型应继续使用 frozen dataclass 子类。
    """


@dataclass(frozen=True, slots=True)
class EmptyStateRuntimeParams(StateRuntimeParams):
    """不需要额外运行参数的状态使用的默认参数。"""


def validate_state_runtime_params(params: StateRuntimeParams) -> None:
    """保证正式状态参数是不可变 dataclass，而不是任意行为对象。"""
    if not isinstance(params, StateRuntimeParams):
        raise TypeError("runtime_params must be a StateRuntimeParams instance")
    if not is_dataclass(params):
        raise TypeError("runtime_params must be a dataclass instance")

    dataclass_params = getattr(type(params), "__dataclass_params__", None)
    if dataclass_params is None or not dataclass_params.frozen:
        raise TypeError("runtime_params dataclass must be frozen")


def state_runtime_params_event_payload(
    params: StateRuntimeParams,
) -> tuple[str, dict[str, Any]]:
    """转换为 EventBus 审计表示；运行时合同本身仍保持强类型。"""
    validate_state_runtime_params(params)
    return type(params).__name__, asdict(params)
