# 状态研究资料说明

Stage 4 当前正式状态语义基线：

```text
research/official_state_catalog_v1/
```

其中保存当前客户端官方接口提取的 40 个具体战斗特殊状态、46 个战斗词条的闭合说明、Hint ID、官方原文和原始工作簿。

旧目录：

```text
research/state_catalog_v1/
```

是早期基于 22 个状态整理的研究资料，仅保留历史审计价值。Stage 4 不应再把它当成状态全集或主要实现依据。

优先级：

```text
official_state_catalog_v1 官方接口原文
    >
stage9_core_arbitration_v2 第二轮定向实证裁决规范（当前规范基线）
    >
stage9_core_arbitration_v1 第一轮实证研究（历史对比资料）
    >
旧 state_catalog_v1 研究归纳
```

---

## Stage 9 核心底层裁决实证资料 (v2 - 当前规范基线)

```text
research/stage9_core_arbitration_v2/
```

针对 v1 审计反馈开展的第二轮定向反例与控制变量实证研究。通过大规模战报统计与边缘案例穷举，完成了目标重定向、群攻/连环派生管线、分担/分摊数学模型以及反击触发、时序、伤害管线、多来源批次与死亡边界等核心机制的严格实证，并建立了对应冻结合同。

当前已形成独立冻结记录：

- `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`
- `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`
- `STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md` — `690087 分担 / DAMAGE_SHARE` 正式实现合同
- `STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md` — `690086 分摊 / DISTRIBUTION` 正式实现合同
- `STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md` — `690085 反击 / COUNTERATTACK` 正式实现合同

当前新增专项研究与审计记录：

- `STAGE9_TAUNT_MECHANICS_RESEARCH_REPORT.md` — `690106 嘲讽 / TAUNT` 40 项机制结论收敛；当前状态 `AUDIT_PASSED_READY_FOR_FREEZE`。
- `STAGE9_TAUNT_FINAL_CONSISTENCY_AUDIT.md` — TAUNT 最终一致性审计；**PASS / READY_FOR_FREEZE**。

其中：

```text
690087 DAMAGE_SHARE
→ post-formula single-sharer partition
→ target-first commit
→ target death interrupt
→ live validation / attribution / statistics / wounded rules frozen

690086 DISTRIBUTION
→ post-formula multi-participant partition
→ Damage-Time dynamic participant set
→ equal independently-rounded participant share
→ participants Slot ASC first, target commits last
→ participant death does not abort remaining commits
→ overflow discarded without redistribution

690085 COUNTERATTACK
→ ON_NORMAL_ATTACK_RECEIVED only
→ independent WEAPON effect damage, not NormalAttack
→ executes before Assault / Combo next hit
→ multi-source CounterState list; same-source refresh
→ trigger-time CounterBatch snapshot + execution-time live context
→ Counter → Counter / Assault / Cleave blocked
→ Counter → Chain / FirstAid / Lifesteal allowed
→ queued sibling Counter survives target death as 0-loss execution
→ original attacker death cancels pending Assault / Combo

690106 TAUNT — audit passed, ready for freeze
→ NormalAttack primary-target override only
→ unique occupied slot; first-come, no refresh, no overwrite
→ multi-suppressor lifecycle (Insight / source-skill disabled)
→ source death retains instance but disables JIT redirect
→ Confusion shadows Taunt by TargetSelector priority, not lifecycle suppression
→ duration follows target action timeline and continues while suppressed
→ Guard can redirect final recipient after Taunt selects intended target
→ EventTarget-based single-target Assault inherits final recipient
→ final audit repaired old R2 terminology and old R6 stronger-replacement ambiguity
```

分担与分摊具有已冻结的非对称优先级：

```text
DAMAGE_SHARE > DISTRIBUTION
```

以上已冻结合同可作为战斗模拟器正式实现依据。嘲讽已经通过最终一致性审计，但尚未执行最后一步 Freeze Record 转换，因此当前准确状态是 `AUDIT_PASSED_READY_FOR_FREEZE`，不是 `FROZEN`。

---

## Stage 9 核心底层裁决实证资料 (v1 - 历史参考)

```text
research/stage9_core_arbitration_v1/
```

第一轮探索性战报实证归纳，厘清了目标重定向、意图与承伤者解耦、普攻生命周期等初版 12 项公共底层裁决规则，供版本沿革比对参考。
