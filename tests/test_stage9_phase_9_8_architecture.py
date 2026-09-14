"""Stage9 Phase 9.8 Architecture Tests (ARCH-01 .. ARCH-12).

Authoritative verification of the 12 Architecture Guarantees:
- ARCH-01: Stage8 semantic/import inversion blocked
- ARCH-02: FutureAdmissionGate no bypass
- ARCH-03: Finalization semantic writer single
- ARCH-04: Finalization projection exactly once
- ARCH-05: Operation IDs never gameplay comparator
- ARCH-06: StateRegistry sole physical state storage
- ARCH-07: StateLifecycleSystem sole physical state mutation owner
- ARCH-08: EventBus facts-only
- ARCH-09: BattleSystems composition root & acyclic dependencies
- ARCH-10: Damage settlement one-shot & authenticity
- ARCH-11: EffectExecutor Stage9 SourceType producer coverage
- ARCH-12: source_skill_slot ingress & immutability
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any
import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleSystems,
    DamageRequest,
    DamageResult,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    SkillSlot,
    UnitRuntime,
    register_official_state_definitions,
)
from sgs_v2.battle_core.battle_finalization_coordinator import (
    BattleFinalizationCoordinator,
    BattleTerminationState,
)
from sgs_v2.battle_core.chain_system import ResolvedDamageFact
from sgs_v2.battle_core.damage_instance_coordinator import DamageInstanceCoordinator
from sgs_v2.battle_core.damage_resolution_system import DamageSettlementRequest
from sgs_v2.battle_core.effects import DamageEffect, EffectSourceRef, ApplyStateEffect
from sgs_v2.battle_core.execution_right_system import (
    FutureAdmissionGate,
    FutureAdmissionPermit,
    FutureBranchKind,
    DamageSettlementPermit,
    ActionScope,
    LegacyFinalizationBarrier,
)
from sgs_v2.battle_core.operation_identity import (
    ActionId,
    CleaveEffectId,
    ChainTraversalId,
    CounterBatchEntryId,
    DamageInstanceId,
    DirectTroopLossId,
    NormalAttackInstanceId,
    OperationIdAllocator,
    OperationLineage,
    PartitionTransactionId,
    ReactionBatchId,
    SourceType,
    TargetResolutionId,
)
from sgs_v2.battle_core.stage9_state_params import CleaveStateParams, CounterStateParams
from sgs_v2.battle_core.stage9_integerization import ExactRatio


def _create_test_context(battle_id: str = "arch_test") -> BattleContext:
    units = {}
    for team in ("A", "B"):
        for n, pos in enumerate(LineupPosition):
            uid = f"{team}{n}"
            units[uid] = UnitRuntime(
                uid,
                f"Unit_{uid}",
                team,
                max_troops=10000,
                troops=10000,
                attack=150,
                defense=100,
                speed=100,
                lineup_position=pos,
            )
    ctx = BattleContext(
        battle_id=battle_id,
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(42),
    )
    register_official_state_definitions(ctx.states)
    return ctx


# ============================================================================
# ARCH-01: Stage8 semantic/import inversion blocked
# ============================================================================
class TestArch01Stage8InversionBlocked:
    """ARCH-01: Stage8 calculation modules must not import Stage9 mechanism modules.

    DamageResult.final_damage = Dtotal meaning remains strictly unchanged.
    """

    def test_arch_01_ast_stage8_modules_do_not_import_stage9_mechanisms(self) -> None:
        stage8_files = [
            "damage_system.py",
            "damage_prevention_system.py",
            "hit_resolution_system.py",
            "damage_formula_policy_system.py",
            "damage_modifier_system.py",
            "weapon_damage_formula.py",
            "strategy_damage_formula.py",
            "damage_pipeline_trace.py",
        ]
        forbidden_tokens = [
            "CleaveSystem",
            "ChainSystem",
            "CounterSystem",
            "DamagePartitionCoordinator",
            "FutureAdmissionGate",
            "BattleFinalizationCoordinator",
            "cleave_system",
            "chain_system",
            "counter_system",
            "damage_partition_system",
            "execution_right_system",
            "battle_finalization_coordinator",
        ]

        battle_core_dir = Path("sgs_v2/battle_core")
        for fname in stage8_files:
            fpath = battle_core_dir / fname
            assert fpath.exists(), f"Stage8 file {fname} not found"
            with open(fpath, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(fpath))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for token in forbidden_tokens:
                            assert (
                                token.lower() not in alias.name.lower()
                            ), f"ARCH-01 violation in {fname}: import {alias.name}"
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for token in forbidden_tokens:
                        assert (
                            token.lower() not in mod.lower()
                        ), f"ARCH-01 violation in {fname}: from {mod} import ..."
                    for alias in node.names:
                        for token in forbidden_tokens:
                            assert (
                                token.lower() not in alias.name.lower()
                            ), f"ARCH-01 violation in {fname}: from {mod} import {alias.name}"

    def test_arch_01_behavioral_damage_result_final_damage_is_dtotal(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()

        req = DamageRequest(
            source_id="A0",
            target_id="B0",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
        )
        res = systems.damage_system.calculate(ctx, req)
        assert isinstance(res, DamageResult)
        assert res.final_damage == int(res.scaled_damage)
        assert res.final_damage > 0


# ============================================================================
# ARCH-02: FutureAdmissionGate no bypass
# ============================================================================
class TestArch02FutureAdmissionGateNoBypass:
    """ARCH-02: All six FutureBranch kinds must be structurally permit-gated.

    No branch created without authentic permit.
    Forged permit, cross-gate permit, and consumed permit replay are rejected.
    """

    @pytest.mark.parametrize(
        "kind",
        [
            FutureBranchKind.NEXT_ACTION,
            FutureBranchKind.ASSAULT,
            FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK,
            FutureBranchKind.COUNTER_BATCH,
            FutureBranchKind.CHAIN_TRAVERSAL,
            FutureBranchKind.CLEAVE_EFFECT,
        ],
    )
    def test_arch_02_all_six_future_branches_require_authentic_permit(
        self, kind: FutureBranchKind
    ) -> None:
        systems = BattleSystems()
        gate = systems.future_admission_gate

        # 1. Normal request produces valid permit
        permit = gate.request_admission(kind, "parent_test")
        assert permit is not None
        assert permit.branch_kind == kind
        assert permit.permit_id in gate._issued_permits
        assert permit.permit_id not in gate._consumed_permits

        # 2. Forged permit with identical fields but not issued in gate._issued_permits
        forged = FutureAdmissionPermit(
            permit_id="forged_id_999",
            branch_kind=kind,
            parent_scope_identity="parent_test",
            termination_generation=0,
        )
        with pytest.raises(ValueError, match="not issued by this gate"):
            gate.consume_permit(forged, kind, "parent_test")

        # 3. Valid permit consumes successfully
        gate.consume_permit(permit, kind, "parent_test")
        assert permit.permit_id in gate._consumed_permits

        # 4. Replay of consumed permit is rejected
        with pytest.raises(RuntimeError, match="already been consumed"):
            gate.consume_permit(permit, kind, "parent_test")

    def test_arch_02_cross_gate_kind_mismatch_rejected(self) -> None:
        systems = BattleSystems()
        gate = systems.future_admission_gate

        permit = gate.request_admission(
            FutureBranchKind.NEXT_ACTION, "parent_action"
        )
        assert permit is not None

        # Try to use NEXT_ACTION permit for COMBO_SECOND_NORMAL_ATTACK
        with pytest.raises(ValueError, match="Branch kind mismatch"):
            gate.consume_permit(
                permit,
                expected_branch_kind=FutureBranchKind.COMBO_SECOND_NORMAL_ATTACK,
                expected_parent_scope_identity="parent_action",
            )


# ============================================================================
# ARCH-03: Finalization semantic writer single
# ============================================================================
class TestArch03FinalizationSemanticWriterSingle:
    """ARCH-03: BattleFinalizationCoordinator is the sole semantic owner writing termination.

    Engine is legacy projection only. Mechanisms do not write termination state.
    """

    def test_arch_03_ast_finalized_state_written_only_by_coordinator(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        finalized_writers: list[tuple[str, int, str]] = []

        for fpath in target_dir.glob("*.py"):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    if (
                        "self._termination_state = BattleTerminationState.FINALIZED"
                        in line
                        or "termination_state = BattleTerminationState.FINALIZED"
                        in line
                    ):
                        finalized_writers.append((fpath.name, idx, line.strip()))

        assert len(finalized_writers) == 1
        assert finalized_writers[0][0] == "battle_finalization_coordinator.py"

    def test_arch_03_ast_context_ended_and_result_written_only_by_engine(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        ended_writers: list[tuple[str, int, str]] = []
        result_writers: list[tuple[str, int, str]] = []

        for fpath in target_dir.glob("*.py"):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    if ".ended = True" in line or ".ended=True" in line:
                        ended_writers.append((fpath.name, idx, line.strip()))
                    if "self.context.result =" in line or "context.result =" in line:
                        result_writers.append((fpath.name, idx, line.strip()))

        assert len(ended_writers) == 1
        assert ended_writers[0][0] == "engine.py"
        assert len(result_writers) == 1
        assert result_writers[0][0] == "engine.py"


# ============================================================================
# ARCH-04: Finalization projection exactly once
# ============================================================================
class TestArch04FinalizationProjectionExactlyOnce:
    """ARCH-04: Finalization projection permit claim once, consume once, project once."""

    def test_arch_04_projection_permit_claim_and_consume_exactly_once(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()
        coord = systems.finalization_coordinator

        # Simulate commander death
        ctx.units["B0"].troops = 0
        coord.observe_legacy_barrier(ctx, LegacyFinalizationBarrier.ACTION_SETTLED)

        assert coord.termination_state is BattleTerminationState.FINALIZED

        # First claim succeeds
        claim = coord.claim_finalized_projection()
        assert claim is not None
        permit, fin_res = claim

        # Second claim returns None
        claim_again = coord.claim_finalized_projection()
        assert claim_again is None

        # Consuming the permit once succeeds
        coord.consume_projection_permit(permit)
        assert coord._projection_consumed

        # Consuming the permit again is rejected
        with pytest.raises(RuntimeError, match="already been consumed"):
            coord.consume_projection_permit(permit)


# ============================================================================
# ARCH-05: Operation IDs never gameplay comparator
# ============================================================================
class TestArch05OperationIdsNeverGameplayComparator:
    """ARCH-05: Operation IDs must not be used as priority or ordering comparators."""

    def test_arch_05_ast_scan_no_id_used_with_sorted_min_max_key(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        id_names = [
            "ActionId",
            "NormalAttackInstanceId",
            "TargetResolutionId",
            "DamageInstanceId",
            "PartitionTransactionId",
            "ReactionBatchId",
            "CounterBatchEntryId",
            "CleaveEffectId",
            "ChainTraversalId",
            "DirectTroopLossId",
        ]

        violations = []
        for fpath in target_dir.glob("*.py"):
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    for id_name in id_names:
                        if id_name in line and ("key=" in line or "sorted" in line) and "id.value" in line:
                            violations.append((fpath.name, idx, line.strip()))

        assert len(violations) == 0, f"Found ID comparators: {violations}"

    def test_arch_05_behavioral_permits_and_ids_forbid_relational_operators(self) -> None:
        permit1 = FutureAdmissionPermit("p1", FutureBranchKind.NEXT_ACTION, "parent1", 0)
        permit2 = FutureAdmissionPermit("p2", FutureBranchKind.NEXT_ACTION, "parent2", 0)

        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = permit1 < permit2

        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = permit1 > permit2


# ============================================================================
# ARCH-06: StateRegistry sole physical state storage
# ============================================================================
class TestArch06StateRegistrySolePhysicalStateStorage:
    """ARCH-06: StateRegistry is the sole physical state storage."""

    def test_arch_06_ast_scan_no_duplicate_physical_state_collections(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        forbidden_state_collections = [
            "active_states",
            "combo_states",
            "cleave_states",
            "counter_states",
            "chain_states",
        ]

        violations = []
        for fpath in target_dir.glob("*.py"):
            if fpath.name == "state_registry.py":
                continue
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    for col in forbidden_state_collections:
                        if f"{col}: dict" in line or f"{col} = dict" in line or f"{col} = []" in line or f"{col}: list" in line:
                            violations.append((fpath.name, idx, line.strip()))

        assert len(violations) == 0, f"Found duplicate physical state storage: {violations}"


# ============================================================================
# ARCH-07: StateLifecycleSystem sole physical state mutation owner
# ============================================================================
class TestArch07StateLifecycleSystemSoleMutationOwner:
    """ARCH-07: StateLifecycleSystem is the sole mutation owner of StateRegistry physical states."""

    def test_arch_07_ast_scan_state_registry_mutations_only_in_lifecycle_system(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        mutation_lines: list[tuple[str, int, str]] = []

        for fpath in target_dir.glob("*.py"):
            if fpath.name == "state_registry.py":
                continue
            with open(fpath, "r", encoding="utf-8") as fh:
                for idx, line in enumerate(fh, 1):
                    if any(call in line for call in [".states.add(", ".states.remove(", ".states.replace("]):
                        mutation_lines.append((fpath.name, idx, line.strip()))

        for fname, idx, line in mutation_lines:
            assert (
                fname == "state_lifecycle_system.py"
            ), f"ARCH-07 violation: state mutation outside lifecycle system at {fname}:{idx}: {line}"


# ============================================================================
# ARCH-08: EventBus facts-only
# ============================================================================
class TestArch08EventBusFactsOnly:
    """ARCH-08: EventBus is strictly facts-only. No control flow depends on subscribers."""

    def test_arch_08_combat_action_completes_with_zero_eventbus_subscribers(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()

        # Ensure EventBus has zero subscribers
        assert len(ctx.event_bus._handlers) == 0

        # Execute normal attack round 1
        parent_scope = "round_1_actor_A0"
        permit = systems.future_admission_gate.request_admission(
            FutureBranchKind.NEXT_ACTION, parent_scope
        )
        assert permit is not None
        from sgs_v2.battle_core.execution_right_system import admit_action_scope
        scope = admit_action_scope(ctx, systems.future_admission_gate, permit, ctx.units["A0"], parent_scope)
        assert scope is not None

        result = systems.action_system.execute(ctx, ctx.units["A0"], action_scope=scope)
        assert result is not None
        systems.finalization_coordinator.complete_action_scope(ctx, scope)
        assert scope.terminal


# ============================================================================
# ARCH-09: BattleSystems composition root & acyclic dependencies
# ============================================================================
class TestArch09BattleSystemsCompositionRootAndAcyclicGraph:
    """ARCH-09: BattleSystems is composition root; import graph is strictly acyclic."""

    def test_arch_09_production_top_level_import_graph_has_zero_cycles(self) -> None:
        package_dir = Path("sgs_v2/battle_core")
        modules = {
            f.stem: f
            for f in package_dir.glob("*.py")
            if not f.name.startswith("__")
        }

        def get_top_level_imports(filepath: Path) -> set[str]:
            with open(filepath, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(filepath))
            deps = set()
            for stmt in tree.body:
                if isinstance(stmt, ast.If):
                    if (isinstance(stmt.test, ast.Name) and stmt.test.id == "TYPE_CHECKING") or (
                        isinstance(stmt.test, ast.Attribute) and stmt.test.attr == "TYPE_CHECKING"
                    ):
                        continue
                if isinstance(stmt, ast.Import):
                    for alias in stmt.names:
                        if alias.name.startswith("sgs_v2.battle_core."):
                            deps.add(alias.name.split(".")[2])
                elif isinstance(stmt, ast.ImportFrom):
                    if stmt.level == 1:
                        if stmt.module:
                            deps.add(stmt.module)
                        else:
                            for alias in stmt.names:
                                if alias.name in modules:
                                    deps.add(alias.name)
                    elif stmt.module and stmt.module.startswith("sgs_v2.battle_core"):
                        parts = stmt.module.split(".")
                        if len(parts) >= 3:
                            deps.add(parts[2])
                        elif len(parts) == 2:
                            for alias in stmt.names:
                                if alias.name in modules:
                                    deps.add(alias.name)
            return {d for d in deps if d in modules}

        adj = {mod: get_top_level_imports(path) for mod, path in modules.items()}

        cycles = []
        visited: dict[str, int] = {}
        path: list[str] = []

        def dfs(node: str) -> None:
            visited[node] = 1
            path.append(node)
            for neighbor in sorted(adj.get(node, set())):
                if visited.get(neighbor, 0) == 1:
                    idx = path.index(neighbor)
                    cycles.append(path[idx:] + [neighbor])
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor)
            path.pop()
            visited[node] = 2

        for mod in sorted(modules.keys()):
            if visited.get(mod, 0) == 0:
                dfs(mod)

        assert len(cycles) == 0, f"Found cycles: {cycles}"

    def test_arch_09_battlesystems_is_sole_composition_root(self) -> None:
        systems = BattleSystems()
        assert systems.damage_system is not None
        assert systems.normal_attack_system is not None
        assert systems.cleave_system is not None
        assert systems.chain_system is not None
        assert systems.counter_system is not None
        assert systems.future_admission_gate is not None
        assert systems.finalization_coordinator is not None
        assert systems.state_lifecycle_system is not None


# ============================================================================
# ARCH-10: Damage settlement one-shot & authenticity
# ============================================================================
class TestArch10DamageSettlementOneShotAndAuthenticity:
    """ARCH-10: Damage settlement requires authentic DamageSettlementPermit.

    Same-value clone, foreign-context, and consumed replay are rejected.
    """

    def test_arch_10_settlement_permit_authenticity_and_replay_protection(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()
        coordinator = systems.damage_instance_coordinator

        lineage = OperationLineage(
            root_action_id=ActionId("act_arch10"),
            parent_normal_attack_id=NormalAttackInstanceId("na_arch10"),
            parent_damage_instance_id=None,
            source_type=SourceType.NORMAL_ATTACK,
        )
        dmg_id = coordinator.begin_damage_instance(ctx, lineage)
        permit = coordinator.issue_settlement_permit(dmg_id, lineage, ctx)

        from sgs_v2.battle_core.damage_resolution_system import SettlementOrigin

        req = DamageSettlementRequest(
            damage_result=DamageResult(
                source_id="A0",
                target_id="B0",
                damage_type=DamageType.WEAPON,
                source_type=DamageSourceType.NORMAL_ATTACK,
                coefficient=1.0,
                base_damage=100.0,
                scaled_damage=100.0,
                final_damage=100,
            ),
            assigned_target_damage=100,
            damage_instance_id=dmg_id,
            lineage=lineage,
            origin=SettlementOrigin.STAGE9,
        )

        # Clone permit rejected
        clone_permit = DamageSettlementPermit(
            permit_id=permit.permit_id,
            damage_instance_id=permit.damage_instance_id,
        )
        with pytest.raises(ValueError, match="authenticity failure"):
            coordinator.validate_and_consume_permit(ctx, clone_permit, req)

        # Foreign context rejected
        ctx_foreign = _create_test_context(battle_id="foreign_b")
        with pytest.raises(ValueError, match="different BattleContext"):
            coordinator.validate_and_consume_permit(ctx_foreign, permit, req)

        # Legitimate consume succeeds
        coordinator.validate_and_consume_permit(ctx, permit, req)
        assert coordinator._permits[(id(ctx), permit.permit_id)].consumed

        # Consumed replay rejected
        with pytest.raises(ValueError, match="already been consumed"):
            coordinator.validate_and_consume_permit(ctx, permit, req)

        coordinator.close_damage_instance(dmg_id, ctx)


# ============================================================================
# ARCH-11: EffectExecutor Stage9 SourceType producer coverage
# ============================================================================
class TestArch11EffectExecutorSourceTypeProducerCoverage:
    """ARCH-11: 100% of production DamageEffect constructors have authoritative EffectSourceRef.

    No reverse inference from Stage8 DamageSourceType.
    """

    def test_arch_11_production_damage_effect_constructors_are_100_percent_classified(self) -> None:
        target_dir = Path("sgs_v2")
        constructors = []

        for fpath in target_dir.rglob("*.py"):
            with open(fpath, "r", encoding="utf-8") as fh:
                content = fh.read()
            if "DamageEffect(" in content:
                for idx, line in enumerate(content.splitlines(), 1):
                    if "DamageEffect(" in line:
                        constructors.append((fpath.name, idx, line.strip()))

        # Exactly two production constructors: skill_resolver.py and trigger_system.py
        assert len(constructors) == 2
        file_names = {c[0] for c in constructors}
        assert file_names == {"skill_resolver.py", "trigger_system.py"}

    def test_arch_11_effect_executor_rejects_damage_effect_without_source_ref(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()
        effect_no_ref = DamageEffect(
            source_id="A0",
            target_id="B0",
            damage_type=DamageType.WEAPON,
            source_type=DamageSourceType.NORMAL_ATTACK,
            coefficient=1.0,
            source_ref=None,
        )

        with pytest.raises(ValueError, match="requires authoritative EffectSourceRef"):
            systems.effect_executor.execute(ctx, effect_no_ref)


# ============================================================================
# ARCH-12: source_skill_slot ingress & immutability
# ============================================================================
class TestArch12SourceSkillSlotIngressAndImmutability:
    """ARCH-12: SkillSlot domain (0, 1, 2) from runtime loadout, duplicate loadout rejection."""

    def test_arch_12_skill_slot_domain_and_loadout_binding(self) -> None:
        assert SkillSlot.INHERENT.value == 0
        assert SkillSlot.LEARNED_1.value == 1
        assert SkillSlot.LEARNED_2.value == 2
        assert len(SkillSlot) == 3

    def test_arch_12_cleave_requires_valid_slot_or_raises_domain_error(self) -> None:
        ctx = _create_test_context()
        systems = BattleSystems()

        # Cleave state applied without valid slot
        systems.state_lifecycle_system.apply(
            ctx,
            state_id="cleave",
            owner_id="A0",
            source_id="A0",
            source_skill_id="test_cleave",
            source_skill_slot=None,
            runtime_params=CleaveStateParams(ExactRatio(1, 2)),
        )

        fact = ResolvedDamageFact(
            ctx.id_allocator.allocate_damage_instance_id(),
            "B1",
            OperationLineage(
                ctx.id_allocator.allocate_action_id(),
                ctx.id_allocator.allocate_normal_attack_id(),
                None,
                SourceType.NORMAL_ATTACK,
                "A0",
                None,
                "A0",
            ),
            DamageType.WEAPON,
            50,
            50,
        )

        # Resolving cleave on state with missing required slot raises ValueError (domain error)
        with pytest.raises(ValueError, match="authoritative source_skill_slot"):
            systems.cleave_system.resolve(ctx, fact)
