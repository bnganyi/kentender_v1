# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — six-stage mutually exclusive pipeline counts."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime, now_datetime

from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_READY_FOR_RELEASE,
)

PIPELINE_STAGES = (
	("demands_under_review", "Demands under review", "/desk/demand-hub"),
	("approved_awaiting_planning", "Approved demands awaiting planning", "/desk/planning-hub"),
	("plan_awaiting_tender", "Plan items awaiting tender initiation", "/desk/planning-hub"),
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


def _count_demands_under_review(pe: str) -> int:
	return int(
		frappe.db.count(
			"Demand",
			{
				"procuring_entity": ["in", pe_aliases(pe)],
				"status": ["in", ["Pending HoD Approval", "Pending Finance Approval"]],
			},
		)
	)


def _count_approved_awaiting_planning(pe: str, user: str | None = None) -> int:
	try:
		from kentender_procurement.procurement_planning.services.approved_demand_queue import (
			get_approved_demands_awaiting_planning,
		)

		actor = (user or frappe.session.user or "").strip() or "Administrator"
		payload = get_approved_demands_awaiting_planning(
			{"procuring_entity": pe},
			actor,
		) or {}
		rows = payload.get("items") or payload.get("demands") or payload.get("rows") or []
		if isinstance(rows, list) and rows:
			return len(rows)
		if isinstance(payload.get("total"), (int, float)):
			return int(payload["total"])
	except Exception:
		pass
	return int(
		frappe.db.count(
			"Demand",
			{
				"procuring_entity": ["in", pe_aliases(pe)],
				"status": "Approved",
				"planning_status": ["in", ["Not Planned", "Partially Planned", "Planning Ready"]],
			},
		)
	)


def _count_plan_awaiting_tender(pe: str) -> int:
	if not frappe.db.exists("DocType", "Procurement Package"):
		return 0
	filters: dict[str, Any] = {
		"status": ["in", [PKG_APPROVED, PKG_READY_FOR_RELEASE]],
	}
	if frappe.db.has_column("Procurement Package", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(pe)]
	elif frappe.db.has_column("Procurement Package", "procuring_entity"):
		filters["procuring_entity"] = pe
	return int(frappe.db.count("Procurement Package", filters))


def _tm_filters(pe: str) -> dict[str, Any]:
	filters: dict[str, Any] = {}
	if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(pe)]
	return filters


def _count_tenders_in_preparation(pe: str) -> int:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0
	filters = {**_tm_filters(pe), "status": ["in", list(_TM_PREP)]}
	return int(frappe.db.count("TM2 Tender", filters))


def _published_open_codes(pe: str) -> list[str]:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return []
	filters = {**_tm_filters(pe), "status": "Published"}
	rows = frappe.get_all("TM2 Tender", filters=filters, fields=["name", "tender_code"], limit=500)
	now = now_datetime()
	open_codes: list[str] = []
	for r in rows:
		code = r.get("tender_code") or r.name
		deadline = None
		if frappe.db.exists("DocType", "TM2 Tender Timeline"):
			deadline = frappe.db.get_value(
				"TM2 Tender Timeline",
				{"tm2_tender": r.name},
				"submission_deadline_at",
			)
			if not deadline:
				deadline = frappe.db.get_value(
					"TM2 Tender Timeline",
					{"tender_code": code},
					"submission_deadline_at",
				)
		if deadline:
			try:
				if get_datetime(deadline) > now:
					open_codes.append(code)
			except Exception:
				continue
		else:
			# Published without deadline: count as open (explicit publish state)
			open_codes.append(code)
	return open_codes


def _count_closed_awaiting(pe: str) -> int:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0
	filters = {**_tm_filters(pe), "status": ["in", list(_TM_CLOSED_AWAITING)]}
	return int(frappe.db.count("TM2 Tender", filters))


def get_home_pipeline(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	_ = fiscal_year
	counts = {
		"demands_under_review": _count_demands_under_review(procuring_entity),
		"approved_awaiting_planning": _count_approved_awaiting_planning(procuring_entity, user),
		"plan_awaiting_tender": _count_plan_awaiting_tender(procuring_entity),
		"tenders_in_preparation": _count_tenders_in_preparation(procuring_entity),
		"published_and_open": len(_published_open_codes(procuring_entity)),
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
