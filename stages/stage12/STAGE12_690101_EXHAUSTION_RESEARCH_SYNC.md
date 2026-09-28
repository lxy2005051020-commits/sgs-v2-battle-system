# Stage12 · 690101 EXHAUSTION Research Authority Sync

> Sync Date: **2026-09-26**
> Battle Runtime Status: **NOT_INTEGRATED**
> Research Status: **FROZEN**
> Purpose: mirror research authority into the Battle repository without treating Research Freeze as Runtime completion.

## 1. Research authority

Repository:
lxy2005051020-commits/sgs-state-mechanics-research

Canonical path:
states/control/exhaustion/MECHANISM_CONTRACT.md

Frozen contract:
v0.2-frozen

Authority pins:

    Contract creation commit       = 8232a64e1778e5b3572ca4536cf31977de68e360
    Frozen contract blob           = c6c0a7d55b455b853b56eba6572a1a66279c8cc0
    Adversarial audit commit       = be5adbb57f13d15adf71ee3d0584e947457f1d48
    Freeze audit commit            = 096e70e19cbdf8b420eb4a1fd81d2e168de144a0
    Freeze audit blob              = c11b5536bc7a5ce3c775c2494c67d13ccc3bb757
    Question ledger commit         = 1638a1eaff4b202bb2430baca86b29560f65ad3f
    Freeze record final commit     = 1bf3a1c6bc24ba69e476cda5e0a02362f0c3c836
    Research completion matrix     = c83da9dffb14ba31c2a51f06163b980a59555f69
    Research mechanics index       = cee8bc2f75ae401869c39a4da5c4b2cbb4362208

## 2. Frozen mechanism summary

    effective EXHAUSTION
      -> blocks ACTIVE_SKILL admission

    EXHAUSTION itself
      -> does not block legal Basic Attack
      -> does not block observed standard post-attack Assault
      -> does not block observed Passive / Command execution

    PREPARING + EXHAUSTION becomes effective
      -> immediate cfg191 preparation interruption
      -> old preparation does not resume

    preparation reduction / skip
      -> does not bypass EXHAUSTION

    already activated Active-Skill instance
      -> is not retroactively rolled back
      -> future independent Active admissions remain blocked

690089 INSIGHT owns incoming EXHAUSTION rejection and existing EXHAUSTION suppression.

## 3. Audit baseline

    Structured battle reports       = 23,002
    Observed EXHAUSTION executions  = 18,487
    TRUE_COUNTEREXAMPLE             = 0
    UNRESOLVED_ARCHITECTURE_BLOCKER = 0

## 4. Runtime obligations imported into Stage12 design

Stage12 Runtime Design must provide:
1. an Active-Skill permission admission owned at the permission layer;
2. an asynchronous hook that can interrupt existing preparation when EXHAUSTION becomes effective;
3. no automatic restoration of interrupted preparation;
4. preservation of legal Basic Attack and standard Assault reachability;
5. no retroactive rollback of an already activated skill instance;
6. preparation reduction/skip cannot bypass EXHAUSTION;
7. INSIGHT suppression/admission rules must be respected;
8. hidden RNG ordering must remain explicitly governed, not inferred from research silence.

## 5. Runtime non-claims

This sync does not mean:
- Stage12 Active = YES;
- 690101 Runtime is implemented;
- 690101 Runtime is tested;
- 690101 Runtime is frozen to contract;
- Strict Complete increased.

Current Battle disposition:

    Research FROZEN            = YES
    Runtime FROZEN TO CONTRACT = NO
    Strict Complete            = NO
    Next                       = Stage12 contract-aligned Runtime Design
