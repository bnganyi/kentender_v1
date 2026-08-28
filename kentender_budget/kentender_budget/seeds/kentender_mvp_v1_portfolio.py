# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Budget seed — BUD-CHG-001 v1.2 §15 deterministic contract.

Drives the real Budget Version lifecycle commands (save_budget_version_draft,
save_budget_lines_draft, submit_budget_version, approve_budget_version) as
the named role actors, not Administrator (§15.8) — this is a genuine
end-to-end exercise of the same domain rules the real UI uses, not a
raw-insert shortcut. The only post-hoc correction is the lifecycle
timestamps: the real commands stamp `now_datetime()` and accept no caller
override, but §15.3/§15.6/§15.7's own narrative dates read naturally as a
short history ending before "today" — so every timestamp here is expressed
as an offset from `nowdate()` at seed-run time (never a fixed calendar
date), which keeps the seed valid indefinitely and satisfies
`Budget Version.validate()`'s own "approval date cannot be in the future"
guard (there is no fixture-clock override for Budget, unlike some other
modules' seeds).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, flt, now_datetime, nowdate

from kentender_budget.services.budget_authorization import CAP_APPROVE, CAP_EDIT
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_core.seeds.kentender_mvp_v1 import constants as C

FIXTURE_NS = C.FIXTURE_NS
FY = "FY-2027-2028"
FUNDING_SOURCE = "Government of Kenya"


def _offset_date(days_ago: int) -> str:
	return add_days(nowdate(), -days_ago)


def _offset_datetime(days_ago: int, time_str: str):
	from frappe.utils import get_datetime

	return get_datetime(f"{add_days(nowdate(), -days_ago)} {time_str}")


def _set_version_timestamps(
	version_name: str, *, submitted_at=None, decided_at=None
) -> None:
	updates: dict[str, Any] = {}
	if submitted_at:
		updates["submitted_at"] = submitted_at
	if decided_at:
		updates["decided_at"] = decided_at
	if updates:
		frappe.db.set_value("Budget Version", version_name, updates, update_modified=False)


def _set_event_timestamps(budget_version: str, event_type: str, event_at) -> None:
	"""Correct every ledger row of one event_type for this version to the
	narrative offset — safe_record_event only ever writes one row per call
	site per version for these lifecycle events."""
	for name in frappe.get_all(
		"Budget Audit Event",
		filters={"budget_version": budget_version, "event_type": event_type},
		pluck="name",
	):
		frappe.db.set_value("Budget Audit Event", name, "event_at", event_at, update_modified=False)


def _as_user(email: str):
	frappe.set_user(email)


def _budget_version_active(generated_reference: str) -> str | None:
	return frappe.db.get_value(
		"Budget Version", {"generated_reference": generated_reference, "status": "Active"}, "name"
	)


def _upsert_active_baseline(
	*,
	pe: str,
	fy: str,
	officer: str,
	approver: str,
	budget_ref: str,
	version_ref: str,
	approval_reference: str,
	authorised_total: float,
	approval_document: str,
	lines: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
	"""§15.3/§15.7 — one Active Budget Version with its Budget Lines, driven
	through the real Officer-submit / Approver-approve commands. Idempotent:
	if a Budget Version with this exact generated_reference is already
	Active, the baseline is already correct and nothing is re-run (§15.8:
	"a second seed run produces no semantic change")."""
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc
	from kentender_budget.services import budget_readiness_contracts as readiness

	existing = _budget_version_active(version_ref)
	if existing:
		version = frappe.get_doc("Budget Version", existing)
		return {"budget": version.budget, "version": existing, "created": False}

	prior_user = frappe.session.user
	try:
		_as_user(officer)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": pe,
				"financial_year": fy,
				"approval_reference": approval_reference,
				"approval_date": _offset_date(60),
				"authorised_total": authorised_total,
				"approval_document": approval_document,
			}
		)
		if not result.get("ok"):
			frappe.throw(f"Budget seed: could not create {budget_ref} draft: {result.get('errors')}")
		budget_name = result["budget"]["id"]
		version_name = result["version"]["id"]

		# allocate_budget_reference's own naming Series is never rolled back by
		# clearing Budget rows (standard Frappe series behaviour — a deleted
		# record's number is not freed), so a reused dev site's next allocation
		# drifts upward every seed/clear cycle instead of reproducing this
		# exact id. §15.8 requires the exact stable identifier regardless —
		# rename both the Budget and its Version to the deterministic §15.3/
		# §15.7 ids directly; every subsequent call in this function chains on
		# the real docnames (budget_name/version_name), never generated_reference,
		# so renaming here is safe at any point in the flow.
		frappe.db.set_value("Budget", budget_name, "generated_reference", budget_ref, update_modified=False)
		frappe.db.set_value("Budget Version", version_name, "generated_reference", version_ref, update_modified=False)

		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version_name,
				"lines": [
					{
						"title": ln["title"],
						"owner_org_unit": ln.get("owner_org_unit") or "",
						"funding_source": FUNDING_SOURCE,
						"approved_amount": ln["approved_amount"],
					}
					for ln in lines
				],
			}
		)
		if not lines_result.get("ok"):
			frappe.throw(f"Budget seed: could not save {budget_ref} lines: {lines_result.get('errors')}")

		# Budget Line generated_reference is likewise auto-allocated (never
		# reset by clearing) — rename each newly created line to its exact
		# §15.3/§15.7 code, matched by title (unambiguous within one version).
		title_to_line = {
			r.title: r.budget_line
			for r in frappe.get_all("Budget Line Version", filters={"budget_version": version_name}, fields=["title", "budget_line"])
		}
		for ln in lines:
			if ln.get("code"):
				line_name = title_to_line.get(ln["title"])
				if not line_name:
					frappe.throw(f"Budget seed: could not find newly created line {ln['title']!r} to rename")
				frappe.db.set_value("Budget Line", line_name, "generated_reference", ln["code"], update_modified=False)

		submit_result = readiness.submit_budget_version({"budget_version": version_name})
		if not submit_result.get("ok"):
			frappe.throw(f"Budget seed: could not submit {version_ref}: {submit_result.get('blockers')}")
		_set_event_timestamps(version_name, "Budget version created", _offset_datetime(55, "09:20:00"))
		_set_event_timestamps(version_name, "Draft approval details saved", _offset_datetime(52, "15:55:00"))
		_set_event_timestamps(version_name, "Draft lines saved", _offset_datetime(52, "15:55:00"))
		_set_event_timestamps(version_name, "Budget version submitted", _offset_datetime(50, "16:20:00"))
		_set_version_timestamps(version_name, submitted_at=_offset_datetime(50, "16:20:00"))

		_as_user(approver)
		approve_result = readiness.approve_budget_version({"budget_version": version_name})
		if not approve_result.get("ok"):
			frappe.throw(f"Budget seed: could not approve {version_ref}: {approve_result.get('blockers')}")
		_set_event_timestamps(
			version_name, "Budget version approved and activated", _offset_datetime(48, "11:15:00")
		)
		_set_version_timestamps(version_name, decided_at=_offset_datetime(48, "11:15:00"))

		return {"budget": budget_name, "version": version_name, "created": True}
	finally:
		frappe.set_user(prior_user)


def _resolve_line_ids(budget_version: str) -> dict[str, str]:
	"""Budget Line generated_reference -> Budget Line name, for this version."""
	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": budget_version},
		fields=["budget_line"],
	)
	names = [r.budget_line for r in rows]
	if not names:
		return {}
	return {
		r.name: r.generated_reference
		for r in frappe.get_all("Budget Line", filters={"name": ["in", names]}, fields=["name", "generated_reference"])
	}


def upsert_kentender_mvp_v1_portfolio(*, include_test_edges: bool = True, commit: bool = True) -> dict[str, Any]:
	"""Idempotent canonical Budget portfolio seed.

	`include_test_edges=False` (the canonical orchestrator's own call shape,
	see kentender_core.seeds.kentender_mvp_v1.budget.upsert_budget) seeds
	only the MOH Active baseline (§15.3) and the Kisumu isolation baseline
	(§15.7) — the exact deterministic default demo pack. `include_test_edges
	=True` additionally seeds the isolated successor Version 2 (§15.6),
	left Submitted-for-approval/undecided, and the isolated Finance/
	commitment test profiles (§15.5) via `upsert_isolated_finance_profiles`.
	"""
	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	ensure_currency_kes()
	pe_moh = ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH")
	pe_cgk = ensure_procuring_entity(
		C.PE_CGKIS, C.PE_CGKIS_NAME, entity_type="County Government", short_name="Kisumu"
	)

	moh = _upsert_active_baseline(
		pe=pe_moh,
		fy=FY,
		officer=C.USER_BUD_OFFICER,
		approver=C.USER_BUD_APPROVER,
		budget_ref=C.BUD_ACTIVE,
		version_ref=C.BUD_ACTIVE_V1,
		approval_reference="MOH-FIN-BUD-2027-01 (Demo)",
		authorised_total=160_000_000,
		approval_document="/files/moh-approved-procurement-budget-2027-28-demo.pdf",
		lines=(
			{
				"title": "Digital health infrastructure programme",
				"owner_org_unit": C.OU_DIR_DHP,
				"approved_amount": 100_000_000,
				"code": C.BL_DHI_2027,
			},
			{
				"title": "Digital health workforce development",
				"owner_org_unit": C.OU_DIR_HRMD,
				"approved_amount": 60_000_000,
				"code": C.BL_HWD_2027,
			},
		),
	)

	cgk = _upsert_active_baseline(
		pe=pe_cgk,
		fy=FY,
		officer=C.USER_CGK_BUD_OFFICER,
		approver=C.USER_CGK_BUD_APPROVER,
		budget_ref=C.CGK_BUD_ACTIVE,
		version_ref=C.CGK_BUD_ACTIVE_V1,
		approval_reference="CGK-FIN-BUD-2027-01 (Demo)",
		authorised_total=20_000_000,
		approval_document="/files/kisumu-approved-procurement-budget-2027-28-demo.pdf",
		lines=(
			{
				"title": "County digital services",
				"owner_org_unit": "",  # PE-wide
				"approved_amount": 20_000_000,
				"code": C.CGK_BL_DIGSVC,
			},
		),
	)

	successor: dict[str, Any] | None = None
	if include_test_edges:
		successor = upsert_isolated_successor_version()

	if commit:
		frappe.db.commit()

	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"procuring_entity": pe_moh,
		"procuring_entity_cgkis": pe_cgk,
		"budgets": [b for b in (moh.get("budget"), cgk.get("budget")) if b],
		"codes": [C.BUD_ACTIVE, C.CGK_BUD_ACTIVE],
		"moh": moh,
		"cgk": cgk,
		"successor": successor,
		"include_test_edges": include_test_edges,
	}


def upsert_isolated_successor_version() -> dict[str, Any]:
	"""§15.6 — isolated successor Version 2 on the MOH baseline: Transfer,
	DHI 100m -> 90m, HWD 60m -> 70m, authorised total unchanged at 160m.
	Left Submitted-for-approval / undecided (populates the pending Approval
	task screens) — a *separate* isolated test copy is decided (returned or
	approved) by the tests that need that outcome, never this canonical seed
	(§15.8: isolated profiles are created/removed by their own tests)."""
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc
	from kentender_budget.services import budget_readiness_contracts as readiness

	existing = frappe.db.get_value("Budget Version", {"generated_reference": C.BUD_ACTIVE_V2}, "name")
	if existing:
		return {"version": existing, "created": False}

	active_name = _budget_version_active(C.BUD_ACTIVE_V1)
	if not active_name:
		frappe.throw("Budget seed: MOH Active baseline (Version 1) must exist before seeding the successor.")
	budget_name = frappe.db.get_value("Budget Version", active_name, "budget")
	budget_ref = frappe.db.get_value("Budget", budget_name, "generated_reference")

	prior_user = frappe.session.user
	try:
		_as_user(C.USER_BUD_OFFICER)
		result = contracts.create_budget_successor_version(
			budget_ref,
			{
				"revision_type": "Transfer",
				"approval_reference": "MOH-FIN-BUD-2027-02 (Demo)",
				"approval_date": _offset_date(15),
				"authorised_total": 160_000_000,
				"approval_document": "/files/moh-approved-procurement-budget-transfer-2027-28-demo.pdf",
			},
		)
		if not result.get("ok"):
			frappe.throw(f"Budget seed: could not create successor version: {result}")
		version_name = result["version"]["id"]
		_set_event_timestamps(version_name, "Budget version created", _offset_datetime(15, "13:10:00"))

		line_ids = _resolve_line_ids(active_name)  # {budget_line_name: code}
		by_code = {code: name for name, code in line_ids.items()}
		# A previously-Active line is identity-locked (BUD-BR-019): the server
		# silently holds title/owner_org_unit/funding_source at their prior
		# values regardless of what's sent, but the payload validation still
		# requires them non-empty upfront — the real editor always resends the
		# currently-loaded identity for a locked row (BudgetVersionEditorScreen
		# .vue's saveLinesOnly()), never blanks it.
		prior_identity = {
			r.budget_line: r
			for r in frappe.get_all(
				"Budget Line Version",
				filters={"budget_version": active_name},
				fields=["budget_line", "title", "owner_org_unit", "funding_source"],
			)
		}
		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version_name,
				"lines": [
					{
						"budget_line": by_code[C.BL_DHI_2027],
						"title": prior_identity[by_code[C.BL_DHI_2027]].title,
						"owner_org_unit": prior_identity[by_code[C.BL_DHI_2027]].owner_org_unit or "",
						"funding_source": prior_identity[by_code[C.BL_DHI_2027]].funding_source,
						"approved_amount": 90_000_000,
					},
					{
						"budget_line": by_code[C.BL_HWD_2027],
						"title": prior_identity[by_code[C.BL_HWD_2027]].title,
						"owner_org_unit": prior_identity[by_code[C.BL_HWD_2027]].owner_org_unit or "",
						"funding_source": prior_identity[by_code[C.BL_HWD_2027]].funding_source,
						"approved_amount": 70_000_000,
					},
				],
			}
		)
		if not lines_result.get("ok"):
			frappe.throw(f"Budget seed: could not save successor lines: {lines_result.get('errors')}")
		_set_event_timestamps(version_name, "Draft lines saved", _offset_datetime(14, "15:55:00"))

		submit_result = readiness.submit_budget_version({"budget_version": version_name})
		if not submit_result.get("ok"):
			frappe.throw(f"Budget seed: could not submit successor version: {submit_result.get('blockers')}")
		_set_event_timestamps(version_name, "Budget version submitted", _offset_datetime(14, "16:20:00"))
		_set_version_timestamps(version_name, submitted_at=_offset_datetime(14, "16:20:00"))

		return {"version": version_name, "created": True}
	finally:
		frappe.set_user(prior_user)


# --- §15.5 Isolated Finance and commitment profiles -------------------------
# Each profile resets to its own named precondition and does not coexist
# with the default integrated seed — callers (Playwright / domain tests)
# invoke exactly the one profile they need, never the whole set at once.


def _ensure_isolated_fy(start_year: int, pe: str) -> str:
	"""BUD-BR-001 — one Budget per (Procuring Entity, Financial Year); the
	canonical MOH baseline already occupies PE-MOH/FY-2027-2028, so each
	isolated profile needs its own Financial Year to get its own Budget slot
	without colliding. Financial Year's own identifier/label/dates are
	strictly generated from `start_year` (BR-003) — there is no custom-named
	variant — so each profile is given a distinct, otherwise-unused future
	start_year rather than a synthetic label. Not part of §15.1's config-
	prerequisite set (those are real, pre-existing Configuration & Governance
	records this seed must never create); this is scaffolding private to one
	named isolated test profile."""
	fy_name = f"FY-{start_year}-{start_year + 1}"
	if not frappe.db.exists("Financial Year", fy_name):
		frappe.get_doc({"doctype": "Financial Year", "start_year": start_year}).insert(ignore_permissions=True)
	if not frappe.db.exists(
		"PE Fiscal Year Context", {"procuring_entity": pe, "financial_year": fy_name, "context_status": "Active"}
	):
		frappe.get_doc(
			{
				"doctype": "PE Fiscal Year Context",
				"procuring_entity": pe,
				"financial_year": fy_name,
				"context_status": "Active",
				"active_from": f"{start_year}-01-01",
				"active_to": f"{start_year + 1}-09-30",
			}
		).insert(ignore_permissions=True)
	return fy_name


def _isolated_line(
	*, budget_ref: str, line_ref: str, title: str, owner_org_unit: str, approved_amount: float, fy_start_year: int
) -> tuple[str, str]:
	"""One Active Budget+Version+Line pair private to one isolated profile
	(never the MOH-BUD-2027-001 canonical baseline) — returns (version_name,
	budget_line_name)."""
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc
	from kentender_budget.services import budget_readiness_contracts as readiness

	existing_budget = frappe.db.get_value("Budget", {"generated_reference": budget_ref}, "name")
	pe = ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH")
	isolated_fy = _ensure_isolated_fy(fy_start_year, pe)

	if existing_budget:
		active_version = _budget_version_active(f"{budget_ref}-V1")
		if active_version:
			line_name = frappe.db.get_value("Budget Line", {"generated_reference": line_ref}, "name")
			return active_version, line_name

	prior_user = frappe.session.user
	try:
		_as_user(C.USER_BUD_OFFICER)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": pe,
				"financial_year": isolated_fy,
				"approval_reference": f"{budget_ref} (Isolated test profile)",
				"approval_date": _offset_date(30),
				"authorised_total": approved_amount,
				"approval_document": "/files/isolated-test-profile-approval-demo.pdf",
			}
		)
		if not result.get("ok"):
			frappe.throw(f"Budget seed: could not create isolated profile {budget_ref}: {result.get('errors')}")
		budget_name = result["budget"]["id"]
		version_name = result["version"]["id"]
		# See _upsert_active_baseline's own comment: the allocator's naming
		# Series is never reset by clearing rows, so force the exact stable id.
		frappe.db.set_value("Budget", budget_name, "generated_reference", budget_ref, update_modified=False)
		frappe.db.set_value("Budget Version", version_name, "generated_reference", f"{budget_ref}-V1", update_modified=False)

		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version_name,
				"lines": [
					{"title": title, "owner_org_unit": owner_org_unit, "funding_source": FUNDING_SOURCE, "approved_amount": approved_amount}
				],
			}
		)
		if not lines_result.get("ok"):
			frappe.throw(f"Budget seed: could not save isolated profile {budget_ref} line: {lines_result.get('errors')}")
		submit_result = readiness.submit_budget_version({"budget_version": version_name})
		if not submit_result.get("ok"):
			frappe.throw(f"Budget seed: could not submit isolated profile {budget_ref}: {submit_result.get('blockers')}")

		_as_user(C.USER_BUD_APPROVER)
		approve_result = readiness.approve_budget_version({"budget_version": version_name})
		if not approve_result.get("ok"):
			frappe.throw(f"Budget seed: could not approve isolated profile {budget_ref}: {approve_result.get('blockers')}")

		line_name = frappe.db.get_value("Budget Line", {"budget": budget_name}, "name")
		frappe.db.set_value("Budget Line", line_name, "generated_reference", line_ref, update_modified=False)
		return version_name, line_name
	finally:
		frappe.set_user(prior_user)


def upsert_isolated_finance_profiles() -> dict[str, Any]:
	"""§15.5 — build (or reuse, if already correctly positioned) all five
	isolated Finance/commitment profiles. Not part of the canonical
	`include_test_edges=False` seed path; called explicitly by the domain/
	Playwright tests that need one specific profile's exact precondition."""
	from kentender_budget.services import budget_check_reserve_contracts as check_reserve
	from kentender_budget.services import budget_commitment_contracts as commitment_svc

	out: dict[str, Any] = {}

	# BUD-SC-FIN-SINGLE — DHI 100m approved/available; reserve 80m; leaves 20m available.
	version_name, line_name = _isolated_line(
		budget_ref="BUD-SC-FIN-SINGLE", line_ref="BUD-SC-FIN-SINGLE-L1",
		title="Finance single-source test line", owner_org_unit=C.OU_DIR_DHP, approved_amount=100_000_000,
		fy_start_year=2031,
	)
	out["BUD-SC-FIN-SINGLE"] = {"version": version_name, "line": line_name}

	# BUD-SC-FIN-COMBINED — DHI 100m + HWD 60m available; two-line combined confirmation.
	version_name, line1 = _isolated_line(
		budget_ref="BUD-SC-FIN-COMBINED-1", line_ref="BUD-SC-FIN-COMBINED-L1",
		title="Finance combined-source test line A", owner_org_unit=C.OU_DIR_DHP, approved_amount=100_000_000,
		fy_start_year=2032,
	)
	_, line2 = _isolated_line(
		budget_ref="BUD-SC-FIN-COMBINED-2", line_ref="BUD-SC-FIN-COMBINED-L2",
		title="Finance combined-source test line B", owner_org_unit=C.OU_DIR_HRMD, approved_amount=60_000_000,
		fy_start_year=2033,
	)
	out["BUD-SC-FIN-COMBINED"] = {"line_a": line1, "line_b": line2}

	# BUD-SC-FIN-SHORT — DHI 100m approved, 30m already reserved -> 70m available; a further 80m request is 10m short.
	version_name, line_name = _isolated_line(
		budget_ref="BUD-SC-FIN-SHORT", line_ref="BUD-SC-FIN-SHORT-L1",
		title="Finance shortfall test line", owner_org_unit=C.OU_DIR_DHP, approved_amount=100_000_000,
		fy_start_year=2034,
	)
	if not frappe.db.exists("Funding Reservation", {"budget_line": line_name, "status": "Active"}):
		prior_user = frappe.session.user
		try:
			_as_user(C.USER_BUD_OFFICER)
			budget_name = frappe.db.get_value("Budget Version", version_name, "budget")
			pe = frappe.db.get_value("Budget", budget_name, "procuring_entity")
			token = check_reserve.check_funding(
				plan_item="BUD-SC-FIN-SHORT-PPI", plan_version="BUD-SC-FIN-SHORT-PLN", finance_task="BUD-SC-FIN-SHORT-FNT",
				source_set_hash="BUD-SC-FIN-SHORT-HASH-PRECOND",
				allocations=[
					{
						"budget_line": line_name,
						"amount": 30_000_000,
						"funding_source": FUNDING_SOURCE,
						"plan_source_allocation": "BUD-SC-FIN-SHORT-PSA-PRECOND",
					}
				],
				correlation_id=frappe.generate_hash(length=12),
			)
			check_reserve.reserve_funding(
				token=token["token"], finance_task="BUD-SC-FIN-SHORT-FNT", source_set_hash="BUD-SC-FIN-SHORT-HASH-PRECOND",
				idempotency_key=frappe.generate_hash(length=12),
			)
		finally:
			frappe.set_user(prior_user)
	out["BUD-SC-FIN-SHORT"] = {"version": version_name, "line": line_name}

	# BUD-SC-CONVERT-PARTIAL — DHI 80m reservation; convert 60m to one commitment; 20m remaining reserved.
	version_name, line_name = _isolated_line(
		budget_ref="BUD-SC-CONVERT-PARTIAL", line_ref="BUD-SC-CONVERT-PARTIAL-L1",
		title="Partial conversion test line", owner_org_unit=C.OU_DIR_DHP, approved_amount=100_000_000,
		fy_start_year=2035,
	)
	reservation_name = frappe.db.get_value("Funding Reservation", {"budget_line": line_name, "status": ["!=", "Converted"]}, "name")
	if not reservation_name:
		prior_user = frappe.session.user
		try:
			_as_user(C.USER_BUD_OFFICER)
			token = check_reserve.check_funding(
				plan_item="BUD-SC-CONVERT-PARTIAL-PPI", plan_version="BUD-SC-CONVERT-PARTIAL-PLN",
				finance_task="BUD-SC-CONVERT-PARTIAL-FNT", source_set_hash="BUD-SC-CONVERT-PARTIAL-HASH",
				allocations=[
					{
						"budget_line": line_name,
						"amount": 80_000_000,
						"funding_source": FUNDING_SOURCE,
						"plan_source_allocation": "BUD-SC-CONVERT-PARTIAL-PSA",
					}
				],
				correlation_id=frappe.generate_hash(length=12),
			)
			reserve_result = check_reserve.reserve_funding(
				token=token["token"], finance_task="BUD-SC-CONVERT-PARTIAL-FNT", source_set_hash="BUD-SC-CONVERT-PARTIAL-HASH",
				idempotency_key=frappe.generate_hash(length=12),
			)
			reservation_name = (reserve_result.get("reservations") or [{}])[0].get("reservation_id")
			commitment_svc.convert_reservation(
				reservation=reservation_name, contract="BUD-SC-CONVERT-PARTIAL-CTR", amount=60_000_000,
				idempotency_key=frappe.generate_hash(length=12),
			)
		finally:
			frappe.set_user(prior_user)
	out["BUD-SC-CONVERT-PARTIAL"] = {"version": version_name, "line": line_name, "reservation": reservation_name}

	# BUD-SC-DUPLICATE-CORRELATION — repeat the SINGLE profile's own successful
	# command with the same correlation_id; verified by the test that calls
	# check_funding/reserve_funding twice with an identical correlation_id
	# against BUD-SC-FIN-SINGLE above, not a separate fixture of its own.
	out["BUD-SC-DUPLICATE-CORRELATION"] = out["BUD-SC-FIN-SINGLE"]

	frappe.db.commit()
	return out
