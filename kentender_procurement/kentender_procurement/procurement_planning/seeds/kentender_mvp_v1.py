# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 — Planning seed entry points (interim stubs).

The Demand-era seed content was demolished in Phase 1 with its doctypes.
The §14 deterministic seed contract is implemented in Phase 11; until then
`upsert_planning_base` is a documented no-op so the KENTENDER_MVP_V1
orchestrator stays green, and `clear_planning_fixture_rows` clears the v1.2
doctypes by fixture namespace so the Playwright purge keeps working.
"""

from __future__ import annotations

from typing import Any

import frappe

PLAYWRIGHT_NS = "KENTENDER_PLAYWRIGHT"

_V12_DOCTYPES = (
	# dependents first, roots last
	"Annual Plan Publication",
	"Plan Reservation Reference",
	"Plan Governance Decision",
	"Plan Governance Task",
	"Plan Finance Decision",
	"Plan Finance Task",
	"Plan Source Allocation",
	"Annual Plan Item",
	"Annual Plan Version",
	"Annual Plan",
	"Departmental Plan Validation Decision",
	"Departmental Plan Validation Task",
	"Departmental Plan Submission",
	"Departmental Plan Entry",
	"Departmental Plan Version",
	"Departmental Plan",
	"Departmental Plan Submission Window",
	"Annual Plan Publication Destination",
)


def upsert_planning_base(*, commit: bool = False) -> dict[str, Any]:
	"""§14 seed pending Phase 11; explicit skip so callers see honest status."""
	return {"ok": False, "skipped": True, "reason": "PLN_CHG_001_V12_SEED_PENDING_PHASE_11"}


def clear_planning_fixture_rows(
	*, include_canonical: bool = False, include_playwright: bool = True
) -> dict[str, int]:
	deleted: dict[str, int] = {}
	namespaces: list[str] = []
	if include_playwright:
		namespaces.append(PLAYWRIGHT_NS)
	for doctype in _V12_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		filters: dict[str, Any] = {}
		if not include_canonical:
			if not namespaces:
				continue
			filters["fixture_namespace"] = ("in", namespaces)
		rows = frappe.get_all(doctype, filters=filters, pluck="name")
		for name in rows:
			frappe.delete_doc(
				doctype, name, force=True, ignore_permissions=True, delete_permanently=True
			)
		deleted[doctype] = len(rows)
	return deleted
