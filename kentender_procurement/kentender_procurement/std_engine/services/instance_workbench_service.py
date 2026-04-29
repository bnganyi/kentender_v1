"""STD workbench: STD Instance shell for detail tabs (STD-CURSOR-1101)."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def build_std_instance_workbench_shell(instance_code: str, actor: str | None = None) -> dict[str, object]:
	"""Return workbench shell flags and reference fields for an STD Instance (read-only + addendum guidance)."""
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {
			"ok": False,
			"error": "not_found",
			"message": str(_("No document matches this instance code.")),
			"instance_code": code,
		}

	doctype, name, doc = resolved
	if doctype != "STD Instance":
		return {"ok": False, "error": "invalid", "message": str(_("Not an STD instance."))}

	if not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	inst_status = str(doc.get("instance_status") or "")
	readiness = str(doc.get("readiness_status") or "")
	read_only = inst_status in ("Published Locked", "Superseded", "Cancelled")

	addendum_guidance = ""
	if inst_status == "Published Locked":
		addendum_guidance = str(
			_(
				"Post-publication changes must follow the addendum workflow. "
				"Use Addendum Impact in this workbench or Tender Management to assess and route changes."
			)
		)
	elif inst_status == "Locked Pre-Publication":
		addendum_guidance = str(
			_(
				"Pre-publication lock is active. After publication, substantive changes require an addendum; "
				"complete readiness checks before locking."
			)
		)
	elif inst_status == "Superseded":
		addendum_guidance = str(
			_("This instance was superseded. Align downstream contracts with the replacement instance.")
		)

	return {
		"ok": True,
		"instance_code": code,
		"tender_code": str(doc.get("tender_code") or ""),
		"template_version_code": str(doc.get("template_version_code") or ""),
		"profile_code": str(doc.get("profile_code") or ""),
		"instance_status": inst_status,
		"readiness_status": readiness,
		"read_only": read_only,
		"addendum_guidance": addendum_guidance,
	}
