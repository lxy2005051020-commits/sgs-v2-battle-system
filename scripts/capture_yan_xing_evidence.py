"""Preserve exact static descriptions and source hashes for the approved base model."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = Path(r"C:\Users\34187\Documents\ChatGPT\三国志战略版战报逆向\outputs\skill_static_descriptions_full_20260808_1632\merged\skill_static_descriptions_named.csv")
config_source = source.with_name("skill_static_descriptions.json")
output = root / "stages/stage14/yan_xing_evidence"
output.mkdir(parents=True, exist_ok=True)
with source.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    rows = [row for row in reader if row.get("name") == "雁行阵"]
assert len(rows) == 10 and all(row["base_id"] == "20862" for row in rows)
with (output / "static_levels.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def find_config(value):
    if isinstance(value, dict):
        if value.get("name") == "雁行阵" and value.get("id") == 20862:
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
manifest = {"baseline": "4357a6b0a46f379945193c0e203a1373dd1c6e03",
    "source_csv": str(source), "source_csv_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "source_json": str(config_source), "source_json_sha256": hashlib.sha256(config_source.read_bytes()).hexdigest(),
    "static_row_count": len(rows), "config": config,
    "user_approved": ["暂时按基础概率和基础偷取量运行", "每回合开始执行",
        "最低统率并列按主将、副将1、副将2", "负面状态按种类抽取1至2种", "转移后本回合结束过期"],
    "deferred": ["携带者统率对三种触发概率的缩放", "携带者统率对偷取量的缩放"],
    "boundaries": ["continuous-damage snapshots and relationship-bearing negative states",
        "query-bound reduction and round curves", "same-kind destination coexistence follows canonical conflict policy"],
    "provenance": "2026-08-08 STATIC_SNAPSHOT / USER_APPROVED_BASE_VALUE_MODEL / NOT_GAMEPLAY_FROZEN"}
(output / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("Preserved ten Yan Xing rows, original config and source hashes")
