# Stage 9 v2 证据档案清单与复现指南 (MANIFEST - Repaired)

> **可复现性声明**: **PARTIALLY REPRODUCIBLE FROM REPOSITORY; FULL REPRODUCTION REQUIRES ORIGINAL BATTLE DATABASE**  
> 仓库内包含全部提取脚本、中间统计 JSON、索引文件、哈希清单、断言索引及关键断言原生切片。在拥有本地原始战报库时可 100% 完整重跑；在无原始库时可通过原生切片直接核验证据链。

---

## 一、 证据数据清单 (Evidence Datasets)

| 文件名 | 大小/格式 | 说明与用途 | 对应核心断言 |
| :--- | :--- | :--- | :--- |
| **`RAW_BATTLE_HASH_MANIFEST.csv`** | CSV | 关键断言所依赖原始战报文件的 SHA-256 哈希值与字节大小清单 | 全量可信性基准 |
| **`CLAIM_EVIDENCE_INDEX.csv`** | CSV | 核心机制断言与战报文件名、事件起止序号的精确映射索引 | 全量证据溯源 |
| **`raw_slices/*.json`** | JSON 集合 | 关键断言的最小原生战报事件切片包（无需原始数据库即可核验） | EM-01, EM-03, EM-08, EM-11, EM-19, EM-21, EM-22 |
| **`r11_confusion_taunt_data.json`** | JSON | 1,351 例混乱 × 嘲讽共现有效样本完整提取集 | EM-01 (BF-01) |
| **`r10_combo_detailed_stratified.json`**| JSON | 34,639 组连击全量多维正交分层索敌统计集 | EM-25 (BF-05) |
| **`r7_recursion_denominators.json`** | JSON | 反击(90)/连环(23620)/分担(0)/连击(34639)事件时点有效机会分母与触发统计 | EM-11 ~ EM-14 (BF-06) |
| **`r10_combo_spot_check_report.json`** | JSON | 110 例跨 5 类战报原文与提取器双重抽检对比报告（错误率 0.00%） | QA 抽检核验 |
| **`r1_lifecycle_data.json`** | JSON | 普通攻击生命周期各反应对共现统计 | EM-08 (BF-02) |
| **`r1_edge_cases.json`** | JSON | 零伤害、抵御、反击致死攻击者切片集 (281 例) | EM-10, EM-20 |
| **`r2_self_rescue_data.json`** | JSON | 25 例“攻击者==援护者”自攻自受样本 | EM-03 |
| **`r3_cleave_damage_data.json`** | JSON | 2,258 组双副目标群攻伤害对比集 | EM-17 (HR-01) |
| **`r4_chain_damage_data.json`** | JSON | 11,104 组多副目标铁索连环伤害对比集 | EM-18 (HR-01) |
| **`r6_fendan_math_data.json`** | JSON | 11,381 组分担减免与承受数学守恒验证集 | EM-15 |
| **`r6_death_near_fendan.json`** | JSON | 154 组主目标致死阻断分担样本集 | EM-19 (HR-02) |
| **`r9_status_conflict_data.json`** | JSON | cfg 23 (1550例) 与 cfg 25 (7875例) 状态冲突集 | EM-23 (BF-07) |
| **`stage9_index.json`** | JSON (2.26MB) | 32,660 份战报的核心机制关键词与特征标签索引 | 全库检索入口 |

---

## 二、 自动化提取与验证基础设施 (Infrastructure & Scripts)

| 模块 / 脚本名 | 核心功能 | 运行方式 |
| :--- | :--- | :--- |
| **`lib/unit_identity.py`** | `BattleUnitRef` 规范 ID 与 `UnitRegistry` 阵营/重名解析 | 内部模块 |
| **`lib/state_tracker.py`** | `StateLifetime` 离散事件时间轴动态生命周期追踪 | 内部模块 |
| **`lib/target_pool.py`** | `TargetPoolManager` 零推测实时候选池重构 | 内部模块 |
| **`lib/action_segmenter.py`** | `ActionSegmenter` 动作切片与 INV-05 援护重定向去重 | 内部模块 |
| **`lib/battle_parser.py`** | `BattleParser` 统一事件摄入与实体映射 | 内部模块 |
| **`tests/`** | 10 项核心抽象与形式化不变量单元测试套件 | `pytest stages/stage9/research/core_arbitration_v2/evidence/tests/` |
| **`run_bf01_reextraction.py`** | BF-01 混乱 × 嘲讽全量 1,349 份战报重提取 | `python evidence/run_bf01_reextraction.py` |
| **`run_bf05_reextraction.py`** | BF-05 连击多维正交分层全量 11,015 份战报重提取 | `python evidence/run_bf05_reextraction.py` |
| **`run_bf06_reextraction.py`** | BF-06 递归资格分母全量候选战报重提取 | `python evidence/run_bf06_reextraction.py` |
| **`run_spot_check.py`** | 跨 5 类 110 份战报原文与提取器双重抽检 | `python evidence/run_spot_check.py` |
| **`inspect_bf03_schema.py`** | 验证战报原生 JSON 物理 Schema | `python evidence/inspect_bf03_schema.py` |
| **`generate_evidence_index.py`** | 生成哈希清单、断言索引与原生切片 | `python evidence/generate_evidence_index.py` |

---

## 三、 本地复现指南 (Reproduction Guide)

### 模式 A: 基于原生切片与单测的快速轻量核验 (无需原始数据库)
1. 运行自动化测试套件：
   ```bash
   pytest stages/stage9/research/core_arbitration_v2/evidence/tests/ -v
   ```
2. 直接读取 `evidence/raw_slices/` 下的 JSON 文件。每个切片均为原生战报的原始子事件数组，可直接核查：
   - `raw_slices/EM-01_*`: 混乱武将被嘲讽后攻击非嘲讽源的原始日志；
   - `raw_slices/EM-03_*`: 张飞混乱打张飞自身的原始日志；
   - `raw_slices/EM-08_*`: 绝地反击作为受击被动回调在突击伤害后执行的原始日志；
   - `raw_slices/EM-19_*`: 主目标致死后未发生分担转嫁的原始日志；
   - `raw_slices/EM-21_*`: 燕人咆哮多目标循环中主将阵亡仍完成目标 2 的原始日志。

### 模式 B: 基于原始数据库的全量重新统计与抽检
需本地挂载 `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`，直接在工作目录下运行：
```bash
python stages/stage9/research/core_arbitration_v2/evidence/run_bf01_reextraction.py
python stages/stage9/research/core_arbitration_v2/evidence/run_bf05_reextraction.py
python stages/stage9/research/core_arbitration_v2/evidence/run_bf06_reextraction.py
python stages/stage9/research/core_arbitration_v2/evidence/run_spot_check.py
```
全部脚本均采用多层异常捕获与确定性统计逻辑，输出结果与本报告保存的 JSON 数据集完全一致。
