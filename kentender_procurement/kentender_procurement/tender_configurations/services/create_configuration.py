# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create Tender Configuration from an approved procurement package."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	ACTIVE_CONFIGURATION_STATUSES,
	ELIGIBLE_PACKAGE_STATUSES,
	STATUS_IN_PROGRESS,
	UI_01_ROUTE,
)
from kentender_procurement.tender_configurations.services.eligibility import (
	get_package_or_throw,
	packages_with_active_configuration,
	resolve_applicable_std_document,
)
from kentender_procurement.tender_configurations.services.std_family_map import (
	resolve_procuring_entity_name,
)


def _next_configuration_ref(package_code: str) -> str:
	base = f"TCFG-{cstr(package_code).strip()}"
	if not frappe.db.exists("Tender Configuration", base):
		return base
	# Collision: append short hash
	return f"{base}-{frappe.generate_hash(length=4).upper()}"


def create_tender_configuration(
	package_id: str,
	std_document_id: str | None = None,
) -> dict[str, Any]:
	"""Validate and create a Tender Configuration. Returns C1-M2 response shape."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required."), frappe.PermissionError)

	if not frappe.has_permission("Tender Configuration", "create"):
		frappe.throw(
			_("You do not have permission to create a tender configuration for this package."),
			frappe.PermissionError,
			title="TCFG_PERMISSION",
		)

	package_id = cstr(package_id or "").strip()
	if not package_id:
		frappe.throw(
			_("Select an approved procurement package before creating a configuration."),
			title="TCFG_PACKAGE_REQUIRED",
		)

	pkg = get_package_or_throw(package_id)
	status = cstr(pkg.status or "").strip()
	if status not in ELIGIBLE_PACKAGE_STATUSES:
		frappe.throw(
			_("Only approved procurement packages can be used to create a tender configuration."),
			title="TCFG_PACKAGE_NOT_APPROVED",
		)

	configured = packages_with_active_configuration()
	if pkg.name in configured:
		frappe.throw(
			_(
				"This procurement package already has a tender configuration. "
				"Open the existing configuration instead."
			),
			title="TCFG_PACKAGE_ALREADY_CONFIGURED",
		)

	std = resolve_applicable_std_document(pkg, std_document_id=std_document_id)
	if not std.get("ok") or not std.get("applicable_std_document_id"):
		frappe.throw(
			_(
				"No active Standard Tender Document is available for this procurement package. "
				"Contact the STD administrator."
			),
			title="TCFG_NO_STD",
		)

	package_code = cstr(pkg.package_code or pkg.name)
	entity_code = cstr(pkg.procuring_entity_code or "")
	title = cstr(pkg.package_name or package_code)
	ref = _next_configuration_ref(package_code)

	from kentender_procurement.tender_configurations.services.configuration_home import (
		default_steps_state_for_seed,
	)

	doc = frappe.get_doc(
		{
			"doctype": "Tender Configuration",
			"configuration_ref": ref,
			"tender_title": title,
			"status": STATUS_IN_PROGRESS,
			"procurement_package": pkg.name,
			"procurement_package_ref": package_code,
			"package_title": title,
			"procuring_entity_code": entity_code,
			"procuring_entity_name": resolve_procuring_entity_name(entity_code) or entity_code,
			"procurement_method": cstr(pkg.procurement_method or ""),
			"std_family_key": std["std_family_key"],
			"std_family_label": std["std_family_label"],
			"std_version": std["applicable_std_document_id"],
			"std_document_label": std["applicable_std_document_label"],
			"blocker_count": 0,
			"warning_count": 0,
			"steps_state": default_steps_state_for_seed(needs_attention=False),
			"approval_date": pkg.approved_at,
		}
	)
	doc.insert(ignore_permissions=False)
	frappe.db.commit()

	return {
		"configuration_id": doc.name,
		"configuration_ref": doc.configuration_ref,
		"std_family_key": doc.std_family_key,
		"std_family_label": doc.std_family_label,
		"redirect_route": f"/desk/{UI_01_ROUTE}?configuration_id={doc.name}",
		"created_at": str(now_datetime()),
	}


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
