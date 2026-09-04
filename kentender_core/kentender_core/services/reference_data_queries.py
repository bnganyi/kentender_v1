# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.4 §10 — read-side projections (List*/Get* contracts).
Reference Data Manager (and System Manager/Administrator) see every PE, FY
and Context; everyone else has no access to this workspace at all — one
global Role is the whole visibility and action decision, per
reference_data_permissions.has_reference_data_read_access.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services import reference_data_permissions as perm


def _authorized_pes(user: str) -> set[str] | None:
	"""None = unrestricted; empty set = no access."""
	if perm.has_reference_data_read_access(user):
		return None
	return set()


def _allowed(user: str) -> bool:
	return perm.has_reference_data_manager_role(user)


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


# --- Organisation Unit / Funding Source picklists -------------------------------
# Supplements, not named in CFG-CHG-002 §10 — small catalogue lookups other
# modules' editors need (e.g. Budget's Budget Line editor, BUD-CHG-001 v1.2
# §12.2 "Owner-scope choices come from Configuration & Governance for the
# exact PE. Funding-source choices come from the configured catalogue.").
# Unscoped read like list_pe_types above — a label-only picklist, not
# sensitive data, and no owning-module-specific role should gate a shared
# catalogue read.


def list_organisation_units(procuring_entity: str | None = None) -> dict[str, Any]:
	"""`procuring_entity` is an optional narrowing filter, not a requirement:
	a caller that still tracks a PE-scoped working context may pass one, but
	the default (omitted) lists every Active Organisation Unit on the site.
	Organisation Unit's own `procuring_entity` field is documented as
	deprecated (AUTH-ADR-001 v1.6 §1.1: "one site is one Procuring Entity,
	so every unit belongs to the site PE by construction... dropped in the
	removal phase") and is hidden/read-only — the current
	`organisation_structure.add_organisation_unit` creation path never sets
	it at all. Requiring a non-empty procuring_entity to return anything was
	therefore doubly broken: Budget's own listOrganisationUnits() never
	passed one (returning {"rows": []} unconditionally — the Owner scope
	picklist on the Budget Lines tab was silently empty for every user,
	every row), and even a caller that resolved and passed "the" PE would
	still match nothing, since units aren't stamped with it any more."""
	pe = (procuring_entity or "").strip()
	filters: dict[str, Any] = {"status": "Active"}
	if pe:
		filters["procuring_entity"] = pe
	rows = frappe.get_all(
		"Organisation Unit",
		filters=filters,
		fields=["name", "unit_name"],
		order_by="unit_name asc",
	)
	return {"rows": [{"id": r.name, "label": r.unit_name} for r in rows]}


def list_funding_sources() -> dict[str, Any]:
	rows = frappe.get_all(
		"Funding Source",
		filters={"record_status": "Available"},
		fields=["name", "label"],
		order_by="label asc",
	)
	return {"rows": [{"id": r.name, "label": r.label} for r in rows]}


# --- Procuring Entity ------------------------------------------------------------


def _pe_allowed_actions(pe, user: str) -> list[str]:
	if not _allowed(user):
		return []
	actions: list[str] = []
	version_state = None
	if pe.current_version_id:
		version_state = frappe.db.get_value("Procuring Entity Version", pe.current_version_id, "version_state")
	if pe.status == "Draft" and version_state == "Draft":
		actions.append("Edit draft")
		actions.append("Activate procuring entity")
	elif pe.status == "Active" and version_state == "Draft":
		actions.append("Edit draft")
		actions.append("Apply amendment")
	if pe.status == "Active":
		actions.append("Propose amendment")
		actions.append("Suspend")
	if pe.status == "Suspended":
		actions.append("Reinstate")
	if pe.status in ("Active", "Suspended"):
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
		"effective_from": pe.effective_from,
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
	if not _allowed(user):
		return []
	actions: list[str] = []
	if fy.record_status == "Draft":
		actions.append("Make available")
	if fy.record_status == "Available":
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
	if not _allowed(user):
		return []
	actions: list[str] = []
	if ctx.context_status == "Active":
		actions.append("Suspend")
	if ctx.context_status == "Suspended":
		actions.append("Reinstate")
	if ctx.context_status in ("Active", "Suspended", "Scheduled"):
		actions.append("Close")
	if ctx.context_status == "Closed":
		actions.append("Reopen")
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
