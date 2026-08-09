# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-SEED-001 — principal KENTENDER_MVP_V1 approved Demand."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_procurement.demands.services.demand_codes import allocate_item_code

AMOUNT = 455_000_000
FIXTURE_NS = C.FIXTURE_NS
APPROVED_AT = "2027-08-16 10:00:00"
STRATEGY_CONFIRMED_AT = "2027-08-14 10:00:00"
BUDGET_CONFIRMED_AT = "2027-08-15 10:00:00"
PAA_USER = "moh.procurement.authority@example.test"
BUDGET_OFFICER_USER = "moh.budget.officer@example.test"

ITEMS = (
	{
		"item_code": allocate_item_code(C.DEMAND_CODE, 1),
		"description": "Resilient compute and storage platform",
		"amount": 300_000_000,
	},
	{
		"item_code": allocate_item_code(C.DEMAND_CODE, 2),
		"description": "Network, monitoring and implementation services",
		"amount": 155_000_000,
	},
)

STRATEGY_REFS = (
	{
		"reference_type": "Primary",
		"target_code": C.TGT_AVAIL_2028,
		"reason": (
			"The infrastructure directly supports availability of core clinical "
			"information systems"
		),
	},
	{
		"reference_type": "Supporting",
		"target_code": C.TGT_RESTORE_2028,
		"reason": (
			"Resilient infrastructure and monitoring support faster restoration "
			"of critical services"
		),
	},
)

VALUE_TREATMENTS = {
	"MOH-PVC-EFT-01": (
		"Embedded in specification",
		"Infrastructure supports reliable critical health services",
	),
	"MOH-PVC-ECO-01": (
		"To be determined in Planning",
		"Whole-life costing, energy use and lifecycle optimisation must be resolved "
		"during plan preparation",
	),
	"MOH-PVC-RES-01": (
		"Contract obligation",
		"Redundancy, continuity and support requirements must carry forward",
	),
	"MOH-PVC-SUS-02": (
		"Delivery or disposal obligation",
		"Replaced ICT equipment requires controlled end-of-life handling",
	),
}


def _required(doctype: str, filters: dict[str, Any], label: str) -> str:
	rows = frappe.get_all(doctype, filters=filters, pluck="name", limit=2)
	if len(rows) != 1:
		raise frappe.ValidationError(
			f"DEM-SEED-001 requires exactly one {label}; found {len(rows)}"
		)
	return rows[0]


def _upsert(
	doctype: str,
	filters: dict[str, Any],
	values: dict[str, Any],
) -> tuple[str, bool]:
	name = frappe.db.get_value(doctype, filters, "name")
	if name:
		doc = frappe.get_doc(doctype, name)
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc.name, False
	doc = frappe.get_doc({"doctype": doctype, **filters, **values})
	doc.insert(ignore_permissions=True)
	return doc.name, True


def _target(code: str) -> frappe._dict:
	name = _required("Performance Target", {"target_code": code}, f"Strategy target {code}")
	row = frappe.db.get_value(
		"Performance Target",
		name,
		["name", "target_code", "title", "plan_version"],
		as_dict=True,
	)
	if not row or not row.plan_version:
		raise frappe.ValidationError(f"DEM-SEED-001 target {code} has no plan version")
	return row


def _existing_user(email: str) -> str | None:
	return email if frappe.db.exists("User", email) else None


def _purge_noncanonical_items(demand: str) -> None:
	"""Drop stray item rows (wrong item_code) so the fixture stays exactly two lines."""
	canonical = {spec["item_code"] for spec in ITEMS}
	for row in frappe.get_all(
		"Demand Item",
		filters={"demand": demand},
		fields=["name", "item_code"],
	):
		if row.item_code not in canonical:
			frappe.delete_doc(
				"Demand Item", row.name, force=True, ignore_permissions=True
			)


def _seed_items(demand: str) -> tuple[list[str], int]:
	_purge_noncanonical_items(demand)
	names: list[str] = []
	created = 0
	for spec in ITEMS:
		name, was_created = _upsert(
			"Demand Item",
			{"item_code": spec["item_code"]},
			{
				"demand": demand,
				"description": spec["description"],
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": spec["amount"],
				"confirmed_quantity": 1,
				"confirmed_uom": "Lot",
				"confirmed_estimate": spec["amount"],
				"remaining_quantity": 1,
				"remaining_amount": spec["amount"],
				"currency": "KES",
				"fixture_namespace": FIXTURE_NS,
			},
		)
		names.append(name)
		created += int(was_created)
	return names, created


def _seed_strategy(demand: str) -> tuple[list[str], int, str]:
	names: list[str] = []
	created = 0
	plan_name = ""
	for spec in STRATEGY_REFS:
		target = _target(spec["target_code"])
		if plan_name and target.plan_version != plan_name:
			raise frappe.ValidationError("DEM-SEED-001 Strategy targets use different plan versions")
		plan_name = target.plan_version
		path = (
			f"{C.PLAN_TITLE} > Digital Health Services > Health Information Systems > "
			"Reliable and accessible digital clinical services"
		)
		name, was_created = _upsert(
			"Demand Strategy Reference",
			{"demand": demand, "reference_type": spec["reference_type"]},
			{
				"plan": target.plan_version,
				"plan_version_id": target.plan_version,
				"target_id": target.name,
				"target_code": target.target_code,
				"target_name": target.title,
				"hierarchy_path": path,
				"snapshot_label": target.title,
				"selection_source": "Canonical fixture",
				"confirmed_by": _existing_user(PAA_USER),
				"confirmed_at": STRATEGY_CONFIRMED_AT,
				"confirmation_reason": spec["reason"],
				"fixture_namespace": FIXTURE_NS,
			},
		)
		names.append(name)
		created += int(was_created)
	return names, created, plan_name


def _seed_value_treatments(demand: str, plan_name: str) -> tuple[list[str], int]:
	names: list[str] = []
	created = 0
	for code, (treatment, rationale) in VALUE_TREATMENTS.items():
		pvc = _required(
			"Plan Value Commitment",
			{"plan_version": plan_name, "commitment_code": code},
			f"Plan Value Commitment {code}",
		)
		name, was_created = _upsert(
			"Demand Value Treatment",
			{"demand": demand, "plan_value_commitment": pvc},
			{
				"pvc_version_id": pvc,
				"pvc_snapshot": code,
				"applicability": "Applicable",
				"treatment": treatment,
				"rationale": rationale,
				"confirmed_by": _existing_user(PAA_USER),
				"confirmed_at": STRATEGY_CONFIRMED_AT,
				"fixture_namespace": FIXTURE_NS,
			},
		)
		names.append(name)
		created += int(was_created)
	return names, created


def upsert_principal_approved_demand(*, commit: bool = True) -> dict[str, Any]:
	"""Idempotently seed only DMD-MOH-2027-014 and attach the existing RSV."""
	frappe.only_for(("System Manager", "Administrator"))

	pe = _required("Procuring Entity", {"entity_code": C.PE_MOH}, C.PE_MOH)
	owner_org_unit = _required(
		"Organisation Unit",
		{"unit_code": C.OU_DIR_DHP},
		C.OU_DIR_DHP,
	)
	if not frappe.db.exists("User", C.USER_MEDICAL):
		raise frappe.ValidationError(f"DEM-SEED-001 requires requester {C.USER_MEDICAL}")

	budget_line = _required(
		"Budget Line",
		{"generated_reference": C.BL_DHI_2027},
		C.BL_DHI_2027,
	)
	budget = frappe.db.get_value("Budget Line", budget_line, "budget")
	reservation = _required(
		"Funding Reservation",
		{"generated_reference": C.RSV_CODE},
		C.RSV_CODE,
	)
	reservation_row = frappe.db.get_value(
		"Funding Reservation",
		reservation,
		["budget", "budget_line", "original_amount", "status"],
		as_dict=True,
	)
	if (
		reservation_row.budget != budget
		or reservation_row.budget_line != budget_line
		or flt(reservation_row.original_amount) != AMOUNT
	):
		raise frappe.ValidationError(
			"DEM-SEED-001 RSV-MOH-0001 does not match MOH-BL-DHI-2027 / KES 455,000,000"
		)

	snapshot = {
		"demand_code": C.DEMAND_CODE,
		"title": "National digital health infrastructure upgrade",
		"confirmed_estimate": AMOUNT,
		"currency": "KES",
		"items": [
			{
				"item_code": spec["item_code"],
				"description": spec["description"],
				"confirmed_estimate": spec["amount"],
			}
			for spec in ITEMS
		],
		"strategy_targets": [spec["target_code"] for spec in STRATEGY_REFS],
		"budget_line": C.BL_DHI_2027,
		"allocation": AMOUNT,
		"reservation": C.RSV_CODE,
	}
	demand, demand_created = _upsert(
		"Demand",
		{"demand_code": C.DEMAND_CODE},
		{
			"title": "National digital health infrastructure upgrade",
			"procuring_entity": pe,
			"owner_org_unit": owner_org_unit,
			"delivery_org_unit": owner_org_unit,
			"requester": C.USER_MEDICAL,
			"need_statement": (
				"Upgrade resilient compute, storage, network and monitoring infrastructure "
				"supporting national digital health services."
			),
			"need_rationale": (
				"Existing infrastructure is approaching capacity and has recurring controller "
				"instability affecting service continuity."
			),
			"expected_outcome": (
				"Reliable and accessible digital clinical services with reduced service "
				"interruption and faster restoration."
			),
			"beneficiaries": (
				"Public health facilities, clinical users and patients using national "
				"digital health services."
			),
			"delivery_location": "National Data Centre and designated health facilities",
			"required_by_date": "2027-09-30",
			"demand_route": "Standard",
			"urgency": "Medium",
			"requester_estimate": AMOUNT,
			"estimate_source": "Indicative market research and current infrastructure assessment",
			"estimate_confidence": "Medium",
			"confirmed_estimate": AMOUNT,
			"currency": "KES",
			"estimate_basis": "Market research and infrastructure assessment",
			"procurement_category": "ICT infrastructure and services",
			"duplicate_assessment": "None found",
			"related_demands_note": "2 infrastructure needs identified",
			"aggregation_treatment": "Aggregation candidate for Planning",
			"aggregation_rationale": "Retain related infrastructure needs for Planning review",
			"status": "Approved",
			"current_stage": "Complete",
			"planning_ready": 1,
			"planning_usage": "Not taken up",
			"approved_baseline_version": 1,
			"approved_baseline_snapshot": json.dumps(snapshot, sort_keys=True),
			"approved_at": APPROVED_AT,
			"fixture_namespace": FIXTURE_NS,
		},
	)
	item_names, items_created = _seed_items(demand)
	strategy_names, strategy_created, plan_name = _seed_strategy(demand)
	treatment_names, treatments_created = _seed_value_treatments(demand, plan_name)
	allocation, allocation_created = _upsert(
		"Demand Funding Allocation",
		{"demand": demand, "budget_line": budget_line},
		{
			"budget": budget,
			"allocation_amount": AMOUNT,
			"currency": "KES",
			"matching_source": "Automatic",
			"funds_check_result": "Sufficient",
			"funds_check_at": BUDGET_CONFIRMED_AT,
			"bo_confirmation_status": "Confirmed",
			"bo_confirmed_by": _existing_user(BUDGET_OFFICER_USER),
			"bo_confirmed_at": BUDGET_CONFIRMED_AT,
			"funding_reservation": reservation,
			"reservation_status": reservation_row.status,
			"availability_before": 480_000_000,
			"availability_after": 25_000_000,
			"fixture_namespace": FIXTURE_NS,
		},
	)

	# Attach existing RSV identity — never create a second reservation.
	frappe.db.set_value(
		"Funding Reservation",
		reservation,
		{
			"demand_code": C.DEMAND_CODE,
			"demand_title": "National digital health infrastructure upgrade",
		},
		update_modified=False,
	)

	if commit:
		frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"demand": demand,
		"demand_code": C.DEMAND_CODE,
		"items": item_names,
		"strategy_references": strategy_names,
		"value_treatments": treatment_names,
		"allocation": allocation,
		"reservation": reservation,
		"created": (
			int(demand_created)
			+ items_created
			+ strategy_created
			+ treatments_created
			+ int(allocation_created)
		),
		"updated": (
			int(not demand_created)
			+ (len(item_names) - items_created)
			+ (len(strategy_names) - strategy_created)
			+ (len(treatment_names) - treatments_created)
			+ int(not allocation_created)
		),
	}


# --- DEM-SEED-002: Returned shortfall Demand ---------------------------------

RETURNED_AMOUNT = 95_000_000
RETURNED_AVAILABLE = 80_000_000
RETURNED_SHORTFALL = 15_000_000
RETURNED_REASON = (
	"The proposed scope exceeds available funding by KES 15,000,000. "
	"Revise the number of participants or provide a phased delivery approach."
)
RETURN_AT = "2027-08-18 11:00:00"
ENRICHED_AT = "2027-08-17 10:00:00"
SUPPORTED_AT = "2027-08-16 10:00:00"
BUSINESS_APPROVER = "moh.business.approver@example.test"

RETURNED_ITEMS = (
	{
		"item_code": allocate_item_code(C.DEMAND_CODE_RETURNED, 1),
		"description": "Digital health technical staff certification programme",
		"amount": RETURNED_AMOUNT,
	},
)


def _seed_returned_items(demand: str) -> tuple[list[str], int]:
	canonical = {spec["item_code"] for spec in RETURNED_ITEMS}
	for row in frappe.get_all(
		"Demand Item",
		filters={"demand": demand},
		fields=["name", "item_code"],
	):
		if row.item_code not in canonical:
			frappe.delete_doc(
				"Demand Item", row.name, force=True, ignore_permissions=True
			)
	names: list[str] = []
	created = 0
	for spec in RETURNED_ITEMS:
		name, was_created = _upsert(
			"Demand Item",
			{"item_code": spec["item_code"]},
			{
				"demand": demand,
				"description": spec["description"],
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": spec["amount"],
				"confirmed_quantity": 1,
				"confirmed_uom": "Lot",
				"confirmed_estimate": spec["amount"],
				"remaining_quantity": 1,
				"remaining_amount": spec["amount"],
				"currency": "KES",
				"fixture_namespace": FIXTURE_NS,
			},
		)
		names.append(name)
		created += int(was_created)
	return names, created


def _seed_returned_strategy(demand: str) -> tuple[str, bool]:
	target = _target(C.TGT_SKILLS_2029)
	path = (
		f"{C.PLAN_TITLE} > Digital Health Capability > Workforce capability > "
		"Digital-health technical staff certification"
	)
	name, was_created = _upsert(
		"Demand Strategy Reference",
		{"demand": demand, "reference_type": "Primary"},
		{
			"plan": target.plan_version,
			"plan_version_id": target.plan_version,
			"target_id": target.name,
			"target_code": target.target_code,
			"target_name": target.title,
			"hierarchy_path": path,
			"snapshot_label": target.title,
			"selection_source": "Canonical fixture",
			"confirmed_by": _existing_user(PAA_USER),
			"confirmed_at": ENRICHED_AT,
			"confirmation_reason": (
				"Certification programme directly advances the digital-health "
				"technical staff skills target"
			),
			"fixture_namespace": FIXTURE_NS,
		},
	)
	# Exactly one Primary; drop stray Supporting refs if any.
	for extra in frappe.get_all(
		"Demand Strategy Reference",
		filters={"demand": demand, "reference_type": ["!=", "Primary"]},
		pluck="name",
	):
		frappe.delete_doc(
			"Demand Strategy Reference", extra, force=True, ignore_permissions=True
		)
	return name, was_created


def _seed_returned_decisions(demand: str) -> list[str]:
	"""Audit trail: Support → Enrich → Budget Return (shortfall)."""
	specs = (
		{
			"stage": "Business Review",
			"decision": "Support",
			"actor": _existing_user(BUSINESS_APPROVER) or "Administrator",
			"actor_role": "Business Approver",
			"decided_at": SUPPORTED_AT,
			"comment": "Business need supported for workforce certification",
			"reason": None,
		},
		{
			"stage": "Procurement Enrichment",
			"decision": "Send for budget confirmation",
			"actor": _existing_user(PAA_USER) or "Administrator",
			"actor_role": "Procurement Approval Authority",
			"decided_at": ENRICHED_AT,
			"comment": "Strategy assigned; send for Budget confirmation",
			"reason": None,
		},
		{
			"stage": "Budget Confirmation",
			"decision": "Return",
			"actor": _existing_user(BUDGET_OFFICER_USER) or "Administrator",
			"actor_role": "Budget Officer",
			"decided_at": RETURN_AT,
			"comment": "Insufficient Funding exception detected",
			"reason": RETURNED_REASON,
		},
	)
	names: list[str] = []
	for spec in specs:
		name, _ = _upsert(
			"Demand Decision",
			{
				"demand": demand,
				"stage": spec["stage"],
				"decision": spec["decision"],
				"fixture_namespace": FIXTURE_NS,
			},
			{
				"actor": spec["actor"],
				"actor_role": spec["actor_role"],
				"decided_at": spec["decided_at"],
				"comment": spec["comment"],
				"reason": spec["reason"],
				"decision_input_snapshot": frappe.as_json(
					{
						"estimate": RETURNED_AMOUNT,
						"available_funding": RETURNED_AVAILABLE,
						"shortfall": RETURNED_SHORTFALL,
						"budget_line": C.BL_HWD_2027,
					}
				),
			},
		)
		names.append(name)
	return names


def _seed_returned_exception(demand: str) -> str:
	"""Resolved Insufficient Funding exception — detected, then returned."""
	name, _ = _upsert(
		"Funding Exception",
		{
			"demand": demand,
			"exception_type": "Insufficient Funding",
			"fixture_namespace": FIXTURE_NS,
		},
		{
			"demand_code": C.DEMAND_CODE_RETURNED,
			"status": "Resolved",
			"current_owner": _existing_user(C.USER_PUBLIC),
			"diagnostic_context": frappe.as_json(
				{
					"available_funding": RETURNED_AVAILABLE,
					"estimate": RETURNED_AMOUNT,
					"shortfall": RETURNED_SHORTFALL,
					"budget_line": C.BL_HWD_2027,
				}
			),
			"resolution": "Returned to requester",
			"resolution_reason": RETURNED_REASON,
			"resolved_by": _existing_user(BUDGET_OFFICER_USER),
			"resolved_at": RETURN_AT,
		},
	)
	# No open exceptions for this Demand.
	for open_name in frappe.get_all(
		"Funding Exception",
		filters={
			"demand": demand,
			"status": ["in", ["Open", "In Progress"]],
			"name": ["!=", name],
		},
		pluck="name",
	):
		frappe.db.set_value(
			"Funding Exception",
			open_name,
			{"status": "Cancelled"},
			update_modified=False,
		)
	return name


def upsert_returned_shortfall_demand(*, commit: bool = True) -> dict[str, Any]:
	"""DEM-SEED-002 — idempotent `DMD-MOH-2027-019` Returned shortfall fixture."""
	frappe.only_for(("System Manager", "Administrator"))

	pe = _required("Procuring Entity", {"entity_code": C.PE_MOH}, C.PE_MOH)
	owner_org_unit = _required(
		"Organisation Unit",
		{"unit_code": C.OU_DIR_HRMD},
		C.OU_DIR_HRMD,
	)
	if not frappe.db.exists("User", C.USER_PUBLIC):
		raise frappe.ValidationError(
			f"DEM-SEED-002 requires requester {C.USER_PUBLIC}"
		)

	budget_line = _required(
		"Budget Line",
		{"generated_reference": C.BL_HWD_2027},
		C.BL_HWD_2027,
	)
	budget = frappe.db.get_value("Budget Line", budget_line, "budget")
	line_meta = frappe.db.get_value(
		"Budget Line",
		budget_line,
		["approved_amount", "amount_reserved", "amount_committed"],
		as_dict=True,
	) or {}
	available = (
		flt(line_meta.get("approved_amount"))
		- flt(line_meta.get("amount_reserved"))
		- flt(line_meta.get("amount_committed"))
	)
	if available < RETURNED_AVAILABLE:
		# Restore canonical headroom without creating negative availability.
		frappe.db.set_value(
			"Budget Line",
			budget_line,
			{
				"approved_amount": (
					flt(line_meta.get("amount_reserved"))
					+ flt(line_meta.get("amount_committed"))
					+ RETURNED_AVAILABLE
				)
			},
			update_modified=False,
		)
		available = RETURNED_AVAILABLE

	demand, demand_created = _upsert(
		"Demand",
		{"demand_code": C.DEMAND_CODE_RETURNED},
		{
			"title": "Digital health technical staff certification programme",
			"procuring_entity": pe,
			"owner_org_unit": owner_org_unit,
			"delivery_org_unit": owner_org_unit,
			"requester": C.USER_PUBLIC,
			"current_owner": C.USER_PUBLIC,
			"need_statement": (
				"Deliver a certification programme for digital-health technical staff "
				"supporting national EMR operations."
			),
			"need_rationale": (
				"Workforce certification is required to operate and sustain upgraded "
				"digital health infrastructure."
			),
			"expected_outcome": (
				"Certified digital-health technical staff able to support clinical "
				"information systems."
			),
			"beneficiaries": "Digital-health technical staff and public health facilities",
			"delivery_location": "Ministry of Health training centres",
			"required_by_date": "2027-12-31",
			"demand_route": "Standard",
			"urgency": "Medium",
			"requester_estimate": RETURNED_AMOUNT,
			"estimate_source": "Training provider quotations and cohort sizing",
			"estimate_confidence": "Medium",
			"confirmed_estimate": RETURNED_AMOUNT,
			"currency": "KES",
			"estimate_basis": "Quoted programme cost for the proposed cohort",
			"procurement_category": "Training and professional services",
			"duplicate_assessment": "None found",
			"aggregation_treatment": "Proceed independently",
			"aggregation_rationale": "Distinct workforce certification Demand",
			"status": "Returned",
			"current_stage": "Request Preparation",
			"planning_ready": 0,
			"planning_usage": "Not taken up",
			"fixture_namespace": FIXTURE_NS,
		},
	)

	item_names, items_created = _seed_returned_items(demand)
	strategy_name, strategy_created = _seed_returned_strategy(demand)
	allocation, allocation_created = _upsert(
		"Demand Funding Allocation",
		{"demand": demand, "budget_line": budget_line},
		{
			"budget": budget,
			"allocation_amount": RETURNED_AMOUNT,
			"currency": "KES",
			"matching_source": "Automatic",
			"funds_check_result": "Insufficient",
			"funds_check_at": RETURN_AT,
			"bo_confirmation_status": "Returned",
			"bo_confirmed_by": None,
			"bo_confirmed_at": None,
			"funding_reservation": None,
			"reservation_status": None,
			"availability_before": available,
			"availability_after": available,
			"fixture_namespace": FIXTURE_NS,
		},
	)
	# Explicitly clear any reservation link that may have been set earlier.
	frappe.db.set_value(
		"Demand Funding Allocation",
		allocation,
		{"funding_reservation": None, "reservation_status": None},
		update_modified=False,
	)
	exception = _seed_returned_exception(demand)
	decisions = _seed_returned_decisions(demand)

	rsv_for_code = frappe.db.count(
		"Funding Reservation", {"demand_code": C.DEMAND_CODE_RETURNED}
	)
	if rsv_for_code:
		raise frappe.ValidationError(
			"DEM-SEED-002 must not create or attach a Funding Reservation for "
			f"{C.DEMAND_CODE_RETURNED}"
		)

	if commit:
		frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"demand": demand,
		"demand_code": C.DEMAND_CODE_RETURNED,
		"items": item_names,
		"strategy_reference": strategy_name,
		"allocation": allocation,
		"funding_exception": exception,
		"decisions": decisions,
		"shortfall": RETURNED_SHORTFALL,
		"available_funding": available,
		"reservation": None,
		"created": int(demand_created)
		+ items_created
		+ int(strategy_created)
		+ int(allocation_created),
	}


# --- DEM-SEED-003: County Draft Demand ---------------------------------------

COUNTY_AMOUNT = 24_000_000
COUNTY_ITEMS = (
	{
		"item_code": allocate_item_code(C.DEMAND_CODE_COUNTY, 1),
		"description": "Solar-powered vaccine refrigerators for rural health facilities",
		"amount": COUNTY_AMOUNT,
	},
)


def upsert_county_draft_demand(*, commit: bool = True) -> dict[str, Any]:
	"""DEM-SEED-003 — idempotent `DMD-CGK-2027-006` Draft isolation fixture."""
	frappe.only_for(("System Manager", "Administrator"))

	pe = _required("Procuring Entity", {"entity_code": C.PE_CGKIS}, C.PE_CGKIS)
	owner_org_unit = _required(
		"Organisation Unit",
		{"unit_code": C.OU_CGK_HEALTH},
		C.OU_CGK_HEALTH,
	)
	if not frappe.db.exists("User", C.USER_KISUMU_OFFICER):
		raise frappe.ValidationError(
			f"DEM-SEED-003 requires requester {C.USER_KISUMU_OFFICER}"
		)

	demand, demand_created = _upsert(
		"Demand",
		{"demand_code": C.DEMAND_CODE_COUNTY},
		{
			"title": "Solar-powered vaccine refrigerators for rural health facilities",
			"procuring_entity": pe,
			"owner_org_unit": owner_org_unit,
			"delivery_org_unit": owner_org_unit,
			"requester": C.USER_KISUMU_OFFICER,
			"current_owner": C.USER_KISUMU_OFFICER,
			"need_statement": (
				"Procure solar-powered vaccine refrigerators to strengthen cold-chain "
				"capacity in rural health facilities."
			),
			"need_rationale": (
				"Rural facilities experience power interruptions that put vaccine "
				"stocks at risk."
			),
			"expected_outcome": (
				"Reliable vaccine cold storage at designated rural health facilities."
			),
			"beneficiaries": "Rural health facilities and immunisation programme clients",
			"delivery_location": "Designated rural health facilities in Kisumu County",
			"required_by_date": "2028-03-31",
			"demand_route": "Standard",
			"urgency": "Medium",
			"requester_estimate": COUNTY_AMOUNT,
			"estimate_source": "Indicative supplier quotations",
			"estimate_confidence": "Low",
			"confirmed_estimate": None,
			"currency": "KES",
			"estimate_basis": None,
			"procurement_category": None,
			"status": "Draft",
			"current_stage": "Request Preparation",
			"planning_ready": 0,
			"planning_usage": "Not taken up",
			"fixture_namespace": FIXTURE_NS,
		},
	)

	canonical = {spec["item_code"] for spec in COUNTY_ITEMS}
	for row in frappe.get_all(
		"Demand Item",
		filters={"demand": demand},
		fields=["name", "item_code"],
	):
		if row.item_code not in canonical:
			frappe.delete_doc(
				"Demand Item", row.name, force=True, ignore_permissions=True
			)
	item_names: list[str] = []
	items_created = 0
	for spec in COUNTY_ITEMS:
		name, was_created = _upsert(
			"Demand Item",
			{"item_code": spec["item_code"]},
			{
				"demand": demand,
				"description": spec["description"],
				"quantity": 1,
				"uom": "Lot",
				"requester_estimate": spec["amount"],
				"confirmed_quantity": None,
				"confirmed_uom": None,
				"confirmed_estimate": None,
				"remaining_quantity": 1,
				"remaining_amount": spec["amount"],
				"currency": "KES",
				"fixture_namespace": FIXTURE_NS,
			},
		)
		item_names.append(name)
		items_created += int(was_created)

	# Isolation: strip Strategy / Budget / exception residues if re-seeded wrongly.
	for doctype in (
		"Demand Strategy Reference",
		"Demand Value Treatment",
		"Demand Funding Allocation",
		"Funding Exception",
	):
		for name in frappe.get_all(doctype, filters={"demand": demand}, pluck="name"):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	if frappe.db.count("Funding Reservation", {"demand_code": C.DEMAND_CODE_COUNTY}):
		raise frappe.ValidationError(
			"DEM-SEED-003 must not attach a Funding Reservation for "
			f"{C.DEMAND_CODE_COUNTY}"
		)

	if commit:
		frappe.db.commit()
	return {
		"ok": True,
		"fixture_namespace": FIXTURE_NS,
		"demand": demand,
		"demand_code": C.DEMAND_CODE_COUNTY,
		"items": item_names,
		"strategy_references": [],
		"allocation": None,
		"reservation": None,
		"created": int(demand_created) + items_created,
	}
