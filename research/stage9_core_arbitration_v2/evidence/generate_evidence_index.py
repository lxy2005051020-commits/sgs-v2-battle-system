import os
import json
import hashlib
import csv

JSON_DIR = r'D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON'
OUT_DIR = r'research/stage9_core_arbitration_v2/evidence'
SLICES_DIR = os.path.join(OUT_DIR, 'raw_slices')
os.makedirs(SLICES_DIR, exist_ok=True)

# Key claims and their representative battle files
key_claims = [
    # BF-01: Confusion x Taunt
    ('EM-01', '战报_1069659_pid1064677.json', 310, 325, 'positive', 'Confusion overrides Taunt: 勇城卫 attacked 黄月英 instead of 孙坚'),
    ('EM-01', '战报_1070619_pid1065637.json', 70, 95, 'positive', 'Confusion overrides Taunt: 勇城卫 attacked friendly 勇城卫'),
    ('EM-01', '战报_1073363_pid1068396.json', 70, 85, 'ambiguous', 'Confusion attacked Taunter 孙坚 by random chance'),

    # BF-02: Cleave vs Counter vs Assault
    ('EM-08', '战报_1068514_pid1063527.json', 40, 70, 'positive', 'Cleave (45) -> Counter stack (48) -> Assault (55, 64)'),
    ('EM-08', '战报_2498273_pid2607877.json', 110, 135, 'counterexample_explained', 'Juedi fanji stack after assault damage (OnDamageTaken callback)'),

    # BF-01 / EM-03: Self-rescue
    ('EM-03', '战报_1111040_pid1106298.json', 110, 120, 'positive', 'Zhang Fei self-rescue under confusion (Zhang Fei attacks Zhang Fei)'),

    # BF-04: Commander death
    ('EM-21', '战报_1000225_pid995488.json', 140, 165, 'positive', 'Yanren paoxiao multi-hit finishes target 2 after commander dies'),
    ('EM-21', '战报_1008109_pid1003336.json', 205, 220, 'positive', 'Counter kills commander -> cfg 209 troop loss -> cfg 157 victory'),
    ('EM-22', '战报_1627796_pid1627641.json', 1320, 1335, 'positive', 'Chain propagation completes atomic loop without recursive chain'),

    # BF-06: Recursion
    ('EM-11', '战报_1008108_pid1003335.json', 35, 55, 'positive', 'Counter damage does not trigger counter back'),

    # HR-02: Share lethal
    ('EM-19', '战报_1008108_pid1003335.json', 130, 150, 'positive', 'Main target dies -> share does not execute')
]

# 1. Generate RAW_BATTLE_HASH_MANIFEST.csv
hash_manifest_path = os.path.join(OUT_DIR, 'RAW_BATTLE_HASH_MANIFEST.csv')
with open(hash_manifest_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['claim_id', 'filename', 'sha256', 'file_size_bytes'])
    
    seen_files = {}
    for claim_id, fname, start, end, status, note in key_claims:
        if fname not in seen_files:
            fpath = os.path.join(JSON_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath, 'rb') as fp:
                    content = fp.read()
                    sha = hashlib.sha256(content).hexdigest()
                    size = len(content)
                seen_files[fname] = (sha, size)
            else:
                seen_files[fname] = ('FILE_NOT_FOUND', 0)
        sha, size = seen_files[fname]
        writer.writerow([claim_id, fname, sha, size])

print(f"Saved {hash_manifest_path}")

# 2. Generate CLAIM_EVIDENCE_INDEX.csv
claim_index_path = os.path.join(OUT_DIR, 'CLAIM_EVIDENCE_INDEX.csv')
with open(claim_index_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['claim_id', 'battle_file', 'event_start', 'event_end', 'evidence_type', 'note'])
    for claim_id, fname, start, end, status, note in key_claims:
        writer.writerow([claim_id, fname, start, end, status, note])

print(f"Saved {claim_index_path}")

# 3. Save raw slices for key evidence in raw_slices/
for claim_id, fname, start, end, status, note in key_claims:
    fpath = os.path.join(JSON_DIR, fname)
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', encoding='utf-8') as fp:
        data = json.load(fp)
    
    events = []
    for g in data.get('detail', {}).get('groups', []):
        for e in g.get('data', {}).get('events', []):
            events.append(e)
            
    slice_events = events[max(0, start):min(len(events), end)]
    slice_fname = f"{claim_id}_{fname.replace('.json', '')}_ev{start}_{end}.json"
    slice_path = os.path.join(SLICES_DIR, slice_fname)
    with open(slice_path, 'w', encoding='utf-8') as out_fp:
        json.dump({
            'claim_id': claim_id,
            'original_file': fname,
            'event_range': [start, end],
            'evidence_type': status,
            'note': note,
            'events': slice_events
        }, out_fp, ensure_ascii=False, indent=2)

print(f"Saved raw slices in {SLICES_DIR}")
