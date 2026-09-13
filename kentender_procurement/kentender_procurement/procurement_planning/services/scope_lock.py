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
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope

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


def guard(plan_item_id: str):
	"""§4.10 / PLN-RI-029's "same stable-item concurrency guard" — row-locks
	the `Plan Item` root for the rest of the caller's transaction, so a
	drawdown authorising against this item and a correction request being
	recorded/disposed of against it cannot interleave and bypass each
	other's effect. Callers hold the returned doc and pass it to `lock()`
	and/or `recompute_hold()` below rather than re-resolving by name."""
	return envelope.locked("Plan Item", cstr(plan_item_id))


def lock(root, *, requisition_reference: str) -> bool:
	"""Plan D9/§5.4.6 — the first Requisition drawdown ever authorised
	against this stable item permanently fixes its procurement scope; a
	later drawdown within that same already-locked scope is an ordinary
	sequential draw, not a second lock event. `root` must already be
	guarded (locked) by the caller via `guard()`. Returns whether this call
	is the one that set the lock."""
	if root.scope_locked_since:
		return False
	envelope.bump(root, scope_locked_since=now_datetime(), first_authorised_requisition=cstr(requisition_reference))
	return True


def recompute_hold(root) -> dict[str, Any]:
	"""PLN-RI-029 — one effective hold is derived while any correction
	request against this stable item is Open or In progress; it is always
	recomputed from the current requests, never independently toggled, and
	release re-evaluates automatically once every request is terminal.
	`root` must already be guarded (locked) by the caller via `guard()`."""
	open_count = frappe.db.count(
		"Plan Item Correction Request",
		{"plan_item_id": root.name, "status": ("in", ("Open", "In progress"))},
	)
	envelope.bump(root, authorisation_hold=1 if open_count else 0, open_correction_requests=open_count)
	return status(root.name)


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
