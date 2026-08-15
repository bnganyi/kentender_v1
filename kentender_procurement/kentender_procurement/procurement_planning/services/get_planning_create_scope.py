"""Read-only annual Plan registration context for PLN-UI-02."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services.financial_context import enabled_fiscal_years, procuring_entity_financial_context
from kentender_procurement.procurement_planning.services.planning_permissions import (
	CREATE_PLAN_ROLES,
	assert_pe_resolved_for_create,
	require_operational_roles,
)


def get_planning_create_scope(
	*, procuring_entity: str, financial_year: str, user: str | None = None
) -> dict[str, Any]:
	actor = (user or frappe.session.user or "").strip()
	require_operational_roles(*CREATE_PLAN_ROLES, user=actor)
	selected_pe = cstr(procuring_entity).strip()
	selected_fy = cstr(financial_year).strip()
	if not selected_pe or not selected_fy:
		frappe.throw(
			frappe._("Explicit Procuring Entity and financial year context is required."),
			title="PLN_CREATE_CONTEXT_REQUIRED",
		)
	pe = assert_pe_resolved_for_create(user=actor, selected_pe=selected_pe)
	context = procuring_entity_financial_context(procuring_entity=pe, financial_year=selected_fy)
	existing = frappe.db.get_value(
		"Procurement Plan",
		{"procuring_entity": pe, "financial_year": context["financial_year"]},
		["name", "plan_code", "open_draft_version", "current_approved_version"],
		as_dict=True,
	)
	destination = ""
	if existing:
		destination = (
			f"/app/procurement-plan-builder?plan={existing.name}"
			if existing.current_approved_version and existing.open_draft_version
			else f"/app/procurement-plan-builder?plan={existing.name}"
		)
	return {
		"ok": True,
		**context,
		"financial_years": enabled_fiscal_years(),
		"identity_values": [
			{"label": "Procuring entity", "value": context["procuring_entity_label"]},
			{"label": "Financial year", "value": context["financial_year"], "mono": True},
			{"label": "Plan title", "value": context["title"]},
			{"label": "Plan period", "value": f"{context['period_start']} – {context['period_end']}"},
			{"label": "Reporting currency", "value": context["currency"], "mono": True},
		],
		"existing": bool(existing),
		"existing_plan": existing.name if existing else None,
		"destination": destination,
		"can_create": not bool(existing) and not context["is_past"],
		"message": (
			"An annual Procurement Plan already exists for this Procuring Entity and financial year."
			if existing
			else "The Plan identity is governed by the selected Procuring Entity and financial year."
		),
	}
