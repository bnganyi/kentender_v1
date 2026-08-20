# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KENTENDER_MVP_V1 Strategy seed — Contract v2.0 §5 identities."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.kentender_mvp_v1 import constants as C
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_plan

# (commitment_code, commitment statement, requirement_level) — STR-CHG-001 §5: no PVO catalogue.
PVC_FIXTURE = (
	("MOH-PVC-EFT-01", "Improve availability of critical health services", "Required consideration"),
	("MOH-PVC-ECO-01", "Reduce whole-life infrastructure cost", "Required consideration"),
	("MOH-PVC-EFY-01", "Reduce implementation and service-restoration time", "Recommended consideration"),
	("MOH-PVC-RES-01", "Improve continuity of critical services", "Recommended consideration"),
	("MOH-PVC-LOC-01", "Develop internal and local technical capability", "Required consideration"),
	("MOH-PVC-SUS-01", "Reduce infrastructure energy consumption", "Recommended consideration"),
	("MOH-PVC-SUS-02", "Ensure compliant handling of replaced ICT equipment", "Required consideration"),
	("MOH-PVC-INT-01", "Minimise uncontrolled contract changes", "Required consideration"),
)

OWN_DHP = {"owner_org_unit": C.OU_DIR_DHP, "fixture_namespace": C.FIXTURE_NS}
OWN_HRMD = {"owner_org_unit": C.OU_DIR_HRMD, "fixture_namespace": C.FIXTURE_NS}
OWN_CGK = {"owner_org_unit": C.OU_CGK_HEALTH, "fixture_namespace": C.FIXTURE_NS}
OWN_ENTITY = {"owner_org_unit": "", "fixture_namespace": C.FIXTURE_NS}


def _pe_moh() -> str:
	from kentender_core.seeds._common import ensure_procuring_entity

	return ensure_procuring_entity(C.PE_MOH, C.PE_MOH_NAME, entity_type="Ministry", short_name="MoH")


def _pe_cgk() -> str:
	from kentender_core.seeds._common import ensure_procuring_entity

	return ensure_procuring_entity(
		C.PE_CGKIS, C.PE_CGKIS_NAME, entity_type="County Government", short_name="Kisumu"
	)


def _upsert_strategy_scope(
	*,
	strategy_doctype: str,
	strategy_item: str,
	strategy_item_code: str,
	pe: str,
	org_unit: str,
	plan_version: str,
	include_descendants: int = 1,
	applicability: str = "Required",
) -> None:
	existing = frappe.db.get_value(
		"Strategy Scope Assignment",
		{
			"strategy_doctype": strategy_doctype,
			"strategy_item": strategy_item,
			"organisation_unit": org_unit,
			"fixture_namespace": C.FIXTURE_NS,
		},
		"name",
	)
	if existing:
		return
	frappe.get_doc(
		{
			"doctype": "Strategy Scope Assignment",
			"strategy_doctype": strategy_doctype,
			"strategy_item": strategy_item,
			"strategy_item_code": strategy_item_code,
			"procuring_entity": pe,
			"organisation_unit": org_unit,
			"include_descendants": include_descendants,
			"applicability": applicability,
			"plan_version": plan_version,
			"fixture_namespace": C.FIXTURE_NS,
		}
	).insert(ignore_permissions=True)


def _upsert(doctype: str, code_field: str, code: str, values: dict) -> str:
	existing = frappe.db.get_value(doctype, {code_field: code}, "name")
	payload = {code_field: code, **values}
	if existing:
		# Always refresh ownership / fixture tags even on Active plans.
		own_keys = ("fixture_namespace", "owner_org_unit")
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


def clear_kentender_mvp_v1_strategy(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, Any]:
	"""Delete fixture-tagged Strategy records (MOH + CGK codes) — no broad PE wipe."""
	deleted: dict[str, int] = {}
	namespaces = [C.FIXTURE_NS, C.LEGACY_FIXTURE_NS] if include_canonical else []
	if include_playwright:
		namespaces.append(C.PLAYWRIGHT_FIXTURE_NS)
	plans: list[str] = []
	if namespaces and frappe.db.has_column("Strategic Plan", "fixture_namespace"):
		plans.extend(
			frappe.get_all(
				"Strategic Plan",
				filters={"fixture_namespace": ["in", list(namespaces)]},
				pluck="name",
			)
		)
	if include_canonical:
		for code in (C.PLAN_CODE, C.CGK_PLAN_CODE, "MOH-SP-0001"):
			plans.extend(
				frappe.get_all("Strategic Plan", filters={"plan_code": code}, pluck="name")
			)
	if include_playwright:
		# Legacy STR Playwright creation predates fixture_namespace. Its title is
		# deliberately test-specific, so it can be removed without a PE-wide wipe.
		plans.extend(
			frappe.get_all(
				"Strategic Plan",
				filters={"title": ["like", "Playwright Create %"]},
				pluck="name",
			)
		)
	seen_plans: set[str] = set()
	uniq_plans: list[str] = []
	for p in plans:
		if p and p not in seen_plans:
			seen_plans.add(p)
			uniq_plans.append(p)
	plans = uniq_plans

	child_doctypes = (
		"Strategy Audit Event",
		"Performance Measurement",
		"Strategy Value Commitment",
		"Performance Target",
		"Performance Indicator",
		"Strategic Objective",
		"Strategic Outcome",
		"Strategy Sub Programme",
		"Strategy Programme",
	)
	for doctype in child_doctypes:
		names: list[str] = []
		if namespaces and frappe.db.has_column(doctype, "fixture_namespace"):
			names.extend(
				frappe.get_all(
					doctype,
					filters={"fixture_namespace": ["in", list(namespaces)]},
					pluck="name",
				)
			)
		for p in plans:
			if frappe.db.has_column(doctype, "plan_version"):
				names.extend(
					frappe.get_all(doctype, filters={"plan_version": p}, pluck="name")
				)
		seen: set[str] = set()
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

	if namespaces and frappe.db.exists("DocType", "Strategy Scope Assignment"):
		ssa = 0
		for name in frappe.get_all(
			"Strategy Scope Assignment",
			filters={"fixture_namespace": ["in", list(namespaces)]},
			pluck="name",
		):
			frappe.delete_doc("Strategy Scope Assignment", name, force=1, ignore_permissions=True)
			ssa += 1
		deleted["Strategy Scope Assignment"] = ssa
	return {"ok": True, "deleted": deleted}


def upsert_kentender_mvp_v1_strategy(*, reset: bool = False) -> dict[str, Any]:
	ensure_strategy_roles()
	pe = _pe_moh()
	if reset:
		clear_kentender_mvp_v1_strategy()

	# Migrate legacy code in place if old plan still exists
	legacy = frappe.db.get_value("Strategic Plan", {"plan_code": "MOH-SP-0001"}, "name")
	if legacy and not frappe.db.exists("Strategic Plan", {"plan_code": C.PLAN_CODE}):
		frappe.db.set_value(
			"Strategic Plan", legacy, "plan_code", C.PLAN_CODE, update_modified=False
		)

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
				"description": "Canonical KENTENDER_MVP_V1 Ministry strategic plan.",
				"fixture_namespace": C.FIXTURE_NS,
				"owner_org_unit": "",
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
				"owner_org_unit": "",
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
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
			**OWN_DHP,
		},
	)

	# Strategic Objective sits alongside the Outcome above (STR-CHG-001 §6.2): an
	# Indicator may measure a Strategic Objective directly instead of an Outcome.
	obj_interop = _upsert(
		"Strategic Objective",
		"objective_code",
		C.OBJ_INTEROP,
		{
			"plan_version": plan_name,
			"programme": prog,
			"sub_programme": sub_his,
			"title": "Strengthen interoperable national digital health services",
			"description": "Strengthen interoperable national digital health services",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 2,
			**OWN_DHP,
		},
	)
	ind_interop = _upsert(
		"Performance Indicator",
		"indicator_code",
		C.IND_INTEROP,
		{
			"plan_version": plan_name,
			"strategic_objective": obj_interop,
			"title": "Percentage of priority facilities using interoperable digital health services",
			"definition": "Percentage of priority facilities exchanging data via interoperable digital health services.",
			"measurement_type": "Percentage",
			"unit": "%",
			"measurement_frequency": "Quarterly",
			"data_source": "Approved interoperability-adoption report",
			"responsible_function": C.DIR_DHP_NAME,
			"order_index": 1,
			**OWN_DHP,
		},
	)
	_upsert(
		"Performance Target",
		"target_code",
		C.TGT_INTEROP_2028,
		{
			"plan_version": plan_name,
			"performance_indicator": ind_interop,
			"title": "At least 80% of priority facilities interoperable by 30 June 2028",
			"comparison_direction": "At least",
			"target_numeric": 80.0,
			"baseline_status": "Known",
			"baseline_numeric": 42.0,
			"baseline_as_of": "2026-06-30",
			"baseline_source": "FY2025/26 interoperability-adoption report",
			"tolerance_value": 1.0,
			"period_start": "2026-07-01",
			"period_end": "2028-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_DHP,
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
			**OWN_HRMD,
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
			**OWN_HRMD,
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
			**OWN_HRMD,
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
			**OWN_HRMD,
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
			**OWN_HRMD,
		},
	)

	# PVCs
	pvcs: dict[str, str] = {}
	for pvc_code, statement, level in PVC_FIXTURE:
		existing = frappe.db.get_value(
			"Strategy Value Commitment", {"commitment_code": pvc_code}, "name"
		)
		if existing:
			frappe.db.set_value(
				"Strategy Value Commitment",
				existing,
				{"fixture_namespace": C.FIXTURE_NS, "status": "Locked"},
				update_modified=False,
			)
			pvcs[pvc_code] = existing
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Strategy Value Commitment",
				"commitment_code": pvc_code,
				"plan_version": plan_name,
				"rationale": statement,
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

	# §5.1 Strategy Scope Assignments (MOH)
	_upsert_strategy_scope(
		strategy_doctype="Strategy Programme",
		strategy_item=prog,
		strategy_item_code=C.PROG_DH,
		pe=pe,
		org_unit=C.OU_SDMS,
		plan_version=plan_name,
	)
	_upsert_strategy_scope(
		strategy_doctype="Strategy Sub Programme",
		strategy_item=sub_dhc,
		strategy_item_code=C.SUB_DHC,
		pe=pe,
		org_unit=C.OU_SDPHPS,
		plan_version=plan_name,
	)

	cgk = _seed_kisumu_strategy()

	return {
		"ok": True,
		"created": created,
		"plan": plan_name,
		"plan_code": C.PLAN_CODE,
		"target_avail": tgt_avail,
		"measurements": meas,
		"pvcs": pvcs,
		"procuring_entity": pe,
		"kisumu": cgk,
	}


def _seed_kisumu_strategy() -> dict[str, Any]:
	"""Contract §5.8–5.9 minimal county Strategy fixture."""
	pe = _pe_cgk()
	plan_name = frappe.db.get_value(
		"Strategic Plan", {"plan_code": C.CGK_PLAN_CODE, "version_number": 1}, "name"
	)
	created = False
	if not plan_name:
		plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": C.CGK_PLAN_CODE,
				"version_number": 1,
				"title": C.CGK_PLAN_TITLE,
				"procuring_entity": pe,
				"plan_type": "Entity Strategic Plan",
				"scope_type": "Procuring Entity",
				"scope_id": pe,
				"status": "Draft",
				"start_date": "2027-07-01",
				"end_date": "2028-06-30",
				"description": "Canonical KENTENDER_MVP_V1 Kisumu county health plan.",
				"fixture_namespace": C.FIXTURE_NS,
				"owner_org_unit": C.OU_CGK_HEALTH,
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
				"title": C.CGK_PLAN_TITLE,
				"fixture_namespace": C.FIXTURE_NS,
				"owner_org_unit": C.OU_CGK_HEALTH,
				"procuring_entity": pe,
			},
			update_modified=False,
		)

	status = frappe.db.get_value("Strategic Plan", plan_name, "status")
	rebuild = status in ("Draft", "Returned") or created
	if rebuild and status not in ("Draft", "Returned"):
		frappe.db.set_value("Strategic Plan", plan_name, "status", "Draft", update_modified=False)

	# Minimal programme scaffolding (Outcome DocType requires programme).
	prog = _upsert(
		"Strategy Programme",
		"programme_code",
		"CGK-PROG-HEALTH",
		{
			"plan_version": plan_name,
			"title": "County Health Services",
			"description": "Kisumu county health services operational programme.",
			"responsible_function": C.OU_CGK_HEALTH_NAME,
			"order_index": 1,
			**OWN_CGK,
		},
	)
	sub = _upsert(
		"Strategy Sub Programme",
		"sub_programme_code",
		"CGK-SUB-COLDCHAIN",
		{
			"plan_version": plan_name,
			"programme": prog,
			"title": "Vaccine Cold Chain",
			"description": "Vaccine cold-chain reliability",
			"responsible_function": C.OU_CGK_HEALTH_NAME,
			"order_index": 1,
			**OWN_CGK,
		},
	)
	out = _upsert(
		"Strategic Outcome",
		"outcome_code",
		C.CGK_OUT_COLDCHAIN,
		{
			"plan_version": plan_name,
			"programme": prog,
			"sub_programme": sub,
			"title": "Reliable vaccine cold-chain services at county health facilities",
			"description": "Reliable vaccine cold-chain services at county health facilities",
			"responsible_function": C.OU_CGK_HEALTH_NAME,
			"executive_owner": "County Director of Health",
			"order_index": 1,
			**OWN_CGK,
		},
	)
	ind = _upsert(
		"Performance Indicator",
		"indicator_code",
		C.CGK_IND_COLDCHAIN,
		{
			"plan_version": plan_name,
			"strategic_outcome": out,
			"title": "Percentage of supported facilities meeting the cold-chain uptime standard",
			"definition": "Share of supported facilities meeting the cold-chain uptime standard.",
			"measurement_type": "Percentage",
			"unit": "%",
			"measurement_frequency": "Annual",
			"data_source": "County cold-chain monitoring report",
			"responsible_function": C.OU_CGK_HEALTH_NAME,
			"order_index": 1,
			**OWN_CGK,
		},
	)
	tgt = _upsert(
		"Performance Target",
		"target_code",
		C.CGK_TGT_COLDCHAIN,
		{
			"plan_version": plan_name,
			"performance_indicator": ind,
			"title": "At least 95% of supported facilities meet the uptime standard by 30 June 2028",
			"comparison_direction": "At least",
			"target_numeric": 95.0,
			"baseline_status": "Known",
			"baseline_numeric": 82.0,
			"baseline_as_of": "2027-06-30",
			"baseline_source": "FY2026/27 county health report",
			"tolerance_value": 2.0,
			"period_start": "2027-07-01",
			"period_end": "2028-06-30",
			"benefit_owner": "Administrator",
			"measurement_verifier": "Administrator",
			"status": "Active",
			**OWN_CGK,
		},
	)

	cgk_pvcs = (
		("CGK-PVC-EFT-01", "Improve availability of critical health services", "Required consideration"),
		("CGK-PVC-ECO-01", "Reduce whole-life infrastructure cost", "Required consideration"),
		("CGK-PVC-SUS-01", "Reduce infrastructure energy consumption", "Recommended consideration"),
	)
	pvcs: dict[str, str] = {}
	for pvc_code, statement, level in cgk_pvcs:
		existing = frappe.db.get_value(
			"Strategy Value Commitment", {"commitment_code": pvc_code}, "name"
		)
		if existing:
			frappe.db.set_value(
				"Strategy Value Commitment",
				existing,
				{"fixture_namespace": C.FIXTURE_NS, "status": "Locked", **OWN_CGK},
				update_modified=False,
			)
			pvcs[pvc_code] = existing
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Strategy Value Commitment",
				"commitment_code": pvc_code,
				"plan_version": plan_name,
				"rationale": statement,
				"consideration_level": level,
				"responsible_owner": C.OU_CGK_HEALTH_NAME,
				"status": "Locked",
				"links": [
					{"link_type": "Strategic Outcome", "linked_outcome": out},
					{"link_type": "Performance Target", "linked_target": tgt},
				],
				**OWN_CGK,
			}
		)
		doc.insert(ignore_permissions=True)
		pvcs[pvc_code] = doc.name

	_upsert_strategy_scope(
		strategy_doctype="Strategic Outcome",
		strategy_item=out,
		strategy_item_code=C.CGK_OUT_COLDCHAIN,
		pe=pe,
		org_unit=C.OU_CGK_HEALTH,
		plan_version=plan_name,
	)
	_upsert_strategy_scope(
		strategy_doctype="Performance Indicator",
		strategy_item=ind,
		strategy_item_code=C.CGK_IND_COLDCHAIN,
		pe=pe,
		org_unit=C.OU_CGK_HEALTH,
		plan_version=plan_name,
	)
	_upsert_strategy_scope(
		strategy_doctype="Performance Target",
		strategy_item=tgt,
		strategy_item_code=C.CGK_TGT_COLDCHAIN,
		pe=pe,
		org_unit=C.OU_CGK_HEALTH,
		plan_version=plan_name,
	)

	frappe.set_user("Administrator")
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

	return {
		"created": created,
		"plan": plan_name,
		"plan_code": C.CGK_PLAN_CODE,
		"target": tgt,
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
				**OWN_DHP,
			}
		)
		sep_doc.insert(ignore_permissions=True)
		sep = sep_doc.name
	else:
		frappe.db.set_value(
			"Performance Measurement", sep, OWN_DHP, update_modified=False
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
				"commentary": "Stabilised after remediation",
				"variance": 99.96 - 99.9,
				"result_status": "On track",
				"workflow_status": "Verified",
				"submitted_by": "Administrator",
				"verified_by": "Administrator",
				**OWN_DHP,
			}
		)
		oct_doc.insert(ignore_permissions=True)
		oct = oct_doc.name
	else:
		frappe.db.set_value(
			"Performance Measurement", oct, OWN_DHP, update_modified=False
		)
	ids["oct"] = oct
	return ids
