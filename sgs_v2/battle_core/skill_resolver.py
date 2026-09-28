from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .context import BattleContext
from .effects import ApplyStateEffect, DamageEffect, Effect, EffectSourceRef
from .enums import DamageSourceType
from .operation_identity import SourceType
from .provider_identity import SkillProviderRef
from .skill_definition import (
    ApplyStateSkillEffectSpec,
    DamageSkillEffectSpec,
    SkillEffectSpec,
    SkillTargetMode,
)
from .skill_operation_admission import (
    SkillOperationAdmissionCoordinator,
    SkillOperationAdmissionRequest,
)
from .skill_permission import SkillOperationKind
from .skill_runtime import SkillRuntime
from .skill_target_policy import SkillTargetPolicy, TargetPolicyBoundary
from .target_operation import (
    TargetCardinality,
    TargetEligibilityContext,
    TargetOperation,
    TargetOperationDomain,
    TargetOperationProducer,
    TargetPurpose,
    TargetRelation,
    TargetSelectionProvenance,
    TargetSelectionResult,
    TargetSelectorKind,
)
from .target_system import TargetSystem
from .unit import UnitRuntime


class SkillResolutionStatus(str, Enum):
    DISABLED = "DISABLED"
    NO_VALID_TARGET = "NO_VALID_TARGET"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True, slots=True)
class SkillResolutionResult:
    """一次明确技能解析尝试的不可变结果。"""

    skill_id: str
    owner_id: str
    status: SkillResolutionStatus
    target_ids: tuple[str, ...]
    effects: tuple[Effect, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.skill_id, str) or not self.skill_id.strip():
            raise ValueError("skill_id cannot be empty")
        if not isinstance(self.owner_id, str) or not self.owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if not isinstance(self.status, SkillResolutionStatus):
            raise TypeError("status must be a SkillResolutionStatus")

        target_ids = tuple(self.target_ids)
        effects = tuple(self.effects)
        object.__setattr__(self, "target_ids", target_ids)
        object.__setattr__(self, "effects", effects)

        if self.status is SkillResolutionStatus.RESOLVED:
            if not target_ids:
                raise ValueError("RESOLVED result must contain target_ids")
            if not effects:
                raise ValueError("RESOLVED result must contain effects")
        elif target_ids or effects:
            raise ValueError(
                f"{self.status.value} result must not contain targets or effects"
            )


class SkillResolver:
    """把一次显式技能解析转换成有序 Effect，不执行任何 Effect。"""

    def __init__(
        self,
        target_system: TargetSystem,
        *,
        admission_coordinator: SkillOperationAdmissionCoordinator | None = None,
        target_policy: SkillTargetPolicy | None = None,
    ) -> None:
        if not isinstance(target_system, TargetSystem):
            raise TypeError("target_system must be a TargetSystem")
        if (
            admission_coordinator is not None
            and not isinstance(admission_coordinator, SkillOperationAdmissionCoordinator)
        ):
            raise TypeError(
                "admission_coordinator must be SkillOperationAdmissionCoordinator or None"
            )
        if target_policy is not None and not isinstance(target_policy, SkillTargetPolicy):
            raise TypeError("target_policy must be SkillTargetPolicy or None")
        self._target_system = target_system
        self._admission_coordinator = admission_coordinator
        self._target_policy = target_policy

    def resolve(
        self,
        context: BattleContext,
        runtime: SkillRuntime,
    ) -> SkillResolutionResult:
        definition = runtime.definition

        if not self._admitted(context, runtime):
            return self._empty_result(runtime, SkillResolutionStatus.DISABLED)

        owner = context.get_unit(runtime.owner_id)

        # Legacy compatibility preflight: Stage6 already guaranteed that an empty
        # raw pool short-circuits before activation RNG. It is enumeration only:
        # no TargetOperation and no selector RNG is created here.
        candidates = self._candidate_units(
            context,
            owner,
            definition,
        )
        if not candidates:
            return self._empty_result(
                runtime,
                SkillResolutionStatus.NO_VALID_TARGET,
            )

        if definition.activation_rate == 0.0:
            return self._empty_result(
                runtime,
                SkillResolutionStatus.ACTIVATION_FAILED,
            )
        if (
            definition.activation_rate < 1.0
            and not context.random.chance(definition.activation_rate)
        ):
            return self._empty_result(
                runtime,
                SkillResolutionStatus.ACTIVATION_FAILED,
            )

        selection = self._resolve_targets_after_activation(
            context,
            runtime,
            candidates,
        )
        if selection is None or not selection.target_ids:
            return self._empty_result(
                runtime,
                SkillResolutionStatus.NO_VALID_TARGET,
            )

        selected = [context.get_unit(target_id) for target_id in selection.target_ids]
        target_ids = selection.target_ids
        effects = tuple(
            self._build_effect(
                runtime=runtime,
                target=target,
                spec=spec,
            )
            for target in selected
            for spec in definition.effect_specs
        )

        return SkillResolutionResult(
            skill_id=definition.skill_id,
            owner_id=runtime.owner_id,
            status=SkillResolutionStatus.RESOLVED,
            target_ids=target_ids,
            effects=effects,
        )

    def _admitted(
        self,
        context: BattleContext,
        runtime: SkillRuntime,
    ) -> bool:
        if self._admission_coordinator is None or runtime.skill_slot is None:
            return runtime.enabled

        definition = runtime.definition
        provider_ref = SkillProviderRef(
            owner_id=runtime.owner_id,
            skill_slot=runtime.skill_slot,
            skill_id=definition.skill_id,
        )
        decision = self._admission_coordinator.evaluate(
            context,
            SkillOperationAdmissionRequest(
                actor_id=runtime.owner_id,
                provider_ref=provider_ref,
                skill_type=definition.skill_type,
                preparation_mode=definition.preparation_mode,
                operation_kind=SkillOperationKind.NEW_ADMISSION,
            ),
        )
        return decision.admitted

    def _resolve_targets_after_activation(
        self,
        context: BattleContext,
        runtime: SkillRuntime,
        candidates: list[UnitRuntime],
    ) -> TargetSelectionResult | None:
        if self._target_policy is None or runtime.skill_slot is None:
            selected = self._select_targets(
                context,
                candidates,
                runtime.definition,
            )
            if not selected:
                return None
            return TargetSelectionResult(
                operation_id=context.id_allocator.allocate_target_operation_id(),
                target_ids=tuple(item.unit_id for item in selected),
                provenance=TargetSelectionProvenance.FRESH_SELECTED,
            )

        operation = self._new_target_operation(context, runtime)
        decision = self._target_policy.evaluate(context, operation, candidates)
        if decision.boundary is TargetPolicyBoundary.UNSUPPORTED:
            raise ValueError("unsupported Skill target-policy boundary")

        eligible_by_id = {
            candidate.unit_id: candidate
            for candidate in candidates
            if candidate.unit_id in decision.eligible_candidate_ids
        }
        eligible = [
            candidate
            for candidate in candidates
            if candidate.unit_id in eligible_by_id
        ]
        if not eligible:
            return None

        selected = self._select_policy_targets(
            context,
            operation,
            eligible,
            decision.required_target_ids,
        )
        if not selected:
            return None
        return TargetSelectionResult(
            operation_id=operation.operation_id,
            target_ids=tuple(item.unit_id for item in selected),
            provenance=TargetSelectionProvenance.FRESH_SELECTED,
        )

    @staticmethod
    def _target_contract(definition):
        """Canonicalize SkillDefinition producer intent into TargetOperation metadata."""

        mode = definition.target_mode
        if mode is SkillTargetMode.SINGLE_RANDOM_ENEMY:
            return (
                TargetRelation.ENEMY,
                TargetCardinality.SINGLE,
                TargetSelectorKind.RANDOM,
                TargetPurpose.HOSTILE,
                None,
            )
        if mode is SkillTargetMode.SINGLE_DETERMINISTIC_ENEMY:
            return (
                TargetRelation.ENEMY,
                TargetCardinality.SINGLE,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.HOSTILE,
                None,
            )
        if mode is SkillTargetMode.CHOOSE_N_RANDOM_ENEMIES:
            return (
                TargetRelation.ENEMY,
                TargetCardinality.CHOOSE_N,
                TargetSelectorKind.RANDOM,
                TargetPurpose.HOSTILE,
                definition.target_count,
            )
        if mode is SkillTargetMode.CHOOSE_N_DETERMINISTIC_ENEMIES:
            return (
                TargetRelation.ENEMY,
                TargetCardinality.CHOOSE_N,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.HOSTILE,
                definition.target_count,
            )
        if mode is SkillTargetMode.FIXED_ALL_ENEMIES:
            return (
                TargetRelation.ENEMY,
                TargetCardinality.FIXED_ALL,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.HOSTILE,
                None,
            )
        if mode is SkillTargetMode.SINGLE_RANDOM_ALLY:
            return (
                TargetRelation.ALLY,
                TargetCardinality.SINGLE,
                TargetSelectorKind.RANDOM,
                TargetPurpose.FRIENDLY_SUPPORT,
                None,
            )
        if mode is SkillTargetMode.SINGLE_DETERMINISTIC_ALLY:
            return (
                TargetRelation.ALLY,
                TargetCardinality.SINGLE,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.FRIENDLY_SUPPORT,
                None,
            )
        if mode is SkillTargetMode.CHOOSE_N_RANDOM_ALLIES:
            return (
                TargetRelation.ALLY,
                TargetCardinality.CHOOSE_N,
                TargetSelectorKind.RANDOM,
                TargetPurpose.FRIENDLY_SUPPORT,
                definition.target_count,
            )
        if mode is SkillTargetMode.CHOOSE_N_DETERMINISTIC_ALLIES:
            return (
                TargetRelation.ALLY,
                TargetCardinality.CHOOSE_N,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.FRIENDLY_SUPPORT,
                definition.target_count,
            )
        if mode is SkillTargetMode.FIXED_ALL_ALLIES:
            return (
                TargetRelation.ALLY,
                TargetCardinality.FIXED_ALL,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.FRIENDLY_SUPPORT,
                None,
            )
        if mode is SkillTargetMode.SELF:
            return (
                TargetRelation.SELF,
                TargetCardinality.SINGLE,
                TargetSelectorKind.DETERMINISTIC,
                TargetPurpose.SELF,
                None,
            )
        raise ValueError(f"unsupported target mode: {mode}")

    def _new_target_operation(
        self,
        context: BattleContext,
        runtime: SkillRuntime,
    ) -> TargetOperation:
        definition = runtime.definition
        if runtime.skill_slot is None:
            raise ValueError("canonical TargetOperation requires a SkillSlot")

        (
            relation,
            cardinality,
            selector_kind,
            purpose,
            requested_count,
        ) = self._target_contract(definition)

        provider_ref = SkillProviderRef(
            owner_id=runtime.owner_id,
            skill_slot=runtime.skill_slot,
            skill_id=definition.skill_id,
        )
        return TargetOperationProducer.new_query(
            context,
            actor_id=runtime.owner_id,
            producer_ref=provider_ref,
            admitted_operation_key=(
                f"skill:{runtime.owner_id}:{int(runtime.skill_slot)}:"
                f"{definition.skill_id}"
            ),
            relation=relation,
            cardinality=cardinality,
            selector_kind=selector_kind,
            eligibility_context=TargetEligibilityContext(
                domain=TargetOperationDomain.SKILL,
                purpose=purpose,
                restriction_keys=definition.target_restriction_keys,
            ),
            requested_count=requested_count,
        )

    def _candidate_units(
        self,
        context: BattleContext,
        owner: UnitRuntime,
        definition,
    ) -> list[UnitRuntime]:
        relation, _, _, _, _ = self._target_contract(definition)
        if relation is TargetRelation.ENEMY:
            return self._target_system.enemies(
                context,
                owner,
                alive_only=True,
            )
        if relation is TargetRelation.ALLY:
            return self._target_system.allies(
                context,
                owner,
                alive_only=True,
                include_self=False,
            )
        if relation is TargetRelation.SELF:
            return [owner] if owner.is_alive else []
        raise ValueError(f"unsupported target relation: {relation}")

    def _select_targets(
        self,
        context: BattleContext,
        candidates: list[UnitRuntime],
        definition,
    ) -> list[UnitRuntime]:
        _, cardinality, selector_kind, _, requested_count = self._target_contract(
            definition
        )
        if cardinality is TargetCardinality.FIXED_ALL:
            return list(candidates)

        count = 1 if cardinality is TargetCardinality.SINGLE else requested_count
        assert count is not None
        if selector_kind is TargetSelectorKind.RANDOM:
            return self._target_system.random_units(
                context,
                candidates,
                count=count,
            )
        if selector_kind is TargetSelectorKind.DETERMINISTIC:
            return list(candidates[:count])
        raise ValueError(
            f"unsupported producer selector without explicit target ids: {selector_kind}"
        )

    def _select_policy_targets(
        self,
        context: BattleContext,
        operation: TargetOperation,
        candidates: list[UnitRuntime],
        required_target_ids: tuple[str, ...],
    ) -> list[UnitRuntime]:
        by_id = {item.unit_id: item for item in candidates}
        required = [
            by_id[target_id]
            for target_id in required_target_ids
            if target_id in by_id
        ]

        if operation.cardinality is TargetCardinality.FIXED_ALL:
            return list(candidates)

        count = (
            1
            if operation.cardinality is TargetCardinality.SINGLE
            else operation.requested_count
        )
        assert count is not None

        # BU-P09 remains an explicit unsupported boundary for canonical
        # CHOOSE_N production operations. Do not silently promote the legacy
        # TargetSystem min(count, legal_count) fallback into the Stage12 law.
        if (
            operation.cardinality is TargetCardinality.CHOOSE_N
            and len(candidates) < count
        ):
            raise ValueError(
                "unsupported Skill target-policy boundary: insufficient candidates"
            )

        if len(required) > count:
            raise ValueError("required targets exceed target cardinality")
        remaining = [
            item for item in candidates if item.unit_id not in required_target_ids
        ]
        slots = count - len(required)

        if operation.selector_kind is TargetSelectorKind.RANDOM:
            tail = self._target_system.random_units(
                context,
                remaining,
                count=slots,
            )
        elif operation.selector_kind is TargetSelectorKind.DETERMINISTIC:
            tail = remaining[:slots]
        elif operation.selector_kind is TargetSelectorKind.EXPLICIT:
            if slots:
                raise ValueError("EXPLICIT selector requires fully specified targets")
            tail = []
        else:
            raise ValueError(f"unsupported selector: {operation.selector_kind}")

        return required + tail

    @staticmethod
    def _build_effect(
        *,
        runtime: SkillRuntime,
        target: UnitRuntime,
        spec: SkillEffectSpec,
    ) -> Effect:
        definition = runtime.definition
        source_ref = EffectSourceRef(
            stage9_source_type=SourceType.ACTIVE_SKILL,
            source_unit_id=runtime.owner_id,
            source_skill_id=definition.skill_id,
            source_skill_slot=runtime.skill_slot,
        )
        if isinstance(spec, DamageSkillEffectSpec):
            return DamageEffect(
                source_id=runtime.owner_id,
                target_id=target.unit_id,
                damage_type=spec.damage_type,
                source_type=DamageSourceType.SKILL,
                coefficient=spec.coefficient,
                source_skill_id=definition.skill_id,
                source_ref=source_ref,
            )
        if isinstance(spec, ApplyStateSkillEffectSpec):
            return ApplyStateEffect(
                state_id=spec.state_id,
                owner_id=target.unit_id,
                source_id=runtime.owner_id,
                source_skill_id=definition.skill_id,
                source_ref=source_ref,
            )
        raise TypeError(f"unsupported skill effect spec: {type(spec).__name__}")

    @staticmethod
    def _empty_result(
        runtime: SkillRuntime,
        status: SkillResolutionStatus,
    ) -> SkillResolutionResult:
        return SkillResolutionResult(
            skill_id=runtime.definition.skill_id,
            owner_id=runtime.owner_id,
            status=status,
            target_ids=(),
            effects=(),
        )
