# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 §10 — read-side projections (List*/Get* contracts). Scope for
list/detail reads mirrors the resolver: System Manager/Administrator see
everything, everyone else sees only PEs they hold an active reference-data
assignment for — the same authorization_policy engine, not a second read-only
permission system.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services import reference_data_permissions as perm
from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, resolve_effective_access


def _is_admin(user: str) -> bool:
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


def _authorized_pes(user: str) -> set[str] | None:
	"""None = unrestricted."""
	if _is_admin(user):
		return None
	return {row["procuring_entity_id"] for row in resolve_effective_access(user)}


def _allowed(user: str, capability: str, resource: ResourceContext) -> bool:
	return evaluate_capability(user, capability, resource).allowed


# --- PE Type -----------------------------------------------------------------------


def list_pe_types() -> dict[str, Any]:
	"""Supplement — feeds the New/Amend Procuring Entity form's PE type selector;
	not separately named in §10, which only requires PE type to be "governed"."""
	rows = frappe.get_all(
		"PE Type",
		filters={"status": "Active"},
		fields=["name", "type_code", "label"],
		order_by="label asc",
	)
	return {"rows": [{"type_code": r.type_code, "label": r.label} for r in rows]}


# --- Procuring Entity ------------------------------------------------------------


def _pe_allowed_actions(pe, user: str) -> list[str]:
	ctx = perm.pe_resource_context(pe.name, prior_actions=perm.prior_actions_for_pe(pe.name))
	actions: list[str] = []
	if pe.status == "Draft" and _allowed(user, perm.PE_CREATE_DRAFT, ctx):
		actions.append("Submit")
	elif pe.status == "Active" and pe.current_version_id:
		version_state = frappe.db.get_value("Procuring Entity Version", pe.current_version_id, "version_state")
		if version_state == "Draft" and _allowed(user, perm.PE_PROPOSE_AMENDMENT, ctx):
			actions.append("Submit amendment")
		if version_state == "Under Review" and _allowed(user, perm.PE_APPROVE_ACTIVATE, ctx):
			actions.append("Approve and activate")
	if pe.status == "Active":
		if _allowed(user, perm.PE_PROPOSE_AMENDMENT, ctx):
			actions.append("Propose amendment")
		if _allowed(user, perm.PE_SUSPEND, ctx):
			actions.append("Suspend")
	if pe.status == "Suspended" and _allowed(user, perm.PE_REINSTATE, ctx):
		actions.append("Reinstate")
	if pe.status in ("Active", "Suspended") and _allowed(user, perm.PE_RETIRE, ctx):
		actions.append("Retire")
	return actions


def list_procuring_entities(
	user: str | None = None, *, status: str | None = None, pe_type: str | None = None, search: str | None = None
) -> dict[str, Any]:
	user = user or frappe.session.user
	pes = _authorized_pes(user)
	filters: dict[str, Any] = {}
	if status:
		filters["status"] = status
	if pes is not None:
		filters["name"] = ["in", sorted(pes)] if pes else ["in", []]

	rows = frappe.get_all(
		"Procuring Entity",
		filters=filters,
		fields=["name", "entity_code", "legal_name", "status", "effective_from", "current_version_id"],
		order_by="entity_code asc",
	)
	out = []
	for r in rows:
		type_code = None
		if r.current_version_id:
			type_code = frappe.db.get_value("Procuring Entity Version", r.current_version_id, "pe_type_code")
		if pe_type and type_code != pe_type:
			continue
		if search and search.lower() not in f"{r.entity_code} {r.legal_name}".lower():
			continue
		out.append(
			{
				"pe_id": r.name,
				"code": r.entity_code,
				"legal_name": r.legal_name,
				"pe_type": type_code,
				"status": r.status,
				"effective_from": str(r.effective_from) if r.effective_from else None,
			}
		)
	return {"rows": out, "count": len(out)}


def get_procuring_entity(pe_id: str, user: str | None = None) -> dict[str, Any]:
	user = user or frappe.session.user
	pes = _authorized_pes(user)
	if pes is not None and pe_id not in pes:
		frappe.throw("Not permitted for this Procuring Entity", frappe.PermissionError)

	pe = frappe.get_doc("Procuring Entity", pe_id)
	version = frappe.get_doc("Procuring Entity Version", pe.current_version_id) if pe.current_version_id else None
	history = frappe.get_all(
		"Audit Event",
		filters={"document_type": "Procuring Entity", "document_name": pe_id},
		fields=["action", "performed_by", "timestamp", "metadata"],
		order_by="timestamp asc",
	)
	return {
		"pe_id": pe.name,
		"code": pe.entity_code,
		"status": pe.status,
		"version": (
			{
				"legal_name": version.legal_name,
				"display_name": version.display_name,
				"pe_type_code": version.pe_type_code,
				"timezone": version.timezone,
				"version_state": version.version_state,
				"version_no": version.version_no,
			}
			if version
			else None
		),
		"history": [dict(h) for h in history],
		"available_actions": _pe_allowed_actions(pe, user),
	}


# --- Financial Year ----------------------------------------------------------------


def _calendar_phase(start_date, end_date) -> str:
	today = now_datetime().date()
	if today < start_date:
		return "Upcoming"
	if today > end_date:
		return "Past"
	return "Current"


def _fy_allowed_actions(fy, user: str) -> list[str]:
	actions: list[str] = []
	if fy.record_status == "Draft" and perm._has_any_active_capability(user, perm.FY_CREATE_DRAFT):
		actions.append("Submit")
	if fy.record_status == "Awaiting Approval" and perm._has_any_active_capability(user, perm.FY_APPROVE_AVAILABLE):
		actions.append("Approve")
	if fy.record_status == "Available" and perm._has_any_active_capability(user, perm.FY_RETIRE):
		actions.append("Retire")
	return actions


def list_financial_years(user: str | None = None, *, record_status: str | None = None) -> dict[str, Any]:
	user = user or frappe.session.user
	filters: dict[str, Any] = {}
	if record_status:
		filters["record_status"] = record_status
	rows = frappe.get_all(
		"Financial Year",
		filters=filters,
		fields=["name", "label", "start_date", "end_date", "record_status"],
		order_by="start_year desc",
	)
	out = []
	for r in rows:
		context_count = frappe.db.count("PE Fiscal Year Context", {"financial_year": r.name})
		out.append(
			{
				"financial_year_id": r.name,
				"label": r.label,
				"start_date": str(r.start_date),
				"end_date": str(r.end_date),
				"calendar_phase": _calendar_phase(r.start_date, r.end_date),
				"record_status": r.record_status,
				"context_count": context_count,
			}
		)
	return {"rows": out, "count": len(out)}


def get_financial_year(financial_year_id: str, user: str | None = None) -> dict[str, Any]:
	user = user or frappe.session.user
	fy = frappe.get_doc("Financial Year", financial_year_id)
	contexts = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"financial_year": financial_year_id},
		fields=["name", "procuring_entity", "context_status"],
	)
	return {
		"financial_year_id": fy.name,
		"label": fy.label,
		"start_date": str(fy.start_date),
		"end_date": str(fy.end_date),
		"timezone": fy.timezone,
		"calendar_phase": _calendar_phase(fy.start_date, fy.end_date),
		"record_status": fy.record_status,
		"contexts": [
			{
				"context_id": c.name,
				"procuring_entity": frappe.db.get_value("Procuring Entity", c.procuring_entity, "legal_name"),
				"status": c.context_status,
			}
			for c in contexts
		],
		"available_actions": _fy_allowed_actions(fy, user),
	}


# --- PE Fiscal Year Context ---------------------------------------------------------


def _context_readiness(ctx) -> str:
	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	return "Ready" if pe_status == "Active" and fy_status == "Available" else "Configuration required"


def _context_core_readiness_checks(ctx) -> list[dict]:
	"""§12.6/§12.11's four-row "Core readiness" breakdown — all within this module's
	own scope (PE and FY are both CFG-CHG-002 doctypes), unlike the separate "Module
	readiness" card (Strategy/Budget/Needs/Planning), which is a genuinely cross-module
	concern this module doesn't own (see the tracker's open items)."""
	pe_status, pe_version_id = frappe.db.get_value(
		"Procuring Entity", ctx.procuring_entity, ["status", "current_version_id"]
	)
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	pe_type_code, timezone = (None, None)
	if pe_version_id:
		pe_type_code, timezone = frappe.db.get_value(
			"Procuring Entity Version", pe_version_id, ["pe_type_code", "timezone"]
		)
	return [
		{"label": "Procuring Entity active", "status": "Ready" if pe_status == "Active" else "Configuration required"},
		{"label": "Financial Year available", "status": "Ready" if fy_status == "Available" else "Configuration required"},
		{"label": "PE type configured", "status": "Ready" if pe_type_code else "Configuration required"},
		{"label": "Timezone configured", "status": "Ready" if timezone else "Configuration required"},
	]


def _context_allowed_actions(ctx, user: str) -> list[str]:
	rctx = perm.context_resource_context(ctx.name, ctx.procuring_entity, ctx.financial_year, prior_actions=perm.prior_actions_for_context(ctx.name))
	actions: list[str] = []
	if ctx.context_status == "Draft" and _allowed(user, perm.CTX_CREATE_DRAFT, rctx):
		actions.append("Submit for review")
	elif ctx.context_status == "Under Review" and _allowed(user, perm.CTX_RECOMMEND, rctx):
		actions.append("Recommend")
	elif ctx.context_status == "Awaiting Approval" and _allowed(user, perm.CTX_APPROVE, rctx):
		actions.append("Approve")
	if ctx.context_status == "Active":
		if _allowed(user, perm.CTX_APPROVE, rctx):
			actions.append("Suspend")
			actions.append("Close")
	if ctx.context_status == "Suspended" and _allowed(user, perm.CTX_APPROVE, rctx):
		actions.append("Reinstate")
		actions.append("Close")
	if ctx.context_status == "Closed" and _allowed(user, perm.CTX_CREATE_DRAFT, rctx):
		actions.append("Propose exceptional reopen")
	return actions


def list_pe_fy_contexts(
	user: str | None = None,
	*,
	procuring_entity: str | None = None,
	financial_year: str | None = None,
	status: str | None = None,
	search: str | None = None,
) -> dict[str, Any]:
	user = user or frappe.session.user
	pes = _authorized_pes(user)
	filters: dict[str, Any] = {}
	if procuring_entity:
		filters["procuring_entity"] = procuring_entity
	if financial_year:
		filters["financial_year"] = financial_year
	if status:
		filters["context_status"] = status
	if pes is not None:
		filters["procuring_entity"] = ["in", sorted(pes)] if pes else ["in", []]

	rows = frappe.get_all(
		"PE Fiscal Year Context",
		filters=filters,
		fields=["name", "procuring_entity", "financial_year", "context_status", "active_from", "active_to"],
		order_by="modified desc",
	)
	out = []
	for r in rows:
		if search and search.lower() not in f"{r.name} {r.procuring_entity}".lower():
			continue
		out.append(
			{
				"context_id": r.name,
				"procuring_entity": frappe.db.get_value("Procuring Entity", r.procuring_entity, "legal_name"),
				"financial_year": frappe.db.get_value("Financial Year", r.financial_year, "label"),
				"active_from": str(r.active_from),
				"active_to": str(r.active_to),
				"status": r.context_status,
				"readiness": _context_readiness(r),
			}
		)
	return {"rows": out, "count": len(out)}


def get_pe_fy_context(context_id: str, user: str | None = None) -> dict[str, Any]:
	user = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_id)
	pes = _authorized_pes(user)
	if pes is not None and ctx.procuring_entity not in pes:
		frappe.throw("Not permitted for this PE/FY context", frappe.PermissionError)

	history = frappe.get_all(
		"Audit Event",
		filters={"document_type": "PE Fiscal Year Context", "document_name": context_id},
		fields=["action", "performed_by", "timestamp"],
		order_by="timestamp asc",
	)
	return {
		"context_id": ctx.name,
		"procuring_entity": {
			"id": ctx.procuring_entity,
			"name": frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "legal_name"),
		},
		"financial_year": {
			"id": ctx.financial_year,
			"label": frappe.db.get_value("Financial Year", ctx.financial_year, "label"),
		},
		"active_from": str(ctx.active_from),
		"active_to": str(ctx.active_to),
		"status": ctx.context_status,
		"readiness": _context_readiness(ctx),
		"core_readiness": _context_core_readiness_checks(ctx),
		"history": [dict(h) for h in history],
		"available_actions": _context_allowed_actions(ctx, user),
		"expected_version": str(ctx.modified),
	}
