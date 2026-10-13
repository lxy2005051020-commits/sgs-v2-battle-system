# 潜龙阵合并前审计

日期：2026-10-13；[PR #73](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/73)。
基线main：`0e8a9ed223e918bc7872e67e88d2102e08cdab2c`。
首个发布head：`23fe2318a05cb539b9ef48bc480be6b0e0032ac0`，其文件树
`c48190fc21266246b5197a36eae90f48ec7293a2`与本地实现提交完全一致。

审计方法：本代理复核远端PR差异、独立对抗测试文件及冻结哈希检查；
不是第二位人工审查者，也未开展客户端原始战报机制验证。

## 结论

审计PASS：未发现阻止本次工程模型合并的缺陷。潜龙阵Lv1–10数值来自逐级静态行；
三阵营条件、真实主副将位置、任意已装备槽主将效果存在性、固定属性快照与双向伤害修饰
均走声明及现有owner。通用接口不硬编码潜龙阵ID、不改变编队身份、不另造伤害/兵力执行器。
源数据和文档明确区分用户确认模型、2026-08-08静态来源与未实证冻结边界。

新增[独立对抗测试](../../tests/test_stage14_qian_long_merge_audit.py)覆盖：

- 突击继承友军目标时两种效果保持同一目标、无重选和额外RNG。
- 开场COMMAND主将分支按资格启用，普通分支仍生效。
- 相同state_id跨自带与学习槽时按真实来源区分，主将停用不误伤普通属性效果。
- INHERENT / LEARNED_1 / LEARNED_2三个槽的主将效果均触发较低属性分支。
- 潜龙阵资格覆盖及提供者阵亡不改变`BattleContext.commander_of()`的真实主将。

七项对抗测试通过；21个冻结核心文件哈希一致，D1对抗11项通过。
本次审计后全量 **2605 passed**（78.51秒）。
完整测试和结果见[对抗输出](qian_long_evidence/merge_adversarial_tests.txt)、
[全量输出](qian_long_evidence/full_regression.txt)、[冻结审计](qian_long_evidence/frozen_owner_audit.json)。

首个head的PR CI [38422680599](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38422680599)
与push CI [38422664536](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/actions/runs/38422664536)
均已`completed/success`。本审计补充提交仍需等待其自己的PR CI成功才可合并；
合并结果与merged-main CI以GitHub的实际状态为准，不预写成功。

## 保留边界

接口声明是权威输入，未声明的真实武将主将分支不会自动产生。开场瞬时主将伤害/恢复
与专属分支独立目标合同保持fail-closed；公共状态事件微时序、净化规则、死亡后的客户端细节
仍OPEN。基础四维快照在潜龙阵所有效果前读取，属性增量固定；这是本次显式工程口径。
