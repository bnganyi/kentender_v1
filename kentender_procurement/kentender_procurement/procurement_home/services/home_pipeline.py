# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — five-stage mutually exclusive pipeline counts.

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
tables directly — see FOLLOW_UPS FU-06. A five-stage pipeline whose every
number is true is worth more than a six-stage one carrying a permanent zero.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

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
	("tenders_in_preparation", "Tenders in preparation", "/desk/tender-management-v2"),
	("published_and_open", "Published and open", "/desk/publications"),
	("closed_awaiting_next", "Closed awaiting next stage", "/desk/tender-management-v2"),
)

_TM_PREP = frozenset(
	(
		"Draft",
		"STD Instance Incomplete",
		"Ready for Publication Review",
		"Returned for Correction",
		"Approved for Publication",
	)
)
_TM_CLOSED_AWAITING = frozenset(("Closed", "Closed - No Valid Submissions", "Opening Ready"))
_TM_EXCLUDE_ACTIVE = frozenset(("Cancelled", "Evaluation Ready"))


def _count_needs_awaiting_planning(pe: str) -> int:
	"""Accepted Needs in this PE that no Active Plan yet represents.

	Read through the published Departmental Needs surface, never its tables:
	`current_accepted_events` is documented as "the published way for a consumer
	to rebuild or reconcile its projection", and `planning_usage` is the §4.7
	projection. That keeps the D1 ownership boundary real for this module too —
	the architecture guard now covers `procurement_home`, not just Planning.

	Summed across every Financial Year rather than the page's selected one,
	because the two use different vocabularies: Procurement Home derives an
	integer start year from Budget's `fiscal_period` (2026), while Needs key on
	`Financial Year` records (`FY-2027-2028`). Filtering by the selected year
	would silently reintroduce the permanent zero this stage exists to remove.
	"""
	if not frappe.db.exists("DocType", "Departmental Need"):
		return 0
	years = frappe.get_all("Financial Year", pluck="name", limit_page_length=0)
	awaiting = 0
	for year in years:
		for payload in current_accepted_events(procuring_entity=pe, financial_year=year):
			need = payload.get("need_id") or payload.get("need")
			if need and planning_usage(need) != USAGE_FULL:
				awaiting += 1
	return awaiting


def _packages_with_tender_initiation(pe: str) -> set[str]:
	"""Package names/codes that already have a tender or tender configuration."""
	claimed: set[str] = set()
	aliases = pe_aliases(pe)
	if frappe.db.exists("DocType", "TM2 Tender"):
		tm_filters: dict[str, Any] = {}
		if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
			tm_filters["procuring_entity_code"] = ["in", aliases]
		for r in frappe.get_all(
			"TM2 Tender",
			filters=tm_filters,
			fields=["procurement_package", "procurement_package_code"],
			limit=2000,
		):
			for key in ("procurement_package", "procurement_package_code"):
				val = (r.get(key) or "").strip()
				if val:
					claimed.add(val)
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


def _tm_filters(pe: str) -> dict[str, Any]:
	filters: dict[str, Any] = {}
	if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(pe)]
	return filters


def _submission_deadline(tender_name: str, tender_code: str):
	if not frappe.db.exists("DocType", "TM2 Tender Timeline"):
		return None
	deadline = frappe.db.get_value(
		"TM2 Tender Timeline",
		{"tm2_tender": tender_name},
		"submission_deadline_at",
	)
	if deadline:
		return deadline
	if tender_code:
		return frappe.db.get_value(
			"TM2 Tender Timeline",
			{"tender_code": tender_code},
			"submission_deadline_at",
		)
	return None


def _count_tenders_in_preparation(pe: str) -> int:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0
	filters = {**_tm_filters(pe), "status": ["in", list(_TM_PREP)]}
	return int(frappe.db.count("TM2 Tender", filters))


def _published_open_and_closed_past_deadline(pe: str) -> tuple[int, int]:
	"""Published+open vs Published with submission period closed (PRD §9)."""
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0, 0
	filters = {**_tm_filters(pe), "status": "Published"}
	rows = frappe.get_all(
		"TM2 Tender", filters=filters, fields=["name", "tender_code"], limit=500
	)
	now = now_datetime()
	open_count = 0
	closed_past = 0
	for r in rows:
		code = r.get("tender_code") or r.name
		deadline = _submission_deadline(r.name, code)
		if deadline:
			try:
				if get_datetime(deadline) > now:
					open_count += 1
				else:
					closed_past += 1
			except Exception:
				continue
		else:
			# Published without deadline: count as open (explicit publish state)
			open_count += 1
	return open_count, closed_past


def _count_closed_awaiting(pe: str) -> int:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0
	filters = {**_tm_filters(pe), "status": ["in", list(_TM_CLOSED_AWAITING)]}
	explicit = int(frappe.db.count("TM2 Tender", filters))
	_, published_closed = _published_open_and_closed_past_deadline(pe)
	return explicit + published_closed


def get_home_pipeline(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	_ = fiscal_year
	published_open, _published_closed = _published_open_and_closed_past_deadline(
		procuring_entity
	)
	counts = {
		"needs_awaiting_planning": _count_needs_awaiting_planning(procuring_entity),
		"plan_awaiting_tender": _count_plan_awaiting_tender(procuring_entity),
		"tenders_in_preparation": _count_tenders_in_preparation(procuring_entity),
		"published_and_open": published_open,
		"closed_awaiting_next": _count_closed_awaiting(procuring_entity),
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
