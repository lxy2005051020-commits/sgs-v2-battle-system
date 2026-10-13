# 形一阵 PR #72 合并前审计

日期：2026-10-13。基线 `c4724e7abef1f7e99eca65c9e09c4074fb43dd92`；
审查原实现提交 `5ff3abc801d0d1ee5a9f1982806cde7fd4426f16` 及本次新增审计测试与文档。
发布入口：[PR #72](https://github.com/lxy2005051020-commits/sgs-v2-battle-system/pull/72)。

结论：工程审计 PASS；未发现阻塞合并的实现缺陷。合并仍要求最终 PR head 的远端CI
`completed/success`，合并完成报告还要求 merged-main CI 成功。
本审计由同一执行代理进行代码复核和独立对抗场景验证，没有第二名人工或独立代理审阅。
测试场景复用现有阵容fixture，新增断言基于公共行为及冻结框架合同；不属于玩法实证。

## 已核对内容

| 审计项 | 结果 |
|---|---|
| 静态来源 | 正式22039、FORMATION、十级原始行、源路径与SHA256保留；仅实现Lv10 |
| 装备条件 | 仅比较三人INHERENT槽类型；缺失明确报错，已知不相同无效果 |
| 目标身份 | 最高属性只属于携带者；双向伤害曲线只作用于另外两名队友 |
| 并列属性 | 用户确认武力→智力→统率→速度，全部11种并列组合仅提高一项60 |
| 回合曲线 | 用户确认R1～3双向-30%/-20%/-10%；R4起每回合OUT+16%、IN+1% |
| 公共组件 | RoundDamageRateParams无战法ID耦合、无RNG、无状态/兵力直接改写 |
| 伤害聚合 | 同侧+16%与另一来源+25%进入既有加算池得到1.41；OUT与IN两池相乘 |
| 来源隔离 | 双方各携形一阵时均有独立来源；一方携带者阵亡不删另一方和其他战法贡献 |
| 生命周期 | 沿用EffectExecutor、StateEffectivenessPolicy、依赖图、DefeatCleanupPort；重复查询不堆状态 |
| 停用语义 | 安装前enabled=False不准入；安装后该标志不撤回已安装状态，重新启用不重复生成 |
| 进度文档 | 修正README“五阵法/形一未实现”的漂移，当前registry为六项 |
| 冻结owner | 原21个Stage13-D1冻结核心文件哈希一致；没有改变生命周期/伤害/目标核心实现 |

新增检查见[对抗测试](../../tests/test_stage14_xing_yi_merge_audit.py)和
[测试输出](xing_yi_evidence/merge_adversarial_tests.txt)。
回合1～20多次查询无新状态和RNG消耗；兵刃/谋略均测试双阵法互动。
测试双方同速时显式提供attacker_team_id，不绕过正式准备阶段排序规则。

## 保留OPEN

最高属性按发动安装时有效属性快照仍为暂定模型；Lv1～9未实现。
死亡/净化/停用细节、准备阶段round=0的首回合修正可见性、当前客户端版本及原始战报逐事件对照
没有因此升级为客户端实证冻结。用户授权的回合曲线、并列优先级与上述假设分别记录。

## 验证与合并门槛

原head PR CI `38417402243` 已completed/success，含全量2512、demo和D1/青州审计。
新增5项对抗检查PASS；包含新增检查的相关阵法专项175项PASS。
本次最终本地全量2517项PASS（13.92秒）。
最新全量、冻结审计与注册结果保存在[xing_yi_evidence](xing_yi_evidence/)。
不使用旧head的CI成功作为新head的合并许可；合并调用必须校验最终expected_head_sha。
