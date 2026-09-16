# Stage 10 · Persistent State Runtime Integration

当前状态：

```text
Mechanism Research:          COMPLETE
Authority:                   PROMOTED / PINNED (HEAD a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe)
Architecture:                FROZEN (STAGE10_DESIGN_FREEZE.md)
Final Freeze-Gate Audit:     PASS (BLOCKER=0, MAJOR=0, MINOR=0, HARDENING=2)
Build:                       NOT STARTED
Production:                  NOT IMPLEMENTED
```

当前设计版本：

```text
STAGE10.md
= STAGE10 ARCHITECTURE DESIGN FROZEN
= FROZEN BY STAGE10_DESIGN_FREEZE.md
= AUDITED BY STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md (PASS)
= NEXT STEP: Stage10 Build Prompt Preparation
```

Stage10 目标是将以下 8 个 persistent state 正式接入 Runtime：

```text
690072 BURN / 灼烧
690073 FLOOD / 水攻
690074 POISON / 中毒
690075 ROUT / 溃逃
690076 SANDSTORM / 沙暴
690077 REBELLION / 叛逃
690078 FIRST_AID / 急救
690079 RECUPERATION / 休整
```

## 当前文档

- [Stage10 Design Freeze Record](STAGE10_DESIGN_FREEZE.md)
- [Stage10 Final Independent Design Freeze-Gate Audit](STAGE10_FINAL_DESIGN_FREEZE_GATE_AUDIT.md)
- [Stage10 Architecture Design (Frozen)](STAGE10.md)
- [Stage10 Research Scope](STAGE10_RESEARCH_SCOPE.md)
- [Stage10 Research Matrix](STAGE10_RESEARCH_MATRIX.md)
- [Stage10 Runtime Mapping](STAGE10_RUNTIME_MAPPING.md)
- [Stage10 Open Questions](STAGE10_OPEN_QUESTIONS.md)
- [Stage10 Independent Design Audit Round 1](STAGE10_DESIGN_AUDIT.md)
- [Stage10 Independent Design Re-Audit Round 2](STAGE10_DESIGN_REAUDIT_R2.md)
- [Stage10 Independent Design Re-Audit Round 3](STAGE10_DESIGN_REAUDIT_R3.md)
- [Stage10 Authority Gap Triage](STAGE10_AUTHORITY_GAP_TRIAGE.md)
- [Stage10 Targeted Research Questions](STAGE10_TARGETED_RESEARCH_QUESTIONS.md)
- [Stage7 → Stage10 Compatibility Addendum](../stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Stage8 → Stage10 Compatibility Addendum](../stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Stage9 → Stage10 Compatibility Addendum](../stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Post-Stage9 项目路线](../../POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)

## R3-B repair result

第三轮独立设计审计结果（`STAGE10_DESIGN_REAUDIT_R3.md`）：

```text
BLOCKER   = 1
MAJOR     = 2
MINOR     = 1
HARDENING = 0
VERDICT   = FAIL
```

R3-B 已为全部 Round 3 问题提供显式修复规范：
1. `S10-R3-B01`: 在 §4.2、§4.3 与 §4.4 中彻底区分目标阵亡（`REJECT_CURRENT(reason=TARGET_DEFEATED)`）与所有者阵亡（`ABORT_OWNER_STATE_REMAINDER(reason=OWNER_DEFEATED)`）。目标阵亡仅拒绝针对该阵亡目标的当前意图，活着的所有者对其他存活目标的意图继续执行；所有者阵亡时丢弃该阵亡所有者在本批次中的所有剩余意图，但批次内其他存活实体的意图正常执行。
2. `S10-R3-M01`: 在 §18.1 与 §22 中引入 `RecoveryOpportunityKind` 枚举（`FIRST_AID_AFTER_DAMAGE` 与 `RECUPERATION_ACTION_START`）。明确 Gate 2 准入条件对 `FIRST_AID` 必须存在有效 `DamageAftermathFact`，但对 `RECUPERATION` 为 `NOT_APPLICABLE`（在 `UNIT_ACTION_START` 直接准入，无需伤害事实）。
3. `S10-R3-M02`: 在 §4.1 中定义强类型 `RuleIntentExecutionDescriptor` 数据类，由 `TriggerSystem` 构造并随 `RuleIntent` 传递，统一 `ExecutionRightSystem.evaluate_rule_intent(descriptor, context) -> ExecutionRightDecision` 签名，彻底消除 duck-typing 或属性探测。
4. `S10-R3-N01`: 在 §18.0 中确认 `sgs_v2` 原生 `RandomSystem.chance`（`self.random() < probability`）对所有 \(p \in [0.0, 1.0]\) 均恒定消耗一次 RNG 浮点数，零短路，无需 reopen Stage 2，保持代码零改动。

当前状态：

```text
BLOCKER repair claimed = 1 / 1
MAJOR repair claimed   = 2 / 2
MINOR addressed        = 1 / 1
HARDENING accepted     = 0 / 0
```

不能写：

```text
DESIGN PASS
DESIGN FROZEN
IMPLEMENTATION AUTHORIZED
```

最终是否接受由最终独立设计冻结前审计（Final Freeze-Gate Audit）决定。

## Key architecture contracts in Draft V4

```text
1. Stage7 death-abort compatibility reopen & ExecutionRight typed abort scopes
2. Target Defeat vs Owner Defeat scope separation (REJECT_CURRENT vs ABORT_OWNER_STATE_REMAINDER)
3. Normative A/B/C/D execution timelines with typed RuleIntentExecutionDescriptor
4. Stage8 FROZEN_APPLICATION limited compatibility reopen
5. Stage9 aftermath settlement & Cleave/ASSAULT compatibility addendum
6. RecoveryOpportunityKind differentiation: FIRST_AID requires aftermath fact, RECUPERATION is action-start
7. ActionProgressTracker exact execution sequence at UNIT_ACTION_START
8. Physical expiry at last eligible ActionStart window completion vs battle-end clear_all_on_battle_end
9. One synchronous DefeatCleanupPort across all death-capable troop-loss paths
10. Battle-authoritative SkillRuntimeRegistry keyed by (owner, SkillSlot)
11. Physical StateInstance identity separated from StateApplicationGenerationId with end-to-end propagation
12. PersistentSourceSkillGate normative family mapping table
13. Native RandomSystem.chance one-draw invariant documented (zero Stage 2 reopen)
14. One shared DamageAftermathPort for standard/Cleave-compatible aftermath invoked at reconciled Stage9 checkpoints
15. Dependency and BattleSystems composition DAG V3
```

## Authority synchronization: PASS

Gameplay Authority 已正式同步：

```text
lxy2005051020-commits/sgs-state-mechanics-research
branch: main
canonical authoritative HEAD: a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe
```

包含 S10-TR-01、S10-TR-02、S10-TR-03 完整研究工件与 FIRST_AID 零战损合同样本，权威同步检查通过。

## Next gate

仅允许以下工作流：

```text
Stage10 Architecture Draft V4
+ Stage7 compatibility addendum
+ Stage8 compatibility addendum
+ Stage9 compatibility addendum
↓
Stage10 Final Independent Design Freeze-Gate Audit
↓
repair again if required
↓
PASS only
↓
Stage10 Design Freeze
↓
Build Prompt
↓
production implementation
```

R3-B 本身严禁修改任何生产代码或测试代码。

