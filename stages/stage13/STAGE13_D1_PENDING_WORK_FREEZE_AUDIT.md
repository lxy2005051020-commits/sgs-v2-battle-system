# Stage13-D1 PendingWork Freeze Audit

Date: 2026-10-04. Verdict: IMPLEMENTED / LOCAL GATES PASS / MAIN CI REQUIRED.
Scope: one-shot PendingWork foundation, not Stage13 completion.

## Baseline authority and architecture audit

Runtime main inspected: `b3b20e42f17262bf866448505b6895525dd19248`;
baseline CI `37206600569` SUCCESS. Research main inspected:
`f7b646876c976c8cdfb8ebb5c5a9ce11b909906a`.
Research STATE_COMPLETION_MATRIX and Runtime Stage13 README confirm 40/40 Research,
40/40 Runtime-to-contract, 40/40 Strict Complete, B1/B2/B2.5/B3 ordinary core integrated,
690221 ACTIVE/DOT and 690099 inclusive 6% and 690086 DSTS9-B02 closed.
Older root-level Runtime status summaries were stale; current authority is reconciled
without reopening mechanisms. Special recovery remains separately owned.

Existing inventory and architecture decisions were written before gameplay scheduling code.
Independent architecture checks: context-scoped unique registry/system, storage versus lifecycle
split, canonical ExecutionRight/Gate calls, no second dependency graph, no EventBus authority,
non-orderable IDs and explicit comparator, no domain mathematics/RNG/troop/state mutation.
21 frozen owner source hashes match the baseline. The new gate method and engine/composition
extensions are limited to scheduling boundaries and leave existing branch/transaction contracts intact.

## Freeze gate

| Gate | Local result | Evidence |
|---|---|---|
| Canonical storage/lifecycle owner | UNIQUE | cross-owner/cross-battle adversarial tests |
| PendingWorkId | PASS | allocator independent counter; ordering rejected |
| Operation lineage | PASS | all parent types retained; child identity/lineage trace; forged child rejected |
| Schedule semantics | PASS | exact/next/holder/trigger, duplicate point, missed point, live clock |
| Lifetime semantics | PASS | one-shot/until-executed/until-round; repeat RESERVED and rejected |
| Snapshot/JIT carriage | PASS | deep immutable snapshot, changed live values, undeclared reads rejected |
| Source validity | PASS | independent death continues; required source cancels |
| Provider validity | PASS | slot-0 provider disabled; zero dispatch/RNG; admission snapshot checked |
| Target validity | PASS | death cancels; relation change delegated or explicitly independent |
| Cancellation/completion | PASS | terminal replay and illegal transition rejected; exception fails closed |
| Finalization interaction | PASS | pending never blocks barrier; same-batch/read closure; lethal domain transaction |
| Deterministic order | PASS | 12 IDs across lexical boundary; inverted storage; three identical typed traces |
| Adapter proof | PASS | real Recuperation producer/generation + probability variants; events/results/RNG identical |
| Focused tests | PASS | 48 cases (37 model/integration + 11 independent adversarial) |
| Full regression | PASS | 1739 passed, all 1691 existing tests retained |
| Demo | PASS | python demo.py exit 0 |
| Independent audit | PASS | scripts/audit_stage13_d1.py, 21 source hashes + independent harness |
| Latest main CI | REQUIRED | final publication evidence appended after GitHub verification |

## Adversarial routes, not a blanket no-issue claim

| Route | Actual attempted counterexample | Result / repair |
|---|---|---|
| A source death | kill deputy source with TroopSystem, test both source modes | independent COMPLETED; required CANCELLED |
| B provider invalid | register INHERENT slot 0, disable after creation; snapshot admission also disabled before create | live CANCELLED; bad creation rejected; valid snapshot preserved |
| C target death | defeat locked target before due point | CANCELLED/TARGET_INVALID |
| D future resurrection | finalize before due, during first sibling, during live reader, and real lethal DamageInstance | no future dispatch; current domain transaction drains; remaining work cancelled |
| E unstable order | reverse registry dictionary; create pw_1..pw_12; repeat three seeded contexts | explicit sequence and full typed trace identical |
| F repeat extra tick | construct REPEAT_N_TIMES and advance one-shot through later/duplicate points | repeat rejected as reserved; one-shot executes once |
| G cancelled replay | explicit cancel then due, illegal terminal transition, dispatcher/read exception | zero replay; exception terminal CANCELLED |
| H accidental JIT snapshot | mutate nested input list and live source intelligence | old snapshot retained; domain recovery snapshot unchanged |
| I accidental live snapshot | restore target wounds after work creation | dispatch reads new live value; reader failure fails closed |
| J gameplay God Object | AST import/call/write/arithmetic audit plus frozen-domain hashes | no formula/RNG/direct troop/state mutation in scheduler |

Audit-driven hardening before freeze: enforce explicit Recuperation potency projection;
recheck gate after validity and live reads; cancel outstanding work even on an exception
when termination closes. Fault injection adapters are test-only and deliberately violate
the pure-reader contract to test the fail-closed boundary.

## Remaining Stage13 scope

D2, D3, D4, D5, G only. Core Gameplay Engine remains NOT YET FROZEN;
Skill Runtime Readiness remains NOT YET READY. Repeated execution is explicitly RESERVED;
the D1 freeze claim applies to the permitted minimal one-shot foundation.
