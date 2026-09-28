# 基础谋略伤害公式 V1

> 状态：记录当前仓库 Stage 2 已实现的基础谋略候选模型。
>
> 这不是官方公开公式，也不是已验证的服务器源码。当前实现是在已有战报逆向候选基础伤害框架中，将属性对抗切换为智力 vs 智力；本文不额外声称已经独立恢复了官方谋略伤害公式。

## 当前实现边界

基础谋略伤害由 `StrategyBaseDamageFormula` 负责，并通过：

```text
DamageType.STRATEGY
        ↓
StrategyBaseDamageFormula
```

进入 `DamageSystem`。

它只负责 **100% 基础谋略伤害**。以下内容不属于基础公式：

```text
DamageRequest.coefficient
增伤 / 减伤
会心 / 奇谋
具体战法类型
击杀封顶
```

其中 `coefficient` 必须在基础伤害计算完成之后由 `DamageSystem` 处理；击杀封顶只由 `TroopSystem.apply_damage()` 处理。

## 属性对抗

与基础兵刃伤害的武力 vs 统率不同，当前基础谋略实现使用：

```text
攻击方最终 intelligence
vs
防守方最终 intelligence
```

双方智力均通过 `AttributeSystem.get_intelligence()` 读取。若任一单位没有可用的 `intelligence`，当前实现拒绝计算谋略基础伤害，而不是偷偷回退到武力、统率或固定值。

## 与兵刃基础框架共享的层

当前仓库实现复用 `WeaponBaseDamageFormula` 已有的基础框架，因此共享：

```text
当前出手兵力 N
        ↓
完整 F(N) 查表
        ↓
等级缩放
        ↓
属性对抗（谋略为 intelligence vs intelligence）
        ↓
兵种克制层
        ↓
士气层
        ↓
随机层
        ↓
低伤害下限
        ↓
base_damage
```

`F(N)` 与兵刃伤害使用同一张完整运行时查表：

```text
data/normal_attack/troop_function_table_1_10000.csv
```

当前表支持 `N=1..10000`。随机层继续只通过 `BattleContext.random / RandomSystem` 取得，保证相同配置和相同 seed 的可复现性。

## coefficient 的位置

谋略基础伤害完成后，统一进入 `DamageSystem`：

```text
base_damage
    ↓
× DamageRequest.coefficient
    ↓
scaled_damage
    ↓
final_damage
```

因此 `StrategyBaseDamageFormula` 不知道具体战法名称，也不负责战法倍率。

## 兵力边界

`DamageSystem` 只返回理论伤害。例如：

```text
目标剩余兵力 = 100
DamageResult.final_damage = 800
```

理论伤害仍保持 `800`。随后：

```text
TroopSystem.apply_damage(target, 800)
```

才把实际损失封顶为 `100` 并修改目标兵力。

## 不做的推断

Stage 2 不根据当前实现继续猜测以下规则：

```text
奇谋概率与倍率
谋略战法分类修正
状态增减伤
具体战法专属公式
未验证的额外随机层
```

这些都需要独立证据和后续系统边界，不能为了让文档显得更“完整”而写进基础公式。
