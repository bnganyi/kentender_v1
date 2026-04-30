from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.evidence_export_service import (
	build_std_evidence_export_package,
)


@frappe.whitelist()
def export_std_evidence_package(
	object_type: str | None = None,
	object_code: str | None = None,
) -> dict:
	"""STD-CURSOR-1301: whitelisted evidence export API for workbench actions."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return build_std_evidence_export_package(
		str(object_type or "").strip(),
		str(object_code or "").strip(),
		actor=frappe.session.user,
	)

