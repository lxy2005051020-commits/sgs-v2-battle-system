# Batch02 验证记录

日期：2026-10-05。分支：`stage14-troop-batch-02`。
父提交：`7cf0620478e540d5859802b8d8c270112f813dea`。

| 最终检查 | 结果 |
|---|---|
| 本批新增行为回归 | 41 项 PASS |
| 本批 + 第一批 + 西凉铁骑专测 | 119 passed in 0.83s |
| 全量 pytest | 1863 passed in 7.85s |
| demo.py | exit 0；输出见 demo_smoke.log |
| Stage13-D1 冻结边界审计 | PASS；frozen owner 哈希全部匹配；11 项 adversarial PASS |
| 全新进程生产注册 | 20097 / 20075 / 20098 / 20100 / 20096；两新增 SKILL 与 factory 一致 |
| git diff --check | PASS |

新增行为覆盖：用户公式阈值、超过 100% 的系数、无额外取整、无效数字拒绝；
全队属性与兵种身份；开场一次性执行、默认双目标与王平全体/副将排除；
中毒真实伤害 R1–R3 与 R4 到期、携带者/主将来源区分、来源死亡后的冻结基础；
启动来源失效/死亡取消，已安装中毒的压制与恢复、旧 always-active 行为保持；
急救真实受击治疗、失败单次 RNG、来源快照、压制/恢复/到期；
非法准入和缺少智力不产生 mutation；自动 Engine 接入与最终清理；高顺空白占位。

复现命令：

```powershell
python -m pytest -q tests/test_stage14_troop_batch02.py tests/test_stage14_troop_batch01.py tests/test_stage14_troop_xiliang.py
python -m pytest -q
python demo.py
python scripts/audit_stage13_d1.py --output AUDIT_STAGE13_D1.json
```

最终实现保留原有架构、冻结清单与测试要求。Stage13-D1 审计是项目既有 harness，
不是本批独立第三方审阅；本批真实游戏机制证据范围及待审事项见上一级说明。
