"""Reproducible USER_SPECIFIED final-addition model checks, not game proof."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgs_v2.battle_core import (
    BattleContext, BattleEngine, BattleSystems, EventBus, LineupPosition, RandomSystem,
    TroopType, UnitRuntime, create_fei_xiong_jun_runtime, register_official_state_definitions,
    BattlePhase, TroopAdmissionStatus, admit_and_install_troop_skill,
)
from sgs_v2.battle_core.recovery_system import RecoveryRequest, RecoveryModifierPolicy
from sgs_v2.battle_core.rule_hooks import UnitActionStartHook


def fixture(commander):
    units = {}
    for team in ('a', 'b'):
        for i, position in enumerate(LineupPosition, 1):
            uid = f'{team}{i}'
            units[uid] = UnitRuntime(uid, commander if uid == 'a1' else uid, team,
                10000, 5000, attack=180, defense=120, intelligence=200, speed=50,
                wounded_troops=5000, troop_type=TroopType.CAVALRY, lineup_position=position)
    context = BattleContext('feixiong-user-model', units, EventBus(), RandomSystem(42), max_rounds=2)
    register_official_state_definitions(context.states)
    runtime = create_fei_xiong_jun_runtime('a2')
    context.skill_runtimes.register(runtime)
    return context, BattleSystems(), runtime


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for commander, expected in [('ordinary', 116), ('董卓', 120)]:
        c, s, rt = fixture(commander)
        c.current_phase = BattlePhase.PRE_BATTLE.value
        assert admit_and_install_troop_skill(c, s, rt).status is TroopAdmissionStatus.SUCCESS
        result = s.recovery_system.resolve(c, RecoveryRequest('a1', 'a3', 100,
            modifier_policy=RecoveryModifierPolicy.APPLY))
        assert result.actual_recovery == expected
        cases.append({'commander': commander, 'base_recovery': 100,
            'modified_recovery': result.modified_recovery, 'actual_recovery': result.actual_recovery,
            'states': len(c.states.find()), 'mode': 'REAL_PRE_BATTLE_ADMISSION'})
    c, s, rt = fixture('ordinary')
    c.current_phase = BattlePhase.PRE_BATTLE.value
    admit_and_install_troop_skill(c, s, rt)
    recovered = s.recovery_system.resolve(c, RecoveryRequest('a2', 'a3', 1000))
    assert recovered.actual_recovery == 1000
    c.current_round, c.current_phase = 1, BattlePhase.UNIT_ACTION_START.value
    c.random.chance = lambda p: True
    first = s.rule_hook_system.process(c, UnitActionStartHook(1, 'a1'))
    assert [r.effect.final_additive_damage for r in first.effect_results] == [100, 100]
    first_results = [{'target': r.effect.target_id, 'coefficient': r.effect.coefficient,
        'unaugmented_final_damage': r.resolution.damage.unaugmented_final_damage,
        'addition': r.resolution.damage.final_additive_damage,
        'final_damage': r.resolution.damage.final_damage} for r in first.effect_results]
    assert all(r['final_damage'] == r['unaugmented_final_damage'] + 100 for r in first_results)
    s.recovery_system.resolve(c, RecoveryRequest('a2', 'a3', 200))
    c.current_round = 2
    s.rule_hook_system.process(c, UnitActionStartHook(2, 'a1'))
    snapshots = [e.payload for e in c.event_bus.history
                 if e.payload.get('event_kind') == 'ACCUMULATED_RECOVERY_SNAPSHOT']
    assert [e['actual_recovery_snapshot'] for e in snapshots] == [1000, 200]
    c, s, _ = fixture('ordinary')
    result = BattleEngine(c, s).run()
    assert c.ended and c.result is result
    report = {'status': 'USER_SPECIFIED_FINAL_ADDITIVE_MODEL / FULL_ENGINE_RUNS',
        'provenance': 'USER_RULE_2026_10_12; ENGINEERING_VALIDATION_ONLY; NOT_GAMEPLAY_FROZEN',
        'formula': 'final_damage = floor(ordinary_final_damage_at_64_percent + actual_team_recovery_snapshot / 10)',
        'known_effect_cases': cases, 'shared_snapshot_cases': snapshots,
        'first_damage_results': first_results,
        'full_engine': {'winner': result.winner_team_id, 'rounds_completed': result.rounds_completed,
            'final_troops': result.final_troops,
            'events': [{'sequence': e.sequence, 'type': e.event_type.value, 'round': e.round_no,
                'actor': e.actor_id, 'target': e.target_id, 'payload': e.payload} for e in c.event_bus.history]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: recovery=116/120; shared snapshot=1000; final addition=100 each; reset=200; full engine runs')


if __name__ == '__main__':
    main()
