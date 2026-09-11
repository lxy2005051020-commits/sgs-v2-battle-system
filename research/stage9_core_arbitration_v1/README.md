# Stage 9 核心问题域实证研究与底层裁决规范 (v1)

> **数据基线**：全盘扫描 32,660 份真实战斗战报（JSON 全量事件流，逾 1,400 万条原始战斗事件）。  
> **研究目的**：针对 Stage 9 反应式、目标重定向与派生伤害机制（连击、群攻、反击、分担、分摊、铁索连环、援护、混乱、嘲讽），彻底厘清多状态共用的 12 项底层裁决问题，避免各状态在实现时各自发明规则导致集成爆炸。

---

## 目录结构

1. **[STAGE9_CORE_ARBITRATION_RULES.md](STAGE9_CORE_ARBITRATION_RULES.md)**
   - **全景总报告**：12 项公共裁决规则全景、四类伤害语义（SPLIT/TRANSFER/COPY/FEEDBACK）、生命周期流水线、递归许可矩阵、短路铁律及 Stage 9 架构重构建议。

2. **[RESEARCH_Q1_Q2_Q11_TARGET_RESOLUTION.md](RESEARCH_Q1_Q2_Q11_TARGET_RESOLUTION.md)**
   - **问题 1、问题 2、问题 11 专项实证**：
     - 目标选择与重定向总顺序：混乱 100% 压制嘲讽；援护高于嘲讽；混乱攻击友军可被援护。
     - 攻击目标（Intended Target）与伤害承受者（Resolved Target）解耦：战报 4 步原子流、群攻以援护者为基准、反击由援护承伤者触发、突击与控制 100% 灌在援护者身上。
     - 同类状态冲突：双援护排斥、双嘲讽排斥（先占独占）。

3. **[RESEARCH_Q3_Q4_Q10_ATTACK_LIFECYCLE.md](RESEARCH_Q3_Q4_Q10_ATTACK_LIFECYCLE.md)**
   - **问题 3、问题 4、问题 10 专项实证**：
     - 普通攻击完整生命周期：`声明 -> 援护 -> 伤害 -> 急救回调 -> 群攻 -> 反击 -> 突击 -> 连击检查点`（群攻严格先于反击，反击严格先于突击）。
     - Reaction Queue 模式：阶段优先制（Phase Priority） + 局域即时内联回调（Inline Callbacks）。
     - 死亡短路规则：攻击者反击致死短路突击与连击第二击；首杀主将直接终战；援护者阵亡普攻闭合不回退；铁索连环为原子性遍历循环。

4. **[RESEARCH_Q5_Q6_Q7_Q8_DAMAGE_DERIVATION.md](RESEARCH_Q5_Q6_Q7_Q8_DAMAGE_DERIVATION.md)**
   - **问题 5、问题 6、问题 7、问题 8 专项实证**：
     - 递归许可矩阵：反击不触发反击、群攻不触发群攻、连环不二次连环、分担不嵌套分担、连击非无限连。
     - 派生分类与数学语义：分担严格为 SPLIT（总量守恒），铁索连环严格为 FEEDBACK（原目标不减等额广播）。
     - 理论伤害 vs 实际兵力损失：致死过量时不分担溢出伤害；致死一击不向连环队友广播；群攻基数继承暴击与增伤。
     - Damage Pipeline 重入：反击为完整独立 DamageRequest；群攻副目标独立受规避/抵御并可被分担；铁索连环不重算智力防抗但独立受规避/抵御；分担直接扣切片数值但可触发急救。

5. **[RESEARCH_Q9_Q12_PROVENANCE_AND_RNG.md](RESEARCH_Q9_Q12_PROVENANCE_AND_RNG.md)**
   - **问题 9、问题 12 专项实证**：
     - 事件身份与 Provenance：无显式 parent_id，依靠定界符（723/734/735/725/724/736/733）结合 DFS 调用栈体现层级，日志显式固化来源信息。
     - RNG 消耗与确定性：无选择不消耗 RNG（候选集为 1 跳过 PRNG）；连击第二击必定重新独立索敌并消耗 1 次 PRNG（实测 46.05% 同目标、53.95% 不同目标）；混乱为 JIT 即时判定。
