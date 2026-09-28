# Stage12 690089「洞察」Runtime Integration Handoff

Date: 2026-09-27  
Round: `STAGE12_690089_INSIGHT_RUNTIME_INTEGRATION`  
Status: **IMPLEMENTED_PENDING_RUNTIME_AUDIT**  
Runtime Freeze: **NOT YET AUTHORIZED**

## 1. Repository lock

Implementation started from:

- Battle main: `d8e35ecab997135caf3960df961e534313f8473e`
- Research main: `e18ae56a4db5662b87458dfa8fdff25dcdd8053b`

Research repository was read-only throughout this integration. No Research reopen was required.

## 2. Authority

The gameplay authority is the frozen Research contract:

`states/functional/insight/MECHANISM_CONTRACT.md`  
Version: `v0.4-frozen`

The implementation also consumes the frozen Stage12 Shared Foundation design/default governance, including PD-INS-001, PD-INS-002 and AR-SF-01.

## 3. Runtime architecture

690089 is integrated through the one canonical `BattleSystems` graph.

Mechanism-specific adapters are registered into:

- `StateAdmissionPolicy`
- `StateConflictPolicy`
- `StateEffectivenessPolicy`
- `StateApplicationCoordinator` dependency-delta seam

There is no `Stage12InsightRuntime`, no second state registry and no second effectiveness policy.

Incoming protected controls and already-resident protected controls deliberately use different owners:

```text
incoming protected candidate
-> StateAdmissionPolicy
-> reject before conflict/generation/mutation

resident protected state
-> explicit StateNode dependency on Insight
-> StateEffectivenessPolicy
-> SUPPRESSED while Insight is EFFECTIVE
```

## 4. Exact ordinary protected set

The explicit protected set is:

```text
690101 SILENCE / EXHAUSTION / 计穷
690102 DISARM / 缴械
690103 CONFUSION / 混乱
690104 WEAKNESS / 虚弱
690105 HEALING_BAN / 禁疗
690106 TAUNT / 嘲讽
690108 PROVOKE / 挑拨
690109 EQUIPMENT_DISABLE / 破坏
690111 STUN / 震慑
```

The ordinary-Insight negative exclusions are explicit:

```text
690107 FALSE_REPORT / 伪报
690222 INTIMIDATION / 威慑
690110 CAPTURE / 捕获
```

No category-wide `CONTROL`, negative-state or debuff fallback defines this set.

## 5. Admission and conflict ordering

Effective Insight rejects protected candidates at `StateAdmissionPolicy`.

The rejection occurs before:

- `StateConflictPolicy`
- state refresh/replace logic
- generation allocation
- physical registry mutation
- dependency commit
- `STATE_APPLIED` publication

A discriminator covers an already-resident protected state to prove an incoming same-state candidate cannot reach REFRESH while Insight is effective.

## 6. PD-INS-001 RNG

Insight owns zero RNG.

For probabilistic sources:

```text
source-owned probability draw
-> candidate
-> Insight admission rejection
```

For deterministic sources, Insight adds no synthetic draw.

Seed parity tests cover both paths.

## 7. PD-INS-002 reapplication

Any PRESENT Insight rejects incoming Insight reapplication, including a PRESENT-but-SUPPRESSED Insight.

The existing Insight:

- remains the same physical instance;
- keeps the same application generation;
- keeps its lifetime;
- is not refreshed;
- does not allocate a new generation;
- consumes no Insight-owned RNG.

## 8. Resident suppression, resume and lifetime

Applying effective Insight to an already-resident protected state creates an explicit dependency edge:

```text
protected StateNode -> Insight StateNode
```

The protected state remains resident and its lifetime continues.

Insight suppression never calls state removal.

When the final effective Insight suppression cause disappears and the protected state is still live:

```text
SUPPRESSED -> EFFECTIVE
```

This is a resume of the same state instance and generation, not refresh or reapplication.

If the protected state expires while suppressed, later Insight expiry cannot recreate or resume it.

If Insight and the protected state expire in the same lifecycle envelope, the Foundation batch-removal path emits no transient false resume.

Multiple suppression causes compose through canonical cause sets. Removing Insight while another cause remains does not emit `STATE_RESUMED`.

## 9. AR-SF-01 Stage9 migration

Production Stage9 Confusion and Taunt operational queries now consume the canonical state-effectiveness truth.

The narrow authority migration is:

```text
Confusion resident
+ effective Insight
=> Confusion remains resident but is operationally ineffective
```

When Insight ends before Confusion expiry, the original Confusion instance resumes and Stage9 arbitration can observe it again.

Legacy isolated Stage9 fixtures without an injected Shared Foundation policy retain their compatibility fallback; production `BattleSystems` uses the canonical policy.

## 10. Stage11 pairs

No Stage11 contract is reopened.

Existing Stage11 consumers already read canonical effectiveness for:

- DISARM
- STUN
- WEAKNESS
- HEALING_BAN

690089 tests prove:

- suppressed DISARM no longer blocks normal attack admission;
- suppressed STUN does not consume `remaining_blocks`;
- suppressed WEAKNESS no longer zeroes real DamageSystem output;
- suppressed HEALING_BAN no longer prevents real RecoverySystem recovery;
- both resume through the pre-existing Stage11 seams when Insight ends.

Stage11 Reopen Required remains **NO**.

## 11. Stage12 pair boundaries

For not-yet-integrated Stage12 mechanics, tests cover only the Insight side of the frozen boundary.

Protected synthetic/resident state IDs:

- 690101 EXHAUSTION
- 690108 PROVOCATION
- 690109 SABOTAGE

Negative ordinary-Insight discriminators:

- 690107 FALSE_REPORT
- 690222 INTIMIDATION
- 690110 CAPTURE

No gameplay behavior for those six mechanisms is implemented by this round.

## 12. Foundation seam used by the first real state

The frozen StateApplicationTransaction design already allowed a mechanism-owned dependency delta. The generic runtime now exposes an atomic multi-replacement dependency commit seam:

- prospective graph built before mutation;
- complete prospective topology validated for cycles;
- one atomic graph replacement commit after lifecycle mutation;
- transition capture includes external affected consumers;
- canonical transition coordinator emits committed state effectiveness facts.

This is a generic Foundation seam, not an Insight-owned second graph.

## 13. Executable validation

Corrected pre-integration full-suite baseline: **1134 passed**.

Validated implementation checkpoint:

- SHA: `ae213863a52a8e4c19b5169939fecb700ac8bfd8`
- GitHub Actions run: `36310190828`
- pytest: **1174 passed**
- demo: **PASS**
- executable delta: **+40 test nodes**

The full suite includes Stage9, Stage10, Stage11 and Shared Foundation Round1-4 regressions.

## 14. Static architecture audit

Executable/static review confirms:

- no direct registry mutation in the Insight adapter;
- no random source in Insight adapters;
- no direct event publication from Insight adapters;
- no lifecycle remove for suppression;
- no lifecycle refresh for resume;
- no generic negative/control/debuff immunity fallback;
- no query-time full-registry scan to derive resident suppression;
- explicit dependency edges use `DependencyEvaluationSupport`;
- graph changes retain pre-commit cycle validation;
- one canonical `StateEffectivenessPolicy`;
- no gameplay implementation for the other six Stage12 mechanisms.

## 15. Files created / updated

Production:

- `sgs_v2/battle_core/insight_integration.py`
- `sgs_v2/battle_core/dependency_evaluation.py`
- `sgs_v2/battle_core/state_application.py`
- `sgs_v2/battle_core/battle_systems.py`
- `sgs_v2/battle_core/stage9_state_runtime.py`

Tests:

- `tests/test_stage12_690089_insight.py`

Governance:

- `stages/stage12/STAGE12_SHARED_FOUNDATION_IMPLEMENTATION_STATUS.md`
- `stages/stage12/STAGE12_690089_INSIGHT_RUNTIME_INTEGRATION.md`

## 16. Implementation blockers

```text
NONE
```

No frozen contract/Foundation incompatibility was found that requires Research reopen.

## 17. Current gates

```text
Stage11 Runtime = FROZEN
Stage11 Reopen Required = NO

Stage12 Research = 7 / 7 FROZEN
Stage12 Shared Foundation Design = FROZEN
Stage12 Shared Foundation Implementation = COMPLETE

690089 INSIGHT Gameplay = IMPLEMENTED_PENDING_RUNTIME_AUDIT
690089 INSIGHT Runtime = NOT YET FROZEN

Stage12 Runtime Frozen = 0 / 7
Other Stage12 gameplay implementations in this round = 0
```

## 18. Next

The only authorized next step is:

```text
690089 INSIGHT Independent Runtime Freeze Audit
```

Only that audit may advance:

```text
690089 Runtime = FROZEN
Stage12 Runtime Frozen = 1 / 7
```

Do not enter 690101 EXHAUSTION Runtime Integration before that gate passes.
