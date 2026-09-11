# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Procurement Requisitions browser specs
(REQ-CHG-001 v1.6, tracker REQ-402). Invoked via `bench execute`; never
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
from frappe.utils.password import update_password

from kentender_core.seeds.constants import TEST_PASSWORD
from kentender_core.services import organisation_structure as structure
from kentender_core.services import responsibility_administration as administration
from kentender_core.services import site_configuration

NS_PW = "KENTENDER_REQ_PLAYWRIGHT"
FY_START = 2099
FY = "2099-2100"
INTAKE_CLOSES_AT = f"{FY_START}-12-31 20:59:59"  # 31 Dec, 23:59 EAT — pinned
PREVIOUS_FLAGS_KEY = "kt_req_playwright_previous_flags"
UNIT = "Each"
DELIVERY_LOCATION = "Playwright — Requisitions Delivery Location"

OU_NAME = "Playwright — Procurement Requisitions"

# Requisitions-facing actors (the ones a spec actually logs in as).
AUTHOR = "pw.req.author@example.test"
HOD = "pw.req.hod@example.test"
HOPF = "pw.req.hopf@example.test"
AUDITOR = "pw.req.auditor@example.test"
OUTSIDER = "pw.req.outsider@example.test"  # a Departmental Author elsewhere, no standing here
NOBODY = "pw.req.nobody@example.test"  # a stale Frappe Role, no responsibility assignment

# Planning-role actors: pure plumbing to build the one eligible Plan Item
# this world needs — never logged into by a Requisitions spec.
PLN_PLANNER = "pw.req.pln.planner@example.test"
PLN_FINANCE = "pw.req.pln.finance@example.test"
PLN_AO = "pw.req.pln.ao@example.test"
PLN_STATUTORY = "pw.req.pln.statutory@example.test"

ACTORS = (AUTHOR, HOD, HOPF, AUDITOR, OUTSIDER, NOBODY, PLN_PLANNER, PLN_FINANCE, PLN_AO, PLN_STATUTORY)

BUDGET_REF = "BUD-PWREQ-0001"
LINE_REF = "BL-PWREQ-0001"

# the world's ids, filled by ensure_world()
OU = ""
BUDGET_LINE = ""

DIRECT_ITEM_VALUES = {
	"title": "Playwright laptop deployment programme",
	"description": "Procure business laptops for the Playwright fixture world's own deployment programme.",
	"plan_horizon": "Single year",
	"aggregation_indicator": "Not aggregated",
	"lotting_indicator": "Single lot",
	"reservation_category": "None",
	"procurement_method": "Open Tender",
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
	"authorised": f"{FY_START}-09-15 07:00:00",  # 15 Sep, 10:00 EAT
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
		budget = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": BUDGET_REF, "fiscal_year": FY, "currency": "KES"}
		).insert(ignore_permissions=True).name
	if not frappe.db.exists("Procurement Budget Line", {"generated_reference": LINE_REF}):
		frappe.get_doc({"doctype": "Procurement Budget Line", "generated_reference": LINE_REF, "budget": budget}).insert(ignore_permissions=True)
	BUDGET_LINE = frappe.db.get_value("Procurement Budget Line", {"generated_reference": LINE_REF}, "name")
	bv = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Procurement Budget Version", "generated_reference": "BUDV-PWREQ-0001", "budget": budget,
				"version_number": 1, "status": "Active", "approval_reference": "PWREQ-APPROVAL-1",
				"approval_date": "2026-06-30", "authorised_total": 100000000, "currency": "KES",
				"approval_document": "/files/pwreq-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	fs = frappe.get_all("Funding Source", limit=1, pluck="name")
	if not frappe.db.exists("Procurement Budget Line Version", {"budget_version": bv, "budget_line": BUDGET_LINE}):
		frappe.get_doc(
			{
				"doctype": "Procurement Budget Line Version", "generated_reference": "BLV-PWREQ-0001", "budget_version": bv,
				"budget_line": BUDGET_LINE, "title": "Playwright ICT programme", "funding_source": fs[0] if fs else None,
				"approved_amount": 80000000, "currency": "KES",
			}
		).insert(ignore_permissions=True)


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
	global OU
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
	site_setup._seed_regulatory_reference(fiscal_year=FY, fixture_namespace=NS_PW)
	if not frappe.db.exists("Currency", "KES"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "KES", "enabled": 1}).insert(ignore_permissions=True)
	_delivery_location()
	_budget_world()
	_strategy_world()

	for email, name in (
		(AUTHOR, "Playwright Requisitions Author"), (HOD, "Playwright Requisitions HoD"),
		(HOPF, "Playwright Requisitions HoPF"), (AUDITOR, "Playwright Requisitions Auditor"),
		(OUTSIDER, "Playwright Requisitions Outsider"), (NOBODY, "Playwright Requisitions Nobody"),
		(PLN_PLANNER, "Playwright Requisitions Planner"), (PLN_FINANCE, "Playwright Requisitions Finance"),
		(PLN_AO, "Playwright Requisitions AO"), (PLN_STATUTORY, "Playwright Requisitions Statutory"),
	):
		_user(email, name)
	_grant(AUTHOR, "Departmental Author", OU)
	_grant(HOD, "Departmental Author", OU)
	_grant(HOD, "Head of User Department", OU)
	_grant(HOPF, "Head of Procurement Function")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", _unit("Playwright — Requisitions Outsider"))
	_grant(PLN_PLANNER, "Procurement Planner")
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
	return {"fy": FY, "ou": OU, "ou_name": OU_NAME}


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
	frappe.db.delete("Plan Item Forecast Revision", {"plan_item": ("in", items or ("",))})
	frappe.db.delete("Plan Drawdown Reference", {"plan_item": ("in", items or ("",))})
	frappe.db.delete("Plan Source Allocation", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Item", {"plan_version": ("in", plan_versions or ("",))})
	for task_doctype, decision_doctype in (("Plan Finance Task", "Plan Finance Decision"), ("Plan Governance Task", "Plan Governance Decision")):
		task_rows = frappe.get_all(task_doctype, filters={"plan_version": ("in", plan_versions or ("",))}, pluck="name")
		frappe.db.delete(decision_doctype, {"task": ("in", task_rows or ("",))})
		frappe.db.delete(task_doctype, {"name": ("in", task_rows or ("",))})
	frappe.db.delete("Annual Plan Publication", {"plan_version": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})
	frappe.db.delete("Planning Command Journal", {"actor": ("in", ACTORS)})
	frappe.db.delete("Funding Reservation", {"budget_line": BUDGET_LINE or "__missing__"})


def _wipe_requisitions_side() -> None:
	for doctype in (
		"Requisition Event", "Requisition Decision", "Requisition Task", "Authorised Requisition Handoff",
		"Requisition Version", "IT Equipment Requirement Package Version", "IT Equipment Requirement Package",
		"Procurement Requisition",
	):
		frappe.db.delete(doctype, {"owner": ("in", ACTORS)})
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


# --- the one eligible Plan Item, built through Planning's own commands ------


def _build_eligible_plan_item(*, indicative_amount: float = 40_000_000) -> tuple[str, str]:
	"""One direct-requirement DPP entry, funded, accepted as Goods, formed,
	completed, funding-confirmed, governed and published — an Active,
	Requisition-eligible Plan Item, driven entirely through Planning's own
	real commands as named Planning-role actors."""
	from kentender_procurement.procurement_planning.services import (
		dpp_lifecycle, dpp_validation, plan_finance, plan_governance, plan_read, plan_workbench, strategy_gateway,
	)

	with _as(AUTHOR):
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=OU, fiscal_year=FY, idempotency_key=_key(), fixture_namespace=NS_PW)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"],
			values={
				"title": DIRECT_ITEM_VALUES["title"], "description": DIRECT_ITEM_VALUES["description"],
				"expected_operational_result": "The Playwright fixture world has one Active, eligible Plan Item to prepare a Requisition against.",
				"quantity": 1, "unit": UNIT, "required_by_date": f"{FY_START}-12-31", "indicative_amount": indicative_amount,
				"budget_line": BUDGET_LINE,
			},
			expected_record_version=opened["record_version"], idempotency_key=_key(),
		)
	with _as(HOD):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=_key(),
		)
	task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
	with _as(PLN_PLANNER):
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=_key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]],
			mode="each", expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
		item_id = formed["created_items"][0]
		item = plan_read.get_plan_item(plan_item_id=item_id)
		objective = strategy_gateway.list_eligible_strategic_objectives()[0]["id"]
		plan_workbench.save_plan_item(
			plan_item=item_id, values={**DIRECT_ITEM_VALUES, "strategic_objective": objective},
			expected_record_version=item["record_version"], idempotency_key=_key(),
		)
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
	with _as(PLN_FINANCE):
		plan_finance.confirm_plan_funding(task=requested["task"], task_token=frappe.get_doc("Plan Finance Task", requested["task"]).task_token, idempotency_key=_key())
	with _as(PLN_PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		submitted_plan = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
	ao_task = frappe.get_doc("Plan Governance Task", submitted_plan["task"])
	with _as(PLN_AO):
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key())
	statutory_task = frappe.get_doc("Plan Governance Task", adopted["statutory_task"])
	with _as(PLN_STATUTORY):
		plan_governance.approve_annual_plan(task=statutory_task.name, task_token=statutory_task.task_token, idempotency_key=_key())
	return accepted["annual_plan"], item_id


def reset_eligible_item_world(*, commit: bool = True) -> dict[str, Any]:
	"""The bare world plus one Active, eligible Plan Item — the Workspace and
	Start screens' own opening state."""
	world = _reset(commit=False)
	plan_reference, item_id = _build_eligible_plan_item()
	if commit:
		frappe.db.commit()
	return {**world, "plan_reference": plan_reference, "plan_item_id": item_id}


# --- Requisitions journeys (real commands as the fixture actors) ------------


def _prepare(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	with _as(AUTHOR):
		return cmd.prepare_it_equipment_requisition(plan_item_id=plan_item_id, idempotency_key=_key())


def _save_summary(requisition: str) -> None:
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	with _as(AUTHOR):
		cmd.save_requisition_summary(
			requisition=requisition,
			values={
				"requirement_title": DIRECT_ITEM_VALUES["title"], "delivery_location": DELIVERY_LOCATION,
				"latest_delivery_date": f"{FY_START}-12-31", "related_services_required": False,
			},
			expected_record_version=0, idempotency_key=_key(),
		)


def reset_start_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-02's opening state: the eligible item, no Requisition yet."""
	return reset_eligible_item_world(commit=commit)


def reset_editor_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-03/04's opening state: a fresh Draft with its one drawdown
	line, no item added yet."""
	world = reset_eligible_item_world(commit=False)
	prepared = _prepare(world["plan_item_id"])
	_save_summary(prepared["requisition"])
	if commit:
		frappe.db.commit()
	return {**world, "requisition": prepared["requisition"]}


def reset_editor_review_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-05/06/07's opening state: the complete package (item,
	confirmed technical rows, warranty, one acceptance row) — ready for
	Steps 3-5 and the review screen."""
	from kentender_procurement.procurement_requisitions.services import draft_commands as cmd

	state = reset_editor_fixture(commit=False)
	requisition = state["requisition"]
	with _as(AUTHOR):
		root = frappe.get_doc("Procurement Requisition", requisition)
		version = frappe.get_doc("Requisition Version", root.current_version)
		line = version.drawdown_lines[0]
		added = cmd.add_requisition_item(
			requisition=requisition,
			values={
				"plan_item_line_id": line.drawdown_line_id, "equipment_category": "Laptop", "item_name": "Business laptops",
				"quantity": int(line.remaining_quantity or 1), "intended_use": "Playwright fixture deployment",
				"delivery_location": DELIVERY_LOCATION, "latest_delivery_date": f"{FY_START}-12-31",
			},
			expected_record_version=0, idempotency_key=_key(),
		)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", added["package_version"])
		for row in list(package_version.technical_requirements):
			if row.row_status != "Proposed":
				continue
			extra = {}
			if not row.required_value_json:
				extra["value"] = {"memory": 16, "storage_capacity": 512}[row.characteristic_key]
			cmd.confirm_proposed_requirement(
				requisition=requisition, technical_requirement_id=row.technical_requirement_id,
				expected_record_version=package_version.record_version, idempotency_key=_key(), **extra,
			)
			package_version.reload()
		cmd.save_warranty_and_support(
			requisition=requisition,
			values={
				"minimum_warranty_months": 24, "onsite_support_required": 1, "maximum_support_response_hours": 8,
				"manufacturer_support_required": 1, "service_location_constraint": "Within Kenya",
				"support_description": "Playwright fixture support description.",
			},
			expected_record_version=package_version.record_version, idempotency_key=_key(),
		)
		package_version.reload()
		cmd.add_acceptance_requirement(
			requisition=requisition,
			values={
				"applies_to_scope": "All items", "check_type": "Quantity",
				"pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record",
			},
			expected_record_version=package_version.record_version, idempotency_key=_key(),
		)
	if commit:
		frappe.db.commit()
	return {**state, "requisition_item_id": added.get("row_id")}


def reset_department_task_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-08's opening state: sent for Dr-Peter-Kimani-equivalent's
	department decision."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	state = reset_editor_review_fixture(commit=False)
	requisition = state["requisition"]
	with _as(AUTHOR):
		root = frappe.get_doc("Procurement Requisition", requisition)
		sent = lifecycle.send_for_department_approval(requisition=requisition, expected_record_version=root.record_version, idempotency_key=_key())
	if commit:
		frappe.db.commit()
	return {**state, "task": sent["task"]}


def reset_procurement_task_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-09's opening state: submitted to the HoPF for authorisation."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	state = reset_department_task_fixture(commit=False)
	requisition = state["requisition"]
	with _as(HOD):
		root = frappe.get_doc("Procurement Requisition", requisition)
		submitted = lifecycle.submit_requisition_to_procurement(
			requisition=requisition, task=state["task"], expected_record_version=root.record_version, idempotency_key=_key(),
		)
	if commit:
		frappe.db.commit()
	return {**state, "task": submitted["task"]}


def reset_authorised_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""REQ-DES-10's opening state: authorised, unconsumed handoff."""
	from kentender_procurement.procurement_requisitions.services import authorise

	state = reset_procurement_task_fixture(commit=False)
	requisition = state["requisition"]
	with _as(HOPF):
		root = frappe.get_doc("Procurement Requisition", requisition)
		authorised = authorise.authorise_requisition(
			requisition=requisition, task=state["task"], expected_record_version=root.record_version, idempotency_key=_key(),
		)
	frappe.db.set_value("Requisition Decision", {"requisition_version": root.current_version, "decision": "Authorise for Tender Preparation"}, "decided_at", CLOCK["authorised"], update_modified=False)
	if commit:
		frappe.db.commit()
	return {**state, "handoff": authorised.get("handoff"), "reservations": authorised.get("reservations")}


def reset_returned_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""The Procurement task returned to the department for correction — a
	Draft successor Version, the original preserved."""
	from kentender_procurement.procurement_requisitions.services import lifecycle

	state = reset_procurement_task_fixture(commit=False)
	requisition = state["requisition"]
	with _as(HOPF):
		task = frappe.get_doc("Requisition Task", state["task"])
		returned = lifecycle.return_requisition_to_department(
			task=state["task"], reason="Playwright fixture: confirm the delivery location.",
			expected_record_version=task.record_version, idempotency_key=_key(),
		)
	if commit:
		frappe.db.commit()
	return {**state, "correction_version": returned["requisition_version"]}
