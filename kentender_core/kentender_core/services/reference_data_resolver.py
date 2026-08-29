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


def _working_context_default_key(module: str) -> str:
	"""frappe.defaults.get_user_default() silently fails to round-trip a
	Title-Case/spaced key: is_a_user_permission_key() (frappe/defaults.py)
	treats any key where `key != frappe.scrub(key)` as a User-Permission-
	backed key and looks it up through that separate, unrelated mechanism
	instead of returning the plain stored value — confirmed live (a value
	set under "KT Budget Working Context" showed correctly in
	get_defaults() but came back "" from get_user_default() for that exact
	key). A pre-scrubbed snake_case key sidesteps the special-casing
	entirely."""
	return f"kt_{module.lower()}_working_context"


def resolve_working_context(
	module: str,
	user: str | None = None,
	*,
	requested_context: str | None = None,
) -> dict[str, Any]:
	"""Zero/one/many authorized PE/FY working contexts for `user`, scoped by
	their own permitted Procuring Entities — distinct from
	resolve_authorized_contexts() above, which is scoped to the global
	Reference Data Manager role and sees every Active context regardless of
	PE assignment. Administrator/System Manager get every non-Suspended
	context (permitted_procuring_entities() returns None for them), never a
	silently-empty "no baseline" result. The selected context is only a
	working-context preference, never an authorization grant — business
	actions stay gated by their own Role/capability checks, and a
	state-changing command still calls validate_context_for_command()
	(Active-only) at the point of that command.

	Resolving via an explicit requested_context also remembers it (same as
	select_working_context) — a deep link or a query-string context is a
	deliberate choice, not a one-off override, and without this the very
	next client-side route change (which carries no query string of its
	own — confirmed live: Budget's useRouteState-based go() drops it) would
	have nothing to fall back on and re-prompt for a selection it was
	effectively just given."""
	user = user or frappe.session.user
	mode, contexts = _authorized_context_rows(user)
	by_id = {c["context_id"]: c for c in contexts}

	requested_context = (requested_context or "").strip() or None
	selected = by_id.get(requested_context) if requested_context else None
	if selected:
		frappe.defaults.set_user_default(_working_context_default_key(module), selected["context_id"], user=user)

	if not selected:
		remembered_id = frappe.defaults.get_user_default(_working_context_default_key(module), user=user)
		if remembered_id:
			selected = by_id.get(remembered_id)

	if not selected and mode == "single":
		selected = contexts[0]

	return {
		"mode": mode,
		"contexts": contexts,
		"selected": selected,
		"selection_required": selected is None and mode != "none",
	}


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

	frappe.defaults.set_user_default(_working_context_default_key(module), selected["context_id"], user=user)
	return selected
