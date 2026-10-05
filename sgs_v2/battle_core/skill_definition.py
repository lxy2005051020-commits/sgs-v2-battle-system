from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .enums import DamageType


class SkillTargetMode(str, Enum):
    """Production Skill target intent mapped into the canonical TargetOperation model."""

    # Stage6 legacy mode. Its behavior remains ENEMY + SINGLE + RANDOM.
    SINGLE_RANDOM_ENEMY = "SINGLE_RANDOM_ENEMY"

    # Stage12 production producer mappings. These are producer intents only;
    # TargetOperation remains the canonical runtime contract.
    SINGLE_DETERMINISTIC_ENEMY = "SINGLE_DETERMINISTIC_ENEMY"
    CHOOSE_N_RANDOM_ENEMIES = "CHOOSE_N_RANDOM_ENEMIES"
    CHOOSE_N_DETERMINISTIC_ENEMIES = "CHOOSE_N_DETERMINISTIC_ENEMIES"
    FIXED_ALL_ENEMIES = "FIXED_ALL_ENEMIES"

    # Stage12 Capture needs real fresh friendly TargetOperation producers. These
    # modes add no Capture policy of their own; they only map producer intent
    # into the already-frozen ALLY/SELF target-operation taxonomy.
    SINGLE_RANDOM_ALLY = "SINGLE_RANDOM_ALLY"
    SINGLE_DETERMINISTIC_ALLY = "SINGLE_DETERMINISTIC_ALLY"
    CHOOSE_N_RANDOM_ALLIES = "CHOOSE_N_RANDOM_ALLIES"
    CHOOSE_N_RANDOM_TEAM = "CHOOSE_N_RANDOM_TEAM"
    CHOOSE_N_DETERMINISTIC_ALLIES = "CHOOSE_N_DETERMINISTIC_ALLIES"
    FIXED_ALL_ALLIES = "FIXED_ALL_ALLIES"
    FIXED_ALL_TEAM = "FIXED_ALL_TEAM"
    TEAM_COMMANDER = "TEAM_COMMANDER"
    TEAM_NON_COMMANDERS = "TEAM_NON_COMMANDERS"
    SELF = "SELF"


class SkillType(str, Enum):
    ACTIVE = "ACTIVE"
    ASSAULT = "ASSAULT"
    PASSIVE = "PASSIVE"
    COMMAND = "COMMAND"
    TROOP = "TROOP"
    FORMATION = "FORMATION"
    TALENT = "TALENT"


class PreparationMode(str, Enum):
    NONE = "NONE"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True, slots=True)
class DamageSkillEffectSpec:
    """把一次技能解析表达为伤害 Effect 的静态规格。"""

    damage_type: DamageType
    coefficient: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.damage_type, DamageType):
            raise TypeError("damage_type must be a DamageType")
        if isinstance(self.coefficient, bool) or not isinstance(
            self.coefficient, (int, float)
        ):
            raise TypeError("coefficient must be an int or float")
        if not math.isfinite(self.coefficient):
            raise ValueError("coefficient must be finite")
        if self.coefficient < 0:
            raise ValueError("coefficient must be >= 0")

        object.__setattr__(self, "coefficient", float(self.coefficient))


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state_runtime_params import StateRuntimeParams


@dataclass(frozen=True, slots=True)
class ApplyStateSkillEffectSpec:
    """把一次技能解析表达为施加状态 Effect 的静态规格。"""

    state_id: str
    runtime_params: StateRuntimeParams | None = None
    expires_round: int | None = None
    expires_phase: str | None = None
    continuous_damage_coefficient: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id cannot be empty")
        if self.continuous_damage_coefficient is not None:
            from .numeric_validation import validate_nonnegative_finite
            object.__setattr__(self, "continuous_damage_coefficient", validate_nonnegative_finite(
                self.continuous_damage_coefficient, "continuous_damage_coefficient"))
        if self.expires_round is not None:
            if isinstance(self.expires_round, bool) or not isinstance(self.expires_round, int):
                raise TypeError("expires_round must be an int or None")
            if self.expires_round < 1:
                raise ValueError("expires_round must be >= 1")
        if self.expires_phase is not None:
            if not isinstance(self.expires_phase, str) or not self.expires_phase.strip():
                raise ValueError("expires_phase cannot be empty when provided")


@dataclass(frozen=True, slots=True)
class RecoverySkillEffectSpec:
    """A nominal recovery amount; the recovery owner applies prevention/capacity."""
    amount: int

    def __post_init__(self) -> None:
        if type(self.amount) is not int or self.amount < 0:
            raise ValueError("recovery amount must be a nonnegative integer")


SkillEffectSpec = DamageSkillEffectSpec | ApplyStateSkillEffectSpec | RecoverySkillEffectSpec


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    """技能的不可变静态定义。

    Stage 6 只保存真正被解析器消费的静态数据；触发、时序、分类、冷却等
    尚未建立正式合同的能力继续延后。
    """

    skill_id: str
    name: str
    activation_rate: float
    target_mode: SkillTargetMode
    effect_specs: tuple[SkillEffectSpec, ...]
    skill_type: SkillType = SkillType.ACTIVE
    preparation_mode: PreparationMode = PreparationMode.NONE
    target_count: int | None = None
    target_restriction_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id cannot be empty")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name cannot be empty")
        if isinstance(self.activation_rate, bool) or not isinstance(
            self.activation_rate, (int, float)
        ):
            raise TypeError("activation_rate must be an int or float")
        if not math.isfinite(self.activation_rate):
            raise ValueError("activation_rate must be finite")
        if not 0.0 <= self.activation_rate <= 1.0:
            raise ValueError("activation_rate must be in [0.0, 1.0]")
        if not isinstance(self.target_mode, SkillTargetMode):
            raise TypeError("target_mode must be a SkillTargetMode")
        if not isinstance(self.skill_type, SkillType):
            raise TypeError("skill_type must be a SkillType")
        if not isinstance(self.preparation_mode, PreparationMode):
            raise TypeError("preparation_mode must be a PreparationMode")

        choose_n_modes = {
            SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,
            SkillTargetMode.CHOOSE_N_DETERMINISTIC_ENEMIES,
            SkillTargetMode.CHOOSE_N_RANDOM_ALLIES,
            SkillTargetMode.CHOOSE_N_RANDOM_TEAM,
            SkillTargetMode.CHOOSE_N_DETERMINISTIC_ALLIES,
        }
        if self.target_mode in choose_n_modes:
            if isinstance(self.target_count, bool) or not isinstance(
                self.target_count, int
            ):
                raise TypeError("CHOOSE_N target_count must be an int")
            if self.target_count <= 0:
                raise ValueError("CHOOSE_N target_count must be > 0")
        elif self.target_count is not None:
            raise ValueError("target_count is only valid for CHOOSE_N target modes")

        restriction_keys = tuple(self.target_restriction_keys)
        if any(
            not isinstance(item, str) or not item.strip()
            for item in restriction_keys
        ):
            raise ValueError(
                "target_restriction_keys must contain non-empty strings"
            )
        object.__setattr__(self, "target_restriction_keys", restriction_keys)

        specs = tuple(self.effect_specs)
        if not specs:
            raise ValueError("effect_specs must contain at least one item")
        if any(
            not isinstance(
                spec,
                (DamageSkillEffectSpec, ApplyStateSkillEffectSpec, RecoverySkillEffectSpec),
            )
            for spec in specs
        ):
            raise TypeError("effect_specs contains an unsupported spec type")

        object.__setattr__(self, "activation_rate", float(self.activation_rate))
        object.__setattr__(self, "effect_specs", specs)
