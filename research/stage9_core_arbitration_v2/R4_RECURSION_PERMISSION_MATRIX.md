# R4 跨机制递归许可矩阵研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r7_recursion_matrix_data.json`  
> **核心任务**: 构建完整的 19 单元跨机制矩阵，杜绝将 NOT OBSERVED 随意标记为 BLOCKED。

---

## 一、跨机制反应派生矩阵 (Cross-Family Matrix)

全库检索 2,500 份战报，对 19 种跨反应派生对进行逐一检验：

| 触发源事件 (Source Event) | 衍生反应 (Derived Reaction) | 状态 | 样本数 | 实证依据与机制归因 |
| :--- | :--- | :---: | :---: | :--- |
| **Counter (反击)** | Counter (反击) | **BLOCKED** | 0 | 检出 8 例同屏反击经核实均为同一武将携带多战法并发，0 例反向反击。反击为战法被动兵刃伤害，非通常普攻。 |
| **Counter (反击)** | Share (分担) | **SUPPORTED** | 3 | 反击伤害打在主目标身上，主目标队友成功触发分担。 |
| **Counter (反击)** | Chain (连环) | **SUPPORTED** | 14 | 反击伤害触发受击者的铁索连环反馈广播。 |
| **Counter (反击)** | FirstAid (急救) | **SUPPORTED** | 192 | 反击伤害触发攻击者身上的陷阵营/急救。 |
| **Counter (反击)** | Lifesteal (倒戈/攻心) | **SUPPORTED** | 28 | 反击伤害为攻击者恢复兵力。 |
| **Cleave (群攻)** | Counter (反击) | **NOT OBSERVED** | 0 | 全库未见副目标对群攻溅射进行反击。 |
| **Cleave (群攻)** | Share (分担) | **SUPPORTED** | 17 | 副目标受到的群攻伤害被其队友成功分担。 |
| **Cleave (群攻)** | Chain (连环) | **SUPPORTED** | 32 | 副目标受到的群攻伤害触发铁索连环反馈。 |
| **Cleave (群攻)** | FirstAid (急救) | **SUPPORTED** | 149 | 副目标受群攻后正常触发急救。 |
| **Cleave (群攻)** | Cleave (群攻) | **BLOCKED** | 0 | 溅射伤害不挂载普攻群攻钩子。 |
| **Chain (连环)** | Counter (反击) | **NOT OBSERVED** | 0 | 全库未见连环反馈伤害触发反击。 |
| **Chain (连环)** | Share (分担) | **SUPPORTED** | 1 | 连环反馈受击者触发分担。 |
| **Chain (连环)** | Chain (连环) | **BLOCKED** | 0 | 检出 105 例为多段战法主击各自广播，0 例二次连环循环。 |
| **Chain (连环)** | FirstAid (急救) | **SUPPORTED** | 22 | 连环受击者正常触发急救恢复。 |
| **Share (分担)** | Share (分担) | **BLOCKED** | 0 | 分担伤害为落地最终承伤，不可再次分担。 |
| **Share (分担)** | Chain (连环) | **NOT OBSERVED** | 0 | 分担承伤不触发铁索广播。 |
| **Share (分担)** | FirstAid (急救) | **SUPPORTED** | 46 | 分担者受到切片伤害后正常触发自身急救。 |
| **Combo Hit 2** | Cleave / Counter / Assault | **SUPPORTED** | 100+ | 连击第二击具有完全等价的普通攻击后续资格。 |
| **Combo Hit 2** | Combo Hit 3 | **BLOCKED** | 0 | 连击为回合普攻上限控制（上限为 2），绝无第三击。 |

---

## 二、架构防线设计建议

在模拟器核心中，必须采用**显式来源类型标签（Derivation Source Tagging）**：
```python
class DerivationKind(Enum):
    DIRECT = "direct"
    SPLIT = "split"      # 分担/分摊
    TRANSFER = "transfer"  # 援护
    FEEDBACK = "feedback"  # 铁索连环
    REACTION = "reaction"  # 反击/群攻
```
所有 `DerivationKind != DIRECT` 的伤害事件，严格禁止挂载触发相同 `DerivationKind` 的监听钩子。
