"""Preserve relevant rows and hash the supplied local client static export."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path(r"C:\Users\34187\Documents\ChatGPT\三国志战略版战报逆向\outputs\skill_static_descriptions_full_20260808_1632\merged\skill_static_descriptions_named.csv")
config_source = source.with_name("skill_static_descriptions.json")
output = root / "stages/stage14/ji_xing_evidence"
output.mkdir(parents=True, exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    rows = [row for row in reader if row.get("name") == "箕形阵"]
assert len(rows) == 10
with (output / "static_levels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
data = json.loads(config_source.read_text(encoding="utf-8-sig"))


def find_config(value):
    if isinstance(value, dict):
        if value.get("name") == "箕形阵" and value.get("id") == 20178:
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


config = find_config(data)
assert config is not None and config["arm_limit"] == {}
manifest = {
    "source_csv": str(source), "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_json": str(config_source), "source_json_sha256": hashlib.sha256(config_source.read_bytes()).hexdigest(),
    "static_row_count": len(rows), "config": config,
    "user_formula": "40% + (16/150 percentage points) * (strength - 100)",
    "runtime_formula": "0.40 + 0.16 / 150 * (strength - 100)",
    "provenance": "USER_SPECIFIED_FORMULA / NOT_CLIENT_EMPIRICALLY_FROZEN",
    "snapshot_policy": "PROVISIONAL_INSTALLATION_TIME_PROVIDER_ATTACK",
}
(output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Preserved 10 static rows, full config, source hashes and user formula")
