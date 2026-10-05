# 解烦卫 Runtime Independent Audit

> Date: 2026-10-06  
> Audit target: `stage14-xie-fan-wei` @ `caad915d07a9138ee2a94171595d3cb8f44248be`  
> PR: #57 (DRAFT)  
> Verdict: **PASS / FINAL REMOTE CI REQUIRED**

## 1. Remote state

```text
Branch head = caad915d07a9138ee2a94171595d3cb8f44248be
PR #57      = OPEN / DRAFT / MERGEABLE
CI          = 37353727411 / SUCCESS
Focused     = 35 passed
Full pytest = 2112 passed
Stage13-D1  = 11 passed
```

Research PR #16 已合并，`MC-STAGE14-XIEFAN-01` 已发布到 Research main；Catalog 概率已从错误的 `30%→60%` 修正为固定 `30%`。

## 2. Research authority conflict

当前 Research Catalog 的解烦卫行仍为 OPEN，并写有 `30%→60%` 概率表述。
当前 Battle 实现与接入说明使用固定 30% 伤害分支，未抽中时进入治疗分支。

独立外部资料复核支持固定 30% 伤害概率、否则治疗，因此 Runtime 的 `.30` 与当前资料更一致；
但 Gameplay Truth authority 仍是 Research Repository，因此在 Research Catalog/专项合同纠正前，不能靠 Runtime 或外部网页直接覆盖当前 Research main。

结论：

```text
RUNTIME_30_PERCENT = CONTRACT_ALIGNED
RESEARCH_CATALOG_30_TO_60 = CORRECTED_TO_FIXED_30
RESEARCH_GATE = PASS
```

## 3. Identity / admission / speed bonus

PASS：

- SPEAR -> XIE_FAN_WEI；
- PRE_BATTLE 使用共享 TroopSkillConfig / troop admission；
- 我军全体 speed +36 通过 Attribute Modifier 状态实现，不直接改 Unit 基础 speed；
- Provider provenance 保留实际携带者与技能槽位；
- 非法兵种与重复安装由既有 admission owner 处理。

## 4. Fastest performer selection

PASS FOR CURRENT AUTHORIZED MODEL：

- performer 在 PRE_BATTLE admission 时固定；
- 查询使用 AttributeSystem 的当前最终 speed；
- 自身 +36 为全队等量修饰，不改变当时排序；
- 并列通过 lineup_position 决定，顺序为 COMMANDER -> DEPUTY_1 -> DEPUTY_2；
- 后续速度变化不会更换 performer；
- 固定 performer 阵亡后不提升下一快武将。

该策略与 Battle 接入说明中的 owner-confirmed 口径一致。

## 5. Normal-attack followup and branch semantics

PASS FOR CURRENT AUTHORIZED MODEL：

- 只允许固定 performer 的真实普通攻击 permit 进入分支；
- Provider 无效、死亡、威慑抑制时不抽分支 RNG；
- 单次 `chance(.30)` 决定互斥分支；
- 抽中伤害后，即使伤害被规避/抵御/虚弱归零，也不回退治疗；
- 普攻自身规避、抵御或零伤害仍允许进入解烦卫分支；
- 伤害与治疗都使用新的随机单体目标，而不是继承原普攻目标。

多种普攻后派生效果之间的更细顺序仍未专项冻结，可继续作为 OPEN。

## 6. Damage branch

PASS FOR CURRENT AUTHORIZED MODEL：

- 武力 > 智力 -> WEAPON；
- 智力 > 武力 -> STRATEGY；
- 相等 -> WEAPON；
- 属性读取使用 performer 执行时实时最终属性；
- 基础 coefficient = 0.36；
- additive damage = performer 实时最终 speed * 0.40；
- additive 值位于 `base_damage * coefficient` 之后、后续暴击/增减伤之前；
- 继续进入完整 DamageSystem 下游流程；
- Stage11 family 使用 COMMAND_XIEFANWEI，因此看破类逻辑可命中该兵种伤害家族。

## 7. AdditiveDamageSystem architecture audit

CONDITIONAL PASS：

- 没有复制 WeaponBaseDamageFormula / StrategyBaseDamageFormula；
- 没有复制 RandomSystem、DamageModifierSystem、HitResolutionSystem 或 settlement；
- `AdditiveDamageSystem` 继承 DamageSystem，并对普通请求完整委托 `super().calculate()`；
- 只有 `AdditiveDamageRequest` 且 nonzero additive 值改变 `base * coefficient` 接缝；
- ContextVar 在单次 calculate 范围内设置并 finally reset，防止请求间泄漏；
- zero-additive 与普通 DamageRequest 的回归测试保持原行为。

但要注意：Stage13-D1 的 frozen-source hash 审计不会发现 `BattleSystems.damage_system` 从 `DamageSystem` 切换为其子类。
因此 `Stage13-D1 PASS` 本身不足以证明 owner 语义未扩展。本独立审计将该方案认定为 **canonical DamageSystem extension**，而不是第二套伤害 owner；`XIE_FAN_ADDITIVE_DAMAGE_SEAM.md` 已正式记录该 opt-in seam 的 owner、公式位置、隔离与回归要求。

## 8. Recovery branch

PASS FOR CURRENT AUTHORIZED MODEL：

- 未抽中 30% 伤害分支时进入治疗；
- 随机选择我军单体，包括自身与满兵成员；
- 不因禁疗或容量不足而重新选目标；
- rate = 0.72；
- source troops 使用固定 performer PRE_BATTLE 兵力快照；
- source attribute 使用 performer 触发时实时 `max(final_force, final_intelligence)`；
- nominal recovery 由 TreatmentFormulaSystem 第一层 CEIL；
- RecoverySystem 在 modifier_policy=APPLY 时执行第二层 CEIL；
- healing block、伤兵容量与最终兵力 mutation 继续由 RecoverySystem / TroopSystem 所有。

专项测试中的 421 用例覆盖了两次向上取整路径。

## 9. Han Dang commander branch

PASS：

当前 Research Catalog 文本包含：韩当统领时基础伤害率提升至满级 72%。
当前实现已补齐：只有韩当为队伍 COMMANDER 时，解烦卫 damage coefficient 从 0.36 提升到 0.72；韩当作为副将不触发。新增辨别性测试覆盖主将/副将两种情况。该分支不改变 30% 概率、Speed×0.40、治疗率 72% 或固定最快者规则。

## 10. Lineage / provenance

NON-BLOCKING OPEN：

- 当前 followup damage/recovery 保留 source skill / provider / performer attribution；
- 父普通攻击编号 / root action id 仍未建立显式关联；
- 这与 PR #57 自身声明一致。

当前可作为追踪/重放改进项保留 OPEN；若未来机制依赖父子 lineage 做玩法判定，则必须先补 canonical OperationLineage，而不能从 EventBus 日志倒推。

## 11. Mainline gate verdict

```text
XIEFAN_RUNTIME_REGRESSION          = PASS
XIEFAN_FASTEST_PERFORMER           = PASS
XIEFAN_DAMAGE_BRANCH               = PASS
XIEFAN_RECOVERY_BRANCH             = PASS
XIEFAN_PROVIDER_LIFECYCLE          = PASS
XIEFAN_ADDITIVE_DAMAGE_ARCH        = CONDITIONAL_PASS

XIEFAN_RESEARCH_CONTRACT           = PASS
XIEFAN_RESEARCH_CATALOG_PROBABILITY= CORRECTED
XIEFAN_HAN_DANG_SCOPE              = CLOSED
XIEFAN_LINEAGE                     = OPEN_NONBLOCKING

XIEFAN_RUNTIME_AUDIT               = PASS
MAINLINE_READINESS                 = READY_IF_FINAL_REMOTE_CI_PASS
```

## 12. Closure evidence

- Research PR #16 merged: `f4aea546537447067d29275e87da5bdcc8f65de8`。
- Catalog fixed to 30% damage branch.
- Han Dang COMMANDER 72% branch implemented; deputy negative case covered.
- Additive seam contract published in `XIE_FAN_ADDITIVE_DAMAGE_SEAM.md`.
- Final repaired runtime head passed remote CI `37355725515`: `2114 passed`, Stage13-D1 `11 passed`.
- Parent/root lineage remains explicitly OPEN and non-blocking.
