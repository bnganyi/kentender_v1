# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Procurement meetings register's second Tender (OVS-CHG-001 v0.6 plan Phase 5, tracker OVS6-0502 and
OVS6-0503; SEED-OPS-001 v1.23 section 9C).

The canonical Tender is Tender A: lead Digital Health, contributor Human Resources Management and
Development, a finalized opening with no session row and two ended evaluation sessions. This branch adds
Tender B beside it, on the Bid Opening browser-test world: a second Tender led by a different department
("Playwright — Digital Health", with one contributor) whose opening was recorded **Not held** (the attendance
service was down; the opening never started). The register must list that opening once and not count it as a
meeting held. A reader whose scope does not reach that department (Dr Peter Kimani) must not see it.

It is an isolated, opt-in branch. `load()` replaces the Bid Opening browser-test world; `unload()` removes it
and restores the site, leaving the canonical story as it was. The canonical rows are never touched. While it is
loaded the register has four rows (three held, one Not held), so a spec that counts the canonical story alone
must run with it unloaded."""

from __future__ import annotations

from typing import Any

import frappe


def load(*, commit: bool = True) -> dict[str, Any]:
	from kentender_procurement.bid_opening.seeds import playwright_ui_fixtures as pw

	out = pw.reset_opening_fixture(stage="not-held", commit=commit)
	row = frappe.db.get_value("Tender", out["tender"], ["lead_org_unit", "tender_reference"], as_dict=True)
	return {"loaded": True, "tender": out["tender"], "tender_reference": row.tender_reference, "lead_department": frappe.db.get_value("Organisation Unit", row.lead_org_unit, "unit_name"),
		"opening_state": frappe.db.get_value("Bid Opening Case", {"tender": out["tender"]}, "state"), "proceeding_state": frappe.db.get_value("Proceeding", {"owner_type": "Bid Opening Case",
		"owner_id": frappe.db.get_value("Bid Opening Case", {"tender": out["tender"]}, "name")}, "state")}


def unload(*, commit: bool = True) -> dict[str, Any]:
	from kentender_procurement.bid_opening.seeds import playwright_ui_fixtures as pw

	return {"loaded": False, **pw.restore_site(commit=commit)}
