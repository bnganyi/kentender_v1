# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-SVC-002 — register annual logical Plan + Version 1 Draft."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.mvp1_constants import (
	PLAN_OPEN,
	PLAN_TYPE_ANNUAL,
	PUB_NOT_SUBMITTED,
	VALIDATION_NOT_RUN,
	VERSION_DRAFT,
)
from kentender_procurement.procurement_planning.services._invariants import (
	ensure_unique_plan,
	new_concurrency_token,
	next_plan_code,
	period_dates_for_financial_year,
)
from kentender_procurement.procurement_planning.services.planning_permissions import (
	assert_can_create_plan,
	assert_pe_resolved_for_create,
	assert_planning_scope,
)


def create_procurement_plan(
	*,
	procuring_entity: str,
	financial_year: str,
	title: str,
	currency: str,
	coordinating_org_unit: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = assert_can_create_plan(user)
	requested_pe = cstr(procuring_entity).strip()
	pe = assert_pe_resolved_for_create(user=actor, selected_pe=requested_pe or None)
	fy = cstr(financial_year).strip()
	ttl = cstr(title).strip()
	cur = (cstr(currency).strip() or "KES").upper()
	ou = cstr(coordinating_org_unit).strip()
	if cur != "KES":
		frappe.throw(_("Kenya MVP plans use KES only."), title="PLN_CURRENCY_KES")
	if not fy or not ttl or not ou:
		frappe.throw(
			_("Procuring Entity, financial year, title and coordinating unit are required."),
			title="PLN_PLAN_REQUIRED",
		)
	if not frappe.db.exists("Procuring Entity", pe):
		frappe.throw(_("Procuring Entity not found."), title="PLN_PE_NOT_FOUND")
	if not frappe.db.exists("Organisation Unit", ou):
		frappe.throw(_("Organisation Unit not found."), title="PLN_OU_NOT_FOUND")

	assert_planning_scope(
		procuring_entity=pe,
		org_unit=ou,
		user=actor,
		require_write=True,
	)

	ensure_unique_plan(pe, fy)
	period_start, period_end = period_dates_for_financial_year(fy)
	plan_code = next_plan_code(pe, fy)

	plan = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_code": plan_code,
			"title": ttl,
			"procuring_entity": pe,
			"financial_year": fy,
			"period_start": period_start,
			"period_end": period_end,
			"currency": cur,
			"plan_type": PLAN_TYPE_ANNUAL,
			"coordinating_org_unit": ou,
			"lifecycle_state": PLAN_OPEN,
			"publication_projection": PUB_NOT_SUBMITTED,
		}
	)
	plan.insert(ignore_permissions=True)

	version_code = f"{plan_code}-V1"
	version = frappe.get_doc(
		{
			"doctype": "Procurement Plan Version",
			"plan": plan.name,
			"version_number": 1,
			"version_code": version_code,
			"status": VERSION_DRAFT,
			"version_reason": "Initial draft",
			"validation_projection": VALIDATION_NOT_RUN,
			"concurrency_token": new_concurrency_token(),
		}
	)
	version.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Procurement Plan",
		plan.name,
		{"open_draft_version": version.name},
		update_modified=False,
	)

	return {
		"ok": True,
		"plan": plan.name,
		"plan_code": plan_code,
		"version": version.name,
		"version_code": version_code,
		"lifecycle_state": PLAN_OPEN,
		"version_status": VERSION_DRAFT,
		"created_by": actor,
		"created_at": str(now_datetime()),
	}
