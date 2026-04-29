"""STD workbench: works requirements + attachments panel (STD-CURSOR-1103)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.works_requirements_service import get_works_requirement_components


def build_std_instance_works_requirements_panel(instance_code: str, actor: str | None = None) -> dict[str, Any]:
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

	read_only = str(inst.get("instance_status") or "") in ("Published Locked", "Superseded", "Cancelled")

	components = get_works_requirement_components(code)

	attachments = frappe.get_all(
		"STD Section Attachment",
		filters={"instance_code": code},
		fields=[
			"attachment_code",
			"section_code",
			"component_code",
			"classification",
			"file_reference",
			"status",
		],
		order_by="modified desc",
		limit=200,
	)

	section_vii = frappe.db.get_value(
		"STD Section Definition",
		{"version_code": inst.template_version_code, "section_number": "VII"},
		"section_code",
	)

	derived = []
	for c in components:
		if int(c.get("drives_dsm") or 0) or int(c.get("drives_dem") or 0) or int(c.get("drives_dcm") or 0):
			derived.append(
				{
					"component_code": c.get("component_code"),
					"component_title": c.get("component_title"),
					"drives_dsm": bool(int(c.get("drives_dsm") or 0)),
					"drives_dem": bool(int(c.get("drives_dem") or 0)),
					"drives_dcm": bool(int(c.get("drives_dcm") or 0)),
				}
			)

	return {
		"ok": True,
		"instance_code": code,
		"read_only": read_only,
		"components": components,
		"attachments": attachments,
		"section_vii_section_code": section_vii,
		"attachment_action_labels": {
			"section_bound": str(_("Add Section-Bound Attachment")),
			"drawing_register": str(_("Add Drawing to Register")),
			"specification": str(_("Add Specification Attachment")),
			"supersede": str(_("Supersede Attachment by Addendum")),
		},
		"derived_impacts": derived,
	}
