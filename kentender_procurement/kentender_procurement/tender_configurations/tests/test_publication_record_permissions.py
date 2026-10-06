# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-011 — role ``All`` must not write the confirmed package or the publication record.

``All`` is every logged-in user (frappe/permissions.py gives it to each non-Guest), so a
supplier account could mark a publication record Published or invalidate a confirmed
tender package with a plain REST write. The doctypes now grant only the officer roles
that already own Tender Configuration, and a direct status change is refused unless it
comes from the publication services, which set an explicit flag.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

PACKAGE = "Confirmed Tender Document Package"
PUBLICATION = "IT Tender Publication Record"


class TestPublicationRecordPermissions(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def _new(self, doctype: str, **values):
		doc = frappe.get_doc({"doctype": doctype, **values})
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.db.exists(doctype, doc.name)
			and frappe.delete_doc(doctype, doc.name, force=True, ignore_permissions=True)
		)
		return doc

	def _load(self, doctype: str, name: str):
		doc = frappe.get_doc(doctype, name)
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		return doc

	def test_role_all_has_no_permission_row(self):
		for doctype in (PACKAGE, PUBLICATION):
			roles = {p.role for p in frappe.get_meta(doctype).permissions}
			self.assertNotIn("All", roles, doctype)
			self.assertIn("System Manager", roles, doctype)

	def test_user_without_officer_role_cannot_write_either_doctype(self):
		email = "xc011.noroles@example.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{"doctype": "User", "email": email, "first_name": "Noroles", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc("User", email, force=True, ignore_permissions=True))
		for doctype in (PACKAGE, PUBLICATION):
			for ptype in ("read", "write", "create"):
				self.assertFalse(
					frappe.has_permission(doctype, ptype, user=email), f"{doctype} {ptype}"
				)

	def test_publication_status_cannot_be_changed_outside_the_service(self):
		pkg = self._new(PACKAGE, configuration="XC011-CFG", package_status="Confirmed")
		pub = self._new(
			PUBLICATION,
			configuration="XC011-CFG",
			confirmed_package=pkg.name,
			status="Awaiting Publication Setup",
		)
		pub = self._load(PUBLICATION, pub.name)
		pub.status = "Published"
		with self.assertRaises(frappe.ValidationError):
			pub.save(ignore_permissions=True)
		self.assertEqual(
			frappe.db.get_value(PUBLICATION, pub.name, "status"), "Awaiting Publication Setup"
		)

		pub = self._load(PUBLICATION, pub.name)
		pub.flags.ignore_publication_boundary = True  # what the publication services set
		pub.status = "Ready to Publish"
		pub.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value(PUBLICATION, pub.name, "status"), "Ready to Publish")

	def test_package_status_cannot_be_changed_outside_the_service(self):
		pkg = self._new(PACKAGE, configuration="XC011-CFG", package_status="Confirmed")
		pkg = self._load(PACKAGE, pkg.name)
		pkg.package_status = "Invalidated"
		with self.assertRaises(frappe.ValidationError):
			pkg.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value(PACKAGE, pkg.name, "package_status"), "Confirmed")

		pkg = self._load(PACKAGE, pkg.name)
		pkg.flags.ignore_package_immutability = True  # what the handoff service sets
		pkg.package_status = "Invalidated"
		pkg.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value(PACKAGE, pkg.name, "package_status"), "Invalidated")
