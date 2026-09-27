from __future__ import annotations

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    EmptyStateRuntimeParams,
    EventBus,
    LineupPosition,
    RandomSystem,
    SkillSlot,
    StateCandidate,
    StateDefinition,
    StateNode,
    UnitRuntime,
)


def _context() -> BattleContext:
    context = BattleContext(
        battle_id="stage12-completion-audit",
        units={
            "a": UnitRuntime(
                "a", "A", "A", 1000, 1000, 100, 100, 100,
                lineup_position=LineupPosition.COMMANDER,
            ),
            "b": UnitRuntime(
                "b", "B", "B", 1000, 1000, 100, 100, 90,
                lineup_position=LineupPosition.COMMANDER,
            ),
        },
        event_bus=EventBus(),
        random=RandomSystem(1204),
    )
    context.current_phase = BattlePhase.PRE_BATTLE.value
    for state_id in ("audit-cause", "audit-target"):
        context.states.register_definition(
            StateDefinition(
                state_id=state_id,
                name=state_id,
                runtime_params_type=EmptyStateRuntimeParams,
            )
        )
    return context


def _candidate(state_id: str) -> StateCandidate:
    return StateCandidate(
        state_id=state_id,
        owner_id="b",
        source_id="a",
        source_skill_id="audit-source",
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params_candidate=EmptyStateRuntimeParams(),
        application_provenance="stage12-completion-audit",
    )


def test_finalization_coordinator_uses_canonical_transition_coordinator() -> None:
    systems = BattleSystems()
    assert (
        systems.finalization_coordinator.effectiveness_transition_coordinator
        is systems.effectiveness_transition_coordinator
    )


def test_battle_teardown_cleans_dependency_graph() -> None:
    context = _context()
    systems = BattleSystems()
    cause = systems.state_application_coordinator.apply_candidate(
        context, _candidate("audit-cause")
    ).instance
    target = systems.state_application_coordinator.apply_candidate(
        context, _candidate("audit-target")
    ).instance
    assert cause is not None and target is not None

    cause_node = StateNode(cause.instance_id)
    target_node = StateNode(target.instance_id)
    systems.dependency_evaluation_support.add_dependency(target_node, cause_node)

    # Exercise the real production finalization path, not a direct Lifecycle test.
    context.units["b"].troops = 0
    BattleEngine(context, systems).run()

    assert context.states.find() == []
    assert systems.dependency_evaluation_support.prerequisites(target_node) == ()
    assert systems.dependency_evaluation_support.dependents(cause_node) == ()
