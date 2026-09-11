# Stage 9 第二轮实证研究证据清单 (Evidence Manifest)

## 1. 检索环境与基础数据

- **代码基线**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)
- **战报数据库**: `D:\战报数据库\三战战报汇总_全盘扫描\完整战报JSON`
- **总战报数量**: 32,660 份（去重后完整战报，全量原始事件流逾 1,400 万条）
- **标签索引文件**: `research/stage9_core_arbitration_v2/evidence/stage9_index.json` (2.26 MB, 32,660 份战报标签)

---

## 2. 核心证据数据文件与查询脚本索引

| 证据数据文件 | 关联脚本 | 样本覆盖与核心统计 | 对应研究模块 |
| :--- | :--- | :--- | :--- |
| `r1_lifecycle_data.json` | `research_r1_lifecycle.py` | 5,208 份候选战报；成对共现统计：Assault vs Combo (162:0), Damage vs FirstAid (4654:0), Cleave vs Assault (74:0), Cleave vs Counter (12:0), Counter vs Combo (54:0), Counter vs Assault (96:3, 3 例反例经核实为绝地反击而非通常普攻反击)；3 反应共存案例 4 例。 | R1 普攻生命周期与反应顺序 |
| `r1_edge_cases.json` | `research_r1_zero_and_death.py` | 18,411 份候选；零伤害触发群攻 33 例、反击 45 例、突击 120 例；抵御触发群攻 9 例、反击 21 例、突击 49 例；反击致死攻击者 113 例（突击与第二击全部短路取消）。 | R1/R5 边界条件与死亡短路 |
| `r2_self_rescue_data.json` | `research_r2_self_rescue.py` | 707 份援护战报；检出 25 例攻击者与援护者为同一人的“自我普攻”案例（混乱打队友，队友由攻击者援护，最终打自己）。 | R2 援护合法性与目标重定向 |
| `r2_combo_rescue_data.json` | `research_r2_combo_rescue.py` | 255 份连击+援护战报；检出 36 例组合：第 1 击与第 2 击均被援护 13 例、仅第 1 击被援护 7 例、仅第 2 击被援护 16 例。证明援护在每次普攻发起时独立判定。 | R2/R7 连击与援护交叉 |
| `r3_cleave_damage_data.json` | `research_r3_cleave.py`<br>`inspect_cleave_diff.py` | 1,303 份群攻战报；2,258 个多副目标群攻事件；1,938 个（85.8%）副目标承受完全相同伤害；320 个不同伤害经逐帧切片全数证实为残血兵力截断、分担拆分、副目标受增减伤 Buff 或攻击者中途获得增伤（如攻其不备），副目标未重走基础攻防公式。 | R3 群攻基数与 Pipeline |
| `r4_chain_damage_data.json` | `research_r4_chain.py`<br>`inspect_chain_diff.py` | 1,522 份连环战报；11,104 个多目标反馈事件；10,817 个（97.4%）副目标承受完全相同伤害；287 个差异案例全数为残血兵力截断或多段攻击各自独立反馈，目标智力/防御不重新参与计算。 | R4 铁索连环反馈基数 |
| `r6_fendan_math_data.json` | `research_r6_overkill.py` | 2,128 份分担战报；11,381 个分担事件对；主目标伤害扣减与分担者承伤之和 100% 严格守恒 ($D_{orig} = D_{main} + D_{sharer}$)。 | R5/R6 分担守恒律 |
| `r6_death_near_fendan.json` | `research_r6_death_during_fendan.py` | 1,974 份战报；检出 154 例分担状态下的死亡切片：主目标受击致死时分担者不承担过量溢出伤害（分担动作不执行）；分担者残血受损致死时伤害截断为剩余兵力。 | R5/R6 致死过量与分担截断 |
| `r9_status_conflict_data.json` | `research_r9_multi_source.py` | 3,000 份战报；cfg 23（已存在同等或更强效果，施加失败）1,550 例（嘲讽、禁疗、计穷、缴械、混乱、洞察）；cfg 24（覆盖）0 例；cfg 25（刷新）7,875 例（仅限增减伤 Buff 与持续状态）。证明控制状态不可覆盖。 | R6 多来源冲突与覆盖规则 |
| `r10_combo_stratified_data.json` | `research_r10_combo_stratified.py` | 11,015 份连击战报；4,017 对完整连击动作；嘲讽分层同目标率 100% (12/12)；常规存活分层同目标率 48.23% (1721/3568)；混乱分层同目标率 34.48% (80/232)。证明第二击为独立均匀重新索敌。 | R7 RNG 与确定性 |
| `r7_recursion_matrix_data.json` | `research_r7_recursion.py`<br>`inspect_recursion_details.py` | 2,500 份战报；跨反应矩阵全量检验：反击套反击 0 例（排查 8 例为同武将多战法并发反击）；连环套连环 0 例；群攻套群攻 0 例；分担套分担 0 例。跨机制衍生支持：Cleave->Share (17), Cleave->FirstAid (149), Counter->FirstAid (192), Counter->Chain (14) 等。 | R4 完整递归许可矩阵 |
