# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Self-contained Planning test world (Phase 2 onward).

A dedicated PE (`PE-PLNT`) with two departments, one far-future pinned FY, an
open and a closed submission window context, governed catalogues and role
actors. Idempotent upserts under the KENTENDER_TEST namespace; the §14 seed
world (Phase 11) is separate and never touched by these tests. Fixture
instants are pinned (never now-relative) except the open window, whose whole
point is to span the real test clock.
"""

from __future__ import annotations

import frappe

NS = "KENTENDER_TEST"

PE = "PE-PLNT"
OU_ALPHA = "OU-PLNT-ALPHA"
OU_BETA = "OU-PLNT-BETA"
# Financial Year names itself FY-{start}-{end}; pinned far-future years so
# nothing here rots on a calendar boundary or collides with the §14 world.
FY_OPEN = "FY-2098-2099"
FY_CLOSED = "FY-2101-2102"
# BUD-CHG-001 v1.3 Phase 4 — Procurement Budget is keyed by the real ERPNext
# Fiscal Year (not Planning's own legacy Financial Year/PE Fiscal Year
# Context world above); same pinned far-future window as FY_OPEN.
BUDGET_FISCAL_YEAR = "2098-2099"
CTX_OPEN = "CTX-PLNT-2098-2099"
CTX_CLOSED = "CTX-PLNT-2101-2102"
UNIT = "UNIT-PLNT-EACH"
BUDGET_LINE_REF = "BL-PLNT-0001"
BUDGET_LINE_REF_2 = "BL-PLNT-0002"
# the Budget Line docname is hash-generated; ensure_world() fills these in
BUDGET_LINE = ""
BUDGET_LINE_2 = ""
# Strategy world (§7.2): hash-autonamed; ensure_world() fills these in
STRATEGY_OBJECTIVE = ""
STRATEGY_OBJECTIVE_PATH = "PLNT Pillar › PLNT Programme"

AUTHOR = "plnt.author@example.test"
HOD = "plnt.hod@example.test"
PLANNER = "plnt.planner@example.test"
BUDGET_OFFICER = "plnt.budget@example.test"
ACCOUNTING_OFFICER = "plnt.ao@example.test"
STATUTORY = "plnt.statutory@example.test"
AUDITOR = "plnt.auditor@example.test"
OUTSIDER = "plnt.outsider@example.test"
# §6.1: role combinations are permitted — the conflict is between actions on
# one evidence chain, not between labels. This persona holds HoD + Planner.
HYBRID = "plnt.hybrid@example.test"
# §6.1 Finance-side segregation: Planner + Budget Officer together
HYBRID_FINANCE = "plnt.hybridfinance@example.test"
# §6.1 Governance-side segregation: Planner + Accounting Officer + Statutory
HYBRID_AO = "plnt.hybridao@example.test"

REQUIREMENT_TYPES = ("Goods", "Consulting services", "Non-consulting services")


def _upsert(doctype: str, name: str, values: dict) -> None:
	"""Insert once; every caller uses a field-autonamed doctype whose naming
	field is already in `values`."""
	if frappe.db.exists(doctype, name):
		return
	frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)


def _user(email: str, roles: tuple[str, ...], permissions: tuple[tuple[str, str], ...]) -> None:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	have = {row.role for row in user.roles}
	for role in roles:
		if role not in have:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)
	for allow, value in permissions:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": allow, "for_value": value}
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": email,
					"allow": allow,
					"for_value": value,
				}
			).insert(ignore_permissions=True)


def ensure_world() -> None:
	from kentender_procurement.procurement_planning.services.planning_roles import (
		ensure_planning_roles,
	)

	ensure_planning_roles()

	if not frappe.db.exists("Currency", "KES"):
		frappe.get_doc(
			{"doctype": "Currency", "currency_name": "KES", "enabled": 1}
		).insert(ignore_permissions=True)

	_upsert(
		"Procuring Entity", PE,
		{
			"entity_code": PE, "legal_name": "Planning Test Entity",
			"entity_name": "Planning Test Entity", "reporting_currency": "KES",
			"status": "Active", "fixture_namespace": NS,
		},
	)
	existing_types = frappe.get_all("Organisation Unit Type", limit=1, pluck="name")
	if existing_types:
		ou_type = existing_types[0]
	else:
		ou_type = "OUT-PLNT-DEPT"
		frappe.get_doc(
			{
				"doctype": "Organisation Unit Type",
				"type_reference": ou_type,
				"display_label": "Department",
				"status": "Active",
				"fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)
	for code, label in ((OU_ALPHA, "Alpha Department"), (OU_BETA, "Beta Department")):
		_upsert(
			"Organisation Unit", code,
			{
				"unit_code": code, "unit_name": label, "unit_type": ou_type,
				"procuring_entity": PE, "status": "Active", "fixture_namespace": NS,
			},
		)
	for name, start_year, start, end in (
		(FY_OPEN, 2098, "2098-07-01", "2099-06-30"),
		(FY_CLOSED, 2101, "2101-07-01", "2102-06-30"),
	):
		if not frappe.db.exists("Financial Year", name):
			frappe.get_doc(
				{
					"doctype": "Financial Year",
					"start_year": start_year,
					"label": f"FY {start_year}/{str(start_year + 1)[-2:]}",
					"start_date": start,
					"end_date": end,
					"timezone": "Africa/Nairobi",
					"record_status": "Available",
				}
			).insert(ignore_permissions=True)
	if not frappe.db.exists("Fiscal Year", BUDGET_FISCAL_YEAR):
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": BUDGET_FISCAL_YEAR,
				"year_start_date": "2098-07-01",
				"year_end_date": "2099-06-30",
			}
		).insert(ignore_permissions=True)
	for name, fy in ((CTX_OPEN, FY_OPEN), (CTX_CLOSED, FY_CLOSED)):
		if not frappe.db.exists("PE Fiscal Year Context", name):
			# the context autonames itself CTX-{PE}-{FY years}; `name` must match
			frappe.get_doc(
				{
					"doctype": "PE Fiscal Year Context",
					"procuring_entity": PE,
					"financial_year": fy,
					"context_status": "Active",
					"active_from": "2020-01-01 00:00:00",
					"active_to": "2105-01-01 00:00:00",
				}
			).insert(ignore_permissions=True)
	_upsert(
		"Unit Of Measure", UNIT,
		{"unit_code": UNIT, "unit_label": "Each", "status": "Active",
		 "fixture_namespace": NS},
	)
	for title in REQUIREMENT_TYPES:
		_upsert("Requirement Type", title, {"title": title, "status": "Active",
		                                    "fixture_namespace": NS})
	_upsert("Procurement Method", "Open Tender",
	        {"title": "Open Tender", "status": "Active", "fixture_namespace": NS})

	# submission windows: CTX_OPEN spans the real clock; CTX_CLOSED is long past
	for ctx, opens, closes in (
		(CTX_OPEN, "2020-01-01 00:00:00", "2099-01-01 00:00:00"),
		(CTX_CLOSED, "2020-01-01 00:00:00", "2020-02-01 00:00:00"),
	):
		if not frappe.db.exists(
			"Departmental Plan Submission Window", {"pe_fy_context": ctx}
		):
			frappe.get_doc(
				{
					"doctype": "Departmental Plan Submission Window",
					"pe_fy_context": ctx,
					"opens_at": opens,
					"closes_at": closes,
					"fixture_namespace": NS,
				}
			).insert(ignore_permissions=True)

	_link_targets()
	_strategy_world()

	pe_scope = (("Procuring Entity", PE),)
	alpha = pe_scope + (("Organisation Unit", OU_ALPHA),)
	_user(AUTHOR, ("Departmental Author",), alpha)
	_user(HOD, ("Departmental Author", "Head of User Department"), alpha)
	_user(PLANNER, ("Procurement Planner",), pe_scope)
	_user(BUDGET_OFFICER, ("Budget Officer",), pe_scope)
	_user(ACCOUNTING_OFFICER, ("Accounting Officer",), pe_scope)
	_user(STATUTORY, ("Plan Statutory Approver",), pe_scope)
	_user(AUDITOR, ("Planning Auditor",), pe_scope)
	_user(OUTSIDER, ("Departmental Author",), (("Organisation Unit", OU_BETA),))
	_user(
		HYBRID,
		("Departmental Author", "Head of User Department", "Procurement Planner"),
		alpha,
	)
	_user(HYBRID_FINANCE, ("Procurement Planner", "Budget Officer"), pe_scope)
	_user(
		HYBRID_AO,
		("Procurement Planner", "Accounting Officer", "Plan Statutory Approver"),
		pe_scope,
	)
	frappe.db.commit()


NEED = "NEED-PLNT-0001"
NEED_V1 = "NEED-PLNT-0001-V1"

def wipe_planning_rows() -> None:
	"""Per-test isolation, scoped by the test PE (namespace alone is not
	enough: rows created through the API surface carry no fixture namespace).
	The runner's rollback semantics are deliberately not relied on."""
	dpp_roots = frappe.get_all(
		"Departmental Plan", filters={"procuring_entity": PE}, pluck="name"
	)
	dpp_versions = frappe.get_all(
		"Departmental Plan Version",
		filters={"departmental_plan": ("in", dpp_roots or ("",))},
		pluck="name",
	)
	submissions = frappe.get_all(
		"Departmental Plan Submission",
		filters={"dpp_version": ("in", dpp_versions or ("",))},
		pluck="name",
	)
	tasks = frappe.get_all(
		"Departmental Plan Validation Task",
		filters={"procuring_entity": PE},
		pluck="name",
	)
	frappe.db.delete(
		"Departmental Plan Validation Decision", {"task": ("in", tasks or ("",))}
	)
	frappe.db.delete("Departmental Plan Validation Task", {"procuring_entity": PE})
	frappe.db.delete(
		"Departmental Plan Submission", {"name": ("in", submissions or ("",))}
	)
	frappe.db.delete(
		"Departmental Plan Entry", {"dpp_version": ("in", dpp_versions or ("",))}
	)
	frappe.db.delete(
		"Departmental Plan Version", {"name": ("in", dpp_versions or ("",))}
	)
	frappe.db.delete("Departmental Plan", {"name": ("in", dpp_roots or ("",))})

	plans = frappe.get_all("Annual Plan", filters={"procuring_entity": PE}, pluck="name")
	plan_versions = frappe.get_all(
		"Annual Plan Version", filters={"annual_plan": ("in", plans or ("",))}, pluck="name"
	)
	for doctype, field in (
		("Plan Source Allocation", "plan_version"),
		("Annual Plan Item", "plan_version"),
	):
		frappe.db.delete(doctype, {field: ("in", plan_versions or ("",))})
	for task_doctype, decision_doctype in (
		("Plan Finance Task", "Plan Finance Decision"),
		("Plan Governance Task", "Plan Governance Decision"),
	):
		task_rows = frappe.get_all(
			task_doctype, filters={"procuring_entity": PE}, pluck="name"
		)
		frappe.db.delete(decision_doctype, {"task": ("in", task_rows or ("",))})
		frappe.db.delete(task_doctype, {"name": ("in", task_rows or ("",))})
	frappe.db.delete(
		"Plan Reservation Reference",
		{"plan_item_id": ("like", "PPI-PLNT-%")},
	)
	frappe.db.delete(
		"Plan Drawdown Reference",
		{"plan_item_id": ("like", "PPI-PLNT-%")},
	)
	frappe.db.delete(
		"Annual Plan Publication",
		{"plan_version": ("in", plan_versions or ("",))},
	)
	frappe.db.delete("Annual Plan Version", {"name": ("in", plan_versions or ("",))})
	frappe.db.delete("Annual Plan", {"name": ("in", plans or ("",))})
	frappe.db.delete("Planning Command Journal", {})


def _link_targets() -> None:
	"""Real rows behind the Link fields the entries carry. Tests are exempt
	from the D5 AST boundary (its own docstring says so); production code
	still only ever touches Needs through the published contracts."""
	if not frappe.db.exists("Procurement Budget", {"generated_reference": "BUD-PLNT-0001"}):
		frappe.get_doc(
			{
				"doctype": "Procurement Budget",
				"generated_reference": "BUD-PLNT-0001",
				"fiscal_year": BUDGET_FISCAL_YEAR,
				"currency": "KES",
			}
		).insert(ignore_permissions=True)
	budget = frappe.db.get_value("Procurement Budget", {"generated_reference": "BUD-PLNT-0001"}, "name")
	if not frappe.db.exists("Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF}):
		frappe.get_doc(
			{
				"doctype": "Procurement Budget Line",
				"generated_reference": BUDGET_LINE_REF,
				"budget": budget,
			}
		).insert(ignore_permissions=True)
	global BUDGET_LINE
	BUDGET_LINE = frappe.db.get_value(
		"Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF}, "name"
	)
	# a second line under the SAME Budget: PLN-DES-09A combines sources across
	# different Budget Lines that still share one Budget (and its currency).
	if not frappe.db.exists("Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF_2}):
		frappe.get_doc(
			{
				"doctype": "Procurement Budget Line",
				"generated_reference": BUDGET_LINE_REF_2,
				"budget": budget,
			}
		).insert(ignore_permissions=True)
	global BUDGET_LINE_2
	BUDGET_LINE_2 = frappe.db.get_value(
		"Procurement Budget Line", {"generated_reference": BUDGET_LINE_REF_2}, "name"
	)
	# §7.3 Finance tests exercise the REAL check_funding/reserve_funding
	# contracts (never mocked, unlike eligible_line_ids elsewhere) — an
	# Active Budget Version with real approved amounts is required.
	bv = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Procurement Budget Version",
				"generated_reference": "BUDV-PLNT-0001",
				"budget": budget,
				"version_number": 1,
				"status": "Active",
				"approval_reference": "PLNT-APPROVAL-1",
				"approval_date": "2026-06-30",
				"authorised_total": 100000000,
				"currency": "KES",
				"approval_document": "/files/plnt-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	fs = frappe.get_all("Funding Source", limit=1, pluck="name")
	for line, ref in ((BUDGET_LINE, "BLV-PLNT-0001"), (BUDGET_LINE_2, "BLV-PLNT-0002")):
		if not frappe.db.exists("Procurement Budget Line Version", {"budget_version": bv, "budget_line": line}):
			frappe.get_doc(
				{
					"doctype": "Procurement Budget Line Version",
					"generated_reference": ref,
					"budget_version": bv,
					"budget_line": line,
					"title": "Digital health programme",
					"funding_source": fs[0] if fs else None,
					"approved_amount": 100000000,
					"currency": "KES",
				}
			).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Need", NEED):
		frappe.get_doc(
			{
				"doctype": "Departmental Need",
				"need_reference": NEED,
				"procuring_entity": PE,
				"organisation_unit": OU_ALPHA,
				"financial_year": FY_OPEN,
				"current_state": "Accepted for planning",
				"record_version": 1,
				"fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Departmental Need Version", NEED_V1):
		frappe.get_doc(
			{
				"doctype": "Departmental Need Version",
				"need_version_id": NEED_V1,
				"departmental_need": NEED,
				"version_number": 1,
				"version_status": "Accepted",
				"title": "Test requirement",
				"description": "Procure and implement the test requirement.",
				"expected_operational_result": "The department can operate the tested capability.",
				"indicative_quantity": 1,
				"unit": UNIT,
				"required_by_date": "2099-05-31",
				"fixture_namespace": NS,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Departmental Need", NEED,
		{"current_version": NEED_V1, "current_accepted_version": NEED_V1},
		update_modified=False,
	)



def _strategy_world() -> None:
	"""§7.2 — one primary Active Strategic Plan for PE-PLNT covering the real
	test clock (resolve_strategy_context defaults `effective_date` to today,
	not to the pinned far-future FY window the rest of this world uses)."""
	global STRATEGY_OBJECTIVE, STRATEGY_OBJECTIVE_PATH
	existing = frappe.db.get_value(
		"Strategy Node",
		{"title": "PLNT Digital Objective", "node_type": "Strategic Objective"},
		"name",
	)
	if existing:
		STRATEGY_OBJECTIVE = existing
		return
	plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"title": "Planning Test Strategic Plan",
			"procuring_entity_id": PE,
			"plan_role": "Primary",
			"period_start": "2020-01-01",
			"period_end": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			"effective_from": "2020-01-01",
			"effective_to": "2105-01-01",
		}
	).insert(ignore_permissions=True)
	# the structure guard only allows edits on a Draft/Returned version —
	# build the hierarchy first, then activate.
	pillar = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Pillar", "title": "PLNT Pillar", "display_order": 1,
		}
	).insert(ignore_permissions=True)
	programme = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Programme", "title": "PLNT Programme", "display_order": 2,
			"parent_node_id": pillar.name,
		}
	).insert(ignore_permissions=True)
	objective = frappe.get_doc(
		{
			"doctype": "Strategy Node", "plan_version_id": version.name,
			"node_type": "Strategic Objective", "title": "PLNT Digital Objective",
			"display_order": 3, "parent_node_id": programme.name,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
	STRATEGY_OBJECTIVE = objective.name
	STRATEGY_OBJECTIVE_PATH = "PLNT Pillar › PLNT Programme"


def accepted_source(
	need_id: str = "NEED-PLNT-0001",
	*,
	version: str = "NEED-PLNT-0001-V1",
	title: str = "Test requirement",
	quantity: float = 1.0,
) -> dict:
	"""A DepartmentalNeedAccepted.v2-shaped payload for patching the intake."""
	return {
		"need_id": need_id,
		"need_reference": need_id,
		"accepted_version_id": version,
		"version_number": int(version.rsplit("V", 1)[-1]),
		"content_hash": "x" * 8,
		"procuring_entity_id": PE,
		"org_unit_id": OU_ALPHA,
		"financial_year_id": FY_OPEN,
		"title": title,
		"description": "Procure and implement the test requirement.",
		"expected_operational_result": "The department can operate the tested capability.",
		"indicative_quantity": quantity,
		"unit_id": UNIT,
		"unit_display_value": "Each",
		"required_by_date": "2099-05-31",
	}


def direct_values(**overrides) -> dict:
	values = {
		"title": "Direct requirement",
		"description": "Assess and remediate the direct requirement.",
		"expected_operational_result": "A prioritised and actionable remediation plan exists.",
		"quantity": 1,
		"unit": UNIT,
		"required_by_date": "2099-04-30",
		"budget_line": BUDGET_LINE,
		"indicative_amount": 1000000,
	}
	values.update(overrides)
	return values
