# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical supplier account (BDS-CHG-001 v0.8 §10.1 "Supplier
organisation and users" and §13.3), built through the real Supplier Account
commands at the spec's own instants:

- 18 May 2027 09:00 — Mary Wanjiku registers Afya Digital Supplies Limited
  (Pending verification; the verification message is captured, since this
  bench sends no email);
- 09:10 — Mary verifies the official email; the Account becomes Active;
- 09:20 — Mary assigns David Ouma as Supplier Representative.

Idempotent: an Active Afya account with David's assignment is returned
untouched. Bid Submission's canonical seed calls this through the
`kt_canonical_supplier_accounts` hook before David starts the canonical bid
(TPR FU-25), so the Tenders stage never needs the retired stand-in."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import frappe

NAMESPACE = "KENTENDER_MVP_1_R1_BDS"
MARY = "mary.wanjiku@afyadigital.example"
DAVID = "david.ouma@afyadigital.example"
AFYA = {
	"legal_name": "Afya Digital Supplies Limited", "country": "Kenya", "registration_number": "PVT-9X7K2M", "tax_identifier": "P051234567X",
	"registered_address": "Westlands Business Park, Waiyaki Way, Nairobi", "official_email": "tenders@afyadigital.example", "official_phone": "+254 709 555 014",
	"job_title": "Managing Director",
}
AUTHORITY_FILE = "mary-wanjiku-signing-authority.pdf"
CLOCK = {"register": "2027-05-18 09:00:00", "verify": "2027-05-18 09:10:00", "representative": "2027-05-18 09:20:00"}


def _pdf() -> bytes:
	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=595, height=842)
	buffer = BytesIO()
	writer.write(buffer)
	return buffer.getvalue()


def _user(email: str, full_name: str) -> None:
	if not frappe.db.exists("User", email):
		first, _, last = full_name.partition(" ")
		frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "user_type": "Website User", "send_welcome_email": 0}).insert(ignore_permissions=True)


def _organisation(country: str, registration_number: str) -> str:
	return frappe.db.get_value("Supplier Organisation", {"country": country, "registration_number": registration_number}, "name") or ""


def afya() -> str:
	return _organisation(AFYA["country"], AFYA["registration_number"])


def _has_representative(organisation: str, representative: str = DAVID) -> bool:
	return bool(frappe.db.exists("Supplier User Assignment", {"organisation": organisation, "user": representative, "responsibility": "Supplier Representative"}))


def ensure_supplier_account(
	*, facts: dict[str, str], registrant: str, registrant_name: str, representative: str, representative_name: str, representative_title: str = "",
	clock: dict[str, str] | None = None, namespace: str = NAMESPACE, key_prefix: str = "seed",
) -> dict[str, Any]:
	"""One Active supplier account with a Supplier Representative, built through
	the real commands (register, verify the official email, assign the
	representative). Idempotent by country and registration number."""
	from kentender_suppliers.supplier_accounts.services import assignments, registration, verification

	clock = clock or CLOCK
	from kentender_core.services import file_integrity

	if not file_integrity.scanner_result(_pdf(), AUTHORITY_FILE).lower().startswith("clean"):
		# The registrant's authority evidence must be accepted before they can
		# assign anyone; refuse before creating anything half-built.
		frappe.throw(
			"No file scanner accepts files on this site, so a seeded signatory's authority evidence cannot be accepted. "
			"On a test site set site_config kt_bds_simulation_environment to 1 (the Test Scanner)."
		)
	existing = _organisation(facts["country"], facts["registration_number"])
	if existing and frappe.db.get_value("Supplier Organisation", existing, "account_status") == "Active" and _has_representative(existing, representative):
		return {"ok": True, "created": False, "organisation": existing}
	sent: list[dict[str, Any]] = []
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_accounts_clock", "kt_account_message_transport", "kt_accounts_fixture_namespace")}
	frappe.flags.kt_account_message_transport = lambda message: sent.append(message) or {"result": "Delivered"}
	frappe.flags.kt_accounts_fixture_namespace = namespace
	try:
		_user(registrant, registrant_name)
		frappe.flags.kt_accounts_clock = clock["register"]
		registered = registration.register_supplier_organisation(**facts, authority_filename=AUTHORITY_FILE, authority_content=_pdf(), idempotency_key=f"{key_prefix}-register-{facts['registration_number']}", user=registrant)
		organisation = registered.get("organisation") or _organisation(facts["country"], facts["registration_number"])
		if not organisation:
			frappe.throw(f"The supplier account could not be registered: {registered}")
		frappe.flags.kt_accounts_clock = clock["verify"]
		if frappe.db.get_value("Supplier Organisation", organisation, "account_status") != "Active":
			if not sent:
				verification.send_account_verification(organisation=organisation, idempotency_key=f"{key_prefix}-verify-{facts['registration_number']}", user=registrant)
			verified = verification.verify_account_communication(token=sent[-1]["link"].split("token=", 1)[1], user=registrant)
			if not verified.get("ok"):
				frappe.throw(f"The supplier account could not be verified: {verified}")
		frappe.flags.kt_accounts_clock = clock["representative"]
		if not _has_representative(organisation, representative):
			assigned = assignments.assign_supplier_representative(
				organisation=organisation, email=representative, full_name=representative_name, job_title=representative_title,
				idempotency_key=f"{key_prefix}-representative-{facts['registration_number']}", user=registrant,
			)
			if not assigned.get("ok"):
				frappe.throw(f"{representative_name} could not be assigned: {assigned}")
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	return {"ok": True, "created": True, "organisation": organisation}


def ensure_canonical_supplier_accounts(*, commit: bool = False) -> dict[str, Any]:
	result = ensure_supplier_account(
		facts=AFYA, registrant=MARY, registrant_name="Mary Wanjiku", representative=DAVID, representative_name="David Ouma", representative_title="Bid Coordinator",
	)
	if frappe.conf.get("developer_mode") or frappe.flags.get("kt_fixture_passwords"):
		# The same rule as the KT-STD-001 §8.3 register's actors (site stage):
		# the canonical supplier people log in with the shared fixture password
		# on a development site or wherever the canonical seed may run
		# (Project Owner, 30 Sep 2026: "Maintain the same universal password").
		from frappe.utils.password import update_password

		from kentender_core.seeds.constants import TEST_PASSWORD

		for email in (MARY, DAVID):
			update_password(email, TEST_PASSWORD)
	if commit:
		frappe.db.commit()
	return result


ACCOUNT_DOCTYPES = ("Supplier Account Access Decision", "Supplier User Assignment", "Supplier Account Verification", "Supplier Account Evidence", "Supplier Organisation")


def remove_supplier_accounts(*, namespace: str, users: tuple[str, ...] = ()) -> dict[str, int]:
	"""Remove every Account record a seed stamped `namespace` (never the
	canonical namespace by accident: an empty namespace removes nothing),
	their command-journal entries and the named portal `users`."""
	deleted: dict[str, int] = {}
	if not namespace:
		return deleted
	names: list[str] = []
	for doctype in ACCOUNT_DOCTYPES:
		for name in frappe.get_all(doctype, filters={"fixture_namespace": namespace}, pluck="name"):
			if doctype == "Supplier Account Evidence":
				for file_name in frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name}, pluck="name"):
					frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
			names.append(name)
			deleted[doctype] = deleted.get(doctype, 0) + 1
	frappe.db.delete("Supplier Account Command Journal", {"fixture_namespace": namespace})
	if names:
		frappe.db.delete("Audit Event", {"document_name": ("in", names)})
	for email in users:
		if frappe.db.exists("User", email):
			frappe.db.delete("Audit Event", {"performed_by": email})
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
			deleted["User"] = deleted.get("User", 0) + 1
	return deleted


def validate() -> list[str]:
	"""Human-readable failures; empty when the canonical account is as §10.1."""
	problems: list[str] = []
	organisation = afya()
	if not organisation:
		return ["Afya Digital Supplies Limited has no supplier account"]
	row = frappe.db.get_value("Supplier Organisation", organisation, ["legal_name", "account_status", "official_email"], as_dict=True)
	if row.account_status != "Active":
		problems.append(f"Afya's account is {row.account_status}, not Active")
	if row.official_email != AFYA["official_email"]:
		problems.append(f"Afya's official email is {row.official_email}")
	if not _has_representative(organisation):
		problems.append("David Ouma is not Afya's Supplier Representative")
	return problems
