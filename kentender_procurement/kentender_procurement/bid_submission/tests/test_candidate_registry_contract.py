# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.3, §5.2 item 10, §7.2 `UpdateTenderNoticeContact` and
TPR-CHG-001 v0.12 §4.9A (plan Phase 5, BDS8-502; TPR FU-25): the arrangement
Start bid creates is the candidate Tenders sees, with the notice address in
force at each instant."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_submission.services import candidate_registry, errors, notice_contact, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, KISIWA, PETER, START_AT, BidCase, key
from kentender_procurement.tenders.services import candidate_gateway


class TestCandidateRegistry(BidCase):
	def start(self, user=DAVID, organisation=AFYA, arrangement=None, contact=f"{AFYA}-C1"):
		return start_bid.start_bid(tender_reference=self.reference, organisation=organisation, arrangement=arrangement or self.single(), notice_contact_id=contact, idempotency_key=key(), user=user)

	def test_the_provider_meets_the_tenders_contract(self):
		for name in ("candidate_audience", "candidate_registration"):
			self.assertTrue(callable(getattr(candidate_registry, name)), name)
		self.assertEqual(frappe.get_hooks("kt_tender_candidate_registry")[-1], "kentender_procurement.bid_submission.services.candidate_registry")

	def test_the_arrangement_is_the_candidate_from_its_start_instant(self):
		arrangement = self.start()["bidder_arrangement_id"]
		jv = self.start(user=PETER, organisation=KISIWA, arrangement=self.joint_venture(), contact=f"{KISIWA}-C1")["bidder_arrangement_id"]
		self.assertEqual(candidate_gateway.candidate_audience(tender=self.name, at="2027-05-19 09:19:59"), [])
		self.assertEqual(
			candidate_gateway.candidate_audience(tender=self.name, at=START_AT),
			[{"candidate_registration_id": arrangement, "destination": "tenders@afyadigital.example", "destination_version": "1"}, {"candidate_registration_id": jv, "destination": "tenders@kisiwadigital.example", "destination_version": "1"}],
		)
		self.assertEqual(candidate_gateway.candidate_name(tender=self.name, candidate_registration_id=arrangement), "Afya Digital Supplies Limited")
		self.assertEqual(candidate_gateway.candidate_name(tender=self.name, candidate_registration_id=jv), "Kisiwa–Jua Technology JV")
		self.assertIsNone(candidate_gateway.candidate_registration(tender=self.name, candidate_registration_id="ARR-NOPE-001"))

	def test_a_notice_email_change_applies_from_its_instant_only(self):
		arrangement = self.start()["bidder_arrangement_id"]
		self.accounts.contacts[AFYA].append({"contact_id": f"{AFYA}-C2", "channel": "Email", "value": "bids@afyadigital.example", "contact_version": 1, "is_official": False})
		self.at("2027-05-25 10:00:00")
		version = frappe.db.get_value("Bidder Arrangement", arrangement, "record_version")
		unverified = notice_contact.update_tender_notice_contact(bidder_arrangement_id=arrangement, notice_contact_id="unverified", expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual((unverified["ok"], unverified["code"]), (False, "BDS_NOTICE_CONTACT_REQUIRED"))
		changed = notice_contact.update_tender_notice_contact(bidder_arrangement_id=arrangement, notice_contact_id=f"{AFYA}-C2", expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual((changed["changed"], changed["notice_contact_version"]), (True, 2))
		self.assertEqual(candidate_gateway.candidate_audience(tender=self.name, at="2027-05-20 09:00:00")[0]["destination"], "tenders@afyadigital.example")
		self.assertEqual(candidate_gateway.candidate_audience(tender=self.name, at="2027-05-26 09:00:00")[0], {"candidate_registration_id": arrangement, "destination": "bids@afyadigital.example", "destination_version": "2"})
		with self.assertRaises(errors.BidSubmissionError) as stale:
			notice_contact.update_tender_notice_contact(bidder_arrangement_id=arrangement, notice_contact_id=f"{AFYA}-C1", expected_record_version=version, idempotency_key=key(), user=DAVID)
		self.assertEqual(stale.exception.code, "BDS_STALE_VERSION")
		with self.assertRaises(errors.BidSubmissionError) as masked:
			notice_contact.update_tender_notice_contact(bidder_arrangement_id=arrangement, notice_contact_id=f"{KISIWA}-C1", expected_record_version=changed["record_version"], idempotency_key=key(), user=PETER)
		self.assertEqual(masked.exception.code, "BDS_TENDER_NOT_FOUND")
