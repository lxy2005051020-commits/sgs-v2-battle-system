"""Opt-in provider-effectiveness gate over the existing counter state reader."""
from dataclasses import dataclass

from .stage9_state_params import CounterStateParams
from .stage9_state_runtime import Stage9StateRuntime
from .dependency_evaluation import ProviderNode
from .provider_identity import SkillProviderRef


@dataclass(frozen=True, slots=True)
class ProviderGatedCounterParams(CounterStateParams):
    """Marker: query existing provider dependencies before admitting a counter."""


class ProviderGatedCounterRuntime(Stage9StateRuntime):
    def get_counter_effects(self, context, holder_id):
        admitted = []
        for state in super().get_counter_effects(context, holder_id):
            if isinstance(state.runtime_params, ProviderGatedCounterParams):
                if self._state_effectiveness_policy is None:
                    raise RuntimeError("provider-gated counter requires an effectiveness policy")
                if state.source_skill_slot is None:
                    raise RuntimeError("provider-gated counter requires a canonical provider slot")
                provider = SkillProviderRef(state.source_id, state.source_skill_slot, state.source_skill_id)
                decision = self._state_effectiveness_policy.dependency_support.evaluate(context, ProviderNode(provider))
                if not decision.valid:
                    continue
                if not self._state_effectiveness_policy.evaluate_state(context, state).effective:
                    continue
            admitted.append(state)
        return tuple(admitted)
