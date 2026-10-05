"""Stage13 Final Exit Whole-Battle Replay Audit.

Executes and verifies:
1. Case A: Same-seed duplicate execution (N >= 20 runs) producing 100% identical canonical projection.
2. Case B: Multi-seed divergence demonstrating differences strictly originate from authorized RNG streams.
3. Case C: Deterministic zero-draw paths ensuring no superfluous RNG consumption.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattleSystems,
    EventBus,
    LineupPosition,
    RandomSystem,
    UnitRuntime,
)
from sgs_v2.battle_core.skill_definition import (
    DamageSkillEffectSpec,
    SkillDefinition,
    SkillTargetMode,
    SkillType,
)
from sgs_v2.battle_core.skill_runtime import SkillRuntime
from sgs_v2.battle_core.skill_resolver import SkillResolver
from sgs_v2.battle_core.enums import DamageType
from sgs_v2.battle_core.skill_runtime import SkillSlot


def make_standard_lineup() -> dict[str, UnitRuntime]:
    return {
        "a1": UnitRuntime(
            unit_id="a1",
            name="A队主将",
            team_id="A",
            max_troops=1000,
            troops=1000,
            attack=240,
            defense=140,
            speed=120,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "a2": UnitRuntime(
            unit_id="a2",
            name="A队第一副将",
            team_id="A",
            max_troops=900,
            troops=900,
            attack=210,
            defense=130,
            speed=105,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
        "b1": UnitRuntime(
            unit_id="b1",
            name="B队主将",
            team_id="B",
            max_troops=1000,
            troops=1000,
            attack=230,
            defense=145,
            speed=115,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b2": UnitRuntime(
            unit_id="b2",
            name="B队第一副将",
            team_id="B",
            max_troops=900,
            troops=900,
            attack=205,
            defense=125,
            speed=110,
            lineup_position=LineupPosition.DEPUTY_1,
        ),
    }


def canonical_battle_projection(seed: int, battle_id: str = "canonical-battle") -> dict[str, Any]:
    units = make_standard_lineup()
    bus = EventBus()
    ctx = BattleContext(
        battle_id=battle_id,
        units=units,
        event_bus=bus,
        random=RandomSystem(seed=seed),
        max_rounds=8,
    )
    engine = BattleEngine(context=ctx, systems=BattleSystems())
    result = engine.run()

    canonical_events = []
    for e in bus.history:
        canonical_events.append({
            "round_no": e.round_no,
            "phase": str(e.phase),
            "event_type": e.event_type.value,
            "actor_id": e.actor_id,
            "target_id": e.target_id,
            "payload": dict(sorted(e.payload.items())),
        })

    return {
        "winner_team_id": result.winner_team_id,
        "reason": result.reason.value,
        "rounds_completed": result.rounds_completed,
        "final_troops": dict(sorted(result.final_troops.items())),
        "event_count": len(canonical_events),
        "events": canonical_events,
    }


def compute_projection_hash(proj: dict[str, Any]) -> str:
    serialized = json.dumps(proj, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def test_replay_case_a_same_seed_25_runs() -> None:
    """Case A: Same seed executed 25 times must produce identical projections."""
    seed = 20260904
    baseline_proj = canonical_battle_projection(seed)
    baseline_hash = compute_projection_hash(baseline_proj)

    for run_idx in range(25):
        run_proj = canonical_battle_projection(seed)
        run_hash = compute_projection_hash(run_proj)
        assert run_hash == baseline_hash, f"Run {run_idx} diverged from baseline!"


def test_replay_case_b_seed_change_divergence() -> None:
    """Case B: Seed variation produces deterministic, authorized divergence."""
    seeds = [101, 202, 303, 404, 505, 606, 707, 808]
    hashes = set()
    projections = []
    for s in seeds:
        proj = canonical_battle_projection(s)
        h = compute_projection_hash(proj)
        hashes.add(h)
        projections.append((s, h, proj["winner_team_id"], proj["rounds_completed"]))

    # Multiple distinct seeds must produce distinct battle paths
    assert len(hashes) > 1, "Seeds did not cause any divergence"

    # Re-running any of those seeds must reproduce exactly the same hash
    for s, expected_h, _, _ in projections:
        re_proj = canonical_battle_projection(s)
        re_h = compute_projection_hash(re_proj)
        assert re_h == expected_h, f"Seed {s} failed to reproduce exactly"


def test_replay_case_c_zero_rng_fast_paths() -> None:
    """Case C: Probability 0, probability 1, single valid target, and disabled do not consume RNG."""
    # Build a counting wrapper for RandomSystem
    class TraceableRNG(RandomSystem):
        def __init__(self, seed: int = 42) -> None:
            super().__init__(seed)
            self.draw_count = 0

        def random(self) -> float:
            self.draw_count += 1
            return super().random()

        def randint(self, a: int, b: int) -> int:
            self.draw_count += 1
            return super().randint(a, b)

        def choice(self, values: Any) -> Any:
            self.draw_count += 1
            return super().choice(values)

        def sample(self, values: Any, k: int) -> list[Any]:
            self.draw_count += 1
            return super().sample(values, k)

    rng = TraceableRNG(seed=12345)
    bus = EventBus()
    units = make_standard_lineup()
    ctx = BattleContext(
        battle_id="zero-rng-test",
        units=units,
        event_bus=bus,
        random=rng,
        max_rounds=8,
    )

    resolver = SkillResolver(target_system=BattleSystems().target_system)

    # 1. Rate 0.0 skill -> 0 RNG draws
    zero_skill = SkillDefinition(
        skill_id="zero_skill",
        name="零概率技能",
        activation_rate=0.0,
        target_mode=SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
        effect_specs=(DamageSkillEffectSpec(damage_type=DamageType.WEAPON, coefficient=1.0),),
    )
    runtime_zero = SkillRuntime(
        definition=zero_skill,
        owner_id="a1",
        skill_slot=SkillSlot.INHERENT,
    )
    draws_before = rng.draw_count
    res_zero = resolver.resolve(ctx, runtime_zero)
    assert res_zero.status.value == "ACTIVATION_FAILED"
    assert rng.draw_count == draws_before, "Rate 0.0 consumed RNG!"

    # 2. Disabled runtime -> 0 RNG draws
    disabled_skill = SkillDefinition(
        skill_id="disabled_skill",
        name="禁用技能",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
        effect_specs=(DamageSkillEffectSpec(damage_type=DamageType.WEAPON, coefficient=1.0),),
    )
    runtime_disabled = SkillRuntime(
        definition=disabled_skill,
        owner_id="a1",
        skill_slot=SkillSlot.INHERENT,
        enabled=False,
    )
    draws_before = rng.draw_count
    res_disabled = resolver.resolve(ctx, runtime_disabled)
    assert res_disabled.status.value == "DISABLED"
    assert rng.draw_count == draws_before, "Disabled skill consumed RNG!"

    # 3. Rate 1.0 + deterministic target -> 0 RNG draws
    det_skill = SkillDefinition(
        skill_id="det_skill",
        name="确定性技能",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,
        effect_specs=(DamageSkillEffectSpec(damage_type=DamageType.WEAPON, coefficient=1.0),),
    )
    runtime_det = SkillRuntime(
        definition=det_skill,
        owner_id="a1",
        skill_slot=SkillSlot.INHERENT,
    )
    draws_before = rng.draw_count
    res_det = resolver.resolve(ctx, runtime_det)
    assert res_det.status.value == "RESOLVED"
    assert rng.draw_count == draws_before, "Rate 1.0 + deterministic target consumed RNG!"
