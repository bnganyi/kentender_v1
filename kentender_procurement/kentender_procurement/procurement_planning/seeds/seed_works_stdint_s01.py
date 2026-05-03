# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINT-WORKS-S01 deterministic chain through package lines and release-to-tender (doc 3 sec. 7–8, 14–15, 18.1, 26).

Creates a **Draft** procurement plan (same workflow bootstrap as F1), **Works** procurement template with STD default,
``PKG-MOH-2026-001`` (when slot is free or already compatible), and **two** package lines with
stable ``package_line_code`` values ``PKGL-MOH-2026-001-01`` / ``PKGL-MOH-2026-001-02``.

**Plan code:** ``PLAN-MOH-2026-WORKS-S01`` is used as the doc §12 ``PLAN-MOH-2026`` equivalent so this
seed can coexist with F1's ``PP-MOH-2026`` plan on the same site.

**Demands:** v1 enforces one active package line per demand (``ProcurementPackageLine``), so line 1 uses
``DEM-MOH-WORKS-2026-001`` and line 2 uses ``DEM-MOH-WORKS-2026-002`` (doc §8 line-1 demand code plus a
second deterministic peer). Both link to ``BL-MOH-2026-001`` and inherit strategy context from the
budget line.

**Budget:** doc §14 totals (95M / 68M+27M) require sufficient ``amount_allocated`` on the budget line;
this seed **raises** ``BL-MOH-2026-001`` allocation when needed (Administrator-only ``run()``).

**Doc 3 §16–17 / §26 order:** Procurement plan and planning template shell are created first; the STD POC row
is imported only via ``tender_management.services.std_template_loader.upsert_std_template``, then
``works_std_seed_requirements.verify_std_template_doc3_section_16`` enforces §16; finally
``Procurement Template.default_std_template`` is set to the POC code (§17 mapping) before the package.

**Doc 3 §18.1:** After lines and roll-up, the seed advances the plan and package through
``procurement_planning.api.workflow`` (``complete_package`` → ``submit_package`` → ``approve_package``,
``submit_plan`` → ``approve_plan``, ``mark_ready_for_tender``, ``release_package_to_tender``). Release uses
the hook path into ``release_procurement_package_to_tender`` (no direct tender ``insert`` in seed). Idempotent
when the package is already ``Released to Tender``.

**Doc 3 §18.2:** The transitional direct-tender seed is **not** implemented; B3/C3 provide the service path only.
See ``procurement_planning/seeds/README.md`` in this package.

**Doc 3 §20 / §28–29:** After release, ``_apply_works_s01_sample_officer_completion`` merges **labelled** sample
officer fields into ``configuration_json`` (not Planning authority data), including flat keys needed for STD
validation after ``generate_sample_boq`` (doc 3 §28–29 smoke). See ``works_stdint_s01_verification``.
**Doc 5 §25 / WH-013:** §29 smoke ends with ``run_works_tender_stage_hardening`` (no second call from ``run()``).

Run::

	bench --site <site> execute kentender_procurement.procurement_planning.seeds.seed_works_stdint_s01.run
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt

from kentender_core.seeds import constants as C
from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	U_REQ,
	_fin_approve,
	_hod_approve,
	_insert_demand,
	_new_demand_dict,
	_submit,
	ensure_budget_line_prerequisites,
	ensure_core_prerequisites,
)
from kentender_procurement.procurement_planning.api import workflow as pp_workflow
from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	recompute_plan_total_planned_value,
)
from kentender_procurement.tender_management.services.officer_guided_field_registry import (
	hydrate_officer_guided_fields_from_configuration,
)
from kentender_procurement.procurement_planning.seeds.works_std_seed_requirements import (
	verify_std_template_doc3_section_16,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.procurement_planning.seeds.works_stdint_s01_verification import (
	gather_doc3_section_28_checks,
	run_doc3_section_29_smoke,
)

# Doc 3 §8 / §12–15 (plan code adapted — see module docstring).
SCENARIO_CODE = "STDINT-WORKS-S01"
PLAN_CODE = "PLAN-MOH-2026-WORKS-S01"
PLAN_NAME = "Ministry of Health Procurement Plan 2026/2027 (WORKS S01)"
TPL_CODE = "PTPL-WORKS-OPEN-BLDG-POC"
TPL_NAME = "Works Open Tender Building/Civil Procurement Template"
PKG_CODE = "PKG-MOH-2026-001"
PKG_NAME = "District Hospital Renovation Works"
PKG_DESCRIPTION = (
	"Renovation of outpatient block, ward block, drainage, roofing, finishes, and associated "
	"external works at Makutano District Hospital"
)
LINE_CODE_1 = "PKGL-MOH-2026-001-01"
LINE_CODE_2 = "PKGL-MOH-2026-001-02"
DEMAND_1 = "DEM-MOH-WORKS-2026-001"
DEMAND_2 = "DEM-MOH-WORKS-2026-002"
BL_CODE = "BL-MOH-2026-001"
PKG_ESTIMATED = 95_000_000.0
LINE1_AMOUNT = 68_000_000.0
LINE2_AMOUNT = 27_000_000.0

# Doc 3 §20 / §28 — deterministic sample values (officer POC smoke; not upstream planning).
_SEED_SAMPLE_OFFICER_LABEL = (
	"Sample officer completion (doc 3 §20, §28) — NOT Planning authority data. Scenario STDINT-WORKS-S01."
)
_SEED_SAMPLE_OFFICER_APPLIED_KEY = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_APPLIED"
_SEED_SAMPLE_OFFICER_LABEL_KEY = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_LABEL"
_SAMPLE_OFFICER_MERGE_VERSION_KEY = "SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_MERGE_VERSION"
_SAMPLE_OFFICER_MERGE_VERSION = 3
_SAMPLE_OFFICER_FLAT_KEYS: dict[str, Any] = {
	"DATES.PUBLICATION_DATE": "2026-06-02",
	"DATES.CLARIFICATION_DEADLINE": "2026-06-20 17:00:00",
	"DATES.SUBMISSION_DEADLINE": "2026-07-15 10:00:00",
	"DATES.OPENING_DATETIME": "2026-07-15 14:00:00",
	"DATES.TENDER_VALIDITY_DAYS": 90,
	"DATES.SITE_VISIT_REQUIRED": 1,
	"DATES.SITE_VISIT_DATE": "2026-06-25 09:00:00",
	"DATES.SITE_VISIT_LOCATION": "Makutano District Hospital main gate (seed sample)",
	"DATES.PRE_TENDER_MEETING_REQUIRED": 1,
	"DATES.PRE_TENDER_MEETING_DATE": "2026-06-18 11:00:00",
	"DATES.PRE_TENDER_MEETING_LOCATION": "MOH Procurement Boardroom (seed sample)",
	"SECURITY.TENDER_SECURITY_MODE": "TENDER_SECURITY",
	"SECURITY.TENDER_SECURITY_AMOUNT": 500_000.0,
	"SECURITY.TENDER_SECURITY_CURRENCY": "KES",
	"PARTICIPATION.JV_ALLOWED": 1,
	"PARTICIPATION.MAX_JV_MEMBERS": 3,
	"QUALIFICATION.MIN_AVERAGE_ANNUAL_TURNOVER": 50_000_000.0,
	"WORKS.DAYWORKS_INCLUDED": 1,
	"WORKS.PROVISIONAL_SUMS_INCLUDED": 1,
	# §28 validation (RULE_REQUIRED_CORE_TENDER_IDENTITY / …) — neutral copy; not STD POC sample_tender narrative.
	"TENDER.PROCURING_ENTITY_ADDRESS": (
		"Ministry of Health, Afya House, Cathedral Road, P.O. Box 30016–00100, Nairobi, Kenya (WORKS S01 seed)"
	),
	"TENDER.PROCURING_ENTITY_EMAIL": "procurement@moh.go.ke",
	"TENDER.CONTRACT_DESCRIPTION": (
		"District hospital renovation works: outpatient block, ward block, drainage, roofing, finishes, "
		"and associated external works (WORKS S01 seed verification)."
	),
	"TENDER.WORKS_LOCATION": "Makutano District Hospital site, seed scenario STDINT-WORKS-S01",
	"QUALIFICATION.MIN_LIQUID_ASSETS": 25_000_000.0,
	"QUALIFICATION.SIMILAR_CONTRACT_COUNT": 2,
	"QUALIFICATION.SIMILAR_CONTRACT_MIN_VALUE": 80_000_000.0,
	"QUALIFICATION.KEY_PERSONNEL_REQUIRED": 1,
	"QUALIFICATION.EQUIPMENT_REQUIRED": 1,
	"QUALIFICATION.BENEFICIAL_OWNERSHIP_REQUIRED": 1,
	"QUALIFICATION.NCA_REGISTRATION_REQUIRED": 1,
	"QUALIFICATION.TAX_COMPLIANCE_REQUIRED": 1,
	"WORKS.SCOPE_SUMMARY": (
		"Renovation of outpatient and ward blocks, drainage, roofing, finishes, and external works "
		"at Makutano District Hospital (WORKS S01 seed)."
	),
	"WORKS.SPECIFICATION_SUMMARY": (
		"Execution per approved drawings, specifications, applicable building standards, and contract "
		"instructions (WORKS S01 seed verification)."
	),
	"WORKS.BOQ_REQUIRED": 1,
	"CONTRACT.ENGINEER_OR_PROJECT_MANAGER": (
		"MOH-appointed Engineer / Project Manager (WORKS S01 seed verification)"
	),
	"CONTRACT.DEFECTS_LIABILITY_PERIOD_MONTHS": 12,
	"CONTRACT.LIQUIDATED_DAMAGES_RATE": (
		"0.05 percent of contract price per day of delay, subject to the maximum stated in the SCC (seed)"
	),
	"CONTRACT.PAYMENT_TERMS": (
		"Interim payments against certified works, retention, taxes, and approved certificates (seed)."
	),
	"CONTRACT.INSURANCE_REQUIREMENTS": (
		"Contractor maintains works, equipment, third-party liability, workers compensation, and other "
		"contract-required insurance (seed)."
	),
	"CONTRACT.RETENTION_PERCENTAGE": 10,
	"CONTRACT.DISPUTE_RESOLUTION_FORUM": "ADJUDICATION_THEN_ARBITRATION",
	"CONTRACT.COMPLETION_PERIOD_MONTHS": 12,
	"CONTRACT.ADVANCE_PAYMENT_ALLOWED": 1,
	"SECURITY.PERFORMANCE_SECURITY_REQUIRED": 1,
	"SECURITY.PERFORMANCE_SECURITY_PERCENTAGE": 10,
	"SECURITY.ADVANCE_PAYMENT_SECURITY_REQUIRED": 1,
	"SECURITY.TENDER_SECURITY_TYPE": "BANK_OR_INSURANCE_GUARANTEE",
	"SECURITY.TENDER_SECURITY_VALIDITY_DAYS_AFTER_TENDER_VALIDITY": 30,
	"SECURITY.TENDER_SECURING_DECLARATION_REQUIRED": 0,
	"SECURITY.RETENTION_MONEY_SECURITY_REQUIRED": 0,
	"LOTS.MULTIPLE_LOTS_ENABLED": 1,
	"LOTS.LOT_EVALUATION_METHOD": "LOT_BY_LOT",
	"LOTS.LOT_AWARD_METHOD": "ONE_OR_MORE_LOTS",
	"ALTERNATIVES.ALTERNATIVE_TENDERS_ALLOWED": 1,
	"ALTERNATIVES.ALTERNATIVE_TENDER_TYPE": "TECHNICAL_ALTERNATIVE_SPECIFIED_PARTS",
	"ALTERNATIVES.ALTERNATIVE_SCOPE_DESCRIPTION": (
		"Alternatives permitted only for roof structure; tenderer must price base design and provide "
		"comparable technical detail (WORKS S01 seed verification)."
	),
}


def _ensure_core_if_needed() -> None:
	if frappe.db.exists("Procuring Entity", C.ENTITY_MOH) and frappe.db.exists("Currency", "KES"):
		return
	ensure_core_prerequisites()


def _ensure_profile_by_code(
	doctype: str,
	*,
	profile_code: str,
	profile_name: str,
	extra_fields: dict,
) -> str:
	name = frappe.db.get_value(doctype, {"profile_code": profile_code}, "name")
	if name:
		return name
	row = {"doctype": doctype, "profile_code": profile_code, "profile_name": profile_name}
	row.update(extra_fields)
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_works_profiles() -> dict[str, str]:
	risk = _ensure_profile_by_code(
		"Risk Profile",
		profile_code="RISK-WORKS-S01",
		profile_name="WORKS S01 Risk",
		extra_fields={
			"risk_level": "Medium",
			"risks": json.dumps([{"risk": "Site disruption", "mitigation": "Phased works"}]),
		},
	)
	kpi = _ensure_profile_by_code(
		"KPI Profile",
		profile_code="KPI-WORKS-S01",
		profile_name="WORKS S01 KPIs",
		extra_fields={"metrics": json.dumps(["Milestone delivery", "Cost variance"])},
	)
	crit = _ensure_profile_by_code(
		"Decision Criteria Profile",
		profile_code="CRIT-WORKS-S01",
		profile_name="WORKS S01 Criteria",
		extra_fields={
			"criteria": json.dumps(
				[
					{"criterion": "Technical", "weight": 60},
					{"criterion": "Price", "weight": 40},
				]
			),
		},
	)
	vm = _ensure_profile_by_code(
		"Vendor Management Profile",
		profile_code="VM-WORKS-S01",
		profile_name="WORKS S01 VM",
		extra_fields={
			"monitoring_rules": json.dumps({"cadence": ["Monthly"]}),
			"escalation_rules": json.dumps({"paths": ["Standard"]}),
		},
	)
	return {
		"risk_profile_id": risk,
		"kpi_profile_id": kpi,
		"decision_criteria_profile_id": crit,
		"vendor_management_profile_id": vm,
	}


def _ensure_bl_capacity(bl_name: str, minimum_allocated: float) -> None:
	row = frappe.db.get_value(
		"Budget Line",
		bl_name,
		["amount_allocated", "amount_reserved", "amount_consumed"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Budget Line {0} not found.").format(bl_name), title=_("WORKS S01 seed"))
	res = flt(row.get("amount_reserved"))
	con = flt(row.get("amount_consumed"))
	alloc = flt(row.get("amount_allocated"))
	need = minimum_allocated + res + con + 1000.0
	if alloc < need:
		frappe.db.set_value("Budget Line", bl_name, "amount_allocated", need, update_modified=False)


def _item_row_works(qty: float, unit_cost: float) -> dict:
	return {
		"item_description": "WORKS S01 seed scope line",
		"category": "Works",
		"uom": "ls",
		"quantity": qty,
		"estimated_unit_cost": unit_cost,
	}


def _ensure_works_demand(*, demand_id: str, title: str, unit_cost: float) -> str:
	name = frappe.db.get_value("Demand", {"demand_id": demand_id}, "name")
	if name:
		st = frappe.db.get_value("Demand", name, "status")
		if st not in ("Approved", "Planning Ready"):
			frappe.throw(
				_("Demand {0} exists but is not Approved/Planning Ready (got {1}).").format(demand_id, st),
				title=_("WORKS S01 seed"),
			)
		return name
	base = _new_demand_dict(
		title=title,
		demand_id=demand_id,
		requested_by=U_REQ,
		demand_type="Planned",
		bl_code=BL_CODE,
		qty=1.0,
		unit_cost=unit_cost,
	)
	base["requisition_type"] = "Works"
	base["items"] = [_item_row_works(1.0, unit_cost)]
	d = _insert_demand(base)
	_submit(d.name)
	_hod_approve(d.name)
	_fin_approve(d.name)
	return d.name


def _assert_package_slot_or_get_name() -> str | None:
	"""Return existing compatible package name, or None if we may create."""
	name = frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "name")
	if not name:
		return None
	tpl = frappe.db.get_value("Procurement Package", name, "template_id")
	cat = (frappe.db.get_value("Procurement Template", tpl, "category") or "").strip().lower()
	method = (frappe.db.get_value("Procurement Package", name, "procurement_method") or "").strip()
	if cat != "works" or method != "Open Tender":
		frappe.throw(
			_(
				"Package code {0} is already used by a non-Works or non-Open-Tender package ({1}). "
				"Resolve manually before running WORKS S01 seed."
			).format(PKG_CODE, name),
			title=_("WORKS S01 seed collision"),
		)
	return name


def _ensure_plan() -> str:
	n = frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name")
	if n:
		return n
	if not frappe.db.exists("Currency", "KES"):
		frappe.throw(_("Currency KES is missing."), title=_("WORKS S01 seed"))
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_name": PLAN_NAME,
			"plan_code": PLAN_CODE,
			"fiscal_year": 2026,
			"procuring_entity": C.ENTITY_MOH,
			"currency": "KES",
			"status": "Draft",
			"is_active": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_template_without_std(profiles: dict[str, str]) -> str:
	"""Procurement Template per doc §26 step 6 — ``default_std_template`` linked after STD import (step 7)."""
	n = frappe.db.get_value("Procurement Template", {"template_code": TPL_CODE}, "name")
	if n:
		frappe.db.set_value(
			"Procurement Template",
			n,
			{
				"category": "Works",
				"default_method": "Open Tender",
				"default_contract_type": "Fixed Price",
			},
			update_modified=False,
		)
		return n
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Template",
			"template_code": TPL_CODE,
			"template_name": TPL_NAME,
			"category": "Works",
			"is_active": 1,
			"applicable_requisition_types": json.dumps(["Works", "Goods", "Services"]),
			"applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
			"default_method": "Open Tender",
			"default_contract_type": "Fixed Price",
			"grouping_strategy": json.dumps({"group_by": []}),
			"threshold_rules": json.dumps([]),
			"planning_lead_days": 45,
			"procurement_cycle_days": 180,
			"override_requires_justification": 1,
			"high_risk_escalation_required": 0,
			"schedule_required": 0,
			**profiles,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _link_std_mapping(template_name: str, std_template_name: str) -> None:
	"""Doc §17: planning template ``default_std_template`` → POC STD row."""
	frappe.db.set_value(
		"Procurement Template",
		template_name,
		"default_std_template",
		std_template_name,
		update_modified=False,
	)


def _ensure_package(plan_name: str, template_name: str) -> str:
	existing = _assert_package_slot_or_get_name()
	if existing:
		pn = frappe.db.get_value("Procurement Package", existing, "plan_id")
		if pn != plan_name:
			frappe.throw(
				_("Existing {0} is on a different plan than {1}.").format(PKG_CODE, PLAN_CODE),
				title=_("WORKS S01 seed"),
			)
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Package",
			"package_code": PKG_CODE,
			"package_name": PKG_NAME,
			"planner_notes": PKG_DESCRIPTION,
			"plan_id": plan_name,
			"template_id": template_name,
			"procurement_method": "Open Tender",
			"contract_type": "Fixed Price",
			"currency": "KES",
			"estimated_value": PKG_ESTIMATED,
			"status": "Draft",
			"is_active": 1,
			"risk_profile_id": frappe.db.get_value("Procurement Template", template_name, "risk_profile_id"),
			"kpi_profile_id": frappe.db.get_value("Procurement Template", template_name, "kpi_profile_id"),
			"decision_criteria_profile_id": frappe.db.get_value(
				"Procurement Template", template_name, "decision_criteria_profile_id"
			),
			"vendor_management_profile_id": frappe.db.get_value(
				"Procurement Template", template_name, "vendor_management_profile_id"
			),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_line(
	package_name: str,
	*,
	package_line_code: str,
	demand_name: str,
	budget_line_name: str,
	amount: float,
) -> str:
	n = frappe.db.get_value(
		"Procurement Package Line",
		{"package_line_code": package_line_code},
		"name",
	)
	if n:
		pkg = frappe.db.get_value("Procurement Package Line", n, "package_id")
		if pkg != package_name:
			frappe.throw(
				_("Package line code {0} already exists on another package.").format(package_line_code),
				title=_("WORKS S01 seed"),
			)
		return n
	ln = frappe.get_doc(
		{
			"doctype": "Procurement Package Line",
			"package_id": package_name,
			"package_line_code": package_line_code,
			"demand_id": demand_name,
			"budget_line_id": budget_line_name,
			"amount": amount,
			"is_active": 1,
		}
	)
	ln.insert(ignore_permissions=True)
	return ln.name


def _find_non_cancelled_tender_for_package(package_name: str) -> str | None:
	rows = frappe.get_all(
		"Procurement Tender",
		filters={"procurement_package": package_name, "tender_status": ("!=", "Cancelled")},
		pluck="name",
		limit=1,
	)
	return rows[0] if rows else None


def _ensure_works_s01_released_to_tender(*, plan_name: str, package_name: str) -> dict[str, Any]:
	"""Doc 3 §18.1: plan Approved, package Ready → hook release → Released to Tender. Idempotent."""
	pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	if pkg_st == "Released to Tender":
		tn = _find_non_cancelled_tender_for_package(package_name)
		if not tn:
			frappe.throw(
				_("Package {0} is Released to Tender but no active Procurement Tender is linked.").format(
					package_name
				),
				title=_("WORKS S01 seed"),
			)
		plan_st = (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip()
		return {
			"release_skipped": True,
			"tender": tn,
			"package_status": pkg_st,
			"plan_status": plan_st,
		}

	while True:
		pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
		if pkg_st in ("Draft", "Returned"):
			pp_workflow.complete_package(package_name)
			continue
		if pkg_st == "Completed":
			pp_workflow.submit_package(package_name)
			continue
		if pkg_st == "Submitted":
			pp_workflow.approve_package(package_name)
			continue
		break

	pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	if pkg_st != "Approved":
		frappe.throw(
			_("WORKS S01 package must reach Approved before plan submit (got {0}).").format(pkg_st or "—"),
			title=_("WORKS S01 seed"),
		)

	while True:
		plan_st = (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip()
		if plan_st in ("Draft", "Returned"):
			pp_workflow.submit_plan(plan_name)
			continue
		if plan_st == "Submitted":
			pp_workflow.approve_plan(plan_name)
			continue
		break

	plan_st = (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip()
	if plan_st != "Approved":
		frappe.throw(
			_("WORKS S01 plan must be Approved before release (got {0}).").format(plan_st or "—"),
			title=_("WORKS S01 seed"),
		)

	pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	if pkg_st == "Approved":
		pp_workflow.mark_ready_for_tender(package_name)
		pkg_st = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()

	if pkg_st != "Ready for Tender":
		frappe.throw(
			_("WORKS S01 package must be Ready for Tender before release (got {0}).").format(pkg_st or "—"),
			title=_("WORKS S01 seed"),
		)

	pp_workflow.release_package_to_tender(package_name)

	pkg_final = (frappe.db.get_value("Procurement Package", package_name, "status") or "").strip()
	if pkg_final != "Released to Tender":
		frappe.throw(
			_("WORKS S01 release did not set package to Released to Tender (got {0}).").format(pkg_final or "—"),
			title=_("WORKS S01 seed"),
		)
	tn = _find_non_cancelled_tender_for_package(package_name)
	if not tn:
		frappe.throw(_("No Procurement Tender linked after release."), title=_("WORKS S01 seed"))

	return {
		"release_skipped": False,
		"tender": tn,
		"package_status": pkg_final,
		"plan_status": (frappe.db.get_value("Procurement Plan", plan_name, "status") or "").strip(),
	}


def _apply_works_s01_sample_officer_completion(tender_name: str) -> bool:
	"""Doc 3 §20 / §28: merge labelled sample officer fields into ``configuration_json``. Idempotent by merge version."""
	if not tender_name or not frappe.db.exists("Procurement Tender", tender_name):
		return False
	# WH-013: after §29 ``load_sample_tender``, snapshot exists and required forms are full primary set — do not
	# re-merge officer flat keys (would confuse doc 3 §20 idempotency vs ``configuration_json`` from sample).
	td_gate = frappe.get_doc("Procurement Tender", tender_name)
	if (frappe.db.get_value("Procurement Tender", tender_name, "works_hardening_snapshot_hash") or "").strip():
		if len(td_gate.get("required_forms") or []) >= 15:
			return False
	raw = frappe.db.get_value("Procurement Tender", tender_name, "configuration_json") or "{}"
	try:
		existing: dict[str, Any] = json.loads(raw) if raw else {}
	except json.JSONDecodeError:
		existing = {}
	ver = int(existing.get(_SAMPLE_OFFICER_MERGE_VERSION_KEY) or 0)
	if ver >= _SAMPLE_OFFICER_MERGE_VERSION:
		return False

	merged: dict[str, Any] = {**existing, **_SAMPLE_OFFICER_FLAT_KEYS}
	merged[_SEED_SAMPLE_OFFICER_LABEL_KEY] = _SEED_SAMPLE_OFFICER_LABEL
	merged[_SEED_SAMPLE_OFFICER_APPLIED_KEY] = 1
	merged[_SAMPLE_OFFICER_MERGE_VERSION_KEY] = _SAMPLE_OFFICER_MERGE_VERSION

	doc = frappe.get_doc("Procurement Tender", tender_name)
	hydrate_officer_guided_fields_from_configuration(doc, merged)
	doc.configuration_json = json.dumps(merged, indent=2, ensure_ascii=False)
	doc.save(ignore_permissions=True)
	return True


def run() -> dict[str, Any]:
	"""Idempotent WORKS S01 seed through package lines; returns summary keys."""
	frappe.only_for(("System Manager", "Administrator"))
	_ensure_core_if_needed()
	ensure_budget_line_prerequisites()
	bl_name = frappe.db.get_value("Budget Line", {"budget_line_code": BL_CODE}, "name")
	if not bl_name:
		frappe.throw(_("Budget line {0} missing.").format(BL_CODE), title=_("WORKS S01 seed"))

	# Finance reservations use line demand totals; keep headroom vs package header.
	_need = max(PKG_ESTIMATED, LINE1_AMOUNT + LINE2_AMOUNT) * 1.05
	_ensure_bl_capacity(bl_name, _need)

	profiles = _ensure_works_profiles()
	plan_name = _ensure_plan()
	template_name = _ensure_template_without_std(profiles)

	upsert_std_template()
	std_row = verify_std_template_doc3_section_16(TEMPLATE_CODE)
	_link_std_mapping(template_name, std_row)

	package_name = _ensure_package(plan_name, template_name)

	d1 = _ensure_works_demand(
		demand_id=DEMAND_1,
		title="District Hospital Renovation — building envelope",
		unit_cost=LINE1_AMOUNT,
	)
	d2 = _ensure_works_demand(
		demand_id=DEMAND_2,
		title="District Hospital Renovation — drainage and external",
		unit_cost=LINE2_AMOUNT,
	)

	_ensure_line(
		package_name,
		package_line_code=LINE_CODE_1,
		demand_name=d1,
		budget_line_name=bl_name,
		amount=LINE1_AMOUNT,
	)
	_ensure_line(
		package_name,
		package_line_code=LINE_CODE_2,
		demand_name=d2,
		budget_line_name=bl_name,
		amount=LINE2_AMOUNT,
	)

	frappe.db.set_value(
		"Procurement Package",
		package_name,
		"estimated_value",
		PKG_ESTIMATED,
		update_modified=False,
	)
	recompute_plan_total_planned_value(plan_name)

	release_info = _ensure_works_s01_released_to_tender(plan_name=plan_name, package_name=package_name)
	tn = release_info.get("tender")
	sample_officer = _apply_works_s01_sample_officer_completion(tn) if tn else False

	section_28: dict[str, Any] = {"checks": [], "all_passed": False}
	section_29: dict[str, Any] = {"ok": False, "skipped": True}
	if tn:
		section_28 = gather_doc3_section_28_checks(
			tender_name=tn,
			package_name=package_name,
			plan_name=plan_name,
			budget_line_name=bl_name,
			demand_ids=(DEMAND_1, DEMAND_2),
			std_template_code=TEMPLATE_CODE,
		)
		if section_28.get("all_passed"):
			section_29 = run_doc3_section_29_smoke(tn)

	return {
		"ok": True,
		"scenario": SCENARIO_CODE,
		"plan": plan_name,
		"plan_code": PLAN_CODE,
		"template": template_name,
		"template_code": TPL_CODE,
		"package": package_name,
		"package_code": PKG_CODE,
		"package_line_codes": [LINE_CODE_1, LINE_CODE_2],
		"demands": [DEMAND_1, DEMAND_2],
		"budget_line": bl_name,
		"sample_officer_completion_applied": sample_officer,
		"section_28_verification": section_28,
		"section_29_smoke": section_29,
		**release_info,
	}
