# Stage 6 Skill Runtime 构建 Prompt

你现在要继续维护项目：

```text
三国志战略版战斗模拟器 V2
```

GitHub 仓库：

```text
lxy2005051020-commits/sgs-v2-battle-system
```

目标分支：

```text
main
```

当前已知的 Stage 6 规划文档同步提交为：

```text
1512c7018ffc57645dba546ca57f292d2b3bdea6
```

但这个 SHA 只作为历史参考。开始施工前，必须重新读取 `main` 最新 HEAD、最新代码、最新测试与最新 GitHub Actions 状态，不得根据旧聊天、旧 Prompt 或该参考 SHA 猜测当前仓库状态。

---

# 一、正式施工依据

Stage 6 的唯一正式施工规范是仓库根目录：

```text
STAGE6.md
```

同时必须重新阅读并保持以下冻结边界：

```text
PROJECT_STATUS.md
stages/stage5/STAGE5.md
stages/stage5/STAGE5_FINAL_AUDIT.md
stages/stage4/STAGE4.md
stages/stage4/STAGE4_FINAL_AUDIT.md
PROJECT_ROADMAP.md
```

以及当前：

```text
sgs_v2/battle_core/
tests/
.github/workflows/tests.yml
```

如果 `STAGE6.md` 与旧路线图中的历史规划存在冲突，以当前 `STAGE6.md` 为 Stage 6 施工依据。

---

# 二、开始施工前必须先做

先完成以下检查，再修改代码：

```text
1. 读取 main 最新 HEAD。
2. 确认 STAGE6.md 已存在于 main。
3. 确认 Stage 5 仍然处于 FROZEN 状态。
4. 检查 main 最新 GitHub Actions 状态。
5. 重新读取当前 battle_core 相关实现，不假设文件与旧聊天一致。
6. 重新读取现有 tests，避免重复建立已有能力。
```

如果发现 Stage 5 冻结边界已经被破坏，或当前 main 本身存在与 Stage 6 无关的 BLOCKER，先明确报告，不要把旧问题伪装成 Stage 6 修改的一部分。

---

# 三、Stage 6 核心目标

本阶段必须建立：

```text
SkillDefinition
      ↓
SkillRuntime
      ↓
SkillResolver
      ↓
ordered Effect(s)
      ↓
EffectExecutor
      ↓
已有 BattleSystem
```

核心验证命题：

> Skill 层只负责表达和产生 Effect，不直接执行底层战斗副作用。

Stage 6 不是实现真实战法目录，也不是实现完整战法触发时序。

---

# 四、必须实现的最小生产代码

原则上新增：

```text
sgs_v2/battle_core/skill_definition.py
sgs_v2/battle_core/skill_runtime.py
sgs_v2/battle_core/skill_resolver.py
```

并按需要最小修改：

```text
sgs_v2/battle_core/battle_systems.py
sgs_v2/battle_core/__init__.py
```

不要为了 Stage 6 顺手重构其他冻结模块。

---

# 五、SkillDefinition 合同

建立不可变静态定义，推荐：

```python
@dataclass(frozen=True, slots=True)
class SkillDefinition:
    skill_id: str
    name: str
    activation_rate: float
    target_mode: SkillTargetMode
    effect_specs: tuple[SkillEffectSpec, ...]
```

必须验证：

```text
skill_id 非空
name 非空
0.0 <= activation_rate <= 1.0
effect_specs 至少 1 项
effect_specs 使用确定顺序 tuple
```

本阶段不要加入：

```text
SkillCategory / SkillType
level
level parameter table
priority
timing
trigger_type
cooldown
charges
metadata
runtime_payload
custom handler
callable
```

禁止使用：

```python
metadata: dict[str, Any]
params: dict[str, Any]
handler: Callable[..., ...]
```

作为万能逃生门。

---

# 六、SkillEffectSpec 合同

Stage 6 只建立当前验证所需的 typed specs：

```text
DamageSkillEffectSpec
ApplyStateSkillEffectSpec
```

推荐形式：

```python
@dataclass(frozen=True, slots=True)
class DamageSkillEffectSpec:
    damage_type: DamageType
    coefficient: float = 1.0


@dataclass(frozen=True, slots=True)
class ApplyStateSkillEffectSpec:
    state_id: str
```

统一类型：

```text
SkillEffectSpec
```

Resolver 只能根据 spec 类型产生已有 Effect：

```text
DamageSkillEffectSpec
→ DamageEffect

ApplyStateSkillEffectSpec
→ ApplyStateEffect
```

禁止核心代码按：

```text
skill_id
skill name
synthetic skill name
```

硬编码具体技能分支。

本阶段不要建立 RecoverSkillEffectSpec。

`RecoverEffect` 仍必须保持 Stage 5：

```text
DEFERRED
→ RECOVERY_SYSTEM_NOT_AVAILABLE
```

---

# 七、SkillRuntime 合同

推荐最小运行模型：

```python
@dataclass(slots=True)
class SkillRuntime:
    definition: SkillDefinition
    owner_id: str
    enabled: bool = True
```

职责：

```text
保存某携带者当前战斗中的技能绑定与最小运行事实
```

不要让 SkillRuntime：

```text
持有 BattleContext
持有 BattleSystems
持有 TargetSystem
持有 EffectExecutor
自己选择目标
自己消费 RNG
自己执行 Effect
自己修改兵力
自己写状态
```

不要新增：

```text
BattleContext.skills
UnitRuntime.skills
SkillRegistry
SkillCatalog
runtime_data: dict[str, Any]
```

Stage 6 测试中显式创建 SkillRuntime 即可。

---

# 八、SkillResolver 合同

建立独立：

```text
SkillResolver
```

不要把 resolve 行为塞进 SkillRuntime。

SkillResolver 只负责一次明确的 resolution attempt。

推荐唯一构造依赖：

```text
TargetSystem
```

运行时 RNG 只通过：

```text
BattleContext.random
→ RandomSystem
```

SkillResolver 不得依赖：

```text
EffectExecutor
DamageSystem
DamageResolutionSystem
TroopSystem
StateLifecycleSystem
StateRegistry
BattleSystems
```

推荐解析顺序：

```text
1. 检查 runtime.enabled
2. 解析 owner
3. 通过 TargetSystem 查询合法候选，不随机选择
4. 无合法目标 → NO_VALID_TARGET
5. 处理 activation_rate
6. 发动失败 → ACTIVATION_FAILED
7. 发动成功后再通过 TargetSystem 随机选目标
8. 按 effect_specs 声明顺序生成 Effect
9. 返回 SkillResolutionResult
```

Resolver 返回时不得产生实际战斗副作用。

---

# 九、SkillResolutionResult

建立类型化结果，至少支持：

```text
DISABLED
NO_VALID_TARGET
ACTIVATION_FAILED
RESOLVED
```

推荐：

```python
@dataclass(frozen=True, slots=True)
class SkillResolutionResult:
    skill_id: str
    owner_id: str
    status: SkillResolutionStatus
    target_ids: tuple[str, ...]
    effects: tuple[Effect, ...]
```

约束：

```text
DISABLED
→ target_ids = ()
→ effects = ()

NO_VALID_TARGET
→ target_ids = ()
→ effects = ()

ACTIVATION_FAILED
→ target_ids = ()
→ effects = ()

RESOLVED
→ Stage 6 当前模式下 target_ids 非空
→ effects 非空
```

不要创建大量 nullable 字段组成的万能 Result。

---

# 十、目标解析合同

Stage 6 只支持最小：

```text
SkillTargetMode.SINGLE_RANDOM_ENEMY
```

目标意图：

```text
SkillDefinition.target_mode
```

目标实际解析：

```text
SkillResolver
→ TargetSystem
```

禁止建立：

```text
SkillTargetSystem
复杂 Target DSL
随机友军
多目标
最低兵力
属性排序
强制目标
混乱 / 嘲讽 / 挑拨
```

除非当前 `STAGE6.md` 已明确要求，否则不要扩大目标模型。

---

# 十一、RNG 精确合同

必须严格实现并测试：

```text
runtime.enabled = False
→ DISABLED
→ 0 activation RNG
→ 0 target RNG

无合法目标
→ NO_VALID_TARGET
→ 0 activation RNG
→ 0 target RNG

activation_rate = 0.0
→ ACTIVATION_FAILED
→ 不调用 RandomSystem.chance()

activation_rate = 1.0
→ 直接成功
→ 不调用 RandomSystem.chance()

0.0 < activation_rate < 1.0
→ 恰好一次 context.random.chance(rate)

发动失败
→ 不进行随机目标选择

发动成功
→ 随机目标只能经过 TargetSystem
```

必须保持：

```text
候选唯一时不消费无意义 target RNG
```

同样：

```text
相同 seed
+ 相同战斗事实
+ 相同 resolution 调用顺序
→ 相同 activation decision
→ 相同 target_ids
→ 相同 Effects
```

以上 RNG 顺序属于 Stage 6 工程确定性合同，不要伪装成已确认官方结算顺序。

---

# 十二、Effect 生成合同

Damage spec 必须生成：

```text
DamageEffect(
    source_id = runtime.owner_id,
    target_id = selected target,
    damage_type = spec.damage_type,
    source_type = DamageSourceType.SKILL,
    coefficient = spec.coefficient,
    source_skill_id = definition.skill_id,
)
```

之后必须仍走：

```text
EffectExecutor
→ DamageResolutionSystem
→ DamageSystem
→ TroopSystem
```

ApplyState spec 必须生成：

```text
ApplyStateEffect(
    state_id = spec.state_id,
    owner_id = selected target,
    source_id = runtime.owner_id,
    source_skill_id = definition.skill_id,
)
```

之后必须仍走：

```text
EffectExecutor
→ StateLifecycleSystem
→ StateRegistry
```

Skill 层不得直接调用这些底层系统。

---

# 十三、多个 Effect 的顺序

必须保持：

```text
SkillDefinition.effect_specs
= tuple

SkillResolver 生成 effects
= 严格保持 declaration order
```

只把这一点作为 Stage 6 synthetic skill 的工程合同。

不要宣称这是所有真实官方战法的通用结算规则。

---

# 十四、Skill 与 EffectExecutor 的硬边界

Stage 6 最重要的集成测试之一必须证明：

```text
result = SkillResolver.resolve(...)
```

之后：

```text
troops 未改变
StateRegistry 未改变
```

只有调用：

```text
EffectExecutor.execute(...)
```

之后，才允许发生真正副作用。

禁止：

```text
SkillResolver 内部执行 EffectExecutor
SkillRuntime 内部执行 EffectExecutor
```

---

# 十五、BattleSystems 接入

推荐把 SkillResolver 加入 BattleSystems 组合根：

```text
TargetSystem
→ SkillResolver
```

不要注入：

```text
EffectExecutor
BattleSystems 本身
```

最终 SkillResolver 与 EffectExecutor 在 BattleSystems 中并列存在，不互相持有。

---

# 十六、BattleEngine / EventBus 红线

Stage 6 不自动运行技能。

不要修改 BattleEngine 加入：

```text
SkillResolver.resolve()
技能类型判断
技能 ID 判断
技能名称判断
主动 / 突击 / 指挥 / 被动 timing
```

这些属于 Stage 7 Trigger / Timing 设计。

EventBus 继续只记录已经发生的事实。

本阶段不要新增：

```text
SKILL_ACTIVATED
SKILL_RESOLVED
```

也不要让 EventBus 订阅事件后反向决定技能发动。

---

# 十七、只允许 synthetic/test skills

Stage 6 不录入任何真实战法。

测试至少使用：

```text
synthetic.weapon_damage
synthetic.disarm
synthetic.damage_and_disarm
synthetic.probabilistic_damage
```

这些定义只能存在于测试 / fixture。

生产代码不得认识这些字符串。

必须验证：

```text
Synthetic Weapon Damage
→ SkillResolver
→ DamageEffect
→ EffectExecutor
→ DamageResolutionSystem

Synthetic Disarm
→ SkillResolver
→ ApplyStateEffect
→ EffectExecutor
→ StateLifecycleSystem

Synthetic Damage And Disarm
→ one resolution
→ ordered multiple Effects

Synthetic Probabilistic Damage
→ activation_rate
→ deterministic RNG contract
```

---

# 十八、测试要求

至少新增或等价覆盖：

```text
tests/test_skill_definition.py
tests/test_skill_runtime.py
tests/test_skill_resolver.py
tests/test_stage6_integration.py
tests/test_stage6_architecture.py
```

必须覆盖：

```text
SkillDefinition immutable / slots / validation
SkillRuntime independence
enabled runtime
0% / 100% activation no RNG
probabilistic activation exactly one chance
no valid target no RNG
activation failed no target RNG
same seed reproducibility
target only via TargetSystem
resolver produces Effects without side effects
Damage skill routes through EffectExecutor
State skill routes through EffectExecutor
multi-effect order
BattleEngine remains generic
RecoverEffect remains DEFERRED
```

---

# 十九、架构静态测试

优先使用：

```text
AST Import / ImportFrom 检查
AST Call / Attribute 检查
行为集成测试
```

不要仅用全文字符串搜索注释。

Stage 6 skill modules 至少禁止导入：

```text
troop_system
damage_system
damage_resolution_system
state_registry
state_lifecycle_system
effect_executor
battle_systems
random
```

同时继续确保：

```text
除 random_system.py 外
battle_core 生产代码不得直接 import Python random
```

架构测试还应检测 Skill 层没有：

```text
*.troops =
*.troops +=
*.troops -=
context.states.add(...)
context.states.remove(...)
```

---

# 二十、禁止范围膨胀

本次施工不得实现：

```text
TriggerSystem
TimingSystem
RecoverySystem
真实战法目录
SkillCategory lifecycle
SkillRegistry
SkillCatalog
BattleContext.skills
UnitRuntime.skills
计穷
伪报
威慑
洞察
持续伤害
反击
群攻
连击
复杂命中系统
Modifier Pipeline
装备系统
```

如果某个 Stage 6 测试似乎“必须”依赖这些能力，先重新检查设计，通常意味着 Stage 6 已经越界。

---

# 二十一、推荐施工顺序

严格按：

```text
1. 重新读取 main 最新状态
2. SkillDefinition / SkillEffectSpec
3. Definition tests
4. SkillRuntime
5. Runtime tests
6. SkillResolver / Result
7. activation / target / RNG tests
8. synthetic skills，仅 tests
9. Skill → Effect 无副作用测试
10. Skill → EffectExecutor 集成测试
11. BattleSystems 接入
12. __init__.py 导出
13. AST / architecture tests
14. Stage 1～5 全回归
15. pytest -q
16. python demo.py
17. GitHub Actions
```

---

# 二十二、验证与 GitHub 要求

施工完成后必须实际执行：

```text
pytest -q
python demo.py
```

并确认：

```text
GitHub Actions = success
```

不要只说“理论上应该通过”。

如果 CI 失败：

```text
读取实际失败日志
定位根因
修复
重新运行
```

不得通过删除测试、降低断言或绕过冻结边界让 CI 变绿。

建议在独立 Stage 6 工作分支施工，例如：

```text
stage6-skill-runtime
```

不要在未完成验证前把 Stage 6 标成 FROZEN。

---

# 二十三、本次施工完成后必须输出

最终报告至少包含：

```text
1. 实际施工起点 main SHA
2. 工作分支 / 最终提交 SHA
3. 新增文件
4. 修改文件
5. 实现的 Stage 6 能力
6. 未实现且明确 DEFER 的能力
7. 新增测试及覆盖内容
8. pytest -q 实际结果
9. python demo.py 实际结果
10. GitHub Actions 实际结果
11. 是否发现 Stage 1～5 回归
12. 是否存在 BLOCKER / MAJOR / MINOR
13. 是否满足进入独立 Stage 6 FINAL AUDIT 的条件
```

---

# 二十四、停止条件

本 Prompt 的任务是：

```text
完成 Stage 6 功能施工
+
测试
+
CI 验证
+
施工后架构自检
```

本次不要提前创建：

```text
STAGE6_FINAL_AUDIT.md
```

也不要直接宣布：

```text
Stage 6 = FROZEN
```

只有后续独立最终审计、必要修复、再次审计，并且最终审计文件进入 `main` 且对应 CI success 后，Stage 6 才能正式 FROZEN。

如果本次施工与测试全部完成且无 BLOCKER / MAJOR，最终只报告：

```text
Stage 6 implementation complete
Ready for independent final audit
```
