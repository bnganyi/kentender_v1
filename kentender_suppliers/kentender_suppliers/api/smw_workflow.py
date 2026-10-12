# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from kentender_suppliers.services import governance
from kentender_suppliers.services import eligibility as elig_service
from kentender_suppliers.services import registry_access


def _require(capability: str) -> None:
	"""One named-capability check per entry point (AUD-XC-004/019)."""
	registry_access.require_capability(capability)


@frappe.whitelist()
def ktsm_submit_for_review(supplier_profile: str) -> dict:
	"""Internal desk – registry may submit for supplier (when supported)."""
	registry_access.require_capability(
		"prepare_registration", _("Not permitted to submit this profile for review.")
	)
	governance.submit_for_review(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_start_review(supplier_profile: str) -> dict:
	_require("start_review")
	governance.start_review(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_approve_supplier(supplier_profile: str) -> dict:
	_require("decide_registration")
	governance.approve_supplier(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_return_supplier(supplier_profile: str, reason: str) -> dict:
	_require("decide_registration")
	governance.return_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_supplier(supplier_profile: str, reason: str) -> dict:
	_require("decide_registration")
	governance.reject_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_suspend(supplier_profile: str, reason: str) -> dict:
	_require("change_operational_status")
	governance.suspend_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reinstate(supplier_profile: str, reason: str) -> dict:
	_require("change_operational_status")
	governance.reinstate_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_blacklist(supplier_profile: str, reason: str) -> dict:
	"""F2: Blacklist; requires role (H1)."""
	_require("blacklist")
	governance.blacklist_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_verify_document(document_name: str) -> dict:
	_require("verify_documents")
	governance.verify_document(document_name)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_document(document_name: str, reason: str) -> dict:
	_require("verify_documents")
	governance.reject_document(document_name, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_check_eligibility(supplier_code: str, category_code: str | None = None) -> dict:
	"""Internal + optional external (no _internal_ keys)."""
	_require("read_registry")
	r = elig_service.check_supplier_eligibility(supplier_code, category_code)
	return r


@frappe.whitelist()
def ktsm_set_expired(supplier_profile: str, reason: str) -> dict:
	"""C2: operational → Expired (internal / registry)."""
	_require("expire_supplier")
	governance.set_operational_expired(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_qualify_category(assignment_name: str, qualified_until: str | None = None) -> dict:
	"""F2: qualify category row."""
	_require("decide_category")
	d = None
	if qualified_until:
		from frappe.utils import getdate
		d = getdate(qualified_until)
	governance.qualify_supplier_category(assignment_name, d)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_category(assignment_name: str, reason: str) -> dict:
	_require("decide_category")
	governance.reject_supplier_category(assignment_name, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_start_category_review(assignment_name: str) -> dict:
	_require("start_category_review")
	governance.start_category_review(assignment_name)
	return {"ok": True}
