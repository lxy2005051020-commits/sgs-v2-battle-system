# Stage 9 核心底层裁决全景总规 (v2 - Repaired)

> **项目**: 三国志战略版战斗模拟器 V2  
> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（逾 1,400 万条原始事件流）  
> **状态**: `REPAIRED — AUDIT READY (CONSISTENT EVIDENCE BASELINE)`  
> **群攻机制冻结记录**: `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`  
> **最高原则**: 
> 1. 反例优先、控制变量优先、直接证据优先；
> 2. 严禁将 NOT OBSERVED 写成 BLOCKED；
> 3. 严禁把工程设计表述为官方内部实证；
> 4. 严禁把统计模型兼容断言为官方机制证明；
> 5. 跨文档同一机制只能存在单一一致结论。

---

## 核心裁决原则全览 (12 个问题域统一裁决)

### 1. 目标选择与重定向总顺序 (R2)
- **流水线**: 存活池 $\rightarrow$ 阵营过滤 $\rightarrow$ **混乱判定 (JIT 即时)** $\rightarrow$ **嘲讽/锁定检查 (若未混乱)** $\rightarrow$ **意图目标 (Intended Target)** $\rightarrow$ **援护拦截 (Rescue Hook)** $\rightarrow$ **受击承伤者 (Resolved Action Target)**。
- **混乱压制嘲讽**: 武将混乱时，嘲讽锁定失效，进入全场无差别抽取（1,351 例共现有效样本，79.13% 攻击非嘲讽源，20.87% 随机命中嘲讽源）。[Grade A]
- **援护高于嘲讽**: 意图目标被嘲讽锁定为其自身时，若嘲讽源身上带有队友援护，伤害由援护者代为承受（89 例无反例）。[Grade A]
- **混乱攻击友军可被援护**: 攻击者==援护者时发生自援护（自攻，25 例验证）。[Grade A]

### 2. 目标身份三级解耦 (R2)
- **必须解耦三级目标属性**:
  1. `pre_redirect_target` (Intended Target): 攻击意图目标；
  2. `post_redirect_attack_target` (Resolved Action Target): 物理受击动作受体，作为后续反击主体、突击受体及群攻溅射中心；
  3. `damage_recipient(s)` (Damage Receivers): 经分担/分摊后的兵力实际扣除实体。
- 突击战法、反击、控制状态作用于 `post_redirect_attack_target`（援护者）。[Grade A]
- 群攻以 `post_redirect_attack_target` 为基准向其余队友溅射（18 例）。[Grade B]

### 3. 普通攻击完整生命周期 (R1)
- **严格时序流转**:
  $$\text{声明 (cfg 9)} \rightarrow \text{援护重定向 (cfg 143/9)} \rightarrow \text{扣血 (cfg 28)} \rightarrow \text{受击回调 (急救/绝地)} \rightarrow \text{群攻反应} \rightarrow \text{普攻反击反应} \rightarrow \text{突击战法} \rightarrow \text{连击检查点}$$
- **时序证据核验**:
  - 群攻先于反击（12:0）[Grade B]；
  - 普攻反击先于突击（96:0，已将绝地反击归因为 OnDamageTaken Callback）[Grade B]；
  - 突击先于连击检查点（162:0）[Grade A]。

### 4. 反应队列架构 (R1)
- 采用 **阶段优先级制 (Phase Priority) + 局域即时内联回调 (Inline Callbacks)**。[Grade B]
- 突击致死时，后续附加状态短路取消（报 cfg 149）。[Grade A]

### 5. 跨机制递归许可矩阵 (R4 + Cleave Freeze)
- **已有研究统计支持的 BLOCKED 项**:
  - 反击套反击: 有效机会 Denominator=90，触发=0 [历史 Grade B；最终冻结仍受提取器语义审计约束]；
  - 连环套连环: 有效机会 Denominator=23,620，触发=0 [历史 Grade A；最终冻结仍受提取器语义审计约束]；
  - 连击第 2 击套第 3 击: 有效机会 Denominator=34,639，触发=0 [Grade A]。
- **已直接确认并冻结的群攻/分担递归边界**:
  - `Cleave → Cleave = BLOCKED`；
  - `Cleave → Counter = BLOCKED`；
  - `Share Damage → Share = BLOCKED`；
  - `Share Damage → FirstAid / Counter / 刚烈不屈等受击响应 = BLOCKED`。
- **已确认跨机制支持**:
  - `Cleave → Share = ALLOWED`；
  - `Cleave → FirstAid = ALLOWED`；
  - Counter → FirstAid、Counter → Chain 维持既有研究结论。

### 6. 四类派生伤害数学语义 (R3, R6)
- **SPLIT (分摊/分担)**: 总量严格守恒，$D_{orig} = D_{main} + \sum D_{sub}$。分担为一对一，分摊为一对全队均摊。[Grade A]
- **TRANSFER (转移 - 援护)**: 动作级 100% 物理重定向。[Grade A]
- **FEEDBACK (反馈 - 铁索连环)**: 原目标承伤不减，按比例向连环队友广播。[Grade A]
- **COPY (复制 - 群攻)**: 主目标承伤不减，以主攻击最终结算伤害乘群攻比例生成副目标派生伤害。群攻核心规则已单独冻结于 `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`。

### 7. 理论伤害 vs 实际兵力损失 (R3, R5, R6)
- **群攻基数**: 群攻使用触发它的主攻击 **最终结算伤害** 作为派生基数，再乘 Cleave Ratio；副目标不重新执行基础攻防公式。
- **历史致死分担观察**: 旧版样本中主目标受击兵力致死时未观察到分担转嫁；由于提取器语义仍在做最终审计，该致死边界暂不提升为新的 Frozen 规则。

### 8. 派生伤害 Pipeline 重入 (R3 + Cleave Freeze)
- **群攻（已冻结）**:
  - 跳过副目标基础攻防公式；
  - 继承原攻击 `DamageType`；
  - 可以被规避；
  - 可以被抵御，抵御成功消耗 1 次抵御；
  - **不重新受到副目标自身伤害增减 Modifier 影响**；
  - 可以进入分担；
  - 实际承伤后可触发急救；
  - 兵刃型群攻可按规则触发倒戈，谋略型群攻可按规则触发攻心；
  - 不触发反击，不再次触发群攻。
- **分担支路**: 分担者被扣除的 Share Damage 属于被动数值结算，不开启新的完整受击响应链。
- **铁索连环**: 仍维持“派生基数、跳过副目标基础公式”的研究结论；不得因为群攻已冻结而自动推定铁索拥有完全相同的 Evasion / Barrier / Modifier / Share / Callback 许可矩阵，铁索边界须独立确认。

### 9. 战报因果溯源结构 (R8)
- **三层因果模型分离**:
  1. **LOG FACT**: 战报事件为绝对平铺序列（仅 `cfg_id`, `desc`, `args`），无 `parent_id`、`root_action_id`、`call_depth`、`indent`。[Grade A]
  2. **RECONSTRUCTED MODEL**: 通过定界符（723/733/734/735/725/724/736）还原动作边界。[Grade B]
  3. **ENGINEERING MODEL**: `root_action_id` 与 `reaction_depth` 属于模拟器实现设计。官方内部调用栈机制标记为 **UNKNOWN**。

### 10. 死亡与终战分层模型 (R5)
- **确立 9 层死亡与终战模型**:
  1. Unit Death (cfg 163)
  2. Current Damage Completion
  3. Inline Callback Completion
  4. Current Reaction Completion
  5. Current Skill / Multi-target Loop Completion
  6. Current Attack Completion
  7. Future Reaction Cancellation
  8. Morale Loss from Commander Death (cfg 209)
  9. Battle Victory Finalization (cfg 157)
- **仲裁定论**: 
  - 攻击者在反击中阵亡: 后续突击与连击立即硬短路 (IMMEDIATE ABORT, 113例) [Grade A]；
  - 技能或连环传播中主将阵亡: 当前多目标循环结算完毕后终战 (DEFERRED TERMINATION, 890例) [Grade A]。连环主将阵亡样本仅 5 例 [Grade C]。

### 11. 多来源冲突裁决 (R6)
- **控制状态排斥**: 重复施加控制多数表现为 cfg 23 拒绝（1,550 例，0 覆盖）；更强效果能否覆盖弱控因数据无法标定强度，属于未证实 (UNKNOWN)。[Grade B]
- **多反击触发**: 同武将携带多个反击战法按装配顺序独立触发（样本仅 8 例）。[Grade C]

### 12. 确定性与 RNG (R7)
- **第二击重新索敌**: 连击第二击重新执行目标决议，合法候选池中按 1/K 独立随机均匀索敌（34,639 对全量分层样本：候选为 1 时同目标率 100.00%，候选为 2 时 50.52%，候选为 3 时 33.83%，第一击目标阵亡时 100% 转移目标）。当前“重新索敌”结论强；严格独立均匀模型仍应由完整 transition matrix 做最终统计封口。
- **官方内部 PRNG 机制**: 具体 PRNG 算法、调用次数与步进序列标记为 **UNKNOWN**（禁止将模拟器设计断言为官方事实）。[UNKNOWN]

---

## 与 Stage 8 Frozen Contract 边界评估

1. **反击 (Counter)**: 构造常规 `DamageRequest`，完全复用 Stage 8 冻结流水线（分类 A：外层编排即可）。
2. **群攻 (Cleave)**:
   - 输入已经是主攻击最终结算伤害派生出的固定值；
   - 跳过基础攻防公式；
   - 不重新跑副目标伤害增减 Modifier；
   - 仍需要规避、抵御、分担、兵力扣除与选择性的 post-damage recovery callback；
   - 必须禁止 Counter / Cleave 递归传播。
3. **铁索反馈 (Chain)**:
   - 仍确定跳过副目标基础攻防公式；
   - 其余重入边界须独立研究，禁止直接复制 Cleave 矩阵。
4. **评估定论**: 群攻与其他派生伤害都提示 Stage 9 可能需要一个明确的 `Derived Damage` extension/interface。该需求应在 Stage 9 设计阶段评估，**当前不构成 Stage 8 Formal Reopen**。
