# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §13.3 and plan D19 (BDS8-503; TPR FU-25): the seeded
candidate is a real Start bid over a real supplier account, through the
installed Supplier Accounts provider (no fake here), and a browser-test
world's own supplier account is removed with it."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.seeds import canonical as bds_seed
from kentender_procurement.bid_submission.tests.support import START_AT, BidCase
from kentender_procurement.tenders.services import candidate_gateway

WORLD = "BDS_TEST_SEED_SUPPLIERS"
SUPPLIER = {
	"facts": {
		"legal_name": "Seed Test Supplies Limited", "country": "Kenya", "registration_number": "PVT-BDST-SEED1", "tax_identifier": "P000000077X",
		"registered_address": "Test House, Mombasa Road, Nairobi", "official_email": "tenders@seedtest.example", "official_phone": "+254 700 000 077", "job_title": "Director",
	},
	"registrant": "director@seedtest.example", "registrant_name": "Seed Test Director", "representative": "bids@seedtest.example",
	"representative_name": "Seed Test Coordinator", "namespace": WORLD,
}
USERS = (SUPPLIER["registrant"], SUPPLIER["representative"])


class TestSeededCandidate(BidCase):
	def setUp(self):
		super().setUp()
		self._flag("kt_supplier_account_provider", None)  # the installed provider
		self._flag("kt_tender_candidate_registry", None)  # the installed registry
		self._flag("kt_bds_fixture_namespace", None)
		# the seeded signatory's authority evidence needs the Test Scanner (owner decision OD-C)
		previous = frappe.conf.get("kt_bds_simulation_environment")
		frappe.conf["kt_bds_simulation_environment"] = 1
		self.addCleanup(frappe.conf.__setitem__, "kt_bds_simulation_environment", previous)
		self.addCleanup(self._remove_world)

	def _remove_world(self):
		bds_seed.remove_seeded_suppliers(namespace=WORLD, users=USERS)
		frappe.db.commit()

	def test_the_seeded_candidate_is_a_start_bid_over_a_real_account(self):
		afya = bds_seed.seed_candidate(tender_reference=self.reference, at=START_AT)
		self.assertEqual(bds_seed.seed_candidate(tender_reference=self.reference, at=START_AT), afya)
		world = bds_seed.seed_candidate(tender_reference=self.reference, at=START_AT, supplier=SUPPLIER)
		audience = candidate_gateway.candidate_audience(tender=self.name, at=START_AT)
		self.assertEqual([(r["candidate_registration_id"], r["destination"]) for r in audience], [(afya, "tenders@afyadigital.example"), (world, "tenders@seedtest.example")])
		self.assertEqual(candidate_gateway.candidate_name(tender=self.name, candidate_registration_id=afya), "Afya Digital Supplies Limited")
		self.assertEqual(frappe.db.get_value("Bidder Arrangement", afya, "created_by"), "david.ouma@afyadigital.example")
		removed = bds_seed.remove_seeded_suppliers(namespace=WORLD, users=USERS)
		self.assertEqual((removed.get("Supplier Organisation"), removed.get("User")), (1, 2))
		self.assertFalse(frappe.db.exists("Supplier Organisation", {"registration_number": "PVT-BDST-SEED1"}))
		self.assertTrue(frappe.db.exists("Supplier Organisation", {"registration_number": "PVT-9X7K2M", "account_status": "Active"}))
