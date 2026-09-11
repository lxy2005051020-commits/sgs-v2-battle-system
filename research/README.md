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
stage9_core_arbitration_v1 真实战报实证裁决规范
    >
旧 state_catalog_v1 研究归纳
```

---

## Stage 9 核心底层裁决实证资料 (v1)

```text
research/stage9_core_arbitration_v1/
```

基于 32,660 份真实战报数据库的全量检索与分析，厘清了目标选择与重定向、意图与承伤者解耦、普攻生命周期、反应队列模型、递归防线、伤害派生分类（拆分/转移/复制/反馈）、理论伤害 vs 实际兵力损失、Pipeline 重入、因果追踪及确定性 RNG 等全部 12 项公共底层裁决规则。

