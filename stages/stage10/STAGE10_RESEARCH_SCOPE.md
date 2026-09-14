# Stage10 · Persistent State Runtime Integration · Research Scope

> 状态：`RESEARCH / DESIGN ONLY`
>
> Production implementation：`NOT AUTHORIZED`

## 1. Stage10 重新定位

Stage10 不再以“高级控制七状态”为目标。

当前正式方向：

```text
Persistent State Runtime Integration
```

目标是把已经在状态研究仓库完成研究冻结的 8 个持续性状态，正式适配到当前 Stage7 / Stage8 / Stage9 冻结 Runtime。

## 2. 目标状态

```text
690072 burn / 灼烧
690073 flood / 水攻
690074 poison / 中毒
690075 rout / 溃逃
690076 sandstorm / 沙暴
690077 rebellion / 叛逃
690078 first_aid / 急救
690079 recuperation / 休整
```

研究 authority：

```text
lxy2005051020-commits/sgs-state-mechanics-research
```

具体当前合同入口以该仓库 `STATE_MECHANICS_INDEX.md` 与各状态 `MECHANISM_CONTRACT.md` 为准。

## 3. Stage10 必须先做的事情

在写任何 production code 前，先完成：

```text
1. 逐状态读取当前 Mechanism Contract
2. 提取触发时机
3. 提取伤害 / 恢复基准
4. 提取来源 provenance
5. 提取生命周期与 reapplication 规则
6. 提取死亡 / 终战边界
7. 提取 RNG 规则
8. 提取与禁疗 / 虚弱 / 分担 / 分摊 / 连环等交叉机制
9. 映射到 Stage7 Trigger / Recovery
10. 映射到 Stage8 Damage Pipeline
11. 映射到 Stage9 operation identity / finalization / future admission
12. 列出 implementation-blocking gaps
```

## 4. Stage10 设计原则

### Trigger

持续性状态不得各自发明新的战斗循环。

统一通过 Stage7 已冻结 trigger infrastructure 接入适当 lifecycle node。

### Damage

所有造成伤害的持续状态必须进入正式 Damage / DamageInstance 路径；除非当前冻结机制合同明确要求 direct troop loss，否则不得直接修改 troops。

### Recovery

急救、休整统一通过 RecoverySystem / TroopSystem 恢复路径，不得直接增加兵力。

### Provenance

必须保留：

```text
source unit
source skill
source skill slot（如适用）
source state
source state instance
operation lineage（如进入 Stage9 operation）
```

### Frozen boundaries

Stage10 不得静默改变：

```text
Stage7 trigger / recovery ownership
Stage8 base damage formula
Stage8 damage prevention / hit / modifier semantics
Stage9 target pipeline
Stage9 operation identity
Stage9 FutureAdmissionGate
Stage9 finalization barriers
```

若 Mechanism Contract 与现有冻结架构真实冲突：

```text
STOP
→ 记录 blocker
→ 进入显式 Reopen / architecture decision
```

不得用局部 special-case 掩盖冲突。

## 5. Stage10 输出物

设计阶段至少应生成：

```text
STAGE10_RESEARCH_MATRIX.md
STAGE10_RUNTIME_MAPPING.md
STAGE10_OPEN_QUESTIONS.md
STAGE10.md
STAGE10_DESIGN_AUDIT.md
```

只有 `STAGE10_DESIGN_AUDIT.md` 得出允许施工结论后，才能编写正式 Build Prompt 并进入 implementation。

## 6. Stage10 完成标准

Stage10 最终目标不是“8 个状态能跑 demo”，而是：

```text
8 个状态 Research authority 无漂移
8 个状态 production runtime binding 完成
交叉机制测试通过
无 silent frozen-contract change
独立 Final Audit PASS
8 个状态 Runtime FROZEN TO CONTRACT
```

若全部完成，严格官方状态完成数预计从：

```text
8 / 40
→
16 / 40
```

前提是没有状态因正式 Reopen 暂时失去 FROZEN 状态。
