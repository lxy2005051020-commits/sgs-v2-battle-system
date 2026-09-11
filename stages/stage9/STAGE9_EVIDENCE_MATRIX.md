# Stage 9 Evidence Matrix · Pre-Design Gate

> Status: `PRE-DESIGN`
>
> Purpose: prevent Stage 9 infrastructure design from silently turning incomplete state research into official production behavior.
>
> This matrix is preparatory. It does not authorize production bindings.

## 1. Pinned baselines

Battle repository:

```text
repository: lxy2005051020-commits/sgs-v2-battle-system
starting exact main HEAD: 660fefe2b92d19358772d8c221c072d58a7eb52c
```

State mechanics research repository:

```text
repository: lxy2005051020-commits/sgs-state-mechanics-research
pinned research baseline: 7f1345681812864d4e34fae453bd69f766202c4c
```

Static project mapping source:

```text
research/official_state_catalog_v1/STATE_SYSTEM_MAPPING_V1.md
```

## 2. Verdict vocabulary

```text
DESIGN_DRIVER
= evidence is currently rich enough to drive shared Stage 9 topology design,
  but production binding still requires formal Stage 9 design audit/freeze.

RESEARCH_REQUIRED
= current evidence confirms only a coarse mechanism skeleton while material
  ordering/interaction/ratio/eligibility questions remain unresolved.

DEFER
= not admitted to Stage 9 official production mapping in the current gate.
```

No row in this pre-design matrix is equivalent to `PASS_STAGE9`.

## 3. Matrix

| state_id | role in roadmap | pinned research source | currently established | architecture-critical unknowns | pre-design verdict |
|---|---|---|---|---|---|
| `combo` | additional standard normal attack | `states/functional/combo/QUESTION_RESULTS_INDEX.md`; `CROSS_QUESTION_CONSISTENCY_AUDIT.md`; Q01-Q51 at pinned research baseline | One extra standard normal attack after attack #1 and all its downstream reactions; max 2 physical normal attacks per own action window; second attack is independent and re-selects target; standard observers can respond; pre-attack and inter-attack control gates distinguished | Formal project mapping of researched lifecycle into existing StateLifecycle; exact Stage 9 operation/queue representation; project event names/provenance; compatibility proof with frozen Stage 8 boundaries | `DESIGN_DRIVER` |
| `cleave` | normal-attack derived splash damage | `states/functional/minimum_usable/690084_SPLASH.md` | Normal attack damage to primary target can also produce damage to other living units in target's team | Damage formula/reference; whether trigger requires requested damage or actual damage; exact ordering; modifier/prevention/hit compatibility; split/share interaction; provenance and death short-circuit | `RESEARCH_REQUIRED` |
| `counterattack` | received-normal-attack reaction | `states/functional/minimum_usable/690085_COUNTERATTACK.md` | Receiving a normal attack can cause counterattack damage to the attacker | Exact formula; trigger checkpoint; whether prevention/evasion/zero actual damage still triggers; whether counterattack is standard normal attack vs special damage; reaction-to-reaction eligibility; multi-source ordering | `RESEARCH_REQUIRED` |
| `damage_split` | one incoming damage partitioned among multiple bearers | `states/functional/minimum_usable/690086_DISTRIBUTION.md` | One originally single-target damage amount is partitioned into multiple shares borne by multiple recipients | Exact ratio; eligible bearers; whether partition occurs before/after Stage 8 finalization; per-recipient prevention/modifier semantics; rounding remainder; source death / recipient death; stacking | `RESEARCH_REQUIRED` |
| `damage_share` | partial incoming damage transfer | `states/functional/minimum_usable/690087_DAMAGE_SHARE.md` | Original target keeps a remainder while another bearer receives the transferred portion | Exact ratio; eligibility; pre/post-finalization boundary; hit/prevention interaction; transferred-damage source family; nested share/split behavior; ordering | `RESEARCH_REQUIRED` |
| `chain_link` | damage-linked propagation | `states/functional/minimum_usable/690097_CHAIN_LINK.md` | Damage to one linked target causes calculated feedback loss to other linked targets; minimum skeleton explicitly avoids treating feedback as a recursively normal damage event | Feedback event family; eligible damage families; formula/reference amount; multiple link sources; whether Stage 8 pipeline runs for feedback; propagation recursion rule; precise ordering | `RESEARCH_REQUIRED` |
| `guard` | post-selection normal-attack target redirect | `states/functional/minimum_usable/690098_GUARD.md` | When a protected ally becomes a normal-attack target, guard source replaces that target and bears the normal attack | Multiple guards; guard vs taunt ordering; guard vs confusion; combo attack interaction; splash interaction; guard-source death; lifecycle; exact event ordering | `RESEARCH_REQUIRED` |
| `confusion` | target candidate-set/faction policy rewrite | `states/control/minimum_usable/690103_CONFUSION.md` | Normal attacks and target-selecting skills stop distinguishing friend from foe within the action's eligible target model | Self eligibility; healing/enemy eligibility; multi-target reconstruction; commander/deputy constraints; confusion vs taunt/provoke/pursuit ordering; exact RNG pool | `RESEARCH_REQUIRED` |
| `taunt` | forced normal-attack target | `states/control/minimum_usable/690106_TAUNT.md` | Taunt source forces the affected unit's normal attack target to itself | Multiple taunt sources; source death; taunt vs confusion; taunt vs guard; taunt vs pursuit; lifecycle; precise event ordering | `RESEARCH_REQUIRED` |

## 4. Cross-state blockers

The following questions block a trustworthy nine-state production implementation even though they do not block synthetic infrastructure design.

### Target arbitration blockers

```text
confusion → how is candidate pool rebuilt?
taunt → when does forced target override normal selection?
guard → when does interception occur relative to taunt?
multiple taunt / guard → what arbitration rule applies?
combo attack #2 → which policies are re-evaluated from live state?
```

### Reaction / derived-operation blockers

```text
counterattack event identity
counterattack recursion eligibility
cleave event identity
cleave trigger checkpoint
combo extra-attack checkpoint
battle-end / actor-death short-circuit
```

### Damage fan-out blockers

```text
split/share use requested final damage vs actual troop loss
split/share per-recipient Stage 8 processing
rounding and deterministic remainder assignment
chain-link feedback event family
chain-link propagation recursion boundary
interaction among split/share/chain-link
```

## 5. Design permission granted by this matrix

Allowed before official-state evidence closes:

```text
synthetic typed operation model
synthetic resolution queue
synthetic recursion/lineage guard
synthetic target arbitration interfaces
synthetic redirect/split result models
trace/provenance models
deterministic ordering tests
RNG-consumption tests
Stage 8 compatibility tests
```

Not allowed:

```text
claiming unresolved ordering as official behavior
binding RESEARCH_REQUIRED rows into production with guessed defaults
using MINIMUM_USABLE as if it were a frozen mechanism contract
letting state-specific code bypass shared orchestration
```

## 6. Current gate result

```text
combo          = DESIGN_DRIVER
cleave         = RESEARCH_REQUIRED
counterattack  = RESEARCH_REQUIRED
damage_split   = RESEARCH_REQUIRED
damage_share   = RESEARCH_REQUIRED
chain_link     = RESEARCH_REQUIRED
guard          = RESEARCH_REQUIRED
confusion      = RESEARCH_REQUIRED
taunt          = RESEARCH_REQUIRED

PASS_STAGE9 official bindings = 0
```

This is intentional. Stage 9 preparation should first produce a safe shared topology, then promote individual states only after evidence and design gates are satisfied.
