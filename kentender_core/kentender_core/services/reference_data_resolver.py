# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.4 §9 — downstream PE/FY Context resolution.

Reference Data Manager is a global central Role (AUTH-ADR-001 v1.1 §5.2): it
carries no PE-specific scope, so a holder is authorized to view every active
context rather than a filtered subset. Everyone else has no reference-data
maintenance view — a genuine per-module business context selector (Budget,
Departmental Needs, Strategy, ...) is each owning module's own concern and is
not implemented here.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services.reference_data_permissions import has_reference_data_read_access


def _snapshot(context_row: dict) -> dict[str, Any]:
	pe = frappe.db.get_value(
		"Procuring Entity", context_row.procuring_entity, ["entity_code", "legal_name", "entity_type"], as_dict=True
	)
	fy = frappe.db.get_value(
		"Financial Year", context_row.financial_year, ["label", "start_date", "end_date", "timezone"], as_dict=True
	)
	return {
		"context_id": context_row.name,
		"procuring_entity": {
			"id": context_row.procuring_entity,
			"code": pe.entity_code if pe else context_row.procuring_entity,
			"name": pe.legal_name if pe else "",
			"type": pe.entity_type if pe else "",
		},
		"financial_year": {
			"id": context_row.financial_year,
			"label": fy.label if fy else context_row.financial_year,
			"start_date": str(fy.start_date) if fy else None,
			"end_date": str(fy.end_date) if fy else None,
		},
		"timezone": fy.timezone if fy else "Africa/Nairobi",
		"context_status": context_row.context_status,
	}


def resolve_authorized_contexts(
	user: str | None = None,
	*,
	remembered_context: str | None = None,
	at_time=None,
) -> dict[str, Any]:
	"""§9 — zero/one/many authorized contexts for the actor, revalidating any
	remembered selection. Never discloses a context's existence outside scope:
	an out-of-scope remembered_context is silently dropped, not reported as
	'exists but denied'."""
	user = user or frappe.session.user

	if not has_reference_data_read_access(user):
		return {"contexts": [], "auto_selected": None, "remembered_context_valid": False}

	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"context_status": "Active"},
		fields=["name", "procuring_entity", "financial_year", "context_status"],
	)
	contexts = [_snapshot(row) for row in rows]

	remembered_valid = bool(remembered_context) and any(c["context_id"] == remembered_context for c in contexts)

	return {
		"contexts": contexts,
		"auto_selected": contexts[0]["context_id"] if len(contexts) == 1 else None,
		"remembered_context_valid": remembered_valid,
	}


def validate_context_for_command(
	user: str,
	context_name: str,
	*,
	at_time=None,
) -> dict[str, Any]:
	"""§10 ValidateContextForCommand — every downstream state-changing command
	should call this before acting, to confirm the operating context it was
	given is real and Active. This is a record-state check only: it never
	requires Reference Data Manager (that Role governs who may maintain the
	context, not who may transact within it — the owning module's own Role,
	scope and state checks decide that). Returns {"allowed": True} or throws
	PEFY_CONTEXT_NOT_ACTIVE for every denial path — never leaks whether a
	genuinely out-of-scope context exists."""

	def _deny():
		frappe.throw("This PE/FY context is not available for new work.", title="PEFY_CONTEXT_NOT_ACTIVE")

	if not frappe.db.exists("PE Fiscal Year Context", context_name):
		_deny()
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	if ctx.context_status != "Active":
		_deny()
	return {"allowed": True, "context": context_name, "context_status": ctx.context_status}
