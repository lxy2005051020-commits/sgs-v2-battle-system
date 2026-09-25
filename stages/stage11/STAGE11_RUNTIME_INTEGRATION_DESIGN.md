# Stage11 Runtime Integration Design

Status: **DESIGN FROZEN**  
Design input Battle HEAD: `fa94a92374ac69af00f54397806df04ebcef535a`  
Design input Research HEAD: `d1b6c74b352de373fb46c99b546e970eaaf1f77e`

## 1. Design objective

Map every Stage11 research rule to one runtime owner, one code path and one test surface without moving Stage7-10 authority into a state-id monolith.

The runtime pipeline is organized around typed owners:

```text
State lifecycle / provenance
    ↓
Primary Action Order
    ↓
Action / NormalAttack admission
    ↓
DamageInstance
    ├─ critical-family outcome latch
    ├─ hit arbitration: Evasion → Resistance, with Sure-Hit bypass semantics
    ├─ defense formula policy: Break Formation
    ├─ ordinary damage modifiers / reduction pool / See-Through
    ├─ Weakness legal-zero result
    ├─ Alert single-hit adjustment + charge consumption
    └─ Stage9 partition / troop-loss commit
         ↓
attacker recovery: Life Steal / Strategy Life Steal
         ↓
recipient recovery permission: Healing Block
```

No Stage11 state owns target selection, troop mutation, Stage9 partition math, death finalization, or Stage10 persistent scheduling.

## 2. Canonical integration matrix

| State | Research authority | Runtime owner | Required extension | Design |
|---|---|---|---|---|
| 690086 分摊 | Stage9 freeze + DSTS9-B02 debt | DamagePartitionCoordinator | audit existing PROJECT_RUNTIME_DEFAULT | DESIGN_FROZEN |
| 690090 先攻 | Research contract | ActionOrderSystem + Stage11 lifecycle | deterministic tier/tie policy | DESIGN_FROZEN |
| 690091 遇袭 | mirror contract | ActionOrderSystem + Stage11 lifecycle | inverse tier, same tie policy | DESIGN_FROZEN |
| 690102 缴械 | Research contract | NormalAttack admission | per-admission JIT policy | DESIGN_FROZEN |
| 690104 虚弱 | Research contract | DamageInstance value gate | replace legacy early-prevention skeleton | DESIGN_FROZEN |
| 690105 禁疗 | Research contract | RecoverySystem | effective recipient-side gate | DESIGN_FROZEN |
| 690111 震慑 | Research contract | natural Action admission | preserve action-start/timeline work | DESIGN_FROZEN |
| 690082 规避 | Research contract | Stage11 hit arbitration | complement-product probability, per instance | DESIGN_FROZEN |
| 690083 抵御 | Research contract | Stage11 hit arbitration | charge consume semantics | DESIGN_FROZEN |
| 690092 必中 | Research contract | Stage11 hit arbitration | bypass evasion; resistance still consumes | DESIGN_FROZEN |
| 690093 破阵 | Research contract | DamageFormulaPolicy | source-local DEF/INT bypass | DESIGN_FROZEN |
| 690099 警戒 | Research contract | post-mitigation single-hit adjustment | FIFO batch + charge mutation | DESIGN_FROZEN |
| 690070 会心 | Research contract | CriticalResolution | WEAPON_DIRECT per-instance outcome | DESIGN_FROZEN |
| 690069 奇谋 | project mirror contract | CriticalResolution | final STRATEGY lane routing | DESIGN_FROZEN |
| 690221 看破 | Research contract | incoming reduction operand transform | cap-before-pierce, lane guard | DESIGN_FROZEN |
| 690094 倒戈 | Research contract | AttackerRecovery | actual-loss basis, per-source CEIL | DESIGN_FROZEN |
| 690095 攻心 | project mirror contract | AttackerRecovery | strategy-lane mirror | DESIGN_FROZEN |

## 3. Shared typed state parameters

Stage11 adds frozen dataclass parameter schemas rather than hiding behavior in string checks. Parameter schemas carry only runtime facts that providers are allowed to supply: probability/ratio, remaining uses, effective/suspended flag, action-start lifetime, source-dependency flag, provider provenance and strength where the research contract requires arbitration.

StateRegistry remains physical storage and StateLifecycleSystem remains the physical mutation owner. Stage11StateRuntime is a query/arbitration façade. It may request typed parameter replacement/removal through StateLifecycleSystem; it does not mutate StateRegistry directly.

## 4. Lifecycle and conflict policy

Action-start-lifetime states use a holder-local maintenance clock. Application before the holder's current action-start consumes that action-start; application after it begins counting at the next holder action-start.

The following observable non-stacking policies are admitted: FIRST_STRIKE, SURPRISE, RESISTANCE, SURE_HIT, DISARM ordinary active domain, WEAKNESS, HEALING_BLOCK and STUN. Incoming equal/equivalent applications are rejected without refresh. Unknown stronger-replacement domains remain explicit boundaries rather than guessed replacement rules.

EVASION, CRITICAL, STRATEGY_CRITICAL, LIFE_STEAL and STRATEGY_LIFE_STEAL may retain multiple independently sourced contributions where their contracts authorize contribution composition.

ALERT uses independent grant batches. Each StateInstance is one batch with its own provenance, remaining uses, reduction parameter and lifetime. FIFO means oldest eligible physical instance first.

Source-death behavior is parameterized only where the provider contract says source-dependent. No generic “applier died, remove all effects” rule is introduced.

## 5. Action order

The priority layer is:

```text
FIRST_STRIKE only > normal/both/neither > SURPRISE only
```

Within one layer:

1. effective speed descending;
2. exact cross-team tie: attacker team before defender team;
3. exact same-team tie: lineup position COMMANDER, DEPUTY_1, DEPUTY_2.

Random shuffle is forbidden.

A cross-team exact tie requires an authoritative attacker team identifier. Runtime reads `context.metadata["attacker_team_id"]`; if the battle has an exact cross-team tie and no authoritative attacker-team metadata, the runtime raises a contract-boundary error instead of inventing a side.

Order is snapshotted when `ActionOrderSystem.determine_order` runs. Mid-round state changes do not mutate the returned order.

## 6. Natural action permission

STUN owns natural action admission, not global rule-intent execution. Stage10 action-start persistent work, DOT/HoT and lifecycle maintenance remain reachable before the natural action is denied.

DISARM owns standard NormalAttack admission only. Each standard normal-attack attempt re-reads the current state and evaluates the provider-supplied per-admission block probability. Counterattack is not routed through this gate. A blocked host NormalAttack never reaches its downstream Assault opportunity. Combo #2 re-enters the same gate.

Unknown reflected/proxy DISARM admission timing is not encoded as a universal delay.

## 7. Damage pipeline

For each independent DamageInstance:

```text
participant/lifecycle validation
→ critical-family route by final damage lane
→ critical Bernoulli outcome latch
→ generic hit infrastructure
→ Stage11 Evasion
→ Stage11 Resistance
    - ordinary: consume one + legal zero/prevented hit
    - Sure-Hit: consume one but do not prevent
→ defense formula policy (Break)
→ base damage / coefficient
→ critical multiplier and ordinary modifier phases
→ incoming reduction pool
→ See-Through transform where authorized
→ Weakness legal zero
→ Alert threshold on post-ordinary-mitigation candidate
→ Alert reduction + consume one FIFO batch
→ central integerization
→ Stage9 partition
→ troop-loss commit
```

Crit-family routing is by final `DamageType`, never by ActionKind. Direct WEAPON instances use 690070; direct STRATEGY instances use 690069. Continuous damage reuses Stage10 application-bound frozen critical/formula context and does not reroll at tick time. Parent-derived Share/Chain/Cleave paths do not gain a second independent crit roll.

Weakness is not `DamagePrevention`. It yields `final_damage=0`, `prevented=False`, and a typed zero-loss cause so Stage9 partition and Stage10 zero-compatible observers remain reachable.

## 8. Break Formation

690093 emits only `DamageFormulaPolicy.IGNORE_RELEVANT_TARGET_DEFENSE` for authorized direct damage. WEAPON bypasses DEF, STRATEGY bypasses INT through the existing formula owner. Continuous application captures the formula policy in the Stage10 frozen basis. Parent-derived paths do not rerun the formula.

## 9. See-Through

The eligible incoming reduction operand is the sum of eligible percentage reductions, capped at 90%, then transformed:

```text
Rcap = min(Rtotal, 0.90)
Reff = Rcap * (1 - pierce_rate)
```

No rounding occurs inside 690221.

Authorized family classification is explicit. NORMAL_ATTACK and observed/authorized ASSAULT families can transform. Known no-invocation members return no transform. ACTIVE_SKILL, DOT/DELAYED and other unobserved families raise `ContractBoundaryViolation` if 690221 would otherwise be invoked. Silence is not an answer to an unknown contract.

ALERT is excluded from the See-Through operand.

## 10. Alert

ALERT reads the candidate after ordinary incoming mitigation and before its own reduction. If Evasion/Resistance/Weakness has already produced zero, no ALERT charge is consumed.

A trigger consumes exactly one use from the oldest eligible batch and applies only that batch's reduction.

Research boundaries become explicit runtime defaults, never “official facts”:

- exact threshold boundary: `candidate_damage > threshold` (**PROJECT_RUNTIME_DEFAULT**, 600 equality remains unobserved);
- positive-result integerization: no ALERT-local rounding; apply the factor as real-valued math and reuse the shared final damage integerization (**PROJECT_RUNTIME_DEFAULT**);
- partition order: ALERT transforms the parent DamageInstance before Stage9 partition; Share/Distribution direct troop loss never re-enters ALERT (**PROJECT_RUNTIME_DEFAULT** for the unobserved Share micro-order, aligned with frozen Stage9 direct-loss topology).

## 11. Attacker recovery

After the parent DamageInstance has committed actual troop loss, attacker recovery runs once per eligible active source.

WEAPON → 690094. STRATEGY → 690095.

Direct/assault/counter and multi-hit instances use that instance's actual target troop loss. Share uses `actual primary loss + actual shared loss` and the share direct loss does not create a second recovery trigger. Each source computes `ceil(basis * ratio)` independently, then RecoverySystem owns healing-block and target capacity.

For DISTRIBUTION, no 690094/690095 authority explicitly expands the Share-chain exception. Runtime therefore uses only the parent's actual target loss and does not add Distribution participant direct losses. This is an explicit **PROJECT_RUNTIME_DEFAULT / RESEARCH-DEBT BOUNDARY**, chosen as the minimum semantic extension and kept isolated for future reopen.

## 12. Healing Block

Recovery opportunity generation remains separate from recovery application. RecoverySystem checks the recipient's current effective HEALING_BLOCK at resolve time. Positive requests are intercepted to zero. A natural zero request is not reclassified as a positive HealingBlock interception.

No catch-up is added.

## 13. RNG

All Stage11 random decisions use `BattleContext.random`.

- Evasion: one aggregate complement-product probability roll per eligible independent DamageInstance.
- Critical/StrategyCritical: one Bernoulli per independently eligible direct instance.
- DISARM provider probability: one roll per standard NormalAttack admission when a probabilistic provider is used.
- probabilities 0 and 1 consume no random draw through the existing deterministic fast path where applicable.

No direct `random.*` calls are allowed outside RandomSystem.

## 14. Integerization

Stage11 does not introduce a second damage integerization utility. Existing central damage finalization remains authoritative except where a frozen contract explicitly calls CEIL for lifesteal.

Lifesteal uses integer actual troop loss and Python-independent mathematical CEIL via integer-safe helper semantics.

690221 never rounds. 690099 never rounds locally under its explicit runtime default.

## 15. Stage7-10 compatibility

The design preserves:

- Stage7 action/lifecycle foundations;
- Stage8 base formula ownership;
- Stage9 DamageInstance, partition, direct-loss and finalization ownership;
- Stage10 persistent application/tick and recovery-opportunity ownership.

Legacy Stage11 skeleton code is not protected authority. In particular the old Weakness-as-early-prevention binding and random exact-speed tie shuffle must be replaced because they contradict frozen Stage11 research.

## 16. Required test matrix

Tests must cover per-state unit behavior plus integration/cross cases: Evasion×SureHit; Resistance×SureHit; Resistance×Alert; Break×SeeThrough; Break×Crit families; Crit families×Alert; Crit×lifesteal; Weakness×Crit/lifesteal/share/FirstAid; HealingBlock×direct/FirstAid/Recuperation/lifesteal; FirstStrike×Surprise; Disarm×Combo/Assault/Counter; Stun×natural action/DOT/recovery; Distribution×Alert/crit/lifesteal; persistent damage application-bound critical/break; death/finalization; zero damage; multi-hit and multi-target.

Full `pytest -q` and demo smoke remain the final regression gate.
