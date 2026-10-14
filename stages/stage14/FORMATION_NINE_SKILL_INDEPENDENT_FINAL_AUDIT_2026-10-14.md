# Stage14 九阵法 Runtime 独立全审计 / Independent Bounded Final Audit

> 2026-10-14 · **本次仅审计，不擅自改写用户确认 Gameplay 或 Stage13 frozen owners**  
> Locked Battle main: `2105a6a10f8d570ef40550cbe94b487142f4f5e6`  
> Locked Research main: `d9d20e16c85355d7349bbb6df2b1b148d44292a4`  
> Source/code authority: Runtime 实现取 Battle main；游戏真实性与证据级别取 Research 合同、历史战报与用户裁决。  
> 本次审计分支: `stage14-formation-final-independent-audit-20261014`。**合并后 mainline CI 状态必须另外核验。**

## A. 独立裁决（Gate 不混用）

| Gate | 核对内容 | 本轮裁决 |
|---|---|---|
| F-A01 Runtime 清单 | nine canonical `FORMATION_SKILL_REGISTRY` entries，单 ID 唯一 | **PASS 9/9** |
| F-A02 官方玩法真实性 | 用户指定/拟合模型与真正战报实证分开 | **BOUNDED，非完整冻结** |
| F-A03 准备阶段准入 | 非法同队双阵法先于被动/RNG拒绝 | **PASS：36/36 个不同阵法组合** |
| F-A04 双军并存 | 双方各一个不同或相同阵法的组合是否违反“一队一阵法” | **PASS：81/81 个顺序组合结构校验** |
| F-A05 双军实际安装 | 完整合法三人阵容，九阵法任意跨队配对进入真正 PRE_BATTLE installer | **PASS：81/81 个真实效果安装组合** |
| F-A06 来源隔离 | 锋矢阵+八门，携带者阵亡仅清理自己的跨目标状态；其他 Provider 保留 | **PASS：真实双技能 installer、死亡端口** |
| F-A07 非装备兼容 | 无阵法时不隐式安装状态、不提前消耗 RNG | **PASS** |
| F-A08 冻结核心/兵种回归 | Stage13-D1 owner hash、11 个 adversarial，青州兵审计 | **PASS，独立 Actions 证据** |
| F-A09 全量 Runtime | pytest、demo、冻结/青州审计 | **PASS（审计分支 3154 pytest）** |
| F-A10 Research↔Battle ID 权威一致性 | 历史目录与 2026-08 静态导出来源、当前 Runtime 的跨命名空间映射 | **OPEN：8 个具名差异** |
| F-A11 客户端真实规则完整冻结 | 所有属性缩放、微时序、死亡与状态转移的实战证据 | **NOT FROZEN / OPEN** |
| F-A12 最终合并主线验证 | Battle PR #78 已合并；merged-main Actions #38586800988：3154 pytest、demo、D1/青州审计成功 | **PASS** |

**结论**：`NINE_FORMATION_BOUNDED_RUNTIME_AUDIT=PASS_ON_MERGED_MAIN`；`CLIENT_GAMEPLAY_FULL_FREEZE=BLOCKED_ON_OPEN_EVIDENCE`。这不是源码中所有可能错误都不存在的证明；不重开已有用户明确暂缓的缩放公式。

## B. 实际九阵法身份与等级范围（Battle 当前代码）

| ID | 阵法 | 当前 Runtime 已实现 | 保留 OPEN/DEFERRED |
|---|---|---|---|
| `20066` | 锋矢阵 | Lv10 主副将四方向减增伤 | Lv1–9及部分客户端生命周期证明 |
| `20025` | 八门金锁阵 | Lv1–10静态基础值、用户指定智力快照缩放、前三回合先攻+敌军二人输出降低 | 客户端真实智力函数、特殊目标/RNG微时序 |
| `20178` | 箕形阵 | Lv10用户武力模型，敌主将+己方副将兵谋方向分支 | 低等级斜率、真实武力快照时点 |
| `22012` | 三势阵 | Lv1–10用户确认回合副将分配/主将自带技能发动率 | 真实客户端微时序与反例 |
| `22031` | 武锋阵 | Lv10全模式目标优先、实时统率减伤、奇偶回合支援；低等级显式 deputies_only | 低等级主将统率缩放、目标优先边界实证 |
| `22039` | 形一阵 | Lv10用户确认 1–8 回合减伤→增伤曲线、最高属性+60 | Lv1–9，最高属性快照实证 |
| `22040` | 潜龙阵 | Lv1–10属性、阵营/角色校验、显式主将效果资格接口 | 其他具体武将战法未声明的 commander effects，客户端微时序 |
| `20836` | 鱼鳞阵 | Lv1–10副将统率、1–3回合抵御及第5回合起受击治疗 **基础值模型** | 主将武力/统率概率缩放、治疗统率缩放，用户明确暂缓；鱼鳞特有受击微时序 |
| `20862` | 雁行阵 | Lv1–10基础值三分支；现有状态类型非缩放复杂转移含动态/关联/持续伤害 | 携带者统率对概率及偷取量缩放暂缓；未来新增状态 schema 需适配 |

来源：[阵法目录](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/FORMATION_CATALOG_V1.md) 属于历史版本化 Research 范围；实际 ID 以 `formation_admission.py` 的 mainline registry + 2026-08 源 manifest 为本次 Runtime 事实基线。

## C. 本次新增独立可重放测试

`tests/test_stage14_formation_final_independent_audit.py` 全新fixture，不调用九阵法原专项fixture：

1. `1` 个清单/名字唯一性断言；`9` 项逐一定义的 SkillType、发动率、installer、provider slot。
2. `36` 个同一队携带任意两种不同阵法：全局 PRE_BATTLE 预检在 passive hook 和 RNG 消耗之前拒绝，状态和安装标记均为空、SkillRuntime 均保留。
3. `81` 个双方每队一阵法的**互斥规则**组合；这里只验证“一队一个合法”，不谎称效果已装。
4. `81` 个双方各携 9 选 1 的 **生产 PRE_BATTLE 效果安装**组合；fixture 使用双方完整三人、同兵种盾、不同 faction、不同兵种适性、相同类型真实 INHERENT 声明，故满足需要的编队条件；验证双方来源状态和 battle-scoped 安装身份同时存在。
5. `1` 个无阵法纯净回归；`1` 个锋矢阵 × 八门真正状态安装 + 来源阵亡后的对方先攻保留/SkillRuntime 保留。
6. 本轮共新增 **210** 个参数展开后 pytest 用例（基线全量2944 → 分支全量3154），无脚本绕过生产状态/伤害核心。此前专项、九阵法旧审计仍包含于全量 pytest。

截至审计分支测试提交 `cf90a0e2708dccf596396c25ee62367b56c36518`，[Actions #38585912496](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38585912496) **SUCCESS**：3154 pytest PASS、Demo PASS、Stage13-D1 owner hash+11 adversarial PASS、Qingzhou independent PASS。

**限制**：81 × 实际安装覆盖九战法配对时的准备阶段基础安装，并**不**等于 81 × 完整8回合、全部事件组合、所有负面状态种类穷举；原九阵法专项已覆盖大量单体/受击/回合测试，但仍需在未来战法组合阶段扩展全战斗的 pairwise cross-trigger stress。

## D. Independent Source / Architecture Audit

- 真实 Runtime: `sgs_v2/battle_core/{formation_admission,pre_battle_scheduler,pre_battle_order,defeat_cleanup_port}.py`；九个独立 formation module，统一 `BattleSystems` provider/adapters。
- 统一注册/每队唯一：`FORMATION_SKILL_REGISTRY`；`SkillRuntimeRegistry` 唯一 owner+slot，来源死亡保留 SkillRuntime，状态按 source/slot 归属清理。
- 用户 V1 PRE_BATTLE `PASSIVE → FORMATION → TROOP → COMMAND`、同阶段速度高者优先、同速真实进攻方优先；这是 **USER_APPROVED_IMPLEMENTATION_RULE**，而非普遍客户端实证。
- F0 来源清理、状态时效性、关联图及伤害修饰接入均复用 Stage10/13 canonical owners；**本独立 PR 只增加测试和治理报告，不改冻结 Owner、DamageSystem、Lifecycle、Recovery、TroopSystem，也不改任何 Gameplay 数值。**
- 已公开各专项自审/合并审计：`XING_YI_ZHEN_MERGE_AUDIT.md`、`QIAN_LONG_ZHEN_MERGE_AUDIT.md`、`YAN_XING_ZHEN_COMPLETION_AUDIT.md`、`YU_LIN_ZHEN_REACTIONS_AUDIT.md`，以及八门/箕形/三势/武锋各自接入文档与证据目录。
- GitHub CI 的 frozen-owner hash+11 adversarial 与 Qingzhou audit 是独立脚本的**工程审计**；不能替代 43,000 份原始战报全量重算或用户确认的真实机制实证。

## E. 显式剩余工作与 Gate Ownership

| ID | 级别 | 下一动作 | 合同/权限 |
|---|---|---|---|
| ID-01~04 | **P1 / Research Governance** | 研究九阵法两个 ID 命名空间，验证8个差异；补版本化数据映射，写入 Research 权威，再更新 Battle 导入 | [独立 ID 研究审计](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/FORMATION_CROSS_REPO_ID_AUDIT_2026-10-14.md) |
| SCALE-01 | DEFERRED BY USER | 鱼鳞武统概率与治疗统率、雁行统率概率及偷取量；其他战法未实装的低等级缩放 | 未授权不得猜公式 |
| TRUTH-01 | OPEN | 九战法客户端等级、真实RNG与微时序、先攻与来源死亡实证、复杂负面状态边界 | Research 单战法专项反例审计 |
| PAIR-01 | P2 / Engineering | 将本轮81真实安装用例扩展成双军动态回合碰撞、选人与抵御/恢复/状态转移交互反例套件 | 不阻断已测试范围的工程有界验收 |
| CMD-READY | P2 / Project | 将阵法正式 scoped freeze 后进入指挥战法 Stage14 Command F0，复用 PRE_BATTLE 和机制 Owner | 先做指挥目录、证据合同、招募有界规则 |

**本次裁决是“双轨并行”**：九阵法当前用户授权的 **已实装基础行为可有边界通过 Runtime 审计**；8 个 ID 差异和未证实机制仍不能认定 `FULL_GAMEPLAY_CLIENT_FROZEN`。用户明确暂缓的属性缩放不阻止下一类指挥战法的 Research 准备。

## F. Publish Checklist

- [x] 九阵法真实源码与已发布审计文件核对
- [x] 9×身份、36同队冲突、81跨队互斥、81跨队真实安装和来源死亡测试
- [x] 独立分支全量3154、demo、Stage13-D1/青州审计 PASS
- [x] Research 8 ID差异另记，未篡改历史目录
- [x] [Battle PR #78](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/78) 已合并；[merged-main CI #38586800988](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38586800988) SUCCESS：3154 pytest、demo、Stage13-D1、青州审计均 PASS。

## G. 最终 merged-main 独立审计裁决（2026-10-14）

- Research 跨仓 ID 治理审计：[PR #21](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/pull/21) MERGED，Research main `95995aa3cfb08fe834f4ca43572635e6d478e729`。
- Battle 九阵法独立审计：[PR #78](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/78) MERGED，测试/main 基线 `ac5dd094b7a3d27ffb7ab17b78a1ff5ad2e73b46`。
- [Merged-main Actions #38586800988](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38586800988) **SUCCESS**：`3154 passed`；Demo PASS；Stage13-D1 independent runtime + 11 adversarial PASS；青州独立审计 PASS；审计产物上传成功。
- `STAGE14_NINE_FORMATION_REGISTERED = 9/9`；`NINE_FORMATION_BOUNDED_RUNTIME_AUDIT = PASS`；`RESEARCH_GAMEPLAY_CLIENT_FULL_FREEZE = NOT_FROZEN`；`RESEARCH_BATTLE_ID_UNIFICATION = OPEN_8_SOURCE_MAPPING_DECISIONS`；`ATTRIBUTE_SCALING_USER_DEFERRED = YES`。
- 可启动下一类战法的 **Research 阶段**，但绝不表示未完成 ID 映射的历史战报/旧队伍配置可以自动重放。
