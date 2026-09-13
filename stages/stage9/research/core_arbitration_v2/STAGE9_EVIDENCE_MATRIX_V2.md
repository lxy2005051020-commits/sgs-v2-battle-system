# Stage 9 Evidence Matrix V2 — RF-C02 Current Contract Overlay

> 本文件同时保留历史证据 ID 与当前 P0 状态。历史样本强度不能覆盖 later Frozen Contract；current implementation semantics 以 [`../../docsync/STAGE9_AUTHORITY_MAP.md`](../../docsync/STAGE9_AUTHORITY_MAP.md) 指向的 authority 为准。

## Status vocabulary

```text
HISTORICAL A/B/C = historical battle-report evidence strength
FROZEN           = current P0 semantic closed for runtime
RUNTIME_READY_WITH_RESEARCH_DEBT = deterministic runtime + explicit empirical debt
SUPERSEDED       = lower-authority historical wording, not current authority
```

## Nine-mechanism evidence / P0 status

| Mechanism | Evidence status | P0 status | Current authority | Current open questions / research debt |
|---|---|---|---|---|
| CONFUSION | historical evidence + formal P0/P1 | FROZEN | state repo `states/control/confusion/MECHANISM_CONTRACT.md`; RF-P03 closes old residual death path as unreachable | none blocking |
| TAUNT | direct freeze record + consistency audit | FROZEN | `STAGE9_TAUNT_MECHANICS_FREEZE_RECORD.md` | none blocking |
| GUARD | formal contract + independent audit | FROZEN | `../../STATE_690098_GUARD_MECHANISM_CONTRACT.md` / state P0 owner | none blocking |
| COMBO | focused evidence + RF-P02/P03/P04 | FROZEN | state repo `states/functional/combo/MECHANISM_CONTRACT.md` | none blocking; exact official PRNG internals are not claimed |
| CLEAVE | direct freeze + RF-P06/P07/P04 empirical repairs | FROZEN | state repo `states/functional/cleave/MECHANISM_CONTRACT.md`; battle Freeze Record supports it | none blocking |
| CHAIN_LINK | direct freeze + RF-P01 integerization | FROZEN | `STAGE9_CHAIN_MECHANICS_FREEZE_RECORD.md` | none blocking |
| DAMAGE_SHARE | direct freeze + RF-P01/P03/P05 | FROZEN | state repo `states/functional/damage_share/MECHANISM_CONTRACT.md`; battle Freeze Record synchronized | none blocking |
| DISTRIBUTION | direct freeze + RF-P01/P03/P04/P05 | RUNTIME_READY_WITH_RESEARCH_DEBT | `STAGE9_DISTRIBUTION_MECHANICS_FREEZE_RECORD.md` + Finalization Barrier | `DSTS9-B02`: empirical OPEN / UNOBSERVED; runtime CLOSED BY EXPLICIT PROJECT_RUNTIME_DEFAULT; design NOT BLOCKING |
| COUNTERATTACK | direct freeze + independent audit + RF-P04 hardening | FROZEN | `STAGE9_COUNTERATTACK_MECHANICS_FREEZE_RECORD.md` | universal comparator/dispel fidelity remains non-blocking; runtime deterministic |

## Historical EM trace with current disposition

| ID | Historical topic | Historical evidence | RF-C02 current disposition |
|---|---|---|---|
| EM-01 | CONFUSION × TAUNT target arbitration | historical A | FROZEN by CONFUSION + TAUNT P0; no extractor-pending gate |
| EM-02 | GUARD after TAUNT | historical A | FROZEN by TAUNT/GUARD target-resolution contracts |
| EM-03 | attacker == protector case | historical A | behavior retained; old “自援护” wording is HISTORICAL, not Self_Guard definition |
| EM-04 | target identity separation | historical A | FROZEN + typed by RF-C01 (`Selected/Intended/PostRedirect/DamageRecipient`) |
| EM-05 | CLEAVE anchor around actual target | historical B | FROZEN by CLEAVE/GUARD P0 |
| EM-06 | COUNTER owner = actual recipient | historical A | FROZEN by Counter P0 |
| EM-07 | Assault follows actual attack target | historical A | historical supporting evidence; current lifecycle owner is shared arbitration / relevant mechanism P0 |
| EM-08 | NormalAttack reaction order | historical B | current order owned by Core + RF-P02/P03/P04; R1 is historical evidence |
| EM-09 | FirstAid callback timing | historical A | retained evidence; mechanism-specific permission policies still apply |
| EM-10 | zero-damage action reactions | historical A | retained evidence; mechanism-specific zero/cancel rules govern current runtime |
| EM-11 | Counter → Counter | historical 0/90 | FROZEN = BLOCKED by Counter P0; no pending extractor audit |
| EM-12 | Cleave → Cleave | direct freeze | FROZEN = BLOCKED |
| EM-13 | Chain → Chain | direct + historical | FROZEN = BLOCKED |
| EM-14 | Share-derived loss → Share | direct freeze | FROZEN = BLOCKED; Share math no longer “next research” |
| EM-15 | Share math | historical A | FROZEN; RF-P01 = ROUND_HALF_UP, RF-P05 = lethal-target transaction closure |
| EM-16 | Chain feedback math | direct + historical | FROZEN; RF-P01 = FLOOR |
| EM-17 | CLEAVE pipeline | direct freeze | FROZEN; canonical term `RESISTANCE`, damage layer completed by RF-P06 |
| EM-18 | CHAIN restricted pipeline | direct freeze | FROZEN; TRUE_FEEDBACK restricted settlement |
| EM-19 | lethal DAMAGE_SHARE target | historical B precursor | FROZEN by RF-P05: 128/128 controlled cases cancel pending sharer commit |
| EM-20 | attacker killed during reaction | historical A precursor | SUPERSEDED as universal slogan; current rule is scoped admission/liveness + finalization (RF-P03/RF-P04) |
| EM-21 | commander death / battle end | historical A precursor | FROZEN by RF-P04 explicit finalization barrier |
| EM-22 | CHAIN target death continuation | direct + historical | FROZEN; admitted Chain traversal drains before finalization |
| EM-23 | same-type control conflict | historical B | remains historical outside the nine-mechanism current P0 gate; no Stage9 runtime blocker created here |
| EM-24 | multiple Counter execution | historical C precursor | CounterBatch semantics FROZEN; universal official comparator fidelity remains non-blocking |
| EM-25 | COMBO fresh target resolution | historical B+ precursor | FROZEN as fresh standard NormalAttack resolution; exact official iid/uniform PRNG claim rejected |
| EM-26 | CONFUSION JIT | historical A precursor | FROZEN = EACH ACTUAL TARGET SELECTION / JIT |

## Distribution dual-status rule

```text
DSTS9-B02
Empirical Status: OPEN / UNOBSERVED
Runtime Status: CLOSED BY EXPLICIT PROJECT_RUNTIME_DEFAULT
Design Admission: NOT BLOCKING
Research Debt: YES
```

This is intentionally not collapsed into “CLOSED”.

## Current research status

```text
CONFUSION      = FROZEN
TAUNT          = FROZEN
GUARD          = FROZEN
COMBO          = FROZEN
CLEAVE         = FROZEN
CHAIN_LINK     = FROZEN
DAMAGE_SHARE   = FROZEN
DISTRIBUTION   = RUNTIME_READY_WITH_RESEARCH_DEBT
COUNTERATTACK  = FROZEN

Architecture blockers = 0
Runtime ambiguities   = 0
Stage8                = FROZEN
Formal Stage8 Reopen  = NO
```

The next project step is the Global Cross-Mechanism Final Audit, not another “next core mechanism research target”.
