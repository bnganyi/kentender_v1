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


class TestPublicationBoundaryOnInsertAndConfigurationLock(IntegrationTestCase):
	"""RG-05 / AUD-XC-011 residue — the boundary also holds on insert, and the
	publication lock on a configuration cannot be lifted with one save."""

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	_new = TestPublicationRecordPermissions._new
	_load = TestPublicationRecordPermissions._load

	def test_a_publication_record_cannot_be_created_already_published(self):
		for values in ({"status": "Published"}, {"status": "Ready to Publish"}, {"electronic_template_snapshot": "{}", "electronic_template_hash": "x" * 64}):
			doc = frappe.get_doc({"doctype": PUBLICATION, "configuration": "RG05-CFG", "status": "Awaiting Publication Setup", **values})
			doc.flags.ignore_links = True
			doc.flags.ignore_mandatory = True
			with self.assertRaises(frappe.ValidationError, msg=str(values)):
				doc.insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists(PUBLICATION, {"configuration": "RG05-CFG"}))

	def test_the_publication_service_still_creates_its_record(self):
		doc = frappe.get_doc({"doctype": PUBLICATION, "configuration": "RG05-CFG-OK", "status": "Awaiting Publication Setup"})
		doc.flags.ignore_publication_boundary = True  # what create_publication_record sets
		doc.flags.ignore_links = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		self.addCleanup(lambda: frappe.delete_doc(PUBLICATION, doc.name, force=True, ignore_permissions=True))
		self.assertEqual(frappe.db.get_value(PUBLICATION, doc.name, "status"), "Awaiting Publication Setup")

	def _locked_configuration(self):
		pkg = self._new(PACKAGE, configuration="RG05-CFG", package_status="Confirmed")
		cfg = self._new("Tender Configuration", configuration_ref="RG05-CFG-REF", tender_title="Locked tender", status="Sent to Publication Workflow", confirmed_document_package=pkg.name)
		return pkg, self._load("Tender Configuration", cfg.name)

	def test_clearing_the_confirmed_package_does_not_lift_the_lock(self):
		pkg, cfg = self._locked_configuration()
		cfg.confirmed_document_package = ""
		with self.assertRaises(frappe.ValidationError):
			cfg.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Tender Configuration", cfg.name, "confirmed_document_package"), pkg.name)

	def test_the_status_of_a_locked_configuration_is_not_a_free_select(self):
		_pkg, cfg = self._locked_configuration()
		cfg.status = "Published"
		with self.assertRaises(frappe.ValidationError):
			cfg.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Tender Configuration", cfg.name, "status"), "Sent to Publication Workflow")

	def test_the_services_still_move_a_locked_configuration(self):
		pkg, cfg = self._locked_configuration()
		cfg.flags.ignore_f1_publication_lock = True  # what the return-for-correction and publish services set
		cfg.confirmed_document_package = ""
		cfg.status = "Returned for Correction"
		cfg.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Tender Configuration", cfg.name, "status"), "Returned for Correction")
