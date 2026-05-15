# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 7 §2 — TM2-WORKS-S01 … TM2-WORKS-S13 scenario catalogue (P12-01 harness).

Rows are copied verbatim from
``docs/prompts/tender management/7. tender_module_v_2_seed_data_specification.md`` §2.
**S-01** through **S-13** have execution-grade modules under ``tests/scenarios/test_tm2_works_sNN.py``
(including **S-01** happy-path P6→P7 chain in ``test_tm2_works_s01.py``).
Doc-7 §1 **golden** row execution (``TND-MOH-2026-001`` / §6 JSON) remains future **N** harness work.
**S-02** has ``test_S_02_*`` in ``tests/scenarios/test_tm2_works_s02.py`` (DEM not current →
``submit_tender_for_publication_review`` denied; aligns with **O-01** / TM2-SMOKE-READ-001).
**S-03** has ``test_S_03_*`` in ``tests/scenarios/test_tm2_works_s03.py`` (addendum BOQ+deadline
impact, issue regenerates outputs + snapshot, supplier ack stub, timeline patch; **P5-05**).
**S-04** has ``test_S_04_*`` in ``tests/scenarios/test_tm2_works_s04.py`` (``convert_clarification_to_addendum``;
**P5-02**).
**S-05** has ``test_S_05_*`` in ``tests/scenarios/test_tm2_works_s05.py`` (late ``submit_bid``;
**P6-06** / **EX-14**).
**S-06** has ``test_S_06_*`` in ``tests/scenarios/test_tm2_works_s06.py`` (``close_tender`` zero bids +
``mark_retender_required``; **P7-01** / **P4-08**).
**S-07** has ``test_S_07_*`` in ``tests/scenarios/test_tm2_works_s07.py`` (``cancel_tender`` on **Published** +
``submit_bid`` gate; **P4-08** / **P6-05**).
**S-08** has ``test_S_08_*`` in ``tests/scenarios/test_tm2_works_s08.py`` (``supersede_tender`` lineage;
**P4-08**).
**S-09** has ``test_S_09_*`` in ``tests/scenarios/test_tm2_works_s09.py`` (``AUTH_SUPPLIER_INELIGIBLE`` on
``start_bid_draft`` / ``submit_bid``; **P6-01** / doc 9 §11.1).
**S-10** has ``test_S_10_*`` in ``tests/scenarios/test_tm2_works_s10.py`` (``AUTH_ADDENDUM_ACK_REQUIRED`` on
``start_bid_draft`` / ``submit_bid``; **P6-02** / **P10-07** pattern).
**S-11** has ``test_S_11_*`` in ``tests/scenarios/test_tm2_works_s11.py`` (``get_bid_content`` →
``AUTH_SEALED_BID_DENIED`` + **Access Denied** audit; **P6-07** / **EX-11** / doc 8 SEAL-001/002).
**S-12** has ``test_S_12_*`` in ``tests/scenarios/test_tm2_works_s12.py`` (``AUTH_CONTRACT_PRICE_SOURCE_INVALID``
then corrected ``create_contract_handoff_reference``; **P7-04** / **EX-10** / doc 8 CON-003).
**S-13** has ``test_S_13_*`` in ``tests/scenarios/test_tm2_works_s13.py`` (**P11-03** scan + **P11-01** /
``AUTH_LEGACY_PATH_DENIED`` on **Procurement Tender**; **EX-20**).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TM2WorksScenarioSpec:
	"""One doc-7 §2 Works Open Tender scenario row."""

	code: str
	name: str
	purpose: str
	expected_result: str


_TM2_WORKS_SCENARIOS: tuple[TM2WorksScenarioSpec, ...] = (
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S01",
		name="Happy Path Works Tender",
		purpose="Full lifecycle from package to contract handoff",
		expected_result=(
			"Successful publication, submissions, opening readiness, evaluation handoff, contract handoff"
		),
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S02",
		name="STD Readiness Blocked",
		purpose="Verify publication blocked when DEM is missing",
		expected_result="Tender cannot submit for publication review",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S03",
		name="Addendum Affecting BOQ and Deadline",
		purpose=(
			"Verify impact analysis, revised outputs, supplier acknowledgement, and deadline extension"
		),
		expected_result=(
			"Addendum issued; revised BOQ and timeline; supplier acknowledgement required"
		),
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S04",
		name="Clarification Escalated to Addendum",
		purpose="Verify clarification cannot materially alter tender outside addendum",
		expected_result="Clarification converted to addendum",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S05",
		name="Late Submission Rejection",
		purpose="Verify server-time deadline enforcement",
		expected_result="Late attempt rejected and audited",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S06",
		name="No Valid Submissions",
		purpose="Verify closure and retender path",
		expected_result="Tender closed with no valid submissions; retender required",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S07",
		name="Tender Cancellation Before Closing",
		purpose="Verify cancellation governance and supplier notification",
		expected_result="Tender cancelled; no further submissions",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S08",
		name="Retender / Superseding Tender",
		purpose="Verify lineage from cancelled/failed tender",
		expected_result="New tender linked to original",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S09",
		name="Supplier Eligibility Block",
		purpose="Verify ineligible supplier cannot submit",
		expected_result="Supplier blocked before bid preparation/submission",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S10",
		name="Addendum Acknowledgement Failure",
		purpose="Verify missing acknowledgement blocks submission",
		expected_result="Submission blocked and audited",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S11",
		name="Sealed Bid Access Denial",
		purpose="Verify internal access attempt before opening is denied",
		expected_result="Access denied and audited",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S12",
		name="Contract Price Source Validation",
		purpose="Verify contract uses corrected evaluated BOQ total",
		expected_result="Contract handoff rejects submitted uncorrected total",
	),
	TM2WorksScenarioSpec(
		code="TM2-WORKS-S13",
		name="Legacy Manual Rule Injection Denial",
		purpose="Verify v1-style manual rule creation is impossible",
		expected_result=(
			"Manual submission/opening/evaluation rule injection denied and audited"
		),
	),
)

_BY_CODE: dict[str, TM2WorksScenarioSpec] = {s.code: s for s in _TM2_WORKS_SCENARIOS}


def tm2_works_scenarios() -> tuple[TM2WorksScenarioSpec, ...]:
	"""All thirteen doc-7 §2 scenarios in stable order (S01 … S13)."""
	return _TM2_WORKS_SCENARIOS


def scenario_by_code(code: str) -> TM2WorksScenarioSpec:
	"""Return the scenario spec for ``TM2-WORKS-SNN``."""
	key = (code or "").strip()
	found = _BY_CODE.get(key)
	if not found:
		known = ", ".join(sorted(_BY_CODE))
		raise KeyError(f"Unknown TM2 Works scenario code {key!r}. Known: {known}")
	return found


def iter_tm2_works_scenario_codes() -> Iterator[str]:
	for spec in _TM2_WORKS_SCENARIOS:
		yield spec.code


def scenario_tracker_slug(spec: TM2WorksScenarioSpec) -> str:
	"""Map ``TM2-WORKS-S01`` → tracker-style ``S-01`` (IMPLEMENTATION_TRACKER §S)."""
	if not spec.code.startswith("TM2-WORKS-S"):
		raise ValueError(f"Unexpected scenario code: {spec.code!r}")
	num = spec.code.removeprefix("TM2-WORKS-S")
	if not num.isdigit():
		raise ValueError(f"Unexpected scenario code suffix: {spec.code!r}")
	return f"S-{int(num):02d}"
