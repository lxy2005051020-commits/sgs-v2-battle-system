from dataclasses import replace
import pytest
from tests.test_stage14_wu_feng_zhen import scene, install, act
from sgs_v2.battle_core import (SkillRuntime, SkillSlot, DamageType, DamageRequest,
    DamageSourceType, BattlePhase, create_wu_feng_zhen_runtime, BattleEngine, RecoveryTargetMode)
from sgs_v2.battle_core.skill_definition import (SkillDefinition, SkillTargetMode, SkillType,
                                               DamageSkillEffectSpec)
from sgs_v2.battle_core.probabilistic_target_priority import (TARGET_PRIORITY_STATE_ID,
    QueryBoundDamageEffect, TargetPriorityParams)
from sgs_v2.battle_core.rule_hooks import RoundStartHook
from sgs_v2.battle_core.effects import RemoveStateEffect, ApplyStateEffect
from sgs_v2.battle_core.state_modifiers import ATTRIBUTE_BONUS_STATE_ID, AttributeBonusParams, register_modifier_state_definitions


def setup(monkeypatch, *, success=True, provider=0, dtype=DamageType.WEAPON,
          mode=SkillTargetMode.SINGLE_RANDOM_ENEMY, count=None, rounds=1):
    ctx, s, rt = scene(provider=provider, mode=RecoveryTargetMode.RANDOM_ALLIES)
    rt.definition = create_wu_feng_zhen_runtime(rt.owner_id).definition
    install(ctx, s, rt)
    ctx.current_round = rounds
    ctx.current_phase = BattlePhase.UNIT_ACTION.value
    calls = []
    def chance(probability):
        calls.append(probability)
        return success
    monkeypatch.setattr(ctx.random, "chance", chance)
    hostile = SkillRuntime(SkillDefinition("test_hostile", "hostile", 1,
        mode, (DamageSkillEffectSpec(dtype),), target_count=count), "b0", SkillSlot.INHERENT)
    ctx.skill_runtimes.register(hostile)
    return ctx, s, rt, hostile, calls


@pytest.mark.parametrize("command,rate", [(100,.30), (200,.40), (350,.55)])
@pytest.mark.parametrize("dtype", list(DamageType))
def test_user_formula_live_main_command_and_bound_production_damage(monkeypatch, command, rate, dtype):
    ctx, s, rt, hostile, calls = setup(monkeypatch, dtype=dtype, provider=1)
    ctx.units["a0"].defense = 100  # Resolution does not freeze command.
    res = s.skill_resolver.resolve(ctx, hostile)
    assert res.target_ids == ("a0",)
    assert calls == [.8]
    assert isinstance(res.effects[0], QueryBoundDamageEffect)
    ctx.units["a0"].defense = command
    ctx.units[rt.owner_id].defense = 999  # Reads commander, not formation carrier.
    result = s.effect_executor.execute(ctx, res.effects[0])
    modifiers = result.resolution.damage.pipeline_trace.modifier_result.applied_modifiers
    own = [m.contribution for m in modifiers if m.contribution.source.source_skill_id == "22031"]
    assert len(own) == 1
    assert own[0].operand == pytest.approx(1-rate)


def test_effective_attribute_modifier_is_read_at_damage_time(monkeypatch):
    ctx, s, rt, hostile, _ = setup(monkeypatch)
    ctx.units["a0"].defense = 100
    effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
    register_modifier_state_definitions(ctx.states)
    s.effect_executor.execute(ctx, ApplyStateEffect(ATTRIBUTE_BONUS_STATE_ID, "a0",
        runtime_params=AttributeBonusParams("defense", 100)))
    own = [m for m in s.damage_rule_provider.collect(ctx, effect.to_request()).modifier_contributions
           if m.source.source_skill_id == "22031"]
    assert own[0].operand == pytest.approx(.60)


@pytest.mark.parametrize("mode,count,total", [(SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES,2,2),
    (SkillTargetMode.FIXED_ALL_ENEMIES,None,3),
    (SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY,None,1)])
def test_target_cardinality_preserved_and_only_commander_bound(monkeypatch, mode, count, total):
    ctx, s, rt, hostile, calls = setup(monkeypatch, mode=mode, count=count)
    result = s.skill_resolver.resolve(ctx, hostile)
    assert len(result.target_ids) == total and "a0" in result.target_ids
    assert len([e for e in result.effects if isinstance(e, QueryBoundDamageEffect)]) == 1
    assert calls == [.8]


def test_failed_probability_no_bound_reduction_even_when_natural_target_is_main(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch, success=False, mode=SkillTargetMode.FIXED_ALL_ENEMIES)
    result = s.skill_resolver.resolve(ctx, hostile)
    assert "a0" in result.target_ids
    assert not any(isinstance(e, QueryBoundDamageEffect) for e in result.effects)
    assert calls == [.8]


def test_reduction_does_not_leak_to_direct_requests_other_skill_or_normal_attack(monkeypatch):
    ctx, s, rt, hostile, _ = setup(monkeypatch)
    effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
    bound = effect.to_request()
    requests = [DamageRequest("b0", "a0", DamageType.WEAPON, DamageSourceType.SKILL, source_skill_id="test_hostile"),
        replace(bound, source_type=DamageSourceType.NORMAL_ATTACK), replace(bound, target_id="a1"),
        replace(bound, source_skill_id="other"), replace(bound, source_state_id="periodic", source_state_instance_id="dot")]
    for request in requests:
        assert not [m for m in s.damage_rule_provider.collect(ctx, request).modifier_contributions
                    if m.source.source_skill_id == "22031"]


def test_independent_query_receipts_do_not_overwrite_each_other(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch)
    first = s.skill_resolver.resolve(ctx, hostile).effects[0]
    second = s.skill_resolver.resolve(ctx, hostile).effects[0]
    assert first.target_priority_receipt.operation_id != second.target_priority_receipt.operation_id
    for effect in (first, second):
        assert len([m for m in s.damage_rule_provider.collect(ctx, effect.to_request()).modifier_contributions
                    if m.source.source_skill_id == "22031"]) == 1
    assert calls == [.8, .8]


def test_multiple_damage_effects_share_one_priority_roll(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch)
    hostile.definition = replace(hostile.definition, effect_specs=(DamageSkillEffectSpec(DamageType.WEAPON),
                                                                 DamageSkillEffectSpec(DamageType.STRATEGY)))
    result = s.skill_resolver.resolve(ctx, hostile)
    assert calls == [.8]
    assert all(isinstance(e, QueryBoundDamageEffect) for e in result.effects)
    assert result.effects[0].target_priority_receipt == result.effects[1].target_priority_receipt


def test_inherited_targets_do_not_query_or_reroll(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch)
    result = s.skill_resolver.resolve(ctx, hostile, inherited_target_ids=("a1",))
    assert result.target_ids == ("a1",) and not calls
    assert not isinstance(result.effects[0], QueryBoundDamageEffect)


def test_existing_required_target_and_exclusion_policy_remain_authoritative(monkeypatch):
    from sgs_v2.battle_core.skill_target_policy import TargetPolicyContribution
    for forced in (False, True):
        ctx, s, rt, hostile, calls = setup(monkeypatch)
        s.skill_target_policy.register_rule_adapter(lambda context, operation, candidates:
            TargetPolicyContribution(required_target_ids=("a1",)) if forced else
            TargetPolicyContribution(excluded_target_ids=("a0",)))
        result = s.skill_resolver.resolve(ctx, hostile)
        assert "a0" not in result.target_ids
        assert not calls


def test_round_six_expiry_preserves_deputy_driver(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch)
    assert ctx.states.find(state_id=TARGET_PRIORITY_STATE_ID)[0].expires_round == 6
    ctx.current_round = 6
    ctx.current_phase = BattlePhase.ROUND_START.value
    s.state_lifecycle_system.expire_at(ctx, round_no=6, phase=BattlePhase.ROUND_START.value)
    s.rule_hook_system.process(ctx, RoundStartHook(6))
    assert not ctx.states.find(state_id=TARGET_PRIORITY_STATE_ID)
    s.skill_resolver.resolve(ctx, hostile)
    assert not calls
    act(ctx, s, rt.owner_id, 6)
    assert ctx.metadata["periodic_team_support_history"][-1]["cumulative_increase_rate"] == pytest.approx(.15)


def test_removed_priority_and_disabled_carrier_cannot_use_old_receipt(monkeypatch):
    for remove in (True, False):
        ctx, s, rt, hostile, calls = setup(monkeypatch)
        effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
        if remove:
            s.effect_executor.execute(ctx, RemoveStateEffect(ctx.states.find(state_id=TARGET_PRIORITY_STATE_ID)[0].instance_id))
        else:
            rt.enabled = False
        assert not [m for m in s.damage_rule_provider.collect(ctx, effect.to_request()).modifier_contributions
                    if m.source.source_skill_id == "22031"]


def test_priority_probability_boundary_uses_canonical_rng(monkeypatch):
    for roll, success in ((.799999, True), (.8, False)):
        ctx, s, rt, hostile, calls = setup(monkeypatch)
        # Restore chance implementation, control its single uniform draw.
        from sgs_v2.battle_core.random_system import RandomSystem
        monkeypatch.setattr(ctx.random, "chance", lambda p: RandomSystem.chance(ctx.random, p))
        monkeypatch.setattr(ctx.random, "random", lambda: roll)
        result = s.skill_resolver.resolve(ctx, hostile)
        assert any(isinstance(e, QueryBoundDamageEffect) for e in result.effects) is success


def test_full_engine_smoke_with_attack_skill_and_seed_reproduction():
    histories=[]
    for _ in range(2):
        ctx, s, rt = scene(mode=RecoveryTargetMode.RANDOM_ALLIES)
        rt.definition = create_wu_feng_zhen_runtime(rt.owner_id).definition
        # Keep the battle alive across the round-five boundary.
        hostile = SkillRuntime(SkillDefinition("test_hostile", "hostile", 1,
            SkillTargetMode.FIXED_ALL_ENEMIES, (DamageSkillEffectSpec(DamageType.WEAPON, .01),)),
            "b0", SkillSlot.INHERENT)
        ctx.skill_runtimes.register(hostile)
        ordinary_actions = s.action_system
        class ExplicitSkillActionPort:
            # Base ActionSystem currently owns normal attacks; this test composes
            # an explicit official skill operation in the actor's real action.
            def execute(self, context, actor, action_scope=None):
                if actor.unit_id == hostile.owner_id:
                    resolution = s.skill_resolver.resolve(context, hostile)
                    for effect in resolution.effects:
                        s.effect_executor.execute(context, effect)
                return ordinary_actions.execute(context, actor, action_scope)
        s.action_system = ExplicitSkillActionPort()
        BattleEngine(context=ctx, systems=s).run()
        history=ctx.metadata["target_priority_history"]
        assert history and all(1 <= row["round"] <= 5 for row in history)
        histories.append(history)
    assert histories[0] == histories[1]


def test_unknown_formula_cap_is_not_silently_invented(monkeypatch):
    ctx, s, rt, hostile, _ = setup(monkeypatch)
    effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
    ctx.units["a0"].defense = 801
    with pytest.raises(ValueError, match="live reduction rate"):
        s.damage_rule_provider.collect(ctx, effect.to_request())


def test_user_random_teammates_rule_cannot_be_replaced_with_lowest_troops():
    with pytest.raises(ValueError, match="requires random recovery"):
        create_wu_feng_zhen_runtime("a0", recovery_target_mode=RecoveryTargetMode.LOWEST_TROOPS)


def test_query_wrapper_preserves_canonical_effect_source_and_additive_fields(monkeypatch):
    ctx, s, rt, hostile, _ = setup(monkeypatch)
    effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
    assert effect.source_ref.source_unit_id == "b0"
    assert effect.source_ref.source_skill_slot is SkillSlot.INHERENT
    assert effect.source_ref.source_skill_id == hostile.definition.skill_id
    augmented = replace(effect, additive_damage=10, final_additive_damage=20)
    request = augmented.to_request()
    assert request.additive_damage == 10 and request.final_additive_damage == 20
    assert request.target_priority_receipt == effect.target_priority_receipt


def test_same_ids_in_another_battle_cannot_reuse_receipt(monkeypatch):
    ctx, s, rt, hostile, _ = setup(monkeypatch)
    foreign, fs, frt, _, _ = setup(monkeypatch)
    effect = s.skill_resolver.resolve(ctx, hostile).effects[0]
    assert not [m for m in fs.damage_rule_provider.collect(foreign, effect.to_request()).modifier_contributions
                if m.source.source_skill_id == "22031"]


def test_prebattle_round_zero_does_not_roll_priority(monkeypatch):
    ctx, s, rt, hostile, calls = setup(monkeypatch, rounds=0)
    s.skill_resolver.resolve(ctx, hostile)
    assert not calls
