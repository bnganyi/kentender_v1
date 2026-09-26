# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared world for the Supplier Accounts tests. This bench has no per-test
rollback, so every record carries the test namespace and `purge()` removes
exactly what the tests made: Account rows and their files, the command
journal, audit events, responsibility grants and the test users."""

from __future__ import annotations

import uuid
from unittest import mock

import frappe
from frappe.tests import IntegrationTestCase

NS = "BDS_ACC_TEST"
DOMAIN = "acc-test.example"
MARY = f"mary.wanjiku@{DOMAIN}"
DAVID = f"david.ouma@{DOMAIN}"
PETER = f"peter.mwangi@{DOMAIN}"
GRACE = f"grace.njeri@{DOMAIN}"
AMINA = f"amina.yusuf@{DOMAIN}"
STAFF = f"internal.staff@{DOMAIN}"
USERS = {MARY: "Mary Wanjiku", DAVID: "David Ouma", PETER: "Peter Mwangi", GRACE: "Grace Njeri"}
def _blank_pdf() -> bytes:
	from io import BytesIO

	from pypdf import PdfWriter

	writer = PdfWriter()
	writer.add_blank_page(width=72, height=72)
	buffer = BytesIO()
	writer.write(buffer)
	return buffer.getvalue()


PDF = _blank_pdf()
CLEAN = "Clean — test scanner"
AFYA = {
	"legal_name": "Afya Digital Supplies Limited", "country": "Kenya", "registration_number": "PVT-ACCT-9X7K2M", "tax_identifier": "P051234567X",  # test-only: the canonical seed holds PVT-9X7K2M
	"registered_address": "Westlands Business Park, Waiyaki Way, Nairobi", "official_email": "tenders@afyadigital.example", "official_phone": "+254 709 555 014",
	"job_title": "Managing Director",
}
ACCOUNT_DOCTYPES = ("Supplier Account Access Decision", "Supplier User Assignment", "Supplier Account Verification", "Supplier Account Evidence", "Supplier Organisation")


def key() -> str:
	return f"acc-test-{uuid.uuid4().hex}"


def _user(email: str, full_name: str, *, desk_role: str = "") -> None:
	"""A portal (Website) user, or internal staff with one Desk role."""
	if frappe.db.exists("User", email):
		return
	first, _, last = full_name.partition(" ")
	doc = frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "send_welcome_email": 0, "user_type": "System User" if desk_role else "Website User"})
	doc.insert(ignore_permissions=True)
	if desk_role:
		doc.add_roles(desk_role)


def ensure_world() -> None:
	from kentender_core.services import responsibility_administration as administration
	from kentender_core.services.business_role_registry import ensure_roles

	frappe.set_user("Administrator")
	ensure_roles()
	for email, name in USERS.items():
		_user(email, name)
	_user(STAFF, "Internal Staff", desk_role="System Manager")
	_user(AMINA, "Amina Yusuf", desk_role="Desk User")
	administration.grant(user=AMINA, business_role="Supplier Account Support Officer", fixture_namespace=NS, actor="Administrator")
	frappe.db.commit()


def wipe_accounts() -> list[str]:
	"""Delete every Account record the tests made; returns their names."""
	names: list[str] = []
	for doctype in ACCOUNT_DOCTYPES:
		for name in frappe.get_all(doctype, filters={"fixture_namespace": NS}, pluck="name"):
			if doctype == "Supplier Account Evidence":
				for file_name in frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name}, pluck="name"):
					frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)
			doc = frappe.get_doc(doctype, name)
			doc.flags.kt_fixture_wipe = True
			doc.delete(ignore_permissions=True, force=True)
			names.append(name)
	frappe.db.delete("Supplier Account Command Journal", {"idempotency_key": ("like", "acc-test-%")})
	if names:
		frappe.db.delete("Audit Event", {"document_name": ("in", names)})
	for email in frappe.get_all("User", filters={"email": ("like", f"%@{DOMAIN}")}, pluck="name"):
		frappe.db.delete("Audit Event", {"performed_by": email})
	frappe.db.commit()
	return names


def purge() -> None:
	frappe.set_user("Administrator")
	wipe_accounts()
	for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NS}, pluck="name"):
		frappe.delete_doc("User Responsibility Assignment", name, force=True, ignore_permissions=True)
	for email in frappe.get_all("User", filters={"email": ("like", f"%@{DOMAIN}")}, pluck="name"):
		for contact in frappe.get_all("Contact", filters={"user": email}, pluck="name"):
			frappe.delete_doc("Contact", contact, force=True, ignore_permissions=True)
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()


class AccountsCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_world()
		cls.addClassCleanup(purge)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		wipe_accounts()
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.flags.kt_accounts_fixture_namespace = NS
		frappe.flags.kt_accounts_clock = "2027-05-18 09:00:00"
		self.sent: list[dict] = []
		frappe.flags.kt_account_message_transport = lambda message: self.sent.append(message) or {"result": "Delivered"}
		for flag in ("kt_accounts_fixture_namespace", "kt_accounts_clock", "kt_account_message_transport"):
			self.addCleanup(setattr, frappe.flags, flag, None)
		self.scanner = mock.patch("kentender_core.services.file_integrity.scanner_result", return_value=CLEAN)
		self.scanner.start()
		self.addCleanup(self.scanner.stop)

	def at(self, instant: str) -> None:
		frappe.flags.kt_accounts_clock = instant

	def register(self, user: str = MARY, **overrides):
		from kentender_suppliers.supplier_accounts.services import registration

		values = {**AFYA, "authority_filename": "mary-wanjiku-signing-authority.pdf", "authority_content": PDF, **overrides}
		return registration.register_supplier_organisation(**values, idempotency_key=key(), user=user)

	def token(self) -> str:
		return self.sent[-1]["link"].split("token=", 1)[1]

	def active_account(self, user: str = MARY, **overrides) -> str:
		from kentender_suppliers.supplier_accounts.services import verification

		result = self.register(user, **overrides)
		verification.verify_account_communication(token=self.token(), user=user)
		return result["organisation"]
