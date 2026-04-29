from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.std_engine.services.tender_std_panel_service import build_tender_std_panel


@frappe.whitelist()
def get_tender_std_panel_data(tender_code: str | None = None) -> dict:
	"""STD configuration summary for Tender Management panel (STD-CURSOR-1108)."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	return build_tender_std_panel(str(tender_code or "").strip())
