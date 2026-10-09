# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.15 §5B — the Goods template's item-quantity rule.

The common requisition frame (identity, lineage, source lines, the open slot,
lifecycle, certification, drawdown, reservation, snapshot, handoff) holds no
rule about what an item is or how a quantity is entered. For the first release
that rule lives here, once:

* quantity is entered on an item row and nowhere else (§5.6);
* a source line's requested quantity is derived as the exact sum of its item
  quantities and never exceeds the quantity that remains available (§5.3);
* a source line with no items and no estimated total cost is unused: it is left
  out of the submitted snapshot, kept as history, and restored into a copied
  Draft (§5.3).

Works and Services will bring their own rule beside this one (§5B); nothing in
the frame needs to change for them.
"""

from __future__ import annotations

import json
from typing import Any

from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import precision, records

#: Child-table bookkeeping that is never part of a line's own content.
_SYSTEM_KEYS = ("name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "modified_by", "docstatus", "doctype")


def itemised(items, line_id: str, *, exclude_item: str = "") -> int:
	"""Whole Each already entered on the items of one source line."""
	return sum(
		int(i.get("quantity") or 0) for i in items or []
		if cstr(i.get("drawdown_line_id")) == cstr(line_id) and cstr(i.get("requisition_item_id")) != cstr(exclude_item)
	)


def room(line, items, *, exclude_item: str = "") -> int:
	"""Whole Each still available to enter on this source line."""
	return int(precision.stored_quantity(line.get("remaining_quantity"))) - itemised(items, line.get("drawdown_line_id"), exclude_item=exclude_item)


def quantity_exceeds_message(department: str, entered: int, available: int) -> str:
	return f"{department} can request at most {max(available, 0):,} Each for this requirement; you entered {entered:,}."


def estimate_exceeds_message(department: str, entered, available) -> str:
	return f"{department} can enter at most {precision.display_money(available)} for this requirement; you entered {precision.display_money(entered)}."


def has_estimate(line) -> bool:
	return precision.stored_money(line.get("requested_value")) > 0


def is_unused(line, items) -> bool:
	"""No items and no estimated total cost: the requester did not use this source."""
	return itemised(items, line.get("drawdown_line_id")) == 0 and not has_estimate(line)


def apply_derived_quantities(version, package_version) -> None:
	"""Set every source line's requested quantity to the exact sum of its items."""
	for line in version.drawdown_lines:
		line.requested_quantity = precision.quantity_text(itemised(package_version.items, line.drawdown_line_id))


def _plain(row) -> dict[str, Any]:
	data = row.as_dict() if hasattr(row, "as_dict") else dict(row)
	return {k: v for k, v in data.items() if k not in _SYSTEM_KEYS}


def omit_unused_lines(version, package_version) -> list[dict[str, Any]]:
	"""At submission: derive every quantity, then take the unused source lines
	out of the Version, recording them as history. At least one line must
	remain (validation has already refused a Draft with none). Returns the
	omitted lines."""
	apply_derived_quantities(version, package_version)
	kept, omitted = [], []
	for line in version.drawdown_lines:
		(omitted if is_unused(line, package_version.items) else kept).append(line)
	if omitted:
		version.omitted_lines_json = json.dumps([_plain(l) for l in omitted], sort_keys=True)
		version.set("drawdown_lines", kept)
	version.unreviewed_line_ids_json = json.dumps([])
	return [_plain(l) for l in omitted]


def omitted_lines(version) -> list[dict[str, Any]]:
	return records.json_list(version.get("omitted_lines_json")) if version.get("omitted_lines_json") else []


def restored_lines(reviewed_version) -> list[dict[str, Any]]:
	"""A copied Draft gets back the sources the submission left out, unused again (no items, estimate 0.00)."""
	out = []
	for line in omitted_lines(reviewed_version):
		out.append({**line, "requested_quantity": "0", "requested_value": "0.00", "reservation_id": None, "planning_drawdown_reference": None})
	return out


def unreviewed_ids(version) -> set[str]:
	raw = version.get("unreviewed_line_ids_json") if hasattr(version, "get") else None
	return set(records.json_list(raw)) if raw else set()


def mark_reviewed(version, line_ids) -> None:
	"""The requester saved these lines' estimated total costs: they are reviewed (§20)."""
	left = unreviewed_ids(version) - set(line_ids)
	if version.get("unreviewed_line_ids_json"):
		version.unreviewed_line_ids_json = json.dumps(sorted(left))
