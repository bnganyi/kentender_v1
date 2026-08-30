"""Server-authoritative Procurement Planning PE/FY selection (PLN-CHG-016)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_planning.services.planning_roles import (
	ALL_PLANNING_ROLES,
)

READ_PLAN_ROLES = frozenset(ALL_PLANNING_ROLES)

# CTX-CHG-001 — persistence moved to kentender_core.working_context: the
# GLOBAL working PE plus this module's kt_planning_financial_year. The old
# Title-Case keys below never restored at all (frappe.defaults'
# is_a_user_permission_key silently reroutes any key != scrub(key)); their
# dead DefaultValue rows are deleted by the delete_planning_titlecase_defaults
# patch, with nothing to migrate.
PLANNING_MODULE = "planning"
SOURCE_SELECTED = "selected"
SOURCE_SAVED_DEFAULT = "saved_default"
SOURCE_LEGACY = "legacy"


def _authorised_entities(actor: str) -> list[dict[str, str]]:
	"""§6 / CTX-CHG-001 (closes DEBT-02): eligibility is a held Planning role
	plus native Procuring Entity User Permission rows — no scope-assignment
	store, no second permission layer."""
	from kentender_procurement.procurement_planning.services.authority import (
		permitted_pes,
	)

	holds_planning_role = bool(READ_PLAN_ROLES & set(frappe.get_roles(actor)))
	pes = sorted(permitted_pes(actor)) if holds_planning_role else []
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
	"""§10 — eligible Financial Years derive from configured FY/context
	records (`PE Fiscal Year Context` + `Financial Year`), never from a user
	assignment. The pre-v1.2 read of the ERPNext `Fiscal Year` doctype is gone
	(it was the CTX-FU-02 vocabulary split: Planning's model links
	`Financial Year`)."""
	from frappe.utils import getdate, nowdate

	today = getdate(nowdate())
	contexts = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"procuring_entity": pe, "context_status": "Active"},
		pluck="financial_year",
		limit_page_length=0,
	)
	if not contexts:
		return [], set()
	years = frappe.get_all(
		"Financial Year",
		filters={"name": ["in", contexts], "record_status": "Available"},
		fields=["name", "label", "start_date", "end_date"],
		order_by="start_date asc",
		limit_page_length=0,
	)
	open_fys = set(frappe.get_all(
		"Annual Plan",
		filters={"procuring_entity": pe},
		pluck="financial_year",
		limit_page_length=0,
	))
	options: list[dict[str, Any]] = []
	for row in years:
		start, end = getdate(row.start_date), getdate(row.end_date)
		is_current = start <= today <= end
		is_future = start > today
		is_past = end < today
		has_plan = row.name in open_fys
		if is_current or is_future or has_plan:
			label = cstr(row.label)
			if label and not label.upper().startswith("FY"):
				label = f"FY {label}"
			options.append(
				{
					"id": row.name,
					"label": label or row.name,
					"start_date": cstr(row.start_date),
					"end_date": cstr(row.end_date),
					"is_current": is_current,
					"is_future": is_future,
					"is_past": is_past,
					"has_open_plan": has_plan,
					"planning_open": bool(not is_past or has_plan),
				}
			)
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

	from kentender_core.services.working_context import get_working_pe

	source = "explicit" if explicit_pe else ""
	pe = explicit_pe
	if not pe:
		# The GLOBAL working PE applies only when it is inside Planning's own
		# narrowed scope; outside it, this module simply prompts (never an
		# error, never a trap — the rail switcher is the recovery path).
		try:
			working = get_working_pe(actor)["selected"]
		except frappe.PermissionError:
			working = None
		if working and working["id"] in allowed:
			pe, source = working["id"], "saved"
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
		from kentender_core.services.working_context import get_module_fy

		saved_fy_state = get_module_fy(
			PLANNING_MODULE, actor, offered=[row["id"] for row in years]
		)
		if saved_fy_state["selected"]:
			fy = saved_fy_state["selected"]["id"]
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
	from kentender_core.services.working_context import select_module_fy, select_working_pe

	actor = cstr(user or frappe.session.user).strip()
	context = resolve_planning_context(procuring_entity=procuring_entity, financial_year=financial_year, user=actor)
	try:
		select_working_pe(context["procuring_entity"], actor)
	except frappe.PermissionError:
		# Readable through a Planning scope row but outside the global PE
		# offer (e.g. a non-Active entity): keep the FY memory, skip the PE.
		frappe.clear_last_message()
	if context["financial_year"]:
		select_module_fy(
			PLANNING_MODULE, context["financial_year"], actor,
			offered=[context["financial_year"]],
		)
	return context
