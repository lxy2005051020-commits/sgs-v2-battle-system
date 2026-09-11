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

针对 v1 审计反馈开展的第二轮定向反例与控制变量实证研究。通过对 32,660 份战报的大规模统计与边缘案例穷举，完成了反例归因、自援护发现、突击前置假象破除、群攻/连环基数派生管线精确定位、分担/分摊数学模型建立、多重控制冲突策略等核心机制的严格实证，并建立了包含全量提取数据与证据等级矩阵（Grade A/B 100%）的复现档案包。

当前已形成独立冻结记录：

- `STAGE9_CLEAVE_MECHANICS_FREEZE_RECORD.md`
- `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md`
- `STAGE9_DAMAGE_SHARE_MECHANICS_FREEZE_RECORD.md` — `690087 分担 / DAMAGE_SHARE` 正式实现合同

其中 `690087 DAMAGE_SHARE` 已完成终伤后拆分、取整、target-first commit、死亡中断、实时校验、援护/规避/抵御/分摊交互、生命周期、归因、统计和伤兵规则冻结，可作为战斗模拟器实现依据。

---

## Stage 9 核心底层裁决实证资料 (v1 - 历史参考)

```text
research/stage9_core_arbitration_v1/
```

第一轮探索性战报实证归纳，厘清了目标重定向、意图与承伤者解耦、普攻生命周期等初版 12 项公共底层裁决规则，供版本沿革比对参考。
