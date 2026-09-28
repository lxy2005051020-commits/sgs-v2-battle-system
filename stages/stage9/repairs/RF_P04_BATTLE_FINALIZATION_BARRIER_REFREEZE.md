# RF-P04 Repair Record

## BATTLE_FINALIZATION_BARRIER_REFREEZE

```text
Package: RF-P04
Level: A (Architecture-level P0 Repair Package)
Priority: P0
Execution Type: EMPIRICAL RESEARCH, BARRIER SPECIFICATION, CONTRACT RE-FREEZE
Need New Extractor: YES — executed and archived:
  - extract_battle_end_normal_attack.py
  - extract_battle_end_normal_attack_deep.py
  - extract_battle_end_cleave.py
  - extract_cleave_commander_death_fixed.py
  - extract_battle_end_counter.py
  - extract_battle_end_chain.py
  - consolidate_finalization_evidence.py
Repair Date: 2026-09-13
Final Verdict: RF-P04 CLOSED
Affected Findings:
  CBS9-B03  = CLOSED (NormalAttack #1 battle ending strictly blocks Combo #2; 0/10,745 second attack admissions)
  CLVS9-B04 = CLOSED (Cleave across death/finalization resolved across Cases A/B/C/D/E; 5/5 secondary commander continuation)
  CTS9-H02  = CLOSED / HARDENED (Admitted sibling counter executes 0-loss before finalization barrier)
  DSTS9-B02 = DUAL-STATUS:
    Empirical Status: OPEN / UNOBSERVED (0/32,999 corpus cases)
    Runtime Status:   CLOSED BY EXPLICIT ENGINEERING DEFAULT (Transaction completion before barrier)
```

---

## 1. Repository Baseline

Before modification, exact `main` refs across both repositories were re-read and verified:

### Battle repository
```text
Repository:
lxy2005051020-commits/sgs-v2-battle-system

repair-before exact main HEAD:
2e21b2f368c8aa6202f8f8e48f10e283a8c17615
repair(stage9): re-freeze partition transaction death semantics
```

### State-mechanics research repository
```text
Repository:
lxy2005051020-commits/sgs-state-mechanics-research

repair-before exact main HEAD:
6a0d8e76c028be9bc1df11ba7f1a2b215f56f0a4
docs(damage-share): re-freeze lethal target transaction semantics
```

Both repositories confirmed `HEAD == origin/main` with clean working trees.

---

## 2. Affected Findings & Dispositions

RF-P04 targets and arbitrates the core coordination boundary between death events and global battle finalization:

```text
CBS9-B03:
普攻第 1 击击杀敌方主将或全体敌军时，连击检查点、cfg 230、cfg 733 与第 2 击普攻的准入关系；
分离暂时无合法目标与战斗胜负终局判定。
-> DISPOSITION: CLOSED (0/10,745 second attacks; 100% BLOCKED after victory latch)

CLVS9-B04:
群攻跨单位死亡与战斗终局的完整行为矩阵（主目标致死、攻击者致死、次要目标致死、次要主将致死、连环致死）。
-> DISPOSITION: CLOSED (All 5 cases empirically verified / codified)

CTS9-H02:
反击批次中 C1 击杀原反击目标主将时，已准入兄弟 C2 的执行行为与终战屏障时机。
-> DISPOSITION: CLOSED / HARDENED (C2 executes with 0 loss; victory finalized after batch)

DSTS9-B02:
伤害分摊中主将作为承担者阵亡时对后续承担者及原目标的提交影响。
-> DISPOSITION: DUAL STATUS:
   Empirical: OPEN / UNOBSERVED (0/32,999 corpus cases)
   Runtime:   CLOSED BY EXPLICIT ENGINEERING DEFAULT (Transaction completion before barrier)
```

---

## 3. Authority Anchors

RF-P04 strictly builds upon the six authoritative anchors established across Stage 9:
1. **CHAIN Anchor** (`STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`):
   主将在铁索连环单次广播中途阵亡，已连接的后续槽位继续执行并提交铁索伤害（159/159 战报实证），单次遍历完成后才到达终战屏障。
2. **COUNTER Anchor** (`STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md`):
   反击批次 `CounterBatch = [C1, C2]` 已准入兄弟反应不随目标死亡溯及注销，出栈对已死目标提交 0 损耗，批次排空后才到达终战屏障。
3. **COMBO Anchor** (`RF-P03` / `CBS9-B01`):
   普通攻击中途阵亡注销未准入的未来分支（Assault, Combo Checkpoint, Combo #2）。
4. **DAMAGE SHARE Anchor** (`RF-P05` / `SHS9-B02`):
   分担微事务在原目标因 $D_{\text{target}}$ 死亡时触发 `TARGET_DEATH_INTERRUPT`，挂起的分担者损耗作废（0 损耗），事务局部终止。
5. **DISTRIBUTION Anchor** (`RF-P05` / `DSTS9-B02 Control`):
   普通承担者副将阵亡不中断后续承担者与原目标的规划提交（`战报_596995` 证实）。
6. **CLEAVE Anchor** (`RF-P07` / `CLVS9-B02` / `CLVS9-B03`):
   多效果按 `EFFECT_MAJOR_ORDER` 组织，每个效果内部次要目标按 `GLOBAL_SLOT_ASCENDING` 组织，执行前执行 JIT 存活校验。

---

## 4. Finalization Vocabulary

RF-P04 正式定义并统一以下六大终战核心术语：

1. **`UnitDeathFact`**：
   单位兵力降至 0（`currentTroops == 0`，发射 `cfg 163`）。不可撤销的底层物理事实，**不直接等于战斗终结**。
2. **`VictoryConditionSatisfied`**：
   世界状态满足胜负逻辑判定（敌方主将阵亡或全体敌军兵力归 0）。胜负状态被锁定（`VictoryConditionLatched`），**严禁产生未来外层工作项**，但**此时战斗不一定已完成 Finalization**。
3. **`CurrentOperation`**：
   当前正在执行且已取得执行权的操作上下文（`ChainTraversal`, `CounterBatch`, `CleaveEffect`, `DamagePartitionTransaction`, `CurrentDamageInstance`）。
4. **`AdmittedWork`**：
   已正式加入当前操作容器或批次队列的工作单元，不随外部目标死亡自动全局作废，仅受自身执行时局部门禁（Local Liveness Gate）约束。
5. **`FutureBranch`**：
   尚未取得准入凭证的未来流程（突击战法、连击第2击、新行动调度等）。
6. **`BattleFinalized`**：
   战斗正式终态：`NO_NEW_WORK`, `NO_NEW_ACTION`, `NO_NEW_REACTION`，胜负结果固化，日志发射完成。

---

## 5. Evidence Corpus

本研究全量扫描了 `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON` 中的 **32,999 份完整战报**，建立全量证据库：
- 证据文件：`stages/stage9/research/battle_finalization_barrier/BATTLE_FINALIZATION_EVIDENCE.json`
- 详细报告：`stages/stage9/research/battle_finalization_barrier/RF_P04_BATTLE_FINALIZATION_RESEARCH_REPORT.md`

---

## 6. Chain Anchor

- 扫描样本：32,999 份战报中存在 333 例铁索连环传播中主将阵亡样本。
- 其中主将阵亡后仍有待传播槽位的样本：**159 例**。
- 实证结果：**159 / 159 (100.0%)** 样本中，主将阵亡后铁索广播**继续传播至后续合法连环副将槽位并完成扣兵**。遍历完全结束后才移交终局胜负宣告（`cfg 157`）。

---

## 7. Counter Anchor

- 继承 RF-P03 与 Counter P0：反击批次内兄弟反应已获准入权。
- 目标主将阵亡时，后续已准入兄弟反击依序出栈，对已死目标提交 0 损耗（committed loss = 0）。
- 若反击者自身在出栈前死亡，则失败自身局部门禁而取消。
- 批次结束后移交终战屏障。`CTS9-H02` 获得完整语义闭环。

---

## 8. Combo Battle-ending Evidence (`CBS9-B03`)

- 全盘扫描 32,999 战报：
  - 第 1 击普攻导致战斗结束：**15,393 例**。
  - 其中直接击杀主将：**10,745 例**。
  - **第 2 击普攻发起率**：
    $$\mathbf{Attack\ \#2\ (cfg\ 9)\ After\ Commander\ Kill:\ 0\ /\ 10,745\ (0.00\%)}$$
  - 在 10,745 例中，410 例在主将阵亡后抛出了 `cfg 230` 连击状态自消耗日志，但在尝试准入第 2 击普攻时，因胜负状态锁定且选敌门禁无合法目标，**第 2 次普通攻击坚决未准入（100% 拦截）**。
  - 其余 10,335 例直接跳过连击检查点，进入行动结束（`cfg 733`）、主将连带溃散扣兵（`cfg 209`）与终局宣告（`cfg 157`）。
- **裁决**：
  - 严格区分“战斗未终结时的暂时无合法目标”（普攻安全跳过，战斗继续）与“胜负条件达成”（锁定终战屏障，取消一切未来分支）。
  - Finding **`CBS9-B03 = CLOSED`**。

---

## 9. Cleave Battle-ending Evidence (`CLVS9-B04`)

全量扫描 32,999 战报，完整覆盖 CLVS9-B04 的全部 5 种子场景：
1. **Case A (主目标致死)**：主目标受普攻死亡，群攻**100% 准入并执行于次要目标**（169/169 战报实证）。
2. **Case B (攻击者致死)**：攻击者在群攻下游反应阵亡，后续未开始的群攻效果或次要目标因攻击者存活门禁失败而取消（2/2 战报实证）。
3. **Case C (次要目标致死)**：次要目标阵亡完成当前微步，后续次要目标执行 JIT 存活重校验（RF-P07 闭环）。
4. **Case D (次要主将致死)**：主将作为次要目标受到群攻死亡，在所有 5 例存在后续规划次要副将的战报中（`战报_1964609`, `战报_2239736`, `战报_2239938`, `战报_3454985`, `战报_786228`），**后续规划的次要副将 100% 照常受到群攻扣兵**！
5. **Case E (连环致死)**：群攻派生铁索连环遵从铁索原子遍历规则。
- **Cleave 准入模型**：
  每个 `CleaveEffect` 在开始执行时一次性准入其次要目标规划；胜负达成后当前效果排空已准入次要目标，尚未准入的后续独立群攻效果作为未来分支坚决禁止准入。
- Finding **`CLVS9-B04 = CLOSED`**。

---

## 10. Partition Inputs

- 继承 RF-P05 成果：
  - DAMAGE_SHARE：目标阵亡触发 `TARGET_DEATH_INTERRUPT`，丢弃挂起分担份额（128/128 战报实证）。
  - 微事务达成局部终止边界后移交终战屏障。

---

## 11. Distribution Empirical Gap

- 在 RF-P05 中扫描 32,999 战报库，主将作为分摊承担者阵亡的样本为 **0 例**。
- 本轮再次核验，真实战报库中依然无法观察到主将作为分摊承担者阵亡的直接用例。
- 绝不伪造或捏造实证。

---

## 12. Engineering-default Decision

针对 `DSTS9-B02` 严格执行双状态分栏：
1. **Empirical Status**：保持 `DSTS9-B02 = EMPIRICALLY UNOBSERVED / OPEN`。
2. **Runtime Status**：采纳显式工程默认：
   > **`PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)`**：
   > 已合法准入的 `DistributionTransaction` 将按照既定承担者与目标规划完成局部提交，然后向外暴露状态变更，交由全局终战屏障统一裁决。未来如有新实证战报推翻此假设，可直接替换局部策略而不影响全局架构。
- 此项决策使模拟器具备 100% 确定性，消除运行时歧义，同时诚实保留研究事实，**不阻塞 Stage 9 设计准入**。

---

## 13. Victory Latch Semantics

- 当 `UnitDeathFact` 导致敌方主将阵亡或全体敌军阵亡时，系统置 `victory_latched = True`。
- **锁定效果**：
  1. 拒绝一切未来宏观行动调度（Next Action Scheduling BLOCKED）；
  2. 拒绝一切未准入未来分支（Assault BLOCKED, NormalAttack #2 BLOCKED）；
  3. 允许当前正在执行的操作容器排空其内部已准入工作项；
  4. 排空后统一执行主将溃散扣兵（`cfg 209`）并在终战屏障处输出终局宣告（`cfg 157`）。

---

## 14. Admission Gate

| 工作项 (Work Item) | 准入时机 (Admission Point) | 胜负锁定后准入状态 | 执行时局部门禁 | 终战屏障归属 |
|---|---|---|---|---|
| **DamageInstance** | 伤害派生时 | 允许（微步提交） | 目标已进入结算 | 微步后评估胜负 |
| **ShareTransaction** | 受到伤害时 | 允许（微事务内） | 目标死亡触发截断 | 事务终止 |
| **DistributionTransaction**| 受到伤害时 | 允许（微事务内） | 参与者存活 | 事务规划提交完毕 |
| **ChainTraversal** | 触发伤害后 | **禁止新触发**；遍历允许排空 | 节点存活 | 槽位遍历完毕 |
| **CounterBatch** | 普攻命中时 | **禁止新批次**；兄弟允许出栈 | 自身存活；死目标0损 | 批次出栈完毕 |
| **CleaveEffect** | 普攻伤害后 | **允许排空**次要目标队列 | 次要目标 JIT 存活 | 目标队列遍历完毕 |
| **Next CleaveEffect** | 前一效果后 | **禁止准入**（取消） | 攻击者存活 | N/A |
| **Assault Dispatch** | 普攻结束后 | **禁止准入**（取消） | 攻击者存活且有目标 | N/A |
| **Combo Checkpoint** | #1 结束后 | 仅状态自消耗；**禁止开启 #2** | 攻击者存活有Grant | 行动结束 |
| **NormalAttack #2** | 检查点通过后| **禁止准入（100% 拦截）** | 存在存活敌方主将 | N/A |

---

## 15. Operation Completion Matrix

| Operation | Admission Point | Completion Boundary | Death Inside Operation | Victory Latch Effect |
|---|---|---|---|---|
| **DamageInstance** | 伤害计算起点 | 扣兵与日志发射 | 提交 `UnitDeathFact` | 微步必定完成提交 |
| **Share** | 伤害计算完成时 | 目标扣兵 + 分担者扣兵 | 目标阵亡触发截断 | 丢弃分担份额，事务终结 |
| **Distribution** | 伤害计算完成时 | 承担者扣兵 + 目标扣兵 | 承担者阵亡继续提交 | 工程默认排空规划提交 |
| **Chain** | 触发节点伤害后 | 单次遍历所有连环槽位 | 主将阵亡继续传播剩余槽位 | 遍历完全排空后终战 |
| **CounterBatch** | 普攻命中触发时 | 批次内所有 Ci 执行完毕 | 目标阵亡提交 0 损耗 | 批次完全出栈后终战 |
| **CleaveEffect** | 主普攻伤害后 | 遍历完所有已规划次要目标 | 主将阵亡继续剩余次要目标 | 排空次要目标后终战 |
| **NormalAttack** | 行动调度起点 | 普攻同步生命周期结束 | 主将阵亡取消突击与连击 | 普攻 #1 结束后终战 |
| **Action** | 回合调度起点 | ACTION_END 边界 | 主将阵亡取消剩余动作 | 行动截断并终战 |

---

## 16. Finalization State Machine

```text
[ RUNNING ]
    │
    ▼ (UnitDeathFact recorded, cfg 163)
[ VICTORY_CONDITION_LATCHED ]
    │  (Invariants: No future branch / action admitted)
    │
    ▼
[ DRAIN_ALLOWED_ADMITTED_WORK ]
    │  - Drain Chain traversal slots
    │  - Drain CounterBatch siblings (0-loss on dead)
    │  - Drain CleaveEffect secondary targets (JIT liveness)
    │  - Finish DistributionTransaction planned commits
    │
    ▼
[ PROCESS_COMMANDER_COLLATERAL ] (cfg 209)
    │
    ▼
[ FINALIZATION_BARRIER_REACHED ] (cfg 733, cfg 157)
    │
    ▼
[ BATTLE_FINALIZED ] (Terminal State)
```

---

## 17. Shared Finalization P0

在 `stages/stage9/research/core_arbitration_v2/` 下创建共享终战屏障核心合同：
- 文件：`STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md`
- 职责：独占定义死亡事实、胜负锁定、已准入排空、未来门禁与终态屏障。严禁底层数值系统与机制系统直接写 `BattleFinalized = True`。

---

## 18. Mechanism P0 Changes

1. **`STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`**：
   - Section 28 更新：正式标记 `CLVS9-B04 = CLOSED`，冻结 Case A/B/C/D/E，状态晋升为 `FULL CONTRACT FROZEN`。
2. **`states/functional/cleave/MECHANISM_CONTRACT.md`**：
   - Header 与 Section 7 同步更新：标记 `CLVS9-B04 = CLOSED`，状态晋升为 `FULL CONTRACT FROZEN`。
3. **`states/functional/combo/MECHANISM_CONTRACT.md`**：
   - Header 与 Section 25 更新：标记 `CBS9-B03 = CLOSED`，新增 Section 26 冻结终战与无目标截断规则，状态晋升为 `FULL CONTRACT FROZEN`。
4. **`STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md`**：
   - Section 19 更新：显式确立 `DSTS9-B02` 双状态分栏（实证保持 OPEN，运行层工程默认封闭）。
5. **`STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md`**：
   - Rule 7 更新：终战委托正式指向 `STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md` 并闭环。
6. **`STAGE9_CORE_ARBITRATION_RULES_V2.md`**：
   - 引用列表新增战斗终结屏障核心合同。

---

## 19. Regression Contract

模拟器必须实现并通过 6 项强制终战回归测试：
1. `FINAL_01_CHAIN_COMMANDER_DEATH`：主将在铁索第一节点阵亡，已连接副将继续受到铁索伤害，遍历完成后终战。
2. `FINAL_02_COUNTER_SIBLING`：C1 击杀反击目标主将，C2 对死目标执行 0 损耗提交，批次完成后终战。
3. `FINAL_03_COMBO_BATTLE_END`：第 1 击击杀敌方主将，第 2 击普攻坚决不发起。
4. `FINAL_04_CLEAVE_COMMANDER_SECONDARY`：主将在次要目标位阵亡，后续次要副将继续受到群攻伤害，排空后结算主将溃散扣兵并终战。
5. `FINAL_05_SHARE_COMMANDER_TARGET`：受保护主将因 $D_{\text{target}}$ 阵亡，挂起分担作废（0 损耗），事务终止后终战。
6. `FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT`：主将作为分摊承担者阵亡，依据工程默认完成规划提交后终战。

---

## 20. Remaining Research Debt

```text
DSTS9-B02: Commander Participant Lethal Case in Distribution
- Empirical Status: OPEN / UNOBSERVED in 32,999 corpus
- Runtime Status:   CLOSED BY EXPLICIT ENGINEERING DEFAULT
- Isolation:        Fully isolated behind replaceable policy in STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md
```

---

## 21. Stage9 Design Admission

```text
================================================================================
STAGE 9 DESIGN ADMISSION ASSESSMENT:
  Remaining Architecture Blockers: 0
  Remaining Runtime Ambiguities:   0
  Empirical Debt Isolated:         1 (DSTS9-B02, deterministic default active)
================================================================================
STAGE 9 DESIGN ADMISSION = READY
================================================================================
```

---

## 22. Changed Files

### Battle Repository (`lxy2005051020-commits/sgs-v2-battle-system`)
- `stages/stage9/research/battle_finalization_barrier/extract_battle_end_normal_attack.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/extract_battle_end_normal_attack_deep.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/extract_battle_end_cleave.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/extract_cleave_commander_death_fixed.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/extract_battle_end_counter.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/extract_battle_end_chain.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/consolidate_finalization_evidence.py` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_END_COMBO_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_END_COMBO_DEEP_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_END_CLEAVE_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/CLEAVE_COMMANDER_DEATH_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_END_COUNTER_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_END_CHAIN_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/BATTLE_FINALIZATION_EVIDENCE.json` [NEW]
- `stages/stage9/research/battle_finalization_barrier/RF_P04_BATTLE_FINALIZATION_RESEARCH_REPORT.md` [NEW]
- `stages/stage9/research/core_arbitration_v2/STAGE9_BATTLE_FINALIZATION_BARRIER_CONTRACT.md` [NEW]
- `stages/stage9/research/core_arbitration_v2/STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md` [MODIFIED]
- `stages/stage9/research/core_arbitration_v2/STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md` [MODIFIED]
- `stages/stage9/research/core_arbitration_v2/STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md` [MODIFIED]
- `stages/stage9/research/core_arbitration_v2/STAGE9_CORE_ARBITRATION_RULES_V2.md` [MODIFIED]
- `stages/stage9/repairs/RF_P04_BATTLE_FINALIZATION_BARRIER_REFREEZE.md` [NEW]

### State Research Repository (`lxy2005051020-commits/sgs-state-mechanics-research`)
- `states/functional/cleave/MECHANISM_CONTRACT.md` [MODIFIED]
- `states/functional/combo/MECHANISM_CONTRACT.md` [MODIFIED]

---

## 23. Commits

1. **State Repository Commit**:
   ```text
   docs(finalization): freeze combo and cleave battle finalization barriers
   ```
2. **Battle Repository Research Commit**:
   ```text
   research(stage9): resolve battle finalization barriers
   ```
3. **Battle Repository Repair Commit**:
   ```text
   repair(stage9): freeze battle finalization barrier contract
   ```

---

## 24. Final Verdict

```text
================================================================================
RF-P04 FINAL VERDICT: RF-P04 CLOSED
  - CBS9-B03  = CLOSED
  - CLVS9-B04 = CLOSED
  - CTS9-H02  = CLOSED / HARDENED
  - DSTS9-B02 = EMPIRICAL OPEN / RUNTIME CLOSED BY ENGINEERING DEFAULT

STAGE 9 ARCHITECTURE-LEVEL P0 PACKAGES: ALL RESOLVED / FROZEN
STAGE 9 DESIGN ADMISSION = READY
================================================================================
```
