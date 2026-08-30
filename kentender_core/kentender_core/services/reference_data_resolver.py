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


def _authorized_context_rows(user: str) -> tuple[str, list[dict[str, Any]]]:
	"""The PE Fiscal Year Context rows `user` may pick as a working context,
	plus a mode tag: "unrestricted" (Administrator/System Manager — every
	non-Suspended context), "single"/"multiple" (a scoped user's permitted
	Procuring Entities have exactly one, or more than one, such context), or
	"none" (no permitted Procuring Entity, or none has a usable context).
	Suspended contexts are excluded (a temporarily-blocked state, not a
	normal working context); Scheduled/Active/Closed are all selectable so a
	user can prepare an upcoming FY or review a prior one — "today" is only
	ever a default suggestion, never the sole resolution path."""
	from kentender_core.services.org_scope_access import permitted_procuring_entities

	pes = permitted_procuring_entities(user)
	filters: dict[str, Any] = {"context_status": ["!=", "Suspended"]}
	if pes is not None:
		if not pes:
			return "none", []
		filters["procuring_entity"] = ["in", sorted(pes)]

	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters=filters,
		fields=["name", "procuring_entity", "financial_year", "context_status"],
		order_by="financial_year desc",
	)
	contexts = [_snapshot(row) for row in rows]
	if pes is None:
		mode = "unrestricted"
	elif not contexts:
		mode = "none"
	elif len(contexts) == 1:
		mode = "single"
	else:
		mode = "multiple"
	return mode, contexts


def resolve_working_context(
	module: str,
	user: str | None = None,
	*,
	requested_context: str | None = None,
) -> dict[str, Any]:
	"""COMPAT SHIM (CTX-CHG-001 Phase D). The response contract is unchanged —
	{mode, contexts, selected, selection_required} over PE Fiscal Year Context
	rows — but the storage underneath is the corrected working-context model:
	the GLOBAL working Procuring Entity plus this module's own remembered
	Financial Year (kentender_core.services.working_context), not a per-module
	context id. A context picked here therefore moves the caller's global PE —
	visible in the PageRail switcher and every other module — while the FY
	stays this module's own. The old kt_{module}_working_context defaults are
	migrated by kentender_budget's Phase D patch.

	Resolution stays never-authoritative: an explicit requested_context is
	validated against the caller's authorized rows and then persisted (a deep
	link is a deliberate choice); otherwise the global PE narrows the rows and
	the module FY picks within them; a single candidate auto-selects; anything
	else prompts. A working PE with no authorized context here falls back to
	the full row set — a preference can never trap a module."""
	from kentender_core.services import working_context as wc

	user = user or frappe.session.user
	mode, contexts = _authorized_context_rows(user)
	by_id = {c["context_id"]: c for c in contexts}

	requested = by_id.get((requested_context or "").strip() or None)
	if requested:
		_persist_context_pair(module, requested, user)
		selected = requested
	else:
		pe_selected = wc.get_working_pe(user)["selected"]
		pool = contexts
		if pe_selected:
			subset = [c for c in contexts if c["procuring_entity"]["id"] == pe_selected["id"]]
			if subset:
				pool = subset
		fy_state = wc.get_module_fy(
			module, user, offered=[c["financial_year"]["id"] for c in pool]
		)
		selected = None
		if fy_state["selected"]:
			matches = [
				c for c in pool if c["financial_year"]["id"] == fy_state["selected"]["id"]
			]
			if len(matches) == 1:
				selected = matches[0]
		if not selected and len(pool) == 1:
			selected = pool[0]

	return {
		"mode": mode,
		"contexts": contexts,
		"selected": selected,
		"selection_required": selected is None and mode != "none",
	}


def _persist_context_pair(module: str, context: dict[str, Any], user: str) -> None:
	"""Remember a picked context as global PE + module FY; persistence must
	never break a read, so a pair the working-context service will not accept
	is simply not remembered."""
	from kentender_core.services import working_context as wc

	try:
		wc.select_working_pe(context["procuring_entity"]["id"], user)
		wc.select_module_fy(
			module,
			context["financial_year"]["id"],
			user,
			offered=[context["financial_year"]["id"]],
		)
	except Exception:
		frappe.clear_last_message()


def select_working_context(module: str, context_id: str, user: str | None = None) -> dict[str, Any]:
	"""Record `context_id` as `user`'s remembered working context for
	`module` (e.g. "budget"), after confirming it's one of their authorized
	contexts. This only stores a preference — it is not a write-time
	eligibility check; see validate_context_for_command() for that."""
	user = user or frappe.session.user
	_mode, contexts = _authorized_context_rows(user)
	by_id = {c["context_id"]: c for c in contexts}
	selected = by_id.get((context_id or "").strip())
	if not selected:
		frappe.throw(
			"This PE/FY context is not available to you.",
			frappe.PermissionError,
			title="PEFY_CONTEXT_NOT_AUTHORIZED",
		)

	_persist_context_pair(module, selected, user)
	return selected
