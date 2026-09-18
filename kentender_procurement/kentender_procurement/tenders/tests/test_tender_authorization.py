# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §6 — the service-layer gates and the two Frappe
permission hooks: Site-wide readers see everything, a departmental reader
sees only a Tender whose lead unit is theirs, an outsider sees nothing (and
is masked as not-found on a record read), technical users read everything
and hold no business action."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.services import envelope, tender_authorization as authz
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.procurement_planning.tests import fixtures as pln_fx
from kentender_procurement.tenders.tests import fixtures as fx


class TendersAuthorizationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_tender_rows()
		self.addCleanup(frappe.set_user, "Administrator")

	def _tender(self, *, lead_unit: str) -> str:
		doc = frappe.get_doc({"doctype": "Tender", "tender_reference": f"TND-TEST-AUTH-{lead_unit[-4:]}", "overall_status": "Draft", "lead_org_unit": lead_unit, "contributing_org_unit_ids": f'["{lead_unit}"]', "record_version": 0, "fixture_namespace": fx.NS})
		envelope.insert(doc)
		envelope.insert(frappe.get_doc({"doctype": "Tender Version", "tender": doc.name, "version_number": 1, "status": "Draft", "record_version": 0, "fixture_namespace": fx.NS}))
		return doc.name


class TestServiceGates(TendersAuthorizationCase):
	def test_each_site_role_gate_accepts_its_holder_and_masks_others(self):
		for gate, holder in ((authz.require_officer, fx.OFFICER), (authz.require_hopf, fx.HOPF), (authz.require_ao, fx.AO)):
			self.assertIsNotNone(gate(holder))
			with self.assertRaises(frappe.DoesNotExistError):
				gate(fx.NOBODY)
			with self.assertRaises(TendersError) as ctx:
				gate(fx.NOBODY, masked=False)
			self.assertEqual(ctx.exception.code, "TND_RESPONSIBILITY_REQUIRED")

	def test_the_both_actor_holds_every_actor_role(self):
		self.assertEqual(authz.site_roles_held(fx.BOTH), ("Procurement Officer", "Head of Procurement Function", "Accounting Officer"))

	def test_page_verdict(self):
		for user in (fx.OFFICER, fx.HOPF, fx.AO, fx.AUDITOR, fx.DEPARTMENTAL, "Administrator"):
			self.assertTrue(authz.holds_any_tender_responsibility(user), user)
		self.assertFalse(authz.holds_any_tender_responsibility(fx.NOBODY))

	def test_reader_mode(self):
		alpha = pln_fx.OU_ALPHA
		self.assertEqual(authz.reader_mode(fx.AUDITOR, contributing_org_units={alpha}), "site")
		self.assertEqual(authz.reader_mode(fx.DEPARTMENTAL, contributing_org_units={alpha}), "department")
		self.assertEqual(authz.reader_mode("Administrator", contributing_org_units=set()), "technical")
		with self.assertRaises(frappe.DoesNotExistError):
			authz.reader_mode(fx.OUTSIDER, contributing_org_units={alpha})
		with self.assertRaises(frappe.DoesNotExistError):
			authz.reader_mode(fx.NOBODY, contributing_org_units={alpha})


class TestFrameworkHooks(TendersAuthorizationCase):
	def test_list_and_record_permissions_follow_the_section_6_scope(self):
		alpha, beta = pln_fx.OU_ALPHA, pln_fx.OU_BETA
		mine = self._tender(lead_unit=alpha)
		theirs = self._tender(lead_unit=beta)
		frappe.set_user(fx.AUDITOR)
		self.assertEqual(set(frappe.get_list("Tender", pluck="name")), {mine, theirs})
		frappe.set_user(fx.OFFICER)
		self.assertEqual(set(frappe.get_list("Tender", pluck="name")), {mine, theirs})
		self.assertEqual(len(frappe.get_list("Tender Version", pluck="name")), 2)
		frappe.set_user(fx.DEPARTMENTAL)
		self.assertEqual(frappe.get_list("Tender", pluck="name"), [mine])
		self.assertTrue(frappe.has_permission("Tender", doc=mine))
		self.assertFalse(frappe.has_permission("Tender", doc=theirs))
		versions = frappe.get_list("Tender Version", pluck="tender")
		self.assertEqual(versions, [mine])
		frappe.set_user(fx.NOBODY)
		# No responsibility at all → no projected Frappe Role → the framework
		# refuses the list outright (never an empty success), and the record
		# check is False.
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Tender", pluck="name")
		self.assertFalse(frappe.has_permission("Tender", doc=mine))
		frappe.set_user(fx.OUTSIDER)  # a departmental reader in the other unit: only that unit's Tender
		self.assertEqual(frappe.get_list("Tender", pluck="name"), [theirs])
		self.assertFalse(frappe.has_permission("Tender", doc=mine))
		frappe.set_user("Administrator")
		self.assertEqual(len(frappe.get_list("Tender", pluck="name")), 2)

	def test_the_template_registry_is_listed_only_by_site_readers(self):
		frappe.set_user(fx.AUDITOR)
		self.assertTrue(frappe.get_list("Supported Tender Template", pluck="name"))
		frappe.set_user(fx.OUTSIDER)
		self.assertFalse(frappe.has_permission("Supported Tender Template", doc=frappe.get_all("Supported Tender Template", pluck="name")[0]))
		frappe.set_user(fx.NOBODY)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_list("Supported Tender Template", pluck="name")
