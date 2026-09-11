# R8 事件事实、因果重建与 Provenance 模型研究报告 (v2)

> **研究基线 Commit**: `a38b992480488557741354a7a685e182f3d5f4ff` (main)  
> **核心任务**: 区分直接日志事实、因果重建模型与模拟器工程设计，避免武断宣称“官方就是 DFS”。

---

## 一、三层认知模型严格分层

### 1. 战报直接事实 (Log Facts)
- 战报 JSON 内部事件流为**完全平铺的线性数组**（Flat Sequence）。
- 事件对象内**绝无显式 `parent_id`、`root_action_id`、`call_depth` 或 `indent` 字段**。
- 日志通过 `cfg_id` 定界符标记生命周期边界，并在 `args` / `desc` 中显式固化 `source_unit`、`source_skill` 与 `source_state`。

### 2. 重建因果模型 (Reconstructed Causal Model)
- 通过定界符（Delimiters）与时间窗口，可以无歧义地将平铺序列重建为树状因果调用关系：
  - `cfg: 723`: 武将行动开始
  - `cfg: 734`: 属性快照 / 进入主动段
  - `cfg: 735`: 持续状态结算快照
  - `cfg: 725`: 伤害结算块闭环
  - `cfg: 724`: 恢复结算块闭环
  - `cfg: 736`: 阵亡处理闭环
  - `cfg: 733`: 武将行动结束

### 3. 模拟器工程设计 (Simulator Engineering Model)
- 在 Stage 9 架构中，推荐在上下文对象中显式维护：
  ```python
  @dataclass(frozen=True)
  class ActionProvenance:
      root_action_id: str
      parent_event_id: str | None
      source_unit_id: str
      source_skill_id: str | None
      source_state_id: str | None
      derivation_kind: DerivationKind
  ```
- 这样既可在模拟器内部实现精确的因果溯源与递归防线，又可在向外发布事件流时自然展平为符合三战规范的平铺日志。
