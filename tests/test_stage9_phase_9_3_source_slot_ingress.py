from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    ApplyStateEffect,
    ApplyStateSkillEffectSpec,
    BattleContext,
    BattlePhase,
    DamageEffect,
    DamageSkillEffectSpec,
    DamageType,
    EffectExecutor,
    EffectSourceRef,
    EmptyStateRuntimeParams,
    EventBus,
    GuardStateParams,
    LineupPosition,
    LoadedSkillRef,
    LoadedSkillSet,
    OfficialStateId,
    RandomSystem,
    SkillDefinition,
    SkillResolver,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SourceType,
    Stage9StateRuntime,
    StateDefinition,
    StateInstance,
    StateLifecycleSystem,
    StateRegistry,
    TauntStateParams,
    UnitRuntime,
    register_official_state_definitions,
)


def make_skill_def(skill_id: str = "test_sk_01") -> SkillDefinition:
    return SkillDefinition(
        skill_id=skill_id,
        name="测试战法",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SINGLE_RANDOM_ENEMY,
        effect_specs=(
            DamageSkillEffectSpec(DamageType.WEAPON, 1.5),
            ApplyStateSkillEffectSpec("test_buff"),
        ),
    )


def make_context() -> BattleContext:
    units = {
        "a1": UnitRuntime(
            "a1", "武将A1", "A", 1000, 1000, 100, 100, 100,
            lineup_position=LineupPosition.COMMANDER,
        ),
        "b1": UnitRuntime(
            "b1", "武将B1", "B", 1000, 1000, 100, 100, 90,
            lineup_position=LineupPosition.COMMANDER,
        ),
    }
    context = BattleContext(
        battle_id="test-source-slot",
        units=units,
        event_bus=EventBus(),
        random=RandomSystem(123),
    )
    context.current_round = 1
    context.current_phase = BattlePhase.UNIT_ACTION.value
    return context


class TestSourceSlotIngress:
    """Tests for holder-specific skill slot ingress, provenance propagation, and guards."""

    def test_loaded_skill_ref_to_skill_runtime_from_loaded(self) -> None:
        sk_def = make_skill_def()
        ref = LoadedSkillRef(
            owner_id="a1",
            definition=sk_def,
            skill_slot=SkillSlot.LEARNED_1,
        )

        runtime = SkillRuntime.from_loaded(ref)
        assert runtime.definition == sk_def
        assert runtime.owner_id == "a1"
        assert runtime.skill_slot == SkillSlot.LEARNED_1
        assert runtime.enabled is True

        # from_loaded rejects non-LoadedSkillRef
        with pytest.raises(TypeError, match="LoadedSkillRef"):
            SkillRuntime.from_loaded("not_a_ref")  # type: ignore[arg-type]

    def test_duplicate_same_holder_same_slot_rejected(self) -> None:
        sk1 = make_skill_def("sk1")
        sk2 = make_skill_def("sk2")

        ref1 = LoadedSkillRef(owner_id="a1", definition=sk1, skill_slot=SkillSlot.LEARNED_1)
        ref2 = LoadedSkillRef(owner_id="a1", definition=sk2, skill_slot=SkillSlot.LEARNED_1)

        with pytest.raises(ValueError, match="Duplicate SkillSlot"):
            LoadedSkillSet(owner_id="a1", loaded=(ref1, ref2))

    def test_different_holders_same_slot_allowed(self) -> None:
        sk1 = make_skill_def("sk1")
        sk2 = make_skill_def("sk2")

        ref_a = LoadedSkillRef(owner_id="a1", definition=sk1, skill_slot=SkillSlot.INHERENT)
        ref_b = LoadedSkillRef(owner_id="b1", definition=sk2, skill_slot=SkillSlot.INHERENT)

        set_a = LoadedSkillSet(owner_id="a1", loaded=(ref_a,))
        set_b = LoadedSkillSet(owner_id="b1", loaded=(ref_b,))

        assert set_a.loaded[0].skill_slot == SkillSlot.INHERENT
        assert set_b.loaded[0].skill_slot == SkillSlot.INHERENT

    def test_no_skill_id_slot_inference(self) -> None:
        sk = make_skill_def("sk_slot_1")
        # Legacy/external runtime without slot must stay None
        runtime = SkillRuntime(definition=sk, owner_id="a1")
        assert runtime.skill_slot is None

    def test_skill_resolver_produces_active_skill_source_ref(self) -> None:
        context = make_context()
        sk_def = make_skill_def("sk_active")
        ref = LoadedSkillRef(
            owner_id="a1",
            definition=sk_def,
            skill_slot=SkillSlot.LEARNED_2,
        )
        runtime = SkillRuntime.from_loaded(ref)

        from sgs_v2.battle_core import TargetSystem
        resolver = SkillResolver(TargetSystem())
        result = resolver.resolve(context, runtime)

        assert result.status.value == "RESOLVED"
        assert len(result.effects) == 2

        dmg_effect = result.effects[0]
        assert isinstance(dmg_effect, DamageEffect)
        assert dmg_effect.source_ref is not None
        assert dmg_effect.source_ref.stage9_source_type == SourceType.ACTIVE_SKILL
        assert dmg_effect.source_ref.source_unit_id == "a1"
        assert dmg_effect.source_ref.source_skill_id == "sk_active"
        assert dmg_effect.source_ref.source_skill_slot == SkillSlot.LEARNED_2
        assert dmg_effect.source_id == "a1"
        assert dmg_effect.source_skill_id == "sk_active"

        state_effect = result.effects[1]
        assert isinstance(state_effect, ApplyStateEffect)
        assert state_effect.source_ref is not None
        assert state_effect.source_ref.stage9_source_type == SourceType.ACTIVE_SKILL
        assert state_effect.source_ref.source_unit_id == "a1"
        assert state_effect.source_ref.source_skill_id == "sk_active"
        assert state_effect.source_ref.source_skill_slot == SkillSlot.LEARNED_2
        assert state_effect.source_id == "a1"
        assert state_effect.source_skill_id == "sk_active"

    def test_state_instance_source_skill_slot_persistence(self) -> None:
        context = make_context()
        context.states.register_definition(StateDefinition(state_id="test_buff", name="测试状态"))
        lifecycle = StateLifecycleSystem()

        instance = lifecycle.apply(
            context,
            state_id="test_buff",
            owner_id="b1",
            source_id="a1",
            source_skill_id="sk_01",
            source_skill_slot=SkillSlot.LEARNED_1,
        )

        assert instance.source_skill_slot == SkillSlot.LEARNED_1
        # Check that event payload includes source_skill_slot
        event = context.event_bus.history[-1]
        assert event.payload["source_skill_slot"] == SkillSlot.LEARNED_1

    def test_apply_state_effect_executor_forwarding(self) -> None:
        context = make_context()
        context.states.register_definition(StateDefinition(state_id="test_buff", name="测试状态"))
        lifecycle = StateLifecycleSystem()

        from sgs_v2.battle_core import (
            AttributeSystem,
            DamageResolutionSystem,
            DamageSystem,
            TroopSystem,
        )
        executor = EffectExecutor(
            damage_resolution_system=DamageResolutionSystem(
                DamageSystem(AttributeSystem()),
                TroopSystem(),
            ),
            state_lifecycle_system=lifecycle,
        )

        effect = ApplyStateEffect(
            state_id="test_buff",
            owner_id="b1",
            source_id="a1",
            source_skill_id="sk_01",
            source_ref=EffectSourceRef(
                stage9_source_type=SourceType.ACTIVE_SKILL,
                source_unit_id="a1",
                source_skill_id="sk_01",
                source_skill_slot=SkillSlot.INHERENT,
            ),
        )

        result = executor.execute(context, effect)
        assert result.state_instance is not None
        saved = context.states.find(owner_id="b1", state_id="test_buff")[0]
        assert saved.source_skill_slot == SkillSlot.INHERENT

    def test_same_source_same_slot_reapply_compatible(self) -> None:
        context = make_context()
        context.states.register_definition(StateDefinition(state_id="burn", name="灼烧"))
        lifecycle = StateLifecycleSystem()

        inst1 = lifecycle.apply(
            context,
            state_id="burn",
            owner_id="b1",
            source_id="a1",
            source_skill_id="fire_attack",
            source_skill_slot=SkillSlot.LEARNED_1,
        )
        assert inst1.source_skill_slot == SkillSlot.LEARNED_1

        # Same source identity and same slot -> compatible
        inst2 = lifecycle.apply(
            context,
            state_id="burn",
            owner_id="b1",
            source_id="a1",
            source_skill_id="fire_attack",
            source_skill_slot=SkillSlot.LEARNED_1,
        )
        assert inst2.source_skill_slot == SkillSlot.LEARNED_1

    def test_same_source_slot_mismatch_rejected_domain_error(self) -> None:
        context = make_context()
        context.states.register_definition(StateDefinition(state_id="burn", name="灼烧"))
        lifecycle = StateLifecycleSystem()

        inst1 = lifecycle.apply(
            context,
            state_id="burn",
            owner_id="b1",
            source_id="a1",
            source_skill_id="fire_attack",
            source_skill_slot=SkillSlot.LEARNED_1,
        )
        assert inst1.source_skill_slot == SkillSlot.LEARNED_1

        # Same source identity but different slot -> DOMAIN ERROR (ValueError)
        with pytest.raises(ValueError, match="same-source reapply slot mismatch"):
            lifecycle.apply(
                context,
                state_id="burn",
                owner_id="b1",
                source_id="a1",
                source_skill_id="fire_attack",
                source_skill_slot=SkillSlot.LEARNED_2,
            )

        # Original StateInstance in registry remains unchanged
        existing_list = context.states.find(owner_id="b1", state_id="burn")
        assert len(existing_list) == 1
        assert existing_list[0].source_skill_slot == SkillSlot.LEARNED_1

    def test_official_state_catalog_runtime_params_wiring(self) -> None:
        registry = StateRegistry()
        register_official_state_definitions(registry)

        taunt_def = registry.get_definition(OfficialStateId.TAUNT.value)
        assert taunt_def.runtime_params_type == TauntStateParams

        guard_def = registry.get_definition(OfficialStateId.GUARD.value)
        assert guard_def.runtime_params_type == GuardStateParams

        context = make_context()
        context.states = registry
        lifecycle = StateLifecycleSystem()

        # Correct params accepted
        t_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.TAUNT.value,
            owner_id="a1",
            source_id="b1",
            runtime_params=TauntStateParams(taunt_target_id="b1"),
        )
        assert isinstance(t_inst.runtime_params, TauntStateParams)

        g_inst = lifecycle.apply(
            context,
            state_id=OfficialStateId.GUARD.value,
            owner_id="b1",
            source_id="a1",
            runtime_params=GuardStateParams(protector_id="a1"),
        )
        assert isinstance(g_inst.runtime_params, GuardStateParams)

        # Incorrect params rejected
        with pytest.raises(TypeError, match="runtime_params type mismatch"):
            lifecycle.apply(
                context,
                state_id=OfficialStateId.TAUNT.value,
                owner_id="a1",
                source_id="b1",
                runtime_params=EmptyStateRuntimeParams(),
            )

        with pytest.raises(TypeError, match="runtime_params type mismatch"):
            lifecycle.apply(
                context,
                state_id=OfficialStateId.GUARD.value,
                owner_id="b1",
                source_id="b1",
                runtime_params=EmptyStateRuntimeParams(),
            )

    def test_stage9_state_runtime_adapter_architecture(self) -> None:
        context = make_context()
        register_official_state_definitions(context.states)
        lifecycle = StateLifecycleSystem()
        adapter = Stage9StateRuntime(state_lifecycle_system=lifecycle)

        # Adapter reads directly from context.states
        assert adapter.lifecycle == lifecycle

        # Apply state through lifecycle
        lifecycle.apply(
            context,
            state_id=OfficialStateId.CONFUSION.value,
            owner_id="a1",
            source_id="b1",
        )

        conf = adapter.get_operational_confusion(context, "a1")
        assert conf is not None
        assert conf.state_id == OfficialStateId.CONFUSION.value
        assert conf.owner_id == "a1"

        # Adapter has no second storage
        assert not hasattr(adapter, "_instances")
        assert not hasattr(adapter, "_states")
