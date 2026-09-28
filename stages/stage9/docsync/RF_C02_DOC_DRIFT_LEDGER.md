# RF_C02_DOC_DRIFT_LEDGER

Package: `RF-C02 — DOC_SYNC_PACKAGE`  
Scope: documentation synchronization only.  
Independent re-extraction source: all nine current `*_CONTRACT_AUDIT.md` files on battle `main` before RF-C02.

## Re-extracted count

```text
CONFUSION     4
TAUNT         4
GUARD         4
COMBO         3
CLEAVE        4
CHAIN_LINK    3
DAMAGE_SHARE  2
DISTRIBUTION  2
COUNTERATTACK 3
TOTAL        29
```

The total independently re-extracted from audit originals is exactly `29`; it was not copied from the old consolidation snapshot.

## Ledger

| Finding | Audit | Stale file / surface | Stale statement | Current authority | Required edit / disposition | Status |
|---|---|---|---|---|---|---|
| CFS9-D01 | CONFUSION | `core_arbitration_v2/README.md` | CONFUSION / COMBO still future research | mechanism P0 + RF-P02/P03/P04 | remove future-target wording; route to current P0 | CLOSED BY DOC SYNC |
| CFS9-D02 | CONFUSION | `STAGE9_EVIDENCE_MATRIX_V2.md` | CONFUSION rows only historical/pending | CONFUSION P0 + RF-P03 | add FROZEN current overlay; retain historical evidence trace | CLOSED BY DOC SYNC |
| CFS9-D03 | CONFUSION | state root `README.md` | COMBO first research target + blanket Target Death | RF-P03 execution/death P0 | replace with current navigation/scoped death model | CLOSED BY DOC SYNC |
| CFS9-D04 | CONFUSION | battle Stage9 navigation / COMBO sync | COMBO P0 omitted from current battle navigation | state COMBO P0 + RF-P02/P03/P04 | authority map points to sole state P0; no duplicate P0 mirror created | CLOSED BY DOC SYNC |
| TAS9-D01 | TAUNT | state `STATE_MECHANICS_INDEX.md` | TAUNT = MINIMUM_USABLE | Taunt Freeze Record | index = FROZEN; old skeleton = SUPERSEDED | CLOSED BY DOC SYNC |
| TAS9-D02 | TAUNT | `core_arbitration_v2/README.md` | CONFUSION/COMBO future + old death summary | current P0 + RF-P03/P04 | rewrite as research archive/current authority nav | CLOSED BY DOC SYNC |
| TAS9-D03 | TAUNT | Evidence Matrix | old EM-20 / historical current state | RF-P03/P04 + mechanism P0 | current contract overlay added | CLOSED BY DOC SYNC |
| TAS9-D04 | TAUNT | R1/R5 + state root README | blanket death-abort semantics | Execution/Death P0 + Finalization P0 | R1/R5 classified HISTORICAL; state current baseline replaced | CLOSED BY DOC SYNC |
| GDS9-D01 | GUARD | core README | GUARD/CONFUSION/COMBO map stale | Guard/Confusion/Combo P0 | current authority navigation synchronized | CLOSED BY DOC SYNC |
| GDS9-D02 | GUARD | Evidence Matrix | Share next research / old EM-20/25/26 | repairs + P0 | synchronized overlay | CLOSED BY DOC SYNC |
| GDS9-D03 | GUARD | state root README | research target/death baseline stale | RF-P03/P04 | root navigation synchronized | CLOSED BY DOC SYNC |
| GDS9-D04 | GUARD | R2 historical report | “自援护” can be confused with forbidden `protector == holder` Self_Guard | Guard P0 canonical terminology | R2 retained as HISTORICAL; current navigation uses target/redirect identities | NOT APPLICABLE / SUPERSEDED |
| CBS9-D01 | COMBO | battle current navigation | no current COMBO P0 mirror | state COMBO P0 is sole authority by RF-P02 | cross-repo authority link added; deliberately no competing mirror | CLOSED BY DOC SYNC |
| CBS9-D02 | COMBO | battle Stage9/core README/Evidence Matrix | COMBO pending/omitted | RF-P02/P03/P04 + state P0 | current status = FROZEN | CLOSED BY DOC SYNC |
| CBS9-D03 | COMBO | state README/index | inconsistent death baseline | RF-P03/P04 | replace universal own-open-action exception with scoped execution model | CLOSED BY DOC SYNC |
| CLVS9-D01 | CLEAVE | current terminology | `Barrier` used as current term | canonical `690083 RESISTANCE` | current navigation/matrix use RESISTANCE; legacy wording historical | CLOSED BY DOC SYNC |
| CLVS9-D02 | CLEAVE | Evidence Matrix | Share next research / Counter pending | later P0 + repairs | matrix synchronized | CLOSED BY DOC SYNC |
| CLVS9-D03 | CLEAVE | state `690084_SPLASH.md` | partially superseded Deferred list | state CLEAVE P0 + RF-P06/P07/P04 | legacy file = SUPERSEDED, canonical name CLEAVE, direct P0 link | CLOSED BY DOC SYNC |
| CLVS9-D04 | CLEAVE | state root README/index | research target/death baseline / MINIMUM_USABLE era | CLEAVE P0 + RF-P04/P06/P07 | root/index current; Cleave = FROZEN | CLOSED BY DOC SYNC |
| CHNS9-D01 | CHAIN_LINK | state `690097_CHAIN_LINK.md` | frozen fields still unresolved | Chain Freeze Record + RF-P01 | skeleton = SUPERSEDED + authority link | CLOSED BY DOC SYNC |
| CHNS9-D02 | CHAIN_LINK | R4 historical report | missing later Distribution participant-loss → Chain BLOCKED | later Core/P0 | R4 retained as HISTORICAL; current authority map/matrix owns current relation | NOT APPLICABLE / SUPERSEDED |
| CHNS9-D03 | CHAIN_LINK | Evidence Matrix footer | Share next research / Counter pending | later P0 | footer replaced by current nine-mechanism status | CLOSED BY DOC SYNC |
| SHS9-D01 | DAMAGE_SHARE | Evidence Matrix | Share next research / death unfrozen | RF-P01/P03/P05 + Share P0 | status = FROZEN; lethal target closure recorded | CLOSED BY DOC SYNC |
| SHS9-D02 | DAMAGE_SHARE | state root README | unconditional global death hard-stop | RF-P03/P04 | scoped shared death/finalization model | CLOSED BY DOC SYNC |
| DSTS9-D01 | DISTRIBUTION | state index + `690086_DISTRIBUTION.md` | MINIMUM_USABLE despite P0 | Distribution P0 + RF-P01/P03/P04/P05 | skeleton = SUPERSEDED; index = runtime-ready with explicit empirical debt | CLOSED BY DOC SYNC |
| DSTS9-D02 | DISTRIBUTION | Evidence Matrix | pre-freeze status rows | Distribution P0 + Finalization Barrier | synchronized dual status; empirical debt preserved | CLOSED BY DOC SYNC |
| CTS9-D01 | COUNTERATTACK | state index | COUNTERATTACK = MINIMUM_USABLE | Counterattack Freeze Record | index = FROZEN | CLOSED BY DOC SYNC |
| CTS9-D02 | COUNTERATTACK | state `690085_COUNTERATTACK.md` | accuracy-deferred skeleton can be mistaken for current contract | Counterattack Freeze Record | skeleton = SUPERSEDED + direct authority link | CLOSED BY DOC SYNC |
| CTS9-D03 | COUNTERATTACK | state root/index death model | Counter-kill vs old COMBO death baseline inconsistent | RF-P03/P04 + Counter P0 | scoped admission/liveness/finalization baseline | CLOSED BY DOC SYNC |

## Closure totals

```text
DOC_DRIFT total                         = 29
CLOSED BY DOC SYNC                     = 27
NOT APPLICABLE / SUPERSEDED            = 2
REMAINS OPEN                           = 0
CLOSED disposition total               = 29
```

`NOT APPLICABLE / SUPERSEDED` means the stale statement remains only inside an explicitly historical lower-authority report and is no longer reachable as current navigation; it does not mean the finding was ignored.

## Immutable history

The nine independent audit files were not rewritten. Their original findings, counts and then-current verdicts remain immutable history. The old consolidation is also retained as a historical snapshot; current navigation explicitly marks it superseded for present status.
