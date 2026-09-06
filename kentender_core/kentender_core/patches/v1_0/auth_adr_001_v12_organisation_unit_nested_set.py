"""Populate `lft`/`rgt` for the Organisation Unit tree (AUTH-ADR-001 v1.2 §6.1).

`bench migrate` adds the three nested-set columns but leaves every existing row
at `lft = rgt = 0`, which makes the descendant range predicate the shared
resolver depends on match nothing at all — a silent, total scope denial rather
than an error. `rebuild_tree` walks each root once and stamps the real ranges.

Idempotent: rebuilding an already-correct tree recomputes the same numbers.
"""

from __future__ import annotations

import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
	if not frappe.db.has_column("Organisation Unit", "lft"):
		# The doctype change has not landed on this site yet; a later migrate
		# runs the patch again once the column exists.
		return
	rebuild_tree("Organisation Unit")
