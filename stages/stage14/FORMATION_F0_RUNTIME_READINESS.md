# Stage14-F0 阵法战法 Runtime 准备阶段审计与接入路线

> **2026-10-13 现行状态与历史文档说明**：本文件原始 2026-10-12 章节为 *F0 设计前* 的历史 gap snapshot，下面 “MISSING / PLANNED / NOT_FROZEN” 结论**不再代表当前 main**。最新权威状态参见本文件末尾“F0 merged-main exit audit”；不得覆盖旧证据。
>
> Research F0 [PR #18](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/pull/18) 已合并；Battle F0-I-A [PR #66](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/66) 已合并并通过 merged-main CI。第一只具体阵法锋矢阵尚未实现。


> 日期：2026-10-12
> 状态：**READINESS GAP IDENTIFIED / DOCUMENTATION ONLY / NO FORMATION GAMEPLAY IMPLEMENTED**
> 用户路线裁决：象兵 DEFERRED；兵种战法已进 main 15/16；下一批接入阵法战法。

## 1. 实际主线状态

截至 Battle main `c8e8b0abeff0a7a79f79e6ed57cfa453f445efb4`：
- 兵种战法 `TROOP_SKILL_REGISTRY` 有 15 个注册项，象兵未注册、未实现。
- 飞熊军 PR #62 与丹阳兵 PR #63 已合并，后者的 Gameplay 细节仍 OPEN。
- `SkillType.FORMATION` 由 `skill_definition.py` 定义，但不是 FORMATION 自动安装的证明。
- `engine.py` 的战斗入口在 `PRE_BATTLE` 调用 `process_pre_battle_troop_skills(context, systems)`。
- `troop_admission.py` 的此函数仅筛选 `rt.definition.skill_type == SkillType.TROOP`。
- 当前没有同等的 FORMATION 入口、队伍互斥准入与全局类型序列 orchestration。

因此：
```text
STAGE14 TROOP SKILLS MAIN   = 15 / 16
XIANG_BING                  = DEFERRED
FORMATION ENUM              = PRESENT
FORMATION OPENING SCHEDULER = MISSING
FORMATION MAINLINE SKILLS   = 0
```

不得直接在阵法单文件里“抢先执行”绕过 `BattleEngine`。

## 2. 继承的游戏研究范围

Research 的 `Stage14_Troop_Skill_Research/02_Evidence/audits/TROOP_PREBATTLE_ORDER_AUDIT.md` 已记录在研究语料中的宏观顺序：

```text
PASSIVE -> FORMATION -> TROOP -> COMMAND
```

本轮 F0 需要以 Research 正式授权作 Runtime requirement，不能从过去代码运行顺序反向冻结 Gameplay Truth。

特别注意当前 Runtime 仅显式 auto-admit TROOP，尚不能宣称这个宏观次序“已经实现”。
准备阶段日志顺序和真实效果提交顺序也必须被区分。

## 3. Runtime owner / seam 设计要求

| 能力 | 已有 owner | 所需工作 |
|---|---|---|
| 战斗入口与 PRE_BATTLE | BattleEngine | 在原入口中集成可组合预战执行序列；禁止私建第二个引擎 |
| 战法身份/槽位 | SkillRuntime / SkillProviderRef | 复用 owner_id + skill_slot，不伪造携带者 |
| 战法类型 | SkillType.FORMATION | 建立 FORMATION 注册/准入模型 |
| 编队约束 | 当前尚无专门阵法准入 owner | 设计每队阵法互斥/合法性 preflight，确认 Research 口径 |
| 目标 | SkillResolver / TargetSystem | 复用主将、副将、全队、敌军目标 intent |
| 状态 / 生命周期 | StateApplication / StateLifecycle | 复用 timed/persistent state，禁止单战法绕过 |
| 属性修改 | AttributeSystem / state_modifiers | 复用原修饰器，区分 snapshot 与 live 读取 |
| 增减伤 | DamageModifierSystem | 复用现有同类型 stacking 与持续时间规则 |
| 回合事件 | Round / Unit action hooks | 依据具体 Formation 合同复用 |
| 随机 | RandomSystem | 不在 Formation 定义中自行构造 PRNG |
| 战斗结束 | BattleFinalizationCoordinator | 继续统一清理，不残留阵法状态 |

## 4. 最重要的阻塞问题

1. **类型顺序**：FORMATION 应在 TROOP 前，但 engine 目前只调用 troop auto-admission。先设计通用 PRE_BATTLE composition，不要在 troop_admission 模块随意插入全局阵法排序。
2. **运行时原子性**：编队冲突、非法阵法身份、缺技能槽或准入失败时，不得产生部分效果。
3. **位置 / 速度次序**：同类型多个效果在研究未冻结时不得通过 `dict` 遍历顺序偷偷指定优先级。
4. **跨类型数据可见性**：阵法阶段对后续兵种与指挥的属性/state 读数应具有明确的前向可见性，允许差分用例验证。
5. **与旧兵种代码兼容**：改变 `BattleEngine` 主入口后，原15个兵种战法必须仍经原 `TroopSkillConfig` / `admit_and_install_troop_skill` 接入；不得替换冻结 damage/recovery owner。
6. **合法化口径**：禁止先实现八门/锋矢后再从运行结果“证明”阵法机制。

## 5. F0 验收测试设计（暂未执行）

- TYPE_ORDER：用 fake PASSIVE / FORMATION / TROOP / COMMAND 记录效果安装操作，断言先后顺序；其中 COMMAND 目前仅测试组合 seam 的合约，不虚构完整指挥实现。
- FORWARD_VISIBILITY：阵法施加修饰后，兵种动态解析读取更新后的最终属性；指挥位置将来应看到兵种结果。
- SINGLE_FORMATION：同队两阵法、重复同槽、两个携带者、敌我双方各一阵法的边界。
- ATOMIC_FAILURE：任一非法条件不会留下半份状态或消耗 RNG。
- PROVIDER：持有者、执行者、实际目标与 source_ref 准确。
- FROZEN_OWNERS：Stage13-D1 哈希、11项对抗测试、不改写核心 owner。
- REGRESSION：15个已接入兵种与新 Formation pilot 同时加载，既有伤害/治疗/状态测试仍通过。
- REPLAY：全套 pytest、完整战斗 demo、独立 Runtime audit、PR CI、merged-main CI。

## 6. 接入次序与门禁

```text
F0-Research  阵法目录、证据/问题清单、准备阶段宏观顺序确认
  -> F0-Runtime  定义最小 PRE_BATTLE dispatch / team-exclusive admission
  -> F0-Audit    无冻结 owner 漂移、保留15兵种回归
  -> F1          首个阵法：建议锋矢阵（具体规则需单独 Research 合同）
  -> F2+         八门金锁阵、箕形阵、三势阵、武锋阵、形一阵、潜龙阵、鱼鳞阵等候选
  -> Formation release review
```

候选阵法集合不是已核实当前客户端穷尽列表。F1 的优先级可根据官方当前文本、证据强度与 Runtime 门禁调整。

## 7. 不属于本阶段的工作

- 不做象兵延迟伤害结算。
- 不擅自补全所有被动与指挥战法；只为未来组合顺序设计接口。
- 不接入任何阵法具体玩法，除非专项合同或用户明确授权的 provisional model 已准备就绪。
- 不声明 FORMATION_F0=FROZEN。当前交付仅是 **route + gap audit**。

## 8. 验收状态

```text
XIANG_BING                   = DEFERRED
FORMATION_F0_RESEARCH        = PLANNED
FORMATION_F0_RUNTIME_DESIGN  = BLOCKED_ON_RESEARCH_AUTHORITY
FORMATION_SPECIFIC_RUNTIME   = NOT_STARTED
FORMATION_MAINLINE           = 0
```

---

## 9. F0 merged-main exit audit（2026-10-13，覆盖上文历史准备状态）

| Gate | Final mainline evidence | Verdict |
|---|---|---|
| Research F0-R | Research PR #18 MERGED; main `abd654a907019a16a61adefee97663b25b073dd2` | PASS / BOUNDED_FROZEN |
| Battle F0-I-A | Battle PR #66 MERGED; main `2238186848fee6c89a9e688174f2fe64d382c1a0` | PASS |
| Foundation tests | 15 in `tests/test_stage14_formation_f0_foundation.py`, part of full CI | PASS |
| Full Regression | [merged-main Actions #38278028436](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38278028436): 2239 tests passed | PASS |
| Demo + frozen owner audit | Demo PASS; Stage13-D1 hash/harness PASS; Qingzhou independent audit PASS | PASS |
| Formation Gameplay | No `20066` actual registry or other formation Gameplay, only synthetic test formations | NOT_STARTED (intentional) |
| F1 research preconditions | F1 research contract and adapter/test readiness document on Research main | READY |

### F0 Runtime capability frozen to accepted baseline

- PRE_BATTLE 全局按 **PASSIVE → FORMATION → TROOP → COMMAND** 调度（用户 V1 实现规则，非客户端全局日志实证）。
- 所有队伍阵法预检在 PASSIVE 前执行。每队最多一个阵法，非法配置零效果与零 RNG；双军各一个阵法可并存。
- 准备阶段即时速度降序，同速跨队按实际 attacker_team_id 优先；身份不明的跨队同速不可悄悄退化为队伍字典序。
- 既有 Canonical SkillRuntimeRegistry 管来源；携带者阵亡后按 source + skill + slot 清理其持续效果，保留其他技能效果和 SkillRuntime 条目。
- **Stage13 frozen `state_lifecycle_system.py` 保持原样**。所有数值与状态仍通过 Stage13 canonical owners。
- 兵种战法 `15/16`，象兵 DEFERRED；F1 前没有任何正式阵法 Gameplay。

### F1 交付入口

Research [锋矢阵合同](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/01_Skills/FENG_SHI_ZHEN_RESEARCH_CONTRACT.md) + [F1 接入前 Adapter/测试清单](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/F1_FENG_SHI_ZHEN_PREINTEGRATION_READINESS.md)。

**F1_IMPLEMENTATION = READY_TO_START / NOT_STARTED**。必须单独功能分支 + Battle PR，严格验证 Lv10 主将 `OUTGOING +30%`/`INCOMING +20%`、副将 `OUTGOING -15%`/`INCOMING -25%`、两种伤害类型、同侧加算池、跨侧乘算层和阵亡后来源失效。不得将 F0 基础设施完成误记为 F1 已完成。

## 10. F1 Stage14 锋矢阵后续发布补记（2026-10-13）

以上 F0 与 F1 待开工说明保留为历史阶段快照。实际 Stage14 F1 已通过 Battle [PR #68](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/68) 进入 main `975b44e67f7d1bfbb6a46fd12be6895e3c8a7cb4`；[F1 merged-main Actions #38280765590](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38280765590) SUCCESS，2267 测试、Stage13-D1 和青州审计全部 PASS。见 [锋矢阵具体战法接入记录](FENG_SHI_ZHEN_INTEGRATION.md)。
