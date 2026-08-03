# Copyright (c) 2026, KenTender and contributors
"""Idempotent MOH-SP-2026-2030 Strategy seed (STRATEGY-MVP1-REQ-1.0 §19).

Also keeps legacy constant aliases for works-master / stable-platform importers.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_plan

# --- Canonical MVP-1 codes (REQ §19) ---
STRATEGY_PLAN_CODE: Final[str] = "MOH-SP-2026-2030"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026–2030"
START_YEAR: Final[int] = 2026
END_YEAR: Final[int] = 2030
PROGRAM_CODE: Final[str] = "MOH-PROG-DH"
PROGRAM_TITLE: Final[str] = "Digital Health Services"
PROGRAM_DESCRIPTION: Final[str] = (
	"Digital clinical services and health information systems that improve access and continuity of care."
)
SUB_PROGRAM_CODE: Final[str] = "MOH-SUB-HIS"
SUB_PROGRAM_TITLE: Final[str] = "Health Information Systems"
OBJECTIVE_CODE: Final[str] = "MOH-OUT-01"  # Strategic Outcome (legacy alias name)
OBJECTIVE_TITLE: Final[str] = "Reliable and accessible digital clinical services"
OBJECTIVE_DESCRIPTION: Final[str] = OBJECTIVE_TITLE
INDICATOR_CODE: Final[str] = "MOH-IND-01"
INDICATOR_TITLE: Final[str] = "Availability of core clinical information systems"
TARGET_CODE: Final[str] = "MOH-TGT-01"
TARGET_TITLE: Final[str] = "At least 99.9% annual availability by 30 June 2028"
TARGET_METRIC_TEXT: Final[str] = "Percent availability"

# Legacy import aliases (pre-teardown codes) — map to MVP-1 where possible
LEGACY_STRATEGY_PLAN_CODE: Final[str] = "STRAT-MOH-2026"

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


def desk_visibility(procuring_entity_name: str) -> dict[str, str]:
	return {
		"procuring_entity": procuring_entity_name,
		"scope_rule": "Entity-scoped Strategy Alignment (MVP-1).",
		"optional_seed_flag": "MOH-SP-2026-2030",
	}


def resolve_procuring_entity_moh() -> str | None:
	for code in ("PE-MOH", "MOH"):
		name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if name:
			return name
	# Fallback: any PE containing Health
	name = frappe.db.get_value("Procuring Entity", {"entity_name": ["like", "%Health%"]}, "name")
	if name:
		return name
	rows = frappe.get_all("Procuring Entity", pluck="name", limit=1)
	return rows[0] if rows else None


def _upsert_by_code(doctype: str, code_field: str, code: str, values: dict) -> str:
	existing = frappe.db.get_value(doctype, {code_field: code}, "name")
	if existing:
		doc = frappe.get_doc(doctype, existing)
		# Only update while Draft/Returned for plan-bound docs
		plan = values.get("plan_version") or doc.get("plan_version")
		if plan:
			status = frappe.db.get_value("Strategic Plan", plan, "status")
			if status not in ("Draft", "Returned", None):
				return existing
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc({"doctype": doctype, code_field: code, **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_pvos(pe: str) -> dict[str, str]:
	out = {}
	for code, pillar, title in PVO_FIXTURE:
		name = frappe.db.get_value(
			"Public Value Objective", {"objective_code": code, "version_number": 1}, "name"
		)
		if name:
			# Force Active for fixture
			frappe.db.set_value("Public Value Objective", name, "status", "Active", update_modified=False)
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
				"source_reference": "MOH Public Value Framework example",
				"applicability_mode": "Universal consideration",
				"measure_guidance": "Track via plan measurement framework",
				"evidence_guidance": "Approved monitoring report",
				"responsible_function": "Digital Health Directorate",
				"default_enforcement_guidance": "Reporting obligation",
				"effective_from": "2026-07-01",
				"effective_to": "2030-06-30",
			}
		)
		# Add category trigger on ICT for applicability demos
		if code in ("PVO-SUS-01", "PVO-SUS-02", "PVO-EFT-01"):
			doc.applicability_mode = "Category-triggered"
			doc.append(
				"triggers",
				{
					"trigger_type": "Procurement Category",
					"trigger_value": "ICT",
					"include": 1,
				},
			)
		doc.insert(ignore_permissions=True)
		out[code] = doc.name
	return out


def _ensure_measurements(plan_name: str, target_name: str) -> dict[str, str]:
	"""Sep/Oct 2027 verified measurements + completed CA (REQ §19.3)."""
	ids = {}
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
				"performance_target": target_name,
				"plan_version": plan_name,
				"measurement_period_start": "2027-09-01",
				"measurement_period_end": "2027-09-30",
				"actual_numeric": 99.82,
				"measurement_date": "2027-10-05",
				"evidence_reference": "INFRA-MON-2027-09",
				"evidence_source": "Approved infrastructure-monitoring report",
				"commentary": "Storage-controller instability observed",
				"variance": 99.82 - 99.9,
				"result_status": "At risk",
				"workflow_status": "Verified",
				"submitted_by": "Administrator",
				"verified_by": "Administrator",
			}
		)
		sep_doc.insert(ignore_permissions=True)
		sep = sep_doc.name
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
			}
		)
		oct_doc.insert(ignore_permissions=True)
		oct = oct_doc.name
	ids["oct"] = oct

	ca = frappe.db.get_value(
		"Strategy Corrective Action",
		{"performance_measurement": sep},
		"name",
	)
	if not ca:
		ca_doc = frappe.get_doc(
			{
				"doctype": "Strategy Corrective Action",
				"performance_measurement": sep,
				"performance_target": target_name,
				"plan_version": plan_name,
				"action": "Resolve storage-controller instability",
				"owner": "Digital Health Directorate",
				"due_date": "2027-10-31",
				"expected_result": "Return availability to On track",
				"status": "Verified complete",
				"completion_evidence": "Controller firmware patch and failover test signed off",
				"verified_by": "Administrator",
			}
		)
		ca_doc.insert(ignore_permissions=True)
		ca = ca_doc.name
	ids["ca"] = ca
	return ids


def upsert_works_master_strategy_hierarchy(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	"""Idempotent loader for MOH-SP-2026-2030 (+ PVOs, commitments, measurements)."""
	ensure_strategy_roles()
	pe = resolve_procuring_entity_moh()
	if not pe:
		return {
			"ok": False,
			"reason": "no-procuring-entity",
			"plan": None,
			"program": None,
			"sub_program": None,
			"objective": None,
			"target": None,
			"procuring_entity": None,
		}

	pvos = _ensure_pvos(pe)

	plan_name = frappe.db.get_value(
		"Strategic Plan",
		{"plan_code": STRATEGY_PLAN_CODE, "version_number": 1},
		"name",
	)
	created = False
	if not plan_name:
		plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": STRATEGY_PLAN_CODE,
				"version_number": 1,
				"title": PLAN_TITLE,
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"status": "Draft",
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"description": "MOH strategic plan fixture for Strategy Alignment MVP-1.",
			}
		)
		plan.insert(ignore_permissions=True)
		plan_name = plan.name
		created = True
	else:
		status = frappe.db.get_value("Strategic Plan", plan_name, "status")
		if status in ("Approved", "Active", "Superseded", "Archived"):
			# Structure locked — ensure measurements/PVOs only
			target_name = frappe.db.get_value(
				"Performance Target",
				{"target_code": TARGET_CODE, "plan_version": plan_name},
				"name",
			)
			meas = _ensure_measurements(plan_name, target_name) if target_name else {}
			frappe.db.commit()
			return {
				"ok": True,
				"skipped": False,
				"created": False,
				"plan": plan_name,
				"plan_code": STRATEGY_PLAN_CODE,
				"program": frappe.db.get_value(
					"Strategy Programme", {"programme_code": PROGRAM_CODE}, "name"
				),
				"sub_program": frappe.db.get_value(
					"Strategy Sub Programme", {"sub_programme_code": SUB_PROGRAM_CODE}, "name"
				),
				"objective": frappe.db.get_value(
					"Strategic Outcome", {"outcome_code": OBJECTIVE_CODE}, "name"
				),
				"target": target_name,
				"measurements": meas,
				"pvos": pvos,
				"procuring_entity": pe,
			}
		# Reset Draft for rebuild
		frappe.db.set_value("Strategic Plan", plan_name, "status", "Draft", update_modified=False)

	prog = _upsert_by_code(
		"Strategy Programme",
		"programme_code",
		PROGRAM_CODE,
		{
			"plan_version": plan_name,
			"title": PROGRAM_TITLE,
			"description": PROGRAM_DESCRIPTION,
			"responsible_function": "Digital Health Directorate",
			"order_index": 1,
		},
	)
	sub = _upsert_by_code(
		"Strategy Sub Programme",
		"sub_programme_code",
		SUB_PROGRAM_CODE,
		{
			"plan_version": plan_name,
			"programme": prog,
			"title": SUB_PROGRAM_TITLE,
			"description": SUB_PROGRAM_TITLE,
			"responsible_function": "Health Information Systems Unit",
			"order_index": 1,
		},
	)
	outcome = _upsert_by_code(
		"Strategic Outcome",
		"outcome_code",
		OBJECTIVE_CODE,
		{
			"plan_version": plan_name,
			"programme": prog,
			"sub_programme": sub,
			"title": OBJECTIVE_TITLE,
			"description": OBJECTIVE_DESCRIPTION,
			"responsible_function": "Digital Health Directorate",
			"executive_owner": "Director, Digital Health",
			"order_index": 1,
		},
	)
	indicator = _upsert_by_code(
		"Performance Indicator",
		"indicator_code",
		INDICATOR_CODE,
		{
			"plan_version": plan_name,
			"strategic_outcome": outcome,
			"title": INDICATOR_TITLE,
			"definition": "Percentage of time core clinical information systems are available.",
			"measurement_type": "Percentage",
			"unit": "%",
			"measurement_frequency": "Monthly",
			"data_source": "Approved infrastructure-monitoring report",
			"responsible_function": "ICT Operations",
			"order_index": 1,
		},
	)
	target = _upsert_by_code(
		"Performance Target",
		"target_code",
		TARGET_CODE,
		{
			"plan_version": plan_name,
			"performance_indicator": indicator,
			"title": TARGET_TITLE,
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
		},
	)

	# Commitments for first two PVOs linked to outcome/target
	for code, level in (("PVO-EFT-01", "Required consideration"), ("PVO-ECO-01", "Recommended consideration")):
		existing = frappe.db.get_value(
			"Plan Value Commitment",
			{"plan_version": plan_name, "public_value_objective_version": pvos[code]},
			"name",
		)
		if existing:
			continue
		c = frappe.get_doc(
			{
				"doctype": "Plan Value Commitment",
				"plan_version": plan_name,
				"public_value_objective_version": pvos[code],
				"rationale": f"Aligned to {code} for digital health investments",
				"consideration_level": level,
				"responsible_owner": "Digital Health Directorate",
				"status": "Draft",
				"links": [
					{"link_type": "Strategic Outcome", "linked_outcome": outcome},
					{"link_type": "Performance Target", "linked_target": target},
				],
			}
		)
		c.insert(ignore_permissions=True)

	# Activate via transitions (Administrator)
	status = frappe.db.get_value("Strategic Plan", plan_name, "status")
	if status == "Draft":
		transition_plan(plan_name, "Submit")
		transition_plan(plan_name, "Approve")
		transition_plan(plan_name, "Activate")
	elif status == "Submitted":
		transition_plan(plan_name, "Approve")
		transition_plan(plan_name, "Activate")
	elif status == "Approved":
		transition_plan(plan_name, "Activate")

	meas = _ensure_measurements(plan_name, target)
	frappe.db.commit()
	return {
		"ok": True,
		"skipped": False,
		"created": created,
		"plan": plan_name,
		"plan_code": STRATEGY_PLAN_CODE,
		"program": prog,
		"sub_program": sub,
		"objective": outcome,
		"indicator": indicator,
		"target": target,
		"measurements": meas,
		"pvos": pvos,
		"procuring_entity": pe,
	}
