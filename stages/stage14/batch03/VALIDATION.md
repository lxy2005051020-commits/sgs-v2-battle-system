# Batch03 验证记录

日期：2026-10-05。分支：`stage14-troop-batch-03`。
父提交：`6dc5e169d7485231976685b98833703778c6e5c8`。

| 检查 | 结果 |
|---|---|
| 本批行为回归 | 42 passed |
| 本批 + 前两批 + 西凉铁骑 | 161 passed in 0.93s；focused.log |
| 全量 pytest | 1905 passed in 10.04s；full.log |
| demo.py | exit 0；demo.log |
| Stage13-D1 frozen owner 哈希及 adversarial | PASS；11 passed；AUDIT_STAGE13_D1.json |
| 全新进程正式注册入口 | 20099 / 20125 对应模块 SKILL 与 factory 一致；共七项 |
| git diff --check | PASS |

验证覆盖全队进阶与效果、携带者/主将分离、陈到/张郃主将与副将分支、物理执行者
属性和攻心恢复归属、随机单体可区别于普攻目标、援护/混乱的目标继承、概率失败、
来源禁用/威慑/恢复、副将来源死亡后监听器保留、缴械/震慑阻断、继承目标死亡不改选、
主将致死终结截断、张郃概率连击真实 grant 与两次普攻上限、Engine 自动安装和清理、
缺少槽位/兵种不符的 mutation 前拒绝、无效概率参数拒绝。

```powershell
python -m pytest -q tests/test_stage14_troop_batch03.py tests/test_stage14_troop_batch02.py tests/test_stage14_troop_batch01.py tests/test_stage14_troop_xiliang.py
python -m pytest -q
python demo.py
python scripts/audit_stage13_d1.py --output stages/stage14/batch03/AUDIT_STAGE13_D1.json
```

冻结检查使用项目既有 harness，不是本批第三方独立审阅。全部行为测试属于工程
验证，不替代真实游戏战报证据；触发细序、公式额外缩放、来源链与 TargetPolicy
持有者口径等待裁决项见上一级 `BATCH03_BAIER_DAJI.md`。
