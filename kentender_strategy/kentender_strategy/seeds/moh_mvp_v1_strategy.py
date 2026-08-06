# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""MOH_MVP_V1 Strategy seed — contract §5 identities."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.moh_mvp_v1 import constants as C
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_plan

PVO_FIXTURE = [
	("PVO-EFT-01", "Strategic and service outcomes", "Improve availability of critical health services"),
	("PVO-ECO-01", "Economy and whole-life value", "Reduce whole-life infrastructure cost"),
	("PVO-EFY-01", "Process efficiency", "Reduce implementation and service-restoration time"),
	("PVO-RES-01", "Contract performance and resilience", "Improve continuity of critical services"),
	("PVO-LOC-01", "Inclusion and economic development", "Develop internal and local technical capability"),
	("PVO-SUS-01", "Sustainability and asset stewardship", "Reduce infrastructure energy consumption"),
	("PVO-SUS-02", "Sustainability and asset stewardship", "Ensure compliant handling of replaced ICT equipment"),
	("PVO-INT-01", "Integrity and accountability", "Minimise uncontrolled contract changes"),
]

# (commitment_code, pvo_objective_code, requirement_level)
PVC_FIXTURE = (
	("MOH-PVC-EFT-01", "PVO-EFT-01", "Required consideration"),
	("MOH-PVC-ECO-01", "PVO-ECO-01", "Required consideration"),
	("MOH-PVC-EFY-01", "PVO-EFY-01", "Recommended consideration"),
	("MOH-PVC-RES-01", "PVO-RES-01", "Recommended consideration"),
	("MOH-PVC-LOC-01", "PVO-LOC-01", "Required consideration"),
	("MOH-PVC-SUS-01", "PVO-SUS-01", "Recommended consideration"),
	("MOH-PVC-SUS-02", "PVO-SUS-02", "Required consideration"),
	("MOH-PVC-INT-01", "PVO-INT-01", "Required consideration"),
)

OWN_SDMS = {"owner_state_department": C.SD_MEDICAL, "owner_directorate": C.DIR_DHP, "fixture_namespace": C.FIXTURE_NS}
OWN_SDPH = {"owner_state_department": C.SD_PUBLIC, "owner_directorate": C.DIR_HRMD, "fixture_namespace": C.FIXTURE_NS}


def _pe() -> str:
	from kentender_core.seeds._common import ensure_procuring_entity

	return ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME)


def _upsert(doctype: str, code_field: str, code: str, values: dict) -> str:
	existing = frappe.db.get_value(doctype, {code_field: code}, "name")
	payload = {code_field: code, **values}
	if existing:
		# Always refresh ownership / fixture tags even on Active plans.
		own_keys = ("fixture_namespace", "owner_state_department", "owner_directorate")
		frappe.db.set_value(
			doctype,
			existing,
			{k: payload[k] for k in own_keys if k in payload},
			update_modified=False,
		)
		plan = payload.get("plan_version")
		if plan:
			status = frappe.db.get_value("Strategic Plan", plan, "status")
			if status not in ("Draft", "Returned", None):
				return existing
		doc = frappe.get_doc(doctype, existing)
		doc.update(payload)
		doc.save(ignore_permissions=True)
		return existing
	doc = frappe.get_doc({"doctype": doctype, **payload})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_pvos(pe: str) -> dict[str, str]:
	out: dict[str, str] = {}
	for code, pillar, title in PVO_FIXTURE:
		name = frappe.db.get_value(
			"Public Value Objective", {"objective_code": code, "version_number": 1}, "name"
		)
		if name:
			frappe.db.set_value(
				"Public Value Objective", name, "status", "Active", update_modified=False
			)
			out[code] = name
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Public Value Objective",
				"objective_code": code,
				"version_number": 1,
				"title": title,
				"pillar": pillar,
				"status": "Active",
				"scope": "Procuring entity",
				"procuring_entity": pe,
				"description": title,
				"source_type": "Entity Strategy",
				"source_reference": "MOH Public Value Framework",
				"applicability_mode": "Universal consideration",
				"measure_guidance": "Track via plan measurement framework",
				"evidence_guidance": "Approved monitoring report",
				"responsible_function": "Digital Health Directorate",
				"default_enforcement_guidance": "Reporting obligation",
				"effective_from": "2026-07-01",
				"effective_to": "2030-06-30",
			}
		)
		doc.insert(ignore_permissions=True)
		out[code] = doc.name
	return out


def clear_moh_mvp_v1_strategy() -> dict[str, Any]:
	"""Delete Strategy records tagged MOH_MVP_V1 (reverse dependency order)."""
	deleted: dict[str, int] = {}
	plan = frappe.db.get_value(
		"Strategic Plan", {"plan_code": C.PLAN_CODE, "version_number": 1}, "name"
	)
	# Also remove legacy remapped plan if present
	legacy = frappe.db.get_value(
		"Strategic Plan", {"plan_code": "MOH-SP-0001", "version_number": 1}, "name"
	)
	plans = [p for p in (plan, legacy) if p]

	for doctype, filters_extra in (
		("Strategy Corrective Action", {}),
		("Performance Measurement", {}),
		("Plan Value Commitment", {}),
		("Performance Target", {}),
		("Performance Indicator", {}),
		("Strategic Outcome", {}),
		("Strategy Sub Programme", {}),
		("Strategy Programme", {}),
	):
		names = []
		if frappe.db.has_column(doctype, "fixture_namespace"):
			names.extend(
				frappe.get_all(
					doctype, filters={"fixture_namespace": C.FIXTURE_NS}, pluck="name"
				)
			)
		for p in plans:
			if frappe.db.has_column(doctype, "plan_version"):
				names.extend(
					frappe.get_all(doctype, filters={"plan_version": p}, pluck="name")
				)
			if doctype == "Performance Measurement" and frappe.db.has_column(
				doctype, "plan_version"
			):
				pass
		# Deduplicate
		seen = set()
		count = 0
		for name in names:
			if name in seen or not frappe.db.exists(doctype, name):
				continue
			seen.add(name)
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			count += 1
		deleted[doctype] = count

	for p in plans:
		if frappe.db.exists("Strategic Plan", p):
			frappe.delete_doc("Strategic Plan", p, force=1, ignore_permissions=True)
			deleted["Strategic Plan"] = deleted.get("Strategic Plan", 0) + 1
	return {"ok": True, "deleted": deleted}


def upsert_moh_mvp_v1_strategy(*, reset: bool = False) -> dict[str, Any]:
	ensure_strategy_roles()
	pe = _pe()
	if reset:
		clear_moh_mvp_v1_strategy()

	# Migrate legacy code in place if old plan still exists
	legacy = frappe.db.get_value("Strategic Plan", {"plan_code": "MOH-SP-0001"}, "name")
	if legacy and not frappe.db.exists("Strategic Plan", {"plan_code": C.PLAN_CODE}):
		frappe.db.set_value(
			"Strategic Plan", legacy, "plan_code", C.PLAN_CODE, update_modified=False
		)

	pvos = _ensure_pvos(pe)
	plan_name = frappe.db.get_value(
		"Strategic Plan", {"plan_code": C.PLAN_CODE, "version_number": 1}, "name"
	)
	created = False
	if not plan_name:
		plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": C.PLAN_CODE,
				"version_number": 1,
				"title": C.PLAN_TITLE,
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": pe,
				"status": "Draft",
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"description": "Canonical MOH_MVP_V1 strategic plan.",
				"fixture_namespace": C.FIXTURE_NS,
			}
		)
		plan.insert(ignore_permissions=True)
		plan_name = plan.name
		created = True
	else:
		frappe.db.set_value(
			"Strategic Plan",
			plan_name,
			{
				"title": C.PLAN_TITLE,
				"fixture_namespace": C.FIXTURE_NS,
				"scope_type": "Procuring Entity",
				"scope_id": pe,
			},
			update_modified=False,
		)

	status = frappe.db.get_value("Strategic Plan", plan_name, "status")
	rebuild = status in ("Draft", "Returned") or created
	if status in ("Approved", "Active", "Superseded", "Archived") and not created:
		# Force Draft only when reset path already cleared; otherwise patch ownership via _upsert
		rebuild = False

	if rebuild and status not in ("Draft", "Returned"):
		frappe.db.set_value("Strategic Plan", plan_name, "status", "Draft", update_modified=False)

	# --- Medical Services hierarchy ---
	prog = _upsert(
		"Strategy Programme",
		"programme_code",
		C.PROG_DH,
		{
			"plan_version": plan_name,
			"title": "Digital Health Services",
			"description": "Digital clinical services and health information systems.",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 1,
			**OWN_SDMS,
		},
	)
	sub_his = _upsert(
		"Strategy Sub Programme",
		"sub_programme_code",
		C.SUB_HIS,
		{
			"plan_version": plan_name,
			"programme": prog,
			"title": "Health Information Systems",
			"description": "Health Information Systems",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 1,
			**OWN_SDMS,
		},
	)
	out_rel = _upsert(
		"Strategic Outcome",
		"outcome_code",
		C.OUT_RELIABILITY,
		{
			"plan_version": plan_name,
			"programme": prog,
			"sub_programme": sub_his,
			"title": "Reliable and accessible digital clinical services",
			"description": "Reliable and accessible digital clinical services",
			"responsible_function": C.DIR_DHP_NAME,
			"executive_owner": "Director, Digital Health and Policy",
			"order_index": 1,
			**OWN_SDMS,
		},
	)
	ind_avail = _upsert(
		"Performance Indicator",
		"indicator_code",
		C.IND_AVAIL,
		{
			"plan_version": plan_name,
			"strategic_outcome": out_rel,
			"title": "Availability of core clinical information systems",
			"definition": "Percentage of time core clinical information systems are available.",
			"measurement_type": "Percentage",
			"unit": "%",
			"measurement_frequency": "Monthly",
			"data_source": "Approved infrastructure-monitoring report",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 1,
			**OWN_SDMS,
		},
	)
	ind_restore = _upsert(
		"Performance Indicator",
		"indicator_code",
		C.IND_RESTORE,
		{
			"plan_version": plan_name,
			"strategic_outcome": out_rel,
			"title": "Average restoration time for critical services",
			"definition": "Average hours to restore critical clinical services.",
			"measurement_type": "Numeric",
			"unit": "hours",
			"measurement_frequency": "Monthly",
			"data_source": "Approved infrastructure-monitoring report",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 2,
			**OWN_SDMS,
		},
	)
	tgt_avail = _upsert(
		"Performance Target",
		"target_code",
		C.TGT_AVAIL_2028,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_avail,
			"title": "At least 99.9% annual availability by 30 June 2028",
			"comparison_direction": "At least",
			"target_numeric": 99.9,
			"baseline_status": "Known",
			"baseline_numeric": 97.8,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 0.1,
			"period_start": "2026-07-01",
			"period_end": "2028-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDMS,
		},
	)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_RESTORE_2028,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_restore,
			"title": "Restore critical services within four hours by 30 June 2028",
			"comparison_direction": "At most",
			"target_numeric": 4.0,
			"baseline_status": "Known",
			"baseline_numeric": 11.5,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 0.5,
			"period_start": "2026-07-01",
			"period_end": "2028-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDMS,
		},
	)
	# Successor targets (§5.4)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_AVAIL_2029,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_avail,
			"title": "Maintain at least 99.95% annual availability by 30 June 2029",
			"comparison_direction": "At least",
			"target_numeric": 99.95,
			"baseline_status": "Known",
			"baseline_numeric": 97.8,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 0.05,
			"period_start": "2028-07-01",
			"period_end": "2029-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDMS,
		},
	)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_RESTORE_2029,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_restore,
			"title": "Restore critical services within two hours by 30 June 2029",
			"comparison_direction": "At most",
			"target_numeric": 2.0,
			"baseline_status": "Known",
			"baseline_numeric": 11.5,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 0.25,
			"period_start": "2028-07-01",
			"period_end": "2029-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDMS,
		},
	)

	# --- Public Health hierarchy (minimal) ---
	sub_dhc = _upsert(
		"Strategy Sub Programme",
		"sub_programme_code",
		C.SUB_DHC,
		{
			"plan_version": plan_name,
			"programme": prog,
			"title": "Digital Health Workforce Capability",
			"description": "Digital Health Workforce Capability",
			"responsible_function": C.DIR_HRMD_NAME,
			"order_index": 2,
			**OWN_SDPH,
		},
	)
	out_cap = _upsert(
		"Strategic Outcome",
		"outcome_code",
		C.OUT_CAPABILITY,
		{
			"plan_version": plan_name,
			"programme": prog,
			"sub_programme": sub_dhc,
			"title": "Sustainable digital-health workforce capability",
			"description": "Sustainable digital-health workforce capability",
			"responsible_function": C.DIR_HRMD_NAME,
			"executive_owner": "Director, HRMD",
			"order_index": 2,
			**OWN_SDPH,
		},
	)
	ind_skills = _upsert(
		"Performance Indicator",
		"indicator_code",
		C.IND_SKILLS,
		{
			"plan_version": plan_name,
			"strategic_outcome": out_cap,
			"title": "Number of trained and certified digital-health technical staff",
			"definition": "Count of trained and certified digital-health technical staff.",
			"measurement_type": "Numeric",
			"unit": "staff",
			"measurement_frequency": "Annual",
			"data_source": "HR training registry",
			"responsible_function": C.DIR_HRMD_NAME,
			"order_index": 1,
			**OWN_SDPH,
		},
	)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_SKILLS_2029,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_skills,
			"title": "Train and certify 150 digital-health technical staff by 30 June 2029",
			"comparison_direction": "At least",
			"target_numeric": 150,
			"baseline_status": "Known",
			"baseline_numeric": 35,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 5,
			"period_start": "2026-07-01",
			"period_end": "2029-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDPH,
		},
	)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_SKILLS_2030,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_skills,
			"title": "Train and certify 220 digital-health technical staff by 30 June 2030",
			"comparison_direction": "At least",
			"target_numeric": 220,
			"baseline_status": "Known",
			"baseline_numeric": 35,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 infrastructure report",
			"tolerance_value": 5,
			"period_start": "2029-07-01",
			"period_end": "2030-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_SDPH,
		},
	)

	# PVCs
	pvcs: dict[str, str] = {}
	for pvc_code, pvo_code, level in PVC_FIXTURE:
		existing = frappe.db.get_value(
			"Plan Value Commitment", {"commitment_code": pvc_code}, "name"
		)
		if existing:
			frappe.db.set_value(
				"Plan Value Commitment",
				existing,
				{"fixture_namespace": C.FIXTURE_NS, "status": "Locked"},
				update_modified=False,
			)
			pvcs[pvc_code] = existing
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Plan Value Commitment",
				"commitment_code": pvc_code,
				"plan_version": plan_name,
				"public_value_objective_version": pvos[pvo_code],
				"rationale": f"Adopt {pvo_code} into Active Plan",
				"consideration_level": level,
				"responsible_owner": C.DIR_DHP_NAME,
				"status": "Locked",
				"fixture_namespace": C.FIXTURE_NS,
				"links": [
					{"link_type": "Strategic Outcome", "linked_outcome": out_rel},
					{"link_type": "Performance Target", "linked_target": tgt_avail},
				],
			}
		)
		doc.insert(ignore_permissions=True)
		pvcs[pvc_code] = doc.name

	# Activate plan
	status = frappe.db.get_value("Strategic Plan", plan_name, "status")
	frappe.set_user("Administrator")
	if status == "Draft":
		transition_plan(plan_name, "Submit")
		transition_plan(plan_name, "Approve")
		transition_plan(plan_name, "Activate")
	elif status == "Submitted":
		transition_plan(plan_name, "Approve")
		transition_plan(plan_name, "Activate")
	elif status == "Approved":
		transition_plan(plan_name, "Activate")

	meas = _ensure_measurements(plan_name, tgt_avail)
	return {
		"ok": True,
		"created": created,
		"plan": plan_name,
		"plan_code": C.PLAN_CODE,
		"target_avail": tgt_avail,
		"measurements": meas,
		"pvos": pvos,
		"pvcs": pvcs,
		"procuring_entity": pe,
	}


def _ensure_measurements(plan_name: str, target_name: str) -> dict[str, str]:
	ids: dict[str, str] = {}
	sep = frappe.db.get_value(
		"Performance Measurement",
		{
			"performance_target": target_name,
			"measurement_period_start": "2027-09-01",
			"measurement_period_end": "2027-09-30",
		},
		"name",
	)
	if not sep:
		sep_doc = frappe.get_doc(
			{
				"doctype": "Performance Measurement",
				"measurement_code": "MOH-MEAS-AVAIL-2027-09",
				"performance_target": target_name,
				"plan_version": plan_name,
				"measurement_period_start": "2027-09-01",
				"measurement_period_end": "2027-09-30",
				"actual_numeric": 99.82,
				"measurement_date": "2027-10-05",
				"evidence_reference": "INFRA-MON-2027-09",
				"evidence_source": "Approved infrastructure-monitoring report",
				"commentary": "Storage-controller instability",
				"variance": 99.82 - 99.9,
				"result_status": "At risk",
				"workflow_status": "Verified",
				"submitted_by": "Administrator",
				"verified_by": "Administrator",
				**OWN_SDMS,
			}
		)
		sep_doc.insert(ignore_permissions=True)
		sep = sep_doc.name
	else:
		frappe.db.set_value(
			"Performance Measurement", sep, OWN_SDMS, update_modified=False
		)
	ids["sep"] = sep

	oct = frappe.db.get_value(
		"Performance Measurement",
		{
			"performance_target": target_name,
			"measurement_period_start": "2027-10-01",
			"measurement_period_end": "2027-10-31",
		},
		"name",
	)
	if not oct:
		oct_doc = frappe.get_doc(
			{
				"doctype": "Performance Measurement",
				"measurement_code": "MOH-MEAS-AVAIL-2027-10",
				"performance_target": target_name,
				"plan_version": plan_name,
				"measurement_period_start": "2027-10-01",
				"measurement_period_end": "2027-10-31",
				"actual_numeric": 99.96,
				"measurement_date": "2027-11-05",
				"evidence_reference": "INFRA-MON-2027-10",
				"evidence_source": "Approved infrastructure-monitoring report",
				"commentary": "Stabilised after corrective action",
				"variance": 99.96 - 99.9,
				"result_status": "On track",
				"workflow_status": "Verified",
				"submitted_by": "Administrator",
				"verified_by": "Administrator",
				**OWN_SDMS,
			}
		)
		oct_doc.insert(ignore_permissions=True)
		oct = oct_doc.name
	else:
		frappe.db.set_value(
			"Performance Measurement", oct, OWN_SDMS, update_modified=False
		)
	ids["oct"] = oct

	ca = frappe.db.get_value(
		"Strategy Corrective Action", {"performance_measurement": sep}, "name"
	)
	if not ca:
		ca_doc = frappe.get_doc(
			{
				"doctype": "Strategy Corrective Action",
				"corrective_action_code": "MOH-CA-AVAIL-2027-09",
				"performance_measurement": sep,
				"performance_target": target_name,
				"plan_version": plan_name,
				"action": "Resolve storage-controller instability",
				"owner": C.DIR_DHP_NAME,
				"due_date": "2027-10-31",
				"expected_result": "Return availability to On track",
				"status": "Verified complete",
				"completion_evidence": "Controller firmware patch and failover test signed off",
				"verified_by": "Administrator",
				**OWN_SDMS,
			}
		)
		ca_doc.insert(ignore_permissions=True)
		ca = ca_doc.name
	else:
		frappe.db.set_value(
			"Strategy Corrective Action", ca, OWN_SDMS, update_modified=False
		)
	ids["ca"] = ca
	return ids
