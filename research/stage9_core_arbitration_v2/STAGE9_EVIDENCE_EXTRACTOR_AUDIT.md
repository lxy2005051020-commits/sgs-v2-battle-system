# Stage 9 核心机制实证提取器全面审计与修复报告
# (Stage 9 Evidence Extractor Audit & Repair Report)

> **审计基线 Commit**: `50a2bca26a359dfd9b8f19d0208a505ed9a2ae6b`  
> **审计范围**: `research/stage9_core_arbitration_v2/evidence/` 目录下全部数据提取脚本、中间统计结果、分母计算逻辑与抽检机制  
> **最高准则**: **在证据提取器被证明可靠之前，任何实证结论均不可信。严禁使用有缺陷的提取器产出作为机制定论。**  
> **最终审计判定 (Final Extractor Verdict)**: **PASS**

---

## 一、 执行摘要 (Executive Summary)

在 Stage 9 核心机制第二轮研究（v2）及一致性修复阶段，独立审计指出：虽然研究团队指出了大量关键战报规律，但支撑部分核心结论（如 BF-01 混乱压制嘲讽、BF-05 连击独立索敌与均匀分布、BF-06 递归阻断分母）的底层 Python 提取脚本存在严重的基础统计工程缺陷。

具体缺陷包括：
1. **武将身份冲突 (Unit Identity Collisions)**：旧脚本依赖裸武将名（`display_name`）进行全局集合或字典映射，在镜像阵容、城卫兵（同一阵营存在多个“强城卫/勇城卫”）、主公同名战报中引发灾难性串号与交叉污染；
2. **状态生命周期静态匹配 (Static State Matching)**：使用全局集合 `counter_units = set()` 或关键词静态匹配，无法感知状态施加时点、刷新、正常过期（cfg 22）及死亡清理（cfg 163）；
3. **候选池推断静默回退与事件时间轴缺失 (Candidate Pool Fallback & Missing Event Time)**：在阵容键名错误时静默回退到 `3 - len(...)` 纯猜测；且初版重构时未记录死亡事件时点，导致后期阵亡武将在前期回合被误判为死亡；
4. **动作切片重复计数 (Action Segmentation Duplication)**：援护发生时日志包含 `cfg 143` 后紧跟 `cfg 9` 重定向普通攻击，旧脚本将第二个 `cfg 9` 计为一次全新普攻，导致普攻次数虚增与连击配对错位；
5. **递归分母不纯 (Impure Recursion Denominator)**：旧脚本分母混淆了“所有同名战法触发事件”与“受害武将当下拥有反击/分担/连环状态且存活”的严格事件时点资格分母；
6. **样本覆盖人为切片 (Artificial Slicing)**：旧脚本普遍存在 `[:1500]` 人为切片，未全量覆盖候选池。

本轮任务彻底重构并落地了规范的基础设施解析库 `evidence/lib/` 与自动化 QA 测试套件 `evidence/tests/`（10/10 单测全绿通过），消除了全部 fallback 猜测，并在全量战报库上重新执行了 BF-01、BF-05、BF-06 的定向重提取，开展了覆盖 5 大类别共 110 例的原文双重抽检（**错误率 0.00%，远低于 2.00% 门槛**）。三大形式化不变量（INV-01, INV-02, INV-06）达成 **100.00%** 通过率。

---

## 二、 提取器架构全景演进 (Legacy vs Repaired Architecture)

| 架构维度 | 旧版提取器 (v2-legacy scripts) | 修复后提取器 (v2-repaired library) | 改进收益 |
| :--- | :--- | :--- | :--- |
| **代码组织** | 单文件 ad-hoc 脚本，逻辑高度冗余且分散 | 模块化分层解析器库 `evidence/lib/` | 单一真理来源，高复用可维护 |
| **测试保障** | 无自动化单元测试，仅靠目测输出 | 独立 QA 测试套件 `evidence/tests/` (10 tests) | 严格回归保障，杜绝静默退化 |
| **武将身份** | 字符串 `m.group(1)` 裸名字匹配 | `BattleUnitRef` (`camp_slot_display_name`) | 根除同名串号，强制阵营隔离 |
| **状态追踪** | 全局 set/dict 静态累加，无时间维度 | `StateLifetime` 严格事件时点区间判定 | 精确感知施加/刷新/过期/阵亡清理 |
| **候选池重构** | 错误键名时回退到 `3 - len(...)` 盲猜 | `TargetPoolManager` 基于存活单位与事件时点实时解析 | 严禁 fallback 猜测，未知显式归入 `UNKNOWN` |
| **动作切片** | 简单正则扫描 `cfg 9`，援护重复计数 | `ActionSegmenter` 识别 `cfg 143 + cfg 9` 重定向去重 | 普攻生命周期定界严格准确 |
| **连击配对** | 顺序临近配对，未校验前后施法者一致 | `ComboPair` 严格强制 INV-06 (`hit1.actor == hit2.actor`) | 杜绝回合内不同武将动作串联 |
| **递归分母** | 粗暴统计战法触发总数，缺少事件资格检验 | 严格核验事件时点 i 受害者存活性与对应状态激活性 | 产出绝对纯净的真正有效机会分母 |
| **样本覆盖** | 人为添加 `[:1500]` 截断切片 | 全量候选扫描（BF-01: 1349; BF-05: 11015; BF-06: 18899） | 根除选择性样本偏差 |

---

## 三、 武将身份解析审计 (Unit Identity Resolution: CANONICAL_ID vs DISPLAY_NAME)

### 1. 缺陷根因
旧脚本直接提取日志中的 `[武将名]`。但在三战战报中：
- 镜像阵容双方可出战完全相同的武将（如红方刘备 vs 蓝方刘备）；
- 守军阵容中存在同一阵营多个相同名称的城卫（如 `enemy` 阵营同时存在 3 个 `强城卫`）；
- 双方主将可能具有通用代称（如 `主公`）。
使用裸字符串字典会导致红方状态被蓝方消耗，或前排城卫阵亡后误将后排城卫标记死亡。

### 2. 修复方案
在 `evidence/lib/unit_identity.py` 中构建 `BattleUnitRef`：
```python
@dataclass(frozen=True)
class BattleUnitRef:
    battle_file: str
    camp: str             # 'my' or 'enemy'
    slot: int             # 0, 1, 2
    position: int         # 1, 2, 3
    display_name: str     # e.g. '刘备'
    hero_type: int | None = None
    max_troops: int = 0

    @property
    def canonical_id(self) -> str:
        return f"{self.camp}_{self.slot}_{self.display_name}"
```
解析日志时，提取器结合 HTML Token 颜色（`#75b3ed` -> `my`, `#ec616b` -> `enemy`）和图标标签（`tag_knight_my.png`, `tag_lancer_enemy.png`）锁定阵营。
对于同阵营存在重名且无法区分 slot 的情况（如 3 个强城卫）：
- `resolve_from_event_text` 明确返回 `is_unambiguous = False`；
- 严禁随意分配到 slot 0；
- 解析器标记其为 `AMBIGUOUS` 并从精密索敌统计中安全剔除。

### 3. 形式化不变量
- **INV-03 (Camp Disjointness)**: 我方武将集合与敌方武将集合交集恒为空。单元测试 `test_inv03_camp_disjoint` 100% 通过。

---

## 四、 状态生命周期审计 (State Lifetime Tracking)

### 1. 缺陷根因
旧脚本以全局布尔值或静态集合追踪状态，无法处理：
- 状态在第 1 回合施加、第 2 回合自然过期（cfg 22）、第 4 回合受击时状态早已不复存在；
- 武将在第 3 回合阵亡（cfg 163），但名下状态未被清理，导致后续判定仍认为其持有状态；
- 嘲讽源武将阵亡，被嘲讽者的嘲讽锁定应当即刻解除。

### 2. 修复方案
在 `evidence/lib/state_tracker.py` 中引入 `StateLifetime`：
- 精确记录 `apply_event_idx`、`expire_event_idx`、`refresh_event_indices`；
- 在任何事件序号 i 处，状态生效条件为：`apply_event_idx <= i < expire_event_idx`；
- 联动死亡事件：当武将阵亡时，立即关闭其名下所有生效状态，并立即关闭以其为 `source` 的嘲讽与援护状态。

### 3. 形式化不变量
- **INV-04 (Active State Expiration)**: 状态过期或宿主死亡后，在后续事件时点查询恒为 `False`。单元测试 `test_inv04_active_state_end` 与 `test_death_cleanup_state` 100% 通过。

---

## 五、 候选池重构审计与零推测法则 (Zero-Fallback Rule)

### 1. 缺陷根因
旧版 `research_bf05_stratify.py` 检索阵容时使用了错误的键名 `lineup.get('attack')` 与 `lineup.get('defend')`。由于 100% 的战报实际键名为 `lineup['my']` 与 `lineup['enemy']`，查询结果恒为空集，脚本静默触发了 `3 - len(...)` 纯盲猜兜底逻辑。这直接导致了旧版数据中所谓“候选人数=1 时同目标率仅 83.93%”的假象（因为敌方明明有 3 人存活，却被盲猜为 1 人）。
此外，重构初版若只维护静态死亡集合，未记录死亡事件时点，会导致在第 8 回合阵亡的武将在第 1 回合就被判定死亡。

### 2. 修复方案
- 彻底废除任何 fallback 盲猜逻辑（Zero-Fallback Rule）；
- 修正阵容键名为 `my` 与 `enemy`；
- `TargetPoolManager` 追踪离散死亡事件时点 `_death_events[canonical_id] = event_idx`；
- 在事件时点 i，武将存活条件为：`canonical_id not in _death_events or i < _death_events[canonical_id]`；
- 若因重名无法唯一确定目标池，显式标记 `is_known = False, unknown_reason = 'DUPLICATE_CAMP_UNIT_NAMES'`，并归入排除分母。

### 3. 形式化不变量
- **INV-01 (Single Candidate Certainty)**: 当候选目标池人数为 1 且目标存活、无池变化时，普攻与连击命中目标 **必须 100% 为该唯一候选**。
  - 修复前（旧脚本盲猜）：83.93%（严重违反逻辑常理）；
  - 修复后（全量 11,015 份战报）：**5,976 / 5,976 = 100.00%**（绝对符合物理规律）。
- **INV-02 (Dead Target Retarget)**: 第一击目标阵亡后，第二击目标不得为已阵亡单位。
  - 修复后：**464 / 464 = 100.00%**。

---

## 六、 动作切片与援护去重审计 (Action Segmentation & Guard Deduplication)

### 1. 缺陷根因
战报在发生援护时，日志物理顺序为：
```text
cfg 9: [A]对[B]发动普通攻击
cfg 143: [C]执行来自【援护】的「援护」效果
cfg 9: [A]对[C]发动普通攻击
```
旧脚本通过简单扫描 `cfg 9` 识别普攻，导致单次普攻被重复计算为两次独立普攻，进而严重破坏了连击第二击的配对关系与时序。

### 2. 修复方案
在 `evidence/lib/action_segmenter.py` 中建立 **INV-05 援护去重规则**：
- 当识别到 `cfg 9` 时，检查前序事件是否为 `cfg 143` 或援护描述；
- 若是，判定为重定向衍生，只将前序攻击的 `resolved_target` 更新为援护者，**严禁追加新的独立普攻动作**。
- 单元测试 `test_inv05_guard_cfg9_dedup` 100% 通过。

---

## 七、 递归事件时点资格分母审计 (Recursion Event-Time Eligible Denominator)

### 1. 缺陷根因
在研究自递归与无限连锁（Q5/EM-11~EM-14）时，旧脚本仅粗暴统计了所有造成反击/连环/分担伤害的事件总数，未检验受害者是否具有反击状态、是否存活，导致得出的所谓“有效机会”并不纯净。

### 2. 修复方案
在 `evidence/run_bf06_reextraction.py` 中建立事件时点资格筛查：
- **反击套反击 (Counter -> Counter)**：
  1. 单位 A 普攻单位 B，B 触发反击对 A 造成兵刃伤害；
  2. 严格核验：A 受到反击后是否依然存活（排除当场暴毙）；
  3. 严格核验：A 在该事件时点 i 是否持有激活性反击状态（如后发制人、气凌三军）；
  4. 满足上述全部条件，方计入 **有效机会分母 (Eligible Opportunity)**；
  5. 检查随后 4 个事件内 A 是否对 B 触发了反击伤害。
- **连环套连环 (Chain -> Chain)**：
  1. 单位 B 承受铁索连环反馈伤害；
  2. 严格核验：B 承伤后依然存活且处于激活的连环状态，且己方阵营存在 >= 1 名其他存活且处于连环状态的友军；
  3. 检查 B 是否作为发起者触发了新的连环广播。
- **分担套分担 (Share -> Share)**：
  1. 单位 B 作为分担者承受分担伤害；
  2. 严格核验：B 是否被第三方友军的第二个分担状态所覆盖；
  3. 检查该伤害是否转嫁给第三方。

---

## 八、 自动化 QA 测试套件审计结果 (QA Test Suite Results)

提取器配备了 10 项针对核心抽象与边界条件的单元测试，位于 `evidence/tests/`：

```text
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\sgs-v2-battle-system, configfile: pyproject.toml
collected 10 items

test_action_segmentation.py::test_action_segmentation_turns PASSED       [ 10%]
test_candidate_pool.py::test_candidate_pool_resolution PASSED           [ 20%]
test_combo_pairing.py::test_combo_pairing_and_invariants PASSED         [ 30%]
test_guard_cfg9_dedup.py::test_inv05_guard_cfg9_dedup PASSED            [ 40%]
test_recursion_eligibility.py::test_counter_to_counter_eligibility PASSED[ 50%]
test_state_lifetime.py::test_inv04_active_state_end PASSED               [ 60%]
test_state_lifetime.py::test_death_cleanup_state PASSED                  [ 70%]
test_unit_identity.py::test_unit_ref_properties PASSED                   [ 80%]
test_unit_identity.py::test_inv03_camp_disjoint PASSED                   [ 90%]
test_unit_identity.py::test_resolve_from_event_color PASSED              [100%]

============================= 10 passed in 0.16s ==============================
```

---

## 九、 核心机制重提取定量对比 (Re-extracted Quantitative Evidence)

### 1. BF-01: 混乱 x 嘲讽共现决策 (Confusion vs Taunt)
- **候选战报总数**: 1,349 份
- **处理战报数**: 1,349 份（100% 全量覆盖，无截断）
- **提取有效样本数**: 1,351 例
- **排除原因统计**: `taunt_source_unknown`: 2 例, `ambiguous`: 0 例
- **数据分布对比**:
  - **命中非嘲讽源目标 (含攻击友军)**: **1,069 例 (79.13%)**（95% CI: [76.90%, 81.21%]）
  - **命中嘲讽源目标**: **282 例 (20.87%)**（95% CI: [18.79%, 23.10%]）
  - 旧版数据修正说明：旧报告中记录为 1,397 例 / 82.75%，系旧版模糊正则匹配计数；经 `BattleParser` 严格规范化武将身份及时间轴过滤后，有效样本定格为 **1,351 例 / 79.13%**。
  - 核心机制结论保持绝对坚固：在 5 目标战场上，均匀随机选中嘲讽源的理论概率为 20.00%，实测 20.87% 落在 95% 置信区间内，彻底确证 **混乱完全压制嘲讽的目标锁定**。

---

### 2. BF-05: 连击第二击索敌多维正交分层 (Combo Retarget Stratification)
- **候选战报总数**: 11,015 份
- **处理战报数**: 11,015 份（100% 全量覆盖，无截断）
- **提取连击对总数**: 34,639 组
- **形式化不变量校验**:
  - `inv01_candidate1_same`: **5,976 / 5,976 = 100.00%**（PASS）
  - `inv02_dead_retarget`: **464 / 464 = 100.00%**（PASS）
  - `inv06_combo_actor_match`: **34,639 / 34,639 = 100.00%**（PASS）

#### 全量多维正交分层统计总表 (Full Stratified Matrix)
| 候选数 (Cand) | 状态条件 (Condition) | 目标1状态 (Target1) | 目标池状态 (Pool) | 样本量 (N) | 同目标 (Same) | 异目标 (Diff) | 同目标率 P(same) | 95% Wilson CI | 理论期望说明 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **NORMAL** | **SURVIVED** | **POOL_STABLE** | **5,976** | **5,976** | **0** | **100.00%** | **[99.94%, 100.00%]** | 唯一合法目标，必然锁定 |
| **2** | **NORMAL** | **SURVIVED** | **POOL_STABLE** | **3,074** | **1,553** | **1,521** | **50.52%** | **[48.75%, 52.29%]** | 理论期望 1/2 = 50.00%，完美重合 |
| **3** | **NORMAL** | **SURVIVED** | **POOL_STABLE** | **21,428** | **7,250** | **14,178** | **33.83%** | **[33.20%, 34.47%]** | 理论期望 1/3 = 33.33%，完美重合 |
| **5** | **CONFUSION** | **SURVIVED** | **POOL_STABLE** | **1,536** | **336** | **1,200** | **21.88%** | **[19.88%, 24.01%]** | 理论期望 1/5 = 20.00%，完美重合 |
| **1** | **TAUNT** | **SURVIVED** | **POOL_STABLE** | **1,701** | **1,698** | **3** | **99.82%** | **[99.48%, 99.94%]** | 嘲讽强制锁定嘲讽源 |
| **1** | **NORMAL** | **DIED** | **POOL_CHANGED** | **207** | **0** | **207** | **0.00%** | **[0.00%, 1.82%]** | 目标阵亡，100% 转移目标 |
| **2** | **NORMAL** | **DIED** | **POOL_CHANGED** | **249** | **0** | **249** | **0.00%** | **[0.00%, 1.52%]** | 目标阵亡，100% 转移目标 |

> **重大机制发现**: 修复提取器缺陷后，常规普攻 3 目标同目标率由旧版虚假的 48.75% 纠正为 **33.83%**，2 目标同目标率为 **50.52%**，5 目标混乱同目标率为 **21.88%**。这无可辩驳地证明了：**普通攻击第二击并非继承第一击目标，而是严格独立、在合法候选池中按均匀分布 1/K 重新随机索敌！**

---

### 3. BF-06: 递归有效机会分母与触发统计 (Recursion Denominators)
全量扫描 4,233 份反击战报、1,522 份连环战报、2,129 份分担战报、11,015 份连击战报：

| 机制类型 (Recursion Type) | 来源伤害事件 (Source Events) | 事件时点有效资格分母 (Eligible Denominator) | 递归触发次数 (Triggered) | 排除原因统计 (Excluded Breakdown) | 判定状态 (Status) |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **反击套反击 (Counter -> Counter)** | 15,060 | **90** | **0** | `VICTIM_NO_COUNTER_STATE`: 14,634<br>`VICTIM_DIED`: 336 | **BLOCKED** |
| **铁索套铁索 (Chain -> Chain)** | 24,525 | **23,620** | **0** | `NO_OTHER_CHAINED_ALLIES`: 704<br>`VICTIM_NOT_CHAINED`: 201 | **BLOCKED** |
| **分担套分担 (Share -> Share)** | 0 | **0** | **0** | 三战无嵌套分担战法配置 | **NOT OBSERVED** |
| **连击第二击套第三击 (Combo2 -> Hit3)** | 34,639 | **34,639** | **0** | 无三连击观察样本 | **BLOCKED** |

---

## 十、 双重验证抽检报告 (Dual-Verification Spot Check Report)

为核验提取器与真实战报原文的一致性，使用 `evidence/run_spot_check.py` 开展了跨 5 大维度的原文事件逐级比对：
- **抽检类别覆盖**:
  - `cand_1`: 20 例
  - `cand_2`: 20 例
  - `cand_3`: 20 例
  - `confusion`: 20 例
  - `taunt`: 30 例
- **核验要素**:
  1. 动作发起者名称与规范 ID 严格对应；
  2. 第一击、第二击目标在原文 `cfg 9` 日志中真实存在；
  3. 候选池状态与战报上下文存活情况完全吻合；
  4. 嘲讽/混乱状态施加与生效日志完全证实。
- **抽检结果**:
  - **总抽检例数**: **110 例**
  - **不匹配例数 (Mismatches)**: **0 例**
  - **抽检错误率**: **0.00%**（门槛要求 <= 2.00%，完美通过）
  - 详细抽检清单保存于 `evidence/r10_combo_spot_check_report.json`。

---

## 十一、 作废数据集登记册 (Evidence Invalidation Register)

| 数据集 / 脚本 | 原存放路径 | 作废原因 | 替代文件 |
| :--- | :--- | :--- | :--- |
| 旧版连击分层数据集 | `evidence/r10_combo_detailed_stratified.json` (Commit `de80a4`) | 存在 `lineup['attack']` 键名错误，大量样本静默触发 `3 - len(...)` 盲猜兜底，数据失真 | 全新重提取同名 JSON (Commit 当前) |
| 旧版分层提取脚本 | `evidence/research_bf05_stratify.py` | 缺少武将身份解析，未追踪死亡事件时点，含 `[:1500]` 人为截断 | `evidence/run_bf05_reextraction.py` |
| 旧版连环/反击分母脚本 | `evidence/research_bf06_recursion_denominator.py` | 未基于 `StateLifetime` 判定事件时点资格，含 `[:1500]` 人为截断 | `evidence/run_bf06_reextraction.py` |
| 旧版混乱嘲讽脚本 | `evidence/research_bf01_confusion_taunt.py` | 字符串裸正则匹配，未做同阵营重名排查 | `evidence/run_bf01_reextraction.py` |

---

## 十二、 提取器最终评定 (Final Extractor Verdict)

### **评定结果: PASS**

**核准依据**:
1. **基础设施健全**: 完成了 `unit_identity`, `state_tracker`, `target_pool`, `action_segmenter`, `battle_parser` 五大核心基础设施模块建设；
2. **QA 质量达标**: 10/10 单元测试全绿通过；
3. **形式化不变量 100% 达成**:
   - INV-01 (单一候选同目标率): **100.00%** (5,976/5,976)
   - INV-02 (阵亡目标重定向率): **100.00%** (464/464)
   - INV-06 (连击施法者自洽性): **100.00%** (34,639/34,639)
4. **人工/代码双重抽检合格**: 110 份战报原文比对，错误率为 **0.00%**（<= 2.00%）；
5. **全量覆盖无截断**: BF-01 (1,349 files), BF-05 (11,015 files), BF-06 (18,899 parses) 均已执行全量检索；
6. **科学结论坚实**: 纠正了旧版统计偏差，实证确立了连击均匀随机独立索敌定律与自递归阻断定律。
