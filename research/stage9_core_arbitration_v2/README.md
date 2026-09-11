# Stage 9 核心底层机制第二轮定向实证研究规范 (v2)

本目录为三国志战略版战斗模拟系统（V2）Stage 9（核心底层机制裁决）的**第二轮定向实证研究档案库**。

针对第一轮探索性研究（v1）的独立审计反馈，本轮研究摒弃了一切主观臆断与“经验直觉”，全面实施：
1. **反例优先与控制变量实证**：逐一审查 v1 报告中的反例与异常案例，修正了“突击先于反击”的假象（实际为绝地反击被动叠加回调，后发/气凌普攻反击 100% 先于突击）。
2. **边缘场景全量穷举**：发现并实证了“混乱导致打友军时的自援护（攻击者同时为援护者，自打自）”现象（25 例）；精确定量连击首击援护对次击目标的影响；实证了致死过量伤害直接短路分担结算等。
3. **管线派生模型重构**：全面排查 2,258 例群攻与 11,104 例铁索连环，证明群攻与反馈以主目标承受/基数伤害按比例派生，子目标跳过 BaseDamagePipeline，但严格进入命中/规避/抵御与伤害修饰层。
4. **可复现证据档案**：所有统计结论均附带全自动提取脚本、结构化 JSON 证据集及真实战报索引（覆盖 32,660 份真实战报）。

---

## 目录结构导航

### 1. 核心规范与汇总报告
- [`STAGE9_CORE_ARBITRATION_RULES_V2.md`](STAGE9_CORE_ARBITRATION_RULES_V2.md): **Stage 9 核心底层裁决规范主文件**（包含目标决议、普攻生命周期、反应队列、派生管线、递归防线、死亡短路、多源仲裁等 9 大模块规范）。
- [`STAGE9_EVIDENCE_MATRIX_V2.md`](STAGE9_EVIDENCE_MATRIX_V2.md): **证据等级评级矩阵**（覆盖 26 项核心断言，19 项 A 级，7 项 B 级，0 项 C/D/E 级，达标率 100%）。
- [`STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md`](STAGE9_RESEARCH_CHANGELOG_V1_TO_V2.md): **v1 到 v2 版本演进与变更记录**。

### 2. 八大专题深入实证报告
- [`R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md`](R1_ATTACK_LIFECYCLE_AND_REACTION_ORDER.md): 普攻生命周期、反应队列结算顺序与反例溯源分析。
- [`R2_TARGET_REDIRECT_AND_GUARD.md`](R2_TARGET_REDIRECT_AND_GUARD.md): 目标重定向、援护判定、自援护发现与连击次击索敌机制。
- [`R3_DAMAGE_DERIVATION_PIPELINE.md`](R3_DAMAGE_DERIVATION_PIPELINE.md): 群攻、铁索连环、分担（转嫁）与分摊（平分）的派生计算与管线重入规则。
- [`R4_RECURSION_PERMISSION_MATRIX.md`](R4_RECURSION_PERMISSION_MATRIX.md): 19 组跨反应类型递归许可矩阵与闭环防线。
- [`R5_DEATH_TERMINATION_MATRIX.md`](R5_DEATH_TERMINATION_MATRIX.md): 死亡事件对正在执行中动作、后续反应队列及连锁传递的短路规则。
- [`R6_MULTI_SOURCE_RULES.md`](R6_MULTI_SOURCE_RULES.md): 多来源同类状态（同队/异队、控制/增益）的冲突、刷新与覆盖裁决。
- [`R7_RNG_AND_DETERMINISM.md`](R7_RNG_AND_DETERMINISM.md): 随机数消耗序列、确定性索敌分流与可复现性规范。
- [`R8_PROVENANCE_MODEL.md`](R8_PROVENANCE_MODEL.md): 事件因果链、根源动作树与战报日志层级溯源模型。

### 3. 可复现性证据包
- [`evidence/MANIFEST.md`](evidence/MANIFEST.md): 证据包清单与复现指南。
- `evidence/*.py`: 全自动战报数据挖掘、比对与验证脚本（共 18 个独立脚本）。
- `evidence/*.json`: 从 32,660 份战报中提取的清洗后结构化证据数据集。
