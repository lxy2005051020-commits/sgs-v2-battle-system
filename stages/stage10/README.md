# Stage 10 · Persistent State Runtime Integration

当前状态：

```text
Mechanism Research:          COMPLETE
Independent Design Audit R1: FAIL / REPAIR REQUIRED
Design Repair R1-C (Draft V2): COMPLETE
Independent Re-Audit R2:     FAIL / REPAIR REQUIRED
R2-A Authority Recovery:     COMPLETE
R2-A4 Authority Promotion:   PASS (HEAD a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe)
Design Repair R2-B:          COMPLETE
Design Re-Audit R3:          READY / NOT STARTED
Production:                  NOT AUTHORIZED
Design Freeze:               NOT AUTHORIZED
```

当前设计版本：

```text
STAGE10.md
= ARCHITECTURE DESIGN DRAFT V3
= R2-B REPAIR COMPLETE
= READY FOR INDEPENDENT DESIGN RE-AUDIT ROUND 3
```

Stage10 目标仍然是将以下 8 个 persistent state 正式接入 Runtime：

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

- [Stage10 Research Scope](STAGE10_RESEARCH_SCOPE.md)
- [Stage10 Research Matrix](STAGE10_RESEARCH_MATRIX.md)
- [Stage10 Runtime Mapping](STAGE10_RUNTIME_MAPPING.md)
- [Stage10 Open Questions](STAGE10_OPEN_QUESTIONS.md)
- [Stage10 Architecture Design Draft V3](STAGE10.md)
- [Stage10 Independent Design Audit Round 1](STAGE10_DESIGN_AUDIT.md)
- [Stage10 Independent Design Re-Audit Round 2](STAGE10_DESIGN_REAUDIT_R2.md)
- [Stage10 Authority Gap Triage](STAGE10_AUTHORITY_GAP_TRIAGE.md)
- [Stage10 Targeted Research Questions](STAGE10_TARGETED_RESEARCH_QUESTIONS.md)
- [Stage7 → Stage10 Compatibility Addendum](../stage7/STAGE7_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Stage8 → Stage10 Compatibility Addendum](../stage8/STAGE8_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Stage9 → Stage10 Compatibility Addendum](../stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md)
- [Post-Stage9 项目路线](../../POST_STAGE9_RESEARCH_AND_INTEGRATION_ROADMAP.md)

## R2-B repair result

第二轮独立设计审计结果（`STAGE10_DESIGN_REAUDIT_R2.md`）：

```text
BLOCKER   = 2
MAJOR     = 5
MINOR     = 3
HARDENING = 2
VERDICT   = FAIL
```

R2-B 已为全部 Round 2 问题提供显式修复规范：
1. `S10-R2-B01`: 创建 `stages/stage9/STAGE9_STAGE10_COMPATIBILITY_ADDENDUM.md`，维持 Stage9 既有横扫与分担冻结时序。
2. `S10-R2-B02`: 在 Stage9 增补与 `ReactionPermissionPolicy.can_trigger_recovery` 中正式授权 `SourceType.ASSAULT`。
3. `S10-R2-M01`: 权威仓库已通过 R2-A4 正式晋升至 `main` @ `a9a05ceffa2a9489cdc1e0a000a4c27bac81a5fe`，权威同步状态为 `PASS`。
4. `S10-R2-M02`: 明确区分判定所有者（`ExecutionRightSystem`）、分发所有者（`RuleHookSystem`）与执行路由器（`EffectExecutor`），规范类型化中止作用域与 Effect A/B/C 时序。
5. `S10-R2-M03`: 建立 `PersistentSourceSkillGate` 规范映射表，统一定义 `EXTERNAL_LIFECYCLE` 为外部物理生命周期管理。
6. `S10-R2-M04`: 建立 `StateApplicationGenerationId` 端到端跨 DTO/请求/结果/事件的传播矩阵，严格区分快照值与 JIT 动态查询。
7. `S10-R2-M05`: 明确定义战斗结束持续状态清理语义（`StateLifecycleSystem.clear_all_on_battle_end`），严格区分于回合内的游戏机制自然失效。
8. `S10-R2-N01` / `N02` / `N03`: 冻结 `UNIT_ACTION_START` 精确步骤顺序，统一恢复预判定顺序，扩充回归测试方案。
9. `S10-R2-H01` / `H02`: 接受阵亡清理仅一次间谍测试与冻结泳道零实时读取插桩测试。

当前状态：

```text
BLOCKER repair claimed = 2 / 2
MAJOR repair claimed   = 5 / 5
MINOR addressed        = 3 / 3
HARDENING accepted     = 2 / 2
```

不能写：

```text
DESIGN PASS
DESIGN FROZEN
IMPLEMENTATION AUTHORIZED
```

最终是否接受由 Round 3 独立设计再审计决定。

## Key architecture contracts in Draft V3

```text
1. Stage7 death-abort compatibility reopen & ExecutionRight typed abort scopes
2. Stage8 FROZEN_APPLICATION limited compatibility reopen
3. Stage9 aftermath settlement & Cleave/ASSAULT compatibility addendum
4. ActionProgressTracker exact execution sequence at UNIT_ACTION_START
5. Physical expiry at last eligible ActionStart window completion vs battle-end clear_all_on_battle_end
6. One synchronous DefeatCleanupPort across all death-capable troop-loss paths
7. Battle-authoritative SkillRuntimeRegistry keyed by (owner, SkillSlot)
8. Physical StateInstance identity separated from StateApplicationGenerationId with end-to-end propagation
9. PersistentSourceSkillGate normative family mapping table
10. FIRST_AID zero-loss resolved-hit eligibility + ASSAULT pursuit recovery authorized
11. Normalized pre-RNG recovery admission gate sequence
12. One shared DamageAftermathPort for standard/Cleave-compatible aftermath invoked at reconciled Stage9 checkpoints
13. Dependency and BattleSystems composition DAG V3
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
Stage10 Architecture Draft V3
+ Stage7 compatibility addendum
+ Stage8 compatibility addendum
+ Stage9 compatibility addendum
↓
Stage10 Independent Design Re-Audit Round 3
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

R2-B 本身严禁修改任何生产代码或测试代码。
