# R4 跨机制递归许可矩阵与有效分母审计报告 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据文件**: `evidence/r7_recursion_denominators.json`, `evidence/r7_recursion_matrix_data.json`, `evidence/raw_slices/EM-11_*`, `evidence/raw_slices/EM-22_*`  
> **核心任务**: 为递归禁止断言计算有效机会（Eligible Opportunities）分母，严格区分 BLOCKED 与 NOT OBSERVED (BF-06)。

---

## 一、 自递归机制的有效机会分母与定性

审计明确指出：未发生递归只有在具备“有效机会分母”的前提下，才能断言为 BLOCKED；若分母为 0，则仅能定性为 NOT OBSERVED。

| 自递归对 (Self-Recursion) | 源事件数 (Source Events) | 有效机会分母 (Eligible Opportunities) | 实际触发数 (Triggered) | 阻断比例 (Blocked Ratio) | 定性状态 (Status) | 证据等级 (Confidence) | 机制说明 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Counter $\rightarrow$ Counter** | 6,287 | **42** | 0 | 100.0% | **BLOCKED** | **Grade B** | 被反击者具备反击战法（后发/气凌）且受击存活的样本共 42 例，无一例反向反击。因分母有限，核定为 B 级。 |
| **Cleave $\rightarrow$ Cleave** | 2,258 | **0** | 0 | - | **NOT OBSERVED** | **Grade C** | 三战无任何“受兵刃伤害后发动群攻”的战法，机制上不存在有效触发机会。作为工程设计不变量。 |
| **Chain $\rightarrow$ Chain** | 24,433 | **24,433** | 0 | 100.0% | **BLOCKED** | **Grade A** | 铁索连环反馈的谋略伤害共现 24,433 次，其受击者身上处于连环且队友存活，但 0 次再次触发连环传播。 |
| **Share $\rightarrow$ Share** | 11,381 | **0** | 0 | - | **NOT OBSERVED** | **Grade C** | 战报中无同队双分担者互相分担的有效构筑样本，分母为 0。作为工程设计不变量。 |
| **Combo2 $\rightarrow$ Combo3** | 5,428 | **5,428** | 0 | 100.0% | **BLOCKED** | **Grade A** | 单回合连击执行第二击后，第三次普攻触发为 0。 |

---

## 二、 跨机制派生矩阵 (Cross-Mechanism Matrix)

在跨机制派生中，战报证实了合法的跨类型连锁触发：

| 触发源 (Source) | 承接机制 (Target) | 全库观察案例 (Observed Cases) | 典型战报举例 | 判定与置信度 |
| :--- | :--- | :---: | :--- | :---: |
| **Cleave (群攻)** | Share (分担) | 17 | `战报_1104450` 赵云受群攻，被刘备严阵以待分担 | 允许 [Grade A] |
| **Cleave (群攻)** | FirstAid (急救) | 149 | `战报_1068287` 副目标受群攻触发青囊急救 | 允许 [Grade A] |
| **Cleave (群攻)** | Chain (连环) | 12 | 谋略群攻命中连环副目标触发连环反馈 | 允许 [Grade B] |
| **Cleave (群攻)** | Counter (反击) | 0 (有效分母 28) | 副目标受溅射不触发对主攻击者的反击 | 阻断 [Grade B] |
| **Counter (反击)** | Share (分担) | 12 | 反击伤害被受击方队友分担 | 允许 [Grade B] |
| **Counter (反击)** | FirstAid (急救) | 192 | 被反击方受伤害触发急救回血 | 允许 [Grade A] |
| **Counter (反击)** | Chain (连环) | 14 | 谋略反击命中连环目标触发反馈 | 允许 [Grade B] |
| **Chain (连环)** | Share (分担) | 19 | 连环反馈伤害被副目标队友分担 | 允许 [Grade B] |
| **Chain (连环)** | FirstAid (急救) | 128 | 连环反馈伤害触发急救回血 | 允许 [Grade A] |
| **Chain (连环)** | Counter (反击) | 0 (有效分母 150) | 连环受击者不触发对伤害源的反击 | 阻断 [Grade A] |

---

## 三、 模拟器工程防御规范

根据上述实证，模拟器设计规范确立：
1. **天然被动阻断机制 (BLOCKED)**: 引擎必须显式增加来源标签过滤，防止 Counter 与 Chain 的二次递归。
2. **未观察到机制 (NOT OBSERVED)**: 针对 Cleave $\rightarrow$ Cleave 与 Share $\rightarrow$ Share，在缺乏官方对抗样本的情况下，统一设定 `ReactionDepth <= 1` 或派生标记，防御性阻断自递归循环。
