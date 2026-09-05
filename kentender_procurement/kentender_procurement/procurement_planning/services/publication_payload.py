# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.13 — the canonical publication payload.

Open Contracting Data Standard planning-stage shape: one release per Plan
Item with an `ocid`, a `planning` block (budget reference, planned value,
rationale) and a `tender` block (title, description, procurement method,
value band, planned milestone dates, plan horizon, aggregation and lotting
indicators, reservation category). The entity is identified from site
configuration, not a stored key, and the payload is characterised as an
invitation to treat under section 53(12) (PLN-AC-077/090/108).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.services import readiness, references, schedule

OCDS_MILESTONES = {
	"invitation": "tenderPeriod.startDate",
	"bid_opening": "tenderPeriod.endDate",
	"evaluation_completion": "awardPeriod.startDate",
	"award_approval": "awardPeriod.endDate",
	"award_notification": "awardNotification",
	"contract_signing": "contractPeriod.startDate",
	"delivery_completion": "contractPeriod.endDate",
}


def build_payload(version, plan) -> dict[str, Any]:
	site = frappe.get_cached_doc("Site Procuring Entity")
	scheme = f"KE-KENTENDER-{cstr(site.pe_code)}"
	fiscal_year = plan.fiscal_year
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": ("in", ("Draft", "Active"))},
		fields=[
			"name", "plan_item_id", "title", "description", "requirement_type", "procurement_category",
			"procurement_method", "threshold_band_at_readiness", "plan_horizon", "multi_year_justification",
			"aggregation_indicator", "lotting_indicator", "lot_count", "reservation_category",
			"county_resident_reservation", "exclusive_preference", "aggregation_reason", "item_status",
			*schedule.BASELINE_FIELDS,
		],
		order_by="creation asc",
	)
	releases = []
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["allocation_id", "budget_line", "indicative_amount", "quantity", "unit", "organisation_unit", "source_origin", "need", "need_version"],
		)
		value = sum(flt(a.indicative_amount) for a in allocations)
		lines = sorted({cstr(a.budget_line) for a in allocations})
		line_refs = {
			row.name: row.generated_reference
			for row in frappe.get_all("Procurement Budget Line", filters={"name": ("in", lines or ("",))}, fields=["name", "generated_reference"])
		}
		milestones = [
			{
				"id": f"{item.plan_item_id}-{m}",
				"title": schedule.MILESTONE_LABELS[m],
				"type": "planning",
				"dueDate": cstr(item.get(f"baseline_{m}_date")),
				"ocdsPeriodField": OCDS_MILESTONES[m],
			}
			for m in schedule.MILESTONES
		]
		releases.append(
			{
				"ocid": f"ocds-{scheme.lower()}-{item.plan_item_id}",
				"id": f"{item.plan_item_id}-{version.version_reference}",
				"date": cstr(version.submitted_at or ""),
				"tag": ["planning"],
				"initiationType": "tender",
				"buyer": {"id": f"{scheme}", "name": cstr(site.pe_name)},
				"planning": {
					"rationale": cstr(item.description),
					"budget": {
						"id": ", ".join(line_refs.get(line, line) for line in lines),
						"description": cstr(item.title),
						"amount": {"amount": value, "currency": "KES"},
						"project": "",
						"source": ", ".join(sorted({cstr(a.source_origin) for a in allocations})),
					},
					"documents": [],
					"milestones": milestones,
					"kentender": {
						"planItemId": item.plan_item_id,
						"requirementType": cstr(item.requirement_type),
						"procurementCategory": cstr(item.procurement_category),
						"planHorizon": cstr(item.plan_horizon),
						"multiYearJustification": cstr(item.multi_year_justification),
						"aggregationIndicator": cstr(item.aggregation_indicator),
						"aggregationReason": cstr(item.aggregation_reason),
						"lottingIndicator": cstr(item.lotting_indicator),
						"lotCount": int(item.lot_count or 0),
						"reservationCategory": cstr(item.reservation_category),
						"countyResidentReservation": bool(item.county_resident_reservation),
						"exclusivePreference": bool(item.exclusive_preference),
						"valueBand": cstr(item.threshold_band_at_readiness),
						"status": cstr(item.item_status),
						"sources": [
							{
								"planSourceAllocationId": a.allocation_id,
								"organisationUnit": a.organisation_unit,
								"budgetLine": line_refs.get(a.budget_line, a.budget_line),
								"amount": flt(a.indicative_amount),
								"quantity": flt(a.quantity),
								"unit": a.unit,
								"origin": a.source_origin,
								"need": cstr(a.need),
								"needVersion": cstr(a.need_version),
							}
							for a in allocations
						],
					},
				},
				"tender": {
					"id": item.plan_item_id,
					"title": cstr(item.title),
					"description": cstr(item.description),
					"status": "planned",
					"procurementMethod": cstr(item.procurement_method),
					"procurementMethodDetails": cstr(item.threshold_band_at_readiness),
					"mainProcurementCategory": cstr(item.procurement_category).lower(),
					"value": {"amount": value, "currency": "KES"},
					"tenderPeriod": {"startDate": cstr(item.baseline_invitation_date), "endDate": cstr(item.baseline_bid_opening_date)},
					"awardPeriod": {"startDate": cstr(item.baseline_evaluation_completion_date), "endDate": cstr(item.baseline_award_approval_date)},
					"contractPeriod": {"startDate": cstr(item.baseline_contract_signing_date), "endDate": cstr(item.baseline_delivery_completion_date)},
					"numberOfLots": int(item.lot_count or 0) if item.lotting_indicator == "Packaged into lots" else 1,
				},
			}
		)
	return {
		"version": "1.1",
		"uri": f"kentender://annual-plan/{plan.plan_reference}/{version.version_reference}",
		"publisher": {"name": cstr(site.pe_name), "scheme": scheme, "uid": cstr(site.pe_code)},
		"publishedDate": cstr(version.submitted_at or ""),
		"license": "",
		"legalCharacter": "Invitation to treat (section 53(12), Public Procurement and Asset Disposal Act)",
		"format": "Third Schedule, Public Procurement and Asset Disposal Regulations 2020",
		"plan": {
			"planReference": plan.plan_reference,
			"versionReference": version.version_reference,
			"versionNumber": int(version.version_number),
			"title": cstr(plan.title),
			"fiscalYear": fiscal_year,
			"fiscalYearLabel": references.fy_label(fiscal_year),
			"entity": {"name": cstr(site.pe_name), "code": cstr(site.pe_code), "ppraRegistration": cstr(site.ppra_registration)},
			"preparedBy": "Head of the Procurement Function",
			"countersignedBy": "Accounting Officer",
			"approvedBy": cstr(site.get("statutory_approval_route")),
			"reservedShare": readiness.reserved_share(version.name),
		},
		"releases": releases,
	}
