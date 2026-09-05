# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Procurement Planning browser specs (PLN-CHG-001
v1.12, decision D13). Invoked via `bench execute`; never imported by api.py.

One fixture world, no Procuring Entity (AUTH-ADR-001 v1.6 §1.1 — the site is
the entity): Fiscal Year **2098-2099**, two dedicated Organisation Units
("Playwright — Procurement Planning" and "Playwright — Planning Outsider"),
nine actors granted through `responsibility_administration.grant`, namespace
KENTENDER_PLAYWRIGHT. The single-valued departmental-plan and Needs intake
flags are moved onto the fixture year for a run and put back by
`restore_site()` (Playwright's globalTeardown and the end of every Make gate).
Every reset deletes by namespace **or** by the fixture year, child → parent,
and clears the actors' server-side context preferences (CTX-CHG-001).

Fixtures are driven through the real §8.2 commands as the fixture actors;
instants are pinned, never `now`-relative. The Python suite (`tests/fixtures`,
FY 2101-2102) and these specs never run concurrently on one site.

Departmental Needs rows are never created, read or deleted here (D5, the
NDS architecture guard): the browser helper asks NDS's own fixture module
(`departmental_needs.seeds.playwright_ui_fixtures.reset_accepted_needs_for`)
for accepted Needs in this world's unit and passes their references in as
the `need`/`needs` arguments below.
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

NS_PW = "KENTENDER_PLAYWRIGHT"
FY_START = 2098
FY = "2098-2099"
FY_LABEL = "FY 2098/99"
INTAKE_CLOSES_AT = "2099-05-31 20:59:59"  # 31 May 2099, 23:59 EAT — pinned
PREVIOUS_FLAGS_KEY = "kt_pln_playwright_previous_flags"

OU_NAME = "Playwright — Procurement Planning"
OUTSIDER_OU_NAME = "Playwright — Planning Outsider"

AUTHOR = "pw.pln.author@example.test"
HOD = "pw.pln.hod@example.test"
PLANNER = "pw.pln.planner@example.test"
FINANCE = "pw.pln.finance@example.test"
ACCOUNTING_OFFICER = "pw.pln.ao@example.test"
STATUTORY = "pw.pln.statutory@example.test"
AUDITOR = "pw.pln.auditor@example.test"
OUTSIDER = "pw.pln.outsider@example.test"  # Departmental Author elsewhere
NOBODY = "pw.pln.nobody@example.test"  # a stale Frappe Role, no responsibility assignment
ACTORS = (AUTHOR, HOD, PLANNER, FINANCE, ACCOUNTING_OFFICER, STATUTORY, AUDITOR, OUTSIDER, NOBODY)

PASSWORD = TEST_PASSWORD
UNIT = "Each"
BUDGET_REF = "BUD-PWPL-0001"
LINE_REF = "BL-PWPL-0001"
LINE_REF_2 = "BL-PWPL-0002"

CONTEXT_PREFERENCE_KEYS = ("kt_planning_financial_year", "kt_needs_org_unit", "kt_needs_financial_year")

DIRECT_CONTENT = {
	"title": "Digital health platform security assessment",
	"description": "Assess the security of the national digital health platform and provide a prioritised remediation report.",
	"expected_operational_result": "The Ministry receives a prioritised and actionable security remediation plan.",
	"quantity": 1,
	"unit": UNIT,
	"required_by_date": "2099-04-30",
	"indicative_amount": 20000000,
}

# the world's ids, filled by ensure_world()
OU = ""
OUTSIDER_OU = ""
BUDGET_LINE = ""
BUDGET_LINE_2 = ""


def _key() -> str:
	return f"pln-pw-{uuid4().hex}"


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw(
		"Procurement Planning Playwright fixtures are test data. Enable "
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
			{
				"doctype": "User", "email": email, "first_name": first, "last_name": last,
				"send_welcome_email": 0, "enabled": 1,
			}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	elif frappe.db.get_value("User", email, "user_type") != "System User":
		frappe.get_doc("User", email).add_roles("Desk User")
	# an existing User row carries no password after a plain insert (the NDS
	# finding) — set it on every reset
	update_password(email, PASSWORD)


def _grant(email: str, role: str, unit: str = "") -> None:
	administration.grant(user=email, business_role=role, organisation_unit=unit, fixture_namespace=NS_PW, actor="Administrator")


def _unit(name: str) -> str:
	existing = frappe.db.get_value("Organisation Unit", {"unit_name": name}, "name")
	if existing:
		return existing
	return structure.add_organisation_unit(parent_id=structure._root(), name=name)["unit"]


def _budget_world() -> None:
	"""Budget → Active Version → two Lines on the fixture year, so the live
	`list_eligible_budget_lines` / `check_plan_affordability` contracts answer
	for real. Test scaffolding for another app's model, outside production
	paths (the NDS test-exemption precedent)."""
	global BUDGET_LINE, BUDGET_LINE_2
	budget = frappe.db.get_value("Procurement Budget", {"generated_reference": BUDGET_REF}, "name")
	if not budget:
		budget = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": BUDGET_REF, "fiscal_year": FY, "currency": "KES"}
		).insert(ignore_permissions=True).name
	for ref in (LINE_REF, LINE_REF_2):
		if not frappe.db.exists("Procurement Budget Line", {"generated_reference": ref}):
			frappe.get_doc({"doctype": "Procurement Budget Line", "generated_reference": ref, "budget": budget}).insert(ignore_permissions=True)
	BUDGET_LINE = frappe.db.get_value("Procurement Budget Line", {"generated_reference": LINE_REF}, "name")
	BUDGET_LINE_2 = frappe.db.get_value("Procurement Budget Line", {"generated_reference": LINE_REF_2}, "name")
	bv = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
	if not bv:
		bv = frappe.get_doc(
			{
				"doctype": "Procurement Budget Version", "generated_reference": "BUDV-PWPL-0001", "budget": budget,
				"version_number": 1, "status": "Active", "approval_reference": "PWPL-APPROVAL-1",
				"approval_date": "2026-06-30", "authorised_total": 200000000, "currency": "KES",
				"approval_document": "/files/pwpl-approval.pdf",
			}
		).insert(ignore_permissions=True).name
	fs = frappe.get_all("Funding Source", limit=1, pluck="name")
	for line, ref, title in (
		(BUDGET_LINE, "BLV-PWPL-0001", "Digital health infrastructure programme"),
		(BUDGET_LINE_2, "BLV-PWPL-0002", "Health workforce programme"),
	):
		if not frappe.db.exists("Procurement Budget Line Version", {"budget_version": bv, "budget_line": line}):
			frappe.get_doc(
				{
					"doctype": "Procurement Budget Line Version", "generated_reference": ref, "budget_version": bv,
					"budget_line": line, "title": title, "funding_source": fs[0] if fs else None,
					"approved_amount": 100000000, "currency": "KES",
				}
			).insert(ignore_permissions=True)


def _strategy_world() -> None:
	"""§7.2 — the site's one Active Strategic Plan: reuse the seeded plan's
	first Active Objective, else build a far-reaching plan (Slice B needs one)."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	if strategy_gateway.list_eligible_strategic_objectives():
		return
	plan = frappe.get_doc(
		{"doctype": "Strategic Plan", "title": "Playwright Planning Strategic Plan", "plan_role": "Primary", "period_start": "2020-01-01", "period_end": "2105-01-01"}
	).insert(ignore_permissions=True)
	version = frappe.get_doc(
		{"doctype": "Strategic Plan Version", "plan_id": plan.name, "version_number": 1, "effective_from": "2020-01-01", "effective_to": "2105-01-01"}
	).insert(ignore_permissions=True)
	pillar = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Pillar", "title": "PW Pillar", "display_order": 1}).insert(ignore_permissions=True)
	programme = frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Programme", "title": "PW Programme", "display_order": 2, "parent_node_id": pillar.name}).insert(ignore_permissions=True)
	frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Strategic Objective", "title": "PW Digital Objective", "display_order": 3, "parent_node_id": programme.name}).insert(ignore_permissions=True)
	frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")


def _open_years(flag: str) -> list[str]:
	return frappe.get_all("Fiscal Year", filters={flag: 1}, pluck="name")


def _move_flags() -> None:
	"""Move both single-valued intake flags onto the fixture year, remembering
	what was open so restore_site() can put it back (CFG-BR-010)."""
	if not frappe.defaults.get_global_default(PREVIOUS_FLAGS_KEY):
		previous = {
			"dpp": [y for y in _open_years(site_configuration.DPP_FLAG_OPEN) if y != FY],
			"needs": [y for y in _open_years(site_configuration.FLAG_OPEN) if y != FY],
		}
		frappe.defaults.set_global_default(PREVIOUS_FLAGS_KEY, json.dumps(previous))
	if not frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_OPEN):
		site_configuration.open_dpp_submission(fiscal_year=FY, closes_at=INTAKE_CLOSES_AT, reason="Planning Playwright world")
	elif str(frappe.db.get_value("Fiscal Year", FY, site_configuration.DPP_FLAG_CLOSES_AT) or "") != INTAKE_CLOSES_AT:
		frappe.db.set_value("Fiscal Year", FY, site_configuration.DPP_FLAG_CLOSES_AT, INTAKE_CLOSES_AT, update_modified=False)
	if not frappe.db.get_value("Fiscal Year", FY, site_configuration.FLAG_OPEN):
		site_configuration.open_needs_submission(fiscal_year=FY, reason="Planning Playwright world: Need-origin fixtures")


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	"""Put the intake flags back on the years that were open before the
	Playwright world moved them (the §8 seed's 2027-2028). Safe to call when
	nothing was moved."""
	_guard()
	frappe.set_user("Administrator")
	raw = frappe.defaults.get_global_default(PREVIOUS_FLAGS_KEY)
	restored = {"dpp": [], "needs": []}
	if raw:
		previous = json.loads(raw)
		for year in previous.get("dpp", []):
			if frappe.db.exists("Fiscal Year", year) and not frappe.db.get_value("Fiscal Year", year, site_configuration.DPP_FLAG_OPEN):
				site_configuration.open_dpp_submission(fiscal_year=year, reason="Playwright teardown: restore the previously open year")
				restored["dpp"].append(year)
		for year in previous.get("needs", []):
			if frappe.db.exists("Fiscal Year", year) and not frappe.db.get_value("Fiscal Year", year, site_configuration.FLAG_OPEN):
				site_configuration.open_needs_submission(fiscal_year=year, reason="Playwright teardown: restore the previously open year")
				restored["needs"].append(year)
		frappe.defaults.clear_default(PREVIOUS_FLAGS_KEY)
	if commit:
		frappe.db.commit()
	return restored


def _clear_context_preferences() -> None:
	for user in ACTORS:
		for key in CONTEXT_PREFERENCE_KEYS:
			frappe.defaults.clear_user_default(key, user)


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	"""The D13 world: fixture year, two units, catalogues, register, Budget
	and Strategy graphs, nine actors with their responsibilities, both intake
	flags on the fixture year."""
	global OU, OUTSIDER_OU
	from kentender_core.seeds import site_setup

	_guard()
	frappe.set_user("Administrator")
	if not site_configuration.is_configured():
		frappe.throw("Configure the site (System setup) before building the Planning Playwright world.")
	site_setup._seed_catalogues()
	if not frappe.db.exists("Fiscal Year", FY):
		site_configuration.add_fiscal_year(start_year=FY_START)
	if not frappe.db.get_value("UOM", UNIT, "enabled"):
		if frappe.db.exists("UOM", UNIT):
			frappe.db.set_value("UOM", UNIT, "enabled", 1, update_modified=False)
		else:
			frappe.get_doc({"doctype": "UOM", "uom_name": UNIT, "enabled": 1}).insert(ignore_permissions=True)
	OU = _unit(OU_NAME)
	OUTSIDER_OU = _unit(OUTSIDER_OU_NAME)
	site_setup._seed_regulatory_reference(fiscal_year=FY, fixture_namespace=NS_PW)
	if not frappe.db.exists("Currency", "KES"):
		frappe.get_doc({"doctype": "Currency", "currency_name": "KES", "enabled": 1}).insert(ignore_permissions=True)
	_budget_world()
	_strategy_world()

	for email, name in (
		(AUTHOR, "Playwright Planning Author"), (HOD, "Playwright Planning HoD"), (PLANNER, "Playwright Procurement Planner"),
		(FINANCE, "Playwright Finance Officer"), (ACCOUNTING_OFFICER, "Playwright Accounting Officer"),
		(STATUTORY, "Playwright Statutory Approver"), (AUDITOR, "Playwright Auditor"),
		(OUTSIDER, "Playwright Outsider Author"), (NOBODY, "Playwright Nobody"),
	):
		_user(email, name)
	_grant(AUTHOR, "Departmental Author", OU)
	_grant(HOD, "Departmental Author", OU)
	_grant(HOD, "Head of User Department", OU)
	_grant(PLANNER, "Procurement Planner")
	_grant(FINANCE, "Finance Confirmation Officer")
	_grant(ACCOUNTING_OFFICER, "Accounting Officer")
	_grant(STATUTORY, "Plan Statutory Approver")
	_grant(AUDITOR, "Auditor")
	_grant(OUTSIDER, "Departmental Author", OUTSIDER_OU)
	# PLN-AC-111..113 — a Frappe Role alone is not authority (AUTH §4): this
	# actor reaches the Page through a stale role and must get the Forbidden
	# panel from the resolver, with nothing else painted.
	nobody = frappe.get_doc("User", NOBODY)
	if "Auditor" not in {row.role for row in nobody.roles}:
		nobody.add_roles("Auditor")
	for assignment in frappe.get_all("User Responsibility Assignment", filters={"user": NOBODY}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", assignment, ignore_permissions=True, force=True)
	_move_flags()
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return {"fy": FY, "ou": OU, "ou_name": OU_NAME, "outsider_ou": OUTSIDER_OU}


# --- reset --------------------------------------------------------------------


def _wipe() -> None:
	"""Every Planning row on the fixture year (rows created through the API
	carry no namespace) plus the namespace-stamped rest, child → parent."""
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

	# Departmental Needs rows are NDS's to purge (`purge_fixture_needs`)

	# §6.1 — the journal is segregation evidence; scope the wipe to this world
	frappe.db.delete("Planning Command Journal", {"actor": ("in", ACTORS)})
	frappe.db.delete("Planning Command Journal", {"fixture_namespace": NS_PW})
	frappe.db.delete("Notification Log", {"for_user": ("in", ACTORS)})


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	"""Remove every Planning Playwright row (the purge entry point). The world
	itself (units, actors, Budget/Strategy graphs) stays; restore_site() puts
	the intake flags back."""
	_guard()
	frappe.set_user("Administrator")
	_wipe()
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS_PW, "fiscal_year": FY}


def _reset(commit: bool) -> dict[str, Any]:
	world = ensure_world(commit=False)
	_wipe()
	_clear_context_preferences()
	if commit:
		frappe.db.commit()
	return world


def reset_workspace_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""Empty world, both windows open — the workspace spec's start state."""
	return _reset(commit)


# --- journeys (real §8.2 commands as the fixture actors) --------------------


def _require_need(need: str) -> str:
	"""The accepted Need the browser helper obtained from NDS's fixture module."""
	if not need:
		frappe.throw(
			"This fixture needs an accepted Need: the browser helper obtains one from "
			"kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures.reset_accepted_needs_for and passes `need=`."
		)
	return need


def _open_dpp(unit: str = "", author: str = AUTHOR) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	with _as(author):
		return dpp_lifecycle.open_departmental_plan(
			organisation_unit=unit or OU, fiscal_year=FY, idempotency_key=_key(), fixture_namespace=NS_PW,
		)


def _need_entry(dpp_version: str, need: str) -> dict[str, Any]:
	row = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": dpp_version, "need": need}, ["name", "entry_id"], as_dict=True)
	if not row:
		frappe.throw("The accepted Need was not projected into the Draft DPP Version.")
	return row


def reset_dpp_fixture(*, need: str = "", with_direct: bool = False, funded: bool = False, commit: bool = True) -> dict[str, Any]:
	"""The caller's accepted Need projected into a freshly opened Draft DPP
	(funding incomplete). `with_direct` adds the PLN-DES-02 direct
	requirement; `funded` completes the Need's funding so the plan reads Ready
	to submit."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	world = _reset(commit=False)
	need = _require_need(need)
	opened = _open_dpp()
	entry = _need_entry(opened["current_version"], need)
	record_version = opened["record_version"]
	direct_entry_id = ""
	if funded:
		with _as(AUTHOR):
			saved = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry.entry_id, budget_line=BUDGET_LINE, indicative_amount=80000000,
				expected_record_version=record_version, idempotency_key=_key(),
			)
		record_version = saved["record_version"]
	if with_direct:
		with _as(AUTHOR):
			added = dpp_lifecycle.save_direct_requirement(
				dpp_version=opened["current_version"], values={**DIRECT_CONTENT, "budget_line": BUDGET_LINE},
				expected_record_version=record_version, idempotency_key=_key(),
			)
		record_version = added["record_version"]
		direct_entry_id = added["entry_id"]
	if commit:
		frappe.db.commit()
	return {
		**world, "need": need, "dpp_reference": opened["dpp_reference"], "dpp_version": opened["current_version"],
		"need_entry_id": entry.entry_id, "direct_entry_id": direct_entry_id, "record_version": record_version,
	}


def reset_review_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""The funded two-row plan submitted by the HoD with its Open validation
	task — the review spec's start."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	state = reset_dpp_fixture(need=need, with_direct=True, funded=True, commit=False)
	with _as(HOD):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=state["dpp_version"], certification_confirmed=True,
			expected_record_version=state["record_version"], idempotency_key=_key(),
		)
	task = frappe.db.get_value("Departmental Plan Validation Task", {"task_reference": submitted["task"]}, "name")
	if commit:
		frappe.db.commit()
	return {**state, "task": task, "submission": submitted["task"]}


def reset_accepted_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""The submitted plan accepted by the Planner (auto-creating the Draft
	Annual Plan), plus a second department's Draft DPP so the register holds
	two rows — PLN-DES-01's exact composition for the Planner."""
	from kentender_procurement.procurement_planning.services import dpp_validation

	state = reset_review_fixture(need=need, commit=False)
	task = frappe.get_doc("Departmental Plan Validation Task", state["task"])
	with _as(PLANNER):
		accepted = dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=_key(),
			classifications={state["need_entry_id"]: "Non-consulting services", state["direct_entry_id"]: "Consulting services"},
		)
	other = _open_dpp(unit=OUTSIDER_OU, author=OUTSIDER)
	if commit:
		frappe.db.commit()
	return {**state, "plan_reference": accepted["annual_plan"], "plan_version": accepted["annual_plan_version"], "other_dpp_reference": other["dpp_reference"]}


# --- Slice B journeys (Annual Plan workbench, formation, the Plan Item editor) --


def _accept(state: dict[str, Any], classifications: dict[str, str]) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_validation

	task = frappe.get_doc("Departmental Plan Validation Task", state["task"])
	with _as(PLANNER):
		return dpp_validation.accept_departmental_plan(
			task=task.name, task_token=task.task_token, idempotency_key=_key(), classifications=classifications,
		)


def _submit(dpp_version: str, record_version: int) -> str:
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	with _as(HOD):
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=dpp_version, certification_confirmed=True, expected_record_version=record_version, idempotency_key=_key(),
		)
	return frappe.db.get_value("Departmental Plan Validation Task", {"task_reference": submitted["task"]}, "name")


def reset_workbench_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-07's exact opening state: one accepted, unallocated Need-origin
	entry (KES 80,000,000) in the auto-created Draft Annual Plan."""
	state = reset_dpp_fixture(need=need, funded=True, commit=False)
	state["task"] = _submit(state["dpp_version"], state["record_version"])
	accepted = _accept(state, {state["need_entry_id"]: "Non-consulting services"})
	if commit:
		frappe.db.commit()
	return {**state, "plan_reference": accepted["annual_plan"], "plan_version": accepted["annual_plan_version"]}


def _form(plan_version: str, entries: list[str], mode: str) -> list[str]:
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench

	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=frappe.db.get_value("Annual Plan Version", plan_version, "annual_plan") and frappe.db.get_value("Annual Plan", frappe.db.get_value("Annual Plan Version", plan_version, "annual_plan"), "plan_reference"))
		formed = plan_workbench.form_plan_items(
			plan_version=plan_version, dpp_entries=entries, mode=mode,
			expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
	return formed["created_items"]


def reset_plan_item_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-09: the single-source Plan Item formed from the accepted Need."""
	state = reset_workbench_fixture(need=need, commit=False)
	entry = frappe.db.get_value("Departmental Plan Entry", {"dpp_version": state["dpp_version"], "entry_id": state["need_entry_id"]}, "name")
	items = _form(state["plan_version"], [entry], "each")
	if commit:
		frappe.db.commit()
	return {**state, "plan_item_id": items[0]}


def reset_combined_item_fixture(*, needs: list[str] | str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-09A: two accepted Needs (the browser helper's training and
	deployment laptops) on one Procurement Budget Line, both Goods, combined
	into one Plan Item."""
	from kentender_procurement.procurement_planning.services import dpp_lifecycle

	if isinstance(needs, str):
		needs = json.loads(needs) if needs else []
	if len(needs) != 2:
		frappe.throw("The combined fixture needs exactly two accepted Needs from NDS's fixture module (`needs=`).")
	world = _reset(commit=False)
	first, second = needs
	opened = _open_dpp()
	record_version = opened["record_version"]
	entries = []
	for need, amount in ((first, 48000000), (second, 72000000)):
		entry = _need_entry(opened["current_version"], need)
		with _as(AUTHOR):
			saved = dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry.entry_id, budget_line=BUDGET_LINE, indicative_amount=amount,
				expected_record_version=record_version, idempotency_key=_key(),
			)
		record_version = saved["record_version"]
		entries.append(entry)
	task = _submit(opened["current_version"], record_version)
	accepted = _accept({"task": task}, {e.entry_id: "Goods" for e in entries})
	items = _form(accepted["annual_plan_version"], [e.name for e in entries], "combined")
	if commit:
		frappe.db.commit()
	return {**world, "dpp_reference": opened["dpp_reference"], "plan_reference": accepted["annual_plan"], "plan_version": accepted["annual_plan_version"], "plan_item_id": items[0]}


# --- Slice C journeys (Finance confirmation, governance decisions) ------------

ITEM_VALUES = {
	"title": "Digital health infrastructure package",
	"description": "Procure and implement the national digital health infrastructure upgrade as one integrated programme.",
	"plan_horizon": "Single year",
	"aggregation_indicator": "Not aggregated",
	"lotting_indicator": "Single lot",
	"reservation_category": "None",
	"procurement_method": "Open Tender",
	"baseline_invitation_date": "2098-09-01",
	"tendering_period_days": 21,
	"evaluation_period_days": 30,
	"award_approval_buffer_days": 5,
	"notification_buffer_days": 2,
	"standstill_period_days": 14,
}


def _complete_item(plan_item_id: str, **overrides) -> None:
	from kentender_procurement.procurement_planning.services import plan_read, plan_workbench, strategy_gateway

	objective = strategy_gateway.list_eligible_strategic_objectives()[0]["id"]
	with _as(PLANNER):
		item = plan_read.get_plan_item(plan_item_id=plan_item_id)
		plan_workbench.save_plan_item(
			plan_item=plan_item_id, values={**ITEM_VALUES, "strategic_objective": objective, **overrides},
			expected_record_version=item["record_version"], idempotency_key=_key(),
		)


def _request_funding(plan_reference: str) -> str:
	from kentender_procurement.procurement_planning.services import plan_finance, plan_read

	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=plan_reference)
		requested = plan_finance.request_plan_funding_confirmation(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
	return requested["task"]


def reset_finance_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-10's opening state: the one complete Plan Item, funding
	confirmation requested — one Open Plan Finance Task for the Version."""
	state = reset_plan_item_fixture(need=need, commit=False)
	_complete_item(state["plan_item_id"])
	task = _request_funding(state["plan_reference"])
	if commit:
		frappe.db.commit()
	return {**state, "task": task}


def reset_governance_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""Funding confirmed and the Plan submitted: PLN-DES-11's Open Accounting
	Officer task."""
	from kentender_procurement.procurement_planning.services import plan_finance, plan_governance, plan_read

	state = reset_finance_fixture(need=need, commit=False)
	task = frappe.get_doc("Plan Finance Task", state["task"])
	with _as(FINANCE):
		plan_finance.confirm_plan_funding(task=task.name, task_token=task.task_token, idempotency_key=_key())
	with _as(PLANNER):
		plan = plan_read.get_annual_plan(plan_reference=state["plan_reference"])
		submitted = plan_governance.submit_consolidated_plan(
			plan_version=plan["version_reference"], expected_record_version=plan["record_version"], idempotency_key=_key(),
		)
	if commit:
		frappe.db.commit()
	return {**state, "finance_task": state["task"], "task": submitted["task"]}


def reset_statutory_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""Adopted by the Accounting Officer: PLN-DES-12's Open statutory task."""
	from kentender_procurement.procurement_planning.services import plan_governance

	state = reset_governance_fixture(need=need, commit=False)
	ao_task = frappe.get_doc("Plan Governance Task", state["task"])
	with _as(ACCOUNTING_OFFICER):
		adopted = plan_governance.adopt_and_submit_plan(task=ao_task.name, task_token=ao_task.task_token, idempotency_key=_key())
	if commit:
		frappe.db.commit()
	return {**state, "ao_task": state["task"], "task": adopted["statutory_task"]}


# --- Slice D journeys (Active plan, cascade, publication) ---------------------


def _approve(state: dict[str, Any], *, transmit=None) -> dict[str, Any]:
	from unittest.mock import patch

	from kentender_procurement.procurement_planning.services import plan_governance, plan_publication

	task = frappe.get_doc("Plan Governance Task", state["task"])
	with _as(STATUTORY):
		if transmit is None:
			return plan_governance.approve_annual_plan(task=task.name, task_token=task.task_token, idempotency_key=_key())
		with patch.object(plan_publication, "_transmit", return_value=transmit):
			return plan_governance.approve_annual_plan(task=task.name, task_token=task.task_token, idempotency_key=_key())


def reset_active_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-14's opening state: the approved, acknowledged, Active Plan
	with its one item's forecasts seeded from baseline."""
	state = reset_statutory_fixture(need=need, commit=False)
	approved = _approve(state)
	publication = frappe.db.get_value("Annual Plan Publication", {"plan_version": state["plan_version"], "result": "Acknowledged"}, "name")
	if commit:
		frappe.db.commit()
	return {**state, "publication_result": approved["publication_result"], "publication": publication}


def reset_publication_failed_fixture(*, need: str = "", commit: bool = True) -> dict[str, Any]:
	"""PLN-DES-13/16: the approved Plan whose first transmission failed —
	approval preserved, a technical retry pending."""
	state = reset_statutory_fixture(need=need, commit=False)
	approved = _approve(state, transmit=("Failed", ""))
	publication = frappe.db.get_value("Annual Plan Publication", {"plan_version": state["plan_version"]}, "name", order_by="attempt_number desc")
	if commit:
		frappe.db.commit()
	return {**state, "publication_result": approved["publication_result"], "publication": publication}


def run_milestone_check(*, today: str = "2098-08-25", commit: bool = True) -> dict[str, Any]:
	"""§8.3 `CheckApproachingMilestones` run for a pinned day (the fixture
	item's invitation is 1 Sep 2098; 25 Aug is inside the 14-day window)."""
	from kentender_procurement.procurement_planning.services import schedule

	_guard()
	frappe.set_user("Administrator")
	first = schedule.check_approaching_milestones(today=today)
	second = schedule.check_approaching_milestones(today=today)
	notifications = frappe.db.count("Notification Log", {"for_user": PLANNER, "email_header": ("like", "pln:milestone:%")})
	if commit:
		frappe.db.commit()
	return {"raised": [list(r) for r in first["raised"]], "raised_again": [list(r) for r in second["raised"]], "notifications": notifications}
