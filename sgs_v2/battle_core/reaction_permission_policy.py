from __future__ import annotations

from .operation_identity import SourceType


class ReactionPermissionPolicy:
    """Centralized typed authority for recursion, callback, and reaction permissions.

    Invariants:
    - Permissions derive from SourceType, NormalAttack identity, and lineage.
    - No string-based permissions, no call-stack booleans, no battle.finished checks.
    - INV-13: Cleave has no NormalAttack identity.
    - INV-17: Cleave permissions are identity-driven (Counter and recursive Cleave blocked).
    - INV-19 / INV-20: Direct troop loss never enters HitResolution / callbacks.
    - INV-35: Chain TRUE_FEEDBACK uses restricted settlement (no Chain, Counter, Share, etc.).
    """

    @staticmethod
    def has_normal_attack_identity(source_type: SourceType) -> bool:
        """Only physical NORMAL_ATTACK retains NormalAttack identity."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        return source_type == SourceType.NORMAL_ATTACK

    @staticmethod
    def is_direct_troop_loss(source_type: SourceType) -> bool:
        """Identify non-hit attributed direct troop loss."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        return source_type in (
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        )

    @classmethod
    def can_trigger_cleave(cls, source_type: SourceType) -> bool:
        """Determine whether the source event can trigger Cleave.

        Only physical NORMAL_ATTACK can trigger Cleave (subject to trigger P0).
        CLEAVE, COUNTER, CHAIN, and direct loss are strictly blocked from triggering Cleave.
        """
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CLEAVE,
            SourceType.COUNTER,
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type == SourceType.NORMAL_ATTACK

    @classmethod
    def can_trigger_counter(cls, source_type: SourceType) -> bool:
        """Determine whether the source event can trigger Counter.

        Counter requires normal attack identity.
        CLEAVE, COUNTER, CHAIN, and direct loss are strictly blocked from triggering Counter.
        """
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CLEAVE,
            SourceType.COUNTER,
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type == SourceType.NORMAL_ATTACK

    @classmethod
    def can_trigger_chain(cls, source_type: SourceType) -> bool:
        """Determine whether the source event can trigger Chain propagation.

        NORMAL_ATTACK, ACTIVE_SKILL, PERIODIC_DAMAGE, CLEAVE, and COUNTER may qualify under P0.
        CHAIN_TRUE_FEEDBACK, SHARE_DIRECT_LOSS, and DISTRIBUTION_DIRECT_LOSS are strictly blocked.
        """
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type in (
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
        )

    @classmethod
    def can_enter_partition(cls, source_type: SourceType) -> bool:
        """Determine whether the damage event can enter Share / Distribution partition."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type in (
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
        )

    @classmethod
    def can_trigger_recovery(cls, source_type: SourceType) -> bool:
        """Determine whether the damage event can trigger recovery (e.g. FirstAid)."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type in (
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.ASSAULT,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
        )

    @classmethod
    def can_trigger_evasion(cls, source_type: SourceType) -> bool:
        """Determine whether the damage event can enter Evasion gate."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type in (
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
        )

    @classmethod
    def can_trigger_resistance(cls, source_type: SourceType) -> bool:
        """Determine whether the damage event can enter Resistance gate."""
        if not isinstance(source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(source_type)}")
        if source_type in (
            SourceType.CHAIN_TRUE_FEEDBACK,
            SourceType.SHARE_DIRECT_LOSS,
            SourceType.DISTRIBUTION_DIRECT_LOSS,
        ):
            return False
        return source_type in (
            SourceType.NORMAL_ATTACK,
            SourceType.ACTIVE_SKILL,
            SourceType.PERIODIC_DAMAGE,
            SourceType.CLEAVE,
            SourceType.COUNTER,
        )
