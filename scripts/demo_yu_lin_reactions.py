"""Deterministic full-engine evidence for base-rate Yu Lin reactions."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sgs_v2.battle_core import (BattleContext, BattleSystems, BattleEngine, EventBus,
    RandomSystem, UnitRuntime, LineupPosition, TroopType, EventType, create_yu_lin_zhen_runtime)

output = Path(__file__).resolve().parents[1] / "stages/stage14/yu_lin_reaction_evidence"
output.mkdir(parents=True, exist_ok=True)
rows = []
for seed in (7,19,31,43):
    units = {f"{t}{i}": UnitRuntime(f"{t}{i}", f"{t}{i}", t, 10000,10000,
        120,250,100-i,intelligence=200,troop_type=TroopType.SHIELD,lineup_position=p)
        for t in ("A","B") for i,p in enumerate(LineupPosition)}
    context = BattleContext(f"yu-lin-{seed}",units,EventBus(),RandomSystem(seed),max_rounds=8)
    context.skill_runtimes.register(create_yu_lin_zhen_runtime("A1"))
    systems = BattleSystems()
    BattleEngine(context=context,systems=systems).run()
    history = context.metadata.get("after_damage_support_history",[])
    recovery = [{"sequence":e.sequence,"round":e.round_no,"source":e.actor_id,
        "target":e.target_id,"actual_recovery":e.payload["actual_recovery"]}
        for e in context.event_bus.history if e.event_type is EventType.TROOPS_RECOVERED
        and e.payload.get("source_skill_id")=="20836"]
    applied = [r for r in history if r.get("kind")=="STATE_GRANT"]
    assert all(1<=r["round"]<=3 and r["target_id"] in ("A1","A2") for r in applied)
    assert all(r["round"]>=5 and r["target_id"]=="A0" and r["provider_id"]=="A1"
        for r in history if r.get("kind")=="RECOVERY")
    row = {"seed":seed,"rounds":context.current_round,"history":history,"recoveries":recovery,
        "barrier_grants":len(applied),"total_actual_recovery":sum(r["actual_recovery"] for r in recovery)}
    (output/f"engine_seed_{seed}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    rows.append({k:row[k] for k in ("seed","rounds","barrier_grants","total_actual_recovery")})
contracts = {name:hashlib.sha256((output/name).read_bytes()).hexdigest()
    for name in ("resistance_contract.md","first_aid_contract.md")}
manifest={"battle_baseline":"6b97b86aab597c73978b11c9118b7b227e09d654",
    "research_main":"d9d20e16c85355d7349bbb6df2b1b148d44292a4",
    "contract_sha256":contracts,"seeds":rows,
    "user_confirmed":["provider troop basis","settled-zero damage eligible","attribute scaling deferred"],
    "engineering_boundaries":["provider live troops read after existing aftermath reactions",
        "no source-description barrier duration means retain until consumed or formation provider defeat",
        "shared recovery eligibility excludes feedback/share/distribution and evasion miss"],
    "provenance":"USER_APPROVED_BASE_VALUE_MODEL / NOT_GAMEPLAY_FROZEN"}
(output/"source_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(rows,ensure_ascii=False))
