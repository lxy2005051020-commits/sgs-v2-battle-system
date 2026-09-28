# Stage12 · 690222 INTIMIDATION Research Authority Sync

> Sync Date: **2026-09-26**
>
> Battle Runtime Status: **NOT_INTEGRATED**
>
> Research Status: **FROZEN**
>
> Mechanism Contract: **FROZEN**
>
> Stage12 Production Active: **NO**
>
> Purpose: mirror the frozen 690222 research authority into the Battle repository without treating Research Freeze as Runtime completion.

## 1. Research authority

Repository:
`lxy2005051020-commits/sgs-state-mechanics-research`

Canonical path:
`states/control/intimidation/MECHANISM_CONTRACT.md`

Frozen contract:
`v1.0-frozen`

Authority pins:

```text
Contract commit                    = f87f9a900ba8d3e33e509fab71690e7181d8e4b7
Contract blob                      = 3e5eaaf4c5ac09eef3cb5c5810c68f5b01f997a1
Question ledger commit             = 05fcbca93728dc6b1949fca4579f3d35761ed273
Question ledger blob               = e2e4e48a526b45218f7a2b9380f61680aac7a238
Falsification audit commit         = 5b57c8aa2869301d3b7e4d9dd6e04d71eb533687
Falsification audit blob           = 1fb9f4bb8b6dbd757d6a9e224152a5bced46f17e
Final freeze audit commit          = f620a28753a53f970c39f806a0562063bc59b378
Final freeze audit blob            = db807ab19b4cd003cda32c6eccadba758521d0e4
Freeze record commit               = afbebdcafd323c8cab5f756ca5c79893bcdb85a0
Freeze record blob                 = 4ed04370bb6ab277a3b318df2493e423b0a122c7
Research completion matrix commit  = 3b54350ea2d0e018ecb0a538699120d0c7bcb5bd
Research completion matrix blob    = 9f669eb97a2cdf0af0aa2a2496092e5fe494f0f1
Research mechanics index commit    = 82f758fe772cb9dc204ca837cee1a6081ce1f84c
Research mechanics index blob      = fa6542ffed62533ec242acec54f456d97288b152
```

## 2. Frozen observable model

```text
Intimidation
→ binds exactly one eligible Skill Provider
→ suppresses that Provider's live behavior
```

Confirmed eligible observed families:

- Active;
- Preparation Active;
- Assault;
- Passive;
- Command;
- Troop.

Confirmed boundaries:

- Formation excluded;
- Normal Attack remains outside the suppressible skill domain;
- Equipment and Bingshu remain bounded unknowns.

## 3. Refresh and lifecycle

```text
Refresh:
  release old selected Provider
  → reroll exactly one eligible skill
  → suppress new selected Provider
  → no multi-disable stacking

Source Resume for observed ChengtianJingshi instances:
  preserve selected binding
  → no reroll
  → no duration reset

Suspended lifetime:
  continues to advance
  → suspended instance may expire naturally
```

Observed ChengtianJingshi-created baseline duration is one round. This is not generalized to every possible future 690222 source.

## 4. Insight, immunity and cleanse

- ordinary Insight does not reject Intimidation;
- selecting the Insight-producing Provider can temporarily suppress Provider-owned Insight;
- 【刚毅】 is a confirmed rejecting mechanism, but is not claimed to be the only possible special immunity;
- tested generic negative cleanse / Grass Boat behavior does not remove Intimidation;
- specialized removal remains bounded unknown.

## 5. Source dependency boundary

For observed Intimidation instances created by 【承天靖世】:

```text
source Provider invalid
→ resident Intimidation temporarily ineffective
→ selected target Provider resumes

source Provider resumes
→ Intimidation continues
→ same selected binding suppressed again
```

This source-gating behavior is **not** generalized to hypothetical future 690222 sources.

## 6. Counter separation

The frozen 690222 State Contract owns only:

```text
no observable State Stack
repeated successful application → Refresh
```

Precise "威慑次数" counting, storage, trigger probability, damage scaling, counter cap, counterattack threshold, and damage coefficients remain **SOURCE_SKILL_SCOPE** for 【承天靖世】.

## 7. Bounded unknowns

Non-blocking research debt remains explicit for:

- source death;
- permanent source removal;
- multiple Intimidation sources;
- transfer;
- extension;
- specialized removal;
- Equipment eligibility;
- Bingshu eligibility;
- exact version provenance;
- Refresh while source Provider is invalid.

No project default is presented as historical game fact.

## 8. Final disposition

```text
Research Campaign                = COMPLETE
Adversarial Falsification        = PASS
Canonical Governance             = PASS
OPEN_BLOCKING                    = 0
Final Freeze Audit               = PASS

Research FROZEN                  = YES
Mechanism Contract FROZEN        = YES
Runtime FROZEN TO CONTRACT       = NO
Strict Complete                  = NO
Stage12 Production Active        = NO
Next                             = Stage12 contract-aligned Runtime Design
```

Later Runtime implementation must conform to the frozen observable contract and preserve all source-skill and bounded-unknown boundaries.
