# Stage13-B2.5 Data Reproducibility & Pipeline Audit

Status: AUTHORITATIVE REPRODUCIBILITY MANIFEST
Effective: 2026-09-29
Corpus: 34,755 Raw Battle Reports (`d:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`)

## 1. Raw Corpus Inventory & Environment Manifest

1. **Raw Database Location**:
   - Path: `d:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`
   - Total Battle JSON Files: **34,755**
   - Format: Complete battle replay recordings containing `metadata`, `lineup`, `detail` (event text logs), and `hero_round_data` (per-round Lua attribute tables).

2. **Git Authority Repositories**:
   - Research Repository: `D:\sgs-research` (`sgs-state-mechanics-research`)
   - Battle System Repository: `D:\sgs-v2-battle-system` (`sgs-v2-battle-system`)
   - Troop Function Table: `D:\sgs-v2-battle-system\data\normal_attack\troop_function_table_1_10000.csv` (10,000 rows, keys 1..10000).

---

## 2. Generated Artifact Manifest

| Artifact Path | Description | Rows / Events | File Size | Generation Command |
| --- | --- | --- | --- | --- |
| `STAGE13_FULL_DAMAGE_ADVANCEMENT_EVENT_DATASET.csv` | Normalized battle events with attack-time troops, Lua attributes, exact modifier percentages, and military books. | 84,674 rows (84,673 events) | 27.5 MB | `python tools/stage13_build_full_damage_dataset.py` |
| `STAGE13_FULL_DAMAGE_REPLAY_OUTPUT.csv` | Multi-model predictions across 8 quantization/advancement combinations with discrete RNG $[86..94]$. | 84,674 rows | 62.8 MB | `python tools/stage13_full_damage_v1_replayer.py` |
| `STAGE13_FULL_DAMAGE_RESIDUAL_LEDGER.csv` | Residual tracking ledger logging observed vs predicted values, ratios, and suspected confounders. | 84,674 rows | 21.3 MB | `--residual-ledger` parameter in replayer |
| `STAGE13_FULL_DAMAGE_RESIDUAL_CLUSTERS.csv` | Anomaly clusters grouped by hero matchup, skill, advancement, and round with statistical shift tests. | 2,631 rows (2,630 clusters) | 365 KB | `python tools/stage13_full_damage_residual_analyzer.py` |

---

## 3. End-to-End Reproducibility Command Sequence

To reproduce every result and dataset from scratch on any machine with access to the raw battle corpus:

### Step 1: Build Normalized Event Dataset
```powershell
python "D:\sgs-research\tools\stage13_build_full_damage_dataset.py"
```
*Outputs: `D:\sgs-research\STAGE13_FULL_DAMAGE_ADVANCEMENT_EVENT_DATASET.csv`*

### Step 2: Execute Multi-Model Damage Replay
```powershell
python "D:\sgs-research\tools\stage13_full_damage_v1_replayer.py" `
  --input "D:\sgs-research\STAGE13_FULL_DAMAGE_ADVANCEMENT_EVENT_DATASET.csv" `
  --troop-table "D:\sgs-v2-battle-system\data\normal_attack\troop_function_table_1_10000.csv" `
  --output "D:\sgs-research\STAGE13_FULL_DAMAGE_REPLAY_OUTPUT.csv" `
  --residual-ledger "D:\sgs-research\STAGE13_FULL_DAMAGE_RESIDUAL_LEDGER.csv"
```
*Outputs: `STAGE13_FULL_DAMAGE_REPLAY_OUTPUT.csv` and `STAGE13_FULL_DAMAGE_RESIDUAL_LEDGER.csv`*

### Step 3: Execute Residual Clustering
```powershell
python "D:\sgs-research\tools\stage13_full_damage_residual_analyzer.py" `
  --input "D:\sgs-research\STAGE13_FULL_DAMAGE_REPLAY_OUTPUT.csv" `
  --output "D:\sgs-research\STAGE13_FULL_DAMAGE_RESIDUAL_CLUSTERS.csv" `
  --group-by "damage_family,source_skill,attacker_name,target_name,attacker_advancement,target_advancement,round,critical" `
  --min-count 5
```
*Outputs: `STAGE13_FULL_DAMAGE_RESIDUAL_CLUSTERS.csv`*

---

## 4. Integrity Verification

All outputs are completely deterministic:
- Given the raw JSON files and the Stage2 $F(N)$ table, the extracted dataset and replay outputs match bit-for-bit.
- All code files (`stage13_build_full_damage_dataset.py`, `stage13_full_damage_v1_replayer.py`, `stage13_full_damage_residual_analyzer.py`) are version-controlled in Git.
