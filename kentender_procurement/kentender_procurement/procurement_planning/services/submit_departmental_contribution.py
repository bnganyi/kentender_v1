# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-008 — Submit departmental contribution (PLN-UI-07)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	DEPT_PREPARING,
	DEPT_RETURNED,
	DEPT_SUBMITTED,
	DOCTYPE_DEPT_SUBMISSION,
	VALIDATION_BLOCKED,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_READY,
)
from kentender_procurement.procurement_planning.services.get_departmental_contribution import (
	DECLARATION_TEXT,
	_dept_row,
	_items_for_ou,
	_ou_validation_status,
	_resolve_ou,
	_submission_hash,
	get_departmental_contribution,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_submit_departmental_contribution,
	assert_planning_scope,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan


def submit_departmental_contribution(
	*,
	plan: str,
	organisation_unit: str | None = None,
	declaration: int | str | bool | None = None,
	submission_note: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_submit_departmental_contribution(user)
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		return {"ok": False, "errors": {"form": "Procurement Plan not found"}}

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	draft = cstr(plan_doc.open_draft_version or "").strip()
	if not draft:
		return {
			"ok": False,
			"errors": {"form": "Open a Draft revision before departmental sign-off."},
		}

	ou = _resolve_ou(plan_doc=plan_doc, actor=actor, organisation_unit=organisation_unit)
	try:
		assert_planning_scope(
			procuring_entity=cstr(plan_doc.procuring_entity).strip(),
			org_unit=ou or None,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError:
		return {"ok": False, "errors": {"form": "Not permitted for this organisational scope"}}

	declared = declaration in (1, "1", True, "true", "True", "on", "yes")
	errors: dict[str, str] = {}
	if not declared:
		errors["declaration"] = "Confirm the declaration before submitting this contribution."

	validate_plan(plan=plan_name, user=actor)
	items = _items_for_ou(plan=plan_name, plan_version=draft, organisation_unit=ou)
	if not items:
		errors["form"] = "No Plan Items for this Organisation Unit to submit."
	else:
		status = _ou_validation_status(items)
		if status == VALIDATION_BLOCKED:
			errors["form"] = "Resolve blocking validation issues before sign-off."
		elif status in (VALIDATION_NEEDS_ATTENTION, "Not run", ""):
			errors["form"] = (
				"Complete Plan Item decisions until validation is Ready before sign-off."
			)

	dept = _dept_row(plan_version=draft, organisation_unit=ou)
	current = cstr(dept.status if dept else DEPT_PREPARING) or DEPT_PREPARING
	if current == DEPT_SUBMITTED:
		errors["form"] = "This contribution is already submitted."

	if errors:
		return {"ok": False, "errors": errors}

	note = cstr(submission_note or "").strip()
	payload = {
		"status": DEPT_SUBMITTED,
		"declaration": DECLARATION_TEXT,
		"submission_note": note,
		"submitted_by": actor,
		"submitted_at": now_datetime(),
		"submission_hash": _submission_hash(items),
		"return_reason": "",
	}
	if dept and dept.name:
		doc = frappe.get_doc(DOCTYPE_DEPT_SUBMISSION, dept.name)
		doc.update(payload)
		doc.save(ignore_permissions=True)
		name = doc.name
	else:
		doc = frappe.get_doc(
			{
				"doctype": DOCTYPE_DEPT_SUBMISSION,
				"plan_version": draft,
				"organisation_unit": ou,
				**payload,
			}
		)
		doc.insert(ignore_permissions=True)
		name = doc.name

	frappe.db.commit()
	projection = get_departmental_contribution(
		plan=plan_name,
		organisation_unit=ou,
		user=actor,
		run_validation=False,
	)
	return {
		"ok": True,
		"departmental_submission": name,
		"organisation_unit": ou,
		"contribution_status": DEPT_SUBMITTED,
		"projection": projection,
		"actor": actor,
	}
