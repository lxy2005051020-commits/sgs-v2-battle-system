"""Preserve exact source descriptions, static config and SHA256 provenance."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path(r"C:\Users\34187\Documents\ChatGPT\三国志战略版战报逆向\outputs\skill_static_descriptions_full_20260808_1632\merged\skill_static_descriptions_named.csv")
config_source = source.with_name("skill_static_descriptions.json")
output = root / "stages/stage14/qian_long_evidence"
output.mkdir(parents=True, exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    rows = [row for row in reader if row.get("name") == "潜龙阵"]
assert len(rows) == 10 and all(row["base_id"] == "22040" for row in rows)
with (output / "static_levels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)

def find_config(value):
    if isinstance(value, dict):
        if value.get("name") == "潜龙阵" and value.get("id") == 22040:
            return value
        children = value.values()
    elif isinstance(value, list):
        children = value
    else:
        return None
    for child in children:
        found = find_config(child)
        if found is not None:
            return found

config = find_config(json.loads(config_source.read_text(encoding="utf-8-sig")))
assert config is not None and config["arm_limit"] == {}
manifest = {"baseline": "0e8a9ed223e918bc7872e67e88d2102e08cdab2c",
    "source_csv": str(source), "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_json": str(config_source), "source_json_sha256": hashlib.sha256(config_source.read_bytes()).hexdigest(),
    "static_row_count": len(rows), "config": config,
    "user_confirmed": ["complete generic commander-effect interface", "installation effective attribute snapshot, fixed increments"],
    "model_boundaries": ["snapshot precedes all formation effects including qualification changes",
        "commander-effect presence comes exclusively from loaded declarative specs in all slots, including disabled",
        "opening commander branches must use distinct persistent state IDs",
        "existing formation provider defeat cleanup policy; no client gameplay freeze"],
    "provenance": "2026-08-08 STATIC_SNAPSHOT + USER_CONFIRMED_MODEL / NOT_CLIENT_FROZEN"}
(output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Preserved ten rows, full config and hashes")
