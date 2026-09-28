# R8 战报日志事实与因果溯源三层模型报告 (v2 - Repaired)

> **研究基线 Commit**: `de80a4ec30fb3bf50220a719011478116bd34e5b` (main)  
> **数据文件**: `evidence/inspect_bf03_schema.py`  
> **核心任务**: 纠正虚构日志字段问题（BF-03），明确划分真实日志事实、重构因果模型与模拟器工程字段。

---

## 一、 战报原生日志事实 (LOG FACT)

全库扫描 200 份战报并提取所有 JSON 键名，实证确立三战战报事件的物理 Schema：

```json
{
  "key": "2_3_12",
  "event": {
    "cfg_id": 28,
    "desc": "[张飞]损失了兵力120",
    "full_desc": "<color=#ff0000>[张飞]</color>损失了兵力120",
    "args": ["张飞", 120],
    "args_raw": "...",
    "not_show": 0
  }
}
```

### 事实清单 (Grade A — FROZEN FACT)
1. **真实包含字段**: 包装层仅包含 `['event', 'key']`；内层字典仅包含 `['args', 'args_raw', 'cfg_id', 'desc', 'full_desc', 'not_show']`。
2. **绝对平铺结构 (Flat Sequence)**: 战报在物理上是由一维数组顺序平铺排列的事件流。
3. **不存在的虚假字段**: 原生战报中**不存在 `parent_id`、`root_action_id`、`call_depth`、`indent` 等任何层级树状字段**。

---

## 二、 因果重构模型 (RECONSTRUCTED CAUSAL MODEL)

由于战报不直接暴露父子关系，因果链条必须通过**定界符与时序上下文**进行重构推断：

### 1. 结构定界符的作用
- `cfg: 723 / 733`: 回合（Turn）与行动大块的开始与终结。
- `cfg: 734 / 735`: 战法发起与准备阶段的前后包裹界定。
- `cfg: 725 / 724`: 单个动作内部子事件流的进入与退出。
- `cfg: 736`: 动作异常中断（如单位阵亡）标志。

### 2. 重构机制说明
- 通过“谁在什么时候发起声明（cfg 7/9/11）”，以及紧随其后的子事件列表，可以高可信度地重构出“攻击 $\rightarrow$ 援护 $\rightarrow$ 扣血 $\rightarrow$ 急救 $\rightarrow$ 反击”的因果父子图谱。[Grade B]
- **官方内部实现定性**: 官方底层是通过 Call Stack 还是 Event Queue 驱动属于**官方内部实现未知 (UNKNOWN)**。禁止宣称“官方底层必定为 DFS 或 FIFO”。

---

## 三、 模拟器工程领域模型 (ENGINEERING MODEL)

为了在模拟器工程实现中完整追踪派生与防御递归，在 Stage 9 架构中引入以下专有工程字段（非官方日志字段）：

```python
class BattleEvent:
    # 模拟器内部工程溯源属性
    root_action_id: str        # 发起整串动作链的根源动作ID（如普攻声明ID）
    parent_event_id: str | None# 直接引发当前事件的父事件ID
    source_skill_id: int | None# 触发战法ID
    source_state_id: int | None# 触发状态ID
    reaction_depth: int        # 派生嵌套深度（用于防止无限递归）
    derivation_kind: str       # 派生类型: 'PRIMARY', 'CLEAVE', 'COUNTER', 'CHAIN', 'SHARE'
```

这些字段严格归属于模拟器内部运行时状态机，在输出官方格式战报日志时会被序列化为平铺的 `cfg_id + args`。
