import os
import json
import re

INDEX_PATH = r'stages/stage9/research/core_arbitration_v2/evidence/stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

both_files = [f for f, tags in index.items() if 'hun_luan' in tags and 'chao_feng' in tags]
print(f"Total candidate battle files with both tags: {len(both_files)}")

results = []

for file_idx, fname in enumerate(both_files):
    p = os.path.join(JSON_DIR, fname)
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        continue

    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc,
                'raw': ev
            })

    states = {}
    current_skill_caster = None
    current_skill_name = None

    for ev_idx, ev in enumerate(events):
        cfg = ev['cfg_id']
        desc = ev['desc']

        m_cast = re.search(r'\[([^\]]+)\]发动战法【([^】]+)】', desc)
        if m_cast:
            current_skill_caster = m_cast.group(1)
            current_skill_name = m_cast.group(2)

        if '「嘲讽」' in desc and ('已施加' in desc or '效果已施加' in desc or '执行来自' in desc):
            m_target = re.search(r'\[([^\]]+)\]', desc)
            if m_target:
                t = m_target.group(1)
                if t not in states:
                    states[t] = {'confusion': False, 'taunt_by': None}
                states[t]['taunt_by'] = current_skill_caster or "UNKNOWN_TAUNTER"

        if '「混乱」' in desc and ('已施加' in desc or '效果已施加' in desc or '执行来自' in desc):
            m_target = re.search(r'\[([^\]]+)\]', desc)
            if m_target:
                t = m_target.group(1)
                if t not in states:
                    states[t] = {'confusion': False, 'taunt_by': None}
                states[t]['confusion'] = True

        if '「嘲讽」' in desc and ('已消失' in desc or '消失' in desc or '无效' in desc or '清除了' in desc):
            m_target = re.search(r'\[([^\]]+)\]', desc)
            if m_target:
                t = m_target.group(1)
                if t in states:
                    states[t]['taunt_by'] = None

        if '「混乱」' in desc and ('已消失' in desc or '消失' in desc or '恢复正常' in desc or '清除了' in desc or '无效' in desc):
            m_target = re.search(r'\[([^\]]+)\]', desc)
            if m_target:
                t = m_target.group(1)
                if t in states:
                    states[t]['confusion'] = False

        if '无法再战' in desc or '已经死亡' in desc:
            m_dead = re.search(r'\[([^\]]+)\]', desc)
            if m_dead:
                dead_unit = m_dead.group(1)
                if dead_unit in states:
                    states[dead_unit]['confusion'] = False
                    states[dead_unit]['taunt_by'] = None
                for u, st in states.items():
                    if st.get('taunt_by') == dead_unit:
                        st['taunt_by'] = None

        if cfg == 9:
            m_atk = re.search(r'\[([^\]]+)\]对\[([^\]]+)\]发动普通攻击', desc)
            if m_atk:
                attacker = m_atk.group(1)
                target = m_atk.group(2)

                st = states.get(attacker, {})
                has_conf = st.get('confusion', False)
                taunt_src = st.get('taunt_by', None)

                if has_conf and taunt_src is not None:
                    is_taunt_target = (target == taunt_src)
                    results.append({
                        'battle_file': fname,
                        'event_index': ev_idx,
                        'attacker': attacker,
                        'actual_target': target,
                        'taunt_source': taunt_src,
                        'confusion_active': True,
                        'target_is_taunt_source': is_taunt_target,
                        'desc': desc
                    })

print(f"Total eligible cases where attacker had BOTH confusion and taunt: {len(results)}")
target_is_taunt = [r for r in results if r['target_is_taunt_source']]
target_not_taunt = [r for r in results if not r['target_is_taunt_source']]
print(f"Target == taunt source: {len(target_is_taunt)}")
print(f"Target != taunt source: {len(target_not_taunt)}")

out_path = r'stages/stage9/research/core_arbitration_v2/evidence/r11_confusion_taunt_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total_eligible': len(results),
        'target_eq_taunt': len(target_is_taunt),
        'target_ne_taunt': len(target_not_taunt),
        'cases': results
    }, f, ensure_ascii=False, indent=2)

print(f"Saved results to {out_path}")
