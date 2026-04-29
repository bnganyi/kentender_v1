"""STD workbench: readiness panel (STD-CURSOR-1106)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def _severity_rank(sev: str) -> int:
	return {"Critical": 4, "High": 3, "Warning": 2, "Info": 1}.get(str(sev or ""), 0)


def build_std_instance_readiness_panel(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}

	doctype, name, inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	latest = frappe.get_all(
		"STD Readiness Run",
		filters={"object_type": "STD_INSTANCE", "object_code": code},
		fields=["readiness_run_code", "status", "run_at"],
		order_by="run_at desc",
		limit=1,
	)
	run_code = latest[0]["readiness_run_code"] if latest else None
	findings: list[dict[str, Any]] = []
	if run_code:
		findings = frappe.get_all(
			"STD Readiness Finding",
			filters={"readiness_run_code": run_code},
			fields=["finding_code", "severity", "rule_code", "message"],
			limit=500,
		)
		findings.sort(key=lambda f: _severity_rank(str(f.get("severity") or "")), reverse=True)

	history = frappe.get_all(
		"STD Readiness Run",
		filters={"object_type": "STD_INSTANCE", "object_code": code},
		fields=["readiness_run_code", "status", "run_at"],
		order_by="run_at desc",
		limit=12,
	)

	outputs = frappe.get_all(
		"STD Generated Output",
		filters={"instance_code": code, "status": ("in", ["Current", "Published"])},
		fields=["output_code", "output_type", "status", "is_stale"],
		limit=20,
	)

	return {
		"ok": True,
		"instance_code": code,
		"instance_readiness_status": str(inst.get("readiness_status") or ""),
		"latest_run": {"readiness_run_code": run_code, "status": latest[0]["status"], "run_at": latest[0]["run_at"]}
		if latest
		else None,
		"findings": [
			{
				**f,
				"source_object": "—",
				"owner_module": "STD Engine",
				"resolution_action": "—",
				"blocks_publication": str(f.get("severity") or "") in ("Critical", "High"),
			}
			for f in findings
		],
		"output_references": outputs,
		"validation_history": history,
		"manual_ready_forbidden": True,
		"manual_ready_message": str(
			_("Readiness status is derived from the engine; manual Ready is not permitted on the instance.")
		),
	}
