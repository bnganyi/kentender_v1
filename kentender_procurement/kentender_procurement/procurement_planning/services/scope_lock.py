# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.4.5 / §5.4.6 — the stable Plan Item's procurement-scope
lock and correction hold (plan D9).

The lock is evidence, not a flag a user sets: once any Requisition for the
stable item is authorised, `Plan Item.scope_locked_since` is written (Phase
2g writes it in the same transaction as the drawdown) and never cleared. A
later APP update may not add sources to that item, increase its scope or
re-form it under a new identity — a later requirement becomes a separate
Plan Item. The hold is derived from unresolved correction requests.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_planning.errors import fail

SCOPE_FIELDS = ("title", "description", "aggregation_indicator", "aggregation_reason", "lotting_indicator", "lot_count", "reservation_category", "procurement_method")


def status(plan_item_id: str) -> dict[str, Any]:
	row = frappe.db.get_value(
		"Plan Item", cstr(plan_item_id),
		["scope_locked_since", "first_authorised_requisition", "authorisation_hold", "open_correction_requests"], as_dict=True,
	)
	if not row:
		return {"locked": False, "since": "", "first_requisition": "", "held": False, "open_requests": 0}
	return {
		"locked": bool(row.scope_locked_since),
		"since": cstr(row.scope_locked_since),
		"first_requisition": cstr(row.first_authorised_requisition),
		"held": bool(row.authorisation_hold),
		"open_requests": int(row.open_correction_requests or 0),
	}


def is_locked(plan_item_id: str) -> bool:
	return status(plan_item_id)["locked"]


def require_unlocked(plan_item_id: str, *, action: str) -> None:
	state = status(plan_item_id)
	if state["locked"]:
		fail("PLN_ITEM_SCOPE_LOCKED", detail={"plan_item_id": plan_item_id, "action": action, "scope_locked_since": state["since"], "first_authorised_requisition": state["first_requisition"]})


def scope_changes(values: dict[str, Any], item) -> list[str]:
	"""The offered fields that would change the package's scope on a locked
	item (title/description/structure/designation/method); schedule,
	estimate and Strategy fields stay editable."""
	changed = []
	for field in SCOPE_FIELDS:
		if field in values and cstr(values[field]).strip() != cstr(item.get(field)).strip():
			changed.append(field)
	return changed


def locked_items_for_sources(fiscal_year: str, dpp_entries: list[str]) -> list[str]:
	"""Stable items that already hold one of these sources (through the source
	lineage) and are scope-locked — the sources may not be re-formed."""
	from kentender_procurement.procurement_planning.services import plan_read

	lineage: set[str] = set()
	for entry in dpp_entries:
		lineage.update(plan_read.same_source_lineage(entry))
	if not lineage:
		return []
	ids = frappe.get_all("Plan Source Allocation", filters={"dpp_entry": ("in", list(lineage))}, pluck="plan_item_id", distinct=True)
	if not ids:
		return []
	return frappe.get_all("Plan Item", filters={"name": ("in", ids), "scope_locked_since": ("is", "set")}, pluck="name")
