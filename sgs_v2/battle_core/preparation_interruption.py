from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from .effectiveness_transition import (
    EffectivenessTransitionCoordinator,
    ProviderValidityChanged,
    StateEffectivenessChanged,
)
from .provider_identity import SkillProviderRef


class PreparationInterruptionScope(str, Enum):
    HOLDER_ACTIVE = "HOLDER_ACTIVE"
    PROVIDER = "PROVIDER"


class PreparationInterruptionStatus(str, Enum):
    INTERRUPTED = "INTERRUPTED"
    NOT_PREPARING = "NOT_PREPARING"
    PROVIDER_NOT_MATCHED = "PROVIDER_NOT_MATCHED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class PreparationInterruptionRequest:
    scope: PreparationInterruptionScope
    holder_id: str
    cause_key: str
    provider_ref: SkillProviderRef | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scope, PreparationInterruptionScope):
            raise TypeError("scope must be a PreparationInterruptionScope")
        if not isinstance(self.holder_id, str) or not self.holder_id.strip():
            raise ValueError("holder_id cannot be empty or whitespace")
        if not isinstance(self.cause_key, str) or not self.cause_key.strip():
            raise ValueError("cause_key cannot be empty or whitespace")
        if self.scope is PreparationInterruptionScope.PROVIDER:
            if not isinstance(self.provider_ref, SkillProviderRef):
                raise TypeError("PROVIDER scope requires provider_ref")
            if self.provider_ref.owner_id != self.holder_id:
                raise ValueError("provider_ref owner must match holder_id")
        elif self.provider_ref is not None:
            raise ValueError("HOLDER_ACTIVE scope does not carry provider_ref")


@dataclass(frozen=True, slots=True)
class PreparationInterruptionResult:
    request: PreparationInterruptionRequest
    status: PreparationInterruptionStatus
    interrupted_provider_refs: tuple[SkillProviderRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, PreparationInterruptionRequest):
            raise TypeError("request must be a PreparationInterruptionRequest")
        if not isinstance(self.status, PreparationInterruptionStatus):
            raise TypeError("status must be a PreparationInterruptionStatus")
        refs = tuple(self.interrupted_provider_refs)
        if any(not isinstance(item, SkillProviderRef) for item in refs):
            raise TypeError("interrupted_provider_refs must contain SkillProviderRef values")
        if self.status is PreparationInterruptionStatus.INTERRUPTED and not refs:
            raise ValueError("INTERRUPTED result must name at least one provider")
        if self.status is not PreparationInterruptionStatus.INTERRUPTED and refs:
            raise ValueError("non-INTERRUPTED result cannot carry interrupted providers")
        object.__setattr__(self, "interrupted_provider_refs", refs)


class PreparationInterruptionPort(Protocol):
    def interrupt(
        self,
        context: object,
        request: PreparationInterruptionRequest,
    ) -> PreparationInterruptionResult:
        ...


class NoopPreparationInterruptionPort:
    """NON-COMPLETE placeholder valid only while production has no PREPARING work."""

    __slots__ = ()

    def interrupt(
        self,
        context: object,
        request: PreparationInterruptionRequest,
    ) -> PreparationInterruptionResult:
        if not isinstance(request, PreparationInterruptionRequest):
            raise TypeError("request must be a PreparationInterruptionRequest")
        return PreparationInterruptionResult(
            request=request,
            status=PreparationInterruptionStatus.NOT_PREPARING,
        )


StatePreparationRequestFactory = Callable[
    [object, StateEffectivenessChanged],
    PreparationInterruptionRequest | None,
]
ProviderPreparationRequestFactory = Callable[
    [object, ProviderValidityChanged],
    PreparationInterruptionRequest | None,
]


class PreparationInterruptionTransitionAdapter:
    """Generic synchronous bridge from canonical transitions to preparation commands."""

    __slots__ = ("_port", "_state_factory", "_provider_factory")

    def __init__(
        self,
        port: PreparationInterruptionPort,
        *,
        state_request_factory: StatePreparationRequestFactory | None = None,
        provider_request_factory: ProviderPreparationRequestFactory | None = None,
    ) -> None:
        if not hasattr(port, "interrupt"):
            raise TypeError("port must implement interrupt")
        if state_request_factory is not None and not callable(state_request_factory):
            raise TypeError("state_request_factory must be callable")
        if provider_request_factory is not None and not callable(provider_request_factory):
            raise TypeError("provider_request_factory must be callable")
        self._port = port
        self._state_factory = state_request_factory
        self._provider_factory = provider_request_factory

    def bind(self, coordinator: EffectivenessTransitionCoordinator) -> None:
        if not isinstance(coordinator, EffectivenessTransitionCoordinator):
            raise TypeError("coordinator must be EffectivenessTransitionCoordinator")
        if self._state_factory is not None:
            coordinator.register_state_port(self.on_state_transition)
        if self._provider_factory is not None:
            coordinator.register_provider_port(self.on_provider_transition)

    def on_state_transition(
        self,
        context: object,
        transition: StateEffectivenessChanged,
    ) -> None:
        if self._state_factory is None:
            return
        request = self._state_factory(context, transition)
        if request is not None:
            self._port.interrupt(context, request)

    def on_provider_transition(
        self,
        context: object,
        transition: ProviderValidityChanged,
    ) -> None:
        if self._provider_factory is None:
            return
        request = self._provider_factory(context, transition)
        if request is not None:
            self._port.interrupt(context, request)
