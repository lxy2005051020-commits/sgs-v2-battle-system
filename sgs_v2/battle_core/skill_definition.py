from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .enums import DamageType


class SkillTargetMode(str, Enum):
    """Stage 6 最小技能目标意图。"""

    SINGLE_RANDOM_ENEMY = "SINGLE_RANDOM_ENEMY"


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


@dataclass(frozen=True, slots=True)
class ApplyStateSkillEffectSpec:
    """把一次技能解析表达为施加状态 Effect 的静态规格。"""

    state_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.state_id, str) or not self.state_id.strip():
            raise ValueError("state_id cannot be empty")


SkillEffectSpec = DamageSkillEffectSpec | ApplyStateSkillEffectSpec


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

        specs = tuple(self.effect_specs)
        if not specs:
            raise ValueError("effect_specs must contain at least one item")
        if any(
            not isinstance(
                spec,
                (DamageSkillEffectSpec, ApplyStateSkillEffectSpec),
            )
            for spec in specs
        ):
            raise TypeError("effect_specs contains an unsupported spec type")

        object.__setattr__(self, "activation_rate", float(self.activation_rate))
        object.__setattr__(self, "effect_specs", specs)
