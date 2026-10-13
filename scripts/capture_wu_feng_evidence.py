"""Preserve ten exact source rows, full static config and source hashes."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path(r"C:\Users\34187\Documents\ChatGPT\三国志战略版战报逆向\outputs\skill_static_descriptions_full_20260808_1632\merged\skill_static_descriptions_named.csv")
config_source = source.with_name("skill_static_descriptions.json")
output = root / "stages/stage14/wu_feng_evidence"
output.mkdir(parents=True, exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    rows = [row for row in reader if row.get("name") == "武锋阵"]
assert len(rows) == 10
with (output / "static_levels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def find_config(value):
    if isinstance(value, dict):
        if value.get("name") == "武锋阵" and value.get("id") == 22031:
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
    "user_rules": ["携带战法者行动时", "降低伤害百分比=30%+0.1%×(主将实时统率−100)", "治疗目标为副将另外两名队友，不包括自己，随机选一个人"],
    "model_assumptions": ["after ordinary provider action-start hooks", "roles frozen at installation", "stacked increases add", "live performer troops and 2 percent per advancement star", "neutral healing attribute; external recovery modifiers use existing owner"],
    "open_questions": ["below-Lv10 command scaling", "recovery modifier read timing", "role behavior after deaths", "source-skill priority details lack dedicated raw-report freeze"],
    "provenance": "STATIC_DESCRIPTION + USER_SPECIFIED_LIVE_COMMAND_FORMULA + USER_CONFIRMED_PROVIDER_ACTION_AND_RANDOM_TEAMMATES / NOT_CLIENT_FROZEN",
}
(output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Preserved ten source rows, canonical config and hashes")
