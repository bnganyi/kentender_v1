# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-010 — Record professional recommend / return on an In-review Plan Version."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	DECISION_RECOMMENDED,
	DECISION_RETURNED,
	DOCTYPE_DECISION,
	VALIDATION_READY,
	VERSION_IN_REVIEW,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services._invariants import (
	assert_version_concurrency,
	new_concurrency_token,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUTHORITY,
	ROLE_DESIGNATED_APPROVER,
	ROLE_REVIEWER,
	assert_can_recommend_plan,
	assert_can_return_plan,
	assert_planning_scope,
	operational_roles,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan

ACTION_RECOMMEND = "recommend"
ACTION_RETURN = "return"


def record_plan_decision(
	*,
	version: str,
	decision: str,
	comment: str | None = None,
	concurrency_token: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	action = cstr(decision).strip().lower()
	if action not in (ACTION_RECOMMEND, ACTION_RETURN):
		return {
			"ok": False,
			"errors": {"form": "Decision must be recommend or return."},
		}

	if action == ACTION_RECOMMEND:
		actor = assert_can_recommend_plan(user)
	else:
		actor = assert_can_return_plan(user)

	version_name = cstr(version).strip()
	if not version_name or not frappe.db.exists("Procurement Plan Version", version_name):
		return {"ok": False, "errors": {"form": "Plan Version not found"}}

	ver = frappe.get_doc("Procurement Plan Version", version_name)
	plan = frappe.get_doc("Procurement Plan", ver.plan)
	try:
		assert_planning_scope(
			procuring_entity=cstr(plan.procuring_entity).strip(),
			org_unit=cstr(plan.coordinating_org_unit or "").strip() or None,
			user=actor,
			require_write=True,
		)
	except frappe.PermissionError:
		return {"ok": False, "errors": {"form": "Not permitted for this organisational scope"}}

	if cstr(ver.status) != VERSION_IN_REVIEW:
		return {
			"ok": False,
			"errors": {"form": "Decisions can only be recorded while the version is In review."},
		}

	try:
		assert_version_concurrency(version_name, concurrency_token)
	except frappe.ValidationError as exc:
		return {"ok": False, "errors": {"form": str(exc) or "Concurrency conflict"}}

	note = cstr(comment or "").strip()
	errors: dict[str, str] = {}
	if action == ACTION_RETURN and not note:
		errors["decision_comment"] = "A comment is required when returning the Plan."

	if action == ACTION_RECOMMEND:
		validation = validate_plan(plan=plan.name, user=actor)
		if cstr(validation.get("status")) != VALIDATION_READY:
			errors["form"] = "Validation must be Ready before recommending approval."

	if errors:
		return {"ok": False, "errors": errors}

	now = now_datetime()
	token = new_concurrency_token()
	decision_label = DECISION_RECOMMENDED if action == ACTION_RECOMMEND else DECISION_RETURNED
	decision_type = "Recommendation" if action == ACTION_RECOMMEND else "Return"
	stage = "Professional review" if action == ACTION_RECOMMEND else "Return from review"

	if action == ACTION_RETURN:
		frappe.db.set_value(
			"Procurement Plan Version",
			version_name,
			{
				"status": VERSION_RETURNED,
				"concurrency_token": token,
			},
			update_modified=True,
		)
	else:
		frappe.db.set_value(
			"Procurement Plan Version",
			version_name,
			{"concurrency_token": token},
			update_modified=True,
		)

	frappe.get_doc(
		{
			"doctype": DOCTYPE_DECISION,
			"plan_version": version_name,
			"decision_type": decision_type,
			"decision_stage": stage,
			"actor": actor,
			"actor_role": _actor_role(actor, action),
			"decision": decision_label,
			"reason": note or ("Recommended for approval" if action == ACTION_RECOMMEND else ""),
			"decided_at": now,
		}
	).insert(ignore_permissions=True)

	frappe.db.commit()
	status = VERSION_RETURNED if action == ACTION_RETURN else VERSION_IN_REVIEW
	return {
		"ok": True,
		"plan": plan.name,
		"version": version_name,
		"decision": decision_label,
		"status": status,
		"concurrency_token": token,
		"actor": actor,
		"decided_at": str(now),
	}


def has_recommendation(*, version: str) -> bool:
	return bool(
		frappe.db.exists(
			DOCTYPE_DECISION,
			{"plan_version": version, "decision": DECISION_RECOMMENDED},
		)
	)


def _actor_role(user: str, action: str) -> str:
	roles = operational_roles(user)
	order = (
		(ROLE_REVIEWER, ROLE_AUTHORITY)
		if action == ACTION_RECOMMEND
		else (
			ROLE_DESIGNATED_APPROVER,
			ROLE_ACCOUNTING_OFFICER,
			ROLE_AUTHORITY,
			ROLE_REVIEWER,
		)
	)
	for role in order:
		if role in roles:
			return role
	return ROLE_REVIEWER
