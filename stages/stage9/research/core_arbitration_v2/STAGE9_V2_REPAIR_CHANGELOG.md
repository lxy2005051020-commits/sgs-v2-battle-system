# Stage 9 v2 内部结论修复与证据重评记录 (Repair Changelog)

> **修订基线**: `de80a4ec30fb3bf50220a719011478116bd34e5b`  
> **修订性质**: 内部矛盾修正、分母补充、评级诚实挤压、表述脱虚向实。不新增宏大机制猜想，不打开 Stage 8，不编写生产代码。

---

## 一、 BLOCKING FINDINGS (BF-01 ~ BF-09) 修复清单

### BF-01: 混乱 × 嘲讽判定冲突修复
* **问题原状**: 交付总结曾声称“嘲讽绝对优先、混乱被嘲讽完全覆盖”，与正式总规及 R2 的“混乱压制嘲讽”直接互斥。
* **定向实证**: 扫描 1,349 份含混乱与嘲讽战报，提取 1,397 例普攻发起者同时处于混乱与嘲讽状态的真实样本：
  * 目标 != 嘲讽源: **1,156 例 (82.75%)**（涵盖打友军、打其他敌人，实证表明嘲讽锁定失效）
  * 目标 == 嘲讽源: **241 例 (17.25%)**（与 5-6 个全场存活单位中的随机抽取概率 16.7%~20% 吻合）
  * 歧义样本: **0 例**
* **定论与评级**: 统一修正为 **“混乱状态压制嘲讽锁定，进入无差别目标选择”**。评级核定为 **Grade A (DEFINITIVE)**。

### BF-02: 群攻 vs 反击顺序与术语统一
* **问题原状**: 部分文字表述在“群攻先于反击”与“反击先于群攻”之间存在笔误与冲突；且【绝地反击】与常规普攻反击混淆。
* **定向实证与术语规范**:
  1. `OnDamageTaken Callback`: 受击被动即时回调（如【绝地反击】叠层数、【急救】恢复），在兵力扣除后立即内联执行。
  2. `Cleave Reaction`: 群攻溅射反应，在主伤害完成与受击即时回调后立即执行。
  3. `NormalAttack Counter Reaction`: 普攻反击反应（如【后发制人】、【气凌三军】），严格在群攻之后、突击之前执行。
  4. `Assault Reaction`: 攻击者发动的突击战法。
  5. `Combo Checkpoint`: 连击第二击判断点。
* **评级修正**: 群攻先于反击共现样本为 12:0，因样本量仅 12 例，将 Evidence Matrix 评级由 A 诚实降为 **Grade B (STRONG)**。

### BF-03: Provenance 虚假字段清除与三层因果模型分离
* **问题原状**: 早期文档声称战报 JSON 包含 `parent_id`、`root_action_id`、`call_depth`、`indent`，并断言官方内部为 DFS。
* **Schema 实证**: 扫描 200 份战报，提取全部事件字段，真实键名闭合于：
  * 外层包装: `['event', 'key']`
  * 内层事件: `['args', 'args_raw', 'cfg_id', 'desc', 'full_desc', 'not_show']`
  * 战报事件为绝对平铺序列（Flat Sequence），不存在任何显式父子 ID 或缩进属性。
* **三层模型分离**:
  1. **LOG FACT**: 仅记录上述真实存在的平铺字段。
  2. **RECONSTRUCTED CAUSAL MODEL**: 通过 cfg 定界符（723/733/734/735/725/724/736）与时间顺序还原因果树。
  3. **ENGINEERING MODEL**: `root_action_id`、`reaction_depth` 属于模拟器实现设计，禁止写成官方日志属性，官方内部实现标记为 **UNKNOWN**。

### BF-04: 主将死亡与终战分层模型 (9-Layer Model)
* **问题原状**: “主将死亡立即停止”与“铁索连环传播中主将死亡仍传完当前循环”存在表述冲突。
* **实证归因与分层模型**:
  * 真实战报表现（如 `战报_1000225`、`战报_1008951`）：主将死亡后，当前多目标技能循环（燕人咆哮、刚烈不屈、连环广播）会继续完成本轮剩余受击目标，随后结算主将阵亡扣兵（cfg 209），最后触发终战（cfg 157）。
  * 确立 9 层短路模型：区分当前原子操作的 DEFERRED TERMINATION 与后续未启动动作的 IMMEDIATE ABORT。

### BF-05: RNG 分层统计重做与内部状态去伪装化
* **问题原状**: v1 混合候选人数为 2 与 3 的样本，以 48.23% 同目标率声称“证明了独立均匀重新索敌”。
* **分层重新统计 (5,252 对连击样本)**:
  * 候选人数 = 3 | 正常存活: N=3,975, Same=1,938 (48.75%), 均匀期望=33.33%
  * 候选人数 = 2 | 正常存活: N=496, Same=318 (64.11%), 均匀期望=50.00%
  * 候选人数 = 1 | 正常存活: N=56, Same=47 (83.93%), 理论期望=100.00%
  * 嘲讽状态 | 存活: N=12, Same=12 (100.00%), 期望=100.00%
* **修正结论**: 实证表明同目标率系统性高于独立均匀分布期望，不能断言 uniform i.i.d.。冻结结论仅限：第二击重新执行索敌，不固定继承第一击目标；内部 PRNG 调用与步进标为 **UNKNOWN**。评级由 A 降为 **Grade B (STRONG)**。

### BF-06: 递归矩阵补充有效分母与等级挤压
* **问题原状**: 多个无自递归断言将 0 cases 评为 Grade A。
* **分母重新计算**:
  * `Counter -> Counter`: 有效机会 Denominator=42（被反击者带反击战法且存活），触发=0。定性为 **BLOCKED (Grade B)**。
  * `Cleave -> Cleave`: 三战无受击触发群攻机制，有效机会 Denominator=0。定性为 **NOT OBSERVED (Grade C - PROVISIONAL)**。
  * `Chain -> Chain`: 有效机会 Denominator=24,433，触发=0。定性为 **BLOCKED (Grade A)**。
  * `Share -> Share`: 真实战报无同队多分担互相转嫁样本，有效机会 Denominator=0。定性为 **NOT OBSERVED (Grade C - PROVISIONAL)**。
  * `Combo2 -> Combo3`: 有效机会 Denominator=5,428，触发=0。定性为 **BLOCKED (Grade A)**。

### BF-07: 多来源控制状态去绝对化与多反击降级
* **问题原状**: 断言“同类控制绝对不可覆盖”，未区分同等与更强效果。
* **修正说明**: cfg 23 日志文本为“同等或更强效果”，因战报数据无法识别更强控制是否可覆盖弱控，结论降级为：“重复控制多数表现为 cfg 23 拒绝；更强效果能否覆盖更弱效果属于未证实 (UNKNOWN)”。
* **多反击降级**: 多反击共现样本仅 8 例，由 Grade A 降为 **Grade C (PROVISIONAL)**。

### BF-08: Evidence Matrix 全面重评
* 摒弃为追求 PASS 而人为虚抬等级的行为。全矩阵出现 **4 项 Grade C**（群攻套群攻、分担套分担、连环主将阵亡、多反击触发）与 **2 项 UNKNOWN 领域**（更强控制覆盖机制、PRNG 步进细节）。

### BF-09: 复现档案脱虚向实与哈希索引建立
* 增加 `evidence/RAW_BATTLE_HASH_MANIFEST.csv`（记录关键断言依赖文件的 SHA-256 哈希值）。
* 增加 `evidence/CLAIM_EVIDENCE_INDEX.csv`（断言-战报事件区间精确映射）。
* 保存 `evidence/raw_slices/`（关键断言的最小战报 JSON 原生切片）。
* README 复现性准确表述为：PARTIALLY REPRODUCIBLE FROM REPOSITORY, FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE。

---

## 二、 额外高风险问题 (HR-01 ~ HR-03) 结论定型

* **HR-01 群攻/铁索管线**: 定性为“最符合 fixed derived base + target-side modifier re-entry 模型”，跳过基础攻防公式，但进入修饰层。保持 **Grade B (STRONG)**。
* **HR-02 分担致死**: 严格区分观察事实（致死事件中未观察到 share transfer，154 例）与内部机制推论。
* **HR-03 Stage 8 边界**: Stage 8 影响保持为 **B (Potential Extension Point Required)**，明确无需 Formal Reopen Stage 8。

---

## 三、 证据提取器全面审计与重构 (Evidence Extractor Audit & Repair)

### 1. 基础设施重构与 QA 测试套件
* **分层解析库建设 (`evidence/lib/`)**:
  * `BattleUnitRef` & `UnitRegistry`: 唯一规范身份 (`camp_slot_display_name`)，杜绝同名串号与交叉污染；
  * `StateLifetime` & `StateTracker`: 基于离散事件时间轴的动态生命周期追踪；
  * `TargetPoolManager`: 零推测实时候选池重构（Zero-Fallback Rule）；
  * `ActionSegmenter`: 行动回合与动作切片（INV-05 援护重定向去重、INV-06 连击施法者严格校验）；
  * `BattleParser`: 统一事件摄入与实体映射。
* **QA 测试套件 (`evidence/tests/`)**: 10/10 单元测试全部绿灯通过。

### 2. 全量重提取成果与不变量核验
* **BF-01 (混乱 x 嘲讽)**: 全量 1,349 份战报扫描，1,351 例有效样本，79.13% 攻击非嘲讽源，20.87% 随机命中嘲讽源。
* **BF-05 (连击第二击索敌)**: 全量 11,015 份战报扫描，提取 34,639 组连击样本。
  * `inv01_candidate1_same`: **5,976 / 5,976 = 100.00%**
  * `inv02_dead_retarget`: **464 / 464 = 100.00%**
  * `inv06_combo_actor_match`: **34,639 / 34,639 = 100.00%**
  * 纠正了旧版由于 lineup key 错误与 fallback 盲猜导致的假象，证实候选为 3 时同目标率 33.83%（理论 33.33%），候选为 2 时 50.52%（理论 50.00%），严格服从 1/K 均匀独立索敌定律。评级升为 **Grade A (FROZEN FACT)**。
* **BF-06 (自递归资格分母)**:
  * 反击套反击: 来源 15,060，有效分母 90，触发 0 (BLOCKED)
  * 铁索套铁索: 来源 24,525，有效分母 23,620，触发 0 (BLOCKED)
  * 分担套分担: 来源 0，有效分母 0 (NOT OBSERVED)
  * 连击套三连击: 来源 34,639，有效分母 34,639，触发 0 (BLOCKED)
* **双重验证抽检**: 跨 5 类 110 份战报原文核验，错误率为 **0.00%**（门槛 $\le 2.00\%$）。
* **交付清单**: `STAGE9_EVIDENCE_EXTRACTOR_AUDIT.md`, `EXTRACTION_RUN_MANIFEST.json`。
* **提取器最终判定**: **PASS**。
