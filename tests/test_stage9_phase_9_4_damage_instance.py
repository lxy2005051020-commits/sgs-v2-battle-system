from __future__ import annotations

import pytest

# Phase 9.4 historical coverage is preserved verbatim in the adjacent non-collected
# history module.  Its phase-scoped EffectExecutor legacy-route assertion is the
# one invariant superseded by the authorized Phase 9.5 production cutover; all
# other Phase 9.4 regression classes remain collected here unchanged.
from _stage9_phase_9_4_damage_instance_history import (
    TestBattleSystemsAndFinalizationObservation,
    TestContextOwnershipBoundaryFinalRepair,
    TestCoordinatorPermitLifecycleRepair,
    TestPermitAuthenticityAndContextIsolationFinalRepairRound2,
    TestThreeLayerSeparationFixture,
    _make_context,
)
from sgs_v2.battle_core.battle_systems import BattleSystems
from sgs_v2.battle_core.damage_resolution_system import SettlementOrigin
from sgs_v2.battle_core.damage_system import DamageRequest, DamageResult
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef
from sgs_v2.battle_core.enums import DamageSourceType, DamageType
from sgs_v2.battle_core.operation_identity import SourceType


class TestPhase95EffectExecutorRouteMigration:
    """Phase 9.5 migration of the superseded Phase 9.4 production-route assertion."""

    def test_p95_reg_mig_01_direct_resolve_remains_legacy_compat(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        systems = BattleSystems()
        context = _make_context(troops_b=1000)
        observed_origins: list[SettlementOrigin] = []
        original_settle_legacy = systems.damage_resolution_system._settle_legacy

        def observed_settle_legacy(ctx, request):
            observed_origins.append(request.origin)
            return original_settle_legacy(ctx, request)

        monkeypatch.setattr(
            systems.damage_resolution_system,
            "_settle_legacy",
            observed_settle_legacy,
        )

        result = systems.damage_resolution_system.resolve(
            context,
            DamageRequest(
                source_id="A1",
                target_id="B1",
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.SKILL,
                coefficient=1.0,
                source_skill_id="p95-reg-mig-01",
            ),
        )

        assert observed_origins == [SettlementOrigin.LEGACY_COMPAT]
        assert result.damage_instance_id is None
        assert result.lineage is None
        assert result.assigned_target_damage == result.damage.final_damage
        assert result.actual_target_troop_loss > 0

    def test_p95_reg_mig_02_direct_apply_result_remains_legacy_compat(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        systems = BattleSystems()
        context = _make_context(troops_b=1000)
        observed_origins: list[SettlementOrigin] = []
        original_settle_legacy = systems.damage_resolution_system._settle_legacy

        def observed_settle_legacy(ctx, request):
            observed_origins.append(request.origin)
            return original_settle_legacy(ctx, request)

        monkeypatch.setattr(
            systems.damage_resolution_system,
            "_settle_legacy",
            observed_settle_legacy,
        )

        damage = DamageResult(
            source_id="A1",
            target_id="B1",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.SKILL,
            coefficient=1.0,
            base_damage=90.0,
            scaled_damage=90.0,
            final_damage=90,
            source_skill_id="p95-reg-mig-02",
        )
        result = systems.damage_resolution_system.apply_result(context, damage)

        assert observed_origins == [SettlementOrigin.LEGACY_COMPAT]
        assert result.damage_instance_id is None
        assert result.lineage is None
        assert result.assigned_target_damage == 90
        assert result.actual_target_troop_loss == 90

    def test_p95_reg_mig_03_effect_executor_uses_stage9_and_never_legacy_resolve(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        systems = BattleSystems()
        context = _make_context(troops_b=1000)
        legacy_resolve_calls = 0

        def forbidden_legacy_resolve(*args, **kwargs):
            nonlocal legacy_resolve_calls
            legacy_resolve_calls += 1
            raise AssertionError("EffectExecutor DamageEffect must not call legacy resolve()")

        monkeypatch.setattr(
            systems.damage_resolution_system,
            "resolve",
            forbidden_legacy_resolve,
        )

        result = systems.effect_executor.execute(
            context,
            DamageEffect(
                source_id="A1",
                target_id="B1",
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.SKILL,
                coefficient=1.0,
                source_skill_id="p95-reg-mig-03",
                source_ref=EffectSourceRef(
                    stage9_source_type=SourceType.ACTIVE_SKILL,
                    source_unit_id="A1",
                    source_skill_id="p95-reg-mig-03",
                ),
            ),
        )

        assert legacy_resolve_calls == 0
        assert result.damage_instance_id is not None
        assert result.resolution.damage_instance_id == result.damage_instance_id
        assert result.resolution.lineage is not None

    def test_legacy_constructor_is_non_damage_compatible_but_damage_fails_fast(self) -> None:
        systems = BattleSystems()
        context = _make_context(troops_b=1000)
        executor = systems.effect_executor.__class__(
            systems.damage_resolution_system,
            systems.state_lifecycle_system,
            systems.recovery_system,
        )

        with pytest.raises(RuntimeError, match="DamageInstanceCoordinator"):
            executor.execute(
                context,
                DamageEffect(
                    source_id="A1",
                    target_id="B1",
                    damage_type=DamageType.WEAPON,
                    source_type=DamageSourceType.SKILL,
                    coefficient=1.0,
                    source_skill_id="legacy-constructor-no-fallback",
                    source_ref=EffectSourceRef(
                        stage9_source_type=SourceType.ACTIVE_SKILL,
                        source_unit_id="A1",
                        source_skill_id="legacy-constructor-no-fallback",
                    ),
                ),
            )
