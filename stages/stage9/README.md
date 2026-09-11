# Stage 9 · Redirect / Reaction / Additional Action

状态：`🟡 PRE-DESIGN / PREPARATION`

> Stage 9 尚未进入 DESIGN FROZEN，更没有进入 production implementation。当前目录只用于保存 Stage 9 的证据梳理、边界审计与正式设计前准备材料。

## Starting baseline

Battle repository:

```text
repository: lxy2005051020-commits/sgs-v2-battle-system
branch: main
starting exact HEAD: 660fefe2b92d19358772d8c221c072d58a7eb52c
starting state: Stage 8 FROZEN / Stage 9 READY FOR DESIGN
```

State-mechanics research repository:

```text
repository: lxy2005051020-commits/sgs-state-mechanics-research
pinned research tree / main HEAD observed during preparation:
7f1345681812864d4e34fae453bd69f766202c4c
```

Stage 9 working branch:

```text
stage9-redirect-reaction
```

## Planned problem domain

Stage 9 的路线图候选范围是：

```text
目标重定向
追加普通攻击
受击反应
伤害拆分 / 转移 / 传播
确定性派生行为顺序
递归 / 环路保护
```

对应候选官方状态：

```text
combo          / 连击
cleave         / 群攻
counterattack  / 反击
damage_split   / 分摊
damage_share   / 分担
chain_link     / 铁索连环
guard          / 援护
confusion      / 混乱
taunt          / 嘲讽
```

这只是 Stage 9 的设计候选集合，不代表九个状态已经全部具备 production evidence，也不代表正式实现范围已经冻结。

## Preparation artifacts

```text
stages/stage9/
├── README.md
├── STAGE9_PREPARATION.md
└── STAGE9_EVIDENCE_MATRIX.md
```

后续只有在证据边界与核心拓扑完成独立设计审计后，才允许新增并冻结：

```text
STAGE9.md
STAGE9_DESIGN_FREEZE.md
STAGE9_BUILD_PROMPT.md
STAGE9_IMPLEMENTATION_AUDIT.md
STAGE9_FINAL_AUDIT.md
STAGE9_FREEZE_RECORD.md
```

## Hard boundary inherited from Stage 8

Stage 9 不得为了实现派生行为而反向改写 Stage 8 的 frozen damage pipeline 语义。

允许：

```text
在 Stage 8 pipeline 外围新增明确的 orchestration / redirect / reaction contract
为 Stage 9 新增 typed request/result/trace/provenance 模型
在不改变 Stage 8 frozen observable semantics 的前提下增加显式扩展点
```

禁止：

```text
把 reaction 逻辑塞进 EventBus handler 让事件反向决定战斗结果
让具体状态直接修改 troops
让具体状态直接调用 Python random
用递归 NormalAttackSystem.execute() 充当追加攻击/反击调度器
在 DamageSystem 内硬编码具体 Stage 9 状态名
未经证据冻结就把 MINIMUM_USABLE 研究骨架当成官方 production contract
```

## Current preparation verdict

```text
Stage 8 baseline       = VERIFIED FROZEN
Stage 9 branch         = CREATED
Stage 9 code           = NOT STARTED
Stage 9 design         = NOT FROZEN
Evidence readiness     = MIXED
Core architecture risk = IDENTIFIED
Next gate              = evidence closure + formal STAGE9.md design
```
