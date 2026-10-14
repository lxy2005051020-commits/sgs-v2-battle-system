> Gameplay Research status is MIRROR ONLY. Research truth and evidence: [pinned Research authority](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/95e7fe78430d623c0240e9615f5f054515a90ce9/RESEARCH_AUTHORITY_INDEX.md). This document owns Runtime/project progress.

# 项目路线

> Current authority: 2026-10-04

历史阶段计划已由当前 Stage13 路线取代。旧路线仍可从 Git 历史追溯，不再保留为当前树中的执行权威。

## 已完成主线

```text
Stage1-8   基础战斗 / Effect / Skill Runtime 基础 / Trigger / Damage
Stage9     跨机制编排
Stage10    持续状态
Stage11    官方状态补全（一）
Stage12    官方状态补全（二） / 40-state Runtime closure
Stage13-B  基础机制公式补全
Stage13-C  残余状态机制关闭
Stage13-D1 PendingWork foundation
```

上述已完成或冻结部分只做回归维护，除非出现正式 reopen authority。

## 当前主线

```text
Stage13
  -> reconcile remaining core capability boundaries
  -> close only true core blockers
  -> whole-battle deterministic replay / exit audit
  -> Core Gameplay Engine = FROZEN
  -> Skill Runtime Readiness = READY

Stage14+
  -> concrete Skill System integration
```

原则：

```text
REUSE -> EXTEND -> COMPOSE
real gameplay requirement -> minimal extension
no generic subsystem merely to satisfy an old roadmap label
```

Stage13 当前权威入口：[stages/stage13/README.md](stages/stage13/README.md)

## Stage14 阵法转段裁决（2026-10-12）

- 兵种战法主线已注册 15/16；**象兵 DEFERRED**，保留 [准备清单](stages/stage14/XIANG_BING_PREPARATION.md)，不作为阵法的前置阻塞。
- 下一目标为 **阵法战法 FORMATION**，仍属于 Stage14+ 具体战法接入路线下的 F0 子阶段，暂不凭空宣布 Stage15 冻结。
- 先完成 Research F0 证据与合同，Battle F0 完成准备阶段 type ordering / 队伍阵法准入设计与回归。
- 第一只 pilot 候选：锋矢阵（当前不声明其数值、时长、限制条件已冻结）。
- 后续指挥战法基于统一 PRE_BATTLE 编排接入，不为阵法造第二套 Engine。

[FORMATION F0 Runtime Readiness](stages/stage14/FORMATION_F0_RUNTIME_READINESS.md)

## Stage14 阵法 F0 mainline 收口与 F1 接入前就绪（历史记录，2026-10-13）

- **Research F0-R**：Research [PR #18](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/pull/18) MERGED；基线 `abd654a907019a16a61adefee97663b25b073dd2`。
- **Battle F0-I-A**：[PR #66](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/66) MERGED；基线 `2238186848fee6c89a9e688174f2fe64d382c1a0`。
- **merged-main CI**：[Actions #38278028436](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38278028436) SUCCESS：2239 pytest、demo、Stage13-D1 冻结 Owner 审计、青州独立审计均 PASS。
- **当时拟开展的独立 Gameplay 阶段**：Stage14 F1 `20066 锋矢阵`，后已通过 Battle PR #68 接入 main（详见下节）。专项研究合同和 [F1 preintegration handoff](https://github.com/lxy2005051020-commits/sgs-state-mechanics-research/blob/main/Stage14_Formation_Skill_Research/00_Governance/F1_FENG_SHI_ZHEN_PREINTEGRATION_READINESS.md) 已就绪。F1 当时要求独立功能 PR、专项数值链测试和 mainline audit，现已于 PR #68 完成。
- **用户批准的 V1 规则**：PRE_BATTLE `PASSIVE -> FORMATION -> TROOP -> COMMAND`；携带者阵亡所属阵法持续效果立即失效；同队至多一个阵法；跨队同速进攻方优先。这些属于模拟器用户裁决，不得改写反向战报证据。
- 兵种 `15/16`，象兵仍 `DEFERRED`，截至 F0 退出时阵法 Gameplay 实装 `0`（历史快照）；当前 F1 已接入 `1`（锋矢阵），见下节。

## Stage14 F1 锋矢阵 Gameplay mainline 完成（2026-10-13）

- Battle [PR #68](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/68) MERGED，Gameplay baseline `975b44e67f7d1bfbb6a46fd12be6895e3c8a7cb4`。
- [F1 merged-main Actions #38280765590](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38280765590) **SUCCESS**，全量 `2267/2267` PASS，Demo PASS、Stage13-D1（含 11 条对抗测试）PASS、青州独立审计 PASS。
- 官方 ID `20066`；骑/盾/枪；满级 Lv10 主将造成伤害 +30%、承伤 +20%，副将造成伤害 -15%、承伤 -25%。适用兵刃/谋略，标准核心分层结算，携带者阵亡后来源级立即清理。
- 具体阵法 Gameplay 进 main `1`（锋矢阵），其他阵法 `DEFERRED_TO_PER_SKILL_RESEARCH`；象兵仍暂缓；Lv1~9 数值与客户端真实性边界仍 OPEN。
- [锋矢阵独立接入记录](stages/stage14/FENG_SHI_ZHEN_INTEGRATION.md)。

## Stage14武锋阵接入增量（2026-10-13）

武锋阵 `22031` 支持Lv10完整运行：前5回合概率优先选中主将及同次战法的实时统率减伤，携带者行动时触发奇数回合副将随机治疗另外两名队友、偶数回合叠加增伤。采用用户指定公式与选人规则，标记 `USER_SPECIFIED_MODEL / NOT_GAMEPLAY_FROZEN`；低等级统率缩放未推导。

[接入记录、组件与验证证据](stages/stage14/WU_FENG_ZHEN_INTEGRATION.md)。

## 五个已完成阵法统一同步（2026-10-13）

实现注册数为5：锋矢阵、八门金锁阵、箕形阵、三势阵、武锋阵。范围与保留的未决项见[同步记录](stages/stage14/FORMATION_COMPLETED_SYNC.md)。原本地候选记录属于历史验证快照；本次整合保留用户指定模型边界，不把实现合并等同于Gameplay实证冻结。

## 2026-10-14 阵法九战法独立审计 / 有界退出门禁

- 当前九阵法 `FORMATION_SKILL_REGISTRY=9/9`，包括鱼鳞阵基础值抵御/恢复和雁行阵非缩放状态转移，不再使用历史 F0“五阵法”的表述作为当前进度。
- [独立审计文档](stages/stage14/FORMATION_NINE_SKILL_INDEPENDENT_FINAL_AUDIT_2026-10-14.md) 覆盖 210 个新增 pytest 参数测试，36同队非法双阵法、81跨队互斥及81个合法跨队真实PRE_BATTLE安装组合，另含来源清理、非装配回归与九定义核对。
- 审计分支 [CI #38585912496](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38585912496) SUCCESS：3154 tests、demo、Stage13-D1 frozen audit、青州审计 PASS；merged-main CI待独立验收。
- **Gameplay client full-freeze 不能宣称**：Research历史目录有8个与Runtime 2026-08静态源不同的ID、鱼鳞/雁行属性缩放用户DEFERRED、其他Lv1~9与状态微时序OPEN。Research专项差异审计单列，未经权威验证不得硬改任何目录ID。
- 阵法已实现范围经有界工程审计后，下一主线建议进入 `Stage14 Command F0`：先指挥战法catalog/合同/证据审计，后Runtime逐个接入，不修改Stage13冻结核心。
