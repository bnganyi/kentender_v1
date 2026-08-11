# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-UI-07 projection — one OU Draft contribution for departmental sign-off."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.mvp1_constants import (
	DEPT_PREPARING,
	DEPT_RETURNED,
	DEPT_SUBMITTED,
	DOCTYPE_DEPT_SUBMISSION,
	ITEM_ACTIVE,
	ITEM_PROPOSED,
	VALIDATION_BLOCKED,
	VALIDATION_NEEDS_ATTENTION,
	VALIDATION_READY,
	VERSION_DRAFT,
	VERSION_RETURNED,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CAP_DEPT_CONTRIB_TASK,
	ROLE_HOD,
	has_any_operational_role,
	is_planning_read_only,
	require_capability,
)
from kentender_procurement.procurement_planning.services.validate_plan import validate_plan

DECLARATION_TEXT = (
	"I confirm that these requirements represent this Organisation Unit’s "
	"planned procurement needs for the stated financial year."
)


def _money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def _ou_label(ou: str) -> str:
	if not ou:
		return ""
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou)


def _focus_draft(plan_doc: Any) -> str:
	return cstr(plan_doc.open_draft_version or "").strip()


def _items_for_ou(*, plan: str, plan_version: str, organisation_unit: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan,
			"owner_org_unit": organisation_unit,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		fields=["name", "plan_item_code", "owner_org_unit"],
		order_by="creation asc",
	)
	out: list[dict[str, Any]] = []
	for it in rows:
		iv_name = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": it.name, "plan_version": plan_version},
			"name",
		)
		if not iv_name:
			continue
		iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			iv_name,
			[
				"name",
				"requirement_title",
				"confirmed_estimate",
				"procurement_method",
				"validation_projection",
				"currency",
			],
			as_dict=True,
		)
		if not iv:
			continue
		currency = cstr(iv.currency or "KES")
		amount = flt(iv.confirmed_estimate)
		out.append(
			{
				"plan_item": it.name,
				"plan_item_code": it.plan_item_code,
				"item_version": iv.name,
				"title": iv.requirement_title or it.plan_item_code,
				"amount": amount,
				"amount_display": _money(amount, currency),
				"method": iv.procurement_method or "—",
				"validation_projection": iv.validation_projection or "Not run",
			}
		)
	return out


def _resolve_ou(*, plan_doc: Any, actor: str, organisation_unit: str | None) -> str:
	from kentender_core.services.org_scope_access import permitted_org_units

	explicit = cstr(organisation_unit or "").strip()
	pe = cstr(plan_doc.procuring_entity).strip()
	units = permitted_org_units(actor, procuring_entity=pe)
	draft = _focus_draft(plan_doc)
	if not draft:
		return explicit or cstr(plan_doc.coordinating_org_unit or "").strip()

	# Prefer an OU that has items and is in scope.
	candidate_ous = frappe.get_all(
		"Procurement Plan Item",
		filters={
			"plan": plan_doc.name,
			"baseline_state": ["in", [ITEM_PROPOSED, ITEM_ACTIVE]],
		},
		pluck="owner_org_unit",
	)
	seen: list[str] = []
	for ou in candidate_ous:
		ou = cstr(ou or "").strip()
		if not ou or ou in seen:
			continue
		seen.append(ou)

	if explicit:
		if units is not None and explicit not in units:
			frappe.throw(
				frappe._("Not permitted for this organisational scope"),
				frappe.PermissionError,
				title="PLN_SCOPE_DENIED",
			)
		return explicit

	for ou in seen:
		if units is None or ou in units:
			return ou

	coord = cstr(plan_doc.coordinating_org_unit or "").strip()
	if coord and (units is None or coord in units):
		return coord
	if seen:
		return seen[0]
	return coord


def _dept_row(*, plan_version: str, organisation_unit: str) -> dict[str, Any] | None:
	name = frappe.db.get_value(
		DOCTYPE_DEPT_SUBMISSION,
		{"plan_version": plan_version, "organisation_unit": organisation_unit},
		"name",
	)
	if not name:
		return None
	return frappe.db.get_value(
		DOCTYPE_DEPT_SUBMISSION,
		name,
		["name", "status", "declaration", "submission_note", "return_reason", "submitted_by", "submitted_at"],
		as_dict=True,
	)


def _ou_validation_status(items: list[dict[str, Any]]) -> str:
	if not items:
		return "Not run"
	projs = [cstr(i.get("validation_projection") or "") for i in items]
	if any(p == VALIDATION_BLOCKED for p in projs):
		return VALIDATION_BLOCKED
	if any(p in (VALIDATION_NEEDS_ATTENTION, "Not run", "") for p in projs):
		return VALIDATION_NEEDS_ATTENTION
	if all(p == VALIDATION_READY for p in projs):
		return VALIDATION_READY
	return VALIDATION_NEEDS_ATTENTION


def _submission_hash(items: list[dict[str, Any]]) -> str:
	payload = "|".join(sorted(cstr(i.get("item_version") or "") for i in items))
	return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def actor_can_submit_departmental(
	*,
	plan_doc: Any,
	organisation_unit: str,
	items: list[dict[str, Any]],
	dept: dict[str, Any] | None,
	actor: str,
) -> bool:
	if is_planning_read_only(actor):
		return False
	if not has_any_operational_role(ROLE_HOD, user=actor):
		# Authority may open for support, but HoD is the declaration owner.
		return False
	draft = _focus_draft(plan_doc)
	if not draft:
		return False
	ver_status = cstr(
		frappe.db.get_value("Procurement Plan Version", draft, "status") or ""
	)
	if ver_status not in (VERSION_DRAFT, VERSION_RETURNED):
		return False
	if not items:
		return False
	if _ou_validation_status(items) != VALIDATION_READY:
		return False
	status = cstr(dept.status if dept else DEPT_PREPARING) or DEPT_PREPARING
	if status == DEPT_SUBMITTED:
		return False
	return True


def get_departmental_contribution(
	*,
	plan: str,
	organisation_unit: str | None = None,
	user: str | None = None,
	run_validation: bool = True,
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	plan_name = cstr(plan).strip()
	if not plan_name or not frappe.db.exists("Procurement Plan", plan_name):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")

	plan_doc = frappe.get_doc("Procurement Plan", plan_name)
	draft = _focus_draft(plan_doc)
	if not draft:
		frappe.throw(
			frappe._("Open a Draft revision before departmental sign-off."),
			title="PLN_NO_DRAFT",
		)

	ou = _resolve_ou(plan_doc=plan_doc, actor=actor, organisation_unit=organisation_unit)
	# C01: contribution is a task surface — not bare record READ (full remove in C02).
	require_capability(
		CAP_DEPT_CONTRIB_TASK,
		procuring_entity=cstr(plan_doc.procuring_entity).strip(),
		org_unit=ou or None,
		user=actor,
		require_write=False,
	)

	if run_validation:
		validate_plan(plan=plan_name, user=actor)

	items = _items_for_ou(plan=plan_name, plan_version=draft, organisation_unit=ou)
	dept = _dept_row(plan_version=draft, organisation_unit=ou)
	status = cstr(dept.status if dept else DEPT_PREPARING) or DEPT_PREPARING
	validation = _ou_validation_status(items)
	total = sum(flt(i.get("amount")) for i in items)
	currency = cstr(plan_doc.currency or "KES")
	can_submit = actor_can_submit_departmental(
		plan_doc=plan_doc,
		organisation_unit=ou,
		items=items,
		dept=dept,
		actor=actor,
	)

	return {
		"ok": True,
		"plan": plan_name,
		"plan_version": draft,
		"organisation_unit": ou,
		"organisation_unit_label": _ou_label(ou),
		"financial_year": plan_doc.financial_year,
		"item_count": len(items),
		"planned_total": total,
		"planned_total_display": _money(total, currency),
		"currency": currency,
		"validation_projection": validation,
		"contribution_status": status,
		"return_reason": cstr(dept.return_reason if dept else "") or "",
		"submission_note": cstr(dept.submission_note if dept else "") or "",
		"declaration_text": DECLARATION_TEXT,
		"items": items,
		"can_submit": can_submit,
		"read_only": is_planning_read_only(actor) or not can_submit,
	}
