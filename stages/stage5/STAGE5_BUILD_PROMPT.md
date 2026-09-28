# Stage 5 Effect 构建 Prompt

你现在要继续维护项目：

```text
三国志战略版战斗模拟器 V2
```

GitHub 仓库：

```text
lxy2005051020-commits/sgs-v2-battle-system
```

开始前必须重新读取目标分支最新代码，不得根据旧聊天记录猜仓库状态。

Stage 4 已完成最终审计并 FROZEN。Stage 5 的正式施工依据是仓库根目录：

```text
STAGE5.md
```

以及：

```text
stages/stage3/STAGE3.md
stages/stage4/STAGE4.md
stages/stage4/STAGE4_FINAL_AUDIT.md
PROJECT_ROADMAP.md
research/official_state_catalog_v1/
```

Stage 5 目标：

```text
Effect
→ EffectExecutor
→ BattleSystem
```

并建立：

```text
StateRuntimeParams
DamageResolutionSystem
```

必须坚持：

```text
Effect = 不可变意图数据
EffectExecutor = 类型路由
DamageSystem = 理论伤害计算
DamageResolutionSystem = 伤害落地协调
TroopSystem = 唯一兵力写入口
StateLifecycleSystem = 状态唯一正式写入口
RandomSystem = 唯一 RNG
EventBus = 事实记录器
BattleEngine = 通用流程推进器
```

第一批 Effect：

```text
DamageEffect
ApplyStateEffect
RemoveStateEffect
RecoverEffect
```

其中 RecoverEffect 在 RecoverySystem 尚未建立前只能返回 DEFERRED，不得直接调用 TroopSystem.restore()。

状态运行参数必须使用不可变强类型 StateRuntimeParams 子类，不得使用 `payload: dict[str, Any]` 作为正式运行时参数合同。

DamageEffect 和普通攻击必须共用 DamageResolutionSystem，不得复制 DAMAGE_PREVENTED / DAMAGE_DEALT / UNIT_DEFEATED 与实际扣兵逻辑。

施工完成后必须：

```text
pytest -q
python demo.py
GitHub Actions
```

全部通过，并执行 Stage 5 最终架构审计。发现 BLOCKER / MAJOR 时先修复后再审计，不得直接标记 FROZEN。
