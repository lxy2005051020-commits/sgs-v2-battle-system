# Stage 9 核心底层裁决全量证据矩阵 (Evidence Matrix v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（全量事件逾 1,400 万条）  
> **置信度标尺**:
> - `A — FROZEN FACT`: 直接可观察、定义无歧义、样本充分、针对性反例搜索完成且归因清晰、跨文档完全一致。
> - `B — STRONG`: 大样本一致支持、统计特征高度显著、机制模型自洽、反例已排除，但允许包含部分内部模型合理推论。
> - `C — PROVISIONAL`: 样本量较少、有效机会（分母）为 0 导致仅为“未观察到 (NOT OBSERVED)”而非“已阻断 (BLOCKED)”、或存在合理解释竞争。
> - `D — WEAK`: 极少量样本或间接日志推断。
> - `E / UNKNOWN`: 当前战报无直接证据，标记为工程待定或官方未知，严禁工程伪装。

---

## 证据矩阵总表

| ID | Mechanism | Claim | Classification | Evidence Files | Cases / Denominator | Counterexamples | Confidence | Stage8 Impact | Remaining Unknowns |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **EM-01** | 目标裁决顺序 | 混乱压制嘲讽锁定，进入全场无差别目标池选择 | OBSERVED | `r11_confusion_taunt_data.json`<br>`raw_slices/EM-01_*` | 1,351 (有效分母1351) | 0 (79.1%切目标, 20.9%随机打嘲讽源) | **A** | A (无冲击) | 混乱全场无差别的精确权重分布（敌/友） |
| **EM-02** | 目标重定向 | 援护优先级高于嘲讽，最终由援护者代为承受物理攻击 | OBSERVED | `战报_5176492`<br>`r2_self_rescue_data.json` | 89 | 0 | **A** | A (无冲击) | 无 |
| **EM-03** | 援护合法性 | 友军受混乱攻击可被同队援护；攻击者==援护者时发生自攻 | OBSERVED | `战报_1111040`<br>`raw_slices/EM-03_*` | 25 | 0 | **A** | A (无冲击) | 无 |
| **EM-04** | 目标解耦 | 必须解耦 `intended_target`, `resolved_target`, `damage_recipient` | INFERRED | `战报_1068287`<br>`战报_1068512` | 3,250 | 0 | **A** | A (无冲击) | 无 |
| **EM-05** | 群攻基准点 | 群攻以受击承伤者（resolved_target）为基准向其余队友溅射 | OBSERVED | `战报_1068287`<br>`r3_cleave_damage_data.json` | 18 | 0 | **B** | A (无冲击) | 样本量较少(18例)，需保持强审慎性 |
| **EM-06** | 反击承伤者 | 反击由实际受击者（援护者）触发，原目标绝不触发 | OBSERVED | `战报_1823297`<br>`r1_lifecycle_data.json` | 96 | 0 | **A** | A (无冲击) | 无 |
| **EM-07** | 突击受击者 | 突击战法及控制状态作用于实际受击者（援护者）身上，原目标免除 | OBSERVED | `战报_1068512`<br>`战报_1104553` | 74 | 0 | **A** | A (无冲击) | 无 |
| **EM-08** | 普攻反应时序 | 严格流转：主扣血 $\rightarrow$ 受击回调(急救/绝地) $\rightarrow$ 群攻 $\rightarrow$ 普攻反击 $\rightarrow$ 突击 $\rightarrow$ 连击 | STATISTICALLY_SUPPORTED | `r1_lifecycle_data.json`<br>`raw_slices/EM-08_*` | 182 | 0 (已排除绝地反击) | **B** | A (外层编排) | 群攻 vs 反击共现仅 12:0，评级定为 B |
| **EM-09** | 急救时点 | 急救挂载于扣血事件后即时内联回调（OnDamageTaken Callback） | OBSERVED | `r1_lifecycle_data.json` | 4,654 | 0 | **A** | A (无冲击) | 无 |
| **EM-10** | 零伤/抵御反应 | 普攻造成 0 伤或被抵御，依然可正常触发群攻、反击与突击 | OBSERVED | `r1_edge_cases.json` | 281 | 0 | **A** | A (无冲击) | 特殊限定战法除外 |
| **EM-11** | 反击套反击防线 | 反击伤害不触发对方被动反击 (BLOCKED) | OBSERVED | `r7_recursion_denominators.json`<br>`raw_slices/EM-11_*` | 0 / 90 (有效分母90) | 0 | **B** | A (无冲击) | 样本分母 90 例，未见递归，评级定为 B |
| **EM-12** | 群攻套群攻防线 | 群攻溅射伤害不触发群攻 (NOT OBSERVED) | INFERRED | `r7_recursion_matrix_data.json` | 0 / 0 (机制无受击群攻) | 0 | **C** | A (无冲击) | 机制无受击触发群攻，分母为0，定为设计不变量 |
| **EM-13** | 连环套连环防线 | 铁索连环反馈伤害绝不再次触发连环广播 (BLOCKED) | STATISTICALLY_SUPPORTED | `r7_recursion_denominators.json`<br>`raw_slices/EM-22_*` | 0 / 23,620 (有效分母23620) | 0 | **A** | A (无冲击) | 无 |
| **EM-14** | 分担套分担防线 | 分担伤害未见被二次分担 (NOT OBSERVED) | INFERRED | `r7_recursion_denominators.json` | 0 / 0 (无同队双分担共存) | 0 | **C** | A (无冲击) | 缺乏双分担同队有效分母，定为设计不变量 |
| **EM-15** | 分担数学语义 | 分担严格为 TRANSFER/SPLIT，总量守恒：$D_{orig} = D_{main} + D_{sharer}$ | STATISTICALLY_SUPPORTED | `r6_fendan_math_data.json` | 11,381 | 0 | **A** | A (无冲击) | ±1 点兵力取整舍入细节 |
| **EM-16** | 铁索反馈语义 | 铁索严格为 FEEDBACK，原目标承伤不减，等额向连环队友广播 | STATISTICALLY_SUPPORTED | `r4_chain_damage_data.json` | 10,817 | 0 | **A** | A (外层广播) | 无 |
| **EM-17** | 群攻 Pipeline | 群攻最符合 fixed derived base + target modifier 模型，跳过副目标攻防公式 | STATISTICALLY_SUPPORTED | `r3_cleave_damage_data.json` | 2,258 | 0 | **B** | B (派生适配器) | 官方内部具体函数实现不可见 |
| **EM-18** | 铁索 Pipeline | 铁索最符合 fixed derived base + target modifier 模型，跳过副目标智力公式 | STATISTICALLY_SUPPORTED | `r4_chain_damage_data.json` | 11,104 | 0 | **B** | B (派生适配器) | 官方内部具体函数实现不可见 |
| **EM-19** | 致死分担截断 | 主目标受击兵力致死时，未观察到分担转嫁发生 | OBSERVED | `r6_death_near_fendan.json`<br>`raw_slices/EM-19_*` | 154 | 0 | **B** | A (无冲击) | 内部具体短路时序节点推论 |
| **EM-20** | 反击致死短路 | 攻击者在反击中阵亡，后续突击战法与连击第二击短路取消 | OBSERVED | `r1_edge_cases.json`<br>`raw_slices/EM-21_*` | 113 | 0 | **A** | A (无冲击) | 无 |
| **EM-21** | 主将阵亡终战 | 主将阵亡执行延迟终战（完成当前原子技能循环后终战） | OBSERVED | `raw_slices/EM-21_*` | 890 | 0 | **A** | A (无冲击) | 极端连环多段循环细节 |
| **EM-22** | 连环主将阵亡 | 连环循环中主将阵亡，先完成本轮剩余连环广播再终战 | OBSERVED | `战报_1104998`<br>`raw_slices/EM-22_*` | 5 | 0 | **C** | A (无冲击) | 仅检出 5 例样本，评级降为 C |
| **EM-23** | 多控制冲突排斥 | 重复施加控制多数表现为 cfg 23 拒绝；更强效果能否覆盖弱控未证实 | OBSERVED | `r9_status_conflict_data.json` | 1,550 | 0 | **B** | A (无冲击) | 更强效果是否可覆盖弱控属于 UNKNOWN |
| **EM-24** | 多反击触发 | 同武将携带多个反击战法，受击后按战法装配顺序独立触发 | OBSERVED | `inspect_recursion_details.py` | 8 | 0 | **C** | A (外层编排) | 样本量较少(仅8例)，评级降为 C |
| **EM-25** | 连击重新索敌 | 连击第二击重新执行索敌，合法候选池中按 1/K 独立随机均匀索敌 | STATISTICALLY_SUPPORTED | `r10_combo_detailed_stratified.json` | 34,639 (全量提取) | 0 (1目标100%, 2目标50.5%, 3目标33.8%) | **A** | A (无冲击) | 官方内部 PRNG 种子算法不可见 |
| **EM-26** | 混乱即时判定 | 混乱为 JIT 即时判定，每次普通攻击发起前就地独立判定 | OBSERVED | `战报_1516261`<br>`战报_1105314` | 320 | 0 | **A** | A (无冲击) | 无 |

---

## 阶段核验统计与评级分布

全矩阵共 26 项核心机制断言，经过提取器全面修复与全量重提取后：
* **Grade A (FROZEN FACT)**: **14 项** (53.8%)
* **Grade B (STRONG)**: **8 项** (30.8%)
* **Grade C (PROVISIONAL)**: **4 项** (15.4%) —— 分别为：
  * `EM-12` (群攻套群攻：机制无受击群攻，有效分母为 0)
  * `EM-14` (分担套分担：无同队双分担互相分担，有效分母为 0)
  * `EM-22` (连环中主将阵亡：极少样本，N=5)
  * `EM-24` (多反击触发：极少样本，N=8)
* **Grade D / E**: **0 项**

> **审计判定说明**: 本矩阵中存在 4 项 Grade C 暂定规则（涉及递归分母缺失与极端边缘极低样本），且包含 2 项 UNKNOWN 领域（强弱控制覆盖能力、官方内部 PRNG 步进机制）。根据“严禁人为虚抬评级”与“存在非冻结事实即不可直接判定完全冻结”的纪律要求，本阶段应如实呈现证据强度分布。
