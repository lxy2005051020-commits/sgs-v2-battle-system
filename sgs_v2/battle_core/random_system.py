from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


class RandomSystem:
    """
    战斗唯一随机源。

    任何后续 BattleSystem / SkillRuntime 都应从 BattleContext.random
    获取随机结果，不直接调用 random.random()。
    """

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, values: Sequence[T]) -> T:
        if not values:
            raise ValueError("choice() cannot select from an empty sequence")
        return self._rng.choice(values)

    def sample(self, values: Sequence[T], k: int) -> list[T]:
        return self._rng.sample(values, k)

    def chance(self, probability: float) -> bool:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be in [0.0, 1.0]")
        return self.random() < probability

    def shuffle(self, values: list[T]) -> None:
        self._rng.shuffle(values)
