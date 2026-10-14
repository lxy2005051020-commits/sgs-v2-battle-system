# 690083 RESISTANCE / 抵御 Mechanism Contract

State ID: 690083  
Official Name: 抵御  
English Name: RESISTANCE  
Category: FUNCTIONAL_STATE  
Status: FROZEN  
Freeze Date: 2026-09-18  
Evidence Maturity: HIGH_CONFIDENCE  

本合同冻结官方状态 690083「抵御」在当前 Authority 与官方战报中能够稳定确认的外部行为。禁止把研究抽象词（如“裁决管道”“状态槽”“消费函数”）提升为官方源码事实。

---

## 1. Official Rule Authority

官方状态说明明确给出：

> 抵御：可免疫伤害，触发攻击带来的效果和突击。

以及状态冲突规则：

> 同类效果不叠加，若武将已存在抵御状态则本次施加状态将失效。

因此本合同冻结两个顶层事实：

1. 抵御负责免疫当前可抵御伤害，但不会仅因伤害被抵御就取消这次攻击本身以及官方说明明确保留的攻击带来效果 / 突击触发资格；
2. 只要目标当前已经存在有效抵御状态，新的抵御施加失效，不叠加、不覆盖、不刷新既有抵御。

第二条直接关闭此前 Old2 跨来源未观察分支：Old2→New1 与 Old2→New2 均属于“已存在抵御状态时再次施加”，因此新施加失效。

---

## 2. Core Damage Effect

对具有抵御资格的独立 Damage Instance：

~~~text
active Resistance
+ eligible Damage Instance
+ no preceding invalidation
→ Resistance handles current Damage Instance
→ current troop loss = 0
→ Resistance count decreases exactly once
~~~

正常成功抵御的可观察核心协议：

~~~text
cfg96  执行抵御
→ 本次兵损 0
→ cfg757 剩余抵御次数同步
~~~

当最后 1 次被消耗：

~~~text
cfg96
→ 本次兵损 0
→ cfg22 抵御消失
→ cfg757 当前抵御总次数为 0
~~~

单个独立 Damage Instance 未观察到一次消耗 2 次及以上抵御。

---

## 3. Eligible Damage Classes

已由战报实证确认具备抵御资格：

1. 普通攻击直接伤害；
2. 主动战法直接伤害；
3. 突击战法直接伤害；
4. 被动战法直接伤害；
5. 指挥战法直接伤害；
6. 六类持续伤害 Tick：
   - 灼烧；
   - 水攻；
   - 中毒；
   - 溃逃；
   - 沙暴；
   - 叛逃；
7. 普通攻击派生群攻 / Cleave 副目标伤害；
8. 已观察到的反击派生 Damage Instance。

边界：本节冻结的是“当前已观察来源具有资格”，不是对未来所有未知伤害拓扑做无限泛化。

---

## 4. Explicit Non-Resistance Boundaries

以下已实证损失拓扑未观察到抵御处理，目标即使持有有效抵御也不消费次数：

1. 【连环计】铁索反馈接收端兵损；
2. 标准 Damage Share / 分担接收端兵损。

Q9：
~~~text
effective resistance overlap = 369
positive feedback bypass = 345
natural-zero feedback = 24
resistance triggered = 0
~~~

Q10：
~~~text
effective share-receiver resistance overlap = 154
positive share receiver loss = 150
natural zero = 4
resistance triggered = 0
~~~

True Substitute 作为独立于重定向和标准分担的第三种机制，在当前 Authority / 语料中未建立可独立观测对象，保持 UNOBSERVABLE，不作为当前运行合同的已知分支。

---

## 5. Adjudication Granularity

抵御至少按独立 Damage Instance 进行可观察裁决：

- 多目标伤害：不同目标独立；
- 同 Action 同 Target 的多个独立 Damage Instance：逐段独立；
- 同一 DOT 实例跨不同 Tick：按 Tick 到实际结算时动态读取当前抵御状态；
- Cleave 副目标与 Counterattack 派生伤害：各自独立进入抵御资格判断。

同一 DOT 实例已经观察到：

~~~text
抵御0 → 后续正兵损
正兵损 → 后续抵御0
抵御0 → 抵御0
~~~

因此不存在“DOT 施加时一次性锁定整段抵御结果”的模型。

---

## 6. EVASION Ordering

只对同时具备规避资格与抵御资格的 Damage Instance 冻结：

~~~text
EVASION observable adjudication
→ success: current Damage invalid, Resistance not invoked, count unchanged
→ failure: same Damage may subsequently reach Resistance
~~~

全量复核：

~~~text
dual-eligible overlap = 718
evasion success = 178
  resistance preserved = 178
evasion failure = 540
  then resistance success = 540
reverse order observed = 0
~~~

正式顺序：

> EVASION BEFORE RESISTANCE.

不得将这一顺序外推到本身不具备规避资格的特殊兵损拓扑。

---

## 7. SURE_HIT Interaction

对本来具有抵御资格的 Damage Instance，当攻击方「必中」生效：

- 抵御本身不能阻止当前 Damage Instance 继续进入下游结算；
- 仍观察到抵御次数减少恰好 1 次；
- N≥2 时可观察 cfg237「抵御(N)效果无法生效」；
- N=1 时观察到抵御消失与 cfg757=0，随后继续进入下游结算；canonical 22 例中 21 例最终为正兵损，1 例被后续弱化/减伤压到 0。

最终去重 Authority：

~~~text
Must-Hit unique true events = 22
behavior contradictions = 0
~~~

因此：

> 抵御次数消费不等价于“成功免伤”。

同时禁止使用“全额伤害”措辞；必中只证明抵御本身未阻止当前 Damage Instance，其他减伤 / 伤害修正仍可使最终兵损降低甚至为 0。

---

## 8. Resistance Count Consumption Contract

当前可观察合同：

| 场景 | 抵御处理可观察 | 次数变化 |
|---|---:|---:|
| 正常成功抵御 | YES | -1 |
| 必中使抵御无法防伤 | YES | -1 |
| 自然 0 但仍执行抵御协议 | YES | -1 |
| 规避成功 | NO | 0 |
| 铁索反馈接收端 | NO | 0 |
| Damage Share 接收端 | NO | 0 |
| cfg204 暂时失效期间 | NO | 0 |

Q16 正常成功抵御样本：

~~~text
33,199
Delta -1 = 33,199
Delta 0 = 0
single-DI Delta <= -2 = 0
~~~

“Resistance adjudication opportunity / pipeline”等词只能作为研究抽象，不代表官方服务器内部阶段。

---

## 9. Lifecycle

### 9.1 Natural Expiry

未被提前耗尽的抵御，其自然移除稳定锚定于 Holder 自身行动开始。

不同来源具有不同持续时间；持续时间属于 Source Authority，不由 690083 统一写死。

已纠正 Authority 示例：

- 【折冲御侮】：2 次抵御，持续 2 回合；
- 【妖术】：1 次抵御，持续 2 回合；
- 【桃园结义】：第 6 回合我军全体获得 2 次抵御；
- 【白衣渡江】：首回合我军全体获得 1 次抵御。

### 9.2 Source Death

已施加抵御在来源死亡后不会立即被撤销。

~~~text
source-death while target active = 30
immediate removal = 0
preserved = 30
post-source-death successful resistance uses = 11
~~~

### 9.3 Holder Death

Holder 死亡后未再观察到抵御参与后续结算。内部是 delete / clear / 不再查询属于不可观察实现细节。

### 9.4 Suspend / Resume

cfg204：
> 「抵御(N)」暂时失效

暂时失效期间：
- 不免伤；
- 不消费抵御次数；
- 原状态生命周期继续由其来源规则管辖。

cfg205：
> 「抵御(N)」继续生效

Resume 当前完整闭环样本较少，Evidence = SUPPORTED。

### 9.5 Battle End

战斗结束后停止后续可观察抵御参与；不要求额外 cfg22 作为 battle-end cleanup 证据。

---

## 10. Application Conflict / Reapplication

### 10.1 Official State-Level Rule

官方规则：

> 同类效果不叠加，若武将已存在抵御状态则本次施加状态将失效。

冻结为：

~~~text
Target currently has active Resistance
+ any new Resistance application attempt
→ new application invalid
→ existing Resistance remains authoritative
~~~

该规则与来源相同 / 不同、当前剩余 1 次 / 2 次无关。

因此以下均由同一状态级冲突规则覆盖：

- Same Source, Old1→New1；
- Same Source, Old1→New2；
- Same Source, Old2→New2；
- Different Source, Old1→New1；
- Different Source, Old1→New2；
- Different Source, Old2→New1；
- Different Source, Old2→New2。

后两项虽在当前战报库中未观察到直接冲突样本，但由官方状态规则直接定义，不再构成机制 UNKNOWN。

### 10.2 Empirical Conflict Evidence

Cross-Source Q14：

~~~text
active-target application attempts = 2,158
accepted cfg21 = 0
rejected cfg23 = 2,158
overwrite = 0
additive = 0
~~~

Same-Source Q15 正式纠正定本：

~~~text
Old2 → New2 = 1,904
Old1 → New2 = 1,158
Old1 → New1 =   163
Total          = 3,225
all rejected cfg23
~~~

历史报告中的 Old2→New2=2,410 / Old1→New2=652 已正式废止，属于历史报告生成误差。

### 10.3 Duration Refresh

已有抵御存在时，新施加本身失效，因此不以新施加刷新既有 Resistance。

战报决定性验证：
- 【折冲御侮】：同源重施加不刷新原到期边界，HIGH_CONFIDENCE；
- 【妖术】：同源重施加不刷新原到期边界，HIGH_CONFIDENCE；
- 其他少量来源：与同一冲突规则一致，战报单来源 duration 证据量较低，但官方状态级“不叠加 / 本次施加失效”已定义新施加不生效。

---

## 11. Resistance Source Authority Boundary

当前已定本的已知来源分为：

### Battle-observed

- 折冲御侮；
- 妖术；
- 西蜀之智；
- 桃园结义；
- 结盟（动态复制，可复制 1 次或 2 次抵御）；
- 勇者得前；
- 白衣渡江；
- 兴云布雨；
- 竭忠尽智；
- 枕戈坐甲；
- 灵动；
- 躲闪。

### Authority-only in current S1-S3 corpus

- 枪舞如风：固定 2 次；
- 同战身先：1 次；
- 挥兵谋胜：1 次。

固定 Nominal-2 来源：

- 折冲御侮；
- 西蜀之智；
- 桃园结义；
- 枪舞如风。

【结盟】是 DYNAMIC / COPIED Source，可复制出 Resistance(2)，但不属于固定 Nominal-2 Source。

Source Inventory 用于解释来源参数，不改变第 10 节统一状态冲突合同。

---

## 12. Observable cfg Protocol

| cfg | 当前冻结语义 |
|---:|---|
| 21 | 抵御状态成功施加 |
| 22 | 抵御效果消失 / 到期 / 次数耗尽 |
| 23 | 既存抵御导致新施加失败 |
| 96 | 执行抵御效果 |
| 204 | 抵御暂时失效 |
| 205 | 抵御继续生效 |
| 237 | 必中条件下抵御效果无法生效 |
| 757 | 当前抵御总次数同步 |

Damage output cfg 随伤害路径变化，不在本合同建立“伤害类型→唯一 cfg”映射。

特别注意：

> cfg23 文本中的「抵御(N)」不得被解释为“旧状态剩余次数比较规则”。顶层官方状态冲突规则只要求“已存在抵御状态”。

---

## 13. Evidence Summary

关键统计：

~~~text
Q1 clean normal-attack valid samples = 18,883

Q3 six-DOT valid resisted ticks = 988

Q5 multi-target actions = 43,082
strong mixed actions = 3,809

Q6 same Action+Target multi-DI pairs = 14,977

Q7 cleave resistance overlap = 54

Q8 counterattack DI = 7,993
effective resistance overlap = 115

Q9 TieSuo effective overlap = 369
Q10 Share effective overlap = 154

Q12 Evasion+Resistance overlap = 718

Q14 cross-source active apply attempts = 2,158
Q15 same-source active reapply attempts = 3,225

Q16 normal success count-consumption samples = 33,199
single-DI over-consumption = 0
~~~

完整问题过程见 RESEARCH_QUESTION_LEDGER.md。

---

## 14. Remaining Unknown / Unobservable

以下事项不阻塞 690083 核心运行合同：

1. cfg205 Resume：完整闭环仅少量样本，Evidence = SUPPORTED；
2. True Substitute：当前 Authority / 语料未建立独立于 Redirect 与 Share 的可观测机制对象，UNOBSERVABLE；
3. 官方服务器内部对象模型、状态槽、函数名、PRNG、精确内部调用栈：UNOBSERVABLE；
4. 未来新增 Resistance Source 的 source-specific 参数：由未来 Source Authority 决定，不改变当前统一状态冲突规则。

Implementation-blocking unresolved = 0。

---

## 15. Frozen Runtime Contract

模拟器实现必须满足：

1. 对已确认具有抵御资格的独立 Damage Instance，按 Damage Instance 粒度判断；
2. 规避与抵御都适用时，规避先于抵御；
3. 规避成功不得消费抵御；
4. 正常抵御成功将当前伤害兵损归零并消费恰好 1 次；
5. 必中使抵御不能成功防伤，但仍消费恰好 1 次；
6. 铁索反馈接收端与标准 Damage Share 接收端不得独立消费抵御；
7. cfg204 暂时失效期间不得防伤或消费次数；
8. 已施加抵御不得因来源死亡自动移除；
9. Holder 死亡后不得继续参与抵御结算；
10. 目标已有有效抵御时，新的抵御施加必须失效，不叠加、不覆盖、不刷新；
11. 旧抵御消失后，后续新的合法施加可以作为 Fresh Application 正常建立；
12. 抵御免疫当前伤害不等价于取消攻击本身；官方说明明确保留攻击带来的效果和突击触发资格。

---

## 16. Freeze Decision

~~~yaml
Mechanism_Status: FROZEN
Core_Damage_Immunity: CONFIRMED
Eligible_Damage_Classes: CONFIRMED
Per_Damage_Instance_Granularity: CONFIRMED
Evasion_Ordering: CONFIRMED
Sure_Hit_Interaction: CONFIRMED
Charge_Consumption: CONFIRMED
Lifecycle: CONFIRMED
Suspend_Behavior: CONFIRMED
Application_Conflict: CONFIRMED_BY_OFFICIAL_RULE_AND_BATTLE_EVIDENCE
Same_Source_Reapplication: CONFIRMED
Different_Source_Reapplication: CONFIRMED
Old2_Cross_Source_Admission: CLOSED_BY_OFFICIAL_STATE_RULE
Implementation_Blocking_Unresolved: 0
~~~

最终冻结定义：

> 690083「抵御」是一种按独立可抵御 Damage Instance 生效的功能性防御状态。正常生效时令当前伤害兵损归零并消费 1 次；规避成功先行终止当前伤害时不消费；必中可阻止抵御成功免伤但仍消费 1 次。铁索反馈与标准 Damage Share 接收端不进入抵御处理。已存在有效抵御时，任何新的抵御施加均因官方同类状态冲突规则而失效，不叠加、不覆盖、不刷新；旧抵御消失后才允许新的 Fresh Application。其自然生命周期按来源持续规则推进并在 Holder 自身行动开始观察到自然移除。
