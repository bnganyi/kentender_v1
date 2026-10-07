# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Procurement Requisitions browser specs
(REQ-CHG-001 v1.11, tracker REQ11-502). Invoked via `bench execute`; never
imported by `api.py`.

Self-contained world, entirely independent of both the canonical MOH seed
(`seeds/kentender_mvp_v1.py`, FY 2027-2028) and Procurement Planning's own
Playwright world (FY 2098-2099): its own Fiscal Year **2099-2100**, its own
Organisation Unit, and its own actors, so the three worlds never collide and
this module never depends on the canonical MOH fixture existing. Requisitions
needs one Active, Goods-classified, IT-equipment-eligible Plan Item to exist
before any screen can be exercised — this world builds that Plan Item itself,
driving Planning's own real `dpp_lifecycle`/`plan_workbench`/`plan_finance`/
`plan_governance` services directly as named Planning-role actors (never
Administrator for a business decision), the same one-source-item chain
`procurement_requisitions/tests/fixtures.py::active_item()` proves for the
Python suite — a single direct requirement, not a Need-origin one, so this
world never depends on Departmental Needs' own Playwright fixture module
either. The Planning-role actors below are pure plumbing: no Requisitions
spec ever authenticates as them.

Fixtures are driven through the real Requisitions commands as the fixture
actors; instants are pinned only where a screen renders one (§16.4's own
clock pattern), never `now`-relative elsewhere. This world and the Python
suite's own `KENTENDER_TEST` world (a different Fiscal Year) never run
concurrently on one site (mirrors PLN-CHG-001's own D13 rule).
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr
from frappe.utils.password import update_password

from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_core.services import site_configuration
from kentender_core.utils.raw_delete import delete_rows
from kentender_core.services.command_write_guard import fixture_insert

NS_PW = "KENTENDER_REQ_PLAYWRIGHT"
FY_START = 2099
FY = "2099-2100"
INTAKE_CLOSES_AT = f"{FY_START}-12-31 23:59:59"  # 31 Dec, 23:59 EAT (site time) — pinned
PREVIOUS_FLAGS_KEY = "kt_req_playwright_previous_flags"
UNIT = "Each"
DELIVERY_LOCATION = "Playwright — Requisitions Delivery Location"

OU_NAME = "Playwright — Digital Health"  # the lead department (larger value)
OU_B_NAME = "Playwright — HR Management and Development"
PROFILE_WINDOW = {"effective_from": f"{FY_START}-07-01", "effective_until": f"{FY_START + 1}-06-30"}
PROFILE_LIMITS = {"bid_opening": (7, None), "evaluation_completion": (None, 30), "contract_signing": (14, None)}
VERIFICATION_FIXTURE = "Fixture-verified — not production law"
DELIVERY_DEFAULT_DAYS = 30

# Requisitions-facing actors (the ones a spec actually logs in as).
AUTHOR = "pw.req.author@example.test"  # Departmental Author in both departments (§13.1 Grace)
HOD = "pw.req.hod@example.test"  # lead Head of User Department (§13.1 Peter)
CONTRIBUTOR = "pw.req.contributor@example.test"  # Author in the second department only (§13.1 Asha)
HOD_B = "pw.req.hodb@example.test"
HOPF = "pw.req.hopf@example.test"
AUDITOR = "pw.req.auditor@example.test"
OUTSIDER = "pw.req.outsider@example.test"  # a Departmental Author elsewhere, no standing here
NOBODY = "pw.req.nobody@example.test"  # a stale Frappe Role, no responsibility assignment

# Planning-role actors: pure plumbing to build the one eligible Plan Item
# this world needs — never logged into by a Requisitions spec.
PLN_PLANNER = "pw.req.pln.planner@example.test"
PLN_HOPF = "pw.req.pln.hopf@example.test"  # v1.18 §6.2: signs and submits the Annual Plan
PLN_FINANCE = "pw.req.pln.finance@example.test"
PLN_AO = "pw.req.pln.ao@example.test"
PLN_STATUTORY = "pw.req.pln.statutory@example.test"

OFFICER = "pw.req.officer@example.test"  # Procurement Officer (REQ-DES-10 base actor)

ACTORS = (AUTHOR, HOD, CONTRIBUTOR, HOD_B, HOPF, AUDITOR, OFFICER, OUTSIDER, NOBODY, PLN_PLANNER, PLN_HOPF, PLN_FINANCE, PLN_AO, PLN_STATUTORY)

BUDGET_REF = "BUD-PWREQ-0001"
LINE_REF = "BL-PWREQ-0001"

# the world's ids, filled by ensure_world()
OU = ""
OU_B = ""
BUDGET_LINE = ""

DIRECT_ITEM_VALUES = {
	"title": "Clinical training and deployment laptops for digital health rollout",
	"description": "Procure business laptops for clinical training and field digital-health deployment.",
	"plan_horizon": "Single year",
	"aggregation_indicator": "Not aggregated",
	"lotting_indicator": "Single lot",
	"reservation_category": "Youth",
	"procurement_method": "Open Tender",
	# PLN-CHG-001 v1.23 readiness: the estimate basis is required before a
	# funding request (plan_read.plan_readiness) — added 19 Sep 2026 when the
	# Tenders Playwright world, which builds on this one, first ran.
	"estimate_basis": "Market survey of three suppliers in July 2099 including delivery and installation.",
	"estimate_basis_reference": "MS-PWREQ-2099-001",
	"baseline_invitation_date": f"{FY_START}-09-01",
	"tendering_period_days": 21,
	"evaluation_period_days": 30,
	"award_approval_buffer_days": 5,
	"notification_buffer_days": 2,
	"standstill_period_days": 14,
}

# §16.4's own timeline instants, reused verbatim for the authorised fixture
# (a screen that renders an exact date/time needs a pinned one, not `now`).
CLOCK = {
	"authorised": f"{FY_START}-09-15 10:00:00",  # 15 Sep, 10:00 EAT (site time)
}


def _key() -> str:
	return f"req-pw-{uuid4().hex}"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Requisitions Playwright fixtures are test data. Enable "
		"developer_mode or allow_tests on this site before building them."
	)


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


# --- world -------------------------------------------------------------------


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		first, _, last = full_name.partition(" ")
		doc = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": first, "last_name": last, "send_welcome_email": 0, "enabled": 1}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	elif frappe.db.get_value("User", email, "user_type") != "System User":
		frappe.get_doc("User", email).add_roles("Desk User")
	update_password(email, TEST_PASSWORD)


def _grant(email: str, role: str, unit: str = "") -> None:
	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS_PW, actor="Administrator")


def _unit(name: str) -> str:
	existing = frappe.db.get_value("Organisation Unit", {"unit_name": name}, "name")
	if existing:
		return existing
	return structure.add_organisation_unit(parent_id=structure._root(), name=name)["unit"]


def _delivery_location() -> None:
	if not frappe.db.exists("Delivery Location", DELIVERY_LOCATION):
		frappe.get_doc(
			{"doctype": "Delivery Location", "location_name": DELIVERY_LOCATION, "address": "Playwright fixture address, Nairobi", "status": "Active"}
		).insert(ignore_permissions=True)


def _budget_world() -> None:
	"""Budget → Active Version → one Line on the fixture year. Test
	scaffolding for another app's model, outside production paths (the NDS
	test-exemption precedent already established in Planning's own module)."""
	global BUDGET_LINE
	budget = frappe.db.get_value("Procurement Budget", {"generated_reference": BUDGET_REF}, "name")
	if not budget:
		budget = fixture_insert(frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": BUDGET_REF, "fiscal_year": FY, "currency": "KES"}
		)).name
	if not frappe.db.exists("Procurement Budget Line", {"generated_reference": LINE_REF}):
		fixture_insert(frappe.get_doc({"doctype": "Procurement Budget Line", "generated_reference": LINE_REF, "budget": budget}))
	BUDGET_LINE = frappe.db.get_value("Procurement Budget Line", {"generated_reference": LINE_REF}, "name")
	bv = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = fixture_insert(frappe.get_doc(
			{
				"doctype": "Procurement Budget Version", "generated_reference": "BUDV-PWREQ-0001", "budget": budget,
				"version_number": 1, "status": "Active", "approval_reference": "PWREQ-APPROVAL-1",
				"approval_date": "2026-06-30", "authorised_total": 100000000, "currency": "KES",
				"approval_document": "/files/pwreq-approval.pdf",
			}
		)).name
	fs = frappe.get_all("Funding Source", limit=1, pluck="name")
	if not frappe.db.exists("Procurement Budget Line Version", {"budget_version": bv, "budget_line": BUDGET_LINE}):
		fixture_insert(frappe.get_doc(
			{
				"doctype": "Procurement Budget Line Version", "generated_reference": "BLV-PWREQ-0001", "budget_version": bv,
				"budget_line": BUDGET_LINE, "title": "Playwright ICT programme", "funding_source": fs[0] if fs else None,
				"approved_amount": 60000000, "currency": "KES",
			}
		))


def _strategy_world() -> None:
	"""§7.2 — one Active Strategic Plan with an Active Objective; reuse
	whatever the site already has, else build a far-reaching one."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	if strategy_gateway.list_eligible_strategic_objectives():
		return
	plan = frappe.get_doc(
		{"doctype": "Strategic Plan", "title": "Playwright Requisitions Strategic Plan", "plan_role": "Primary", "period_start": "2020-01-01", "period_end": "2110-01-01"}
	).insert(ignore_permissions=True)
	version = frappe.get_doc(
		{"doctype": "Strategic Plan Version", "plan_id": plan.name, "version_number": 1, "effective_from": "2020-01-01", "effective_to": "2110-01-01"}
	).insert(ignore_permissions=True)
	pillar = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Pillar", "title": "PWREQ Pillar", "display_order": 1}).insert(ignore_permissions=True)
	programme = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Programme", "title": "PWREQ Programme", "display_order": 2, "parent_node_id": pillar.name}).insert(ignore_permissions=True)
	frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Strategic Objective", "title": "PWREQ Digital Objective", "display_order": 3, "parent_node_id": programme.name}).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")


def _open_years(flag: str) -> list[str]:
	return frappe.get_all("Fiscal Year", filters={flag: 1}, pluck="name")


def _move_flags() -> None:
	"""The DPP submission flag is single-valued site-wide (CFG-BR-010):
	move it onto this world's own FY for a run, remembering what was open
	so `restore_site()` can put it back."""
	if not frappe.defaults.get_global_default(PREVIOUS_FLAGS_KEY):
		previous = {"dpp": [y for y in _open_years(site_configuration.DPP_FLAG_OPEN) if y != FY]}
		frappe.defaults.set_global_default(PREVIOUS_FLAGS_KEY, json.dumps(previous))
	if not frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_OPEN):
		site_configuration.open_dpp_submission(fiscal_year=FY, closes_at=INTAKE_CLOSES_AT, reason="Requisitions Playwright world")
	elif str(frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_CLOSES_AT) or "") != INTAKE_CLOSES_AT:
		frappe.db.set_value("Fiscal Year", FY, site_configuration.DPP_FLAG_CLOSES_AT, INTAKE_CLOSES_AT, update_modified=False)


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	"""Put the DPP intake flag back on the year that was open before this
	world moved it (the canonical MOH seed's own 2027-2028, most likely).
	Safe to call when nothing was moved."""
	_guard()
	frappe.set_user("Administrator")
	# The fixture-verified profiles this world seeds for its own year leave
	# with it (they are test data; the Python suite's own world seeds and
	# purges its twin the same way).
	from kentender_core.services import procurement_settings

	procurement_settings.purge_fixture_profiles(NS_PW)
	raw = frappe.defaults.get_global_default(PREVIOUS_FLAGS_KEY)
	restored: list[str] = []
	if raw:
		previous = json.loads(raw)
		for year in previous.get("dpp", []):
			if frappe.db.exists("Fiscal Year", year) and not frappe.db.get_value("Fiscal Year", year, site_configuration.DPP_FLAG_OPEN):
				site_configuration.open_dpp_submission(fiscal_year=year, reason="Requisitions Playwright teardown: restore the previously open year")
				restored.append(year)
		frappe.defaults.clear_default(PREVIOUS_FLAGS_KEY)
	if commit:
		frappe.db.commit()
	return {"restored": restored}


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	"""The fixture year, one Organisation Unit, Budget/Strategy graphs, six
	Requisitions-facing actors plus four Planning-plumbing actors, all with
	their responsibilities."""
	global OU, OU_B
	from kentender_core.seeds import site_setup

	_guard()
	frappe.set_user("Administrator")
	if not site_configuration.is_configured():
		frappe.throw("Configure the site (System setup) before building the Requisitions Playwright world.")
	site_setup._seed_catalogues()
	if not frappe.db.exists("Fiscal Year", FY):
		site_configuration.add_fiscal_year(start_year=FY_START)
	if not frappe.db.get_value("UOM", UNIT, "enabled"):
		if frappe.db.exists("UOM", UNIT):
			frappe.db.set_value("UOM", UNIT, "enabled", 1, update_modified=False)
		else:
			frappe.get_doc({"doctype": "UOM", "uom_name": UNIT, "enabled": 1}).insert(ignore_permissions=True)
	OU = _unit(OU_NAME)
	OU_B = _unit(OU_B_NAME)
	# A reservation rule still at "Production verification pending" blocks
	# Sign and submit (plan_read.plan_readiness → PLN_REFERENCE_UNAVAILABLE);
	# the seeder is find-or-create, so an earlier pending version for this
	# year is removed first and the fixture-verified one seeded, target 0,
	# exactly as Planning's own worlds do.
	fy_start = frappe.db.get_value("Fiscal Year", FY, "year_start_date")
	frappe.db.delete("Regulatory Reference", {"reference_key": "RESERVATION-RULES", "effective_from": fy_start, "verification_status": ("!=", VERIFICATION_FIXTURE)})
	site_setup._seed_regulatory_reference(fiscal_year=FY, fixture_namespace=NS_PW, verification_status=VERIFICATION_FIXTURE, reservation_target_percent=0)
	# PLN-CHG-001 v1.23 (D10): method admissibility and the schedule now
	# resolve from Procurement Method / Schedule Profiles in force on the
	# package's applicable date — the site's own profiles cover 2027-2028
	# only, so this world seeds fixture-verified ones for its own year the
	# way Planning's Playwright world does (added 19 Sep 2026).
	site_setup._seed_method_profiles(effective=PROFILE_WINDOW, verification_status=VERIFICATION_FIXTURE, fixture_namespace=NS_PW)
	# Open Tender only, like Planning's Playwright world; the canonical site
	# seeds every method.
	site_setup._seed_schedule_profiles(effective=PROFILE_WINDOW, verification_status=VERIFICATION_FIXTURE, fixture_namespace=NS_PW, limits=PROFILE_LIMITS, estimated_delivery_default_days=DELIVERY_DEFAULT_DAYS, methods=("Open Tender",))
	if not frappe.db.exists("Currency", "KES"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "KES", "enabled": 1}).insert(ignore_permissions=True)
	_delivery_location()
	_budget_world()
	_strategy_world()

	for email, name in (
		(AUTHOR, "Grace Wanjiku"), (HOD, "Peter Kimani"), (CONTRIBUTOR, "Asha Odhiambo"), (HOD_B, "Playwright HRMD Head"),
		(OFFICER, "Playwright Procurement Officer"),
		(HOPF, "Charles Mutiso"), (AUDITOR, "Playwright Requisitions Auditor"),
		(OUTSIDER, "Playwright Requisitions Outsider"), (NOBODY, "Playwright Requisitions Nobody"),
		(PLN_PLANNER, "Playwright Requisitions Planner"), (PLN_HOPF, "Playwright Requisitions Planning HoPF"), (PLN_FINANCE, "Playwright Requisitions Finance"),
		(PLN_AO, "Playwright Requisitions AO"), (PLN_STATUTORY, "Playwright Requisitions Statutory"),
	):
		_user(email, name)
	_grant(AUTHOR, "Departmental Author", OU)
	_grant(AUTHOR, "Departmental Author", OU_B)
	_grant(HOD, "Departmental Author", OU)
	_grant(HOD, "Head of User Department", OU)
	_grant(CONTRIBUTOR, "Departmental Author", OU_B)
	_grant(HOD_B, "Departmental Author", OU_B)
	_grant(HOD_B, "Head of User Department", OU_B)
	_grant(HOPF, "Head of Procurement Function")
	_grant(OFFICER, "Procurement Officer")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", _unit("Playwright — Requisitions Outsider"))
	_grant(PLN_PLANNER, "Procurement Planner")
	_grant(PLN_HOPF, "Head of Procurement Function")
	_grant(PLN_FINANCE, "Finance Confirmation Officer")
	_grant(PLN_AO, "Accounting Officer")
	_grant(PLN_STATUTORY, "Plan Statutory Approver")
	# REQ-AC-002/032-style Forbidden fixture — a stale Frappe Role is not
	# authority (AUTH §4): this actor must get the Forbidden panel, nothing else.
	nobody = frappe.get_doc("User", NOBODY)
	if "Auditor" not in {row.role for row in nobody.roles}:
		nobody.add_roles("Auditor")
	for assignment in frappe.get_all("User Responsibility Assignment", filters={"user": NOBODY}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", assignment, ignore_permissions=True, force=True)
	_move_flags()
	if commit:
		frappe.db.commit()
	return {"fy": FY, "ou": OU, "ou_name": OU_NAME, "ou_b": OU_B, "ou_b_name": OU_B_NAME}


# --- reset --------------------------------------------------------------------


def _wipe_planning_side() -> None:
	"""Every Planning row on the fixture year (rows created through the API
	carry no namespace), child → parent — mirrors Planning's own Playwright
	`_wipe()`, scoped to this world's own FY."""
	dpp_roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": FY}, pluck="name")
	dpp_versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": ("in", dpp_roots or ("",))}, pluck="name")
	submissions = frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ("in", dpp_versions or ("",))}, pluck="name")
	tasks = frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": FY}, pluck="name")
	frappe.db.delete("Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))})
	frappe.db.delete("Departmental Plan Validation Task", {"name": ("in", tasks or ("",))})
	frappe.db.delete("Departmental Plan Submission", {"name": ("in", submissions or ("",))})
	frappe.db.delete("Departmental Plan Entry", {"dpp_version": ("in", dpp_versions or ("",))})
	frappe.db.delete("Departmental Plan Version", {"name": ("in", dpp_versions or ("",))})
	frappe.db.delete("Departmental Plan", {"name": ("in", dpp_roots or ("",))})

	plans = frappe.get_all("Annual Plan", filters={"fiscal_year": FY}, pluck="name")
	plan_versions = frappe.get_all("Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name")
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
	frappe.db.delete("Plan Drawdown Reference", {"plan_item": ("in", items or ("",))})
	frappe.db.delete("Plan Source Allocation", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Item", {"plan_version": ("in", plan_versions or ("",))})
	# Activation (Treasury evidence + publish, added 19 Sep 2026) writes the
	# published Plan Item roots and their publication trail — the same rows
	# Planning's own `wipe_planning_rows()` removes, in the same order.
	roots = frappe.get_all("Plan Item", filters={"annual_plan": ("in", plans or ("",))}, pluck="name")
	for doctype in ("Milestone Actual Event", "Proceeding Coverage"):
		if frappe.db.exists("DocType", doctype):
			frappe.db.delete(doctype, {"plan_item": ("in", roots or ("",))})
	frappe.db.delete("Plan Item Correction Disposition", {"correction_request": ("in", frappe.get_all("Plan Item Correction Request", filters={"plan_item_id": ("in", roots or ("",))}, pluck="name") or ("",))})
	frappe.db.delete("Plan Item Correction Request", {"plan_item_id": ("in", roots or ("",))})
	frappe.db.delete("Plan Item", {"name": ("in", roots or ("",))})
	for task_doctype, decision_doctype in (("Plan Finance Task", "Plan Finance Decision"), ("Plan Governance Task", "Plan Governance Decision")):
		task_rows = frappe.get_all(task_doctype, filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
		frappe.db.delete(decision_doctype, {"task": ("in", task_rows or ("",))})
		frappe.db.delete(task_doctype, {"name": ("in", task_rows or ("",))})
	frappe.db.delete("Annual Plan Publication", {"plan_version": ("in", plan_versions or ("",))})
	for doctype in ("Plan Preparation Signature", "Plan Financial Basis", "Plan Finance Basis Reuse", "Treasury Submission Evidence", "Plan Publication Hold", "Late Activation Explanation"):
		if frappe.db.exists("DocType", doctype):
			frappe.db.delete(doctype, {"plan_version": ("in", plan_versions or ("",))})
	snapshots = frappe.get_all("Approved Plan Snapshot", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
	publications = frappe.get_all("Plan Publication", filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
	for doctype in ("Publication Intent", "Publication Attempt", "Publication Acknowledgement"):
		if frappe.db.exists("DocType", doctype):
			frappe.db.delete(doctype, {"publication": ("in", publications or ("",))})
	frappe.db.delete("Plan Publication", {"name": ("in", publications or ("",))})
	frappe.db.delete("Approved Plan Snapshot", {"name": ("in", snapshots or ("",))})
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})
	frappe.db.delete("Planning Command Journal", {"actor": ("in", ACTORS)})
	frappe.db.delete("Funding Reservation", {"budget_line": BUDGET_LINE or "__missing__"})


def _wipe_requisitions_side() -> None:
	for doctype in (
		"Requisition Event", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
		"Requisition Version", "IT Equipment Requirement Package Version", "IT Equipment Requirement Package",
		"Procurement Requisition", "Requisition Correction Outcome",
	):
		delete_rows(doctype, {"owner": ("in", ACTORS)})
	frappe.db.delete("Requisition Command Journal", {"idempotency_key": ("like", "req-pw-%")})
	frappe.db.delete("Plan Item Correction Request", {"reason": ("like", "%Playwright%")})
	frappe.db.delete("Notification Log", {"for_user": ("in", ACTORS)})


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	"""Remove every Requisitions/Planning Playwright row this world owns.
	The world itself (units, actors, Budget/Strategy graphs) stays."""
	_guard()
	frappe.set_user("Administrator")
	_wipe_requisitions_side()
	_wipe_planning_side()
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS_PW, "fiscal_year": FY}


def _reset(commit: bool) -> dict[str, Any]:
	world = ensure_world(commit=False)
	_wipe_requisitions_side()
	_wipe_planning_side()
	if commit:
		frappe.db.commit()
	return world




# --- the §13.1 combined purchase, built through Planning's own commands ----


def _direct_entry(*, unit: str, author: str, hod: str, amount: int, quantity: int, title: str) -> tuple[dict, str]:
	from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation

	with _as(author):
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=unit, fiscal_year=FY, idempotency_key=_key(), fixture_namespace=NS_PW)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values={
				"title": title, "description": "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout.",
				"expected_operational_result": "Staff can use secure, supported equipment for training and field digital-health work.",
				"quantity": quantity, "unit": UNIT, "required_by_date": f"{FY_START}-12-31", "indicative_amount": amount, "budget_line": BUDGET_LINE,
			},
			expected_record_version=opened["record_version"], idempotency_key=_key(),
		)
	with _as(hod):
		submitted = dpp_lifecycle.submit_departmental_plan(dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=_key())
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLN_PLANNER):
		accepted = dpp_validation.accept_departmental_plan(task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=_key())
	entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": opened["current_version"], "entry_id": added["entry_id"]}, "name")
	return accepted, entry


def _activate(plan_reference: str) -> None:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_governance, plan_read, publication_pipeline, treasury

	with _as(PLN_PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key())
	with _as(PLN_FINANCE):
		plan_finance.confirm_plan_funding(task=requested["task"], task_token=frappe.get_doc("Plan Finance Task", requested["task"]).task_token, idempotency_key=_key())
	with _as(PLN_HOPF):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		submitted_plan = plan_governance.submit_consolidated_plan(plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key())
	ao_task = frappe.get_doc("Plan Governance Task", submitted_plan["task"])
	with _as(PLN_AO):
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key())
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(PLN_STATUTORY):
		approved = plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=_key())
	version_name = frappe.db.get_value("Plan Publication", approved["publication"], "plan_version")
	with _as(PLN_AO):
		treasury.record_treasury_submission(
			plan_version=version_name, submitted_at=f"{FY_START}-11-01 09:00:00", channel="Email", destination="treasury@example.test",
			dispatch_reference=f"MOH/APP/{FY_START}/001", exact_document_confirmed=True, idempotency_key=_key(),
		)
	frappe.set_user("Administrator")
	publication_pipeline.publish_annual_plan(plan_version=version_name, idempotency_key=_key())


def _build_eligible_plan_item(*, overrides: dict[str, Any] | None = None, single: bool = False) -> tuple[str, str]:
	"""§13.1 in the Playwright year: Digital Health 150 Each / KES 30m and HR
	Management and Development 100 Each / KES 20m, combined by Planning into
	one Youth-reserved laptop purchase and activated."""
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench, strategy_gateway

	accepted, lead_entry = _direct_entry(unit=OU, author=AUTHOR, hod=HOD, amount=30_000_000, quantity=150, title="Business laptops")
	entries = [lead_entry]
	if not single:
		accepted, second_entry = _direct_entry(unit=OU_B, author=HOD_B, hod=HOD_B, amount=20_000_000, quantity=100, title="Business laptops")
		entries.append(second_entry)
	with _as(PLN_PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=entries, mode="combined" if len(entries) > 1 else "each",
			combination_reason="Both departments require the same laptop specification for one programme; combining secures better unit pricing and one delivery schedule." if len(entries) > 1 else None,
			expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		objective = strategy_gateway.list_eligible_strategic_objectives()[0]["id"]
		values = {**DIRECT_ITEM_VALUES, "strategic_objective": objective, **(overrides or {})}
		if len(entries) > 1:
			values.update({"aggregation_indicator": "Aggregated into this package", "aggregation_reason": "Both laptop batches ship in a single combined tender lot."})
		plan_workbench.save_plan_item(plan_item=item_id, values=values, expected_record_version=item["record_version"], idempotency_key=_key())
	_activate(accepted["annual_plan"])
	return accepted["annual_plan"], item_id


def reset_eligible_item_world(*, commit: bool = True, single: bool = False) -> dict[str, Any]:
	"""REQ-DES-01 READY / REQ-DES-02 base: the world plus the eligible purchase."""
	world = _reset(commit=False)
	plan_reference, item_id = _build_eligible_plan_item(single=single)
	if commit:
		frappe.db.commit()
	return {**world, "plan_reference": plan_reference, "plan_item_id": item_id}


# --- Requisitions journeys (real commands as the fixture actors) ------------


def _cmd():
	from kentender_procurement.procurement_requisitions.services import draft_commands

	return draft_commands


def _view(requisition: str, user: str = AUTHOR) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import read

	with _as(user):
		return read.get_requisition_record(requisition=requisition)


def _prepare(plan_item_id: str, user: str = AUTHOR) -> str:
	with _as(user):
		return _cmd().prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key())["requisition"]


def _request_information(requisition: str, user: str = AUTHOR) -> None:
	view = _view(requisition, user)
	with _as(user):
		_cmd().save_requisition_summary(
			requisition=requisition, values={"delivery_location": DELIVERY_LOCATION, "latest_delivery_date": f"{FY_START}-12-31"},
			expected_record_version=view["header"]["version_record_version"], idempotency_key=_key(),
		)


def _add_laptops(requisition: str, user: str = AUTHOR) -> None:
	view = _view(requisition, user)
	uses = {OU: "Field digital-health deployment for Digital Health staff", OU_B: "Clinical training for Human Resources Management and Development staff"}
	lines = {l["drawdown_line_id"]: l for l in view["amounts"]}
	rows = [{"drawdown_line_id": r["drawdown_line_id"], "quantity": r["quantity"], "intended_use": uses.get(lines[r["drawdown_line_id"]]["contributing_org_unit"], "Field deployment for department staff")} for r in view["equipment"]["add_rows"] if r["quantity"] > 0]
	with _as(user):
		_cmd().add_same_specification_items(
			requisition=requisition, shared={"equipment_category": "Laptop", "item_name": "Business laptops", "delivery_location": DELIVERY_LOCATION},
			rows=rows, expected_record_version=view["package_record_version"], idempotency_key=_key(),
		)


def _apply_package(requisition: str, user: str = AUTHOR) -> None:
	view = _view(requisition, user)
	req = view["requirements"]

	def raw(value):
		return value.get("ports") or value.get("values") or value.get("value")

	technical = [{"technical_requirement_id": r["technical_requirement_id"], "characteristic_key": r["characteristic_key"], "value": raw(r["value"]), "selected": True} for g in req["technical_groups"] for r in g["rows"]]
	acceptance = [{k: a[k] for k in ("acceptance_requirement_id", "check_type", "pass_condition", "evidence_type", "applies_to_scope", "applies_to_id")} | {"selected": True} for a in req["acceptance"]]
	with _as(user):
		_cmd().apply_selected_requirement_package(
			requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"],
			technical=technical, acceptance=acceptance, support=req["support"], expected_record_version=view["package_record_version"], idempotency_key=_key(),
		)


def _root_version(requisition: str) -> int:
	return int(frappe.db.get_value("Procurement Requisition", requisition, "record_version"))


def _task(requisition: str, role: str) -> str:
	return frappe.db.get_value("Requisition Task", {"requisition": requisition, "business_role": role, "status": "Open"}, "name")


def _send(requisition: str) -> None:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	with _as(AUTHOR):
		lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=_root_version(requisition), idempotency_key=_key())


def _submit(requisition: str) -> None:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	with _as(HOD):
		lifecycle.submit_requisition_to_procurement(requisition=requisition, task=_task(requisition, "Head of User Department"), expected_record_version=_root_version(requisition), idempotency_key=_key())


def _authorise(requisition: str) -> None:
	from kentender_procurement.procurement_requisitions.services import authorise

	with _as(HOPF):
		authorise.authorise_requisition(requisition=requisition, task=_task(requisition, "Head of Procurement Function"), expected_record_version=_root_version(requisition), idempotency_key=_key())


def _state(stage: str, **kwargs) -> dict[str, Any]:
	"""Build the world up to one named stage; each reset below is one call."""
	world = reset_eligible_item_world(commit=False, single=kwargs.get("single", False))
	out = {**world}
	if stage == "eligible":
		return out
	requisition = _prepare(world["plan_item_id"])
	out["requisition"] = requisition
	if stage == "draft":
		return out
	_request_information(requisition)
	if stage == "request_information":
		return out
	_add_laptops(requisition)
	if stage == "review_required":
		return out
	_apply_package(requisition)
	if stage == "complete":
		return out
	_send(requisition)
	out["department_task"] = _task(requisition, "Head of User Department")
	if stage == "awaiting":
		return out
	_submit(requisition)
	out["procurement_task"] = _task(requisition, "Head of Procurement Function")
	if stage == "submitted":
		return out
	_authorise(requisition)
	out["handoff"] = frappe.db.get_value("Procurement Requisition", requisition, "handoff")
	return out


def _done(state: dict[str, Any], commit: bool) -> dict[str, Any]:
	if commit:
		frappe.db.commit()
	return state


def reset_workspace_ready(*, commit: bool = True) -> dict[str, Any]:
	return _done(_state("eligible"), commit)


def reset_draft(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-01-DRAFT and REQ-DES-03 base: a fresh Draft, request information filled, no equipment."""
	return _done(_state("request_information"), commit)


def reset_review_required(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-03-COMPLETE / REQ-DES-05 base: equipment added, standard package Review required."""
	return _done(_state("review_required"), commit)


def reset_complete_draft(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-05-COMPLETE / REQ-DES-06: every task complete, ready to send."""
	return _done(_state("complete"), commit)


def reset_department_task(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-01-ACTION (HoD) / REQ-DES-07."""
	return _done(_state("awaiting"), commit)


def reset_procurement_task(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-08 / REQ-DES-09."""
	return _done(_state("submitted"), commit)


def reset_authorised(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-10."""
	return _done(_state("authorised"), commit)


# --- REQ-DES-10 / REQ-DES-11 states, each through the real commands ---


def _request_planning_correction(requisition: str) -> str:
	from kentender_procurement.procurement_requisitions.services import lifecycle

	with _as(HOD):
		lifecycle.request_upstream_plan_correction(
			requisition=requisition,
			reason="The approved source allocation refers to the wrong Budget Line. Please review the departmental funding specification.",
			expected_record_version=_root_version(requisition), idempotency_key=_key(),
		)
	return cstr(frappe.db.get_value("Procurement Requisition", requisition, "planning_correction_request_id"))


def reset_stopped(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-11 Open: submitted, then the lead HoD requests a Planning correction."""
	state = _state("submitted")
	state["correction_request"] = _request_planning_correction(state["requisition"])
	return _done(state, commit)


def reset_stopped_closed(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-11 Closed without change: the Planner closes the request; the
	outcome reaches Requisitions through Planning's published event."""
	from kentender_procurement.procurement_planning.services import plan_requisition

	state = _state("submitted")
	request = _request_planning_correction(state["requisition"])
	with _as(PLN_PLANNER):
		version = frappe.db.get_value("Plan Item Correction Request", request, "record_version")
		plan_requisition.close_plan_item_correction_without_change(
			correction_request=request, reason="The approved source allocation and Budget Line are correct. No Planning change is required.",
			expected_record_version=version, idempotency_key=_key(),
		)
	state["correction_request"] = request
	return _done(state, commit)


def reset_revoked(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-10 Revoked: authorised, then the HOPF revokes before consumption."""
	from kentender_procurement.procurement_requisitions.services import authorise

	state = _state("authorised")
	with _as(HOPF):
		authorise.revoke_unconsumed_authorisation(
			requisition=state["requisition"], reason="The authorised warranty terms must be corrected before tendering.",
			expected_record_version=_root_version(state["requisition"]), idempotency_key=_key(),
		)
	return _done(state, commit)


def reset_consumed(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-10 Consumed: authorised, then consumed by one Tender through the
	guarded Requisitions command (Tenders itself is out of scope, D15)."""
	from kentender_procurement.procurement_requisitions.services import handoff

	state = _state("authorised")
	handoff.record_handoff_consumption(
		handoff=state["handoff"], tender="TND-PW-REQ-1", tender_version="TNV-PW-REQ-1",
		template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=_key(),
	)
	return _done(state, commit)


def reset_direct_hod_draft(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-06-DIRECT-HOD: the lead Head of User Department prepares the
	complete Draft themselves, so they submit directly (no self-approval)."""
	# Single-department item: the HoD's own authority covers every row.
	world = reset_eligible_item_world(commit=False, single=True)
	requisition = _prepare(world["plan_item_id"], user=HOD)
	_request_information(requisition, user=HOD)
	_add_laptops(requisition, user=HOD)
	_apply_package(requisition, user=HOD)
	return _done({**world, "requisition": requisition}, commit)
