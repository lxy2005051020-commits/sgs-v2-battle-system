import os
import json
import re

INDEX_PATH = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\stage9_index.json'
JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'

with open(INDEX_PATH, encoding='utf-8') as f:
    index = json.load(f)

def load_events(report_name):
    path = os.path.join(JSON_DIR, report_name)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    events = []
    for g in data.get('detail', {}).get('groups', []):
        gkey = g.get('key')
        for e in g.get('data', {}).get('events', []):
            ev = e.get('event', {})
            raw_desc = ev.get('full_desc') or ev.get('desc') or ''
            clean_desc = re.sub(r'<[^<]+?>', '', raw_desc)
            events.append({
                'group': gkey,
                'key': e.get('key'),
                'cfg_id': ev.get('cfg_id'),
                'desc': clean_desc,
                'raw': ev
            })
    return events

fendan_reports = [f for f, tags in index.items() if 'fen_dan' in tags]
print(f"Scanning {len(fendan_reports)} fen_dan reports...")

pattern_dmg_red = re.compile(r'\[(.*?)\]由于【(.*?)】的「分担」效果，本次攻击受到的伤害减少了(\d+(?:\.\d+)?)%')
pattern_share_exec = re.compile(r'\[(.*?)\]执行来自【(.*?)】的「分担」效果')
pattern_loss = re.compile(r'\[(.*?)\](?:由于.*?的伤害，)?损失了兵力(\d+)（(\d+)）')

fendan_cases = []

for r_name in fendan_reports[:2000]:
    try:
        events = load_events(r_name)
    except Exception:
        continue
    
    for i, e in enumerate(events):
        if e['cfg_id'] == 123 and '分担' in e['desc']:
            m_red = pattern_dmg_red.search(e['desc'])
            if not m_red:
                continue
            main_target_name = m_red.group(1)
            ratio = float(m_red.group(3)) / 100.0
            
            # Find main loss in next 3 events
            main_loss, main_rem = None, None
            for k in range(i+1, min(len(events), i+4)):
                if '损失了兵力' in events[k]['desc']:
                    m_loss = pattern_loss.search(events[k]['desc'])
                    if m_loss and m_loss.group(1) == main_target_name:
                        main_loss = int(m_loss.group(2))
                        main_rem = int(m_loss.group(3))
                        break
            
            # Find sharer exec and sharer loss in next 8 events
            sharer_name = None
            sharer_loss, sharer_rem = None, None
            for k in range(i+1, min(len(events), i+10)):
                if e['cfg_id'] == 123 and k == i:
                    continue
                if events[k]['cfg_id'] == 96 and '分担' in events[k]['desc']:
                    m_se = pattern_share_exec.search(events[k]['desc'])
                    if m_se:
                        sharer_name = m_se.group(1)
                        # next event after this should be sharer loss
                        for q in range(k+1, min(len(events), k+4)):
                            if '损失了兵力' in events[q]['desc']:
                                m_sl = pattern_loss.search(events[q]['desc'])
                                if m_sl and m_sl.group(1) == sharer_name:
                                    sharer_loss = int(m_sl.group(2))
                                    sharer_rem = int(m_sl.group(3))
                                    break
                        break
            
            if main_loss is not None and sharer_loss is not None:
                is_lethal = (main_rem == 0)
                total = main_loss + sharer_loss
                fendan_cases.append({
                    'report': r_name,
                    'event_idx': i,
                    'main_target': main_target_name,
                    'ratio': ratio,
                    'main_loss': main_loss,
                    'main_rem': main_rem,
                    'sharer': sharer_name,
                    'sharer_loss': sharer_loss,
                    'sharer_rem': sharer_rem,
                    'is_lethal': is_lethal,
                    'total_loss': total,
                    'actual_sharer_ratio': sharer_loss / total if total > 0 else 0
                })

print(f"Total analyzed fen_dan cases: {len(fendan_cases)}")
normal_cases = [c for c in fendan_cases if not c['is_lethal']]
lethal_cases = [c for c in fendan_cases if c['is_lethal']]
print(f"Normal cases (survived): {len(normal_cases)}")
print(f"Lethal cases (main died, rem==0): {len(lethal_cases)}")

if normal_cases:
    print("\n--- Normal Cases Sample ---")
    for c in normal_cases[:5]:
        print(f"Report: {c['report']} MainLoss={c['main_loss']} SharerLoss={c['sharer_loss']} Total={c['total_loss']} ExpectedRatio={c['ratio']:.2f} ActualRatio={c['actual_sharer_ratio']:.4f}")

if lethal_cases:
    print("\n--- Lethal Cases Sample ---")
    for c in lethal_cases[:5]:
        print(f"Report: {c['report']} MainLoss={c['main_loss']}(rem=0) SharerLoss={c['sharer_loss']} Total={c['total_loss']} ExpectedRatio={c['ratio']:.2f} ActualRatio={c['actual_sharer_ratio']:.4f}")

out_path = r'D:\sgs-v2-battle-system\research\stage9_core_arbitration_v2\evidence\r6_fendan_math_data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({
        'total': len(fendan_cases),
        'normal_count': len(normal_cases),
        'lethal_count': len(lethal_cases),
        'normal_samples': normal_cases[:15],
        'lethal_samples': lethal_cases[:15]
    }, f, ensure_ascii=False, indent=2)
print("Saved to", out_path)
