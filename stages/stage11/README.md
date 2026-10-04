# Stage11 · State Runtime Integration

> Status: RUNTIME FROZEN / POST-FREEZE ACCEPTED

Canonical scope: 17 states.

```text
690086 690090 690091 690102 690104 690105 690111
690082 690083 690092 690093 690099 690070 690069
690221 690094 690095
```

## Current authority

- [Design freeze record](STAGE11_DESIGN_FREEZE_RECORD.md)
- [Design amendment 001](STAGE11_DESIGN_AMENDMENT_001.md)
- [Runtime integration design](STAGE11_RUNTIME_INTEGRATION_DESIGN.md)
- [Runtime adversarial audit](STAGE11_RUNTIME_ADVERSARIAL_AUDIT.md)
- [Runtime freeze record](STAGE11_RUNTIME_FREEZE_RECORD.md)
- [Post-freeze acceptance](STAGE11_POST_FREEZE_ACCEPTANCE_AUDIT.md)

## Important post-freeze amendments

```text
Share RecoveryBasis
= PrimaryAssignedDamage + SharedAssignedDamage

BaseRecovery
= CEIL(RecoveryBasis × EffectiveLifeStealRatio)

ModifiedRecovery
= CEIL(BaseRecovery × EffectiveRecoveryModifier)
```

690086 DSTS9-B02、690099 6% inclusive threshold、690221 ACTIVE/DOT applicability 均已由 Stage13 后续权威关闭并集成。Stage11 README 不再保留这些历史债务为当前状态。

Stage11 的设计审计草稿、planning 和重复过程账本不再作为当前权威；历史可由 Git history 追溯。
