"""Opt-in additive basis adapter over the unchanged canonical damage owner.

The frozen owner has one base * coefficient seam before all downstream modifiers.
An internal numeric basis supplies base * coefficient + addition at that seam.
It never escapes the adapter: published base_damage remains an ordinary float.
No RNG, modifier, damage permission or settlement algorithm is reproduced here.

An independent opt-in final addition lane augments the ordinary final integer
result after modifiers, before partition/settlement. It never changes coefficient
or feeds that addition back into the ordinary modifier pipeline.
"""
from contextvars import ContextVar
from dataclasses import dataclass, fields, replace

from .damage_system import DamageRequest, DamageResult, DamageSystem
from .enums import DamageCalculationBasis
from .numeric_validation import validate_nonnegative_finite


@dataclass(frozen=True, slots=True)
class AdditiveDamageRequest(DamageRequest):
    additive_damage: float = 0.0

    def __post_init__(self):
        DamageRequest.__post_init__(self)
        object.__setattr__(self, "additive_damage", validate_nonnegative_finite(
            self.additive_damage, "additive_damage"))
        if self.calculation_basis is not DamageCalculationBasis.LIVE_RUNTIME and self.additive_damage:
            raise ValueError("additive damage only supports LIVE_RUNTIME")


@dataclass(frozen=True, slots=True)
class FinalAdditiveDamageRequest(AdditiveDamageRequest):
    """Opt-in addition to final theoretical damage, after ordinary modifiers."""
    final_additive_damage: float = 0.0

    def __post_init__(self):
        AdditiveDamageRequest.__post_init__(self)
        object.__setattr__(self, "final_additive_damage", validate_nonnegative_finite(
            self.final_additive_damage, "final_additive_damage"))
        if self.calculation_basis is not DamageCalculationBasis.LIVE_RUNTIME and self.final_additive_damage:
            raise ValueError("final additive damage only supports LIVE_RUNTIME")


@dataclass(frozen=True, slots=True)
class FinalAdditiveDamageResult(DamageResult):
    # pipeline_trace remains the original modifier trace; this separate lane is
    # explicitly recorded instead of masquerading as an ordinary modifier.
    unaugmented_final_damage: int = 0
    final_additive_damage: float = 0.0


class _AdditiveBasis(float):
    def __new__(cls, value, addition):
        basis = super().__new__(cls, value)
        basis.addition = addition
        return basis

    def __mul__(self, coefficient):
        return float(self) * coefficient + self.addition


class AdditiveDamageSystem(DamageSystem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._addition = ContextVar("damage_basis_addition", default=0.0)

    def calculate(self, context, request):
        addition = request.additive_damage if isinstance(request, AdditiveDamageRequest) else 0.0
        token = self._addition.set(addition)
        try:
            result = super().calculate(context, request)
            if isinstance(result.base_damage, _AdditiveBasis):
                result = replace(result, base_damage=float(result.base_damage))
            final_addition = (request.final_additive_damage
                              if isinstance(request, FinalAdditiveDamageRequest) else 0.0)
            if (final_addition and not result.prevented and result.zeroed_by_state_id is None
                    and not (result.alert_consumed_instance_id is not None and result.final_damage == 0)):
                # Keep prevention/weakness/alert authoritative. Settlement,
                # partition, aftermath and troop capacity consume this result
                # through their existing owners; never add after troop mutation.
                result = FinalAdditiveDamageResult(
                    **{field.name: getattr(result, field.name) for field in fields(DamageResult)
                       if field.name != "final_damage"},
                    final_damage=int(result.final_damage + final_addition),
                    unaugmented_final_damage=result.final_damage,
                    final_additive_damage=final_addition,
                )
            return result
        finally:
            self._addition.reset(token)

    def _calculate_weapon_base_damage(self, *args, **kwargs):
        value = super()._calculate_weapon_base_damage(*args, **kwargs)
        return _AdditiveBasis(value, self._addition.get()) if self._addition.get() else value

    def _calculate_strategy_base_damage(self, *args, **kwargs):
        value = super()._calculate_strategy_base_damage(*args, **kwargs)
        return _AdditiveBasis(value, self._addition.get()) if self._addition.get() else value
