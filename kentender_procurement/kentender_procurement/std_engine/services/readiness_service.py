from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.boq_instance_service import validate_boq_instance
from kentender_procurement.std_engine.services.works_requirements_service import validate_works_requirements


def _write_instance_readiness(instance, status: str) -> None:
	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = status
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False


def _supersede_prior_readiness_runs(object_type: str, object_code: str) -> None:
	for name in frappe.get_all(
		"STD Readiness Run",
		filters={"object_type": object_type, "object_code": object_code, "status": ("!=", "Superseded")},
		pluck="name",
	):
		frappe.flags.std_transition_service_context = True
		try:
			doc = frappe.get_doc("STD Readiness Run", name)
			doc.status = "Superseded"
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False


def _severity_rank(sev: str) -> int:
	return {"Critical": 4, "High": 3, "Warning": 2, "Info": 1}.get(sev, 0)


def _derive_run_status(findings: list[tuple[str, str, str]]) -> str:
	if not findings:
		return "Ready"
	ranks = [_severity_rank(s) for _, s, _ in findings]
	if max(ranks) >= 4:
		return "Blocked"
	if max(ranks) >= 3:
		return "Blocked"
	if max(ranks) >= 2:
		return "Warning"
	return "Incomplete"


@frappe.whitelist()
def run_std_readiness(object_type: str, object_code: str, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-0701 — evaluate STD instance against readiness rules; persist run + findings."""
	actor = actor or frappe.session.user
	ot = (object_type or "").strip().upper()
	if ot != "STD_INSTANCE":
		frappe.throw(_("Only STD_INSTANCE readiness is supported."), title=_("STD readiness"))

	inst_name = frappe.db.get_value("STD Instance", {"instance_code": object_code}, "name")
	if not inst_name:
		frappe.throw(_("STD Instance not found."), title=_("STD readiness"))
	instance = frappe.get_doc("STD Instance", inst_name)

	findings: list[tuple[str, str, str]] = []

	ver_status = frappe.db.get_value("STD Template Version", instance.template_version_code, "version_status")
	if ver_status != "Active":
		findings.append(("R_TEMPLATE_VERSION_ACTIVE", "Critical", f"Template version must be Active (is {ver_status})."))

	prof_status = frappe.db.get_value("STD Applicability Profile", instance.profile_code, "profile_status")
	if prof_status != "Active":
		findings.append(("R_PROFILE_ACTIVE", "Critical", f"Applicability profile must be Active (is {prof_status})."))

	sec_count = frappe.db.count("STD Section Definition", {"version_code": instance.template_version_code})
	if sec_count < 1:
		findings.append(("R_MANDATORY_SECTIONS", "High", "No section definitions for template version."))

	req_params = frappe.get_all(
		"STD Parameter Definition",
		filters={"version_code": instance.template_version_code, "required": 1},
		pluck="parameter_code",
	)
	for pcode in req_params:
		if not frappe.db.exists("STD Instance Parameter Value", {"instance_code": object_code, "parameter_code": pcode}):
			findings.append(("R_REQUIRED_PARAMETER", "High", f"Required parameter not set: {pcode}"))

	wr = validate_works_requirements(object_code, persist=False)
	if not wr.get("is_valid"):
		for b in wr.get("blockers") or []:
			findings.append(
				(
					f"R_WORKS_{b.get('component_code', 'UNK')}",
					"High",
					f"Works requirement blocker: {b.get('reason')}",
				)
			)

	boq = validate_boq_instance(object_code)
	if not boq.get("is_valid"):
		findings.append(("R_BOQ_COMPLETE", "Critical", "BOQ is incomplete or not initialized."))

	for out_type in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
		row = frappe.db.get_value(
			"STD Generated Output",
			{"instance_code": object_code, "output_type": out_type, "status": "Current"},
			["name", "is_stale", "output_code"],
			as_dict=True,
		)
		if not row:
			findings.append((f"R_OUTPUT_CURRENT_{out_type.upper()}", "Critical", f"No Current {out_type} generated output."))
		elif int(row.get("is_stale") or 0):
			findings.append(
				(
					f"R_OUTPUT_STALE_{out_type.upper()}",
					"Critical",
					f"Current {out_type} output is stale ({row.get('output_code')}).",
				)
			)

	run_status = _derive_run_status(findings)
	readiness_run_code = f"RRUN-{frappe.generate_hash(length=10).upper()}"
	_supersede_prior_readiness_runs(ot, object_code)

	run = frappe.get_doc(
		{
			"doctype": "STD Readiness Run",
			"readiness_run_code": readiness_run_code,
			"object_type": ot,
			"object_code": object_code,
			"status": run_status,
			"run_at": datetime.utcnow(),
		}
	).insert(ignore_permissions=True)

	for rule_code, severity, message in findings:
		frappe.get_doc(
			{
				"doctype": "STD Readiness Finding",
				"finding_code": f"RD-{frappe.generate_hash(length=8).upper()}",
				"readiness_run_code": readiness_run_code,
				"severity": severity,
				"rule_code": rule_code,
				"message": message,
			}
		).insert(ignore_permissions=True)

	_write_instance_readiness(instance, run_status)

	record_std_audit_event(
		"READINESS_RUN_CREATED",
		"STD Readiness Run",
		readiness_run_code,
		actor=actor,
		new_state=run_status,
		metadata={"object_code": object_code, "finding_count": len(findings)},
	)

	return {
		"readiness_run_code": readiness_run_code,
		"status": run_status,
		"findings": [{"rule_code": c, "severity": s, "message": m} for c, s, m in findings],
		"instance_readiness_status": run_status,
	}
