# Stage12 Insight × Confusion Authority Migration

Date: 2026-09-27
Round: STAGE12_SF_ROUND2_AUTHORITY_AND_IDENTITY_DESIGN
Status: ACCEPTED AUTHORITY MIGRATION
Gameplay changes in this round: NONE

## 1. Repository lock

- Battle main at migration start: e6e5a6c43c4c0265af8509274de338a6c5b2783e
- Research main at migration start: e18ae56a4db5662b87458dfa8fdff25dcdd8053b
- Current Research authority: 690089 INSIGHT v0.4-frozen.
- Historical Battle authority remains preserved as historical evidence; this document changes authority precedence for the narrow conflict only.

## 2. Historical authority

The historical Stage9 Battle authority is:

- tests/test_stage9_phase_9_3_target_resolution.py
  - P0-CFS-P93-01
  - test_p0_cfs_p93_01_insight_immunity_not_reinterpreted_as_jit_confusion_suppression
- stages/stage9/implementation/STAGE9_PHASE_9_3_REPAIR_REPORT.md
  - P93-B01

The historical rule was:

Confusion resident
→ later Insight
→ existing Confusion remains operational at JIT Normal Attack target resolution.

P93-B01 explicitly described Insight as application immunity only for Confusion and removed the then-existing JIT suppression check from Stage9StateRuntime.get_operational_confusion.

Historical verdict:

These Stage9 conclusions were legitimate frozen results under the Research and Runtime authority available at that time. This migration MUST NOT be described as “Stage9 was simply wrong”. The later Research authority changed the canonical contract boundary.

## 3. Current authority

Current authority is:

- Research states/functional/insight/MECHANISM_CONTRACT.md
- Contract Version: v0.4-frozen
- Relevant rule groups: §§3, 4, 7, 8, 21, 22.

Current rule:

- 690103 CONFUSION is in PROTECTED_CONTROL_SET.
- If effective Insight appears while a protected control already exists, the control remains resident but becomes temporarily ineffective.
- Suppression is not purge, delete, cleanse, or timer pause.
- The suppressed control continues normal lifetime progression.
- If Insight ceases to be effective first and the protected control is still alive, the control resumes without a new canonical application.
- If the protected control expires while suppressed, it never resumes later.

Therefore the current canonical Insight × Confusion behavior is:

Confusion resident
→ Insight effective
→ Confusion resident but suppressed
→ Confusion does not own current target arbitration
→ Insight ends or becomes ineffective
→ if Confusion is still alive, Confusion resumes
→ no new cfg21 is created by resume.

## 4. Authority order and scoped supersession

The current frozen 690089 v0.4 Research contract supersedes the conflicting historical Battle runtime assertion only where the old assertion says:

P0-CFS-P93-01:
existing Confusion remains operational after Insight becomes effective.

SUPERSEDED SCOPE:

- P0-CFS-P93-01 only in the above existing-Confusion operationality claim.
- P93-B01 only in the corresponding statement that existing Confusion cannot be runtime-suppressed by later effective Insight.
- Stage9StateRuntime.get_operational_confusion only insofar as its current presence-only behavior conflicts with the later Stage12 effectiveness authority.

PRESERVED SCOPE:

- Confusion candidate construction.
- Confusion RNG ownership and consumption.
- Confusion > Taunt priority when Confusion is effective.
- TargetSystem ownership of legal candidate construction.
- TargetResolutionSystem ownership of Normal Attack target arbitration.
- NormalAttackSystem ownership of Normal Attack permission/execution.
- Guard post-selector ownership and single-pass behavior.
- Other Stage9 invariants and regression contracts.
- Historical Stage9 audit facts and commit provenance.

No other Stage9 rule is superseded by implication.

## 5. Historical artifact preservation

Historical repair reports and freeze records remain historical records. They must not be rewritten to make Stage9 appear to have known the later v0.4 contract.

This migration document is the canonical supersession notice. A future historical appendendum may link here, but must not alter the old finding text.

## 6. Test migration plan

This round does not modify gameplay or tests.

P0-CFS-P93-01 must not be deleted, xfailed, or weakened merely to obtain green CI.

At the Stage12 implementation migration, the old regression must be explicitly replaced or renamed under this authority so that the new discriminator proves all of the following:

1. Confusion is physically resident before and during Insight suppression.
2. Effective Insight makes the existing Confusion ineffective.
3. While suppressed, Confusion does not own current Normal Attack target arbitration.
4. Suppression does not remove the Confusion instance.
5. Confusion lifetime continues while suppressed.
6. Insight removal or ineffectiveness resumes Confusion only if that same instance is still alive.
7. Resume does not create a new cfg21 application.
8. Confusion that expires while suppressed never resurrects after Insight ends.
9. Existing Confusion candidate construction, RNG, Confusion-over-Taunt priority when effective, TargetSystem ownership, and Guard ordering remain unchanged.

Planned migration discriminator names:

- test_stage12_migration_confusion_resident_but_suppressed_by_effective_insight
- test_stage12_migration_confusion_resume_reuses_surviving_instance
- test_stage12_migration_confusion_expired_while_suppressed_never_resumes
- test_stage12_migration_confusion_rng_and_candidate_authority_preserved

The implementation commit must cite this document when changing the historical regression.

## 7. Stage11 reopen adjudication

Stage11 Reopen Required? NO.

Reason:

- The proven contradiction is between a Stage9 Confusion operational read and later Stage12 Insight effectiveness authority.
- This Round 2 migration changes no Stage11 gameplay, clock, suppression implementation, or Stage11 frozen regression.
- The future Stage12 State Effectiveness design is responsible for the shared resident/effective distinction and Stage9 delegation.
- DQ-SF-24 remains responsible for detecting any genuine Stage11 clock contradiction. If one is later proven, only that affected scope may reopen.

A blanket Stage11 reopen is not authorized.

## 8. AR-SF-02 provenance qualification

690222 INTIMIDATION provides the positive cross-contract authority for its own scope:

- Intimidation v1.0-frozen §5: ordinary Insight does not reject Intimidation.
- Intimidation v1.0-frozen §11: ordinary active Insight does not reject Intimidation application and Provider-linked Insight may become temporarily ineffective if its Provider is selected.

690089 INSIGHT retains its historical evidence label:

- SPECIAL_CASE_SUPPORTED / DIRECT_OVERLAP_UNOBSERVED for 690222 in the Insight corpus.

These statements are not contradictory because they describe different provenance bases.

Runtime may use the frozen 690222 contract as positive authority for the Intimidation boundary. It must not rewrite the 690089 evidence label to claim direct Insight-corpus observation.

AR-SF-02 = PROVENANCE QUALIFIED.
DQ-SF-28 = CLOSED_BY_PROVENANCE_QUALIFICATION.

## 9. Exit verdict

- AR-SF-01: CLOSED_BY_AUTHORITY_MIGRATION.
- DQ-SF-15: CLOSED_BY_AUTHORITY_MIGRATION.
- DQ-SF-16: CLOSED_BY_SCOPED_SUPERSESSION.
- Stage11 Reopen Required: NO.
- Gameplay implementation: NONE.
- Historical file rewrite: NONE.
- Stage12 Runtime Frozen: 0 / 7.
- Stage13 Active: NO.

This authority migration permits later Shared Foundation effectiveness design. It does not implement Insight suppression and does not by itself freeze Shared Foundation design.
