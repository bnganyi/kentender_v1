# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.9 / §5.5.2.1 — the approved Plan's content and the
canonical `KenTenderAnnualPlan.v1` public payload (plan D8; PLN18-209).

`build_snapshot` is the COMPLETE governed content frozen once at approval —
every applicable §4.6 field, the exact source allocations, the financial
basis and the governance/rule/Strategy evidence index. It becomes
`Approved Plan Snapshot.content`; the protected review pack (Phase 3F) reads
it directly. `build_public_payload` derives the publishable subset: opaque
stable/exact IDs, decimal-string Money/Quantity, ISO dates, `null` with
applicability stated for an inapplicable value, and none of the internal
assignment IDs, confidential attachments or financial-availability detail.
No `ocid`, no disposal block, no operational actual/forecast overwrite —
those were the retired OCDS-shaped contract's defects (v1.18 §5.5.2.1).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt

from kentender_procurement.procurement_planning.services import financial_basis, money, profiles, readiness, references, schedule

SCHEMA_VERSION = "KenTenderAnnualPlan.v1"


def _item_content(item, allocations: list) -> dict[str, Any]:
	value = money.sum_money(a.indicative_amount for a in allocations)
	schedule_profile = profiles.schedule_profile_by_name(cstr(item.schedule_profile_version))
	applicable = set(profiles.applicable_milestones(schedule_profile)) if schedule_profile.get("found") else set(schedule.MILESTONES)
	baseline_rows = []
	for m in schedule.MILESTONES:
		applies = m in applicable
		baseline_rows.append(
			{
				"milestone": m, "label": schedule.MILESTONE_LABELS[m], "applies": applies,
				"date": cstr(item.get(f"baseline_{m}_date")) if (applies and item.get(f"baseline_{m}_date")) else None,
			}
		)
	return {
		"planItemId": item.plan_item_id,
		"title": item.title,
		"description": item.description,
		"requirementType": cstr(item.requirement_type),
		"procurementCategory": cstr(item.procurement_category),
		"procurementMethod": cstr(item.procurement_method),
		"methodProfileVersion": cstr(item.method_profile_version) or None,
		"scheduleProfileVersion": cstr(item.schedule_profile_version) or None,
		"strategicObjectivePath": cstr(item.objective_path) or None,
		"planHorizon": cstr(item.plan_horizon),
		"aggregationIndicator": cstr(item.aggregation_indicator),
		"aggregationReason": cstr(item.aggregation_reason) or None,
		"lottingIndicator": cstr(item.lotting_indicator),
		"lotCount": int(item.lot_count or 0) if item.lotting_indicator == "Packaged into lots" else None,
		"reservationCategory": cstr(item.reservation_category) or None,
		"countyResidentReservation": bool(item.county_resident_reservation),
		"estimateBasis": cstr(item.estimate_basis) or None,
		"estimatedDeliveryPeriodDays": readiness.item_delivery_days(item),
		"estimatedCompletionDate": cstr(item.estimated_completion_date) or None,
		"plannedValue": money.money_text(value),
		"currency": "KES",
		"baselineMilestones": baseline_rows,
		"itemState": item.item_state,
	}


def _source_content(allocation, entry_labels: dict[str, str]) -> dict[str, Any]:
	return {
		"planSourceAllocationId": allocation.allocation_id,
		"sourceOrigin": allocation.source_origin,
		"sourceKey": cstr(allocation.source_key),
		"organisationUnit": entry_labels.get(allocation.organisation_unit, allocation.organisation_unit),
		"quantity": money.quantity_text(allocation.quantity),
		"unit": cstr(allocation.unit),
		"requiredByDate": cstr(allocation.required_by_date),
		"budgetLine": cstr(allocation.budget_line),
		"amount": money.money_text(allocation.indicative_amount),
		"currency": "KES",
		"allocationState": allocation.allocation_state,
	}


def _evidence_index(version, plan) -> dict[str, Any]:
	"""§4.9 — the approved source/strategy/Finance/rule/decision evidence
	index a reviewer or the review pack (Phase 3F) resolves against."""
	from kentender_procurement.procurement_planning.services import planning_authorization as authz

	ao_decision = frappe.db.get_value(
		"Plan Governance Decision", {"plan_version": version.name, "stage": "Accounting Officer adoption"}, ["decision_reference", "actor", "decided_at"], as_dict=True, order_by="decided_at desc",
	)
	statutory_decision = frappe.db.get_value(
		"Plan Governance Decision", {"plan_version": version.name, "stage": "Statutory approval"}, ["decision_reference", "actor", "capacity", "collective_resolution_reference", "decided_at"], as_dict=True, order_by="decided_at desc",
	)
	chain = authz.evidence_chain(version.name) or [version.name]
	task_name = frappe.db.get_value("Plan Finance Task", {"plan_version": ("in", chain), "status": "Completed"}, "financial_basis", order_by="modified desc")
	basis = financial_basis.summary(frappe.get_doc(financial_basis.DOCTYPE, task_name)) if task_name and frappe.db.exists(financial_basis.DOCTYPE, task_name) else None
	return {
		"preparationSignature": cstr(version.preparation_signature) or None,
		"accountingOfficerDecision": ao_decision.decision_reference if ao_decision else None,
		"statutoryDecision": statutory_decision.decision_reference if statutory_decision else None,
		"statutoryCapacity": statutory_decision.capacity if statutory_decision else None,
		"collectiveResolutionReference": statutory_decision.collective_resolution_reference if statutory_decision else None,
		"financialBasisDigest": basis.get("basis_digest") if basis else None,
	}


def build_snapshot(version, plan) -> dict[str, Any]:
	site = frappe.get_cached_doc("Site Procuring Entity")
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": ("in", ("Draft", "Active"))},
		fields=[
			"name", "plan_item_id", "title", "description", "requirement_type", "procurement_category", "procurement_method",
			"method_profile_version", "schedule_profile_version", "objective_path", "plan_horizon", "aggregation_indicator",
			"aggregation_reason", "lotting_indicator", "lot_count", "reservation_category", "county_resident_reservation",
			"estimate_basis", "estimated_completion_date", "period_inputs", "item_state",
			*schedule.BASELINE_FIELDS,
		],
		order_by="creation asc",
	)
	item_rows, source_rows = [], []
	entry_labels = {row.name: cstr(row.unit_name) for row in frappe.get_all("Organisation Unit", fields=["name", "unit_name"])}
	total = 0
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation", filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["allocation_id", "source_origin", "source_key", "organisation_unit", "quantity", "unit", "required_by_date", "budget_line", "indicative_amount", "allocation_state"],
		)
		item_rows.append(_item_content(item, allocations))
		for allocation in allocations:
			source_rows.append({"planItemId": item.plan_item_id, **_source_content(allocation, entry_labels)})
		total += flt(sum(flt(a.indicative_amount) for a in allocations))
	return {
		"schemaVersion": SCHEMA_VERSION,
		"planId": plan.name,
		"planReference": plan.plan_reference,
		"planVersionId": version.name,
		"versionReference": version.version_reference,
		"versionNumber": int(version.version_number),
		"fiscalYear": plan.fiscal_year,
		"fiscalYearLabel": references.fy_label(plan.fiscal_year),
		"title": cstr(plan.title),
		"projectName": cstr(version.project_name) or None,
		"entity": {"name": cstr(site.pe_name), "code": cstr(site.pe_code), "ppraRegistration": cstr(site.ppra_registration)},
		"items": item_rows,
		"sources": source_rows,
		"totals": {"currency": "KES", "planTotal": money.money_text(total)},
		"evidence": _evidence_index(version, plan),
	}


def content_digest(content: dict[str, Any]) -> str:
	return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def build_public_payload(snapshot_doc) -> dict[str, Any]:
	"""The publishable subset of one approved snapshot. Every field maps
	explicitly; nothing here is copied wholesale from the internal content."""
	content = json.loads(snapshot_doc.content)
	return {
		"schemaVersion": SCHEMA_VERSION,
		"publicationId": None,  # filled in once the Plan Publication exists
		"planId": content["planId"],
		"planVersionId": content["planVersionId"],
		"versionNumber": content["versionNumber"],
		"fiscalYear": content["fiscalYear"],
		"entity": {"name": content["entity"]["name"], "publicName": content["entity"]["name"]},
		"approvedAt": cstr(snapshot_doc.approved_at),
		"publicationCharacter": "Invitation to treat (section 53(12), Public Procurement and Asset Disposal Act)",
		"header": {"title": content["title"], "projectName": content.get("projectName")},
		"items": [
			{
				"planItemId": row["planItemId"], "title": row["title"], "description": row["description"],
				"requirementType": row["requirementType"], "procurementCategory": row["procurementCategory"],
				"procurementMethod": row["procurementMethod"], "planHorizon": row["planHorizon"],
				"aggregationIndicator": row["aggregationIndicator"], "lottingIndicator": row["lottingIndicator"],
				"lotCount": row["lotCount"], "reservationCategory": row["reservationCategory"],
				"countyResidentReservation": row["countyResidentReservation"], "plannedValue": row["plannedValue"],
				"currency": row["currency"], "baselineMilestones": row["baselineMilestones"], "itemState": row["itemState"],
			}
			for row in content["items"]
		],
		"sources": [
			{"planItemId": row["planItemId"], "sourceOrigin": row["sourceOrigin"], "organisationUnit": row["organisationUnit"], "quantity": row["quantity"], "unit": row["unit"], "amount": row["amount"], "currency": row["currency"]}
			for row in content["sources"]
		],
		"totals": content["totals"],
		"evidence": {k: v for k, v in content["evidence"].items() if v is not None},
	}


def manifest_for(payload: dict[str, Any], package_hash: str) -> list[dict[str, Any]]:
	body = json.dumps(payload, sort_keys=True, default=str)
	return [{"filename": "annual-procurement-plan.json", "media_type": "application/json", "hash": package_hash, "size": len(body.encode("utf-8"))}]
