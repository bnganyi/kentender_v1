# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Give every department that already has an accepted Need its Draft plan.

Accepting a Departmental Need now starts that department's departmental plan
(`procurement_planning.services.dpp_autostart`). Needs accepted before that
reached the site left their department looking at **Start departmental plan**
with work already accepted — the friction this change removes. One Draft per
department and year, created exactly as an acceptance would have created it,
and nothing at all where the department already has a plan of any kind.

Idempotent: re-running replays each department's recorded command.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr

from kentender_procurement.departmental_needs.services.events import current_accepted_events
from kentender_procurement.procurement_planning.services import dpp_lifecycle


def execute() -> None:
	started = 0
	for fiscal_year in frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name"):
		units = {
			cstr(payload.get("org_unit_id")).strip()
			for payload in current_accepted_events(financial_year=fiscal_year)
			if cstr(payload.get("org_unit_id")).strip()
		}
		for organisation_unit in sorted(units):
			if frappe.db.exists(
				"Departmental Plan", {"organisation_unit": organisation_unit, "fiscal_year": fiscal_year}
			):
				continue
			outcome = dpp_lifecycle.ensure_departmental_plan(
				organisation_unit=organisation_unit,
				fiscal_year=fiscal_year,
				trigger_event=f"BACKFILL-{fiscal_year}-{organisation_unit}",
			)
			if outcome.get("action") == "opened":
				started += 1
	if started:
		print(f"Started {started} departmental plan(s) for departments with accepted Needs.")
