# 690092 SURE_HIT / 必中 — Stage11 Research Authority Bridge

Status: RESEARCH_FROZEN / RUNTIME_NOT_INTEGRATED  
Date: 2026-09-20

## 1. Purpose

本文件只负责把 Battle 仓库 Stage11 规划与外部 690092 必中 FROZEN research authority 连接起来。Battle 仓库不得复制维护第二份 current mechanism authority。

正式研究 authority：

- Repository: lxy2005051020-commits/sgs-state-mechanics-research
- Contract: states/functional/sure_hit/MECHANISM_CONTRACT.md
- Research Ledger: states/functional/sure_hit/RESEARCH_QUESTION_LEDGER.md
- Freeze Audit: states/functional/sure_hit/FREEZE_AUDIT.md
- Frozen research head: 313f1a71369683ca6eb8213a412c94506aa00372
- Freeze date: 2026-09-20

## 2. Current Battle-Repo Status

Research: FROZEN  
Runtime: NOT_INTEGRATED  
Strict completion: NO  
Stage owner: Stage11  
Production implementation: NOT AUTHORIZED BY THIS BRIDGE

## 3. Frozen Behavior Summary

Stage11 设计必须消费以下外部合同：

- 项目级 eligibility rule：凡是本来可以进入规避裁决的 Damage Instance，都属于必中可作用对象；
- 有效必中抑制该 DI 的可见 cfg134/cfg135 规避协议，规避不能阻止当前 DI；
- Sure-Hit × Resistance canonical true set = 22：抵御不能阻止当前 DI，但仍消费恰好 1 次；后续 modifier 仍可把最终兵损降到 0；
- hit-eligible multi-hit 按 Damage Instance 独立裁决；
- Sure-Hit 使用 per-DI current effective state，不允许 Action-start snapshot；
- 已有有效 Sure-Hit 时，新的 Sure-Hit application REJECT；同源重复施加不刷新、不延长；
- Redirect 先确定 Final Receiver，再基于 Final Receiver 的防御状态裁决；
- Chain Feedback 与标准 Damage Share 不创建新的 Hit/Sure-Hit re-adjudication；
- Provider-death dependency 是 source-defined；当前仅【国士将风】有 HIGH_CONFIDENCE 提前移除证据，不得泛化。

## 4. Runtime Integration Constraints

禁止：
- 按技能名硬编码哪些伤害“必中”；
- 把 Sure-Hit 做成 Action-start snapshot；
- 一个 cast 的首段命中结果共享给所有 DI；
- Sure-Hit 让 Resistance 不消费；
- Resistance 在有效 Sure-Hit 下阻止当前 DI；
- 把 Sure-Hit 表述为全额伤害 / 保证正兵损；
- 在 Chain Feedback / Damage Share Receiver 上重新做 Hit adjudication；
- 通用化“Provider 死亡即移除所有必中”；
- 允许第二个 Sure-Hit instance 叠加；
- reject 时刷新当前 Sure-Hit duration。

Stage11 必须复用正式 Hit / Damage rule 扩展点，不得为了 690092 改写 Stage8/9/10 已冻结所有权。
