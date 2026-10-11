# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""KT-ACCESS-REV-001 AR-01 — a technical reader never reads a bid's identity or
payload before governed opening through a raw Desk / REST read.

BDS-CHG-001 v0.11 §6: Administrator / System Manager see "configuration/health
metadata only for sealed bids; no business authority and no content access
before governed opening". The service layer already answers that; the DocPerm
rows must not hand the same records out by another door. Project Owner, 10
October 2026: that includes Administrator, whom Frappe lets past every
`has_permission` hook — the record itself now refuses (`sealed.SealedRecordMixin`),
and no technical account sees a bid's existence, count, identity, receipt or a
supplier's security intake, before or after the opening.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.tests import v16_fixtures as fx

SEALED = (
	"Bid Section Response",
	"Bid Evidence",
	"Bid Draft Change",
	"Bid Command Journal",
	"Bid Receipt",
	"Bid Submission Change",
	"Bidder Arrangement",
	"Bid Organisation Snapshot",
	"Bid Workspace",
	"Bid Submission Attempt",
	"Bid Submission Version",
	"Bid Submission Event",
	"Tender Box Envelope",
	"Bid Opening Handoff",
	"Bid Hand-off",
	"Bid Submission Close",
	"Bid Submission Incident",
	"Tender Security Intake",
	"Tender Security Intake Match",
	"Tender Security Exposure",
	"Tender Security Duty Conflict",
	"Tender Security Verification",
	"Opening Access Incident",
	"Opening Exception",
	"Opening Decision Item",
	"Opening Entry",
	"Opening Register Request",
	"Opening Incident Access Event",
)


class TestSealedBidDeskRead(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.manager = fx.user("sealed.sysmgr", "Sealed Test System Manager", roles=("System Manager",))

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_each_record_carries_both_denial_hooks(self):
		"""The list query is closed (`1=0`) and a single record is refused."""
		access = frappe.get_hooks("has_permission")
		query = frappe.get_hooks("permission_query_conditions")
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				self.assertIn("deny_desk_access", " ".join(access.get(doctype) or []))
				self.assertIn("deny_desk_query", " ".join(query.get(doctype) or []))

	def test_a_system_manager_cannot_read_a_single_record_of_them(self):
		# Frappe consults a has_permission hook for a concrete document, so the
		# check is made against one (an unsaved shell is enough for the hook).
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				doc = frappe.new_doc(doctype)
				doc.name = "sealed-probe"
				self.assertFalse(frappe.has_permission(doctype, "read", doc=doc, user=self.manager), doctype)

	def test_administrator_is_refused_the_record_itself(self):
		"""Frappe lets Administrator past has_permission, so the document refuses a read
		(REST read, form load, getdoc) unless the owning service is the caller."""
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				doc = frappe.new_doc(doctype)
				doc.name = "sealed-probe"
				self.assertFalse(doc.has_permission("read"), doctype)
				with self.assertRaises(frappe.PermissionError):
					doc.check_permission("read")
				doc.flags.ignore_permissions = True  # the owning service's own flag
				self.assertTrue(doc.has_permission("read"), doctype)

	def test_no_role_holds_a_docperm_on_a_sealed_record(self):
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				self.assertEqual(frappe.get_meta(doctype).permissions, [], doctype)

	def test_every_sealed_record_controller_carries_the_refusal(self):
		from kentender_procurement.bid_submission.services.sealed import SEALED_DOCTYPES, SealedRecordMixin

		self.assertEqual(set(SEALED_DOCTYPES), set(SEALED))
		for doctype in SEALED:
			with self.subTest(doctype=doctype):
				self.assertTrue(issubclass(frappe.get_meta(doctype).get_controller() if hasattr(frappe.get_meta(doctype), "get_controller") else frappe.get_doc({"doctype": doctype}).__class__, SealedRecordMixin), doctype)
