from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from .enums import DamageType
from .operation_identity import SourceType
from .state_generation import StateApplicationGenerationId


class DamageHitTopology(str, Enum):
    """Authoritative hit topology enum (STAGE10.md §15.1)."""

    RESOLVED_HIT = "RESOLVED_HIT"
    NO_RESOLVED_HIT_EVASION_OR_MISS = "NO_RESOLVED_HIT_EVASION_OR_MISS"


class DamageZeroLossCause(str, Enum):
    """Authoritative zero-loss classification enum (STAGE10.md §15.1)."""

    WEAKNESS_ZERO = "WEAKNESS_ZERO"
    BARRIER_ZERO = "BARRIER_ZERO"
    SETTLED_ZERO = "SETTLED_ZERO"


@dataclass(frozen=True, slots=True)
class DamageAftermathFact:
    """
    Typed damage aftermath fact emitted after hit resolution & troop loss settlement.
    Required for FIRST_AID_AFTER_DAMAGE recovery opportunities (STAGE10.md §15.1).
    """

    damage_instance_id: str
    target_id: str
    source_type: SourceType
    damage_type: DamageType
    assigned_target_damage: int
    actual_target_troop_loss: int
    target_troops_after: int
    target_defeated: bool
    hit_topology: DamageHitTopology
    zero_loss_cause: DamageZeroLossCause | None = None
    source_state_generation: StateApplicationGenerationId | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.damage_instance_id, str) or not self.damage_instance_id.strip():
            raise ValueError("damage_instance_id cannot be empty or whitespace")
        if not isinstance(self.target_id, str) or not self.target_id.strip():
            raise ValueError("target_id cannot be empty or whitespace")
        if not isinstance(self.source_type, SourceType):
            raise TypeError(f"source_type must be a SourceType, got {type(self.source_type)}")
        if not isinstance(self.damage_type, DamageType):
            raise TypeError(f"damage_type must be a DamageType, got {type(self.damage_type)}")
        if isinstance(self.assigned_target_damage, bool) or not isinstance(
            self.assigned_target_damage, int
        ):
            raise TypeError("assigned_target_damage must be an int")
        if self.assigned_target_damage < 0:
            raise ValueError("assigned_target_damage must be >= 0")
        if isinstance(self.actual_target_troop_loss, bool) or not isinstance(
            self.actual_target_troop_loss, int
        ):
            raise TypeError("actual_target_troop_loss must be an int")
        if self.actual_target_troop_loss < 0:
            raise ValueError("actual_target_troop_loss must be >= 0")
        if isinstance(self.target_troops_after, bool) or not isinstance(
            self.target_troops_after, int
        ):
            raise TypeError("target_troops_after must be an int")
        if self.target_troops_after < 0:
            raise ValueError("target_troops_after must be >= 0")
        if not isinstance(self.target_defeated, bool):
            raise TypeError("target_defeated must be a bool")
        if not isinstance(self.hit_topology, DamageHitTopology):
            raise TypeError(
                f"hit_topology must be a DamageHitTopology, got {type(self.hit_topology)}"
            )
        if self.zero_loss_cause is not None and not isinstance(
            self.zero_loss_cause, DamageZeroLossCause
        ):
            raise TypeError(
                f"zero_loss_cause must be a DamageZeroLossCause or None, got {type(self.zero_loss_cause)}"
            )
        if self.source_state_generation is not None and not isinstance(
            self.source_state_generation, StateApplicationGenerationId
        ):
            raise TypeError(
                f"source_state_generation must be a StateApplicationGenerationId or None, got {type(self.source_state_generation)}"
            )


class DamageAftermathPort(Protocol):
    """
    Port interface for damage aftermath commitment (STAGE10.md §15, §23).
    Shared checkpoint across standard damage, periodic damage, counter, assault, and cleave.
    Formally integrated in Phase 6.
    """

    def commit_aftermath(self, context: Any, aftermath_fact: DamageAftermathFact) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class AftermathResult:
    """Synchronous outcome of a DamageAftermathPort commitment."""

    aftermath_fact: DamageAftermathFact
    opportunity_results: tuple[Any, ...]
    executed: bool = False


def create_damage_aftermath_fact(
    *,
    damage_instance_id: Any,
    target_id: str,
    source_type: SourceType,
    damage_type: DamageType,
    assigned_target_damage: int,
    actual_target_troop_loss: int,
    target_troops_after: int,
    target_defeated: bool,
    damage_result: Any = None,
    hit_topology: DamageHitTopology | None = None,
    zero_loss_cause: DamageZeroLossCause | None = None,
    source_state_generation: StateApplicationGenerationId | None = None,
) -> DamageAftermathFact:
    """
    Authoritative factory deriving a typed DamageAftermathFact from settled damage.
    Resolves hit topology, zero-loss cause, and generation provenance per STAGE10.md §15.
    """
    d_id = str(damage_instance_id)

    if hit_topology is None:
        if damage_result is not None and getattr(damage_result, "prevented", False):
            prevented_by = getattr(damage_result, "prevented_by_state_id", None)
            if prevented_by == "weakness":
                hit_topology = DamageHitTopology.RESOLVED_HIT
                zero_loss_cause = zero_loss_cause or DamageZeroLossCause.WEAKNESS_ZERO
            elif prevented_by == "barrier":
                hit_topology = DamageHitTopology.RESOLVED_HIT
                zero_loss_cause = zero_loss_cause or DamageZeroLossCause.BARRIER_ZERO
            else:
                hit_topology = DamageHitTopology.NO_RESOLVED_HIT_EVASION_OR_MISS
                zero_loss_cause = None
        else:
            hit_topology = DamageHitTopology.RESOLVED_HIT

    if hit_topology == DamageHitTopology.RESOLVED_HIT and actual_target_troop_loss == 0:
        if zero_loss_cause is None:
            zero_loss_cause = DamageZeroLossCause.SETTLED_ZERO
    elif hit_topology != DamageHitTopology.RESOLVED_HIT:
        zero_loss_cause = None

    if source_state_generation is None and damage_result is not None:
        source_state_generation = getattr(damage_result, "source_generation_id", None)

    return DamageAftermathFact(
        damage_instance_id=d_id,
        target_id=target_id,
        source_type=source_type,
        damage_type=damage_type,
        assigned_target_damage=assigned_target_damage,
        actual_target_troop_loss=actual_target_troop_loss,
        target_troops_after=target_troops_after,
        target_defeated=target_defeated,
        hit_topology=hit_topology,
        zero_loss_cause=zero_loss_cause,
        source_state_generation=source_state_generation,
    )


class DamageAftermathSystem:
    """
    Authoritative concrete implementation of DamageAftermathPort (STAGE10.md §15, §23).
    Bridges settled damage checkpoints across standard, DOT, counter, assault, and cleave
    to RecoveryOpportunitySystem for FIRST_AID.
    """

    def __init__(
        self,
        trigger_system: Any = None,
        recovery_opportunity_system: Any = None,
    ) -> None:
        self._trigger = trigger_system
        self._recovery = recovery_opportunity_system

    def commit_aftermath(
        self,
        context: Any,
        aftermath_fact: DamageAftermathFact,
    ) -> AftermathResult:
        if not isinstance(aftermath_fact, DamageAftermathFact):
            raise TypeError(
                f"aftermath_fact must be DamageAftermathFact, got {type(aftermath_fact)}"
            )

        # Fatal damage exclusion (STAGE10.md §15.2, §24.1): target defeated -> no recovery opportunity
        if aftermath_fact.target_defeated:
            return AftermathResult(
                aftermath_fact=aftermath_fact,
                opportunity_results=(),
                executed=False,
            )

        # Source type permission exclusion (STAGE10.md §15, §23): direct loss & chain feedback blocked
        from .reaction_permission_policy import ReactionPermissionPolicy

        if not ReactionPermissionPolicy.can_trigger_recovery(aftermath_fact.source_type):
            return AftermathResult(
                aftermath_fact=aftermath_fact,
                opportunity_results=(),
                executed=False,
            )

        # Evasion / Miss exclusion (STAGE10.md §15.2): no resolved hit -> no recovery opportunity
        if aftermath_fact.hit_topology != DamageHitTopology.RESOLVED_HIT:
            return AftermathResult(
                aftermath_fact=aftermath_fact,
                opportunity_results=(),
                executed=False,
            )

        trigger = (
            self._trigger
            or getattr(getattr(context, "systems", None), "trigger_system", None)
        )
        if trigger is None:
            return AftermathResult(
                aftermath_fact=aftermath_fact,
                opportunity_results=(),
                executed=False,
            )

        recovery_sys = (
            self._recovery
            or getattr(
                getattr(context, "systems", None),
                "recovery_opportunity_system",
                None,
            )
        )
        if recovery_sys is None:
            return AftermathResult(
                aftermath_fact=aftermath_fact,
                opportunity_results=(),
                executed=False,
            )

        opportunities = trigger.collect_after_damage(
            context, aftermath_fact.target_id, aftermath_fact
        )
        results = []
        for opp in opportunities:
            res = recovery_sys.evaluate_and_resolve(
                context, opp, aftermath_fact=aftermath_fact
            )
            results.append(res)

        return AftermathResult(
            aftermath_fact=aftermath_fact,
            opportunity_results=tuple(results),
            executed=any(r.executed for r in results),
        )

