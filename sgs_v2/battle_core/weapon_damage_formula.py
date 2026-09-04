from __future__ import annotations

import csv
from collections.abc import Mapping
from functools import lru_cache
from math import ceil
from pathlib import Path

from .attribute_system import AttributeSystem
from .context import BattleContext
from .enums import TroopType
from .unit import UnitRuntime


_TROOP_FUNCTION_TABLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "normal_attack"
    / "troop_function_table_1_10000.csv"
)


@lru_cache(maxsize=1)
def _load_repository_troop_function_table() -> dict[int, int]:
    """读取仓库中的完整 F(N) 查表，覆盖 N=1..10000。"""
    table: dict[int, int] = {}
    with _TROOP_FUNCTION_TABLE_PATH.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            table[int(row[0])] = int(row[1])
    return table


class WeaponBaseDamageFormula:
    """NORMAL_ATTACK_FORMULA_V1.md 的基础兵刃伤害实现。

    F(N) 在运行时完全由查表得到，不再分段计算公式。
    默认表为 data/normal_attack/troop_function_table_1_10000.csv。
    """

    _TROOP_MIN = 1
    _TROOP_MAX = 10000

    def __init__(
        self,
        attribute_system: AttributeSystem,
        *,
        troop_function_table: Mapping[int, int] | None = None,
        random_percent_range: tuple[int, int] = (86, 94),
        low_damage_floor_range: tuple[int, int] = (5, 15),
    ) -> None:
        self._validate_int_range("random_percent_range", random_percent_range)
        self._validate_int_range("low_damage_floor_range", low_damage_floor_range)
        self._attributes = attribute_system
        self.random_percent_range = random_percent_range
        self.low_damage_floor_range = low_damage_floor_range
        self._troop_function_table = self._validate_troop_function_table(
            _load_repository_troop_function_table()
            if troop_function_table is None
            else troop_function_table
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
        """通过完整查表返回 F(N)。"""
        if not isinstance(troops, int):
            raise TypeError("troops must be an integer")
        if not self._TROOP_MIN <= troops <= self._TROOP_MAX:
            raise ValueError("troops must be within lookup-table range [1, 10000]")
        return self._troop_function_table[troops]

    @staticmethod
    def _counter_multiplier(source: UnitRuntime, target: UnitRuntime) -> float:
        if source.troop_type is TroopType.SPEAR and target.troop_type is TroopType.CAVALRY:
            return 1.12
        if source.troop_type is TroopType.CAVALRY and target.troop_type is TroopType.SPEAR:
            return 0.88
        return 1.0

    @classmethod
    def _validate_troop_function_table(
        cls,
        table: Mapping[int, int],
    ) -> dict[int, int]:
        copied = dict(table)
        expected_keys = set(range(cls._TROOP_MIN, cls._TROOP_MAX + 1))
        if set(copied) != expected_keys:
            raise ValueError("troop_function_table must contain exactly keys 1..10000")
        if any(value < 0 for value in copied.values()):
            raise ValueError("troop_function_table values must be >= 0")
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
