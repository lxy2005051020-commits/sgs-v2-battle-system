from __future__ import annotations

from typing import TYPE_CHECKING

from .damage_rule_models import (
    DamagePreventionContribution,
    DamagePreventionRuleKind,
    DamageRuleFamily,
    RuleContributionSource,
)
from .damage_rule_provider import StateRuleAdapter, StateRuleBinding
from .official_state_catalog import OfficialStateId
from .state_instance import StateInstance

if TYPE_CHECKING:
    from .damage_system import DamageRequest


def _build_weakness_prevention(
    instance: StateInstance,
    source: RuleContributionSource,
    request: "DamageRequest",
) -> DamagePreventionContribution | None:
    if instance.owner_id != request.source_id:
        return None
    return DamagePreventionContribution(
        kind=DamagePreventionRuleKind.SOURCE_CANNOT_DEAL_DAMAGE,
        source=source,
        order_key=source.origin_key,
    )


DEFAULT_STAGE8_STATE_RULE_BINDINGS = (
    StateRuleBinding(
        state_id=OfficialStateId.WEAKNESS.value,
        adapters=(
            StateRuleAdapter(
                adapter_key="weakness_prevention",
                family=DamageRuleFamily.PREVENTION,
                build=_build_weakness_prevention,
            ),
        ),
    ),
)


def default_stage8_official_binding_state_ids() -> frozenset[str]:
    return frozenset(binding.state_id for binding in DEFAULT_STAGE8_STATE_RULE_BINDINGS)
