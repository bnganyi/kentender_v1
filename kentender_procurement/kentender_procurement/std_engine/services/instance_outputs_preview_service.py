"""STD workbench: generated outputs preview (STD-CURSOR-1105)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def build_std_instance_outputs_preview(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}

	doctype, name, _inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	outputs = frappe.get_all(
		"STD Generated Output",
		filters={"instance_code": code},
		fields=[
			"output_code",
			"output_type",
			"status",
			"is_stale",
			"stale_reason",
			"version_number",
			"generated_by_job_code",
			"source_addendum_code",
		],
		order_by="output_type asc, modified desc",
		limit=200,
	)
	by_type: dict[str, list[dict[str, Any]]] = {}
	for o in outputs:
		t = str(o.get("output_type") or "Unknown")
		by_type.setdefault(t, []).append(dict(o))

	jobs = frappe.get_all(
		"STD Generation Job",
		filters={"instance_code": code},
		fields=["generation_job_code", "job_type", "status", "error_message", "modified"],
		order_by="modified desc",
		limit=30,
	)

	failed = [j for j in jobs if str(j.get("status") or "").lower() in ("failed", "error")]

	return {
		"ok": True,
		"instance_code": code,
		"outputs_by_type": by_type,
		"generation_jobs": jobs,
		"failed_jobs": failed,
		"warnings": {
			"dem": str(
				_(
					"Evaluation criteria are generated from the STD instance. "
					"They cannot be edited in Tender Management or Evaluation."
				)
			),
			"dom": str(_("Opening does not perform arithmetic correction. Arithmetic correction is part of Evaluation.")),
			"dcm": str(
				_(
					"Contract price source is defined by DCM and must follow the corrected evaluated BOQ total after Evaluation/Award."
				)
			),
		},
	}
