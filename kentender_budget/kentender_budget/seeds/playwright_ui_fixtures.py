# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright-only UI fixture: a real-time Active Budget baseline for
BUD-UI-01's workspace auto-resolve.

`get_budget_workspace()` has no PE/FY selector (BUD-CHG-001 v1.2 §10/§12.1's
own documented stopgap — see budget_contracts._current_financial_year) and
resolves "current" Financial Year from genuine `nowdate()`, not the shared
seed narrative's fixed FIXTURE_NOW (2027-11-05) — Budget Version.validate()
rejects a future approval_date and has no fixture-clock override (see
kentender_mvp_v1_portfolio.py's own module docstring). The canonical
MOH-BUD-2027-001 baseline therefore only renders on BUD-UI-01 while real
wall-clock time happens to fall inside FY-2027-2028 (Jul 2027 - Jun 2028) —
everywhere else it is reached by direct navigation (BUD-UI-03/04/05), which
does not depend on "today".

This fixture creates a second, distinct Active Budget for PE-MOH in whatever
Financial Year covers *today* at seed-run time, using the same real
USER_BUD_OFFICER / USER_BUD_APPROVER personas — so BUD-UI-01's Active-state
UI has something real to render regardless of when the Playwright suite
runs. Idempotent; safe to call every run.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import getdate, nowdate

from kentender_budget.seeds.kentender_mvp_v1_portfolio import (
	_as_user,
	_ensure_isolated_fy,
	_offset_date,
	_upsert_active_baseline,
	FUNDING_SOURCE,
)
from kentender_budget.services.budget_permissions import ensure_budget_roles
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_core.seeds.kentender_mvp_v1 import constants as C

BUD_PW_CURRENT = "BUD-PW-CURRENT"
BUD_PW_CURRENT_V1 = "BUD-PW-CURRENT-V1"


def _current_fy_start_year() -> int:
	"""Kenya fiscal year: 1 Jul - 30 Jun, matching every FY row already
	seeded (`FY-2027-2028` = 2027-07-01..2028-06-30)."""
	today = getdate(nowdate())
	return today.year if today.month >= 7 else today.year - 1


def upsert_playwright_current_baseline() -> dict[str, Any]:
	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	ensure_currency_kes()
	pe_moh = ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH")

	start_year = _current_fy_start_year()
	fy = _ensure_isolated_fy(start_year, pe_moh)

	result = _upsert_active_baseline(
		pe=pe_moh,
		fy=fy,
		officer=C.USER_BUD_OFFICER,
		approver=C.USER_BUD_APPROVER,
		budget_ref=BUD_PW_CURRENT,
		version_ref=BUD_PW_CURRENT_V1,
		approval_reference="MOH-FIN-BUD-PW-CURRENT (Playwright fixture)",
		authorised_total=50_000_000,
		approval_document="/files/moh-approved-procurement-budget-pw-current-demo.pdf",
		lines=(
			{
				"title": "Playwright current-baseline test line",
				"owner_org_unit": C.OU_DIR_DHP,
				"approved_amount": 50_000_000,
				"code": "BUD-PW-CURRENT-L1",
			},
		),
	)
	frappe.db.commit()
	return {"budget_code": BUD_PW_CURRENT, "version_code": BUD_PW_CURRENT_V1, "financial_year": fy, **result}


BUD_PW_SCOPELESS_VIEWER = "bud.pw.scopeless.viewer@example.test"


def ensure_scopeless_budget_viewer() -> str:
	"""A real, non-admin user holding a Page-allowed Budget role (so Frappe's
	own Page.roles gate lets them load /app/budget-funding at all) but with
	*no* Procuring Entity scope (no User Permission/User Scope Assignment
	row) — the only way to actually reach BudgetWorkspaceScreen.vue's own
	graceful "Forbidden" branch. A user with zero Budget role never gets
	past the Page's own role gate in the first place (a hard Frappe 403
	dialog, not Budget's in-app state); Administrator/System Manager never
	hits this branch either since resolve_scoped_entity() never fails
	closed for them. Idempotent; safe to call every run."""
	from frappe.utils.password import update_password

	frappe.only_for(("System Manager", "Administrator"))
	ensure_budget_roles()
	email = BUD_PW_SCOPELESS_VIEWER
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Playwright",
				"last_name": "Scopeless Viewer",
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	missing = [r for r in ("Desk User", "Budget Viewer") if r not in {row.role for row in user.roles}]
	if missing:
		user.add_roles(*missing)
	update_password(email, "Test@123")
	# Deliberately no ensure_user_permission/User Scope Assignment call — an
	# unscoped Budget Viewer is exactly the fixture this test needs.
	frappe.db.commit()
	return email


def _reset_budget(budget_ref: str) -> None:
	"""Cascade-delete any existing Budget with this generated_reference, so a
	Playwright-only fixture can be recreated fresh every test run (mirrors
	kentender_core.seeds.kentender_mvp_v1.clear._delete_budget_graph)."""
	from kentender_core.seeds.kentender_mvp_v1.clear import _delete_budget_graph

	name = frappe.db.get_value("Budget", {"generated_reference": budget_ref}, "name")
	if name:
		_delete_budget_graph(name, {})
		frappe.db.commit()


def _reset_budget_for_pe_fy(pe: str, fy: str) -> None:
	"""Cascade-delete whatever Budget currently occupies this (Procuring
	Entity, Financial Year) slot (BUD-BR-001: at most one), regardless of its
	generated_reference. Unlike the seed helpers in kentender_mvp_v1_portfolio.py,
	a Playwright spec drives real UI clicks through save_budget_version_draft's
	own auto-allocator (allocate_budget_reference) — there is no post-hoc
	rename step — so a prior run's Budget never has a predictable reference
	to reset by; the (PE, FY) pair is the only stable key (confirmed live:
	resetting by a fixed reference left a stray "CGKIS-BUD-2026-002" behind
	that a subsequent run's own reset never matched, permanently blocking
	this PE+FY slot's "no baseline" state)."""
	from kentender_core.seeds.kentender_mvp_v1.clear import _delete_budget_graph

	name = frappe.db.get_value("Budget", {"procuring_entity": pe, "financial_year": fy}, "name")
	if name:
		_delete_budget_graph(name, {})
		frappe.db.commit()


def reset_editor_create_fixture() -> dict[str, Any]:
	"""BUD-UI-02 pre-creation form: delete any prior Playwright-created Budget
	for PE-CGKIS in *today's* Financial Year, so the "Register approved
	budget" flow (one Budget per PE+FY, BUD-BR-001) can be exercised fresh
	every run. PE-CGKIS is used (not PE-MOH) because upsert_playwright_
	current_baseline already occupies PE-MOH's current-FY slot."""
	frappe.only_for(("System Manager", "Administrator"))
	pe_cgk = ensure_procuring_entity(
		C.PE_CGKIS, C.PE_CGKIS_NAME, entity_type="County Government", short_name="Kisumu"
	)
	start_year = _current_fy_start_year()
	fy = _ensure_isolated_fy(start_year, pe_cgk)
	_reset_budget_for_pe_fy(pe_cgk, fy)
	return {"procuring_entity": pe_cgk, "financial_year": fy}


def _create_pending_task(
	*, budget_ref: str, fy_start_year: int, submitter: str, approved_amount: float = 40_000_000
) -> dict[str, Any]:
	"""One fresh Budget+Version left at 'Submitted for approval' (never
	auto-approved) — the BUD-UI-04 approval task screen's own precondition.
	Always reset-and-recreated so the Return/Approve UI flows have a clean,
	still-decidable version every run."""
	from kentender_budget.services import budget_contracts as contracts
	from kentender_budget.services import budget_line_contracts as lines_svc
	from kentender_budget.services import budget_readiness_contracts as readiness

	_reset_budget(budget_ref)
	pe = ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH")
	fy = _ensure_isolated_fy(fy_start_year, pe)

	prior_user = frappe.session.user
	try:
		_as_user(submitter)
		result = contracts.save_budget_version_draft(
			{
				"procuring_entity": pe,
				"financial_year": fy,
				"approval_reference": f"{budget_ref} (Playwright fixture)",
				"approval_date": _offset_date(5),
				"authorised_total": approved_amount,
				"approval_document": "/files/playwright-approval-task-demo.pdf",
			}
		)
		if not result.get("ok"):
			frappe.throw(f"Playwright fixture: could not create {budget_ref} draft: {result.get('errors')}")
		budget_name = result["budget"]["id"]
		version_name = result["version"]["id"]
		frappe.db.set_value("Budget", budget_name, "generated_reference", budget_ref, update_modified=False)
		frappe.db.set_value("Budget Version", version_name, "generated_reference", f"{budget_ref}-V1", update_modified=False)

		lines_result = lines_svc.save_budget_lines_draft(
			{
				"budget_version": version_name,
				"lines": [
					{
						"title": "Playwright approval-task test line",
						"owner_org_unit": C.OU_DIR_DHP,
						"funding_source": FUNDING_SOURCE,
						"approved_amount": approved_amount,
					}
				],
			}
		)
		if not lines_result.get("ok"):
			frappe.throw(f"Playwright fixture: could not save {budget_ref} lines: {lines_result.get('errors')}")

		submit_result = readiness.submit_budget_version({"budget_version": version_name})
		if not submit_result.get("ok"):
			frappe.throw(f"Playwright fixture: could not submit {budget_ref}: {submit_result.get('blockers')}")

		frappe.db.commit()
		return {"budget": budget_name, "version": version_name, "version_code": f"{budget_ref}-V1"}
	finally:
		frappe.set_user(prior_user)


def reset_approval_task_return_fixture() -> dict[str, Any]:
	"""BUD-PW-TASK-RETURN — a fresh Submitted-for-approval initial baseline,
	submitted by USER_BUD_OFFICER, for the Approver's Return flow."""
	return _create_pending_task(budget_ref="BUD-PW-TASK-RETURN", fy_start_year=2036, submitter=C.USER_BUD_OFFICER)


def reset_approval_task_approve_fixture() -> dict[str, Any]:
	"""BUD-PW-TASK-APPROVE — a fresh Submitted-for-approval initial baseline,
	submitted by USER_BUD_OFFICER, for the Approver's Approve flow."""
	return _create_pending_task(budget_ref="BUD-PW-TASK-APPROVE", fy_start_year=2037, submitter=C.USER_BUD_OFFICER)


def reset_approval_task_selfblock_fixture() -> dict[str, Any]:
	"""BUD-PW-TASK-SELFBLOCK — submitted by USER_BUD_DUAL (holds both Budget
	Officer and Budget Approver): BUD-AC-008 requires that persona's own
	Approve action stay blocked on this exact version, Return still allowed."""
	return _create_pending_task(budget_ref="BUD-PW-TASK-SELFBLOCK", fy_start_year=2038, submitter=C.USER_BUD_DUAL)
