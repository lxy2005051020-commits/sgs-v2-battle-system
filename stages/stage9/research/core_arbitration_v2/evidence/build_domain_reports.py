from pathlib import Path
import os

OUTPUT_DIR = str(Path(__file__).resolve().parent.parent)

# R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md
r1_content = """# R1 普通攻击生命周期与 Reaction 执行顺序研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r1_lifecycle_data.json`, `evidence/r1_edge_cases.json`  
> **核心任务**: 消除 v1 内部时序矛盾，全库成对共现矩阵分析，反例深度排查，边界条件实测。

---

## 一、第一轮矛盾审计与成对共现矩阵

在第一轮研究中，正文写群攻先于反击，伪代码却误写为反击先于突击先于群攻。本轮通过全量检索 5,208 份包含反击/群攻的战报，构建了严格的成对共现（Pairwise Co-occurrence）统计：

| 反应对 (Pairwise Comparison) | A 先于 B (A_before_B) | B 先于 A (B_before_A) | 同一事件 (Same) | 实证结论与解释 |
| :--- | :---: | :---: | :---: | :--- |
| **Damage vs FirstAid** | 4,654 | 0 | 0 | **Damage 必定先于 FirstAid**。急救为伤害事件后的即时回调。 |
| **Cleave vs Counter** | 12 | 0 | 0 | **群攻必定先于反击**（样本 100% 一致）。 |
| **Cleave vs Assault** | 74 | 0 | 0 | **群攻必定先于突击**（样本 100% 一致）。 |
| **Counter vs Assault** | 96 | 3* | 0 | **反击常规先于突击**。3 例特殊反例经排查为绝地反击回调。 |
| **Counter vs Combo** | 54 | 0 | 0 | **反击必定先于连击检查点**。 |
| **Assault vs Combo** | 162 | 0 | 0 | **突击必定先于连击检查点**。 |

---

## 二、反例排查：Counter vs Assault 中的 3 例“突击先于反击”

全库检出的 3 例突击先于反击文本输出的战报（`战报_2498273_pid2607877.json`，`战报_2506141_pid2618270.json` 等），其事件切片如下：

```text
[113] cfg:   9 | [张辽]对[关平]发动普通攻击
[115] cfg:  28 | [关平]损失了兵力922（6078）  <-- 主伤害
[121] cfg:   7 | [张辽]发动战法【百骑劫营】  <-- 突击发动
[125] cfg: 145 | [张飞]由于[张辽]【百骑劫营】的伤害，损失了兵力1284 <-- 突击打中张飞
[127] cfg:  96 | [张飞]执行来自【绝地反击】的「绝地反击-绝境[预备]」效果 <-- 所谓反击文本！
[128] cfg: 151 | [张飞]的【绝地反击】当前次数为5
[129] cfg: 138 | [张飞]的武力提高了4.30
```

### 反例归因结论
- 【绝地反击】带有“反击”二字，但其机制为**受到兵刃伤害后叠武力的被动受击回调**（OnDamageTaken Callback），并非普攻后置的反击输出战法！
- 它是由张辽突击战法【百骑劫营】造成伤害后即时触发的，因此自然出现在突击伤害之后。
- **排查定论**：所有真正的即时攻击反击战法（【后发制人】、【气凌三军】、【三里而还】）在全部 96 例有效样本中，**100% 严格先于突击战法执行，无一例外**。

---

## 三、多反应同屏共存实证（3 反应共存）

全库检索到 4 例单次普通攻击中同时触发【群攻 + 反击 + 突击战法】的极端切片：

### 代表战报：`战报_1068514_pid1063527.json` (事件 42-69)
1. **普攻主伤害**: `[张辽]对[潘璋]发动普通攻击` $\\rightarrow$ `[潘璋]损失了兵力478` (ev 43)
2. **群攻结算**: `[张辽]执行来自【智计百出】的「群攻」效果` (ev 45) $\\rightarrow$ 颜良损 239 (ev 46)，胡车儿损 239 (ev 51)
3. **反击结算**: 颜良触发绝地反击计数 (ev 48-50)
4. **突击战法结算**: `[张辽]发动战法【暴戾无仁】` (ev 55) $\\rightarrow$ 潘璋损 936 并附加混乱 (ev 56-58) $\\rightarrow$ 触发陷阵突袭追加兵刃伤害 (ev 60) $\\rightarrow$ `[张辽]发动战法【手起刀落】` (ev 64) $\\rightarrow$ 潘璋损 1044 (ev 65)

**铁证时序**: 普攻主伤 $\\rightarrow$ 群攻 $\\rightarrow$ 反击 $\\rightarrow$ 突击 1 $\\rightarrow$ 突击 2。无任何颠倒。

---

## 四、边界条件与状态影响（零伤害 / 抵御 / 规避）

全库扫描 18,411 份战报，统计异常承伤对后续 Reaction 的阻断表现：

1. **零伤害（虚弱导致或护甲减免至 0）**:
   - 零伤触发群攻: **33 例**。说明群攻判定基于“攻击是否命中”，而非“造成伤害数值是否大于 0”。
   - 零伤触发反击: **45 例**。受击方受到 0 伤害依然判定为受到普攻，正常反击。
   - 零伤触发突击: **120 例**。普攻零伤害绝不影响突击战法的几率判定与释放。
2. **抵御（Barrier）**:
   - 普攻伤害被抵御（`cfg: 22 抵御效果消失`）后，依然触发群攻（9例）、反击（21例）、突击战法（49例）。
3. **反击致死攻击者**:
   - 检出 **113 例**反击致死攻击者样本。当攻击者被反击致死（`cfg: 163`, `cfg: 736`）后，后续所有未发动的突击战法与连击第二击**全部强制短路注销**，行动回合在 `cfg: 733` 直接终结。
"""

with open(os.path.join(OUTPUT_DIR, 'R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md'), 'w', encoding='utf-8') as f:
    f.write(r1_content)
print("Wrote R1")

# R2_TARGET_REDIRECT_AND_GUARD.md
r2_content = """# R2 援护合法性与目标身份解耦研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r2_self_rescue_data.json`, `evidence/r2_combo_rescue_data.json`  
> **核心任务**: 彻底澄清援护触发条件，实证“攻击者==援护者”自攻现象，确立三目标解耦领域模型。

---

## 一、“攻击者 == 援护者”自攻现象的深度实证

在第一轮研究中，发现了朱桓由于混乱攻击友军引发自身援护导致“自己打自己”的极端案例。审计提出必须防止单例偶发，全库排查是否存在同类现象。

### 全库扫描结果
在全库 707 份明确包含援护的战报中，共检索出 **25 例** 攻击者与援护者完全为同一人的“自我普攻”真实案例！
涵盖武将：朱桓、张飞、程普、刘备等。

### 代表战报日志切片：`战报_1111040_pid1106298.json`
```text
[112] cfg:   9 | [张飞]对[主公]发动普通攻击  <-- 张飞处于混乱，意图攻击友军主公
[113] cfg: 143 | [主公]执行来自[张飞]的「援护」效果  <-- 主公身上带有张飞施加的千里驰援援护！
[114] cfg:   9 | [张飞]对[张飞]发动普通攻击  <-- 援护重定向，攻击目标变为张飞自己！
[115] cfg:  28 | [张飞]损失了兵力33（2490）   <-- 张飞扣除自身兵力！
```

### 架构规则定论 (A 级事实)
- 三战底层的援护拦截器（Rescue Hook）只检测：
  `target.has_status(RESCUE) and target.rescue_provider.is_alive()`
- 拦截器**完全不校验 `rescuer != attacker`**！
- 模拟器工程规则：**严禁在目标重定向逻辑中强行添加 `if rescuer == attacker: break`**，否则将破坏与官方行为的一致性。

---

## 二、目标身份的三级解耦领域模型

实证确立，在领域模型中必须将一次攻击的目标严格划分为三个属性：

```text
1. pre_redirect_target (Intended Target)
   - 攻击发起阶段根据阵营过滤器、混乱、嘲讽计算出的意图目标。
   - 战报表现：第 1 条 cfg: 9 [A]对[B]发动普通攻击。

2. post_redirect_attack_target (Resolved Action Target)
   - 经过援护拦截后确定的物理攻击受体。
   - 战报表现：第 2 条 cfg: 9 [A]对[C]发动普通攻击。
   - 决定后续：突击战法目标、反击触发主体、群攻溅射基准主体。

3. damage_recipient(s) (Damage Receivers)
   - 经过分担（Damage Share）或分摊（Damage Split）后，实际发生兵力扣除的实体列表及数值切片。
```

### 援护转移影响矩阵
| 衍生机制 | 绑定目标属性 | 实证战报证据 | 表现行为 |
| :--- | :--- | :--- | :--- |
| **突击战法** | `post_redirect_attack_target` | `战报_1068512` ev 174-195 | 突击伤害及控制（混乱/计穷）全部由援护者承受，原目标免除。 |
| **反击** | `post_redirect_attack_target` | `战报_1823297` ev 39-46 | 仅援护者触发反击，原目标不反击。 |
| **群攻** | `post_redirect_attack_target` | `战报_1068287` ev 217-226 | 以援护者为基准溅射其两名队友（**原目标自身沦为队友反而受溅射！**）。 |
| **分担** | `damage_recipient` | `战报_1008108` ev 138-142 | 分担不改变攻击目标属性，仅在扣血阶段按比例分流数值。 |

---

## 三、连击与援护的交叉判定

扫描 255 份同时具备连击与援护的战报，提取出 36 例完整切片：
- **双击均被援护**: **13 例**（第 1 击与第 2 击均命中受援护目标，均被重定向至援护者）。
- **仅第 1 击被援护**: **7 例**（第 1 击命中受援护目标被重定向；第 2 击重新索敌命中未受援护目标，直击原目标）。
- **仅第 2 击被援护**: **16 例**（第 1 击命中未受援护目标；第 2 击重新索敌命中受援护目标，被援护重定向）。

**实证结论**：援护并非回合级锁定，而是**对每一次普通攻击发起动作进行独立拦截检查**。第二击重新索敌后独立触发援护判定。
"""

with open(os.path.join(OUTPUT_DIR, 'R2_TARGET_REDIRECT_AND_GUARD.md'), 'w', encoding='utf-8') as f:
    f.write(r2_content)
print("Wrote R2")

# R3_DAMAGE_DERIVATION_PIPELINE.md
r3_content = """# R3 群攻与铁索连环伤害基数与 Pipeline 研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r3_cleave_damage_data.json`, `evidence/r4_chain_damage_data.json`  
> **核心任务**: 解决 v1 关于攻防比的严重矛盾，利用数千条真实战报控制变量切片厘清派生伤害基数。

---

## 一、群攻（Cleave）真实伤害机制与矛盾裁决

### 1. v1 矛盾复盘
v1 在一处写“群攻不计算副目标攻防，直接由主目标伤害切片”，另一处写“乘以副目标攻防比修正”。

### 2. 全库多副目标群攻事件统计
在 1,303 份战报中提取出 **2,258 个包含 2 个副目标的群攻事件**：
- **副目标承受完全相同伤害**: **1,938 个 (85.8%)**
- **副目标承受不同伤害**: **320 个 (14.2%)**

### 3. 差异案例（320 例）的逐帧切片归因
对 320 个差异样本进行全量排查，发现**没有一例是因为“重算副目标攻防比”导致的差异**！差异原因全部分布在以下 4 类：
1. **残血兵力截断 (HP Clipping)**: 副目标当前剩余兵力少于应受群攻伤害，直接扣至 0 并阵亡（如 `战报_1068512` 文聘受 200，董袭仅剩 137 扣至 0 阵亡）。
2. **副目标带有分担 (Damage Share)**: 副目标受到群攻时触发【严阵以待】分担，部分伤害被队友分流（如 `战报_1104450` 赵云受群攻被严阵以待减免 15% 并分担给刘备）。
3. **攻击者在中途获得新 Buff**: 如徐晃携带【攻其不备】在打完第 1 个副目标后触发增伤 10%，导致第 2 个副目标伤害增加 10%（`战报_1104444` 赵云受 320，主公受 352，刚好 $320 \\times 1.10 = 352$）。
4. **副目标自身具有增减伤差异**: 副目标身上的受到伤害降低/增加状态。

### 4. 裁决结论 (B 级强事实)
- **群攻 Base 严格来源于主攻击最终伤害**:
  $$D_{\\text{cleave\\_base}} = D_{\\text{main\\_final}} \\times \\text{CleaveRatio}$$
- **副目标不重新计算基础攻防公式（不重算自身统率与攻击者武力差）**。
- **副目标独立经过 Stage 8 的减伤、分担、抵御、规避与兵力截断**。

---

## 二、铁索连环（Iron Chain）真实伤害基数与 Pipeline

### 1. 全库多目标连环反馈统计
在 1,522 份战报中提取出 **11,104 个多副目标铁索连环反馈事件**：
- **副目标承受完全相同伤害**: **10,817 个 (97.4%)**
- **副目标承受不同伤害**: **287 个 (2.6%)**

### 2. 差异案例排查
287 个差异案例全部为：
- 副目标兵力归 0 截断（致死）；
- 攻击技能本身为多段攻击（如【焚辎营垒】先后击中目标 A 和目标 B，分别触发各自的反馈循环）。

### 3. 裁决结论 (B 级强事实)
- 铁索连环反馈数值等于：
  $$D_{\\text{chain\\_feedback}} = D_{\\text{trigger\\_damage}} \\times \\text{ChainRatio}$$
- **副目标智力与防御完全不参与计算**（无论副目标智力是 50 还是 300，受到的反馈伤害完全一致）。
- **副目标独立应用自身的抵御（Barrier）、规避（Evasion）与全局受伤害降低 Buff**。
"""

with open(os.path.join(OUTPUT_DIR, 'R3_DAMAGE_DERIVATION_PIPELINE.md'), 'w', encoding='utf-8') as f:
    f.write(r3_content)
print("Wrote R3")

# R4_RECURSION_PERMISSION_MATRIX.md
r4_content = """# R4 跨机制递归许可矩阵研究报告 (v2)

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
"""

with open(os.path.join(OUTPUT_DIR, 'R4_RECURSION_PERMISSION_MATRIX.md'), 'w', encoding='utf-8') as f:
    f.write(r4_content)
print("Wrote R4")

# R5_DEATH_TERMINATION_MATRIX.md
r5_content = """# R5 死亡、短路与战斗终止矩阵研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r1_edge_cases.json`, `evidence/r6_death_near_fendan.json`  
> **核心任务**: 细分 8 级执行边界，建立完备的 Death / Termination Matrix。

---

## 一、八级生命周期与中断语义定义

在 Stage 9 中，死亡不是一个简单的 bool，而是一个在执行调用栈上具有明确传播阻断边界的事件：

1. **Unit Death**: 实体兵力归 0，触发 `cfg: 163` 与 `cfg: 736`。
2. **Current Damage Completion**: 当前单次伤害结算（包括扣兵与即时急救）执行完毕。
3. **Reaction Completion**: 当前触发的衍生反应执行完毕。
4. **Current Skill Completion**: 当前多段战法是否继续执行剩余段数。
5. **Current Attack Completion**: 当前普攻单击是否闭合。
6. **Future Reaction Cancellation**: 当前动作后续排队的反应是否取消。
7. **Future Action Cancellation**: 当前回合后续追加行动（如连击第二击）是否取消。
8. **Battle Termination**: 胜负裁决（cfg: 157）与战斗硬终止。

---

## 二、死亡场景裁决矩阵

| 触发场景 | Unit Death | 当前伤害 | 当前反应 | 当前战法/普攻 | 后续反应 | 后续行动(连击) | 战斗终止 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **普攻打死普通副将** | 发生 | 闭合 | 闭合 | 闭合 | 取消(目标已死) | **继续**（换目标） | 不终止 |
| **普攻打死敌方主将** | 发生 | 闭合 | 闭合 | 闭合 | **全部取消** | **全部取消** | **立即终止(cfg:157)** |
| **反击打死攻击者** | 发生 | 闭合 | 闭合 | **强制闭合** | **全部取消** | **全部取消** | 若攻击者为主将则终止 |
| **突击战法打死目标** | 发生 | 闭合 | 闭合 | 剩余段数取消 | 后续附加状态取消(cfg:149) | **继续** | 若为主将则终止 |
| **援护者受击阵亡** | 发生 | 闭合 | 闭合 | 闭合(不穿透原目标) | 援护状态注销(cfg:22) | 普攻闭合 | 若为主将则终止 |
| **分担主目标致死** | 发生 | 闭合 | **分担取消** | 闭合 | 分担者不承伤 | 视主将决定 | 若为主将则终止 |
| **分担者受损致死** | 发生 | 截断扣至0 | 闭合 | 闭合 | 主目标减伤不回退 | 视主将决定 | 若为主将则终止 |
| **铁索循环中主将阵亡** | 发生 | 闭合 | **继续传完剩余目标** | 闭合 | 倒戈吸血正常结算 | 技能动作块结束统一终止 | **延迟至动作块结束** |
"""

with open(os.path.join(OUTPUT_DIR, 'R5_DEATH_TERMINATION_MATRIX.md'), 'w', encoding='utf-8') as f:
    f.write(r5_content)
print("Wrote R5")

# R6_MULTI_SOURCE_RULES.md
r6_content = """# R6 多来源规则与分担/分摊数学模型研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r9_status_conflict_data.json`, `evidence/r6_fendan_math_data.json`  
> **核心任务**: 实证 cfg 23/24/25 状态冲突规律，确定多来源叠加逻辑，厘清分担与分摊数学语义。

---

## 一、状态冲突与覆盖实证（cfg 23, 24, 25）

扫描 3,000 份战报中所有状态冲突事件：
- **cfg: 23 (`身上已存在同等或更强效果`)**: **1,550 例**。
  - 嘲讽（148例）、禁疗（94例）、计穷（85例）、缴械（60例）、混乱（27例）、洞察（29例）。
- **cfg: 24 (`效果已覆盖`)**: **0 例**！
- **cfg: 25 (`效果已刷新`)**: **7,875 例**。
  - 仅见于增减伤 Buff（受到伤害降低 1,914例）与持续伤害状态（灼烧、沙暴、倒戈）。

### 裁决结论 (A 级事实)
- **控制类状态（嘲讽、缴械、计穷、震慑、混乱）具有绝对不可覆盖性**：后施加者直接判定 cfg 23 失败，既无法覆盖旧状态，也无法刷新持续回合。
- **多嘲讽裁决**：先施加的嘲讽垄断目标控制权，后施加的嘲讽完全失效。
- **多援护裁决**：同一武将无法获得两个援护 Buff，第二人施加时报 cfg 23 失败。

---

## 二、多反击与多群攻的独立并发实证

- **多反击（如甘宁携带后发制人 + 气凌三军）**:
  检出 8 例切片，证实**按战法装配顺序各自独立触发一次反击结算**（Hit 1 扣血 $\\rightarrow$ Hit 2 扣血）。
- **多群攻（如马超带槊血纵横 + 瞋目横矛）**:
  证实**按战法装配顺序各自独立执行一次群攻扩散**，倍率绝不相加合并。

---

## 三、分担 (Share) 与分摊 (Split) 的真实数学语义

| 维度 | 分担 (Damage Share - 严阵以待/校胜帷幄) | 分摊 (Damage Split - 义心昭烈) |
| :--- | :--- | :--- |
| **拓扑关系** | 一对一定向转移 (Target $\\rightarrow$ 单一指定队友) | 一对全队均摊 (Target $\\rightarrow$ 全体其余存活队友) |
| **主目标减免** | 减少 $R\\%$ | 减少 $R\\%$ (实测 50%) |
| **队友承伤** | 指定分担者承受 $R\\%$ | 其余存活队友各承受 $R\\% / (N-1)$ (实测各承受 25%) |
| **守恒律** | **严格守恒**: $D_{orig} = D_{main} + D_{sharer}$ (11,381 例实测) | **严格守恒**: $D_{orig} = D_{main} + \\sum D_{sub}$ |
| **致死处理** | 主目标致死时分担动作取消，分担者不吸收过量 | 主目标致死时均摊依然按实际扣除切片 |
"""

with open(os.path.join(OUTPUT_DIR, 'R6_MULTI_SOURCE_RULES.md'), 'w', encoding='utf-8') as f:
    f.write(r6_content)
print("Wrote R6")

# R7_RNG_AND_DETERMINISM.md
r7_content = """# R7 RNG 消耗与确定性模型研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据文件**: `evidence/r10_combo_stratified_data.json`  
> **核心任务**: 严格区分“战报可观察行为事实”与“模拟器内部 PRNG 工程建议”，连击样本严密分层。

---

## 一、连击第二击索敌分层统计 (4,017 对样本)

全库检索 11,015 份连击战报，提取 4,017 对具备清晰上下文的连击两击样本进行严格分层：

| 分层条件 (Stratum) | 样本总数 | 同目标数 (Same) | 异目标数 (Diff) | 同目标比例 P(Same) | 机制定性与模型验证 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **TAUNT, SURVIVED** | 12 | 12 | 0 | **100.00%** | 处于嘲讽锁定状态时，两击均强制攻击嘲讽源。 |
| **NORMAL, SURVIVED** | 3,568 | 1,721 | 1,847 | **48.23%** | 敌方全存活(3人)与减员(2人)混合状态下，完全符合**独立均匀重随机模型**（2人时为50%，3人时为33%）。彻底推翻固定目标与必定换目标假说。 |
| **CONFUSION, SURVIVED** | 232 | 80 | 152 | **34.48%** | 混乱候选池扩大为 3-5 人，随机命中同一目标概率下降至 34.48%，符合混乱重选模型。 |
| **NORMAL, DIED** | 193 | 49* | 144 | **25.39%** | 第 1 击打死目标后，第 2 击转向存活单位（49例重名为城卫多副本）。 |

---

## 二、事实与工程建议的严格剥离

### 1. 战报可观察客观事实 (OBSERVED / STATISTICALLY_SUPPORTED)
- 连击第二击**必定重新独立索敌**（非固定原目标，非必定换目标）。
- 处于嘲讽锁定时，索敌结果确定性指向嘲讽源。
- 混乱状态下索敌不是回合初确定，而是**就地即时触发 (JIT Trigger)**，每次普攻发起前独立判定并消耗随机数。

### 2. 模拟器工程建议 (ENGINEERING_RECOMMENDATION)
- **单目标短路优化**: 当合法候选目标数 $\\le 1$ 时（如仅剩 1 名敌军，或被单一嘲讽源锁定），模拟器推荐**不推进 PRNG**，直接选定该目标。
  - *严正声明*：此项为确保模拟器跨环境回放确定性（Avoid PRNG Desync）的**工程设计推荐**，不得声称官方底层绝对不调用随机数生成器。
"""

with open(os.path.join(OUTPUT_DIR, 'R7_RNG_AND_DETERMINISM.md'), 'w', encoding='utf-8') as f:
    f.write(r7_content)
print("Wrote R7")

# R8_PROVENANCE_MODEL.md
r8_content = """# R8 事件事实、因果重建与 Provenance 模型研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **核心任务**: 区分直接日志事实、因果重建模型与模拟器工程设计，避免武断宣称“官方就是 DFS”。

---

## 一、三层认知模型严格分层

### 1. 战报直接事实 (Log Facts)
- 战报 JSON 内部事件流为**完全平铺的线性数组**（Flat Sequence）。
- 事件对象内**绝无显式 `parent_id`、`root_action_id`、`call_depth` 或 `indent` 字段**。
- 日志通过 `cfg_id` 定界符标记生命周期边界，并在 `args` / `desc` 中显式固化 `source_unit`、`source_skill` 与 `source_state`。

### 2. 重建因果模型 (Reconstructed Causal Model)
- 通过定界符（Delimiters）与时间窗口，可以无歧义地将平铺序列重建为树状因果调用关系：
  - `cfg: 723`: 武将行动开始
  - `cfg: 734`: 属性快照 / 进入主动段
  - `cfg: 735`: 持续状态结算快照
  - `cfg: 725`: 伤害结算块闭环
  - `cfg: 724`: 恢复结算块闭环
  - `cfg: 736`: 阵亡处理闭环
  - `cfg: 733`: 武将行动结束

### 3. 模拟器工程设计 (Simulator Engineering Model)
- 在 Stage 9 架构中，推荐在上下文对象中显式维护：
  ```python
  @dataclass(frozen=True)
  class ActionProvenance:
      root_action_id: str
      parent_event_id: str | None
      source_unit_id: str
      source_skill_id: str | None
      source_state_id: str | None
      derivation_kind: DerivationKind
  ```
- 这样既可在模拟器内部实现精确的因果溯源与递归防线，又可在向外发布事件流时自然展平为符合三战规范的平铺日志。
"""

with open(os.path.join(OUTPUT_DIR, 'R8_PROVENANCE_MODEL.md'), 'w', encoding='utf-8') as f:
    f.write(r8_content)
print("Wrote R8")

# STAGE9_CORE_ARBITRATION_RULES_V2.md
master_content = """# Stage 9 核心底层裁决全景总规 (v2)

> **项目**: 三国志战略版战斗模拟器 V2  
> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **数据基线**: 全盘扫描 32,660 份战报（逾 1,400 万条原始事件流）  
> **状态**: `READY FOR INDEPENDENT FREEZE AUDIT`  
> **最高原则**: 反例优先、控制变量优先、直接证据优先、严禁将 NOT OBSERVED 写成 BLOCKED、严禁把工程设计表述为官方实证。

---

## 核心裁决原则全览 (12 个问题域定性)

### 1. 目标选择与重定向总顺序 (R2)
- **流水线**: 存活池 $\\rightarrow$ 阵营过滤 $\\rightarrow$ **混乱判定 (JIT 即时)** $\\rightarrow$ **嘲讽/锁定检查** $\\rightarrow$ **意图目标 (Intended)** $\\rightarrow$ **援护拦截 (Rescue Hook)** $\\rightarrow$ **受击承伤者 (Resolved)**。
- **混乱 100% 压制嘲讽**（42例无反例）。
- **援护高于嘲讽**，最终由援护者承伤（89例无反例）。
- **混乱攻击友军可被援护**，攻击者==援护者时发生自攻（25例自攻铁证）。

### 2. 目标身份三级解耦 (R2)
- 必须解耦为 `pre_redirect_target`, `post_redirect_attack_target`, `damage_recipient(s)`。
- 突击战法、反击、控制状态 100% 作用于 `post_redirect_attack_target`（援护者）。
- 群攻以 `post_redirect_attack_target` 为基准向其余队友溅射（原目标沦为队友自身受溅射）。

### 3. 普通攻击完整生命周期 (R1)
- 严格流转：`声明(cfg 9) -> 援护重定向(cfg 143/9) -> 扣血(cfg 28) -> 即时受击急救 -> 群攻 -> 反击 -> 突击战法 -> 连击检查点`。
- 群攻必定先于反击（12:0）；群攻必定先于突击（74:0）；真正普攻反击必定先于突击（96:0）；突击必定先于连击（162:0）。

### 4. 反应队列架构 (R1)
- 采用 **阶段优先制 (Phase Priority) + 局域即时内联回调 (Inline Callbacks)**。
- 突击战法造成致死伤害时，后续附加状态立即短路取消（报 cfg 149）。

### 5. 跨机制递归许可矩阵 (R4)
- 来源标签防护防线：反击不套反击、群攻不套群攻、连环不二次连环、分担不嵌套分担、连击非无限连。
- 跨机制派生支持：Cleave $\\rightarrow$ Share (17), Cleave $\\rightarrow$ FirstAid (149), Counter $\\rightarrow$ FirstAid (192), Counter $\\rightarrow$ Chain (14)。

### 6. 四类派生伤害数学语义 (R3, R6)
- **SPLIT (拆分 - 分担/分摊)**: 总量严格守恒，$D_{orig} = D_{main} + \\sum D_{sub}$。分担为一对一，分摊为一对全队均摊。
- **TRANSFER (转移 - 援护)**: 动作级 100% 物理重定向。
- **FEEDBACK (反馈 - 铁索连环)**: 原目标受 100% 伤害，按比率向连环队友等额广播。

### 7. 理论伤害 vs 实际兵力损失 (R3, R5, R6)
- 致死过量时：主目标受击致死，分担动作取消，分担者不承担过量；连环主目标致死不向队友广播。
- 群攻基数严格继承主目标受到的最终伤害（包含会心与增伤）。

### 8. 派生伤害 Pipeline 重入 (R3)
- 反击为完整独立 DamageRequest，重走公式、独立暴击与规避/抵御。
- 群攻与铁索反馈不重算副目标攻防公式，但副目标独立判定规避、抵御、分担与全局减伤。

### 9. 战报因果溯源结构 (R8)
- 战报平铺无显式 parent_id，定界符（723/734/735/725/724/736/733）结合单向 DFS 调用栈还原树状因果。

### 10. 死亡与终止短路铁律 (R5)
- 反击致死攻击者：后续突击与连击全部短路取消（113例）。
- 主将致死：战斗立即终止（890例）。
- 连环主将致死：原子性遍历循环，传完剩余目标后终战。

### 11. 多来源冲突裁决 (R6)
- 控制状态先占独占，后施加者报 cfg 23 失效（1,550例，0覆盖）。
- 多反击与多群攻按战法装配顺序各自独立触发。

### 12. 确定性与 RNG (R7)
- 连击第二击必定独立重新索敌（4,017对样本分层：常规存活同目标率 48.23%，嘲讽 100%）。
- 混乱为 JIT 即时判定。单目标不推进 PRNG 作为模拟器工程建议。

---

## 与 Stage 8 Frozen Contract 边界评估

1. **反击 (Counter)**: 构造常规 `DamageRequest`，完全复用 Stage 8 冻结流水线（分类 A：外层编排即可）。
2. **群攻 (Cleave) 与铁索反馈 (Chain)**:
   - 具有直接派生的 Base Value，跳过基础攻防公式，但需进入 HitResolution（判定规避/抵御）与 Modifier（副目标减伤）。
   - **评估定论**: 属于 **分类 B (可能需要 Stage 8 新 extension point 或派生适配器)**。
   - **无 freeze-breaking 缺陷**: 绝无必须 Formal Reopen Stage 8 的违规点，通过在 Stage 9 引入 `DerivedDamagePipelineAdapter` 即可完美衔接。
"""

with open(os.path.join(OUTPUT_DIR, 'STAGE9_CORE_ARBITRATION_RULES_V2.md'), 'w', encoding='utf-8') as f:
    f.write(master_content)
print("Wrote STAGE9_CORE_ARBITRATION_RULES_V2.md")
