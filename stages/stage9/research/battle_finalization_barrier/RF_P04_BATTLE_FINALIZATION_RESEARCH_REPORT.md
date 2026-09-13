# RF-P04 战斗终结屏障研究报告 (Battle Finalization Barrier Research Report)

> 项目：三国志战略版战斗模拟器 V2  
> 阶段：Stage 9 Contract Closure — Architecture-level P0 Repair Package  
> 编号：`RF-P04`  
> 状态：`RESEARCH COMPLETE / CONTRACT FROZEN`  
> 报告日期：2026-09-13  
> 关联 Findings：  
> - `CBS9-B03` = **CLOSED**  
> - `CLVS9-B04` = **CLOSED**  
> - `CTS9-H02`  = **CLOSED / HARDENED**  
> - `DSTS9-B02` = **EMPIRICAL OPEN / RUNTIME CLOSED BY ENGINEERING DEFAULT**  

---

## 1. 研究基线与核心问题

在 Stage 9 架构闭环前，各子系统在面临“主将阵亡”、“全军覆没”等世界状态跃迁时，曾存在两类相互冲突的极端实现：
1. **粗暴全局短路极**：
   ```python
   if commander.dead:
       battle.finished = True
       return
   ```
   该模式破坏了铁索连环（CHAIN）原子广播遍历、反击批次（CounterBatch）兄弟结算、群攻（CLEAVE）次要目标清空与主将阵亡全军溃散扣兵（`cfg 209`）等已被战报实证确立的确定性行为。
2. **无限执行极**：
   ```python
   if work_was_queued:
       execute_everything_forever()
   ```
   该模式误将未来分支（如连击第2击、突击战法、新行动）视作不可撤销的既有工作，直接违背了战斗胜利即刻阻断未来外层分支的铁证。

本研究彻底厘清并冻结 **UnitDeathFact**、**VictoryConditionSatisfied**、**CurrentOperationCompletion**、**AlreadyAdmittedSiblingWork**、**FutureBranchAdmission** 与 **BattleFinalization** 六者之间的微观因果次序与屏障边界。

---

## 2. 核心术语定义 (Core Vocabulary)

1. **`UnitDeathFact`（单位死亡事实）**：
   - 指某战斗单位兵力降至 0（`currentTroops == 0`，发射 `cfg 163`）这一物理状态变更已经提交。
   - 死亡事实是不可撤销的底层事实，但**并不等同于全局战斗结束**。

2. **`VictoryConditionSatisfied`（胜负条件达成）**：
   - 指当前世界状态已经满足全局胜负判定逻辑（如敌方主将阵亡、或敌方所有合法战斗单位兵力均归 0）。
   - 此时胜负判定在逻辑上已被锁定（Latched），禁止准入一切未来分支，但**战斗尚未执行全局 Finalization**。

3. **`CurrentOperation`（当前进行中操作）**：
   - 当前正在执行且已经取得执行权（Execution Right）的操作实体，例如：
     - `ChainTraversal`（铁索连环单次广播遍历）
     - `CounterBatch`（反击已准入批次）
     - `CleaveEffect`（当前群攻效果及其次要目标队列）
     - `DamagePartitionTransaction`（当前分担/分摊微事务）
     - `CurrentDamageInstance`（当前单次伤害实例计算与扣除）

4. **`AdmittedWork`（已准入工作项）**：
   - 在触发检查点已正式加入当前操作容器、反应批次或目标规划的工作单元。
   - 已准入工作项享有在当前操作生命周期内排队出栈的执行权，仅受自身**执行时存活门禁（Local Liveness Gate）**约束，不受外部目标死亡的事后溯及抹除。

5. **`FutureBranch`（未准入未来分支）**：
   - 尚未到达触发检查点或尚未取得正式准入资格的潜在流程。例如：
     - 突击战法分发（Assault Dispatch）
     - 连击检查点后的第二击普通攻击（NormalAttack #2）
     - 新行动回合调度（Next Action / Round Phase）
     - 尚未触发的新派生反应批次

6. **`BattleFinalized`（战斗正式终结）**：
   - 战斗正式进入终态：`NO_NEW_WORK`, `NO_NEW_ACTION`, `NO_NEW_REACTION`, 胜负结果固化，抛出胜负宣告日志（`cfg 157`）或平局日志（`cfg 6`）。

---

## 3. 最高级别不变量与核心原则

### 3.1 最高级别不变量 (Invariant 1)
$$\mathbf{VictoryConditionSatisfied \ne BattleFinalized}$$
> **胜负条件达成（逻辑为真）并不等于战斗终结。**
> 当胜负条件达成时，已经在执行中的原子操作、微事务与已准入工作项必须按规则排空（Drain），随后在统一的终战屏障（Finalization Barrier）处才触发战斗终结。

### 3.2 第二不变量 (Invariant 2)
$$\mathbf{BattleFinalization\ occurs\ ONLY\ at\ an\ explicit\ Finalization\ Barrier}$$
> **战斗终结绝不能发生在任意一个 `troops -> 0` 的突变点后直接全局 return。**
> 任何伤害扣减、死亡检测器、状态处理器均无权直接将战斗置为终态；终战判定必须由顶层协调器在操作完成边界统一裁决。

---

## 4. 全量实证研究数据（32,999 战报全盘扫描）

针对 Stage 9 的核心疑问，本研究基于 `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON` 中的 32,999 份战报开发并运行了全量微观抽取器，提取了确凿的实证切片：

### 4.1 COMBO 终战截断研究 (`CBS9-B03`)
- 扫描脚本：`extract_battle_end_normal_attack_deep.py`
- 扫描战报总数：**32,999 份**
- 普攻第 1 击（Attack #1）导致战斗结束（触发 `cfg 157`）的切片样本：**15,393 例**
- 其中击杀敌方主将样本：**10,745 例**
- **实证观测 1（第 2 击普攻发起率）**：
  $$\mathbf{Attack\ \#2\ (cfg\ 9)\ After\ Commander\ Kill:\ 0\ /\ 10,745\ (0.00\%)}$$
  在敌方主将死亡且战斗胜负锁定的 10,745 例样本中，**第 2 次普通攻击发起次数为严格的 0 例（0.00%）**。
- **实证观测 2（连击检查点 cfg 230 表现）**：
  - 在 10,745 例主将阵亡样本中，有 410 例在主将阵亡（`cfg 163`）后抛出了 `cfg 230: [武将]执行来自【强攻/兵锋】的「连击」效果`。
  - 这 410 例的共同微观时序为：
    ```text
    163: [主将]兵力为0，无法再战
    736: (微步完成)
    230: [武将]执行来自【兵锋/强攻】的「连击」效果 (Combo Checkpoint 状态自消耗)
    733: (行动结束标志)
    209: [副将]由于主将[xxx]阵亡，损失了兵力xx (主将阵亡副将全军溃散扣兵)
    157: 防守方主将[xxx]兵力为0，无法再战，攻击方胜利！
    ```
  - 这证明：连击检查点即使抛出状态消耗或日志，在试图准入 `NORMAL_ATTACK #2` 时，由于 `VictoryConditionSatisfied` 已经锁定，选敌门禁判定无合法未决目标，**第 2 次普通攻击被坚决拦截（100% BLOCKED）**。
- **实证观测 3（无目标与战斗终结的区分）**：
  - 战斗未终结时的“暂时无合法目标”（如全员被隐身/无法被选）：行动安全结束，战斗继续进行；
  - 敌方主将阵亡 / 全军覆没：触发 `VictoryConditionSatisfied`，进入 `FINALIZATION_BARRIER`，不仅取消当前行动的一切未来分支，同时终止后续所有武将的行动调度。
- **结论**：**`CBS9-B03 = CLOSED`**。

---

### 4.2 CLEAVE 死亡与终战边界研究 (`CLVS9-B04`)
- 扫描脚本：`extract_battle_end_cleave.py` 及 `extract_cleave_commander_death_fixed.py`
- 扫描战报总数：**32,999 份**
- 抽取结果覆盖 CLVS9-B04 的全部 5 种子场景：

#### Case A: 主目标在主普攻中阵亡，群攻是否执行？
- **实证样本**：**169 例**（如 `战报_1068287_pid1063304.json` 等）
- **现象**：主目标在受到普通攻击主伤害后兵力归 0（`cfg 163`），随后群攻效果依序触发，次要目标依序受到群攻伤害（`cfg 26`）。
- **裁决**：**主目标死亡不阻止群攻的准入与执行（169 / 169，100.0% 执行）**。

#### Case B: 攻击者在群攻下游反应中死亡
- **实证样本**：**2 例**
- **裁决**：攻击者阵亡后，未开始执行的后续群攻效果或后续次要目标因攻击者不满足自身存活门禁而终止。

#### Case C: 次要目标在群攻中死亡
- **裁决**：已在 RF-P07 冻结。当前次要目标提交死亡事实，后续规划的次要目标在执行前进行 JIT 存活重校验。

#### Case D: 次要目标为主将且在群攻中阵亡
- **实证样本**：**14 例真实战报**（主将作为次要目标受到群攻并被击杀至 0 兵力）
- **微观切片验证**：
  在 14 例中，有 5 例（如 `战报_1964609_pid2017107.json`, `战报_2239736_pid2310487.json`, `战报_2239938_pid2310721.json`, `战报_3454985_pid3821875.json`, `战报_786228_pid782471.json`）在主将阵亡后，同一个群攻效果内部仍规划有后续次要目标（副将）。
- **实证观测**：
  在这 5 例中，主将阵亡后，**后续规划的次要目标 100% 照常执行群攻扣兵**！
  - 以 `战报_2239938_pid2310721.json` 为例：
    ```text
    26: [庞德]由于[马超]【槊血纵横】的「群攻」效果，损失了兵力13（0）
    163: [庞德]兵力为0，无法再战 (主将死亡！)
    26: [韩遂]由于[马超]【槊血纵横】的「群攻」效果，损失了兵力471（5067） (后续次要副将继续执行群攻！)
    96: [纪灵]执行来自【后发制人】的「反击」效果 (原主普攻已准入反击继续执行！)
    26: [马超]由于[纪灵]【后发制人】的「反击」效果，损失了兵力13（6250）
    733: (行动结束)
    209: [纪灵]由于主将[庞德]阵亡，损失了兵力165（1493） (主将连带溃散扣兵)
    209: [韩遂]由于主将[庞德]阵亡，损失了兵力506（4561）
    157: 防守方主将[庞德]兵力为0，无法再战，攻击方胜利！
    ```
- **裁决**：
  1. 当前群攻效果（`CleaveEffect`）在进入执行时已经准入了其由 `GLOBAL_SLOT_ASCENDING` 决定的次要目标规划。
  2. 主将在次要目标位阵亡后，**当前群攻效果内部已准入的后续次要目标继续执行**（受 JIT 存活门禁约束）。
  3. 伴随原普通攻击已准入的兄弟反应（如反击）继续执行。
  4. 当前群攻效果及伴随反应全部排空后，执行主将阵亡连带扣兵（`cfg 209`），最后在终战屏障处触发 `cfg 157`。
  5. 尚未准入的未来宏观分支（如第二个群攻技能、连击 #2）不再准入。
- **结论**：**`CLVS9-B04 = CLOSED`**。

---

### 4.3 CHAIN 铁索连环主将阵亡锚点验证
- 扫描脚本：`extract_battle_end_chain.py`
- 扫描战报总数：**32,999 份**
- 铁索连环传播中主将阵亡样本：**333 例**
- 主将阵亡后仍有连环目标待传播并继续执行样本：**159 例**（如 `战报_1104998_pid1100090.json` 等）
- **实证规律**：
  1. 主将在铁索连环第 1 或第 2 个传播节点阵亡（`cfg 163`）。
  2. 铁索连环作为不可分割的单次原子遍历（Atomic Traversal），**继续向剩余合法连环槽位（副将）传播伤害并提交扣兵**。
  3. 铁索遍历完成后，才到达终局屏障并抛出胜负日志（`cfg 157`）。
- **结论**：铁索连环遍历完成是典型的 `CurrentOperationCompletion` 屏障。

---

### 4.4 COUNTER 反击兄弟延续与主将阵亡 (`CTS9-H02`)
- 扫描脚本：`extract_battle_end_counter.py`
- 扫描战报总数：**32,999 份**
- 反击批次内兄弟延续样本：2 例（普通副将）。主将攻击者被 C1 击杀且已排队 C2 的极端边界样本在 32,999 战报库中为 0 例。
- **裁决与固化**：
  - 依据 RF-P03 确立的“已准入反应不随目标死亡撤销，出栈面对已死目标执行 0 损耗提交”及 R5 原则，对 `CTS9-H02` 进行确定性合同固化：
    $$\mathbf{CounterBatch = [C1, C2]},\ C1\ kills\ attacker\ commander \implies C2\ executes\ with\ 0\ loss \to Barrier \to Finalization$$
  - **结论**：**`CTS9-H02 = CLOSED / HARDENED`**。

---

### 4.5 DAMAGE SHARE 目标死亡截断 (RF-P05 继承)
- 在 RF-P05 中已由 128 例无干扰干净样本证伪了分担者继续扣兵的假设：
  $$\mathbf{Target\ Death \implies TARGET\_DEATH\_INTERRUPT \implies Pending\ Sharer\ Loss\ Discarded\ (0\ loss)}$$
- 分担微事务在目标死亡后即刻达成局部终止（Terminal），直接将控制权交由终战屏障。

---

### 4.6 DISTRIBUTION 承担者死亡与工程默认 (`DSTS9-B02`)
- 在 RF-P05 中扫描 32,999 战报库，主将作为分摊承担者并阵亡的样本为 **0 例**（实证未观察到）。
- **决策分离**：
  1. **Empirical Status（实证状态）**：保持 `DSTS9-B02 = EMPIRICALLY UNOBSERVED / OPEN`。
  2. **Runtime Status（模拟器运行规范）**：采纳 **工程默认策略（ENGINEERING_DEFAULT）**：
     > **`PROJECT_RUNTIME_DEFAULT (NOT EMPIRICALLY PROVEN GAME RULE)`**：
     > 已合法准入的 `DistributionTransaction` 将按照既定承担者与目标规划完成局部提交，然后向外暴露状态变更，交由全局终战屏障统一裁决。未来如有新实证战报推翻此假设，可直接替换局部策略而不影响全局架构。
- **结论**：双状态汇报，模拟器确定性达成，不阻塞 Stage 9 设计准入。

---

## 5. 工作项准入与终战门禁矩阵 (Admission & Barrier Matrix)

| 工作项 (Work Item) | 准入时机 (Admission Point) | 胜负条件达成（Latch）后的准入状态 | 执行时局部门禁 (Local Liveness Gate) | 对应终战屏障 (Finalization Barrier) |
|---|---|---|---|---|
| **单次伤害实例 (DamageInstance)** | 伤害派生时 | 允许（微步提交） | 目标需已进入结算流程 | 微步提交后立即评估胜负 |
| **分担微事务 (ShareTransaction)** | 受到普攻/战法伤害时 | 允许（属于当前伤害子事务） | 原目标死亡则触发 `TARGET_DEATH_INTERRUPT` | 事务局部 Commit/Discard 结束 |
| **分摊微事务 (DistributionTransaction)** | 受到伤害并存在分摊时 | 允许（属于当前伤害子事务） | 参与者执行前检查存活 | 全部规划份额 Commit 结束 |
| **铁索连环广播 (ChainTraversal)** | 触发节点伤害完成后 | **禁止新触发**；已开始的遍历**允许排空** | 传播节点存活校验（跳过死亡槽位） | 遍历完所有连环槽位 |
| **反击反应批次 (CounterBatch)** | 普攻命中触发时快照 | **禁止新批次**；批次内兄弟**允许出栈** | 反击者自身存活；目标死亡则 0 损耗 | 批次内所有 Ci 执行完毕 |
| **当前群攻效果 (CleaveEffect)** | 主普攻伤害结算完成时 | **允许排空**已规划的次要目标队列 | 次要目标 JIT 存活重校验（跳过阵亡者） | 该效果所有次要目标处理完毕 |
| **后续群攻效果 (Next CleaveEffect)** | 前一效果执行完毕后 | **禁止准入**（胜利锁定后取消） | 攻击者自身存活 | N/A（直接取消） |
| **突击战法 (Assault Dispatch)** | 普攻及伴随反应完全结束时 | **禁止准入**（直接取消） | 攻击者自身存活且有合法目标 | N/A（直接取消） |
| **连击检查点 (Combo Checkpoint)** | #1 同步生命周期结束时 | 仅发射状态自消耗（如有）；**禁止开启 #2** | 攻击者存活且具备有效连击 Grant | N/A（直接终止行动） |
| **第2次普通攻击 (NormalAttack #2)** | 连击检查点通过后 | **禁止准入（100% 严格拦截）** | 选敌门禁判定必须存在存活敌方主将 | N/A（直接取消） |
| **主将连带溃散扣兵 (`cfg 209`)** | 主将死亡事实记录后 | **强制排空**（属于终战前必须提交的连锁事实） | 针对所有存活副将 | 扣兵提交完成 |
| **全局胜负宣告 (`cfg 157`)** | 所有已准入操作排空后 | **触发终战** | 胜负条件成立 | `BattleFinalized = true` |

---

## 6. 终战状态机 (Battle Finalization State Machine)

```text
[ RUNNING ]
    │
    ▼ (Damage / Mutation commits)
[ UNIT_DEATH_FACT_RECORDED ] (cfg 163)
    │
    ├─► If Not Commander & Teammates Remain:
    │       Return to normal operation draining
    │
    └─► If Commander Reaches 0 OR All Legal Enemies Dead:
            │
            ▼
    [ VICTORY_CONDITION_LATCHED ]
            │  (Invariants: Future branches STRICTLY FORBIDDEN)
            │  (Cancel: Assault, Combo #2, Next Action, Unadmitted Reactions)
            │
            ▼
    [ DRAIN_ALLOWED_ADMITTED_WORK ]
            │  - Drain current Chain traversal slots
            │  - Drain current CounterBatch siblings (0-loss on dead)
            │  - Drain current CleaveEffect secondary targets (JIT liveness)
            │  - Finish current Partition transaction local commits
            │
            ▼
    [ PROCESS_COMMANDER_COLLATERAL ] (cfg 209)
            │  - Surviving deputies lose troops due to commander death
            │  - (If deputies reach 0, record death fact without opening new reactions)
            │
            ▼
    [ FINALIZATION_BARRIER_REACHED ]
            │  - All admitted containers completely drained
            │  - Emit cfg 733 (Action End if inside action)
            │  - Emit cfg 157 (Victory / Defeat log)
            │
            ▼
    [ BATTLE_FINALIZED ] (Terminal State: battle.finished = true)
```

---

## 7. 终战协调伪代码 (Reference Implementation)

```python
class BattleOrchestrator:
    def __init__(self):
        self.victory_latched = False
        self.victory_side = None
        self.battle_finalized = False
        self.active_operation_stack = []

    def on_unit_troop_mutation(self, unit, delta, cause):
        unit.current_troops -= delta
        if unit.current_troops <= 0:
            unit.current_troops = 0
            self.record_death_fact(unit)

    def record_death_fact(self, unit):
        # 1. 物理死亡事实
        emit_event(cfg=163, desc=f"[{unit.name}]兵力为0，无法再战")

        # 2. 检查胜负条件是否满足
        if not self.victory_latched:
            if unit.is_commander or self.all_enemies_dead(unit.side):
                self.victory_latched = True
                self.victory_side = unit.opponent_side
                # 严禁在此处立即置 battle_finalized = True 或 return！

    def check_future_branch_admission(self, branch_type, actor):
        """未来分支准入门禁（Assault, Combo #2, Next Action）"""
        if self.victory_latched:
            return False  # 胜负已锁定，坚决拒绝一切未来分支准入
        if not actor.is_alive():
            return False  # 执行权存活门禁
        return True

    def run_cleave_effect(self, actor, cleave_effect, actual_target):
        """群攻效果排空语义"""
        # 进入时即快照已准入次要目标列表 (GLOBAL_SLOT_ASCENDING)
        secondary_plan = self.resolve_cleave_secondary_plan(actual_target)
        
        for sec_target in secondary_plan:
            # JIT 存活校验
            if not sec_target.is_alive():
                continue
            
            # 执行群攻伤害
            self.execute_derived_cleave_damage(actor, sec_target, cleave_effect)
            
            # 若次要目标是主将且阵亡，victory_latched 会被置为 True
            # 但循环不打断，继续完成 secondary_plan 中的下一个次要目标！

    def reach_operation_completion_barrier(self):
        """当最外层当前操作容器完全排空时触发"""
        if not self.victory_latched:
            return

        # 1. 处理主将阵亡连带扣兵 (cfg 209)
        self.process_commander_death_collateral()

        # 2. 终战日志抛出
        emit_event(cfg=733, desc="")
        emit_event(cfg=157, desc=f"主将阵亡，{self.victory_side}方胜利！")

        # 3. 终态锁定
        self.battle_finalized = True
```

---

## 8. Stage 9 Design Admission Gate 裁决

所有 Stage 9 Architecture-level P0 修复包的状态：
```text
RF-P01 = CLOSED (Integerization)
RF-P02 = CLOSED (Normal Attack Lifecycle & Combo)
RF-P03 = CLOSED (Execution Right & Death Scope)
RF-P04 = CLOSED (Battle Finalization Barrier)
RF-P05 = PARTIALLY CLOSED (SHS9-B02 CLOSED, DSTS9-B02 RUNTIME CLOSED BY DEFAULT)
RF-P06 = CLOSED (Cleave Damage Layer & Recovery Basis)
RF-P07 = CLOSED (Cleave State Lifecycle & Secondary Targets)
```

综合审计结论：
1. **Architecture Blocker = 0**
2. **Runtime Ambiguity = 0**
3. **Empirical Research Debt**：唯一剩余 `DSTS9-B02` 实证未观察到，但已通过显式 `ENGINEERING_DEFAULT` 隔离锁定，绝不阻塞模拟器运行和设计规范。

**STAGE 9 DESIGN ADMISSION = READY**。
