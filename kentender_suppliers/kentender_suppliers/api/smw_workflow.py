# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from kentender_suppliers.services import governance
from kentender_suppliers.services import eligibility as elig_service
from kentender_suppliers.services import supplier_policy


def _roles() -> set:
	return set(frappe.get_roles())


def _assert_approver_or_admin() -> None:
	"""[8. Smoke SCENARIO 12] only Approver / admin may approve, return, reject in workflow."""
	if not _roles() & {
		"System Manager",
		"Administrator",
		"KenTender Approving Authority",
	}:
		frappe.throw(_("Not permitted to act on this approval step."))


def _assert_compliance_reviewer() -> None:
	"""Document verify / reject: Compliance Officer, Approver, or admin (see doc 8)."""
	if not _roles() & {
		"System Manager",
		"Administrator",
		"KenTender Approving Authority",
		"KenTender Compliance Officer",
	}:
		frappe.throw(_("Not permitted to verify or reject documents in this system."))


def _assert_start_review() -> None:
	"""Move Submitted → Under Review: registry, compliance, approver, or admin."""
	if not _roles() & {
		"System Manager",
		"Administrator",
		"KenTender Approving Authority",
		"KenTender Supplier Registry Officer",
		"KenTender Compliance Officer",
	}:
		frappe.throw(_("Not permitted to start review for this profile."))


@frappe.whitelist()
def ktsm_submit_for_review(supplier_profile: str) -> dict:
	"""Internal desk – registry may submit for supplier (when supported)."""
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if not frappe.has_permission("KTSM Supplier Profile", "write", prof, throw=False):
		frappe.throw(_("Not permitted to submit this profile for review."))
	governance.submit_for_review(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_start_review(supplier_profile: str) -> dict:
	_assert_start_review()
	governance.start_review(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_approve_supplier(supplier_profile: str) -> dict:
	_assert_approver_or_admin()
	governance.approve_supplier(supplier_profile)
	return {"ok": True}


@frappe.whitelist()
def ktsm_return_supplier(supplier_profile: str, reason: str) -> dict:
	_assert_approver_or_admin()
	governance.return_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_supplier(supplier_profile: str, reason: str) -> dict:
	_assert_approver_or_admin()
	governance.reject_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_suspend(supplier_profile: str, reason: str) -> dict:
	governance.suspend_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reinstate(supplier_profile: str, reason: str) -> dict:
	governance.reinstate_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_blacklist(supplier_profile: str, reason: str) -> dict:
	"""F2: Blacklist; requires role (H1)."""
	if not supplier_policy.can_blacklist():
		frappe.throw(_("Not permitted to blacklist."))
	governance.blacklist_supplier(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_verify_document(document_name: str) -> dict:
	_assert_compliance_reviewer()
	governance.verify_document(document_name)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_document(document_name: str, reason: str) -> dict:
	_assert_compliance_reviewer()
	governance.reject_document(document_name, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_check_eligibility(supplier_code: str, category_code: str | None = None) -> dict:
	"""Internal + optional external (no _internal_ keys)."""
	r = elig_service.check_supplier_eligibility(supplier_code, category_code)
	return r


@frappe.whitelist()
def ktsm_set_expired(supplier_profile: str, reason: str) -> dict:
	"""C2: operational → Expired (internal / registry)."""
	governance.set_operational_expired(supplier_profile, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_qualify_category(assignment_name: str, qualified_until: str | None = None) -> dict:
	"""F2: qualify category row."""
	d = None
	if qualified_until:
		from frappe.utils import getdate
		d = getdate(qualified_until)
	governance.qualify_supplier_category(assignment_name, d)
	return {"ok": True}


@frappe.whitelist()
def ktsm_reject_category(assignment_name: str, reason: str) -> dict:
	governance.reject_supplier_category(assignment_name, reason)
	return {"ok": True}


@frappe.whitelist()
def ktsm_start_category_review(assignment_name: str) -> dict:
	governance.start_category_review(assignment_name)
	return {"ok": True}
