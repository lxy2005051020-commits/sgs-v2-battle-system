from __future__ import annotations

# Stage11 official states no longer piggy-back on the provisional Stage8
# WEAKNESS-as-prevention skeleton. Their frozen semantics are owned by the
# dedicated Stage11 runtime seams.
DEFAULT_STAGE8_STATE_RULE_BINDINGS = ()


def default_stage8_official_binding_state_ids() -> frozenset[str]:
    return frozenset()
