"""Preserve ten exact source rows, full static config and source hashes."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path(r"C:\Users\34187\Documents\ChatGPT\三国志战略版战报逆向\outputs\skill_static_descriptions_full_20260808_1632\merged\skill_static_descriptions_named.csv")
config_source = source.with_name("skill_static_descriptions.json")
output = root / "stages/stage14/san_shi_evidence"
output.mkdir(parents=True, exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    rows = [row for row in reader if row.get("name") == "三势阵"]
assert len(rows) == 10
with (output / "static_levels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def find_config(value):
    if isinstance(value, dict):
        if value.get("name") == "三势阵" and value.get("id") == 22012:
            return value
        for child in value.values():
            found = find_config(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_config(child)
            if found is not None:
                return found


config = find_config(json.loads(config_source.read_text(encoding="utf-8-sig")))
assert config is not None and config["arm_limit"] == {}
manifest = {
    "baseline": "74817c59325bcaf7fafd5fc67f40621174ec9d65",
    "source_csv": str(source), "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_json": str(config_source), "source_json_sha256": hashlib.sha256(config_source.read_bytes()).hexdigest(),
    "static_row_count": len(rows), "config": config,
    "user_rules": ["损失兵力相同时选择副将1", "旧效果清除"],
    "model_assumptions": ["provider action start, after ordinary hooks",
        "net troop loss = entry troops minus current troops",
        "deputy redistribution continues beyond round 5; only activation bonus expires",
        "missing living deputy pair: clear old split effects and skip redistribution"],
    "provenance": "STATIC_DESCRIPTION + USER_CONFIRMED_TIE_AND_REPLACEMENT / NOT_CLIENT_FROZEN",
}
(output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Preserved ten source rows, canonical config and hashes")
