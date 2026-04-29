"""Tender Management STD panel payload (STD-CURSOR-1108)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.instance_readiness_panel_service import (
	build_std_instance_readiness_panel,
)
from kentender_procurement.std_engine.services.tender_binding_service import get_tender_std_binding


def build_tender_std_panel(tender_code: str, actor: str | None = None) -> dict[str, Any]:
	"""Aggregate STD binding, instance status, outputs, blockers for Tender STD Configuration UI."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	tc = (tender_code or "").strip()
	if not tc:
		return {"ok": False, "error": "invalid", "message": str(_("Tender code is required."))}

	bind = get_tender_std_binding(tc)
	binding = bind.get("binding")
	instance_code = str(binding.get("std_instance_code") or "").strip() if binding else ""

	blockers: list[str] = []
	readiness = None
	outputs_summary: dict[str, Any] = {}
	panel_readiness = None
	inst_status: str | None = None

	if instance_code:
		resolved = resolve_std_document("STD Instance", instance_code)
		if resolved:
			dt, nm, inst = resolved
			if _perm_read(dt, nm, user):
				inst_status = str(inst.get("instance_status") or "")
				readiness = str(inst.get("readiness_status") or "")
				panel_readiness = build_std_instance_readiness_panel(instance_code, actor=user)
				for f in (panel_readiness.get("findings") or [])[:20]:
					if f.get("blocks_publication"):
						blockers.append(str(f.get("message") or f.get("rule_code") or ""))
				for o in panel_readiness.get("output_references") or []:
					outputs_summary[str(o.get("output_type") or "")] = {
						"output_code": o.get("output_code"),
						"status": o.get("status"),
						"is_stale": bool(int(o.get("is_stale") or 0)),
					}

	return {
		"ok": True,
		"tender_code": tc,
		"binding": binding,
		"std_instance_code": instance_code or None,
		"template_version_code": str(binding.get("std_template_version_code") or "") if binding else None,
		"profile_code": str(binding.get("std_profile_code") or "") if binding else None,
		"instance_status": inst_status,
		"readiness_status": readiness,
		"generated_outputs": {
			"bundle": binding.get("std_bundle_code") if binding else None,
			"dsm": binding.get("std_dsm_code") if binding else None,
			"dom": binding.get("std_dom_code") if binding else None,
			"dem": binding.get("std_dem_code") if binding else None,
			"dcm": binding.get("std_dcm_code") if binding else None,
			"detail": outputs_summary,
		},
		"blockers": [b for b in blockers if b],
		"std_outputs_current": bool(binding.get("std_outputs_current")) if binding else False,
		"hide_manual_attachment_ui": True,
		"hide_manual_rule_configuration": True,
		"readiness_panel": panel_readiness,
	}
