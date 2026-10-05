# Stage14 Troop Batch01-04 Mainline Audit

> Date: 2026-10-05  
> Verdict: **PASS**  
> Scope: 白马义从、虎豹骑、无当飞军、陷阵营、白毦兵、大戟士、藤甲兵  
> Baseline before merge chain: `766eeaac16e227c9eee250e452403020f16e11ea`

## 1. Research gate

Research PR #10 已合并：

```text
Contract:
MC-STAGE14-TROOP-BATCH01-04-BASELINE-01

Status:
FROZEN_BASELINE / EXTENSIONS_OPEN

Research merge SHA:
36e4faeb513226098251b4b5d193ed54c56cc6e2
```

冻结范围仅覆盖已确认的基础玩法与已明确的统领分支。公孙瓒/曹纯/高顺等尚未关闭的缩放或时序问题继续保持 OPEN / DEFERRED，不因 Runtime 通过测试而升级为 Gameplay Truth。

## 2. Runtime audit

审计确认：

- Stage13 冻结 owner 未被本批次直接篡改；
- DamageSystem、RecoverySystem、StateLifecycleSystem、RandomSystem、TargetSystem、TriggerSystem 等冻结 owner 哈希审计保持 PASS；
- 新能力通过组合层扩展，不建立第二套伤害、治疗、随机或状态物理生命周期系统；
- TROOP 准入继续由共享 `TroopSkillConfig / admit_and_install_troop_skill` 管理；
- Provider、威慑抑制、来源死亡、特殊兵种身份生命周期继续继承 Stage14 foundation；
- 统一 RNG 仍由 `RandomSystem` 所有；
- 新的 Attribute / Activation Modifier、Scheduled Skill、Normal Attack Followup、Application Reaction 都作为可复用 seam 接入现有 owner。

## 3. Mainline merge chain

| PR | Scope | Merge SHA | merged-main CI |
|---|---|---|---|
| #46 | 白马义从 + 虎豹骑 | `47fc9b0857421a9492aa13c3ef522cd7dff3658b` | `37313973838 / SUCCESS` |
| #47 | 无当飞军 + 陷阵营 | `b5dbd2db52a70834b7b9eeb9bce1b3816f837e06` | `37314103287 / SUCCESS` |
| #48 | 白毦兵 + 大戟士 | `d9b890490596a6fe368fff103ae3bdf6a23670c5` | `37314228006 / SUCCESS` |
| #49 | 藤甲兵 | `8d3f19eaae7e69b9f8f7e7422182d7870acb7be5` | `37314342610 / SUCCESS` |

最终 merged-main 全量：

```text
pytest = 1951 passed
Stage13-D1 adversarial = 11 passed
Stage13-D1 verdict = PASS
```

## 4. Skills in main after this audit

```text
20097 西凉铁骑
20075 白马义从
20098 虎豹骑
20100 无当飞军
20096 陷阵营
20099 白毦兵
20125 大戟士
20095 藤甲兵
```

合计：**8 个兵种战法已进入 main**。

## 5. Preserved open boundaries

本次 PASS 不关闭以下问题：

- 白马义从公孙瓒统领速度缩放与“四回合”精确作用范围；
- 虎豹骑曹纯统领额外武力缩放；
- 陷阵营高顺统领统率缩放；
- 无当飞军首回合中毒与其它开场效果的更细相对顺序；
- 白毦兵 / 大戟士相对其它普攻衍生效果的更细顺序与 lineage；
- 藤甲兵效果自身的特殊净化 / 免疫分类；
- 任何未列入 Research bounded freeze 的未来战法机制。

这些是后续 amendment / family research 的边界，不是本次已合入基础 Runtime 的回滚理由。

## 6. Final verdict

```text
STAGE14_BATCH01_04_RUNTIME_AUDIT = PASS
RESEARCH_BASELINE_GATE           = PASS
FROZEN_OWNER_INTEGRITY           = PASS
MERGED_MAIN_CI                   = PASS
TROOP_SKILLS_IN_MAIN             = 8
NEXT_SKILL_LANE                  = READY
```
