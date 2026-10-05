# Batch01 验证记录

日期：2026-10-05。分支：`stage14-troop-batch-01`。
基线：`766eeaac16e227c9eee250e452403020f16e11ea`。

最终代码验证：

| 检查 | 结果 |
|---|---|
| 本批新增行为回归 | 39 项，全部 PASS |
| 本批 + 西凉铁骑专测 | 78 passed in 0.79s |
| 全量 pytest | 1822 passed in 8.18s |
| demo.py | exit 0，输出见 demo_smoke.log |
| scripts/audit_stage13_d1.py | PASS；既有冻结 owner 哈希全部匹配；11 项 adversarial PASS |
| 全新 Python 进程的生产注册检查 | 20097 / 20075 / 20098 唯一注册；新增两定义与模块 SKILL 一致 |
| git diff --check | PASS |

复现命令（项目根目录，使用已装依赖的 Python）：

```powershell
python -m pytest -q tests/test_stage14_troop_batch01.py tests/test_stage14_troop_xiliang.py
python -m pytest -q
python demo.py
python scripts/audit_stage13_d1.py --output AUDIT_STAGE13_D1.json
```

Stage13-D1 审计是项目既有独立 harness，对本次冻结边界复用有效；它不是
白马义从/虎豹骑的独立审阅，也不能替代战法机制研究或真实战报留出验证。
本次没有远端 PR CI、主线合并或战法独立合同 FROZEN 声明。

来源快照保留 20 条原 CSV 记录（每战法 10 个等级），实现范围为满级基础分支。
统领缩放及白马统领时长边界见上一级 BATCH01_BAIMA_HUBAO.md。
