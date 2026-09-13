# Stage 9 执行权与死亡作用域核心合同

```text
Status: FROZEN
Freeze Date: 2026-09-13
Package: RF-P03
Authority Level: P0 Shared Arbitration Rule
Replaces / Narrows: Universal "if unit.dead: abort everything" & "if action started: death never matters"
```

---

## 1. 核心目标与范围

本文件为 `sgs-v2-battle-system` 与状态机制研究仓库中涉及**执行权判定（Execution Right / Admission Ownership）与死亡作用域（Death Scope）**的公共底层标准。

废除 Stage 9 早期粗糙的两种极端全称规则：
- 否定极：“只要单位死亡，立即粗暴取消一切全局调用（`if unit.dead: abort everything`）”；
- 肯定极：“只要行动已经开始，死亡绝不影响后续分支执行（`death never matters during own action`）”。

正式模型建立在**执行权准入（Admission Right）与执行时局部门禁（Execution-time Local Gate）的分层解耦**之上。

---

## 2. 执行作用域分层（Execution Scopes）

模拟器与机制规范必须能够严格区分以下 9 级执行作用域：

```text
1. CURRENT_MICROSTEP
   - 当前正在原子计算/赋值的微操作（如数值扣除、属性修改、快照读取）。
   - 强不变量：已经开始执行的微步必定执行完毕并提交，不可被溯及既往撤销。

2. CURRENT_DAMAGE_INSTANCE
   - 当前单次伤害实例（含伤害公式结算、目标扣兵、日志抛出）。

3. CURRENT_PARTITION_TRANSACTION
   - 当前分流微事务（如 DAMAGE_SHARE、DISTRIBUTION）。
   - 机制局部只拥有自身事务内部的切分与 Commit 顺序，不拥有外部 Action 生命周期。

4. CURRENT_REACTION
   - 当前正在执行的单一派生反应（如当前正在出手的反击 C1、急救回调）。

5. ALREADY_ADMITTED_REACTION_BATCH
   - 已经在触发检查点完成准入判定的反应批次（如 CounterBatch = [C1, C2]）。
   - 兄弟反应已获得执行权准入凭证，不随外部目标死亡自动全局作废。

6. CURRENT_NORMAL_ATTACK_INSTANCE
   - 当前单次普通攻击实例（包括选敌、援护、主伤害、派生窗口）。

7. CURRENT_ACTION
   - 当前行动主体的一个完整行动回合（从 ACTION_START 到 ACTION_END）。

8. NOT_YET_DISPATCHED_FUTURE_BRANCH
   - 尚未到达触发检查点或尚未准入的未来分支（如 Assault 突击窗口、Combo Checkpoint、第二击 #2）。

9. BATTLE_FINALIZATION
   - 战斗胜负终局裁决（由 RF-P04 拥有，本合同不越权规定终战屏障细节）。
```

---

## 3. 执行状态模型（Execution State Model）

一个工作项（Work Item）的生命周期状态在合同语义上细分为：

```text
NOT_ADMITTED
  ↓ (满足触发条件并通过准入检查)
ADMITTED_PENDING
  ↓ (调度引擎出栈执行)
EXECUTING
  ↓ (执行完毕提交)
COMPLETED

异常退出态：
- CANCELLED_BEFORE_ADMISSION：尚未准入即因前置条件或前序死亡取消。
- CANCELLED_BY_LOCAL_EXECUTION_GATE：已获准入，但出栈执行时自身局部门禁失败（如执行时自身阵亡）。
```

---

## 4. 七大核心执行原则（Core Execution Invariants）

### Rule 1: 不可逆微步提交（Microstep Irreversibility）
> **Death does not retroactively undo a completed microstep.**
任何已经完成计算、扣除或日志发射的微步，其物理事实不可被后续发生的死亡事件撤销。

### Rule 2: 准入权不随目标死亡溯及失效（Admitted Reaction Retention）
> **Death does not automatically revoke an already-admitted sibling reaction unless that reaction fails its own execution-time liveness gate.**
例如：反击批次 `CounterBatch = [C1, C2]`，当 C1 造成原攻击者死亡并提交后，已准入的 C2 依然依序出栈执行。C2 面对已死亡的目标，执行其自身局部门禁定义的“已死目标零损耗提交（committed loss = 0）”，而非全局强行删除。

### Rule 3: 尚未准入的未来分支必须满足存活门禁（Future Branch Live Gate）
> **A future branch not yet admitted must satisfy its owner's live admission gate.**
未被调度准入的未来分支（如 Assault 突击、连击检查点 Combo Checkpoint、第二击 Normal Attack #2），在出栈准入前必须核验主体存活状态。若行动主体已在前置流程中死亡，未来分支直接注销（`CANCELLED_BEFORE_ADMISSION`）。

### Rule 4: 机制局部事务仅拥有自身行为（Transaction-Scope Ownership）
> **Mechanism-local transaction rules own only their transaction.**
机制 P0（如 DAMAGE_SHARE、DISTRIBUTION）只拥有自身计算、分配与局部 Commit/Discard 行为。当检测到目标死亡时，机制仅抛出 `TargetDeathFact`，并将外部 Action、ReactionStack 或 Battle Finalization 的继续/终止裁决权**完全委托给全局调度器（Core Orchestrator / Shared Finalization Owner）**，不得擅自在局部写死 `ABORT_REMAINING_ACTION`。

### Rule 5: 死亡事实不等于战斗终结（UnitDeathFact != BattleFinalized）
> **Unit death fact is distinct from battle finalization.**
单位死亡（`cfg 163` 兵力为 0）发生后，系统可能仍需完成当前原子遍历、已准入反应结算或主将附带扣兵（`cfg 209`）。终战判定与胜利宣告属于独立的全局屏障。

### Rule 6: 状态物理清理不撤销已准入执行权（State Physical Cleanup vs Execution Right）
> **State physical cleanup does not automatically revoke already acquired execution rights.**
单位死亡后状态实例从数据结构中清除，但已经合法准入、正在执行队列中的微事务或反应继续按各自规则结算完毕。

### Rule 7: 终战时机委托（Finalization Delegation）
> **Battle finalization timing and exact barrier mechanics are delegated to RF-P04.**
本文件不冻结胜负宣告的精确时机、无目标判定（`CBS9-B03`）或全军覆灭屏障。

---

## 5. 跨机制执行权与门禁矩阵

| 工作项 (Work Item) | 准入时机 (Admission Time) | 准入后发生死亡的表现 | 执行时局部门禁 (Liveness Gate) | 权威属主 (Owner) |
|---|---|---|---|---|
| **当前扣兵微步** | 执行即原子提交 | 完成当前扣兵事实 | 无需存活 | Damage Resolver |
| **已准入反击兄弟 C2** | CounterBatch 产生时 | 保持出栈，对已死目标提交 0 损耗 | 检查反击者自身存活与合法性 | Counter P0 |
| **突击战法 (Assault)** | CounterBatch 结束且非终止路径 | 前置死亡则未准入 $\to$ 取消 | 攻击者必须存活 | Core / Assault |
| **连击检查点 (Combo #2)** | Combo Checkpoint 窗口 | 前置死亡则未准入 $\to$ 取消 | 行动者必须存活且具备有效 grant | COMBO P0 |
| **分担剩余份额提交** | 原目标提交并存活时 | 依 SHS-P05 细则 | 分担者必须存活 | Damage Share P0 |
| **分摊承担者后续提交** | 分摊事务规划时 | 依 DST-P05 细则 | 承担者实时存活校验 | Distribution P0 |
| **铁索连环广播遍历** | Chain 传播触发时 | 继续遍历当前循环余下连环目标 | 连环目标存活 | Chain Link P0 |
