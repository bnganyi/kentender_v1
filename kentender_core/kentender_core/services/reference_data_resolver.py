# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 §9 — downstream PE/FY Context resolution.

Not an extension of org_scope_access.py's User-Scope-Assignment-based model
(that is a separate, older mechanism used by Strategy/Budget) — built on
authorization_policy.resolve_effective_access() instead, the same engine the
rest of this module's permission wiring already uses. See the tracker's
decision log for why.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_core.services.authorization_policy import resolve_effective_access
from kentender_core.services.reference_data_permissions import require_context_capability

# Any reference-data capability implies the holder may at least *view* contexts
# scoped to the PEs they're assigned to — read access is not itself a separate
# governed capability in §7's role table (every role there reads its own PE).
_VIEW_IMPLYING_CAPABILITIES = {
	"reference_data.context.create_draft",
	"reference_data.context.recommend",
	"reference_data.context.approve",
}


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
	at = get_datetime(at_time) if at_time else now_datetime()

	assignments = resolve_effective_access(user, at_time=at)
	authorized_pes: set[str] = set()
	for row in assignments:
		if _VIEW_IMPLYING_CAPABILITIES.intersection(row.get("capabilities") or []):
			authorized_pes.add(row["procuring_entity_id"])

	if not authorized_pes:
		return {"contexts": [], "auto_selected": None, "remembered_context_valid": False}

	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": ["in", sorted(authorized_pes)], "context_status": "Active"},
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
	capability: str,
	context_name: str,
	*,
	at_time=None,
) -> dict[str, Any]:
	"""§10 ValidateContextForCommand — every downstream state-changing command
	should call this before acting. Returns {"allowed": True} or throws
	PEFY_CONTEXT_NOT_ACTIVE for every denial path — never leaks whether a
	genuinely out-of-scope context exists. AC-013 requires this literally: an
	out-of-scope-but-real context and a non-existent one must be indistinguishable
	to the caller, so a capability denial here is normalized to the same safe
	message/title rather than letting authorization_policy's own distinct
	CAPABILITY_NOT_ASSIGNED wording (which implies existence) leak through."""

	def _deny():
		frappe.throw("This PE/FY context is not available for new work.", title="PEFY_CONTEXT_NOT_ACTIVE")

	if not frappe.db.exists("PE Fiscal Year Context", context_name):
		_deny()
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	try:
		require_context_capability(user, capability, context_name, ctx.procuring_entity, ctx.financial_year)
	except frappe.PermissionError:
		# require_capability() already msgprint'd its own CAPABILITY_NOT_ASSIGNED-style
		# message before raising — discard it so only the normalized safe message reaches
		# the caller, or the leaked message itself would disclose that this context exists.
		frappe.local.message_log = []
		_deny()
	if ctx.context_status != "Active":
		_deny()
	return {"allowed": True, "context": context_name, "context_status": ctx.context_status}
