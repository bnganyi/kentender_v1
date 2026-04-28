# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

# External-oriented APIs (E1–E3) — return business codes, no internal profile names in responses.

import time

import frappe
from frappe import _
from frappe.exceptions import PermissionError
from frappe.utils import now_datetime
from frappe.utils.file_manager import save_file

from kentender_suppliers.services import compliance, eligibility, governance


def _require_login() -> None:
	"""E3: whitelisted non-guest API entry points."""
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(_("Log in to use this method."), exc=PermissionError)


@frappe.whitelist(allow_guest=True)
def ktsm_register(
	supplier_name: str,
	primary_email: str,
	primary_contact_name: str = "",
	supplier_type: str = "Company",
) -> dict:
	"""E1: public registration; Supplier + Profile + (optional) Website user + API access; smoke §SCENARIO 1."""
	uname = _ensure_website_user_for_registration(
		primary_email, (primary_contact_name or supplier_name or "Supplier")
	)
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
			"external_user": uname,
		}
	)
	prof.insert(ignore_permissions=True)
	_ensure_api_access_for_profile(prof.name, uname)
	compliance.recompute_and_save_profile(prof.name)
	comp = frappe.db.get_value("KTSM Supplier Profile", prof.name, "compliance_status")
	return {
		"ok": True,
		"supplier_code": code,
		"approval_status": "Draft",
		"operational_status": "Pending",
		"compliance_status": comp or "Unknown",
		"api_access": "created" if uname else "skipped",
		"next_steps": [
			"Complete profile and required documents in desk",
			"Submit for review when ready",
		],
		"message": "Registration created. Complete onboarding via supplier portal (when available) or ask a registry officer.",
	}


def _ensure_website_user_for_registration(email: str, display_first_name: str) -> str | None:
	email = (email or "").strip()
	if not email or "@" not in email:
		return None
	# Frappe `User` name is typically the email for login.
	if not frappe.db.exists("User", email):
		usr = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": (display_first_name or "Supplier")[:140],
				"send_welcome_email": 0,
				"user_type": "Website User",
			}
		)
		if frappe.db.exists("Role", "KenTender External Supplier"):
			usr.append("roles", {"role": "KenTender External Supplier"})
		usr.insert(ignore_permissions=True, ignore_links=True)
	return email


def _ensure_api_access_for_profile(
	supplier_profile: str, external_user: str | None
) -> None:
	if not external_user:
		return
	if frappe.db.exists(
		"KTSM Supplier API Access", {"supplier_profile": supplier_profile}
	):
		return
	frappe.get_doc(
		{
			"doctype": "KTSM Supplier API Access",
			"supplier_profile": supplier_profile,
			"external_user": external_user,
			"access_status": "Pending",
		}
	).insert(ignore_permissions=True)


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


def _assert_may_access_supplier(supplier_code: str) -> "frappe.model.document.Document":
	"""E3: only own supplier (or privileged desk user). Returns profile doc."""
	if not (supplier_code or "").strip():
		frappe.throw(_("Supplier code is required."))
	pname = eligibility.get_profile_name_for_supplier_code(supplier_code)
	if not pname:
		frappe.throw(_("Unknown supplier code."))
	prof = frappe.get_doc("KTSM Supplier Profile", pname)
	roles = set(frappe.get_roles())
	if "System Manager" in roles or "Administrator" in roles:
		return prof
	if prof.get("external_user") and prof.external_user == frappe.session.user:
		return prof
	if frappe.has_permission("KTSM Supplier Profile", "write", prof, throw=False):
		return prof
	frappe.throw(_("You are not allowed to act for this supplier."))


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
	prof = _assert_may_access_supplier(supplier_code)
	if prof.approval_status not in ("Draft", "Returned"):
		frappe.throw(_("Profile can only be edited in Draft or Returned from this API."))
	if risk_level is not None and risk_level not in ("Low", "Medium", "High"):
		frappe.throw(_("Invalid risk level."))
	if risk_level is not None:
		d = frappe.get_doc("KTSM Supplier Profile", prof.name)
		d.flags.bypass_governance = True
		d.risk_level = risk_level
		d.save(ignore_permissions=True)
	return ktsm_get_status(supplier_code)


@frappe.whitelist()
def ktsm_get_status(supplier_code: str) -> dict:
	"""E2: operational + approval + compliance snapshot (no internal ids)."""
	_require_login()
	_assert_may_access_supplier(supplier_code)
	return eligibility.check_supplier_eligibility(supplier_code, None)


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
	prof = _assert_may_access_supplier(supplier_code)
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
	d.insert(ignore_permissions=True)
	saved = save_file(fname, content, "KTSM Supplier Document", d.name, is_private=0)
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
	prof = _assert_may_access_supplier(supplier_code)
	governance.submit_for_review(prof.name)
	return {
		"ok": True,
		"supplier_code": supplier_code,
		"approval_status": "Submitted",
	}
