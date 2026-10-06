# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — mutually exclusive pipeline counts.

The first two stages used to be **Demands under review** and **Approved demands
awaiting planning**. NDS-CHG-001 v1.1 replaced the Demands module with
Departmental Needs, and neither stage was updated: both counters returned a
hard-coded `0` behind a guard their own comments described as "permanently
unreachable", and both linked to `/desk/demands-workspace`, a route Phase 8
deleted. The dashboard therefore showed two stages that always read zero and
navigated to a 404.

They are replaced by one stage that reports real data. There is no fifth
counter for "needs under review" because §8.1 publishes no count contract for
submitted Needs, and inventing one here would mean reading another module's
tables directly — see FOLLOW_UPS FU-06. A pipeline whose every number is true is
worth more than a longer one carrying permanent zeros. The tender-side stages
(preparation, published, closed) read the retired tender workbench and were
removed with it; Tenders has not published a count contract for them yet.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.departmental_needs.constants import USAGE_FULL
from kentender_procurement.departmental_needs.services.events import (
	current_accepted_events,
)
from kentender_procurement.departmental_needs.services.usage import planning_usage
from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases

PIPELINE_STAGES = (
	(
		"needs_awaiting_planning",
		"Accepted needs awaiting planning",
		"/desk/departmental-needs",
	),
	("plan_awaiting_tender", "Plan items awaiting tender initiation", "/desk"),
)


def _count_needs_awaiting_planning(pe: str) -> int:
	"""Accepted Needs that no Active Plan yet represents.

	Read through the published Departmental Needs surface, never its tables:
	`current_accepted_events` is documented as "the published way for a consumer
	to rebuild or reconcile its projection", and `planning_usage` is the §4.7
	projection. That keeps the D1 ownership boundary real for this module too —
	the architecture guard now covers `procurement_home`, not just Planning.

	Summed across every Fiscal Year rather than the page's selected one — the
	stage is a site-wide funnel count, not one scoped to a single year.
	NDS-CHG-001 v1.6 moved Departmental Needs onto ERPNext's canonical
	`Fiscal Year` (previously a bespoke `Financial Year` doctype in a
	different vocabulary from Budget's own year selector, FOLLOW_UPS FU-07);
	this reads the same doctype Needs now does. The site has one implicit
	Procuring Entity (AUTH-ADR-001 v1.6) — `pe` is accepted for the caller's
	own PE-alias bookkeeping elsewhere in this module but is no longer a
	filter on the published Needs contract.
	"""
	if not frappe.db.exists("DocType", "Departmental Need"):
		return 0
	years = frappe.get_all("Fiscal Year", pluck="name", limit_page_length=0)
	awaiting = 0
	for year in years:
		for payload in current_accepted_events(financial_year=year):
			need = payload.get("need_id") or payload.get("need")
			if need and planning_usage(need) != USAGE_FULL:
				awaiting += 1
	return awaiting


def _packages_with_tender_initiation(pe: str) -> set[str]:
	"""Package names/codes that already have a tender or tender configuration."""
	claimed: set[str] = set()
	aliases = pe_aliases(pe)
	if frappe.db.exists("DocType", "Tender Configuration"):
		cfg_filters: dict[str, Any] = {}
		if frappe.db.has_column("Tender Configuration", "procuring_entity_code"):
			cfg_filters["procuring_entity_code"] = ["in", aliases]
		for r in frappe.get_all(
			"Tender Configuration",
			filters=cfg_filters or None,
			fields=["procurement_package", "procurement_package_ref"],
			limit=2000,
		):
			for key in ("procurement_package", "procurement_package_ref"):
				val = (r.get(key) or "").strip()
				if val:
					claimed.add(val)
	return claimed


def _count_plan_awaiting_tender(pe: str) -> int:
	"""PP2 Package queue retired — MVP-1 Plan Item take-up not yet live."""
	return 0


def get_home_pipeline(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	_ = fiscal_year
	counts = {
		"needs_awaiting_planning": _count_needs_awaiting_planning(procuring_entity),
		"plan_awaiting_tender": _count_plan_awaiting_tender(procuring_entity),
	}
	stages = []
	for key, label, url in PIPELINE_STAGES:
		stages.append(
			{
				"key": key,
				"label": label,
				"count": int(counts.get(key) or 0),
				"url": url,
			}
		)
	return {
		"ok": True,
		"stages": stages,
		"lifecycle_url": "/desk/plc-procurement-journey",
	}
