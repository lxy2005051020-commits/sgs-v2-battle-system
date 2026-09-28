from __future__ import annotations

from dataclasses import asdict, dataclass
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


def validate_state_runtime_params_type(
    params_type: type[StateRuntimeParams],
) -> None:
    """要求参数 schema 本身就是显式声明的 frozen dataclass。"""
    if not isinstance(params_type, type) or not issubclass(
        params_type, StateRuntimeParams
    ):
        raise TypeError("runtime_params_type must be a StateRuntimeParams subclass")

    # 使用类自身 __dict__，避免未加 @dataclass 的普通子类仅靠继承
    # __dataclass_params__ 冒充正式参数 schema。
    dataclass_params = params_type.__dict__.get("__dataclass_params__")
    if dataclass_params is None:
        raise TypeError("runtime_params_type must be an explicit dataclass")
    if not dataclass_params.frozen:
        raise TypeError("runtime_params_type dataclass must be frozen")


def validate_state_runtime_params(params: StateRuntimeParams) -> None:
    """保证正式状态参数实例符合不可变强类型合同。"""
    if not isinstance(params, StateRuntimeParams):
        raise TypeError("runtime_params must be a StateRuntimeParams instance")
    validate_state_runtime_params_type(type(params))


def state_runtime_params_event_payload(
    params: StateRuntimeParams,
) -> tuple[str, dict[str, Any]]:
    """转换为 EventBus 审计表示；运行时合同本身仍保持强类型。"""
    validate_state_runtime_params(params)
    return type(params).__name__, asdict(params)
