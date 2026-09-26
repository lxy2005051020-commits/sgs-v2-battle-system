# Stage12 · 690107 FALSE_REPORT Research Authority Sync

> Sync Date: **2026-09-26**
>
> Battle Runtime Status: **NOT_INTEGRATED**
>
> Research Status: **FROZEN**
>
> Purpose: mirror the frozen research authority into the Battle repository without treating Research Freeze as Runtime completion.

## 1. Research authority

Repository:
`lxy2005051020-commits/sgs-state-mechanics-research`

Canonical path:
`states/control/false_report/MECHANISM_CONTRACT.md`

Frozen contract:
`v1.0.1-frozen`

Authority pins:

```text
Contract commit                 = 17054f63bb4f328c27eed475a93eb0b98a95c171
Contract blob                   = 19804cf515cea29d6311235ab42463619267240a
Final correction audit commit   = 1885ae09c6eba9f6fe5bf7d06528b41b7450128a
Final correction audit blob     = 2a5dddfb4965483182c77d0d55e82ddf656fdb07
Falsification audit commit      = 4e89c15e7e325dabf3c34f5412c5f9232941c461
Falsification audit blob        = 443dc43d6f7cc12be22b990ef14ddabec368c28a
Question ledger commit          = b1f59fb2289564627d00aa0fe384bdc4a9c85a8b
Question ledger blob            = 9139c942fe39557d5847cc58b60f9bee66fbee22
Freeze record commit            = ce4a391a681e68cb61cf04a703c1d414cddeeddc
Freeze record blob              = a9ef9e1d0a243915e1f188aabb0a7b39da9dc246
Research completion matrix commit = d6ac36b88e4be9def475a73e8f44551ed729ebbe
Research completion matrix blob   = 4eca302aa16214140b8430943a223cd2d89bb5ef
Research mechanics index commit   = a38d424ce29d3685e18bb9ca2ef4e3dbb139f6e9
Research mechanics index blob     = 4cfaff7b78dbf877fbe88ce49999ba0d4829b6a6
```

## 2. Frozen mechanism summary

```text
Admission:
  ordinary Insight does not reject FalseReport
  tested special protections may reject it

Applied:
  core confirmed suppressible SkillTypes = PASSIVE / COMMAND
  tested persistent Equipment Specials are separately confirmed
  tested Provider-dependent still-live ongoing effects can become temporarily ineffective

Ownership:
  tested ongoing validity follows Provider, not merely Holder

Skill/action boundaries:
  Active / Preparation Active / Assault / Normal Attack
  standard Formation / Troop / Talent
  are not directly suppressed in tested standard cases

Lifecycle:
  equal-strength reapply = rejected / no refresh / no extension
  tested cleanse can remove early
  source death does not remove
  stronger-vs-weaker = BOUNDED_UNKNOWN

Removal:
  still-live dependent effects continue
  missed trigger windows are not replayed
  resolved facts are not rolled back
```

## 3. Stage12 design obligations

Stage12 Runtime Design must preserve:

1. Admission and post-application suppression as distinct concerns;
2. Provider ownership rather than Holder-only blanket invalidation;
3. PASSIVE / COMMAND core suppression plus the separately tested Equipment boundary;
4. non-suppression of tested Active-family / Formation / Troop / Talent cases;
5. equal-strength no-refresh reapplication;
6. tested cleanse behavior;
7. source-death persistence;
8. future-only restoration with no missed-trigger replay;
9. cross-state independence for EXHAUSTION / STUN / DISARM / CONFUSION;
10. all bounded unknowns as non-research facts.

The frozen contract defines a minimum 30-test Runtime obligation for later implementation.

## 4. Bounded unknowns

```text
B-U01 stronger-over-weaker FalseReport
B-U02 unseen future special immunity
B-U03 special NPC/scenario-only rules
B-U04 untested Equipment Special subtypes
```

These are non-blocking for current standard Stage12 design.

## 5. Runtime non-claims

This sync does not mean:

- Stage12 production Runtime is active;
- 690107 Runtime is implemented;
- 690107 Runtime is tested;
- 690107 Runtime is frozen to contract;
- Strict Complete increased.

Current Battle disposition:

```text
Research FROZEN            = YES
Runtime FROZEN TO CONTRACT = NO
Strict Complete            = NO
Next                       = Stage12 contract-aligned Runtime Design
```
