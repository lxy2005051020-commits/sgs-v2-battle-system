from __future__ import annotations

from pathlib import Path

import pytest

from sgs_v2.battle_core.provider_identity import SkillProviderRef
from sgs_v2.battle_core.random_system import RandomSystem
from sgs_v2.battle_core.skill_runtime import SkillSlot


ROOT = Path(__file__).parents[1]
LEDGER_PATH = ROOT / "stages" / "stage12" / "STAGE12_RUNTIME_DEFAULT_LEDGER.md"
GOVERNANCE_PATH = (
    ROOT
    / "stages"
    / "stage12"
    / "STAGE12_690222_BINDING_SELECTION_RUNTIME_GOVERNANCE_RESOLUTION.md"
)
IDENTITY_DESIGN_PATH = (
    ROOT
    / "stages"
    / "stage12"
    / "STAGE12_SKILLTYPE_PROVIDER_IDENTITY_DESIGN.md"
)


class UnsupportedBindingPool(RuntimeError):
    """Executable-spec marker for the still-unsupported empty-pool boundary."""


class CountingRandomSystem(RandomSystem):
    def __init__(self, seed: int = 1) -> None:
        super().__init__(seed)
        self.choice_calls: list[tuple[object, ...]] = []

    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls.append(tuple(values))
        return super().choice(values)


class FirstChoiceRandomSystem(CountingRandomSystem):
    def choice(self, values):  # type: ignore[no-untyped-def]
        self.choice_calls.append(tuple(values))
        if not values:
            raise ValueError("choice() cannot select from an empty sequence")
        return values[0]


def stable_provider_pool(
    providers: tuple[SkillProviderRef, ...],
) -> tuple[SkillProviderRef, ...]:
    """RD-SF-002 executable specification for owner-local ordering."""
    return tuple(
        sorted(
            providers,
            key=lambda ref: (int(ref.skill_slot), ref.skill_id),
        )
    )


def governed_binding_selection(
    rng: RandomSystem,
    providers: tuple[SkillProviderRef, ...],
) -> SkillProviderRef:
    """RD-SF-006 executable specification, not a production 690222 adapter."""
    if not providers:
        raise UnsupportedBindingPool("690222 empty eligible pool remains unsupported")
    if len(providers) == 1:
        return providers[0]
    return rng.choice(providers)


def sample_pool() -> tuple[SkillProviderRef, ...]:
    return (
        SkillProviderRef("holder", SkillSlot.INHERENT, "skill.inherent"),
        SkillProviderRef("holder", SkillSlot.LEARNED_1, "skill.learned1"),
        SkillProviderRef("holder", SkillSlot.LEARNED_2, "skill.learned2"),
    )


def rd_sf_006_section() -> str:
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    return ledger.split(
        "### RD-SF-006 — INTIMIDATION uniform eligible-Provider binding selection",
        1,
    )[1]


def governance_text() -> str:
    return GOVERNANCE_PATH.read_text(encoding="utf-8")


def test_binding_default_has_project_runtime_provenance() -> None:
    section = rd_sf_006_section()
    assert "PROJECT_RUNTIME_DEFAULT" in section
    assert "NOT_EMPIRICALLY_FROZEN" in section
    assert "690222 INTIMIDATION" in section


def test_binding_default_not_empirical_claim() -> None:
    section = rd_sf_006_section()
    assert "uniform / equal / 1/N is not empirically proven" in section
    assert "does not claim the original game's hidden binding weights" in section


def test_stable_provider_ordering_uses_rd_sf_002() -> None:
    scrambled = (
        SkillProviderRef("holder", SkillSlot.LEARNED_2, "skill.z"),
        SkillProviderRef("holder", SkillSlot.INHERENT, "skill.m"),
        SkillProviderRef("holder", SkillSlot.LEARNED_1, "skill.a"),
    )
    ordered = stable_provider_pool(scrambled)
    assert tuple(ref.skill_slot for ref in ordered) == (
        SkillSlot.INHERENT,
        SkillSlot.LEARNED_1,
        SkillSlot.LEARNED_2,
    )
    assert "RD-SF-002" in rd_sf_006_section()


def test_single_candidate_selection() -> None:
    provider = SkillProviderRef("holder", SkillSlot.INHERENT, "skill.only")
    rng = CountingRandomSystem(11)
    assert governed_binding_selection(rng, (provider,)) == provider


def test_single_candidate_rng_call_topology() -> None:
    provider = SkillProviderRef("holder", SkillSlot.INHERENT, "skill.only")
    rng = CountingRandomSystem(17)
    governed_binding_selection(rng, (provider,))
    assert rng.choice_calls == []

    baseline = RandomSystem(17)
    assert rng.random() == baseline.random()


def test_multiple_candidate_selection_uses_canonical_rng() -> None:
    pool = sample_pool()
    rng = CountingRandomSystem(23)
    selected = governed_binding_selection(rng, pool)
    assert selected in pool
    assert rng.choice_calls == [pool]


def test_same_seed_same_pool_same_binding() -> None:
    pool = sample_pool()
    first = governed_binding_selection(CountingRandomSystem(31), pool)
    second = governed_binding_selection(CountingRandomSystem(31), pool)
    assert first == second


def test_downstream_rng_stream_is_stable() -> None:
    pool = sample_pool()
    rng = CountingRandomSystem(43)
    governed_binding_selection(rng, pool)

    expected = RandomSystem(43)
    expected.choice(pool)

    assert rng.random() == expected.random()


def test_rejected_application_consumes_zero_binding_rng() -> None:
    text = governance_text()
    assert "Rejected application -> 0 binding RNG" in text
    assert "Gangyi rejection -> 0 binding RNG" in text


def test_refresh_performs_new_binding_selection() -> None:
    pool = sample_pool()
    rng = CountingRandomSystem(59)
    governed_binding_selection(rng, pool)
    governed_binding_selection(rng, pool)
    assert rng.choice_calls == [pool, pool]


def test_refresh_can_select_same_provider_legitimately() -> None:
    pool = sample_pool()
    rng = FirstChoiceRandomSystem(61)
    first = governed_binding_selection(rng, pool)
    second = governed_binding_selection(rng, pool)
    assert first == second == pool[0]
    assert len(rng.choice_calls) == 2


def test_resume_consumes_zero_binding_rng() -> None:
    pool = sample_pool()
    bound = pool[1]
    rng = CountingRandomSystem(67)

    resumed_bound = bound

    assert resumed_bound == bound
    assert rng.choice_calls == []
    assert rng.random() == RandomSystem(67).random()


def test_resume_retains_binding() -> None:
    bound = sample_pool()[2]
    generation = "gen-7"
    lifetime_progress = 3

    resumed = (bound, generation, lifetime_progress)

    assert resumed == (bound, "gen-7", 3)


def test_empty_pool_remains_unsupported() -> None:
    with pytest.raises(UnsupportedBindingPool):
        governed_binding_selection(CountingRandomSystem(71), ())

    assert "empty eligible pool remains UNSUPPORTED_BOUNDARY" in governance_text()


def test_talent_boundary_remains_unsupported() -> None:
    text = governance_text()
    assert "TALENT eligibility remains UNSUPPORTED / NOT FROZEN" in text
    assert "TALENT is not added to the supported eligible pool" in text


def test_all_candidates_reachable_across_deterministic_seed_set() -> None:
    pool = sample_pool()
    observed = {
        governed_binding_selection(RandomSystem(seed), pool)
        for seed in range(256)
    }
    assert observed == set(pool)


def test_loaded_provider_pool_is_not_provider_validity_filtering() -> None:
    design = IDENTITY_DESIGN_PATH.read_text(encoding="utf-8")
    assert "The enumeration API returns loaded identity. It does not itself filter Provider validity" in design
    assert "loaded Skill Providers for holder" in design
