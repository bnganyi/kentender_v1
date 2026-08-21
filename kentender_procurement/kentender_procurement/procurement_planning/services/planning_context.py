"""Server-authoritative Procurement Planning PE/FY selection (PLN-CHG-016)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_core.services.org_scope_access import user_scope_rows
from kentender_procurement.procurement_planning.services.planning_permissions import READ_PLAN_ROLES

PE_DEFAULT = "KT Planning Procuring Entity"
FY_DEFAULT = "KT Planning Financial Year"
SOURCE_SELECTED = "selected"
SOURCE_SAVED_DEFAULT = "saved_default"
SOURCE_LEGACY = "legacy"


def _authorised_entities(actor: str) -> list[dict[str, str]]:
	pes = sorted({
		cstr(row.get("procuring_entity")).strip()
		for row in user_scope_rows(actor)
		if cstr(row.get("role")).strip() in READ_PLAN_ROLES
		and cstr(row.get("procuring_entity")).strip()
	})
	if not pes:
		return []
	meta = frappe.get_meta("Procuring Entity")
	label_field = "legal_name" if meta.has_field("legal_name") else "entity_name"
	rows = frappe.get_all(
		"Procuring Entity",
		filters={"name": ["in", pes], "status": "Active"},
		fields=["name", label_field],
		limit_page_length=0,
	)
	labels = {row.name: cstr(row.get(label_field) or row.name) for row in rows}
	return [
		{"id": pe, "code": pe, "name": labels[pe], "label": labels[pe]}
		for pe in pes if pe in labels
	]


def _selectable_years(pe: str) -> tuple[list[dict[str, Any]], set[str]]:
	periods = enabled_fiscal_years(include_past=True)
	open_fys = set(frappe.get_all(
		"Procurement Plan",
		filters={"procuring_entity": pe, "lifecycle_state": "Open"},
		pluck="financial_year",
		limit_page_length=0,
	))
	options: list[dict[str, Any]] = []
	for row in periods:
		has_plan = row["id"] in open_fys
		if row["is_current"] or row["is_future"] or has_plan:
			options.append({**row, "has_open_plan": has_plan, "planning_open": bool(not row["is_past"] or has_plan)})
	return options, open_fys


def _default_year(options: list[dict[str, Any]], open_fys: set[str]) -> str:
	current = next((row for row in options if row["is_current"]), None)
	if current and current["id"] in open_fys:
		return current["id"]
	future = [row for row in options if row["is_future"] and row["id"] in open_fys]
	if future:
		return min(future, key=lambda row: getdate(row["start_date"]))["id"]
	past = [row for row in options if row["is_past"] and row["id"] in open_fys]
	if past:
		return max(past, key=lambda row: getdate(row["end_date"]))["id"]
	if current:
		return current["id"]
	return ""


def resolve_planning_context(
	*, procuring_entity: str | None = None, financial_year: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user).strip()
	if not actor or actor == "Guest":
		frappe.throw("Login required.", frappe.PermissionError, title="PLN_LOGIN_REQUIRED")
	entities = _authorised_entities(actor)
	if not entities:
		return {"procuring_entity": None, "financial_year": "", "procuring_entities": [], "financial_years": [], "selection_source": "none", "resolved_financial_year_source": SOURCE_LEGACY, "selection_required": False, "no_scope": True}
	allowed = {row["id"] for row in entities}
	explicit_pe = cstr(procuring_entity).strip()
	explicit_fy = cstr(financial_year).strip()
	if explicit_pe and explicit_pe not in allowed:
		frappe.throw("Selected Procuring Entity is not in your Planning scope.", frappe.PermissionError, title="PLN_SCOPE_DENIED")

	source = "explicit" if explicit_pe else ""
	pe = explicit_pe
	if not pe:
		saved_pe = cstr(frappe.defaults.get_user_default(PE_DEFAULT, user=actor)).strip()
		if saved_pe in allowed:
			pe, source = saved_pe, "saved"
		elif len(entities) == 1:
			pe, source = entities[0]["id"], "sole_procuring_entity"
	if not pe:
		return {"procuring_entity": None, "financial_year": "", "procuring_entities": entities, "financial_years": [], "selection_source": "selection_required", "resolved_financial_year_source": SOURCE_LEGACY, "selection_required": True, "no_scope": False}

	years, open_fys = _selectable_years(pe)
	by_id = {row["id"]: row for row in years}
	if explicit_fy:
		if explicit_fy not in by_id:
			frappe.throw("Selected financial year is not available for Planning.", title="PLN_FY_NOT_SELECTABLE")
		fy = explicit_fy
		source = "explicit"
	else:
		saved_pe = cstr(frappe.defaults.get_user_default(PE_DEFAULT, user=actor)).strip()
		saved_fy = cstr(frappe.defaults.get_user_default(FY_DEFAULT, user=actor)).strip()
		if saved_fy in by_id and (not saved_pe or saved_pe == pe):
			fy = saved_fy
			source = "saved"
		else:
			fy = _default_year(years, open_fys)
			if fy:
				source = "default"
	return {
		"procuring_entity": pe,
		"financial_year": fy,
		"procuring_entities": entities,
		"financial_years": [{"id": row["id"], "label": row["label"], "start_date": row["start_date"], "end_date": row["end_date"], "is_current": row["is_current"], "is_future": row["is_future"], "is_past": row["is_past"], "planning_open": row["planning_open"], "has_open_plan": row["has_open_plan"]} for row in years],
		"selection_source": source or "selection_required",
		"resolved_financial_year_source": (
			SOURCE_SELECTED if explicit_fy else SOURCE_SAVED_DEFAULT if source == "saved" else SOURCE_LEGACY
		),
		"selection_required": not bool(fy),
		"no_scope": False,
	}


def select_planning_context(*, procuring_entity: str, financial_year: str, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user).strip()
	context = resolve_planning_context(procuring_entity=procuring_entity, financial_year=financial_year, user=actor)
	frappe.defaults.set_user_default(PE_DEFAULT, context["procuring_entity"], user=actor)
	frappe.defaults.set_user_default(FY_DEFAULT, context["financial_year"], user=actor)
	return context
