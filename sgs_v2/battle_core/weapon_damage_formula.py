from __future__ import annotations

import csv
from collections.abc import Mapping
from functools import lru_cache
from math import ceil, floor, log2
from pathlib import Path

from .attribute_system import AttributeSystem
from .context import BattleContext
from .enums import TroopType
from .unit import UnitRuntime


_MID_TROOP_TABLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "normal_attack"
    / "mid_troop_table_2001_4999.csv"
)


@lru_cache(maxsize=1)
def _load_repository_mid_troop_table() -> dict[int, int]:
    """读取仓库中的 2001..4999 精确单调查表。"""
    table: dict[int, int] = {}
    with _MID_TROOP_TABLE_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            table[int(row[0])] = int(row[1])
    return table


class WeaponBaseDamageFormula:
    """NORMAL_ATTACK_FORMULA_V1.md 的基础兵刃伤害实现。"""

    _MID_TROOP_MIN = 2001
    _MID_TROOP_MAX = 4999

    def __init__(
        self,
        attribute_system: AttributeSystem,
        *,
        mid_troop_table: Mapping[int, int] | None = None,
        random_percent_range: tuple[int, int] = (86, 94),
        low_damage_floor_range: tuple[int, int] = (5, 15),
    ) -> None:
        self._validate_int_range("random_percent_range", random_percent_range)
        self._validate_int_range("low_damage_floor_range", low_damage_floor_range)
        self._attributes = attribute_system
        self.random_percent_range = random_percent_range
        self.low_damage_floor_range = low_damage_floor_range
        self._mid_troop_table = self._validate_mid_troop_table(
            _load_repository_mid_troop_table()
            if mid_troop_table is None
            else mid_troop_table
        )

    def calculate(
        self,
        context: BattleContext,
        source: UnitRuntime,
        target: UnitRuntime,
    ) -> int:
        """计算文档中的 DamageBase，不执行扣兵封顶。"""
        troops = source.troops
        weapon_attack = self._attributes.get_attack(context, source)
        defense = self._attributes.get_defense(context, target)

        source_level_scale = 0.6 + 0.02 * source.level
        target_level_scale = 0.6 + 0.02 * target.level

        x = (
            self.troop_function(troops)
            + weapon_attack * source_level_scale
            - defense * target_level_scale
        )
        troop_floor = min(100, ceil(troops / 50))
        b0 = ceil(max(x, troop_floor))

        b1 = ceil(b0 * self._counter_multiplier(source, target))

        morale_multiplier = 1 - 0.007 * max(0, 100 - source.morale)
        b2 = ceil(b1 * morale_multiplier)

        random_percent = context.random.randint(*self.random_percent_range)
        d0 = ceil(b2 * random_percent / 100)

        low_damage_floor = context.random.randint(*self.low_damage_floor_range)
        return max(d0, low_damage_floor)

    def troop_function(self, troops: int) -> int:
        """严格计算公式中的 F(N)。"""
        if troops < 0:
            raise ValueError("troops must be >= 0")

        if troops <= 2000:
            return ceil(troops / 10) + ceil(troops / 50)

        if troops < 5000:
            return self._mid_troop_table[troops]

        return self._round_half_up(429.27105 + 100 * log2(troops / 5000))

    @staticmethod
    def _counter_multiplier(source: UnitRuntime, target: UnitRuntime) -> float:
        if source.troop_type is TroopType.SPEAR and target.troop_type is TroopType.CAVALRY:
            return 1.12
        if source.troop_type is TroopType.CAVALRY and target.troop_type is TroopType.SPEAR:
            return 0.88
        return 1.0

    @classmethod
    def _validate_mid_troop_table(
        cls,
        table: Mapping[int, int],
    ) -> dict[int, int]:
        copied = dict(table)
        expected_keys = set(range(cls._MID_TROOP_MIN, cls._MID_TROOP_MAX + 1))
        if set(copied) != expected_keys:
            raise ValueError("mid_troop_table must contain exactly keys 2001..4999")
        if any(value < 0 for value in copied.values()):
            raise ValueError("mid_troop_table values must be >= 0")
        return copied

    @staticmethod
    def _validate_int_range(name: str, values: tuple[int, int]) -> None:
        if len(values) != 2:
            raise ValueError(f"{name} must contain exactly two integers")
        low, high = values
        if not isinstance(low, int) or not isinstance(high, int):
            raise TypeError(f"{name} values must be integers")
        if low > high:
            raise ValueError(f"{name} lower bound cannot exceed upper bound")

    @staticmethod
    def _round_half_up(value: float) -> int:
        if value < 0:
            raise ValueError("round_half_up only supports non-negative values")
        return floor(value + 0.5)
