# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.2 §4.3/§4.4/§9.1/§9.2/§12.2 — Budget Line drafting and the
eligible-line read contracts. Owns `save_budget_lines_draft`,
`list_eligible_budget_lines`, and the Budget Lines tab read models for the
version editor (BUD-UI-02) and the Active workspace (BUD-UI-03).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_budget.services.budget_authorization import CAP_EDIT, require_budget_version_capability, require_budget_version_read_scope
from kentender_budget.services.budget_contracts import (
	_active_version,
	_line_position,
	_resolve_budget_version,
	_version_totals,
	format_kes_full,
	resolve_scoped_entity,
)
from kentender_budget.services.budget_permissions import assert_org_unit_in_scope
from kentender_budget.services.budget_reference import allocate_budget_line_reference, allocate_budget_line_version_reference


def _lines_previously_in_active(budget_version) -> dict[str, Any]:
	"""Budget Line names present in this version's `based_on_budget_version`,
	keyed by budget_line — the "previously Active line" identity-lock set
	(§12.2: "Removing or changing identity fields on a previously Active line
	is rejected")."""
	if not budget_version.based_on_budget_version:
		return {}
	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": budget_version.based_on_budget_version},
		fields=["budget_line", "title", "owner_org_unit", "funding_source"],
	)
	return {r.budget_line: r for r in rows}


def save_budget_lines_draft(payload: dict | str | None = None) -> dict[str, Any]:
	"""§9.2 `save_budget_lines_draft` — create, update or remove Draft lines
	as one validated change set."""
	if isinstance(payload, str):
		payload = frappe.parse_json(payload)
	payload = payload or {}

	version = _resolve_budget_version(payload.get("budget_version") or "")
	require_budget_version_capability(frappe.session.user, CAP_EDIT, version)
	if version.status != "Draft":
		frappe.throw(_("Only a Draft version can be edited"), frappe.ValidationError, title="BUDGET_INVALID_STATE")

	budget = frappe.get_doc("Budget", version.budget)
	locked = _lines_previously_in_active(version)
	rows = payload.get("lines") or []
	errors: dict[str, str] = {}

	existing_versions = {
		lv.budget_line: lv
		for lv in frappe.get_all(
			"Budget Line Version", filters={"budget_version": version.name}, fields=["name", "budget_line"]
		)
	}
	seen: set[str] = set()

	for i, row in enumerate(rows):
		budget_line_key = (row.get("budget_line") or "").strip()
		remove = bool(row.get("remove"))

		if remove:
			if budget_line_key in locked:
				errors[f"lines.{i}"] = _("A previously Active line cannot be removed")
				continue
			if budget_line_key and budget_line_key in existing_versions:
				frappe.delete_doc("Budget Line Version", existing_versions[budget_line_key].name, ignore_permissions=True)
			continue

		title = (row.get("title") or "").strip()
		owner_org_unit = (row.get("owner_org_unit") or "").strip()
		funding_source = (row.get("funding_source") or "").strip()
		approved_amount = flt(row.get("approved_amount"))

		if not title:
			errors[f"lines.{i}.title"] = _("Line title is required")
		if not funding_source:
			errors[f"lines.{i}.funding_source"] = _("Funding source is required")
		if approved_amount <= 0:
			errors[f"lines.{i}.approved_amount"] = _("Approved amount must be positive")
		if owner_org_unit:
			try:
				assert_org_unit_in_scope(budget.procuring_entity, owner_org_unit, require_write=False)
			except frappe.PermissionError:
				errors[f"lines.{i}.owner_org_unit"] = _("Organisation unit is outside this Procuring Entity")

		if budget_line_key and budget_line_key in locked:
			prior = locked[budget_line_key]
			# BUD-BR-019 — identity fields are immutable once previously Active;
			# only approved_amount may change. Silently hold the prior identity
			# rather than accept a client-supplied change.
			title = prior.title
			owner_org_unit = prior.owner_org_unit
			funding_source = prior.funding_source

		seen.add(budget_line_key)
		if errors:
			continue

		if budget_line_key and budget_line_key in existing_versions:
			line_version = frappe.get_doc("Budget Line Version", existing_versions[budget_line_key].name)
			line_version.title = title
			line_version.owner_org_unit = owner_org_unit or None
			line_version.funding_source = funding_source
			line_version.approved_amount = approved_amount
			line_version.save(ignore_permissions=True)
		else:
			if not budget_line_key:
				line_ref = allocate_budget_line_reference(budget.procuring_entity)
				budget_line = frappe.get_doc(
					{"doctype": "Budget Line", "generated_reference": line_ref, "budget": budget.name}
				)
				budget_line.insert(ignore_permissions=True)
				budget_line_key = budget_line.name
			else:
				budget_line = frappe.get_doc("Budget Line", budget_line_key)
				if budget_line.budget != budget.name:
					errors[f"lines.{i}"] = _("Budget Line does not belong to this Budget")
					continue

			frappe.get_doc(
				{
					"doctype": "Budget Line Version",
					"generated_reference": allocate_budget_line_version_reference(budget_line.generated_reference, version.version_number),
					"budget_version": version.name,
					"budget_line": budget_line.name,
					"title": title,
					"owner_org_unit": owner_org_unit or None,
					"funding_source": funding_source,
					"approved_amount": approved_amount,
					"currency": budget.currency,
				}
			).insert(ignore_permissions=True)

	if errors:
		return {"ok": False, "errors": errors}

	from kentender_budget.services.budget_audit_contracts import EVENT_DRAFT_LINES_SAVED, safe_record_event

	safe_record_event(
		budget=budget.name,
		budget_version=version.name,
		event_type=EVENT_DRAFT_LINES_SAVED,
		actor=frappe.session.user,
		correlation_id=frappe.generate_hash(length=12),
		calling_module="Budget & Funding",
	)

	totals = _version_totals(version.name)
	return {
		"ok": True,
		"totals": {
			"authorised_total": flt(version.authorised_total),
			"line_total": totals["approved"],
			"difference": flt(version.authorised_total) - totals["approved"],
		},
	}


def get_budget_version_lines_editor(budget_version: str) -> dict[str, Any]:
	"""BUD-UI-02 Budget Lines tab — BUD-DES-03 (baseline) / BUD-DES-15 (successor)."""
	from kentender_budget.services.budget_contracts import _org_unit_label

	version = _resolve_budget_version(budget_version)
	require_budget_version_read_scope(version)
	locked = _lines_previously_in_active(version)

	rows = frappe.get_all(
		"Budget Line Version",
		filters={"budget_version": version.name},
		fields=["name", "budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	codes = (
		{
			r.name: r.generated_reference
			for r in frappe.get_all(
				"Budget Line", filters={"name": ["in", [row.budget_line for row in rows]]}, fields=["name", "generated_reference"]
			)
		}
		if rows
		else {}
	)
	line_total = 0.0
	out = []
	for r in rows:
		line_total += flt(r.approved_amount)
		is_locked = r.budget_line in locked
		row_dto: dict[str, Any] = {
			"budget_line": r.budget_line,
			"budget_line_code": codes.get(r.budget_line, ""),
			"title": r.title,
			"owner_org_unit": r.owner_org_unit,
			"owner_org_unit_label": _org_unit_label(r.owner_org_unit),
			"funding_source": r.funding_source,
			"approved_amount": flt(r.approved_amount),
			"identity_locked": is_locked,
			"can_remove": not is_locked,
		}
		if version.based_on_budget_version:
			active_amount = 0.0
			if is_locked:
				active_amount = flt(
					frappe.db.get_value(
						"Budget Line Version",
						{"budget_version": version.based_on_budget_version, "budget_line": r.budget_line},
						"approved_amount",
					)
				)
			row_dto["active_amount"] = active_amount
			row_dto["change"] = flt(r.approved_amount) - active_amount
		out.append(row_dto)

	return {
		"rows": out,
		"is_successor": bool(version.based_on_budget_version),
		"totals": {
			"authorised_total": flt(version.authorised_total),
			"line_total": line_total,
			"difference": flt(version.authorised_total) - line_total,
		},
	}


def get_budget_lines_active(budget: str) -> dict[str, Any]:
	"""BUD-UI-03 Budget Lines tab — BUD-DES-05: Active line positions + Total row."""
	from kentender_budget.services.budget_contracts import _resolve_budget

	doc = _resolve_budget(budget)
	resolve_scoped_entity(doc.procuring_entity)
	version = _active_version(doc.name)
	if not version:
		frappe.throw(_("No Active Budget Version"), frappe.DoesNotExistError, title="BUDGET_CONTEXT_NOT_FOUND")
	require_budget_version_read_scope(version)

	totals = _version_totals(version.name)
	currency = doc.currency or "KES"
	rows = []
	for line in totals["lines"]:
		pos = line["positions"]
		rows.append(
			{
				"budget_line": line["budget_line"],
				"code": line.get("code", ""),
				"title": line["title"],
				"owner_org_unit": line.get("owner_org_unit_label", ""),
				"funding_source": line.get("funding_source_label", ""),
				"approved": pos["approved"],
				"reserved": pos["reserved"],
				"committed": pos["committed"],
				"available": pos["available"],
				"approved_display": format_kes_full(pos["approved"], currency=currency),
				"reserved_display": format_kes_full(pos["reserved"], currency=currency),
				"committed_display": format_kes_full(pos["committed"], currency=currency),
				"available_display": format_kes_full(pos["available"], currency=currency),
			}
		)
	return {
		"rows": rows,
		"total": {
			"approved": totals["approved"],
			"reserved": totals["reserved"],
			"committed": totals["committed"],
			"available": totals["available"],
		},
	}


def list_eligible_budget_lines(
	procuring_entity: str,
	financial_year: str,
	source_org_unit: str | None = None,
	funding_source: str | None = None,
	search: str | None = None,
) -> list[dict[str, Any]]:
	"""§9.1 `list_eligible_budget_lines` — Active eligible lines only
	(BUD-BR-007: PE-wide or matching the source Need's organisation unit),
	no Draft lines."""
	budget_name = frappe.db.get_value("Budget", {"procuring_entity": procuring_entity, "financial_year": financial_year}, "name")
	if not budget_name:
		return []
	version = _active_version(budget_name)
	if not version:
		return []
	require_budget_version_read_scope(version)

	filters: dict[str, Any] = {"budget_version": version.name}
	if funding_source:
		filters["funding_source"] = funding_source
	if search:
		filters["title"] = ["like", f"%{search}%"]

	rows = frappe.get_all(
		"Budget Line Version",
		filters=filters,
		fields=["budget_line", "title", "owner_org_unit", "funding_source", "approved_amount"],
		order_by="title asc",
	)
	out = []
	for r in rows:
		if r.owner_org_unit and source_org_unit and r.owner_org_unit != source_org_unit:
			continue
		pos = _line_position(r.budget_line, r)
		out.append(
			{
				"id": r.budget_line,
				"title": r.title,
				"owner_org_unit": r.owner_org_unit,
				"funding_source": r.funding_source,
				"approved": pos["approved"],
				"reserved": pos["reserved"],
				"committed": pos["committed"],
				"available": pos["available"],
			}
		)
	return out
