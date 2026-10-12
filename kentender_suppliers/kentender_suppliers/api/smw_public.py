# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

# External-oriented APIs (E1–E3) — return business codes, no internal profile names in responses.

import time

import frappe
from frappe import _
from frappe.exceptions import PermissionError
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file

from kentender_core.services.command_write_guard import command_write
from kentender_suppliers.services import compliance, eligibility, governance, registry_access
from kentender_suppliers.services.registry_access import WRITE_FAMILY


def _require_login() -> None:
	"""E3: whitelisted non-guest API entry points."""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Log in to use this method."), exc=PermissionError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def ktsm_register(
	supplier_name: str,
	primary_email: str,
	primary_contact_name: str = "",
	supplier_type: str = "Company",
) -> dict:
	"""E1: public registration: a Supplier and a Draft profile, nothing else.

	AUD-XC-020 / RG-12 (owner default Q5, 6 Oct 2026): this is a public, unauthenticated write with
	no verified e-mail. No login is created here: a disabled User made for an unverified address
	could never be enabled and blocked the real owner of that address from signing up, so the User
	(and its API access) is created only after the address is verified, by a step that does not
	exist yet. The Supplier and profile still need `ignore_permissions` because a Guest holds no
	DocPerm on them; the guard is the content (a Draft with no login), the throttle above (5 per
	hour per address), POST only, and the profile guard that keeps governance fields command-only.
	Whether guest registration should exist at all is an open owner question; the supported
	onboarding route is `supplier_accounts.register_supplier_organisation`.
	"""
	sg = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	if not sg:
		sg = frappe.db.get_value("Supplier Group", {}, "name")
	code = _next_supplier_code()
	# Use code in display name to avoid unique collision on `tabSupplier.name` when supplier_name is reused
	display = (supplier_name or "Supplier").strip() + f" [{code}]"
	erp = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": display,
			"supplier_type": supplier_type,
			"supplier_group": sg,
			"kentender_supplier_code": code,
		}
	)
	erp.insert(ignore_permissions=True)
	prof = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Profile",
			"erpnext_supplier": erp.name,
			"identity_display": display,
		}
	)
	prof.insert(ignore_permissions=True)
	compliance.recompute_and_save_profile(prof.name)
	comp = frappe.db.get_value("KTSM Supplier Profile", prof.name, "compliance_status")
	return {
		"ok": True,
		"supplier_code": code,
		"approval_status": "Draft",
		"operational_status": "Pending",
		"compliance_status": comp or "Unknown",
		"api_access": "skipped",
		"next_steps": [
			"Verify the contact e-mail address (a login is created only after verification)",
			"A registry officer completes the profile and the required documents",
		],
		"message": "Registration created. No login exists yet: it is created after the e-mail address is verified.",
	}


def _next_supplier_code() -> str:
	yr = str(now_datetime().year)
	prefix = f"SUP-KE-{yr}-"
	rows = frappe.get_all(
		"Supplier",
		filters={"kentender_supplier_code": ("like", f"{prefix}%")},
		pluck="kentender_supplier_code",
	)
	mx = 0
	for r in rows or []:
		if not r:
			continue
		parts = (r or "").rsplit("-", 1)
		if len(parts) == 2 and parts[-1].isdigit():
			mx = max(mx, int(parts[-1]))
	return f"SUP-KE-{yr}-" + str(mx + 1).zfill(4)


def _profile_for_session_user():
	rows = frappe.get_all(
		"KTSM Supplier Profile",
		filters={"external_user": frappe.session.user},
		limit=1,
		pluck="name",
	)
	if not rows:
		return None
	return frappe.get_doc("KTSM Supplier Profile", rows[0])


def _assert_may_access_supplier(supplier_code: str, *, write: bool = False) -> "frappe.model.document.Document":
	"""E3: the supplier's own account, or a registry user with the matching capability. Returns profile doc.

	System Manager and Administrator get nothing from their technical role (RG-30): reads need the
	registry read capability (which does include them, as readers), writes need the registry's
	`prepare_registration` capability."""
	if not (supplier_code or "").strip():
		frappe.throw(_("Supplier code is required."))
	pname = eligibility.get_profile_name_for_supplier_code(supplier_code)
	if not pname:
		frappe.throw(_("Unknown supplier code."))
	prof = frappe.get_doc("KTSM Supplier Profile", pname)
	if prof.get("external_user") and prof.external_user == frappe.session.user:
		return prof
	if registry_access.has_capability("prepare_registration" if write else "read_registry"):
		return prof
	frappe.throw(_("You are not allowed to act for this supplier."), exc=PermissionError)


@frappe.whitelist()
def ktsm_get_me() -> dict:
	"""E1/E3: current session user’s supplier (by external_user link), codes only when known."""
	_require_login()
	prof = _profile_for_session_user()
	if not prof:
		return {"ok": True, "supplier_code": None, "message": "No supplier profile linked to this user."}
	code = frappe.db.get_value("Supplier", prof.erpnext_supplier, "kentender_supplier_code")
	return {
		"ok": True,
		"supplier_code": code,
		"approval_status": prof.approval_status,
		"operational_status": prof.operational_status,
		"compliance_status": prof.compliance_status,
	}


@frappe.whitelist()
def ktsm_get_profile(supplier_code: str) -> dict:
	"""E1: read-only view of supplier state (no internal document names)."""
	return ktsm_get_status(supplier_code)


@frappe.whitelist()
def ktsm_update_profile(
	supplier_code: str,
	risk_level: str | None = None,
) -> dict:
	"""E1: limited Draft/Returned edits (e.g. risk) — not governance fields."""
	_require_login()
	prof = _assert_may_access_supplier(supplier_code, write=True)
	if prof.approval_status not in ("Draft", "Returned"):
		frappe.throw(_("Profile can only be edited in Draft or Returned from this API."))
	if risk_level is not None and risk_level not in ("Low", "Medium", "High"):
		frappe.throw(_("Invalid risk level."))
	if risk_level is not None:
		d = frappe.get_doc("KTSM Supplier Profile", prof.name)
		d.risk_level = risk_level
		d.save(ignore_permissions=True)
	return ktsm_get_status(supplier_code)


@frappe.whitelist()
def ktsm_get_status(supplier_code: str) -> dict:
	"""E2: operational + approval + compliance snapshot (no internal ids)."""
	_require_login()
	_assert_may_access_supplier(supplier_code)
	return eligibility.compute_eligibility(supplier_code, None)


@frappe.whitelist()
def ktsm_list_documents(supplier_code: str) -> dict:
	"""E2: list current documents for supplier (type code + name + verification)."""
	_require_login()
	prof = _assert_may_access_supplier(supplier_code)
	rows = frappe.get_all(
		"KTSM Supplier Document",
		filters={"supplier_profile": prof.name, "is_current": 1},
		fields=["document_name", "document_type", "verification_status", "expiry_date", "is_current"],
	)
	out = []
	for r in rows or []:
		dcode = frappe.db.get_value("KTSM Document Type", r.document_type, "document_type_code")
		out.append(
			{
				"document_type_code": dcode,
				"document_name": r.document_name,
				"verification_status": r.verification_status,
				"expiry_date": r.expiry_date,
			}
		)
	return {"ok": True, "supplier_code": supplier_code, "documents": out}


@frappe.whitelist()
def ktsm_upload_document(
	supplier_code: str,
	document_type_code: str,
	document_name: str = "",
) -> dict:
	"""E2: multipart `file` field; tags external_uploaded=1 for SOD."""
	_require_login()
	prof = _assert_may_access_supplier(supplier_code, write=True)
	dt_name = frappe.db.get_value(
		"KTSM Document Type",
		{"document_type_code": document_type_code, "is_active": 1},
		"name",
	)
	if not dt_name:
		frappe.throw(_("Document type is invalid or inactive."))
	req = getattr(frappe.local, "request", None)
	if not req or "file" not in req.files:
		frappe.throw(_("No file uploaded (form field `file`)."))
	f = req.files["file"]
	content = f.stream.read()
	if not content:
		frappe.throw(_("Empty file."))
	fname = f.filename or f"doc-upload-{int(time.time() * 1000)}"
	dn = (document_name or "").strip() or fname
	d = frappe.get_doc(
		{
			"doctype": "KTSM Supplier Document",
			"supplier_profile": prof.name,
			"document_type": dt_name,
			"document_name": dn,
			"verification_status": "Pending",
			"is_current": 1,
			"external_uploaded": 1,
		}
	)
	d.flags.ignore_validate = False
	with command_write(WRITE_FAMILY):  # `external_uploaded` is the upload endpoint's to set (RG-13)
		d.insert(ignore_permissions=True)
	# Registration documents are private (KT-ACCESS-REV-001 AR-15): read through the document's own permission, never by URL.
	saved = save_file(fname, content, "KTSM Supplier Document", d.name, is_private=1)
	d.db_set("file", saved.file_url, update_modified=False)
	return {
		"ok": True,
		"supplier_code": supplier_code,
		"document_type_code": document_type_code,
		"document_name": dn,
	}


@frappe.whitelist()
def ktsm_supplier_submit(supplier_code: str) -> dict:
	"""E2: submit profile for review (governance + compliance checks)."""
	_require_login()
	prof = _assert_may_access_supplier(supplier_code, write=True)
	governance.submit_for_review(prof.name)
	return {
		"ok": True,
		"supplier_code": supplier_code,
		"approval_status": "Submitted",
	}
