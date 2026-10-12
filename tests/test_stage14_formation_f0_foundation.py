from __future__ import annotations

import pytest

from sgs_v2.battle_core import (
    BattleContext,
    BattleEngine,
    BattlePhase,
    BattleSystems,
    DamageModifierContribution,
    DamageModifierKind,
    DamageModifierOperation,
    DamageModifierPhase,
    DamageRequest,
    DamageSourceType,
    DamageType,
    EventBus,
    EventType,
    LineupPosition,
    RandomSystem,
    SkillDefinition,
    SkillRuntime,
    SkillSlot,
    SkillTargetMode,
    SkillType,
    TroopType,
    UnitRuntime,
    admit_and_install_formation_skill,
    register_formation_skill_config,
    unregister_formation_skill_config,
    FormationAdmissionRejectedError,
    FormationAdmissionResult,
    FormationAdmissionStatus,
    FormationSkillConfig,
    PreBattleOrderSystem,
    run_pre_battle_preparation_phases,
    register_pre_battle_passive_processor,
    unregister_pre_battle_passive_processor,
    register_pre_battle_command_processor,
    unregister_pre_battle_command_processor,
)
from sgs_v2.battle_core.skill_runtime_registry import SkillRuntimeRegistry
from sgs_v2.battle_core.state_modifiers import (
    ATTRIBUTE_BONUS_STATE_ID,
    INCOMING_DAMAGE_REDUCTION_STATE_ID,
    AttributeBonusParams,
    IncomingDamageReductionParams,
    register_modifier_state_definitions,
)
from sgs_v2.battle_core.skill_definition import ApplyStateSkillEffectSpec


# Synthetic Formation IDs purely for tests (NO real gameplay like Feng Shi Zhen or Ba Men)
SYNTHETIC_FORMATION_1_ID = "99001"
SYNTHETIC_FORMATION_2_ID = "99002"
SYNTHETIC_FORMATION_SHIELD_ID = "99003"


def _make_unit(
    unit_id: str,
    team_id: str,
    *,
    speed: float = 100.0,
    lineup_position: LineupPosition = LineupPosition.COMMANDER,
    troop_type: TroopType = TroopType.CAVALRY,
    troops: int = 1000,
    attack: float = 200.0,
    defense: float = 100.0,
    intelligence: float = 100.0,
) -> UnitRuntime:
    return UnitRuntime(
        unit_id=unit_id,
        name=f"Unit_{unit_id}",
        team_id=team_id,
        max_troops=troops,
        troops=troops,
        attack=attack,
        defense=defense,
        speed=speed,
        lineup_position=lineup_position,
        troop_type=troop_type,
        intelligence=intelligence,
    )


def _make_context(
    units: list[UnitRuntime],
    *,
    attacker_team_id: str | None = None,
) -> tuple[BattleContext, BattleSystems]:
    from sgs_v2.battle_core.official_state_catalog import register_official_state_definitions

    bus = EventBus()
    unit_map = {u.unit_id: u for u in units}
    # Ensure at least two teams exist in context
    team_ids = {u.team_id for u in units}
    if len(team_ids) < 2:
        dummy = _make_unit("__dummy_b__", "__team_dummy_B__")
        unit_map[dummy.unit_id] = dummy

    ctx = BattleContext(
        battle_id="test_formation_foundation",
        units=unit_map,
        event_bus=bus,
        random=RandomSystem(42),
    )
    if attacker_team_id is not None:
        ctx.metadata["attacker_team_id"] = attacker_team_id
    systems = BattleSystems()
    register_official_state_definitions(ctx.states)
    register_modifier_state_definitions(ctx.states)
    return ctx, systems


# Setup synthetic definitions
def _create_synthetic_formation_def_1() -> SkillDefinition:
    return SkillDefinition(
        skill_id=SYNTHETIC_FORMATION_1_ID,
        name="测试阵法壹",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SELF,
        effect_specs=(
            ApplyStateSkillEffectSpec(
                ATTRIBUTE_BONUS_STATE_ID,
                AttributeBonusParams("attack", 30.0),
            ),
        ),
        skill_type=SkillType.FORMATION,
    )


def _create_synthetic_formation_def_2() -> SkillDefinition:
    return SkillDefinition(
        skill_id=SYNTHETIC_FORMATION_2_ID,
        name="测试阵法贰",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SELF,
        effect_specs=(
            ApplyStateSkillEffectSpec(
                ATTRIBUTE_BONUS_STATE_ID,
                AttributeBonusParams("defense", 25.0),
            ),
        ),
        skill_type=SkillType.FORMATION,
    )


def _create_synthetic_formation_def_shield() -> SkillDefinition:
    return SkillDefinition(
        skill_id=SYNTHETIC_FORMATION_SHIELD_ID,
        name="测试盾兵专属阵法",
        activation_rate=1.0,
        target_mode=SkillTargetMode.SELF,
        effect_specs=(
            ApplyStateSkillEffectSpec(
                ATTRIBUTE_BONUS_STATE_ID,
                AttributeBonusParams("defense", 40.0),
            ),
        ),
        skill_type=SkillType.FORMATION,
    )


@pytest.fixture(autouse=True)
def setup_and_teardown_synthetic_formations():
    register_formation_skill_config(
        FormationSkillConfig(
            skill_id=SYNTHETIC_FORMATION_1_ID,
            name="测试阵法壹",
            applicable_troops=(TroopType.CAVALRY, TroopType.SHIELD, TroopType.SPEAR),
            definition_factory=_create_synthetic_formation_def_1,
        )
    )
    register_formation_skill_config(
        FormationSkillConfig(
            skill_id=SYNTHETIC_FORMATION_2_ID,
            name="测试阵法贰",
            applicable_troops=(TroopType.CAVALRY, TroopType.SHIELD, TroopType.BOW),
            definition_factory=_create_synthetic_formation_def_2,
        )
    )
    register_formation_skill_config(
        FormationSkillConfig(
            skill_id=SYNTHETIC_FORMATION_SHIELD_ID,
            name="测试盾兵专属阵法",
            applicable_troops=(TroopType.SHIELD,),
            definition_factory=_create_synthetic_formation_def_shield,
        )
    )
    yield
    unregister_formation_skill_config(SYNTHETIC_FORMATION_1_ID)
    unregister_formation_skill_config(SYNTHETIC_FORMATION_2_ID)
    unregister_formation_skill_config(SYNTHETIC_FORMATION_SHIELD_ID)


# =========================================================================
# F0-I-A-01: 阵法注册基础 (SkillRuntime & Canonical Registry)
# =========================================================================

def test_formation_registration_and_lookup():
    """Verify formation recognition strictly via SkillType.FORMATION and canonical skill ID."""
    u = _make_unit("a1", "team_A")
    ctx, systems = _make_context([u])

    defn = _create_synthetic_formation_def_1()
    runtime = SkillRuntime(defn, owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(runtime)

    looked_up = ctx.skill_runtimes.lookup("a1", SkillSlot.LEARNED_1, expected_skill_id=SYNTHETIC_FORMATION_1_ID)
    assert looked_up is runtime
    assert looked_up.definition.skill_type == SkillType.FORMATION

    # Rejection of duplicate slot
    with pytest.raises(ValueError, match="Duplicate SkillRuntime registration"):
        ctx.skill_runtimes.register(runtime)


# =========================================================================
# F0-I-A-02: 准入与互斥 (RULE-03: Team Formation Limit & Atomic Admission)
# =========================================================================

def test_team_formation_limit_single_allowed():
    """RULE-03: Team with 0 or 1 formation is admitted."""
    u1 = _make_unit("a1", "team_A")
    u2 = _make_unit("a2", "team_A", lineup_position=LineupPosition.DEPUTY_1)
    ctx, systems = _make_context([u1, u2], attacker_team_id="team_A")

    rt = SkillRuntime(_create_synthetic_formation_def_1(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt)

    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    result = admit_and_install_formation_skill(ctx, systems, rt)
    assert result.status == FormationAdmissionStatus.SUCCESS


def test_team_formation_limit_multiple_fail_closed():
    """RULE-03: Team with 2 formations fails closed before installation."""
    u1 = _make_unit("a1", "team_A")
    u2 = _make_unit("a2", "team_A", lineup_position=LineupPosition.DEPUTY_1)
    ctx, systems = _make_context([u1, u2], attacker_team_id="team_A")

    rt1 = SkillRuntime(_create_synthetic_formation_def_1(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    rt2 = SkillRuntime(_create_synthetic_formation_def_2(), owner_id="a2", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt1)
    ctx.skill_runtimes.register(rt2)

    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    # Individual admission should reject due to team limit
    result = admit_and_install_formation_skill(ctx, systems, rt1)
    assert result.status == FormationAdmissionStatus.REJECTED_TEAM_FORMATION_EXCEEDED

    # Engine run fails closed at pre-battle preflight
    engine = BattleEngine(ctx, systems)
    with pytest.raises(FormationAdmissionRejectedError, match="exceeds formation limit"):
        engine.run()

    # Zero side effects: no state applied
    assert len(ctx.states.find()) == 0


def test_independent_formations_both_teams_admitted():
    """RULE-03: Both Attacker and Defender can each have 1 formation independently."""
    u_a = _make_unit("a1", "team_A")
    u_b = _make_unit("b1", "team_B")
    ctx, systems = _make_context([u_a, u_b], attacker_team_id="team_A")

    rt_a = SkillRuntime(_create_synthetic_formation_def_1(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    rt_b = SkillRuntime(_create_synthetic_formation_def_2(), owner_id="b1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt_a)
    ctx.skill_runtimes.register(rt_b)

    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    res_a = admit_and_install_formation_skill(ctx, systems, rt_a)
    res_b = admit_and_install_formation_skill(ctx, systems, rt_b)
    assert res_a.status == FormationAdmissionStatus.SUCCESS
    assert res_b.status == FormationAdmissionStatus.SUCCESS


def test_formation_troop_incompatibility_rejected():
    """Formation admission rejects when team troop type does not match applicable troops."""
    u = _make_unit("a1", "team_A", troop_type=TroopType.BOW)  # not shield
    ctx, systems = _make_context([u], attacker_team_id="team_A")

    rt = SkillRuntime(_create_synthetic_formation_def_shield(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt)

    ctx.current_phase = BattlePhase.PRE_BATTLE.value
    res = admit_and_install_formation_skill(ctx, systems, rt)
    assert res.status == FormationAdmissionStatus.REJECTED_INVALID_TROOP
    assert len(ctx.states.find()) == 0


# =========================================================================
# F0-I-A-03: 准备阶段全局四阶段顺序 (RULE-01)
# =========================================================================

def test_four_stage_pre_battle_global_order_trace():
    """RULE-01: Execution follows PASSIVE -> FORMATION -> TROOP -> COMMAND.
    Verified with an execution trace across all 4 stages.
    """
    u_a = _make_unit("a1", "team_A", speed=150.0)
    u_b = _make_unit("b1", "team_B", speed=200.0)
    ctx, systems = _make_context([u_a, u_b], attacker_team_id="team_A")

    trace: list[str] = []

    # Stage 1: PASSIVE hook
    def passive_hook(c, s):
        trace.append("STAGE_1_PASSIVE")
    register_pre_battle_passive_processor(passive_hook)

    # Stage 2: Formation runtime
    rt_formation = SkillRuntime(_create_synthetic_formation_def_1(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt_formation)

    # Monitor states applied to see when formation executes
    def on_state_applied(event):
        if event.payload.get("state_id") == ATTRIBUTE_BONUS_STATE_ID:
            trace.append("STAGE_2_FORMATION")
    ctx.event_bus.subscribe(EventType.STATE_APPLIED, on_state_applied)

    # Stage 3: Troop skill runtime (Xiliang Cavalry)
    from sgs_v2.battle_core.troop_admission import create_xiliang_cavalry_runtime
    rt_troop = create_xiliang_cavalry_runtime("b1", slot=SkillSlot.LEARNED_2)
    ctx.skill_runtimes.register(rt_troop)

    # Monitor troop state applied
    def on_troop_applied(event):
        if event.payload.get("state_id") == "critical":
            trace.append("STAGE_3_TROOP")
    ctx.event_bus.subscribe(EventType.STATE_APPLIED, on_troop_applied)

    # Stage 4: COMMAND hook
    def command_hook(c, s):
        trace.append("STAGE_4_COMMAND")
    register_pre_battle_command_processor(command_hook)

    try:
        ctx.current_phase = BattlePhase.PRE_BATTLE.value
        run_pre_battle_preparation_phases(ctx, systems)

        assert trace == [
            "STAGE_1_PASSIVE",
            "STAGE_2_FORMATION",
            "STAGE_3_TROOP",
            "STAGE_4_COMMAND",
        ]
    finally:
        unregister_pre_battle_passive_processor(passive_hook)
        unregister_pre_battle_command_processor(command_hook)


# =========================================================================
# F0-I-A-04: 准备阶段速度与同速进攻方优先 (RULE-04)
# =========================================================================

def test_pre_battle_speed_order_attacker_priority_on_tie():
    """RULE-04: Speed descending order; when equal speed, attacker first."""
    order_sys = PreBattleOrderSystem(BattleSystems().attribute_system)

    # 1. Attacker faster
    u_atk = _make_unit("a1", "team_A", speed=150.0)
    u_def = _make_unit("b1", "team_B", speed=100.0)
    ctx, _ = _make_context([u_atk, u_def], attacker_team_id="team_A")
    order = order_sys.determine_order(ctx, units=[u_atk, u_def])
    assert [u.unit_id for u in order] == ["a1", "b1"]

    # 2. Defender faster
    u_atk.speed = 100.0
    u_def.speed = 150.0
    order = order_sys.determine_order(ctx, units=[u_atk, u_def])
    assert [u.unit_id for u in order] == ["b1", "a1"]

    # 3. Same speed tie: attacker first
    u_atk.speed = 120.0
    u_def.speed = 120.0
    order = order_sys.determine_order(ctx, units=[u_atk, u_def])
    assert [u.unit_id for u in order] == ["a1", "b1"]

    # 4. Same team intra-team tie: commander before deputy
    u_atk2 = _make_unit("a2", "team_A", speed=120.0, lineup_position=LineupPosition.DEPUTY_1)
    ctx2, _ = _make_context([u_atk2, u_atk], attacker_team_id="team_A")
    order2 = order_sys.determine_order(ctx2, units=[u_atk2, u_atk])
    assert [u.unit_id for u in order2] == ["a1", "a2"]


def test_pre_battle_speed_order_missing_attacker_fallback():
    """RULE-04: If attacker_team_id is missing or invalid, stable deterministic order without crashing."""
    order_sys = PreBattleOrderSystem(BattleSystems().attribute_system)
    u1 = _make_unit("a1", "team_A", speed=120.0)
    u2 = _make_unit("b1", "team_B", speed=120.0)
    ctx, _ = _make_context([u1, u2], attacker_team_id=None)

    order = order_sys.determine_order(ctx)
    assert len(order) == 2
    # Deterministic sorting
    order_again = order_sys.determine_order(ctx)
    assert [u.unit_id for u in order] == [u.unit_id for u in order_again]


# =========================================================================
# F0-I-A-05 & F0-I-A-06: 阵法来源绑定与携带者阵亡持续效果清理 (RULE-02)
# =========================================================================

def test_formation_provider_death_cleans_active_formation_effects():
    """RULE-02: When formation provider dies, its active formation effects on self/allies/enemies
    are immediately removed, while other skill modifiers remain intact.
    """
    u_provider = _make_unit("a1", "team_A", troops=500)
    u_ally = _make_unit("a2", "team_A", lineup_position=LineupPosition.DEPUTY_1, troops=1000)
    u_enemy = _make_unit("b1", "team_B", troops=1000)

    ctx, systems = _make_context([u_provider, u_ally, u_enemy], attacker_team_id="team_A")
    ctx.current_phase = BattlePhase.PRE_BATTLE.value

    # Formation runtime provided by a1
    rt_formation = SkillRuntime(_create_synthetic_formation_def_1(), owner_id="a1", skill_slot=SkillSlot.LEARNED_1)
    ctx.skill_runtimes.register(rt_formation)

    # Apply formation effects:
    # 1. Attribute bonus on provider
    # 2. Incoming damage reduction on ally (provided by a1)
    # 3. Attribute bonus on enemy (provided by a1)
    # 1. Attribute bonus on provider (attack +30)
    # 2. Incoming damage reduction on ally (20% reduction provided by a1)
    # 3. Attribute modifier on enemy (defense -15 provided by a1)
    # 4. Outgoing damage increase / general persistent state provided by a1 to ally
    # 5. Non-formation modifier from another skill
    from sgs_v2.battle_core.official_state_catalog import OfficialStateId

    systems.state_lifecycle_system.apply(
        ctx,
        state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="a1",
        source_id="a1",
        source_skill_id=SYNTHETIC_FORMATION_1_ID,
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params=AttributeBonusParams("attack", 30.0),
    )
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=INCOMING_DAMAGE_REDUCTION_STATE_ID,
        owner_id="a2",
        source_id="a1",
        source_skill_id=SYNTHETIC_FORMATION_1_ID,
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params=IncomingDamageReductionParams(DamageType.WEAPON, 0.20),
    )
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="b1",
        source_id="a1",
        source_skill_id=SYNTHETIC_FORMATION_1_ID,
        source_skill_slot=SkillSlot.LEARNED_1,
        runtime_params=AttributeBonusParams("defense", -15.0),
    )
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=OfficialStateId.BURN.value,
        owner_id="b1",
        source_id="a1",
        source_skill_id=SYNTHETIC_FORMATION_1_ID,
        source_skill_slot=SkillSlot.LEARNED_1,
        duration_rounds=3,
    )

    # Apply an UNRELATED effect from another skill on ally a2 (e.g., self buff or command)
    systems.state_lifecycle_system.apply(
        ctx,
        state_id=ATTRIBUTE_BONUS_STATE_ID,
        owner_id="a2",
        source_id="a2",
        source_skill_id="OTHER_SKILL_123",
        source_skill_slot=SkillSlot.LEARNED_2,
        runtime_params=AttributeBonusParams("defense", 50.0),
    )

    # Initial assertion: all 5 states exist
    assert len(ctx.states.find(owner_id="a1")) == 1
    assert len(ctx.states.find(owner_id="a2")) == 2
    assert len(ctx.states.find(owner_id="b1")) == 2

    # Kill provider a1 via direct troop loss / damage resolution commit_defeat
    ctx.current_phase = BattlePhase.UNIT_ACTION.value
    u_provider.troops = 0
    assert not u_provider.is_alive

    # Commit defeat via DefeatCleanupPort
    res = systems.defeat_cleanup_port.commit_defeat(ctx, "a1", defeat_source_ref="lethal_hit")

    # Assertions:
    # 1. SkillRuntime in registry is NOT deleted (Invariant preserved!)
    assert ctx.skill_runtimes.contains("a1", SkillSlot.LEARNED_1)

    # 2. a1's own states removed
    assert len(ctx.states.find(owner_id="a1")) == 0

    # 3. a2's formation state provided by a1 is removed!
    a2_states = ctx.states.find(owner_id="a2")
    assert len(a2_states) == 1
    assert a2_states[0].source_skill_id == "OTHER_SKILL_123"  # Non-formation effect PRESERVED!

    # 4. b1's formation states provided by a1 are all removed!
    assert len(ctx.states.find(owner_id="b1")) == 0

    # 5. Events published with reason PROVIDER_DEFEATED
    provider_defeat_events = [
        e for e in ctx.event_bus.history
        if e.event_type == EventType.STATE_REMOVED and e.payload.get("removal_reason") == "PROVIDER_DEFEATED"
    ]
    assert len(provider_defeat_events) == 3  # a2 reduction, b1 attribute, b1 burn


# =========================================================================
# F0-I-A-07: 无阵法时零副作用与兵种完全兼容
# =========================================================================

def test_no_formation_battle_executes_identically():
    """Verify that battles without formations proceed normally without error."""
    u_a = _make_unit("a1", "team_A", speed=100.0)
    u_b = _make_unit("b1", "team_B", speed=80.0)
    ctx, systems = _make_context([u_a, u_b], attacker_team_id="team_A")

    engine = BattleEngine(ctx, systems)
    res = engine.run()
    assert res is not None
    assert ctx.ended
