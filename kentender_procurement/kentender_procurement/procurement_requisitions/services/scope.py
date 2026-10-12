# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.18 §5.7A — which items a requirement row covers.

A technical, service or acceptance row names the exact Requisition Items it
covers in `applies_to_item_ids_json`. `applies_to_scope` is derived from that
list: `Item` (one), `Items` (several, not all) or `All items` (every item).
This module is the one owner of that rule; the Draft commands, validation, the
proposal, the presenters and the handoff all read it here.

An `All items` row in a Draft stores no list (it follows the items as they
change); at lock the list is filled in so the frozen Version records exactly
what each requirement covered. A row saved before v1.18 holds no list at all
and is read from its scope (`All items` = every item, `Item` = the stated one),
which is also how the handoff reads a Version locked earlier.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from frappe.utils import cstr

ALL_ITEMS = "All items"
ITEM = "Item"
ITEMS = "Items"
SERVICE = "Service"


def _ids_of(items: Iterable[Any]) -> list[str]:
	return [cstr(i.get("requisition_item_id")) for i in items or [] if i.get("requisition_item_id")]


def stored_ids(row) -> list[str]:
	raw = row.get("applies_to_item_ids_json") if hasattr(row, "get") else None
	if not raw:
		return []
	try:
		value = json.loads(raw) if isinstance(raw, str) else list(raw)
	except ValueError:
		return []
	return [cstr(v) for v in value if v]


def item_ids(row, items: Iterable[Any]) -> list[str]:
	"""The exact items a row covers, in item order."""
	all_ids = _ids_of(items)
	scope = row.get("applies_to_scope")
	if scope == SERVICE:
		return []
	if scope == ALL_ITEMS or not scope:
		return all_ids
	wanted = stored_ids(row) or ([cstr(row.get("applies_to_id"))] if scope == ITEM and row.get("applies_to_id") else [])
	return [i for i in all_ids if i in set(wanted)] if wanted else []


def categories_of(row, items: Iterable[Any]) -> list[str]:
	"""The categories (first seen, once each) of the items a row covers."""
	covered = set(item_ids(row, items))
	out: list[str] = []
	for item in items or []:
		category = cstr(item.get("equipment_category"))
		if cstr(item.get("requisition_item_id")) in covered and category and category not in out:
			out.append(category)
	return out


def normalise(ids: Iterable[str], items: Iterable[Any], characteristic=None) -> dict[str, Any]:
	"""The stored form of a row that covers `ids`: scope, `applies_to_id` and the item list.

	`All items` only when the row covers every item AND (for a technical row) the characteristic applies
	to every category present, so a request that mixes kinds never falls back to it."""
	all_ids = _ids_of(items)
	by_id = {cstr(i.get("requisition_item_id")): cstr(i.get("equipment_category")) for i in items or []}
	wanted = [i for i in all_ids if i in set(ids)]
	if wanted and len(wanted) == len(all_ids) and (characteristic is None or all(characteristic.applies(c) for c in by_id.values())):
		return {"applies_to_scope": ALL_ITEMS, "applies_to_id": "", "applies_to_item_ids_json": ""}
	if len(wanted) == 1:
		return {"applies_to_scope": ITEM, "applies_to_id": wanted[0], "applies_to_item_ids_json": json.dumps(wanted)}
	# `applies_to_id` names the first item only so an older reader under-applies rather than over-applies.
	return {"applies_to_scope": ITEMS, "applies_to_id": wanted[0] if wanted else "", "applies_to_item_ids_json": json.dumps(wanted)}


def freeze(row, items: Iterable[Any]) -> None:
	"""At lock: record the exact items an `All items` row covered (before the digest is computed)."""
	if row.get("applies_to_scope") == ALL_ITEMS:
		row.applies_to_item_ids_json = json.dumps(_ids_of(items))


def label(row, items: Iterable[Any]) -> str:
	"""What a row applies to, in words: `All items`, an item name, or the distinct names of its items."""
	scope = row.get("applies_to_scope")
	if scope == ALL_ITEMS or scope == SERVICE or not scope:
		return ALL_ITEMS
	covered = set(item_ids(row, items))
	names: list[str] = []
	for item in items or []:
		if cstr(item.get("requisition_item_id")) in covered and cstr(item.get("item_name")) not in names:
			names.append(cstr(item.get("item_name")))
	return ", ".join(names) or cstr(row.get("applies_to_id"))
