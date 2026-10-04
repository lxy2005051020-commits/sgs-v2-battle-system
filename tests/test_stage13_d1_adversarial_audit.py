"""Independent adversarial harness: no imports from the implementation test fixture."""
import ast
from pathlib import Path

import pytest

from sgs_v2.battle_core import (
    BattleContext, BattleSystems, BattlePhase, EventBus, LineupPosition,
    RandomSystem, UnitRuntime, OperationLineage, SourceType,
)
from sgs_v2.battle_core.execution_right_runtime import ExecutionRightRequest, ExecutionRightSpec, ExecutionRightMode
from sgs_v2.battle_core.execution_right_system import LegacyFinalizationBarrier
from sgs_v2.battle_core.pending_work import (
    PendingWorkDispatchResult, PendingWorkReadPolicy, WorkReadMode,
    PendingWorkScheduleSpec, ScheduleKind, PendingWorkTimingPoint,
    PendingWorkStatus, WorkLifetimeSpec, WorkLifetimeKind,
)


def harness():
    c = BattleContext("independent-d1", {
        key: UnitRuntime(key, key, key, 100, 100, 10, 10, 10,
                         lineup_position=LineupPosition.COMMANDER)
        for key in ("L", "R")
    }, EventBus(), RandomSystem(2026))
    c.current_round = 1
    c.current_phase = BattlePhase.ROUND_END.value
    return c, BattleSystems()


def queue(c, s, kind, **kwargs):
    opts = dict(work_kind=kind, parent_lineage=OperationLineage(None, None, None, SourceType.PERIODIC_DAMAGE),
                execution_right_request=ExecutionRightRequest(target_id="L"),
                schedule_spec=PendingWorkScheduleSpec(ScheduleKind.SPECIFIC_ROUND_PHASE, BattlePhase.ROUND_START, 2))
    opts.update(kwargs)
    return s.pending_work_system.create(c, **opts)


def advance(c, s):
    c.current_round = 2
    c.current_phase = BattlePhase.ROUND_START.value
    return s.pending_work_system.process(c, PendingWorkTimingPoint(2, BattlePhase.ROUND_START))


def test_finalization_during_first_dispatch_cancels_same_batch_siblings():
    c, s = harness()
    calls = []
    def first(ctx, frame):
        calls.append("first")
        # Audit fault injection uses the existing troop/finalization owners.
        s.troop_system.apply_damage(ctx.units["R"], 100)
        s.finalization_coordinator.observe_legacy_barrier(ctx, LegacyFinalizationBarrier.ROUND_START_HOOKS_SETTLED)
        return PendingWorkDispatchResult(ctx.id_allocator.allocate_effect_operation_id(), frame.lineage)
    def second(ctx, frame):
        calls.append("second")
        return PendingWorkDispatchResult(ctx.id_allocator.allocate_effect_operation_id(), frame.lineage)
    s.pending_work_system.register_dispatcher("first", first)
    s.pending_work_system.register_dispatcher("second", second)
    a = queue(c, s, "first")
    b = queue(c, s, "second")
    advance(c, s)
    assert calls == ["first"]
    assert c.pending_work.get(a.work_id).status is PendingWorkStatus.COMPLETED
    assert c.pending_work.get(b.work_id).status is PendingWorkStatus.CANCELLED
    assert s.finalization_coordinator.finalization_result is not None


def test_gate_closure_during_live_read_cancels_before_gameplay():
    c, s = harness()
    calls = []
    def read(ctx, work):
        s.troop_system.apply_damage(ctx.units["R"], 100)
        s.finalization_coordinator.observe_legacy_barrier(ctx, LegacyFinalizationBarrier.ACTION_SETTLED)
        return 1
    s.pending_work_system.register_live_reader("fault_injection", read)
    s.pending_work_system.register_dispatcher("work", lambda *args: calls.append("unsafe"))
    work = queue(c, s, "work", read_policy=PendingWorkReadPolicy((("fault_injection", WorkReadMode.LIVE_AT_EXECUTION),)))
    advance(c, s)
    assert calls == []
    assert c.pending_work.get(work.work_id).terminal_reason == "BATTLE_ADMISSION_CLOSED"


def test_delayed_damage_uses_existing_transaction_and_preserves_child_lineage():
    from sgs_v2.battle_core import DamageRequest, DamageType, DamageSourceType
    c, s = harness()
    s.weapon_random_percent_range = (90, 90)
    def damage(ctx, frame):
        execution = s.damage_instance_coordinator.execute_partitioned_damage_instance(
            context=ctx,
            request=DamageRequest("L", "R", DamageType.WEAPON, DamageSourceType.SKILL, coefficient=1000),
            lineage=frame.lineage,
        )
        return PendingWorkDispatchResult(execution.damage_instance_id, frame.lineage, execution)
    s.pending_work_system.register_dispatcher("damage", damage)
    s.pending_work_system.register_dispatcher("later", lambda *_: pytest.fail("future sibling revived gameplay"))
    parent = OperationLineage(c.id_allocator.allocate_action_id(), None, None, SourceType.ACTIVE_SKILL,
                              physical_attacker="L", physical_skill="fixture", credit_owner="L")
    work = queue(c, s, "damage", parent_lineage=parent)
    sibling = queue(c, s, "later")
    result = advance(c, s)[0]
    assert result.lineage.root_action_id == parent.root_action_id
    assert result.lineage.parent_pending_work_id == work.work_id
    assert result.result.resolution.target_defeated
    assert s.finalization_coordinator.finalization_result is not None
    assert not s.finalization_coordinator.has_admitted_work
    assert c.pending_work.get(sibling.work_id).status is PendingWorkStatus.CANCELLED


def test_forged_child_lineage_fails_closed():
    c, s = harness()
    wrong = OperationLineage(None, None, None, SourceType.PERIODIC_DAMAGE)
    s.pending_work_system.register_dispatcher("bad", lambda ctx, frame:
        PendingWorkDispatchResult(ctx.id_allocator.allocate_effect_operation_id(), wrong))
    work = queue(c, s, "bad")
    with pytest.raises(TypeError, match="matching child"):
        advance(c, s)
    assert c.pending_work.get(work.work_id).terminal_reason == "DISPATCH_FAILED"


def test_live_reader_failure_does_not_leave_executing_or_retry():
    c, s = harness()
    calls = []
    def fail(ctx, work):
        raise LookupError("missing live fact")
    s.pending_work_system.register_live_reader("fact", fail)
    s.pending_work_system.register_dispatcher("work", lambda *args: calls.append("unsafe"))
    work = queue(c, s, "work", read_policy=PendingWorkReadPolicy((("fact", WorkReadMode.LIVE_AT_EXECUTION),)))
    with pytest.raises(LookupError):
        advance(c, s)
    assert c.pending_work.get(work.work_id).status is PendingWorkStatus.CANCELLED
    assert advance(c, s) == () and calls == []


@pytest.mark.parametrize("spec", [
    ExecutionRightSpec(provider_validity=ExecutionRightMode.RECHECK_AT_EXECUTION),
    ExecutionRightSpec(state_effectiveness=ExecutionRightMode.RECHECK_AT_EXECUTION),
    ExecutionRightSpec(actor_permission=ExecutionRightMode.UNSUPPORTED_BOUNDARY),
])
def test_missing_required_dependency_and_unsupported_right_fail_at_creation(spec):
    c, s = harness()
    s.pending_work_system.register_dispatcher("work", lambda *_: None)
    with pytest.raises(ValueError, match="creation execution right denied"):
        queue(c, s, "work", execution_right_spec=spec)
    assert c.pending_work.all() == () and c.pending_work.trace == ()


def test_repeat_off_by_one_route_is_explicit_unsupported_boundary():
    with pytest.raises(NotImplementedError):
        WorkLifetimeSpec(WorkLifetimeKind.REPEAT_N_TIMES)


def test_scheduler_has_no_domain_math_mutation_random_or_event_authority():
    root = Path(__file__).resolve().parents[1] / "sgs_v2" / "battle_core"
    tree = ast.parse((root / "pending_work.py").read_text(encoding="utf-8"))
    forbidden_imports = {"random", "uuid", "damage_system", "recovery_system", "treatment_formula", "target_system", "events"}
    imports = {node.module.rsplit(".", 1)[-1] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    imports |= {item.name for node in ast.walk(tree) if isinstance(node, ast.Import) for item in node.names}
    assert not imports & forbidden_imports
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            assert not any(isinstance(target, ast.Attribute) and target.attr in ("troops", "wounded_troops", "states", "ended", "result") for target in targets)
        if isinstance(node, ast.BinOp):
            assert not isinstance(node.op, (ast.Mult, ast.Div, ast.FloorDiv, ast.Pow))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in ("random", "randint", "sample", "shuffle", "publish", "restore", "apply_damage")


def test_domain_owner_source_files_untouched_relative_to_frozen_baseline():
    # Structural seam test complements the independent command's baseline hashes.
    root = Path(__file__).resolve().parents[1] / "sgs_v2" / "battle_core"
    for name in ("damage_system.py", "recovery_system.py", "state_lifecycle_system.py", "random_system.py"):
        assert "PendingWorkSystem" not in (root / name).read_text(encoding="utf-8")
