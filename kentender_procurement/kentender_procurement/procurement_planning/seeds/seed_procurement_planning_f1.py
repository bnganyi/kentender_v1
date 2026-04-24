# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""F1 — Full locked Procurement Planning seed (6. Seed Data + 9. Cursor Pack Phase F).

**Run order (Phase F, tracker: F2 → F1):**

1. DIA + Budget prerequisites (e.g. ``seed_budget_line_dia``, ``seed_dia_basic`` for 0004).
2. **F2** — ``validate_planning_seed_dependencies.run`` (or rely on the guard inside F1 which calls
   :func:`assert_prerequisites` after DIA is ensured).
3. ``seed_dia_planning_f1_prerequisites.run`` to create / align the four business Demand rows.
4. This module — **F1** full seed: profiles, templates, plan, three packages, emergency flag on 003.

``grouping_strategy`` for templates uses **only** fields allowed in v1 (see
``template_application``): empty ``group_by`` so multi-demand **TPL-MED-001** yields a single
package, matching 7.1. The 6. Seed *region / equipment* grouping is conceptual; v1 mapping is
documented in ``seed_planning_pp3_slice``.

Run::

	# UAT / dev: use a concrete site (e.g. ``kentender.midas.com``) when running the bench.
	bench --site kentender.midas.com execute kentender_procurement.demand_intake.seeds.seed_dia_planning_f1_prerequisites.run
	bench --site kentender.midas.com execute kentender_procurement.procurement_planning.seeds.validate_planning_seed_dependencies.run
	bench --site kentender.midas.com execute kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1.run

**Desk (after seed):** open the **Procurement Planning** workspace on the same site, ensure the
plan selector is **PP-MOH-2026** (FY2026 Procurement Plan). You need a role with planning read
(e.g. Procurement Planner / Planning Authority / Administrator). If the list looks stale, run
``bench --site kentender.midas.com clear-cache`` and hard-refresh the browser.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt

from kentender_core.seeds import constants as C
from kentender_procurement.demand_intake.seeds.dia_seed_common import (
	ensure_budget_line_prerequisites,
	ensure_core_prerequisites,
)
from kentender_procurement.demand_intake.seeds.seed_dia_planning_f1_prerequisites import run as run_dia_f1_prereq
from kentender_procurement.procurement_planning.seeds.validate_planning_seed_dependencies import assert_prerequisites
from kentender_procurement.procurement_planning.services.planning_references import (
	resolve_demand_name,
	resolve_procurement_plan_name,
	resolve_procurement_template_name,
)
from kentender_procurement.procurement_planning.services.template_application import apply_template_to_demands

# Locked 6. / 7.
PLAN_CODE = "PP-MOH-2026"
TPL_MED = "TPL-MED-001"
TPL_ICT = "TPL-ICT-001"
TPL_EMG = "TPL-EMG-001"
PKG1_CODE = "PKG-MOH-2026-001"
PKG1_NAME = "Diagnostic Imaging Equipment - Western Region"
PKG2_CODE = "PKG-MOH-2026-002"
PKG2_NAME = "Ministry ICT Devices Batch 1"
PKG3_CODE = "PKG-MOH-2026-003"
PKG3_NAME = "Emergency ICU Equipment"

BID_0004 = "DIA-MOH-2026-0004"
BID_0011 = "DIA-MOH-2026-0011"
BID_0020 = "DIA-MOH-2026-0020"
BID_0030 = "DIA-MOH-2026-0030"


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


def _ensure_f1_risk_profiles() -> dict[str, str]:
	standard = _ensure_profile_by_code(
		"Risk Profile",
		profile_code="RISK-STANDARD",
		profile_name="Standard Risk",
		extra_fields={
			"risk_level": "Medium",
			"risks": json.dumps(
				[
					{"risk": "Delivery delay", "mitigation": "Penalty clauses"},
					{"risk": "Quality failure", "mitigation": "Inspection checkpoints"},
				]
			),
		},
	)
	high = _ensure_profile_by_code(
		"Risk Profile",
		profile_code="RISK-HIGH",
		profile_name="High Risk",
		extra_fields={
			"risk_level": "High",
			"risks": json.dumps(
				[
					{"risk": "Cost overrun", "mitigation": "Strict budget control"},
					{"risk": "Vendor non-performance", "mitigation": "Performance guarantees"},
				]
			),
		},
	)
	emg = _ensure_profile_by_code(
		"Risk Profile",
		profile_code="RISK-EMERGENCY",
		profile_name="Emergency Risk",
		extra_fields={
			"risk_level": "High",
			"risks": json.dumps(
				[
					{"risk": "Supplier unavailability", "mitigation": "Pre-qualified vendors"},
					{"risk": "Price escalation", "mitigation": "Price caps"},
				]
			),
		},
	)
	return {"RISK-STANDARD": standard, "RISK-HIGH": high, "RISK-EMERGENCY": emg}


def _ensure_f1_kpi_profiles() -> dict[str, str]:
	std = _ensure_profile_by_code(
		"KPI Profile",
		profile_code="KPI-STANDARD",
		profile_name="Standard Procurement KPIs",
		extra_fields={
			"metrics": json.dumps(["Cost savings %", "Lead time adherence", "Delivery completeness"])
		},
	)
	ict = _ensure_profile_by_code(
		"KPI Profile",
		profile_code="KPI-ICT",
		profile_name="ICT Procurement KPIs",
		extra_fields={"metrics": json.dumps(["Device acceptance rate", "Warranty response time", "Delivery time"])},
	)
	emg = _ensure_profile_by_code(
		"KPI Profile",
		profile_code="KPI-EMERGENCY",
		profile_name="Emergency Procurement KPIs",
		extra_fields={"metrics": json.dumps(["Response time", "Delivery speed", "Service restoration time"])},
	)
	return {"KPI-STANDARD": std, "KPI-ICT": ict, "KPI-EMERGENCY": emg}


def _ensure_f1_criteria_profiles() -> dict[str, str]:
	std = _ensure_profile_by_code(
		"Decision Criteria Profile",
		profile_code="CRIT-STANDARD",
		profile_name="Standard Weighted Criteria",
		extra_fields={
			"criteria": json.dumps(
				[
					{"criterion": "Price", "weight": 40},
					{"criterion": "Quality", "weight": 30},
					{"criterion": "Delivery", "weight": 20},
					{"criterion": "Compliance", "weight": 10},
				]
			)
		},
	)
	tech = _ensure_profile_by_code(
		"Decision Criteria Profile",
		profile_code="CRIT-TECH",
		profile_name="Technical Heavy Criteria",
		extra_fields={
			"criteria": json.dumps(
				[
					{"criterion": "Technical Compliance", "weight": 50},
					{"criterion": "Price", "weight": 30},
					{"criterion": "Support", "weight": 20},
				]
			)
		},
	)
	emg = _ensure_profile_by_code(
		"Decision Criteria Profile",
		profile_code="CRIT-EMERGENCY",
		profile_name="Emergency Minimal Criteria",
		extra_fields={
			"criteria": json.dumps(
				[
					{"criterion": "Availability", "weight": 50},
					{"criterion": "Speed", "weight": 30},
					{"criterion": "Price Reasonableness", "weight": 20},
				]
			)
		},
	)
	return {"CRIT-STANDARD": std, "CRIT-TECH": tech, "CRIT-EMERGENCY": emg}


def _ensure_f1_vm_profiles() -> dict[str, str]:
	std = _ensure_profile_by_code(
		"Vendor Management Profile",
		profile_code="VM-STANDARD",
		profile_name="Standard Monitoring",
		extra_fields={
			"monitoring_rules": json.dumps({"monitoring": ["Monthly review"]}),
			"escalation_rules": json.dumps({"escalation": ["Escalate after 2 failures"]}),
		},
	)
	hi = _ensure_profile_by_code(
		"Vendor Management Profile",
		profile_code="VM-HIGH",
		profile_name="High-Touch Monitoring",
		extra_fields={
			"monitoring_rules": json.dumps({"monitoring": ["Weekly review"]}),
			"escalation_rules": json.dumps({"escalation": ["Immediate escalation on failure"]}),
		},
	)
	return {"VM-STANDARD": std, "VM-HIGH": hi}


def _med_template_body(rp: str, kpi: str, crit: str, vm: str) -> dict:
	return {
		"doctype": "Procurement Template",
		"template_code": TPL_MED,
		"template_name": "Medical Equipment Procurement",
		"category": "Healthcare",
		"is_active": 1,
		"applicable_requisition_types": json.dumps(["Goods", "Works", "Services"]),
		"applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
		"default_method": "Open Tender",
		"default_contract_type": "Fixed Price",
		"grouping_strategy": json.dumps({"group_by": []}),
		"threshold_rules": json.dumps([]),
		"planning_lead_days": 30,
		"procurement_cycle_days": 90,
		"override_requires_justification": 1,
		"high_risk_escalation_required": 0,
		"schedule_required": 0,
		"risk_profile_id": rp,
		"kpi_profile_id": kpi,
		"decision_criteria_profile_id": crit,
		"vendor_management_profile_id": vm,
	}


def _ict_template_body(rp: str, kpi: str, crit: str, vm: str) -> dict:
	return {
		"doctype": "Procurement Template",
		"template_code": TPL_ICT,
		"template_name": "ICT Equipment Procurement",
		"category": "ICT",
		"is_active": 1,
		"applicable_requisition_types": json.dumps(["Goods", "Works", "Services"]),
		"applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
		"default_method": "RFQ",
		"default_contract_type": "Fixed Price",
		"grouping_strategy": json.dumps({"group_by": []}),
		"threshold_rules": json.dumps([]),
		"planning_lead_days": 20,
		"procurement_cycle_days": 60,
		"override_requires_justification": 1,
		"high_risk_escalation_required": 0,
		"schedule_required": 0,
		"risk_profile_id": rp,
		"kpi_profile_id": kpi,
		"decision_criteria_profile_id": crit,
		"vendor_management_profile_id": vm,
	}


def _emg_template_body(rp: str, kpi: str, crit: str, vm: str) -> dict:
	return {
		"doctype": "Procurement Template",
		"template_code": TPL_EMG,
		"template_name": "Emergency Procurement",
		"category": "Emergency",
		"is_active": 1,
		"applicable_requisition_types": json.dumps(["Goods", "Works", "Services"]),
		"applicable_demand_types": json.dumps(["Planned", "Unplanned", "Emergency"]),
		"default_method": "Direct",
		"default_contract_type": "T&M",
		"grouping_strategy": json.dumps({"group_by": []}),
		"threshold_rules": json.dumps([]),
		"planning_lead_days": 1,
		"procurement_cycle_days": 14,
		"override_requires_justification": 1,
		"high_risk_escalation_required": 0,
		"schedule_required": 0,
		"risk_profile_id": rp,
		"kpi_profile_id": kpi,
		"decision_criteria_profile_id": crit,
		"vendor_management_profile_id": vm,
	}


def _ensure_f1_templates(links: dict) -> dict[str, str]:
	# links: r_std, r_emg, k_*, c_*, vm_* keys by get from _ensure return dicts
	rp = links["RISK"]
	kp = links["KPI"]
	cp = links["CRIT"]
	vp = links["VM"]
	out: dict[str, str] = {}

	med = frappe.db.get_value("Procurement Template", {"template_code": TPL_MED}, "name")
	if not med:
		doc = frappe.get_doc(
			_med_template_body(
				rp["RISK-STANDARD"],
				kp["KPI-STANDARD"],
				cp["CRIT-STANDARD"],
				vp["VM-STANDARD"],
			)
		)
		doc.insert(ignore_permissions=True)
		med = doc.name
	out[TPL_MED] = med

	ict = frappe.db.get_value("Procurement Template", {"template_code": TPL_ICT}, "name")
	if not ict:
		doc = frappe.get_doc(
			_ict_template_body(
				rp["RISK-STANDARD"],
				kp["KPI-ICT"],
				cp["CRIT-TECH"],
				vp["VM-STANDARD"],
			)
		)
		doc.insert(ignore_permissions=True)
		ict = doc.name
	out[TPL_ICT] = ict

	emg = frappe.db.get_value("Procurement Template", {"template_code": TPL_EMG}, "name")
	if not emg:
		doc = frappe.get_doc(
			_emg_template_body(
				rp["RISK-EMERGENCY"],
				kp["KPI-EMERGENCY"],
				cp["CRIT-EMERGENCY"],
				vp["VM-HIGH"],
			)
		)
		doc.insert(ignore_permissions=True)
		emg = doc.name
	out[TPL_EMG] = emg

	return out


def _ensure_f1_plan() -> str:
	name = frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name")
	if name:
		return name
	currency = "KES"
	if not frappe.db.exists("Currency", currency):
		frappe.throw(_("Currency KES is missing. Run seed_core_minimal."), title=_("Missing prerequisite"))
	doc = frappe.get_doc(
		{
			"doctype": "Procurement Plan",
			"plan_name": "FY2026 Procurement Plan",
			"plan_code": PLAN_CODE,
			"fiscal_year": 2026,
			"procuring_entity": C.ENTITY_MOH,
			"currency": currency,
			"status": "Draft",
			"is_active": 1,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _package_on_plan(plan_name: str, package_code: str) -> str | None:
	return frappe.db.get_value("Procurement Package", {"plan_id": plan_name, "package_code": package_code}, "name")


def _f1_assert_invariants() -> None:
	"""Defensive checks: package value = sum of active lines; ≥1 line; emergency on EMG pack."""
	p1 = _package_on_plan(
		frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name") or "", PKG1_CODE
	)
	if not p1:
		return
	lines1 = frappe.get_all(
		"Procurement Package Line",
		filters={"package_id": p1, "is_active": 1},
		fields=["amount"],
	)
	s1 = sum(flt(x.amount) for x in lines1)
	pv1 = flt(frappe.db.get_value("Procurement Package", p1, "estimated_value"))
	if abs(s1 - pv1) > 0.5:
		frappe.throw(
			_("F1 invariant: {0} estimated_value {1} != sum of lines {2}.").format(PKG1_CODE, pv1, s1),
			title=_("F1 seed validation"),
		)

	# template link on p1
	t1 = frappe.db.get_value("Procurement Package", p1, "template_id")
	if not t1 or frappe.db.get_value("Procurement Template", t1, "template_code") != TPL_MED:
		frappe.throw(_("F1: {0} must link to {1}.").format(PKG1_CODE, TPL_MED), title=_("F1 seed validation"))

	p3n = _package_on_plan(
		frappe.db.get_value("Procurement Plan", {"plan_code": PLAN_CODE}, "name") or "", PKG3_CODE
	)
	if p3n and cint(frappe.db.get_value("Procurement Package", p3n, "is_emergency")) != 1:
		frappe.throw(
			_("F1: {0} must have is_emergency set (template apply does not set the flag).").format(PKG3_CODE),
			title=_("F1 seed validation"),
		)


def run(ensure_dia: bool = True) -> dict:
	"""F1 — full locked seed. When ``ensure_dia`` is True, runs the DIA prerequisite pack first
	(``seed_dia_planning_f1_prerequisites``), then re-validates F2 dependencies."""
	frappe.only_for(("System Manager", "Administrator"))
	if not frappe.db.exists("DocType", "Procurement Plan"):
		frappe.throw(_("Procurement Planning is not installed."), title=_("Missing doctype"))
	_ensure_core_if_needed()
	ensure_budget_line_prerequisites()
	if ensure_dia:
		run_dia_f1_prereq()
	assert_prerequisites()

	rp = _ensure_f1_risk_profiles()
	kp = _ensure_f1_kpi_profiles()
	cp = _ensure_f1_criteria_profiles()
	vp = _ensure_f1_vm_profiles()
	_ensure_f1_templates({"RISK": rp, "KPI": kp, "CRIT": cp, "VM": vp})
	plan_name = _ensure_f1_plan()

	plan_id = resolve_procurement_plan_name(PLAN_CODE)
	created: list[dict] = []
	skipped: list[str] = []

	# 7.1 Medical
	if not _package_on_plan(plan_name, PKG1_CODE):
		out = apply_template_to_demands(
			plan_id,
			resolve_procurement_template_name(TPL_MED),
			[resolve_demand_name(BID_0004), resolve_demand_name(BID_0011)],
			actor=frappe.session.user,
			options={"package_code": PKG1_CODE, "package_name": PKG1_NAME},
		)
		created.append({"package_code": PKG1_CODE, "apply": out})
	else:
		skipped.append(PKG1_CODE)

	# 7.2 ICT
	if not _package_on_plan(plan_name, PKG2_CODE):
		out2 = apply_template_to_demands(
			plan_id,
			resolve_procurement_template_name(TPL_ICT),
			[resolve_demand_name(BID_0020)],
			actor=frappe.session.user,
			options={"package_code": PKG2_CODE, "package_name": PKG2_NAME},
		)
		created.append({"package_code": PKG2_CODE, "apply": out2})
	else:
		skipped.append(PKG2_CODE)

	# 7.3 Emergency
	p3n = _package_on_plan(plan_name, PKG3_CODE)
	if not p3n:
		out3 = apply_template_to_demands(
			plan_id,
			resolve_procurement_template_name(TPL_EMG),
			[resolve_demand_name(BID_0030)],
			actor=frappe.session.user,
			options={"package_code": PKG3_CODE, "package_name": PKG3_NAME},
		)
		created.append({"package_code": PKG3_CODE, "apply": out3})
		p3n = (out3.get("packages") or [{}])[0].get("name")
	else:
		skipped.append(PKG3_CODE)
	if p3n:
		frappe.db.set_value("Procurement Package", p3n, "is_emergency", 1, update_modified=False)

	frappe.db.commit()
	_f1_assert_invariants()

	return {
		"pack": "seed_procurement_planning_f1",
		"plan": plan_name,
		"plan_code": PLAN_CODE,
		"created": created,
		"skipped_package_codes": skipped,
		"message": str(_("F1 complete. Packages created: {0}, skipped: {1}.").format(len(created), len(skipped))),
	}
