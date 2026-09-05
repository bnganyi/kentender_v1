# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Self-contained Planning test world (PLN-CHG-001 v1.12, tracker D13).

One site is one Procuring Entity, so isolation is by a dedicated far-future
ERPNext Fiscal Year (`2101-2102` with departmental-plan intake open;
`2103-2104` closed) and two dedicated Organisation Units beneath the site
root, never by a Procuring Entity. Actors are granted role-bound
`User Responsibility Assignment` rows through the administration command —
no Frappe Role list, no framework permission row is authority. Idempotent
upserts under the KENTENDER_TEST namespace; the §14 seed world is separate
and never touched by these tests.

The DPP intake flag is single-valued site-wide: `ensure_world()` moves it
onto the test year and records the previously open year, and every test
module registers `restore_site` as a class cleanup so the canonical seed
world is left exactly as found. The Python suite and a Playwright run
therefore never execute concurrently against one site (tracker rule 8).
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

NS = "KENTENDER_TEST"

FY_OPEN = "2101-2102"
FY_CLOSED = "2103-2104"
INTAKE_CLOSES_AT = "2102-05-31 20:59:59"  # 31 May 2102, 23:59 EAT — pinned, never now-relative
FY_OPEN_START = 2101
FY_CLOSED_START = 2103
BUDGET_FISCAL_YEAR = FY_OPEN

OU_ALPHA_NAME = "Test — Planning Alpha"
OU_BETA_NAME = "Test — Planning Beta"
# unit docnames are server-generated codes; ensure_world() fills these in
OU_ALPHA = ""
OU_BETA = ""
UNIT = "Each"
BUDGET_LINE_REF = "BL-PLNT-0001"
BUDGET_LINE_REF_2 = "BL-PLNT-0002"
BUDGET_LINE = ""
BUDGET_LINE_2 = ""
STRATEGY_OBJECTIVE = ""
STRATEGY_OBJECTIVE_PATH = ""

AUTHOR = "plnt.author@example.test"
HOD = "plnt.hod@example.test"
PLANNER = "plnt.planner@example.test"
FINANCE_OFFICER = "plnt.finance@example.test"
ACCOUNTING_OFFICER = "plnt.ao@example.test"
STATUTORY = "plnt.statutory@example.test"
AUDITOR = "plnt.auditor@example.test"
OUTSIDER = "plnt.outsider@example.test"
# §6.1: role combinations are permitted — the conflict is between actions.
HYBRID = "plnt.hybrid@example.test"
HYBRID_FINANCE = "plnt.hybridfinance@example.test"
HYBRID_AO = "plnt.hybridao@example.test"
ACTORS = (AUTHOR, HOD, PLANNER, FINANCE_OFFICER, ACCOUNTING_OFFICER, STATUTORY, AUDITOR, OUTSIDER, HYBRID, HYBRID_FINANCE, HYBRID_AO)

NEED = "NEED-PLNT-0001"
NEED_V1 = "NEED-PLNT-0001-V1"

_previous_open: dict[str, list[str]] = {}


def pe_code() -> str:
	return cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code")).removeprefix("PE-")


def dpp_prefix(unit: str = "", start_year: int = FY_OPEN_START) -> str:
	from kentender_procurement.procurement_planning.services import references

	return f"DPP-{references.pe_code()}-{references.ou_code(unit or OU_ALPHA)}-{start_year}-"


def plan_prefix(start_year: int = FY_OPEN_START) -> str:
	from kentender_procurement.procurement_planning.services import references

	return f"PLN-{references.pe_code()}-{start_year}-"


def _user(email: str, full_name: str) -> None:
	"""An enabled System User (AUTH §4.5 — a responsibility needs a desk
	account; Frappe derives `user_type` from the roles, so `Desk User` is the
	only Frappe Role a fixture actor ever carries directly)."""
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": full_name, "send_welcome_email": 0, "enabled": 1}
		).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
	if frappe.db.get_value("User", email, "user_type") != "System User":
		user.add_roles("Desk User")


def _grant(email: str, role: str, unit: str = "") -> None:
	from kentender_core.services import responsibility_administration as administration

	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS, actor="Administrator")


def _fiscal_year(start_year: int) -> str:
	from kentender_core.services import site_configuration

	name = site_configuration._fy_name(start_year)
	if not frappe.db.exists("Fiscal Year", name):
		frappe.set_user("Administrator")
		site_configuration.add_fiscal_year(start_year=start_year)
	return name


def _unit(name: str) -> str:
	from kentender_core.services import organisation_structure as structure

	existing = frappe.db.get_value("Organisation Unit", {"unit_name": name}, "name")
	if existing:
		return existing
	frappe.set_user("Administrator")
	return structure.add_organisation_unit(parent_id=structure._root(), name=name)["unit"]


def ensure_world() -> None:
	global OU_ALPHA, OU_BETA, STRATEGY_OBJECTIVE, STRATEGY_OBJECTIVE_PATH
	from kentender_core.seeds import site_setup
	from kentender_core.services import site_configuration
	from kentender_core.tests import v16_fixtures as core_fx

	frappe.set_user("Administrator")
	core_fx.ensure_site_configured()
	site_setup._seed_catalogues()
	if not frappe.db.get_value("UOM", UNIT, "enabled"):
		if frappe.db.exists("UOM", UNIT):
			frappe.db.set_value("UOM", UNIT, "enabled", 1, update_modified=False)
		else:
			frappe.get_doc({"doctype": "UOM", "uom_name": UNIT, "enabled": 1}).insert(ignore_permissions=True)
	_fiscal_year(FY_OPEN_START)
	_fiscal_year(FY_CLOSED_START)
	OU_ALPHA = _unit(OU_ALPHA_NAME)
	OU_BETA = _unit(OU_BETA_NAME)
	site_setup._seed_regulatory_reference(fiscal_year=FY_OPEN, fixture_namespace=NS)
	if not frappe.db.exists("Currency", "KES"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "KES", "enabled": 1}).insert(ignore_permissions=True)

	_link_targets()
	_strategy_world()

	for email, name in (
		(AUTHOR, "PLNT Author"), (HOD, "PLNT Head of Department"), (PLANNER, "PLNT Planner"),
		(FINANCE_OFFICER, "PLNT Finance Officer"), (ACCOUNTING_OFFICER, "PLNT Accounting Officer"),
		(STATUTORY, "PLNT Statutory Approver"), (AUDITOR, "PLNT Auditor"), (OUTSIDER, "PLNT Outsider"),
		(HYBRID, "PLNT Hybrid"), (HYBRID_FINANCE, "PLNT Hybrid Finance"), (HYBRID_AO, "PLNT Hybrid AO"),
	):
		_user(email, name)
	_grant(AUTHOR, "Departmental Author", OU_ALPHA)
	_grant(HOD, "Departmental Author", OU_ALPHA)
	_grant(HOD, "Head of User Department", OU_ALPHA)
	_grant(PLANNER, "Procurement Planner")
	_grant(FINANCE_OFFICER, "Finance Confirmation Officer")
	_grant(ACCOUNTING_OFFICER, "Accounting Officer")
	_grant(STATUTORY, "Plan Statutory Approver")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", OU_BETA)
	_grant(HYBRID, "Departmental Author", OU_ALPHA)
	_grant(HYBRID, "Head of User Department", OU_ALPHA)
	_grant(HYBRID, "Procurement Planner")
	_grant(HYBRID_FINANCE, "Procurement Planner")
	_grant(HYBRID_FINANCE, "Finance Confirmation Officer")
	_grant(HYBRID_AO, "Procurement Planner")
	_grant(HYBRID_AO, "Accounting Officer")
	_grant(HYBRID_AO, "Plan Statutory Approver")

	# the single-valued intake flag: move it onto the test year, remember
	# what was open so restore_site() can put it back
	if not _previous_open:
		_previous_open["dpp"] = frappe.get_all("Fiscal Year", filters={site_configuration.DPP_FLAG_OPEN: 1}, pluck="name")
	if not frappe.db.get_value("Fiscal Year", FY_OPEN, site_configuration.DPP_FLAG_OPEN):
		site_configuration.open_dpp_submission(fiscal_year=FY_OPEN, closes_at=INTAKE_CLOSES_AT, reason="Planning test world")
	elif str(frappe.db.get_value("Fiscal Year", FY_OPEN, site_configuration.DPP_FLAG_CLOSES_AT) or "") != INTAKE_CLOSES_AT:
		frappe.db.set_value("Fiscal Year", FY_OPEN, site_configuration.DPP_FLAG_CLOSES_AT, INTAKE_CLOSES_AT, update_modified=False)
	frappe.db.commit()


def restore_site() -> None:
	"""Re-open departmental-plan intake on whichever year was open before the
	test world moved it (the §8 seed's 2027-2028)."""
	from kentender_core.services import site_configuration

	from kentender_core.seeds import site_setup

	frappe.set_user("Administrator")
	for year in _previous_open.get("dpp", []):
		if year != FY_OPEN and frappe.db.exists("Fiscal Year", year) and not frappe.db.get_value("Fiscal Year", year, site_configuration.DPP_FLAG_OPEN):
			site_configuration.open_dpp_submission(fiscal_year=year, reason="test cleanup: restore the previously open year")
	# the site must end on the §8 seed's state whatever was captured: with no
	# year holding a flag, re-seed the flags exactly as site_setup does
	if not frappe.get_all("Fiscal Year", filters={site_configuration.DPP_FLAG_OPEN: 1}, pluck="name") or frappe.get_all("Fiscal Year", filters={site_configuration.DPP_FLAG_OPEN: 1}, pluck="name") == [FY_OPEN]:
		site_setup._seed_dpp_intake()
	if not frappe.get_all("Fiscal Year", filters={site_configuration.FLAG_OPEN: 1}, pluck="name") or frappe.get_all("Fiscal Year", filters={site_configuration.FLAG_OPEN: 1}, pluck="name") == [FY_OPEN]:
		site_setup._seed_intake()
	frappe.db.commit()


def open_test_intake() -> None:
	from kentender_core.services import site_configuration

	frappe.set_user("Administrator")
	if not frappe.db.get_value("Fiscal Year", FY_OPEN, site_configuration.DPP_FLAG_OPEN):
		site_configuration.open_dpp_submission(fiscal_year=FY_OPEN, closes_at=INTAKE_CLOSES_AT, reason="Planning test world")


def close_test_intake() -> None:
	from kentender_core.services import site_configuration

	frappe.set_user("Administrator")
	if frappe.db.get_value("Fiscal Year", FY_OPEN, site_configuration.DPP_FLAG_OPEN):
		site_configuration.close_dpp_submission(fiscal_year=FY_OPEN, reason="Planning test: window closed")


def wipe_planning_rows() -> None:
	"""Per-test isolation, scoped by the two test Fiscal Years (namespace
	alone is not enough: rows created through the API carry no namespace)."""
	fys = (FY_OPEN, FY_CLOSED)
	dpp_roots = frappe.get_all("Departmental Plan", filters={"fiscal_year": ("in", fys)}, pluck="name")
	dpp_versions = frappe.get_all("Departmental Plan Version", filters={"departmental_plan": ("in", dpp_roots or ("",))}, pluck="name")
	submissions = frappe.get_all("Departmental Plan Submission", filters={"dpp_version": ("in", dpp_versions or ("",))}, pluck="name")
	tasks = frappe.get_all("Departmental Plan Validation Task", filters={"fiscal_year": ("in", fys)}, pluck="name")
	frappe.db.delete("Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))})
	frappe.db.delete("Departmental Plan Validation Task", {"name": ("in", tasks or ("",))})
	frappe.db.delete("Departmental Plan Submission", {"name": ("in", submissions or ("",))})
	frappe.db.delete("Departmental Plan Entry", {"dpp_version": ("in", dpp_versions or ("",))})
	frappe.db.delete("Departmental Plan Version", {"name": ("in", dpp_versions or ("",))})
	frappe.db.delete("Departmental Plan", {"name": ("in", dpp_roots or ("",))})

	plans = frappe.get_all("Annual Plan", filters={"fiscal_year": ("in", fys)}, pluck="name")
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
	# the journal is §6.1 segregation evidence — scope the wipe to this world
	frappe.db.delete("Planning Command Journal", {"actor": ("in", ACTORS)})
	frappe.db.delete("Planning Command Journal", {"fixture_namespace": NS})
	frappe.db.delete("Need Planning Usage Projection", {"departmental_need": NEED})
	frappe.db.delete("Notification Log", {"for_user": ("in", ACTORS)})


def _link_targets() -> None:
	"""Real rows behind the Link fields the entries carry. Tests are exempt
	from the D5 AST boundary; production code only touches Needs through the
	published contracts."""
	global BUDGET_LINE, BUDGET_LINE_2
	if not frappe.db.exists("Procurement Budget", {"generated_reference": "BUD-PLNT-0001"}):
		frappe.get_doc({"doctype": "Procurement Budget", "generated_reference": "BUD-PLNT-0001", "fiscal_year": BUDGET_FISCAL_YEAR, "currency": "KES"}).insert(ignore_permissions=True)
	budget = frappe.db.get_value("Procurement Budget", {"generated_reference": "BUD-PLNT-0001"}, "name")
	for ref in (BUDGET_LINE_REF, BUDGET_LINE_REF_2):
		if not frappe.db.exists("Procurement Budget Line", {"generated_reference": ref}):
			frappe.get_doc({"doctype": "Procurement Budget Line", "generated_reference": ref, "budget": budget}).insert(ignore_permissions=True)
	BUDGET_LINE = frappe.db.get_value("Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF}, "name")
	BUDGET_LINE_2 = frappe.db.get_value("Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF_2}, "name")
	bv = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Procurement Budget Version", "generated_reference": "BUDV-PLNT-0001", "budget": budget,
				"version_number": 1, "status": "Active", "approval_reference": "PLNT-APPROVAL-1",
				"approval_date": "2026-06-30", "authorised_total": 200000000, "currency": "KES",
				"approval_document": "/files/plnt-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	fs = frappe.get_all("Funding Source", limit=1, pluck="name")
	for line, ref, title in ((BUDGET_LINE, "BLV-PLNT-0001", "Digital health programme"), (BUDGET_LINE_2, "BLV-PLNT-0002", "Health workforce programme")):
		if not frappe.db.exists("Procurement Budget Line Version", {"budget_version": bv, "budget_line": line}):
			frappe.get_doc(
				{
					"doctype": "Procurement Budget Line Version", "generated_reference": ref, "budget_version": bv,
					"budget_line": line, "title": title, "funding_source": fs[0] if fs else None,
					"approved_amount": 100000000, "currency": "KES",
				}
			).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Need", NEED):
		frappe.get_doc(
			{
				"doctype": "Departmental Need", "need_reference": NEED, "organisation_unit": OU_ALPHA,
				"financial_year": FY_OPEN, "current_state": "Accepted for planning", "record_version": 1, "fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("Departmental Need", NEED, {"organisation_unit": OU_ALPHA, "financial_year": FY_OPEN}, update_modified=False)
	if not frappe.db.exists("Departmental Need Version", NEED_V1):
		frappe.get_doc(
			{
				"doctype": "Departmental Need Version", "need_version_id": NEED_V1, "departmental_need": NEED,
				"version_number": 1, "version_status": "Accepted", "title": "Test requirement",
				"description": "Procure and implement the test requirement.",
				"expected_operational_result": "The department can operate the tested capability.",
				"indicative_quantity": 1, "unit": UNIT, "required_by_date": "2102-05-31", "fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_value("Departmental Need", NEED, {"current_version": NEED_V1, "current_accepted_version": NEED_V1}, update_modified=False)


def _strategy_world() -> None:
	"""§7.2 — the site's one Active Strategic Plan. Reuse the seeded plan's
	first Active Objective where the site has one; otherwise build a
	far-reaching test plan covering the real clock."""
	global STRATEGY_OBJECTIVE, STRATEGY_OBJECTIVE_PATH
	from kentender_procurement.procurement_planning.services import strategy_gateway

	rows = strategy_gateway.list_eligible_strategic_objectives()
	if rows:
		STRATEGY_OBJECTIVE = rows[0]["id"]
		STRATEGY_OBJECTIVE_PATH = rows[0]["path_display"]
		return
	plan_values = {
		"doctype": "Strategic Plan", "title": "Planning Test Strategic Plan", "plan_role": "Primary",
		"period_start": "2020-01-01", "period_end": "2105-01-01",
	}
	plan = frappe.get_doc(plan_values).insert(ignore_permissions=True)
	version = frappe.get_doc({"doctype": "Strategic Plan Version", "plan_id": plan.name, "version_number": 1, "effective_from": "2020-01-01", "effective_to": "2105-01-01"}).insert(ignore_permissions=True)
	pillar = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Pillar", "title": "PLNT Pillar", "display_order": 1}).insert(ignore_permissions=True)
	programme = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Programme", "title": "PLNT Programme", "display_order": 2, "parent_node_id": pillar.name}).insert(ignore_permissions=True)
	objective = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Strategic Objective", "title": "PLNT Digital Objective", "display_order": 3, "parent_node_id": programme.name}).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
	STRATEGY_OBJECTIVE = objective.name
	STRATEGY_OBJECTIVE_PATH = "PLNT Pillar › PLNT Programme"


def accepted_source(need_id: str = NEED, *, version: str = NEED_V1, title: str = "Test requirement", quantity: float = 1.0) -> dict:
	"""A DepartmentalNeedAccepted.v2-shaped payload for patching the intake."""
	return {
		"need_id": need_id,
		"need_reference": need_id,
		"accepted_version_id": version,
		"version_number": int(version.rsplit("V", 1)[-1]),
		"content_hash": "x" * 8,
		"org_unit_id": OU_ALPHA,
		"financial_year_id": FY_OPEN,
		"title": title,
		"description": "Procure and implement the test requirement.",
		"expected_operational_result": "The department can operate the tested capability.",
		"indicative_quantity": quantity,
		"unit_id": UNIT,
		"unit_display_value": "Each",
		"required_by_date": "2102-05-31",
	}


def direct_values(**overrides) -> dict:
	values = {
		"title": "Direct requirement",
		"description": "Assess and remediate the direct requirement.",
		"expected_operational_result": "A prioritised and actionable remediation plan exists.",
		"quantity": 1,
		"unit": UNIT,
		"required_by_date": "2102-04-30",
		"budget_line": BUDGET_LINE,
		"indicative_amount": 1000000,
	}
	values.update(overrides)
	return values


def item_values(**overrides) -> dict:
	"""A complete, readiness-passing Plan Item save payload (PLN-DES-09)."""
	values = {
		"title": "Test procurement package",
		"description": "Procure and implement the test requirement as one package.",
		"strategic_objective": STRATEGY_OBJECTIVE,
		"plan_horizon": "Single year",
		"aggregation_indicator": "Not aggregated",
		"lotting_indicator": "Single lot",
		"reservation_category": "None",
		"procurement_method": "Open Tender",
		"baseline_invitation_date": "2101-09-01",
		"tendering_period_days": 21,
		"evaluation_period_days": 30,
		"award_approval_buffer_days": 5,
		"notification_buffer_days": 2,
		"standstill_period_days": 14,
	}
	values.update(overrides)
	return values
