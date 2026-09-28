# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Browser worlds for the supplier Account portal (BDS-CHG-001 v0.8 §10.4–10.5,
plan Phase 11 slices 11.3–11.4). This world's own people, namespaced and on
the test password, so the canonical personas are never touched:

- Mary Wanjiku (Test), the organisation's Authorised Signatory;
- David Ouma (Test), its Supplier Representative;
- Peter Mwangi (Test), a signed-in person of another organisation;
- Amina Yusuf (Test), the Supplier Account support officer who suspends.

`reset_account_fixture(state=…)` builds one board state — "new" (Mary has no
Account yet: BDS-DES-03), "verify", "active", "attention" or "suspended"
(BDS-DES-04 variants) — through the real commands, on the 18 May 2027
timeline, and puts the live pages on the world's instant. `restore_site`
removes everything this world made, including records a browser run created
(those carry no namespace, so they are found by this world's people)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import test_clock
from kentender_suppliers.supplier_accounts.seeds import canonical

NAMESPACE = "PW_SUPPLIER_ACCOUNTS"
PASSWORD = "Test@123"
MARY = "pw.acc.mary@afya-acc-pw.example"
DAVID = "pw.acc.david@afya-acc-pw.example"
PETER = "pw.acc.peter@kisiwa-acc-pw.example"
AMINA = "pw.acc.amina@kentender-acc-pw.example"
PORTAL_USERS = {MARY: "Mary Wanjiku", DAVID: "David Ouma", PETER: "Peter Mwangi"}
USERS = (*PORTAL_USERS, AMINA)
FACTS = {
	"legal_name": "Afya Digital Supplies (Account Test) Limited", "country": "Kenya", "registration_number": "PVT-PW-ACC001", "tax_identifier": "P009000201X",
	"registered_address": "Westlands Business Park, Waiyaki Way, Nairobi", "official_email": "tenders@afya-acc-pw.example", "official_phone": "+254 709 555 201",
	"job_title": "Managing Director",
}
CLOCK = {"register": "2027-05-18 09:00:00", "verify": "2027-05-18 09:10:00", "representative": "2027-05-18 09:20:00", "evidence": "2027-05-18 09:30:00", "suspend": "2027-05-19 08:00:00"}
ACCOUNT_AT = "2027-05-19 10:00:00"
EVIDENCE = (
	{"evidence_type": "Certificate of incorporation", "reference": "PVT-PW-ACC001", "valid_until": "", "title": "Certificate of incorporation"},
	{"evidence_type": "Tax compliance certificate", "reference": "P009000201X", "valid_until": "2027-12-31", "title": "Tax compliance certificate"},
	{"evidence_type": "Reservation evidence", "reference": "AGPO-Y-2026-04172", "valid_until": "2027-06-30", "title": "Youth reservation evidence"},
)
STATES = ("new", "verify", "active", "attention", "suspended")
ACCOUNT_DOCTYPES = ("Supplier Account Access Decision", "Supplier User Assignment", "Supplier Account Verification", "Supplier Account Evidence", "Supplier Organisation")


def _users() -> None:
	from frappe.utils.password import update_password

	from kentender_core.services import responsibility_administration as administration
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
	for email, name in PORTAL_USERS.items():
		canonical._user(email, name)
		update_password(email, PASSWORD)
	if not frappe.db.exists("User", AMINA):
		doc = frappe.get_doc({"doctype": "User", "email": AMINA, "first_name": "Amina", "last_name": "Yusuf", "send_welcome_email": 0, "user_type": "System User"})
		doc.insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	if not frappe.db.exists("User Responsibility Assignment", {"user": AMINA, "business_role": "Supplier Account Support Officer", "status": "Enabled"}):
		administration.grant(user=AMINA, business_role="Supplier Account Support Officer", fixture_namespace=NAMESPACE, actor="Administrator")


def _claim_browser_records() -> None:
	"""Stamp this world's namespace on Account rows its people made through
	the browser (no namespace there), so the namespaced removal takes them."""
	orgs = set(frappe.get_all("Supplier Organisation", filters={"registered_by": ("in", list(PORTAL_USERS))}, pluck="name"))
	orgs |= set(frappe.get_all("Supplier User Assignment", filters={"user": ("in", list(PORTAL_USERS))}, pluck="organisation"))
	if not orgs:
		return
	for doctype in ACCOUNT_DOCTYPES:
		field = "name" if doctype == "Supplier Organisation" else "organisation"
		for name in frappe.get_all(doctype, filters={field: ("in", list(orgs))}, pluck="name"):
			frappe.db.set_value(doctype, name, "fixture_namespace", NAMESPACE, update_modified=False)
	frappe.db.set_value("Supplier Account Command Journal", {"organisation": ("in", list(orgs))}, "fixture_namespace", NAMESPACE, update_modified=False)
	frappe.db.set_value("Supplier Account Command Journal", {"actor": ("in", list(PORTAL_USERS))}, "fixture_namespace", NAMESPACE, update_modified=False)


def _wipe_accounts() -> None:
	_claim_browser_records()
	canonical.remove_supplier_accounts(namespace=NAMESPACE)


def _pinned(instant: str):
	frappe.flags.kt_accounts_clock = instant


def _register_only() -> str:
	from kentender_suppliers.supplier_accounts.services import registration

	sent: list[dict] = []
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_accounts_clock", "kt_account_message_transport", "kt_accounts_fixture_namespace")}
	frappe.flags.kt_account_message_transport = lambda message: sent.append(message) or {"result": "Delivered"}
	frappe.flags.kt_accounts_fixture_namespace = NAMESPACE
	try:
		_pinned(CLOCK["register"])
		result = registration.register_supplier_organisation(**FACTS, authority_filename=canonical.AUTHORITY_FILE, authority_content=canonical._pdf(), idempotency_key=f"{NAMESPACE.lower()}-register", user=MARY)
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	if not result.get("ok"):
		frappe.throw(f"The test account could not be registered: {result}")
	return result["organisation"]


def _active() -> str:
	from kentender_suppliers.supplier_accounts.services import evidence

	organisation = canonical.ensure_supplier_account(
		facts=FACTS, registrant=MARY, registrant_name=PORTAL_USERS[MARY], representative=DAVID, representative_name=PORTAL_USERS[DAVID], representative_title="Bid Coordinator",
		clock=CLOCK, namespace=NAMESPACE, key_prefix=NAMESPACE.lower(),
	)["organisation"]
	saved = {flag: frappe.flags.get(flag) for flag in ("kt_accounts_clock", "kt_accounts_fixture_namespace")}
	frappe.flags.kt_accounts_fixture_namespace = NAMESPACE
	try:
		_pinned(CLOCK["evidence"])
		for index, item in enumerate(EVIDENCE):
			result = evidence.upload_account_evidence(organisation=organisation, filename=f"{item['reference'].lower()}.pdf", content=canonical._pdf(), idempotency_key=f"{NAMESPACE.lower()}-evidence-{index}", user=MARY, **item)
			if not result.get("ok"):
				frappe.throw(f"Test evidence could not be added: {result}")
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value
	return organisation


def _suspend(organisation: str) -> None:
	from kentender_suppliers.supplier_accounts.services import access

	saved = {flag: frappe.flags.get(flag) for flag in ("kt_accounts_clock", "kt_accounts_fixture_namespace")}
	frappe.flags.kt_accounts_fixture_namespace = NAMESPACE
	try:
		_pinned(CLOCK["suspend"])
		version = frappe.db.get_value("Supplier Organisation", organisation, "record_version")
		access.suspend_supplier_account(organisation=organisation, reason="Reported misuse of the account (test world).", expected_version=version, idempotency_key=f"{NAMESPACE.lower()}-suspend", user=AMINA)
	finally:
		for flag, value in saved.items():
			frappe.flags[flag] = value


def reset_account_fixture(*, state: str = "active", commit: bool = True) -> dict[str, Any]:
	if state not in STATES:
		raise ValueError(f"unknown account world {state!r}; one of {STATES}")
	frappe.set_user("Administrator")
	_wipe_accounts()
	_users()
	organisation = ""
	if state == "verify":
		organisation = _register_only()
	elif state in ("active", "attention", "suspended"):
		organisation = _active()
		if state == "attention":
			# the isolated legacy-record fixture: an Account created before the phone was required
			frappe.db.set_value("Supplier Organisation", organisation, "official_phone", "", update_modified=False)
		elif state == "suspended":
			_suspend(organisation)
	if not test_clock.set_instant(ACCOUNT_AT):
		frappe.throw("The Account browser worlds need a test environment (site_config kt_bds_simulation_environment = 1).")
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {
		"state": state, "organisation": organisation, "password": PASSWORD, "signatory": MARY, "representative": DAVID, "other_person": PETER,
		"official_email": FACTS["official_email"], "legal_name": FACTS["legal_name"], "facts": FACTS,
	}


def suspend_organisation(*, registration_number: str, commit: bool = True) -> dict[str, Any]:
	"""Suspend another browser world's organisation (the Bid Submission worlds'
	Afya (Test), PVT-PW-AFYA01) through the real suspension command, by this
	world's support officer; `restore_site` removes the officer's records."""
	frappe.set_user("Administrator")
	_users()
	organisation = frappe.db.get_value("Supplier Organisation", {"registration_number": registration_number}, "name")
	if not organisation:
		frappe.throw(f"No supplier organisation with registration number {registration_number}.")
	_suspend(organisation)
	if commit:
		frappe.db.commit()
	return {"organisation": organisation, "account_status": frappe.db.get_value("Supplier Organisation", organisation, "account_status")}


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	frappe.set_user("Administrator")
	_wipe_accounts()
	for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NAMESPACE}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", name, force=True, ignore_permissions=True)
	removed = canonical.remove_supplier_accounts(namespace=NAMESPACE, users=USERS)
	test_clock.set_instant(None)
	if commit:
		frappe.db.commit()
	return {"ok": True, "removed": removed}
