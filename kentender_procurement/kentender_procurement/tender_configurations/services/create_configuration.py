# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create / load Tender Configuration — PP2 Package create path retired."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr


def create_tender_configuration(
	package_id: str,
	std_document_id: str | None = None,
) -> dict[str, Any]:
	"""PP2 create-from-package retired until MVP-1 Plan Item handoff."""
	frappe.throw(
		_(
			"Creating a tender configuration from a procurement package is retired. "
			"MVP-1 Plan Item take-up will restore this flow."
		),
		frappe.ValidationError,
		title="TCFG_PACKAGE_RETIRED",
	)


def get_configuration(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(_("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return {
		"configuration_id": doc.name,
		"configuration_ref": doc.configuration_ref,
		"tender_title": doc.tender_title,
		"status": doc.status,
		"procurement_package_ref": doc.procurement_package_ref,
		"std_family_label": doc.std_family_label,
		"std_document_label": doc.std_document_label,
		"procuring_entity_name": doc.procuring_entity_name,
		"procurement_method": doc.procurement_method,
		"blocker_count": doc.blocker_count or 0,
		"warning_count": doc.warning_count or 0,
		"modified": str(doc.modified),
	}
