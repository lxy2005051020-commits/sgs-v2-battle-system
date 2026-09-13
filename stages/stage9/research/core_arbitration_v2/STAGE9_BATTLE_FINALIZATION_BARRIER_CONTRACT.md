# Stage 9 战斗终结屏障核心合同 (Battle Finalization Barrier Contract)

```text
Status: FROZEN
Freeze Date: 2026-09-13
Package: RF-P04
Authority Level: P0 Shared Arbitration Rule
Dependencies:
  - STAGE9_EXECUTION_RIGHT_AND_DEATH_SCOPE_CONTRACT.md (RF-P03)
  - STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md (CHAIN P0)
  - STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md (COUNTER P0)
  - STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md (CLEAVE P0)
  - STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md (SHARE P0 / RF-P05)
  - STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md (DISTRIBUTION P0 / RF-P05)
Resolves Findings:
  - CBS9-B03 = CLOSED
  - CLVS9-B04 = CLOSED
  - CTS9-H02  = CLOSED / HARDENED
  - DSTS9-B02 = EMPIRICAL OPEN / RUNTIME CLOSED BY ENGINEERING DEFAULT
```

---

## 1. 范围与边界

本合同为 `sgs-v2-battle-system` 与状态机制研究仓库中统管**单位死亡事实、胜负条件判定、已准入操作排空、未来分支准入门禁与战斗终结屏障**的最高权威标准。

本合同**不复制**各具体机制的局部运行算法（如铁索遍历数学、反击优先级判定、群攻次要目标排序、分担与分摊公式），仅统领其在面临死亡与胜负转换时的终结与屏障接口。

---

## 2. 核心术语与语义层次 (Vocabulary & Hierarchy)

系统必须严格分离以下六个语义层次：

1. **`UnitDeathFact`（单位死亡事实）**：
   - 某单位兵力降至 0（`currentTroops == 0`，发射 `cfg 163`）。
   - 属于不可撤销的底层数值事实。

2. **`VictoryConditionSatisfied`（胜负条件达成）**：
   - 当前世界状态满足胜负判定条件（敌方主将阵亡或敌方全体合法战斗单位阵亡）。
   - 状态被锁定（`VictoryConditionLatched`），禁止产生任何未来外层工作项。

3. **`CurrentOperation`（进行中操作容器）**：
   - 当前正在执行且持有执行权的操作上下文（如 `ChainTraversal`, `CounterBatch`, `CleaveEffect`, `DamagePartitionTransaction`）。

4. **`AdmittedWork`（已准入工作项）**：
   - 已正式加入当前操作容器队列的子项。不随外部目标死亡而溯及既往作废，仅受自身执行时局部门禁校验。

5. **`FutureBranch`（未准入未来分支）**：
   - 尚未取得准入凭证的未来流程（突击战法分发、连击第2击、后续宏观行动、新派生反应等）。

6. **`BattleFinalized`（战斗正式终态）**：
   - 战斗彻底闭环：不再调度任何新工作、新行动或新反应，胜负日志发射，结果不可变更。

---

## 3. 两大核心不变量 (Core Invariants)

### Rule 1: 胜负达成不等于战斗终结 (VictoryConditionSatisfied != BattleFinalized)
> **`VictoryConditionSatisfied` becomes true while an already-admitted operation is still completing.**
> 胜负条件可在宏观或微观操作执行中途被满足，但系统决不在任意一个死亡事件后立即退出全局函数。

### Rule 2: 终战必须在明确的屏障处发生 (Explicit Finalization Barrier)
> **Battle finalization occurs ONLY at an explicit Finalization Barrier after permitted admitted operations have drained.**
> 只有当当前允许排空的已准入操作容器全部清空，并完成必要的主将连带事实提交后，全局终战才正式生效。

---

## 4. 机制局部 P0 引用与操作完成边界 (Operation Completion Boundaries)

终战屏障不抹平各机制自身的局部完成语义，各操作容器由其自身权威 P0 统领，终战屏障仅在操作到达其完成边界后接入：

### 4.1 铁索连环 (ChainTraversal)
- **权威属主**：`CHAIN P0`
- **准入时机**：触发节点伤害结算完成时。
- **完成边界**：单次遍历完成所有已连接槽位（One-pass slot traversal）。
- **死亡与屏障语义**：
  若主将在广播遍历中途阵亡（如连环槽位 1 阵亡）：
  - 剩余合法槽位（如连环槽位 2）**继续执行并提交铁索伤害**（159/159 战报实证）。
  - 遍历完成后，移交终战屏障。

### 4.2 反击反应批次 (CounterBatch)
- **权威属主**：`COUNTER P0`
- **准入时机**：普通攻击命中触发反击时快照批次 `CounterBatch = [C1, C2, ...]`.
- **完成边界**：批次内所有兄弟反击依序出栈完毕。
- **死亡与屏障语义**：
  若 C1 击杀原攻击者（包括攻击方主将）：
  - 已准入兄弟 C2 依然依序出栈，因目标已死，执行“对已死目标提交 0 损耗”，记录执行事实。
  - 若反击者自身在执行前死亡，则失败其局部门禁并跳过。
  - 批次完全出栈完毕后，移交终战屏障（`CTS9-H02` 封闭）。

### 4.3 群攻效果队列 (CleaveEffect)
- **权威属主**：`CLEAVE P0`
- **准入时机**：普通攻击主目标伤害结算完成时，当前生效的 `CleaveEffect` 生成其 `GLOBAL_SLOT_ASCENDING` 次要目标规划。
- **完成边界**：当前 `CleaveEffect` 的次要目标规划遍历完成。
- **死亡与屏障语义**：
  - **主目标阵亡 (Case A)**：主目标受普攻死亡，不阻止群攻对次要目标的准入与执行（169/169 战报实证）。
  - **次要主将阵亡 (Case D)**：主将作为次要目标受到群攻死亡，**当前群攻效果内部已规划的剩余次要目标（副将）继续执行群攻**（5/5 战报实证）。
  - **后续不同源群攻效果**：若攻击者配有多个群攻技能，在第一效果中主将已死且胜负锁定后，后续未开始的群攻效果作为未来分支**禁止准入**。
  - 当前效果排空后，移交终战屏障（`CLVS9-B04` 封闭）。

### 4.4 伤害分担微事务 (ShareTransaction)
- **权威属主**：`DAMAGE_SHARE P0 / RF-P05`
- **完成边界**：`TARGET-FIRST` 顺序下，目标扣兵后分担者扣兵完成。
- **死亡与屏障语义**：
  若目标因 $D_{\text{target}}$ 阵亡，触发 `TARGET_DEATH_INTERRUPT`，丢弃挂起的分担份额（分担者损耗 0，128/128 战报实证）。微事务终止，移交终战屏障。

### 4.5 伤害分摊微事务 (DistributionTransaction)
- **权威属主**：`DISTRIBUTION P0 / RF-P05`
- **完成边界**：`PARTICIPANTS-FIRST` 顺序下，所有承担者及原目标扣兵提交完成。
- **死亡与屏障语义**：
  - 普通承担者阵亡：后续承担者与原目标继续执行提交（战报实证闭环）。
  - **主将承担者阵亡 (`DSTS9-B02`)**：
    - 实证状态：`EMPIRICALLY UNOBSERVED`（32,999 战报库中无主将作为分摊承担者阵亡的样本）。
    - **模拟器工程默认规范 (`PROJECT_RUNTIME_DEFAULT`)**：
      已合法准入的微事务将按既定规划完成其余承担者和原目标的提交，随后移交终战屏障。未来如有新实证战报推翻此项，可直接替换局部策略。

### 4.6 普通攻击与连击分支 (NormalAttack & Combo)
- **权威属主**：`Core Lifecycle / COMBO P0`
- **死亡与屏障语义 (`CBS9-B03`)**：
  - 必须严格区分：
    - `Temporary No Legal Target`（战斗未结束时的暂时无合法目标）：普攻无法锁定目标，安全跳过，战斗保持进行。
    - `VictoryConditionSatisfied`（敌方主将阵亡或全体阵亡）：胜负条件满足，锁定状态。
  - 第 1 击普通攻击满足胜负条件时：
    - 严禁准入任何突击战法（Assault Dispatch）。
    - 连击检查点若已到达可发射状态消耗日志（`cfg 230`），但在试图准入第 2 击普攻时被选敌门禁与胜负屏障**绝对拦截（0 / 10,745 发起率，100% 拦截）**。
    - 不再开始 `NormalAttack #2`，移交终战屏障（`CBS9-B03` 封闭）。

---

## 5. 终战排空与屏障状态机 (Finalization State Machine)

```text
[ RUNNING ]
    │
    ▼ (Troop Loss / Mutation)
[ UNIT_DEATH_FACT_RECORDED ] (cfg 163)
    │
    ├─► If Not Commander & Opponent Side Has Alive Heroes:
    │       Continue normal operation draining
    │
    └─► If Commander Dead OR Opponent Side Has 0 Alive Heroes:
            │
            ▼
    [ VICTORY_CONDITION_LATCHED ]
            │  (Invariants: No Future Outer Branch / Action / Combo #2 Allowed)
            │
            ▼
    [ DRAIN_ALLOWED_ADMITTED_WORK ]
            │  - Drain current Chain traversal slots
            │  - Drain current CounterBatch siblings
            │  - Drain current CleaveEffect secondary targets
            │  - Finish current Partition transaction commits
            │
            ▼
    [ PROCESS_COMMANDER_COLLATERAL ] (cfg 209)
            │  - Surviving deputies lose troops due to commander collapse
            │
            ▼
    [ FINALIZATION_BARRIER_REACHED ]
            │  - Emit cfg 733 (Action End)
            │  - Emit cfg 157 (Victory/Defeat Announcement)
            │
            ▼
    [ BATTLE_FINALIZED ] (Terminal State: battle.finished = True)
```

---

## 6. 系统属主权（System Ownership Invariant）

> **底层数值系统与机制系统严禁直接写入 `BattleFinalized = True`。**

- 兵力扣减管线、死亡检测器、铁索、反击、群攻、分担、分摊等系统：
  - **有权**：抛出 `UnitDeathFact`，上报操作容器完成信号 `OperationTerminal`。
  - **无权**：擅自更改全局战斗生命周期或执行全局中断返回。
- 全局终战标志与胜负日志由 **顶层战斗协调器（Battle Orchestrator）** 在确认所有当前合法准入操作排空后唯一写入。

---

## 7. 回归测试规范 (Regression Contracts)

所有符合 Stage 9 架构的模拟器实现必须通过以下 6 项终战回归测试：

1. **`FINAL_01_CHAIN_COMMANDER_DEATH`**：
   - 铁索连环传播中主将在第一节点阵亡，已连接的后续副将节点必须继续受到铁索伤害并扣兵，铁索广播完全结束后才触发胜利宣告。
2. **`FINAL_02_COUNTER_SIBLING`**：
   - 反击批次 `[C1, C2]`，C1 击杀原反击目标主将，已准入的 C2 必须对死目标执行 0 损耗提交，批次结束后触发胜利宣告。
3. **`FINAL_03_COMBO_BATTLE_END`**：
   - 普攻第 1 击击杀敌方主将或敌军全员，胜负条件锁定，坚决不准入、不发起第 2 次普通攻击。
4. **`FINAL_04_CLEAVE_COMMANDER_SECONDARY`**：
   - 群攻效果命中主将副将，主将在次要目标位阵亡，同一个群攻效果内已规划的后续次要副将必须继续受到群攻扣兵，排空后结算主将溃散扣兵并终战。
5. **`FINAL_05_SHARE_COMMANDER_TARGET`**：
   - 分担受保护目标主将因 $D_{\text{target}}$ 阵亡，触发 `TARGET_DEATH_INTERRUPT`，挂起的分担者损耗作废（0 损耗），事务终止后进入终战。
6. **`FINAL_06_DISTRIBUTION_COMMANDER_PARTICIPANT`**：
   - 主将作为分摊承担者阵亡时，采用工程默认规范，完成已规划承担者与目标扣兵后进入终战屏障。
