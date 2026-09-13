# RF-P07 Cleave State Lifecycle and Secondary Target Research Report
## 1. Executive Summary
本报告为 Stage 9 Contract Closure 中 **`RF-P07 — CLEAVE_STATE_AND_SECONDARY_TARGET_COMPLETION`** 的专项实证研究成果。
聚焦解决两个核心开放问题：- **`CLVS9-B02`**：690084 完整状态生命周期、容器模型、多来源共存与排序、同源刷新、倍率绑定。
- **`CLVS9-B03`**：群攻副目标候选池、数量、稳定排序规则、援护重定向副目标准入及 JIT 存活重校验。

### 核心实证结论
1. **Track A — 状态生命周期与多来源共存 (`CLVS9-B02`)**：   - **容器模型（Container Model）**：`SOURCE_BOUND_EFFECT_LIST`。同一武将身上的多个群攻来源**完全独立并存**，绝不将倍率相加合并为一个状态（`MERGED_RATIO_STATE` 证伪）。全库检出 **121 例**同一武将多群攻并存样本（如马超【槊血纵横】+【瞋目横矛】）。   - **同源重施加（Same-source Reapply）**：**`REFRESH`**。同战法再次发动时，输出 `[武将]身上的「群攻」效果已刷新`（检出 203 例），刷新持续时间，不叠加层数，不产生新实例，不拒绝施加。   - **多来源执行顺序（Execution Comparator）**：严格按照 **战法栏位升序（`SKILL_SLOT_ORDER`: Slot 0 主带固有 $	o$ Slot 1 第二战法 $	o$ Slot 2 第三战法）** 依次判定并执行。在全部 121 例多群攻样本中，【槊血纵横】（Slot 0）$	o$ 【瞋目横矛】（Slot 1/2）占比 **100.0%**（121/121），无一例外！   - **队列组织（Queue Composition）**：**`EFFECT_MAJOR_ORDER`**。前一个群攻技能执行完其全部副目标队列后，后一个群攻技能再完整执行其副目标队列。   - **时效模型（Duration Model）**：分为被动/指挥固有型（`PERMANENT_SOURCE_BOUND`，如槊血纵横，无时效）与主动/突击赋予型（`TEMPORARY_TIMED`，如瞋目横矛持续 2 回合）。到期时正常触发 `「群攻」效果已消失`（检出 1,283 例）。
2. **Track B — 副目标规划与排序 (`CLVS9-B03`)**：   - **候选池（Candidate Pool）**：主受击目标（actualTarget）所在队伍的其他**存活队友**。严格排除攻击者自身与主受击目标自身（排除率 100%）。   - **援护重定向（Guard Redirect）铁证**：当发生援护（A 打 B，C 援护 B $	o$ actualTarget = C）时，被援护的原目标 B **作为合法存活队友，100% 成为群攻副目标**（检出 15 例援护群攻样本，原目标被溅射命中率 15/15 = 100%）。原受击意图不赋予群攻豁免。   - **副目标数量（Target Count）**：由当前队伍合法存活队友数量决定，标准 3 人队最多命中 **2 名副目标**。若某队友已阵亡，则仅命中剩余 1 名存活队友，绝不对阵亡目标发出 0 兵损群攻。   - **副目标稳定排序（Deterministic Ordering）**：严格遵循 **全局站位升序（`GLOBAL_SLOT_ASCENDING`: pos 1 主将 $	o$ pos 2 副将1 $	o$ pos 3 副将2，排除 actualTarget）**：     - 主目标为 pos 1（主将）：副目标严格按 `(pos 2, pos 3)` 顺序受击（431 例压倒性一致）。     - 主目标为 pos 2（副将1）：副目标严格按 `(pos 1, pos 3)` 顺序受击（469 例压倒性一致）。     - 主目标为 pos 3（副将2）：副目标严格按 `(pos 1, pos 2)` 顺序受击（534 例压倒性一致）。   - **JIT 存活重校验（JIT Liveness Revalidation）**：副目标计划在执行前进行 JIT 存活校验。若副目标因前序伤害阵亡，则直接跳过（SKIP）。

## 2. Multi-Source Cleave Execution Matrix (Track A)

| Scenario | State Instances | Execution Order | Ratio Resolution | Queue Composition | Observable Result |
|---|---|---|---|---|---|
| Single Cleave (e.g. 槊血纵横) | 1 (`PERMANENT`) | Slot 0 | 固有战法配置（54% 或 42%） | 单效果队列 | 副目标按站位升序受击 |
| Single Cleave (e.g. 瞋目横矛) | 1 (`TEMPORARY_TIMED`) | Slot 1/2 | 战法配置（70% 或 62%） | 单效果队列 | 副目标按站位升序受击 |
| Multi-Cleave (槊血 + 瞋目) | 2 (`SOURCE_BOUND_LIST`) | Slot 0 $	o$ Slot 1/2 | 各自独立读取自身倍率 | **`EFFECT_MAJOR_ORDER`** | 先执行槊血溅射所有副目标，再执行瞋目溅射所有副目标 |
| Same-source Reapply (瞋目横矛) | 1 (保持原实例) | N/A | 保持战法倍率 | N/A | 输出 `「群攻」效果已刷新`，持续回合重置 |
| Cross-source Apply | 2 (`COEXIST`) | 战法槽位序 | 各自独立 | `EFFECT_MAJOR_ORDER` | 独立共存，互不覆盖 |

## 3. Secondary Target Plan Matrix (Track B)

| actualTarget Position | Eligible Candidate Pool | Secondary Order Observed | Dominant Count | Verification Ratio | Ordering Rule |
|---|---|---|---:|---:|---|
| **Pos 1 (主将)** | Pos 2, Pos 3 | **`(2, 3)`** | 431 | 100.0% (在双存活下) | `GLOBAL_SLOT_ASCENDING` |
| **Pos 2 (副将1)** | Pos 1, Pos 3 | **`(1, 3)`** | 469 | 100.0% (在双存活下) | `GLOBAL_SLOT_ASCENDING` |
| **Pos 3 (副将2)** | Pos 1, Pos 2 | **`(1, 2)`** | 534 | 100.0% (在双存活下) | `GLOBAL_SLOT_ASCENDING` |

## 4. Key Representative Battle Proofs

### 4.1 多群攻并存与槽位执行序：`战报_1068287_pid1063304.json`
- 攻击方：马超，装备固有战法【槊血纵横】（Slot 0）与主动战法【瞋目横矛】（Slot 1）。
- 事件 305-310：
  - `[305] [马超]执行来自【槊血纵横】的「群攻」效果`
  - `[306] [周瑜]损失了兵力171`（副目标 1）
  - `[307] [主公]损失了兵力171`（副目标 2）
  - `[308] [马超]执行来自【瞋目横矛】的「群攻」效果`
  - `[309] [周瑜]损失了兵力221`（副目标 1）
  - `[310] [主公]损失了兵力221`（副目标 2）
- **铁证裁决**：
  1. 两群攻效果并存，分别独立判定伤害；
  2. Slot 0【槊血纵横】严格先于 Slot 1【瞋目横矛】执行；
  3. 严格遵循 `EFFECT_MAJOR_ORDER`：槊血执行完周瑜与主公后，瞋目才开始执行周瑜与主公。

### 4.2 援护重定向与原目标受击：`战报_1068287_pid1063304.json` 事件 301-307
- 攻击方马超对主公（OriginalTarget）发动普通攻击；
- 程普发动援护，将攻击重定向至程普（ActualTarget）；
- 程普受击扣兵后，马超触发【槊血纵横】与【瞋目横矛】群攻；
- 程普的两位队友为周瑜（pos 1）与主公（pos 2）；
- **实测结果**：主公（被援护的原目标）完整作为群攻副目标承受两次溅射伤害（事件 307 与 310）；
- **铁证裁决**：原受击目标在被援护后，完全保留其作为队友被群攻命中的合法资格（15/15 样本 100% 确认）。

