"""AUTH-UI-05 neutral, audited Procurement Plan support projection."""

from __future__ import annotations

import frappe
from frappe.utils import cstr, flt

from kentender_core.services.authorization_diagnostics import authorize_support_record_view
from kentender_core.services.authorization_policy import ResourceContext
from kentender_procurement.procurement_planning.mvp1_constants import FINANCE_CONFIRMED
from kentender_procurement.procurement_planning.services.plan_item_finance import effective_finance_status


def _version_summary(version: str) -> tuple[float, int, int]:
	if not version:
		return 0.0, 0, 0
	rows = frappe.get_all("Procurement Plan Item Version", filters={"plan_version": version}, pluck="name")
	total = confirmed = 0
	value = 0.0
	for name in rows:
		doc = frappe.get_doc("Procurement Plan Item Version", name)
		value += flt(doc.confirmed_estimate)
		total += 1
		confirmed += effective_finance_status(doc) == FINANCE_CONFIRMED
	return value, confirmed, total


def get_support_plan(*, plan: str, purpose: str, user: str | None = None) -> dict:
	actor = user or frappe.session.user
	if not frappe.db.exists("Procurement Plan", plan):
		frappe.throw(frappe._("Procurement Plan not found."), title="PLN_PLAN_NOT_FOUND")
	doc = frappe.get_doc("Procurement Plan", plan)
	resource = ResourceContext("Procurement Plan", doc.name, doc.procuring_entity, cstr(doc.financial_year))
	authorize_support_record_view(user=actor, resource=resource, purpose=purpose)
	approved_value, _, _ = _version_summary(cstr(doc.current_approved_version))
	draft_value, confirmed, total = _version_summary(cstr(doc.open_draft_version))
	pe_label = frappe.db.get_value("Procuring Entity", doc.procuring_entity, "entity_name") or doc.procuring_entity
	return {
		"access_label": "Support read-only", "access_copy": "You can inspect this neutral Plan projection for support. You cannot perform Planning, Finance or approval actions. This access is audited.",
		"plan": doc.name, "title": cstr(doc.get("plan_title") or doc.get("title") or doc.name), "lifecycle": cstr(doc.lifecycle_state), "procuring_entity": pe_label, "financial_year": cstr(doc.financial_year),
		"approved_version": cstr(doc.current_approved_version), "draft_version": cstr(doc.open_draft_version),
		"approved_value": f"{doc.currency or 'KES'} {approved_value:,.0f}", "draft_value": f"{doc.currency or 'KES'} {draft_value:,.0f}",
		"finance_confirmed": f"{confirmed} of {total}", "validation": cstr(frappe.db.get_value("Procurement Plan Version", doc.open_draft_version, "validation_status") if doc.open_draft_version and frappe.get_meta("Procurement Plan Version").has_field("validation_status") else "Not run"),
		"actions": {"back": {"label": "Back to access diagnostic", "route": "/app/access-diagnostic"}},
	}
