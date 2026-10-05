"""Read-only projection of the frozen TroopSystem.restore capacity contract.

This view allocates a nominal shared budget; only RecoverySystem/TroopSystem
can enforce prevention, adopt a legacy pool, or mutate troops and wounds.
"""
from .unit import UnitRuntime


def recoverable_capacity(target: UnitRuntime) -> int:
    if not target.is_alive:
        return 0
    missing = target.max_troops - target.troops
    wounded = target.wounded_troops
    assert wounded is not None
    if not target._wounded_pool_authoritative:
        wounded = max(wounded, missing)
    return min(missing, wounded)
