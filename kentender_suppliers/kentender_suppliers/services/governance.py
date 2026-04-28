# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_suppliers.services import compliance, eligibility, history, sod


def _save(
	profile_name: str, updates: dict
) -> "frappe.model.document.Document":
	prof = frappe.get_doc("KTSM Supplier Profile", profile_name)
	prof.flags.bypass_governance = True
	for k, v in updates.items():
		prof.set(k, v)
	prof.save(ignore_permissions=True)
	return prof


def assert_ready_for_submission(supplier_profile: str) -> None:
	"""B1/E2: require Complete compliance before first submission to review."""
	comp = compliance.recompute_compliance(supplier_profile)
	if comp != "Complete":
		frappe.throw(
			_("All required document types must be on file, verified, and not expired before submission.")
		)


def submit_for_review(supplier_profile: str) -> None:
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.approval_status not in ("Draft", "Returned"):
		frappe.throw(_("Invalid state for submit."))
	assert_ready_for_submission(supplier_profile)
	before = prof.approval_status
	_save(
		supplier_profile,
		{
			"approval_status": "Submitted",
			"submitted_by": frappe.session.user,
			"submitted_at": now_datetime(),
		},
	)
	history.log_status_change(
		supplier_profile, "Approval", "Submitted", before, None
	)
	compliance.recompute_and_save_profile(supplier_profile)
	eligibility.bust_eligibility_cache(supplier_profile)


def start_review(supplier_profile: str) -> None:
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.approval_status != "Submitted":
		frappe.throw(_("Only Submitted can move to Under Review."))
	before = prof.approval_status
	_save(supplier_profile, {"approval_status": "Under Review"})
	history.log_status_change(
		supplier_profile, "Approval", "Under Review", before, None
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def approve_supplier(supplier_profile: str) -> None:
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.approval_status != "Under Review":
		frappe.throw(_("Only Under Review can be approved."))
	sod.assert_not_same_user_submit_and_approve(prof.submitted_by)
	before_a = prof.approval_status
	before_o = prof.operational_status
	_save(
		supplier_profile,
		{
			"approval_status": "Approved",
			"operational_status": "Active",
			"approved_by": frappe.session.user,
			"approved_at": now_datetime(),
		},
	)
	history.log_status_change(
		supplier_profile, "Approval", "Approved", before_a, None
	)
	history.log_status_change(
		supplier_profile, "Operational", "Active", before_o, None
	)
	compliance.recompute_and_save_profile(supplier_profile)
	eligibility.bust_eligibility_cache(supplier_profile)


def return_supplier(supplier_profile: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Return reason is required."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.approval_status not in ("Under Review", "Submitted"):
		frappe.throw(_("Invalid return state."))
	before = prof.approval_status
	_save(supplier_profile, {"approval_status": "Returned", "return_reason": reason})
	history.log_status_change(
		supplier_profile, "Approval", "Returned", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def reject_supplier(supplier_profile: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Rejection reason is required."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.approval_status != "Under Review":
		frappe.throw(_("Only Under Review can be rejected."))
	before = prof.approval_status
	_save(supplier_profile, {"approval_status": "Rejected", "rejection_reason": reason})
	history.log_status_change(
		supplier_profile, "Approval", "Rejected", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def suspend_supplier(supplier_profile: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Suspension reason is required."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	before = prof.operational_status
	_save(supplier_profile, {"operational_status": "Suspended"})
	history.log_status_change(
		supplier_profile, "Operational", "Suspended", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def reinstate_supplier(supplier_profile: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Reinstatement reason is required."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.operational_status != "Suspended":
		frappe.throw(_("Not suspended."))
	before = prof.operational_status
	_save(supplier_profile, {"operational_status": "Active"})
	history.log_status_change(
		supplier_profile, "Operational", "Active", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def blacklist_supplier(supplier_profile: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Blacklist reason is required."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	before = prof.operational_status
	_save(supplier_profile, {"operational_status": "Blacklisted"})
	history.log_status_change(
		supplier_profile, "Operational", "Blacklisted", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def verify_document(document_name: str) -> None:
	doc = frappe.get_doc("KTSM Supplier Document", document_name)
	sod.assert_not_same_user_upload_and_verify(document_name, "verify")
	before = doc.verification_status
	doc.db_set("verification_status", "Verified", update_modified=False)
	doc.db_set("verified_by", frappe.session.user, update_modified=False)
	doc.db_set("verified_at", now_datetime(), update_modified=False)
	doc.db_set("rejection_reason", None, update_modified=False)
	prof = doc.supplier_profile
	history.log_status_change(
		prof, "Compliance", f"doc_verified:{doc.name}", before, None
	)
	compliance.recompute_and_save_profile(prof)
	eligibility.bust_eligibility_cache(prof)


def reject_document(document_name: str, reason: str) -> None:
	if not (reason or "").strip():
		frappe.throw(_("Rejection reason is required."))
	sod.assert_not_same_user_upload_and_verify(document_name, "reject")
	doc = frappe.get_doc("KTSM Supplier Document", document_name)
	before = doc.verification_status
	doc.db_set("verification_status", "Rejected", update_modified=False)
	doc.db_set("rejection_reason", reason, update_modified=False)
	doc.db_set("verified_by", None, update_modified=False)
	doc.db_set("verified_at", None, update_modified=False)
	prof = doc.supplier_profile
	history.log_status_change(
		prof, "Compliance", f"doc_rejected:{doc.name}", before, reason
	)
	compliance.recompute_and_save_profile(prof)
	eligibility.bust_eligibility_cache(prof)


def set_operational_expired(supplier_profile: str, reason: str) -> None:
	"""C2: move operational status to Expired (e.g. cert lapse)."""
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to mark a supplier as expired."))
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	if prof.operational_status in ("Blacklisted", "Expired"):
		return
	before = prof.operational_status
	_save(supplier_profile, {"operational_status": "Expired"})
	history.log_status_change(
		supplier_profile, "Operational", "Expired", before, reason
	)
	eligibility.bust_eligibility_cache(supplier_profile)


def qualify_supplier_category(
	assignment_name: str, qualified_until=None
) -> None:
	"""C3 / F2: set category row to Qualified."""
	row = frappe.get_doc("KTSM Category Assignment", assignment_name)
	if row.qualification_status != "Under Review":
		frappe.throw(
			_("Category must be Under Review before it can be qualified (current: {0}).").format(
				row.qualification_status
			)
		)
	before = row.qualification_status
	row.db_set("qualification_status", "Qualified", update_modified=False)
	if qualified_until:
		row.db_set("qualified_until", qualified_until, update_modified=False)
	row.db_set("reviewed_by", frappe.session.user, update_modified=False)
	row.db_set("reviewed_at", now_datetime(), update_modified=False)
	history.log_status_change(
		row.supplier_profile,
		"Compliance",
		f"qual_qualified:{assignment_name}",
		before,
		None,
	)
	eligibility.bust_eligibility_cache(row.supplier_profile)


def reject_supplier_category(assignment_name: str, reason: str) -> None:
	"""C3 / F2: Rejected category qualification."""
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to reject a category request."))
	row = frappe.get_doc("KTSM Category Assignment", assignment_name)
	if row.qualification_status != "Under Review":
		frappe.throw(
			_("Category must be Under Review before it can be rejected (current: {0}).").format(
				row.qualification_status
			)
		)
	before = row.qualification_status
	row.db_set("qualification_status", "Rejected", update_modified=False)
	row.db_set("review_notes", reason, update_modified=False)
	row.db_set("reviewed_by", frappe.session.user, update_modified=False)
	row.db_set("reviewed_at", now_datetime(), update_modified=False)
	history.log_status_change(
		row.supplier_profile,
		"Compliance",
		f"qual_rejected:{assignment_name}",
		before,
		reason,
	)
	eligibility.bust_eligibility_cache(row.supplier_profile)


def start_category_review(assignment_name: str) -> None:
	"""C3: Requested → Under Review (registry/compliance)."""
	row = frappe.get_doc("KTSM Category Assignment", assignment_name)
	if row.qualification_status != "Requested":
		frappe.throw(_("This category request is not awaiting review."))
	before = row.qualification_status
	row.db_set("qualification_status", "Under Review", update_modified=False)
	history.log_status_change(
		row.supplier_profile,
		"Compliance",
		f"qual_in_review:{assignment_name}",
		before,
		None,
	)
	eligibility.bust_eligibility_cache(row.supplier_profile)
