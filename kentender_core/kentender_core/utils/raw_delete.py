# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A direct delete that takes the record's child-table rows with it.

Seeds and test fixtures delete records with `frappe.db.delete` because the
controllers refuse ordinary deletes by design. That skips the document
layer, so a record with child tables leaves their rows behind, where no
screen can ever reach them — found 26 Sep 2026: about 50,000 such rows on
the dev site. Use `delete_rows` wherever a record with child tables is
deleted directly. No commit.
"""

from __future__ import annotations

from typing import Any

import frappe

_CHUNK = 500


def delete_rows(doctype: str, filters: dict[str, Any] | None = None, *, deleted: dict[str, int] | None = None) -> int:
	"""`frappe.db.delete(doctype, filters)` plus the child-table rows of every
	record it removes. `filters=None` removes every record. `deleted`, when
	given, accumulates a count per doctype. Returns the records removed."""
	tables = [df.options for df in frappe.get_meta(doctype).get_table_fields()]
	names = frappe.get_all(doctype, filters=filters or {}, pluck="name")
	for start in range(0, len(names), _CHUNK):
		chunk = names[start : start + _CHUNK]
		for child in tables:
			child_filters = {"parenttype": doctype, "parent": ("in", chunk)}
			if deleted is not None and (count := frappe.db.count(child, child_filters)):
				deleted[child] = deleted.get(child, 0) + count
			frappe.db.delete(child, child_filters)
		frappe.db.delete(doctype, {"name": ("in", chunk)})
	if deleted is not None and names:
		deleted[doctype] = deleted.get(doctype, 0) + len(names)
	return len(names)
