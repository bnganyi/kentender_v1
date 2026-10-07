# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Seeds and tests only: add the Version's current optimistic-lock stamp to a
Budget command payload.

Every state-changing Budget command requires `expected_modified` (BUD §9.2,
AUD-XC-119). A real client sends the stamp it loaded; a seed or a test that
drives the commands in-process and has nothing stale to prove reads the current
one here. Never use this in a service or an endpoint: a command that stamps its
own payload defeats the check.
"""

from __future__ import annotations

from typing import Any

import frappe


def current_stamp(version: str) -> str:
	"""The stamp of a Budget Version given by name or generated reference."""
	name = version if frappe.db.exists("Procurement Budget Version", version) else frappe.db.get_value("Procurement Budget Version", {"generated_reference": version}, "name")
	return str(frappe.db.get_value("Procurement Budget Version", name, "modified")) if name else ""


def stamped(payload: dict[str, Any]) -> dict[str, Any]:
	"""`payload` plus `expected_modified` taken from the database now. A payload
	that already carries a stamp, or that creates a first Draft (no existing
	Version), is returned unchanged."""
	payload = dict(payload)
	if payload.get("expected_modified") not in (None, ""):
		return payload
	version = (payload.get("budget_version") or "").strip()
	if version:
		payload["expected_modified"] = current_stamp(version)
		return payload
	budget = (payload.get("budget") or "").strip()
	if budget and not payload.get("fiscal_year"):
		draft_edit = "authorised_total" in payload or "approval_reference" in payload
		statuses = ("Draft",) if draft_edit else ("Active",)
		name = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": ["in", statuses]}, "name", order_by="version_number desc")
		if not name:
			name = frappe.db.get_value("Procurement Budget Version", {"budget": frappe.db.get_value("Procurement Budget", {"generated_reference": budget}, "name") or budget, "status": ["in", statuses]}, "name", order_by="version_number desc")
		if name:
			payload["expected_modified"] = current_stamp(name)
	return payload
