> Gameplay Research status is MIRROR ONLY. Research truth and evidence: [Research authority](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/RESEARCH_AUTHORITY_INDEX.md). This document owns Runtime/project progress.

# 当前项目状态

> Reconciled: 2026-10-05

## 总体完成度

```text
Official States                 = 40
Research FROZEN                 = 40 / 40
Runtime FROZEN TO CONTRACT      = 40 / 40
Strict Complete                 = 40 / 40

Stage14 Troop Foundation        = FROZEN in Research
Stage14 Concrete Skill Integration = ACTIVE
```

## 阶段状态

```text
Stage 1-8  = COMPLETE / FROZEN as applicable
Stage 9    = FROZEN
Stage10    = FROZEN
Stage11    = RUNTIME FROZEN / POST-FREEZE ACCEPTED
Stage12    = FROZEN / COMPLETE
Stage13    = COMPLETE / FROZEN
Stage14    = ACTIVE / 10 BOUNDED-FROZEN + 2 USER-PROVISIONAL + 1 USER-FIT INTEGRATION
```

Stage13 当前已完成：

```text
B1 Wounded / Recoverable Capacity  = FROZEN / IMPLEMENTED
B2 Damage Modifier Mathematics     = FROZEN / IMPLEMENTED
B2.5 Advancement / Damage Closure  = CLOSED / IMPLEMENTED
B3 Ordinary Treatment Core         = FROZEN / IMPLEMENTED
Residual state closure             = CLOSED / INTEGRATED
D1 PendingWork Foundation          = FROZEN / IMPLEMENTED
```

## Stage14 兵种战法基础合同

Research 已冻结：

```text
MC-STAGE14-TROOP-FOUNDATION-01 = FROZEN
MC-STAGE14-TROOP-BATCH01-04-BASELINE-01 = FROZEN_BASELINE / EXTENSIONS_OPEN
MC-STAGE14-HUWEI-PROVISIONAL-01 = USER_PROVISIONAL_MODEL / RUNTIME_BASELINE_ENABLED
MC-STAGE14-XIANDENG-USER-FIT-01 = USER_FIT_MODEL / RUNTIME_BASELINE_ENABLED / GAMEPLAY_DETAILS_OPEN
MC-STAGE14-XIEFAN-01 = BOUNDED_FROZEN / FINE_LINEAGE_OPEN
MC-STAGE14-JIN-FAN-JUN-01 = BOUNDED_FROZEN / FORMULA_PLACEHOLDERS

- 特殊兵种在 PRE_BATTLE / 准备阶段完成进阶
- 特殊兵种继承基础兵种克制家族
- 后续准备阶段战法读取前序效果修改后的当前状态
- Provider 为 holder-bound skill instance
- Provider 临时失效与 Provider 阵亡是不同生命周期
```

Canonical Research contract:
[Stage14 troop foundation](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Troop_Skill_Research/00_Governance/TROOP_SKILL_IDENTITY_AND_PROVIDER_LIFECYCLE_CONTRACT.md)

## Stage14 当前状态

当前已有 **8 个兵种战法** 完成 Research gate、Runtime 审计与 merged-main CI 并进入 `main`：西凉铁骑、白马义从、虎豹骑、无当飞军、陷阵营、白毦兵、大戟士、藤甲兵。

本次新增 **青州兵20153**，采用用户授权的暂定模型，见[接入说明](stages/stage14/QING_ZHOU_BING_INTEGRATION.md)
与[PR #52](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/52)。
其D/10、统计口径和分配策略不声明实证冻结，曹操额外统率加成为空白占位。
Research合同经PR #13进入main；暂定模型接入与上方八个bounded freeze分开记录。

本次新增 **虎卫军20154（推断ID）**，采用用户授权的暂定损兵增伤模型；治疗后增伤回落已由项目所有者确认并进入 Research 合同。Research PR #14 与 Battle PR #53 均已合并，merged-main CI 为 SUCCESS。

本次新增 **先登死士20246（推断ID）**，采用用户拟合公式并冻结“携带者开局统率快照”读取策略；零伤害触发、独立层到期和 fine aftermath order 继续 OPEN。Research PR #15 与 Battle PR #55 均已合并，merged-main CI 为 SUCCESS。

本次新增 **解烦卫20248（推断ID）**，Research 合同 `MC-STAGE14-XIEFAN-01` 已 bounded freeze：固定 30% 伤害分支、韩当主将伤害率 72%、实时武智与速度附加、治疗双 CEIL 均已接入。Research PR #16 与 Battle PR #57 已合并，merged-main CI `37356182948 / SUCCESS`；fine followup order 与 parent/root lineage 继续 OPEN。

本次补回 **锦帆军20152**。旧 PR #51 因落后主线 23 个提交被关闭为 superseded；current-main 版本从 `main@2e38f3a` 重建并经 PR #60 合并。Research 合同 `MC-STAGE14-JIN-FAN-JUN-01` 保持 BOUNDED_FROZEN：溃逃武力缩放与甘宁概率公式继续使用显式 placeholder，恢复基数/CEIL/甘宁另外两名友军会心+6%保持冻结。merged-main CI `37358410369 / SUCCESS`。

后续单战法或机制家族进入 main 仍需同时满足：

```text
1. Stage13 exit gate = PASS
2. Selected troop skill mechanism contract = CLOSED/FROZEN, or explicitly user-authorized provisional model with named open boundaries
3. Pilot-specific tests = PASS
4. No unresolved core primitive is guessed into Runtime
```

当前正式接入：

```text
20097 西凉铁骑
20075 白马义从
20098 虎豹骑
20100 无当飞军
20096 陷阵营
20099 白毦兵
20125 大戟士
20095 藤甲兵
20153 青州兵 (USER_PROVISIONAL_MODEL / CAO_CAO_PLACEHOLDER)
20154 虎卫军 (USER_PROVISIONAL_MODEL / HEALING_ROLLBACK_FROZEN)
20246 先登死士 (USER_FIT_MODEL / OPENING_COMMAND_SNAPSHOT_FROZEN)
20248 解烦卫 (BOUNDED_FROZEN / FINE_LINEAGE_OPEN)
20152 锦帆军 (BOUNDED_FROZEN / FORMULA_PLACEHOLDERS)

Troop Skills Registered      = 13 (10 bounded-frozen + 2 user-provisional + 1 user-fit)
Latest Merged-main CI        = PASS
Batch01-04 Runtime Audit     = PASS
```

## 当前边界

```text
Core Gameplay Engine      = FROZEN
Skill Runtime Readiness   = READY
Stage14 Troop Skills Registered = 13 (10 bounded-frozen + 2 user-provisional + 1 user-fit)
Stage14 Mainline Gate        = OPEN
Batch Integration             = ACTIVE / FAMILY-GATED
```

详细权威：

- [Stage13 README](stages/stage13/README.md)
- [Stage14 README](stages/stage14/README.md)
- [Stage14 Batch01-04 Mainline Audit](stages/stage14/BATCH01_04_MAINLINE_AUDIT.md)
- [Stage14 Hu Wei Runtime Audit](stages/stage14/HU_WEI_JUN_RUNTIME_AUDIT.md)
- [Stage14 Xian Deng Runtime Audit](stages/stage14/XIAN_DENG_SI_SHI_RUNTIME_AUDIT.md)
- [Stage14 Xie Fan Runtime Audit](stages/stage14/XIE_FAN_WEI_RUNTIME_AUDIT.md)
- [Stage14 Jinfan Runtime Audit](stages/stage14/JIN_FAN_JUN_RUNTIME_AUDIT.md)
- [Stage13 Gap Ledger](stages/stage13/STAGE13_CORE_GAMEPLAY_GAP_LEDGER.md)
- [Stage13 Owner Matrix](stages/stage13/STAGE13_CORE_RUNTIME_OWNER_MATRIX.md)
