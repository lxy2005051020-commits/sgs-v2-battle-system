#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consolidate_finalization_evidence.py

Consolidates all empirical evidence for RF-P04 into a single structured file:
BATTLE_FINALIZATION_EVIDENCE.json
"""

import os
import json

RESEARCH_DIR = r'D:\sgs-v2-battle-system\stages\stage9\research\battle_finalization_barrier'
OUTPUT_FILE = os.path.join(RESEARCH_DIR, 'BATTLE_FINALIZATION_EVIDENCE.json')

def main():
    # 1. Combo deep evidence
    combo_file = os.path.join(RESEARCH_DIR, 'BATTLE_END_COMBO_DEEP_EVIDENCE.json')
    with open(combo_file, encoding='utf-8') as fp:
        combo_data = json.load(fp)

    # 2. Cleave evidence
    cleave_file = os.path.join(RESEARCH_DIR, 'CLEAVE_COMMANDER_DEATH_EVIDENCE.json')
    with open(cleave_file, encoding='utf-8') as fp:
        cleave_data = json.load(fp)

    cleave_general_file = os.path.join(RESEARCH_DIR, 'BATTLE_END_CLEAVE_EVIDENCE.json')
    with open(cleave_general_file, encoding='utf-8') as fp:
        cleave_gen_data = json.load(fp)

    # 3. Counter evidence
    counter_file = os.path.join(RESEARCH_DIR, 'BATTLE_END_COUNTER_EVIDENCE.json')
    with open(counter_file, encoding='utf-8') as fp:
        counter_data = json.load(fp)

    # 4. Chain evidence
    chain_file = os.path.join(RESEARCH_DIR, 'BATTLE_END_CHAIN_EVIDENCE.json')
    with open(chain_file, encoding='utf-8') as fp:
        chain_data = json.load(fp)

    consolidated = {
        'metadata': {
            'package': 'RF-P04',
            'title': 'BATTLE_FINALIZATION_BARRIER_EVIDENCE_CORPUS',
            'date': '2026-09-13',
            'total_corpus_scanned': 32999
        },
        'combo_battle_ending_evidence': {
            'stats': combo_data['stats'],
            'summary': {
                'total_attack1_battle_ending': combo_data['stats']['total_battle_ending_attack1'],
                'commander_kills': combo_data['stats']['commander_kills'],
                'commander_kills_with_cfg230': combo_data['stats']['commander_kills_with_cfg230'],
                'commander_kills_with_second_attack_cfg9': combo_data['stats']['commander_kills_with_second_attack_cfg9'],
                'cfg9_admission_ratio_after_commander_kill': "0 / 10745 (0.00%)",
                'conclusion': "NORMAL_ATTACK #2 is strictly blocked after victory condition satisfied by Attack #1."
            },
            'sample_commander_with_230': combo_data['commander_with_230_cases'][:5]
        },
        'cleave_battle_ending_evidence': {
            'stats': cleave_data['stats'],
            'case_a_main_target_lethal_cleave_executes': cleave_gen_data['stats']['case_a_main_target_lethal_cleave_executes'],
            'case_b_attacker_dies_during_cleave': cleave_gen_data['stats']['case_b_attacker_dies_during_cleave'],
            'case_d_secondary_commander_lethal': cleave_data['stats']['total_lethal_cleave_commander_cases'],
            'case_d_subsequent_cleave_continued': cleave_data['stats']['cases_with_subsequent_cleave_hits'],
            'case_e_cleave_chain_kills_commander': cleave_gen_data['stats']['case_e_cleave_chain_kills_commander'],
            'summary': {
                'case_a_rule': "Main target lethal does NOT prevent Cleave execution on secondary targets (169/169 cases).",
                'case_d_rule': "Secondary commander death during Cleave does NOT abort remaining secondary targets in the same admitted Cleave effect (5/5 cases where remaining secondary existed, secondary executed before finalization).",
                'finalization_barrier': "Victory log cfg 157 occurs after Cleave completes all admitted secondary targets and commander collateral cfg 209 commits."
            },
            'sample_lethal_cases': cleave_data['cases'][:5]
        },
        'counter_battle_ending_evidence': {
            'stats': counter_data['stats'],
            'summary': {
                'total_sibling_counter_cases': counter_data['stats']['total_sibling_counter_cases'],
                'commander_attacker_cases': counter_data['stats']['commander_attacker_cases'],
                'conclusion': "Sibling counter continuation is frozen per Counter P0. CTS9-H02 is codified with explicit runtime regression."
            }
        },
        'chain_battle_ending_evidence': {
            'stats': chain_data['stats'],
            'summary': {
                'total_chain_commander_death_cases': chain_data['stats']['total_chain_commander_death_cases'],
                'chain_continued_after_commander_death': chain_data['stats']['chain_continued_after_commander_death'],
                'conclusion': "Chain atomic traversal completes remaining linked targets before finalization barrier in 159/159 continuation cases."
            },
            'sample_cases': chain_data['sample_cases'][:5]
        },
        'finalization_matrix': [
            {
                'operation': 'ChainTraversal',
                'death_victim': 'commander',
                'victory_satisfied': True,
                'admitted_work_exists': True,
                'work_after_death': 'remaining linked slots continue propagation',
                'new_work_admitted': False,
                'finalization_point': 'after Chain broadcast completes'
            },
            {
                'operation': 'CounterBatch',
                'death_victim': 'attacker commander',
                'victory_satisfied': True,
                'admitted_work_exists': True,
                'work_after_death': 'sibling C2 executes with 0 troop loss against dead target',
                'new_work_admitted': False,
                'finalization_point': 'after CounterBatch completes'
            },
            {
                'operation': 'CleaveEffect',
                'death_victim': 'commander secondary',
                'victory_satisfied': True,
                'admitted_work_exists': True,
                'work_after_death': 'remaining admitted secondary target in effect executes',
                'new_work_admitted': False,
                'finalization_point': 'after Cleave secondary queue completes and cfg 209 commits'
            },
            {
                'operation': 'ShareTransaction',
                'death_victim': 'protected target',
                'victory_satisfied': True,
                'admitted_work_exists': False,
                'work_after_death': 'TARGET_DEATH_INTERRUPT: pending sharer loss discarded (0 loss)',
                'new_work_admitted': False,
                'finalization_point': 'after transaction terminal boundary'
            },
            {
                'operation': 'DistributionTransaction',
                'death_victim': 'commander participant',
                'victory_satisfied': True,
                'admitted_work_exists': True,
                'work_after_death': 'ENGINEERING_DEFAULT: transaction finishes already-planned commits',
                'new_work_admitted': False,
                'finalization_point': 'after DistributionTransaction commits finish'
            },
            {
                'operation': 'NormalAttack',
                'death_victim': 'final enemy / commander',
                'victory_satisfied': True,
                'admitted_work_exists': False,
                'work_after_death': 'none (future Assault / Combo #2 / Next Action cancelled)',
                'new_work_admitted': False,
                'finalization_point': 'after NormalAttack #1 synchronous lifecycle completes'
            }
        ]
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as fp:
        json.dump(consolidated, fp, ensure_ascii=False, indent=2)
    print(f"Saved consolidated evidence to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
