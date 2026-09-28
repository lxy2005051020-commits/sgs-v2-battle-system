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
        with pytest.raises(ValueError, match="issued by this gate"):
            gate.consume_permit(forged, kind, "parent_test")

        # 3. Cross-gate permit from a different gate instance rejected
        other_gate = FutureAdmissionGate(coordinator=systems.finalization_coordinator)
        other_permit = other_gate.request_admission(kind, "parent_test")
        assert other_permit is not None
        with pytest.raises(ValueError, match="issued by this gate"):
            gate.consume_permit(other_permit, kind, "parent_test")



        # 4. Valid permit consumes successfully
        gate.consume_permit(permit, kind, "parent_test")
        assert permit.permit_id in gate._consumed_permits

        # 5. Replay of consumed permit is rejected
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

    def test_arch_02_structural_branch_instantiation_without_permit_rejected(self) -> None:
        from sgs_v2.battle_core.cleave_system import CleaveEffect
        from sgs_v2.battle_core.chain_system import ChainTraversal
        from sgs_v2.battle_core.counter_system import CounterBatch

        with pytest.raises(TypeError, match="Use CleaveSystem.create_effect with an authentic permit"):
            CleaveEffect()

        with pytest.raises(TypeError, match="Use ChainSystem.create_traversal with an authentic permit"):
            ChainTraversal()

        with pytest.raises(TypeError, match="Use CounterSystem.create_batch with an authentic permit"):
            CounterBatch()



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

    def test_arch_04_battle_engine_consumes_projection_permit_exactly_once(self) -> None:
        from sgs_v2.battle_core.engine import BattleEngine

        ctx = _create_test_context()
        systems = BattleSystems()
        # B0 (commander) has 1 troop, will die on first attack
        ctx.units["B0"].troops = 1
        events_emitted: list[str] = []
        ctx.event_bus.subscribe(
            EventType.BATTLE_ENDED, lambda ev: events_emitted.append("BATTLE_ENDED")
        )

        engine = BattleEngine(context=ctx, systems=systems)
        result = engine.run()
        assert result is not None
        assert systems.finalization_coordinator._projection_consumed is True
        assert systems.finalization_coordinator.claim_finalized_projection() is None
        assert events_emitted == ["BATTLE_ENDED"]



# ============================================================================
# ARCH-05: Operation IDs never gameplay comparator
# ============================================================================
class TestArch05OperationIdsNeverGameplayComparator:
    """ARCH-05: Operation IDs must not be used as priority or ordering comparators."""

    def test_arch_05_ast_scan_no_id_used_with_sorted_min_max_key(self) -> None:
        target_dir = Path("sgs_v2/battle_core")
        id_names = {
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
        }

        violations = []
        for fpath in target_dir.glob("*.py"):
            with open(fpath, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=str(fpath))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    is_sort_call = False
                    if isinstance(node.func, ast.Name) and node.func.id in ("sorted", "min", "max"):
                        is_sort_call = True
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
                        is_sort_call = True

                    if is_sort_call:
                        for kw in node.keywords:
                            if kw.arg == "key":
                                key_str = ast.unparse(kw.value)
                                for id_name in id_names:
                                    if id_name in key_str:
                                        violations.append((fpath.name, node.lineno, key_str))

        assert len(violations) == 0, f"Found ID comparators: {violations}"

    def test_arch_05_behavioral_permits_and_ids_forbid_relational_operators(self) -> None:
        # Permits
        permit1 = FutureAdmissionPermit("p1", FutureBranchKind.NEXT_ACTION, "parent1", 0)
        permit2 = FutureAdmissionPermit("p2", FutureBranchKind.NEXT_ACTION, "parent2", 0)

        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = permit1 < permit2
        with pytest.raises(TypeError, match="does not support comparison operator"):
            _ = permit1 > permit2

        # All 10 Operation Identities
        all_ids = [
            (ActionId("act1"), ActionId("act2")),
            (NormalAttackInstanceId("na1"), NormalAttackInstanceId("na2")),
            (TargetResolutionId("tr1"), TargetResolutionId("tr2")),
            (DamageInstanceId("dmg1"), DamageInstanceId("dmg2")),
            (PartitionTransactionId("ptn1"), PartitionTransactionId("ptn2")),
            (ReactionBatchId("rbt1"), ReactionBatchId("rbt2")),
            (CounterBatchEntryId("cbe1"), CounterBatchEntryId("cbe2")),
            (CleaveEffectId("cle1"), CleaveEffectId("cle2")),
            (ChainTraversalId("chn1"), ChainTraversalId("chn2")),
            (DirectTroopLossId("dtl1"), DirectTroopLossId("dtl2")),
        ]

        for id1, id2 in all_ids:
            with pytest.raises(TypeError, match="does not support comparison operator"):
                _ = id1 < id2
            with pytest.raises(TypeError, match="does not support comparison operator"):
                _ = id1 <= id2
            with pytest.raises(TypeError, match="does not support comparison operator"):
                _ = id1 > id2
            with pytest.raises(TypeError, match="does not support comparison operator"):
                _ = id1 >= id2



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

    @staticmethod
    def _get_all_runtime_imports(filepath: Path, modules: dict[str, Path]) -> set[str]:
        with open(filepath, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=str(filepath))
        deps: set[str] = set()

        def is_type_checking(node: ast.AST) -> bool:
            if isinstance(node, ast.If):
                if (isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING") or (
                    isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING"
                ):
                    return True
            return False

        def visit(node: ast.AST) -> None:
            if is_type_checking(node):
                return
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("sgs_v2.battle_core."):
                        parts = alias.name.split(".")
                        if len(parts) >= 3 and parts[2] in modules:
                            deps.add(parts[2])
                    elif alias.name in modules:
                        deps.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 1:
                    if node.module and node.module in modules:
                        deps.add(node.module)
                    else:
                        for alias in node.names:
                            if alias.name in modules:
                                deps.add(alias.name)
                elif node.module and node.module.startswith("sgs_v2.battle_core"):
                    parts = node.module.split(".")
                    if len(parts) >= 3 and parts[2] in modules:
                        deps.add(parts[2])
                    elif len(parts) == 2:
                        for alias in node.names:
                            if alias.name in modules:
                                deps.add(alias.name)
            for child in ast.iter_child_nodes(node):
                visit(child)

        visit(tree)
        return {d for d in deps if d in modules and d != filepath.stem}

    def test_arch_09_production_full_import_graph_has_zero_cycles(self) -> None:
        package_dir = Path("sgs_v2/battle_core")
        modules = {
            f.stem: f
            for f in package_dir.glob("*.py")
            if not f.name.startswith("__")
        }

        adj = {mod: self._get_all_runtime_imports(path, modules) for mod, path in modules.items()}


        cycles: list[list[str]] = []
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

        assert len(cycles) == 0, f"Found runtime import cycles: {cycles}"

    def test_arch_09_regression_execution_right_and_coordinator_no_cycle(self) -> None:
        from sgs_v2.battle_core.execution_right_system import FinalizationCoordinatorContract
        from sgs_v2.battle_core.battle_systems import BattleSystems

        systems = BattleSystems()
        coord = systems.finalization_coordinator
        assert isinstance(coord, FinalizationCoordinatorContract)

        # Confirm execution_right_system has no runtime import of battle_finalization_coordinator
        fpath = Path("sgs_v2/battle_core/execution_right_system.py")
        package_dir = Path("sgs_v2/battle_core")
        modules = {f.stem: f for f in package_dir.glob("*.py") if not f.name.startswith("__")}
        runtime_deps = self._get_all_runtime_imports(fpath, modules)
        assert "battle_finalization_coordinator" not in runtime_deps


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

    def test_arch_09_no_service_self_construction(self) -> None:
        # Systems must receive dependencies rather than constructing other core systems internally
        target_dir = Path("sgs_v2/battle_core")
        service_constructors = {
            "DamageSystem()",
            "CleaveSystem(",
            "ChainSystem(",
            "CounterSystem(",
            "BattleFinalizationCoordinator()",
            "FutureAdmissionGate(",
        }
        violations = []
        for fpath in target_dir.glob("*.py"):
            if fpath.name in ("battle_systems.py", "__init__.py"):
                continue
            with open(fpath, "r", encoding="utf-8") as fh:
                content = fh.read()
            for sc in service_constructors:
                if sc in content:
                    violations.append((fpath.name, sc))
        assert len(violations) == 0, f"Found service self-construction: {violations}"

    def test_arch_09_context_is_not_service_locator(self) -> None:
        ctx = _create_test_context()
        # Context holds state, data, event bus, random, and id allocator, but NO references to systems
        for forbidden in (
            "damage_system",
            "normal_attack_system",
            "cleave_system",
            "chain_system",
            "counter_system",
            "future_admission_gate",
            "finalization_coordinator",
            "state_lifecycle_system",
        ):
            assert not hasattr(ctx, forbidden), f"Context should not be service locator for {forbidden}"



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

    def test_arch_12_skill_slot_invalid_domain_value_rejected(self) -> None:
        with pytest.raises(ValueError):
            SkillSlot(3)

        with pytest.raises(ValueError):
            SkillSlot(-1)

    def test_arch_12_duplicate_slot_in_unit_runtime_loadout_rejected(self) -> None:
        from sgs_v2.battle_core.skill_runtime import LoadedSkillRef, LoadedSkillSet
        from sgs_v2.battle_core.skill_definition import (
            SkillDefinition,
            SkillTargetMode,
            ApplyStateSkillEffectSpec,
        )

        def0 = SkillDefinition(
            skill_id="s0",
            name="Skill 0",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(ApplyStateSkillEffectSpec("some_state"),),
        )
        def1 = SkillDefinition(
            skill_id="s1",
            name="Skill 1",
            activation_rate=1.0,
            target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
            effect_specs=(ApplyStateSkillEffectSpec("some_state2"),),
        )
        ref0 = LoadedSkillRef(owner_id="A0", definition=def0, skill_slot=SkillSlot.INHERENT)
        ref1 = LoadedSkillRef(owner_id="A0", definition=def1, skill_slot=SkillSlot.LEARNED_1)
        valid_set = LoadedSkillSet(owner_id="A0", loaded=(ref0, ref1))
        assert len(valid_set.loaded) == 2

        # Duplicate slot in loadout is rejected
        ref1_dup = LoadedSkillRef(owner_id="A0", definition=def0, skill_slot=SkillSlot.LEARNED_1)
        with pytest.raises(ValueError, match="Duplicate SkillSlot"):
            LoadedSkillSet(owner_id="A0", loaded=(ref0, ref1, ref1_dup))



