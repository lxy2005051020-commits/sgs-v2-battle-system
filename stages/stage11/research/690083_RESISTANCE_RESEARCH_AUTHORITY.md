# 690083 RESISTANCE / 抵御 — Stage11 Research Authority Bridge

Status: RESEARCH_FROZEN / RUNTIME_NOT_INTEGRATED
Date: 2026-09-18

## 1. Purpose

本文件只负责把 sgs-v2-battle-system 的 Stage11 规划与已经冻结的外部 690083 抵御研究 authority 连接起来。

Battle 仓库不得复制并另行维护第二份 690083 current mechanism authority；正式机制正文位于：

- Repository: lxy2005051020-commits/sgs-state-mechanics-research
- Contract: states/functional/resistance/MECHANISM_CONTRACT.md
- Research Question Ledger: states/functional/resistance/RESEARCH_QUESTION_LEDGER.md
- Current corrected authority head: 5741751b2723243606d9e83be40c1df5b9395ab2
- Freeze date: 2026-09-18
- Evidence maturity: HIGH_CONFIDENCE

## 2. Current Battle-Repo Status

~~~text
Research: FROZEN
Runtime: NOT_INTEGRATED
Strict completion: NO
Stage owner: Stage11
Production implementation: NOT YET AUTHORIZED BY THIS RECORD
~~~

## 3. Frozen Behavior Summary

外部合同至少冻结：

- 普通攻击、已观察的四类战法直接伤害、六类 DOT Tick、Cleave 副目标、已观察 Counterattack Damage Instance 可进入抵御；
- 【连环计】铁索反馈接收端与标准 Damage Share 接收端不独立进入抵御；
- 抵御按独立 Damage Instance 进行可观察裁决；
- 同时具备规避与抵御资格时，EVASION BEFORE RESISTANCE；
- 规避成功时抵御不执行、不消费；
- 正常抵御成功使当前兵损归零并消费恰好 1 次；
- 必中使抵御不能阻止当前 Damage Instance 继续下游结算，但抵御仍消费恰好 1 次；canonical true set = 22，其中 1 例 downstream 最终兵损为 0；
- cfg204 暂时失效期间不防伤、不消费，cfg205 已观察到继续生效闭环；
- 已施加抵御不会因 source death 自动消失；
- 自然移除稳定锚定 Holder 自身行动开始，具体 duration 由 Source Authority 决定；
- 官方状态规则明确：同类效果不叠加，若武将已存在抵御状态，则新的抵御施加失效；
- 因此同源/异源、Old1/Old2 的 active-state reapplication 均不得叠加、覆盖或刷新既有抵御；
- 旧抵御消失后，后续合法新施加作为 Fresh Application 处理。

这只是导航摘要。如果本桥接文件与正式研究合同冲突，以外部 FROZEN Mechanism Contract 为唯一 authority。

## 4. Runtime Integration Rule

Stage11 实现必须消费正式冻结合同，而不是旧 minimum_usable skeleton。

特别禁止：

- 把“必中”实现成简单跳过 Resistance 对象，因为冻结研究观察到必中仍会让抵御次数减少；
- 把 cfg23 的“同等或更强”文案实现成层数强弱比较规则；顶层官方状态规则是“已有抵御则新施加失效”；
- 让规避成功后继续消费抵御；
- 让铁索反馈或标准 Share 接收端重复走 Resistance；
- 为了接入抵御而改写 Stage8/9/10 已冻结所有权。

任何内部对象、函数名、状态槽或 adjudication pipeline 都只能作为工程实现，不得标记成官方事实。
