# Stage 9 → Stage 10 Compatibility Addendum
# 结算管线与伤害后效恢复权限兼容性增补文档

> Project: 三国志战略版战斗模拟器 V2  
> Scope: Stage 9 damage settlement, reaction ordering, aftermath recovery permission, and battle finalization compatibility for Stage 10 persistent states  
> Status: `LIMITED COMPATIBILITY REOPEN / DESIGN ADDENDUM`  
> Origin: `Stage10 Design Re-Audit Round 2 (Findings S10-R2-B01 & S10-R2-B02)`  
> Production implementation: `NOT AUTHORIZED BY THIS DOCUMENT`  
>  
> `stages/stage9/STAGE9_DESIGN_FREEZE.md` and `stages/stage9/STAGE9_FREEZE_RECORD.md` remain authoritative except for the clauses explicitly reopened and reconciled below.

---

## 1. Context & Scope Rule

Stage9 冻结文档明确规定：战斗结算层（Settlement Layers）、反应排序（Reaction Ordering）、权限矩阵（Permission Matrix）、终局裁决所有权（Finalization Ownership）以及公共运行时契约属于严格冻结表面，后续阶段若需对上述语义进行修改，**严禁跨阶段隐式重写**，必须进行正式的 `LIMITED COMPATIBILITY REOPEN` 并产出专门的增补规范（Addendum）。

本增补文档针对 Stage10 引入的持续状态伤害结算、急救伤害后效恢复（FIRST_AID Damage Aftermath）以及突击伤害恢复权限，正式开启**受控的最小局部重开**。

**严格不重开（Unaffected Frozen Surface）**：
- 铁索连环（Chain）真实反馈伤害的受限结算规则保持冻结不变；
- 普攻与反击的基础判定及触发逻辑保持冻结不变；
- 分担（Share）与群攻分摊（Distribution）的数值配平与目标优先扣减算法保持冻结不变；
- 胜负判定（VictorySystem）与终局协调器（BattleFinalizationCoordinator）的状态机转换契约保持冻结不变；
- 战斗事件总线（EventBus）纯观察性原则保持冻结不变。

---

## 2. Original Frozen Stage9 Contract

### 2.1 原始结算路径与排序
Stage9 原始冻结的伤害结算管线由 `DamageInstanceCoordinator` 驱动，包含以下主要分支：

1. **无分担/标准结算 (`NoPartition`)**:
   ```text
   target settlement (DamageResolutionSystem.settle)
   → target death/defeat observation
   → resolved_damage_callback
   → complete DamageInstance
   ```
2. **分担结算 (`Share`)**:
   ```text
   target settlement
   → if target defeated:
       TARGET_DEATH_INTERRUPT
       discard pending sharer direct loss
       invoke finish callback
   → if target survives:
       commit sharer DirectTroopLoss
       observe sharer death if applicable
       invoke finish callback
   → complete DamageInstance
   ```
3. **分摊结算 (`Distribution`)**:
   ```text
   drain participant DirectTroopLoss in fixed slot order
   → target settlement
   → invoke finish callback
   → complete DamageInstance
   ```
4. **横扫衍生伤害 (`CleaveDerivedDamageSystem`)**:
   ```text
   Cleave target settlement
   → target death/finalization observation
   → if target survives:
       commit Share DirectTroopLoss
       observe sharer death if applicable
   → execute Cleave FIRST_AID callback (if can_trigger_recovery)
   → execute attacker recovery (倒戈/吸血, if can_trigger_recovery)
   → invoke callbacks
   → complete Cleave
   ```

### 2.2 原始反应恢复权限 (`ReactionPermissionPolicy.can_trigger_recovery`)
Stage9 在 `ReactionPermissionPolicy` 中定义了各类伤害来源是否允许触发恢复的统一判定：
```python
@classmethod
def can_trigger_recovery(cls, source_type: SourceType) -> bool:
    if source_type in (
        SourceType.CHAIN_TRUE_FEEDBACK,
        SourceType.SHARE_DIRECT_LOSS,
        SourceType.DISTRIBUTION_DIRECT_LOSS,
    ):
        return False
    return source_type in (
        SourceType.NORMAL_ATTACK,
        SourceType.ACTIVE_SKILL,
        SourceType.PERIODIC_DAMAGE,
        SourceType.CLEAVE,
        SourceType.COUNTER,
    )
```

---

## 3. Conflicts Introduced by Stage10 & Authority

### 3.1 S10-R2-B01: 横扫与急救相对排序冲突 (Cleave vs FIRST_AID Ordering)
- **冲突事实**: Stage10 Draft V2 试图统一标准普攻与横扫的伤害后效端口（`DamageAftermathPort`），将急救执行点直接放在目标扣血结算之后：
  `Cleave target settlement → DamageAftermathPort(FIRST_AID) → Share DirectTroopLoss`。
- **违规性质**: 此改动颠倒了 Stage9 冻结的横扫执行链条（原为：目标结算 $\to$ 友方分担扣血 $\to$ 急救与倒戈），在未经 Stage9 兼容重开授权的情况下改变了真实可观测时序（例如分担者濒死/阵亡判定与急救回血的相对顺序）。

### 3.2 S10-R2-B02: 突击伤害 (`ASSAULT`) 恢复权限缺失
- **冲突事实**: 最新的权威机制合同（`states/persistent/first_aid/MECHANISM_CONTRACT.md` @ `a9a05cef`）明确规定：
  `Pursuit_Counterattack: ELIGIBLE (突击与反击伤害可触发急救)`。
- **机制矛盾**: Stage9 中定义了独立的 `SourceType.ASSAULT`，但在 `ReactionPermissionPolicy.can_trigger_recovery()` 中遗漏了 `SourceType.ASSAULT`。导致突击战法造成的合格受击命中无法触发急救，产生明确的官方机制违规。

### 3.3 DirectTroopLoss 边界侵蚀风险
- 分担与分摊产生的非命中直接扣血（`SHARE_DIRECT_LOSS` 与 `DISTRIBUTION_DIRECT_LOSS`）在 Stage9 中属于 `DirectTroopLoss`，严禁作为常规伤害事件触发急救。Stage10 必须严守此边界。

---

## 4. Reconciled Stage9 Specifications for Stage10

### 4.1 横扫结算时序收口 (Reconciled Cleave Ordering)
为尊重 Stage9 既有冻结运行时的稳定性，同时支持 Stage10 统一的后效恢复架构，**正式维持 Stage9 既有的横扫时序**，并将 Stage10 的 `DamageAftermathPort` 挂载到合法的冻结检查点：

```text
[Cleave Derived Damage Pipeline]
1. Cleave Target Settlement:
   - DamageResolutionSystem.settle(target, assigned)
   - Publish DAMAGE_DEALT
   - If target defeated:
       - Publish UNIT_DEFEATED
       - DefeatCleanupPort.commit_defeat(target)
       - FinalizationCoordinator.observe_damage_instance_death
       - Discard pending sharer DirectTroopLoss
       - Abort Aftermath (target dead, not eligible)
       - Return CleaveDerivedDamageResult(TARGET_DEATH_INTERRUPT)

2. Sharer Direct Troop Loss (if target survives and SharePlan exists):
   - Commit sharer DirectTroopLoss
   - If sharer defeated:
       - DefeatCleanupPort.commit_defeat(sharer)
       - FinalizationCoordinator.observe_damage_instance_death

3. Damage Aftermath Recovery Checkpoint (DamageAftermathPort):
   - Check ReactionPermissionPolicy.can_trigger_recovery(SourceType.CLEAVE) -> True
   - Build DamageAftermathFact(target, resolved_hit=True, loss=actual_loss, ...)
   - Invoke shared DamageAftermathPort.commit_aftermath(context, aftermath_fact)
     -> Executes target's FIRST_AID if eligible

4. Attacker Recovery:
   - If ReactionPermissionPolicy.can_trigger_recovery(SourceType.CLEAVE) -> True:
       - Execute attacker recovery (倒戈/吸血)

5. Callbacks & Finalization:
   - Invoke remaining Stage9 callbacks
   - Complete Cleave execution
```

**关键原则（Shared Port ≠ Identical Relative Timing）**：
`DamageAftermathPort` 作为全战斗唯一的后效恢复接入点，由不同的 Stage9 结算路径在各自合法的冻结检查点进行调用，绝不强制要求所有结算路径必须具有完全相同的相对代码位置。

---

### 4.2 各种结算路径的统一 Aftermath 检查点规范

| 结算路径 (Settlement Route) | 目标结算时序 | 附随直接扣血时序 | DefeatCleanup 插入点 | DamageAftermathPort (FIRST_AID) 插入点 | 后续步骤 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NoPartition** (普攻/主动/指挥/持续跳伤) | 目标扣血结算 | 无 | 目标阵亡时立即执行 | 目标存活时在观察事件后立即调用 | 回调与 DamageInstance 完成 |
| **Share** (分担主伤害) | 目标扣血结算 | 目标存活时执行分担者 DirectTroopLoss | 目标阵亡立即执行；分担者阵亡在扣血后立即执行 | **目标存活且分担者扣血完成后调用** | 回调与 DamageInstance 完成 |
| **Distribution** (群攻分摊主伤害) | 分摊者扣血完成后执行目标结算 | 分摊者在目标结算前扣血 | 分摊者扣血后若死立即执行；目标结算后若死立即执行 | **目标结算完成且存活时调用** | 回调与 DamageInstance 完成 |
| **Cleave** (横扫衍生伤害) | 目标扣血结算 | 目标存活时执行分担者 DirectTroopLoss | 目标阵亡立即执行；分担者阵亡在扣血后立即执行 | **目标存活且分担者扣血完成后调用** | 攻击方吸血倒戈 $\to$ 回调 |
| **Counter** (反击) | 目标扣血结算 | 无 | 目标阵亡时立即执行 | 目标存活时在观察事件后立即调用 | 回调与反击批次完成 |
| **Chain** (铁索传导) | 受限结算 | 无 | 目标阵亡时立即执行 | **禁止调用 (INELIGIBLE)** | 传导游标推进 |

---

### 4.3 突击恢复权限修复 (`SourceType.ASSAULT` Authorization)
正式修订 Stage9 `ReactionPermissionPolicy`：

1. **`can_trigger_recovery` 判定集合扩展**:
   - 正式将 `SourceType.ASSAULT` 纳入允许列表；
   - 保持 `CHAIN_TRUE_FEEDBACK`, `SHARE_DIRECT_LOSS`, `DISTRIBUTION_DIRECT_LOSS` 严格阻断。

2. **单一权限权威原则 (Single Authoritative Permission Owner)**:
   `ReactionPermissionPolicy.can_trigger_recovery(source_type)` 为战斗核心中关于“伤害事件是否具备后效恢复资格”的**唯一权威仲裁源**。
   `DamageInstanceCoordinator`, `CleaveDerivedDamageSystem`, `DamageAftermathPort` 均只能调用该策略方法，严禁在各自子系统中硬编码第二套来源白名单。

---

## 5. Permission Matrix Comparison (Stage9 Old vs Stage10 Compatible)

| 伤害来源类型 (`SourceType`) | Stage9 原始权限 (`can_trigger_recovery`) | Stage10 兼容权限 (`can_trigger_recovery`) | FIRST_AID 最终资格 | 权威与机制依据 |
| :--- | :---: | :---: | :---: | :--- |
| `NORMAL_ATTACK` | `True` | `True` | **`ELIGIBLE`** | 普通攻击合格命中结算 |
| `ACTIVE_SKILL` | `True` | `True` | **`ELIGIBLE`** | 主动/指挥技能合格命中结算 |
| `ASSAULT` (突击) | **`False` (遗漏)** | **`True` (修复)** | **`ELIGIBLE`** | 机制合同: `Pursuit_Counterattack: ELIGIBLE` |
| `PERIODIC_DAMAGE` (持续跳伤) | `True` | `True` | **`ELIGIBLE`** | 机制合同: 6 类跳伤合格结算均产生急救机会 |
| `CLEAVE` (横扫衍生) | `True` | `True` | **`ELIGIBLE`** | 横扫合格结算命中 |
| `COUNTER` (反击) | `True` | `True` | **`ELIGIBLE`** | 机制合同: `Pursuit_Counterattack: ELIGIBLE` |
| `CHAIN_TRUE_FEEDBACK` (铁索传导) | `False` | `False` | **`INELIGIBLE`** | Stage9 冻结: 铁索使用受限结算，禁止连锁触发恢复 |
| `SHARE_DIRECT_LOSS` (分担扣血) | `False` | `False` | **`INELIGIBLE`** | 非伤害命中，属于内部直接兵力扣减 |
| `DISTRIBUTION_DIRECT_LOSS` (分摊扣血) | `False` | `False` | **`INELIGIBLE`** | 非伤害命中，属于内部直接兵力扣减 |

---

## 6. DirectTroopLoss 保护与胜负判定时序 (Finalization Interplay)

1. **DirectTroopLoss 绝不生成 DamageAftermathFact**:
   分担与分摊扣血仅派发直接兵力扣除与死亡检测，绝不进入 `DamageAftermathPort`。
2. **终局闭锁期间的排空 (Victory-Latched Admitted Drain)**:
   - 若某次结算（如分摊直接扣血或目标主伤害）导致敌方全灭，`BattleFinalizationCoordinator` 立即将状态置为 `VICTORY_LATCHED`；
   - 此时该次已被准入的 `DamageInstance` 事务中的剩余本地排空工作（例如目标本地急救后效结算）允许作为事务收尾工作被执行完毕；
   - 排空完成后，系统正式完成终局（`FINALIZED`），不再准入任何新的未来分支。

---

## 7. Mandatory Regression Obligations

任何实现 Stage9 增补规范的生产代码，必须通过以下强制性回归用例：

1. **`test_stage9_assault_first_aid_eligible`**:
   验证当 `SourceType.ASSAULT` 伤害命中挂载有 FIRST_AID 且存活的目标时，`DamageAftermathPort` 能够正确接收到后效事实并生成急救恢复机会。
2. **`test_stage9_cleave_share_first_aid_ordering`**:
   验证横扫衍生伤害触发分担时，执行顺序严格为：目标扣血 $\to$ 分担者 DirectTroopLoss $\to$ 目标 FIRST_AID 急救 $\to$ 攻击方倒戈吸血。
3. **`test_stage9_share_direct_loss_never_triggers_first_aid`**:
   验证挂载 FIRST_AID 的武将在代友分担受到 `SHARE_DIRECT_LOSS` 时，绝不产生急救机会。
4. **`test_stage9_counter_first_aid_preserved`**:
   验证反击造成的合格伤害依然保持合法的急救后效资格，不受 ASSAULT 权限增补影响。
5. **`test_stage9_chain_feedback_recovery_blocked`**:
   验证铁索传导伤害依然严格阻断急救与倒戈恢复。
