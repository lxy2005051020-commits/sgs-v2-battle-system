"""Preserve captured potency while canonical lifecycle allocates new identities."""
from dataclasses import dataclass
from .stage10_state_params import FrozenContinuousDamageBasis


@dataclass(frozen=True, slots=True)
class TransferredFrozenDamageBasis(FrozenContinuousDamageBasis):
    def __post_init__(self):
        # dataclasses.replace inside the canonical lifecycle updates generation
        # and physical identity. Rebuild provenance from those new fields while
        # retaining formula facts, modifier plan and critical snapshot unchanged.
        object.__setattr__(self, "historical_source", None)
        super(TransferredFrozenDamageBasis, self).__post_init__()
