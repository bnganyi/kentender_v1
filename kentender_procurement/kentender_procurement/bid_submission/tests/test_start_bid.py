# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.3, §4.5, §5.1, §5.2, §7.2 `StartBid` and §8 (plan
Phase 5, BDS8-502; BDS01-AC-011, BDS08-AC-001…003): one committing command
creates or returns the Tender-bound arrangement (the candidate registration),
its mandatory-notice address and one Draft on the current definition; every
guard leaves nothing behind."""

from __future__ import annotations

import json
from unittest import mock

import frappe

from kentender_procurement.bid_submission.services import errors, start_bid
from kentender_procurement.bid_submission.tests.support import AFYA, DAVID, JUA, KISIWA, MARY, NOBODY, PETER, START_AT, BidCase, key
from kentender_procurement.tenders.services import bid_definition

class StartBidCase(BidCase):
	def start(self, user=DAVID, organisation=AFYA, arrangement=None, notice_contact_id=f"{AFYA}-C1", idempotency_key=None):
		return start_bid.start_bid(
			tender_reference=self.reference, organisation=organisation, arrangement=arrangement or self.single(), notice_contact_id=notice_contact_id,
			idempotency_key=idempotency_key or key(), user=user,
		)

	def assertNothingCreated(self):
		self.assertEqual(frappe.db.count("Bidder Arrangement", {"tender": self.name}), 0)
		self.assertEqual(frappe.db.count("Bid Workspace", {"tender": self.name}), 0)

	def assertFails(self, code, **kwargs):
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			self.start(**kwargs)
		self.assertEqual(ctx.exception.code, code)
		self.assertNothingCreated()


class TestStartSingleOrganisation(StartBidCase):
	def test_david_starts_a_bid_that_is_the_candidate_registration_and_one_draft(self):
		result = self.start()
		suffix = self.reference.removeprefix("TND-")
		self.assertEqual((result["ok"], result["created"], result["bid_reference"], result["bidder_arrangement_id"]), (True, True, f"BID-{suffix}-001", f"ARR-{suffix}-001"))
		arrangement = frappe.get_doc("Bidder Arrangement", result["bidder_arrangement_id"])
		self.assertEqual(
			(arrangement.arrangement_type, arrangement.lead_organisation, arrangement.lead_legal_name, arrangement.status, str(arrangement.candidate_registered_at)),
			("Single organisation", AFYA, "Afya Digital Supplies Limited", "Active", START_AT),
		)
		self.assertEqual((arrangement.mandatory_notice_email, arrangement.notice_contact_version), ("tenders@afyadigital.example", 1))
		self.assertEqual([(c.notice_contact_version, c.email, c.set_by) for c in arrangement.notice_contacts], [(1, "tenders@afyadigital.example", DAVID)])
		self.assertEqual((arrangement.tender_contact_user, arrangement.tender_contact_name, arrangement.tender_contact_email), (DAVID, "David Ouma", DAVID))
		self.assertEqual([m.organisation_id for m in arrangement.members], [])
		workspace = frappe.get_doc("Bid Workspace", result["bid_reference"])
		current = bid_definition.current(self.name)
		self.assertEqual(
			(workspace.status, workspace.current_draft_version, workspace.bid_definition_id, workspace.definition_version, workspace.definition_digest, workspace.bidder_arrangement),
			("Draft", 1, current["bid_definition_id"], current["definition_version"], current["definition_digest"], arrangement.name),
		)
		snapshot = frappe.get_doc("Bid Organisation Snapshot", workspace.organisation_snapshot)
		facts = json.loads(snapshot.facts_json)
		self.assertEqual((snapshot.snapshot_version, facts["organisation"]["legal_name"], facts["organisation"]["registration_number"], facts["members"]), (1, "Afya Digital Supplies Limited", "PVT-9X7K2M", []))
		self.assertEqual(frappe.get_all("Bid Submission Event", filters={"bid_workspace": workspace.name}, pluck="event_type"), ["BidStarted"])

	def test_the_tender_contact_phone_starts_as_the_phone_the_organisation_registered(self):
		# like the email: a default the bidder may change for this bid
		result = self.start()
		registered = start_bid.supplier_gateway.organisation(organisation_id=AFYA)["official_phone"]
		self.assertTrue(registered)
		self.assertEqual(frappe.db.get_value("Bidder Arrangement", result["bidder_arrangement_id"], "tender_contact_phone"), registered)

	def test_a_registered_phone_the_contact_rules_would_refuse_is_left_for_the_bidder_to_enter(self):
		real = start_bid.supplier_gateway.organisation

		def long_phone(**kwargs):
			return {**real(**kwargs), "official_phone": "1" * 25}

		with mock.patch.object(start_bid.supplier_gateway, "organisation", side_effect=long_phone):
			result = self.start()
		self.assertEqual(frappe.db.get_value("Bidder Arrangement", result["bidder_arrangement_id"], "tender_contact_phone"), "")

	def test_starting_again_returns_the_same_bid_for_any_person_of_the_organisation(self):
		first = self.start()
		again = self.start(user=MARY)
		self.assertEqual((again["created"], again["bid_reference"], again["bidder_arrangement_id"]), (False, first["bid_reference"], first["bidder_arrangement_id"]))
		self.assertEqual(frappe.db.count("Bid Workspace", {"tender": self.name}), 1)

	def test_a_replayed_request_returns_its_result_and_a_changed_one_is_refused(self):
		request = key()
		first = self.start(idempotency_key=request)
		self.assertEqual(self.start(idempotency_key=request), first)
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			self.start(idempotency_key=request, notice_contact_id="another")
		self.assertEqual(ctx.exception.code, "BDS_IDEMPOTENCY_CONFLICT")


class TestStartGuards(StartBidCase):
	def test_each_guard_refuses_before_anything_is_created(self):
		self.assertFails("BDS_SIGN_IN_REQUIRED", user="Guest")
		self.assertFails("BDS_ACCOUNT_REQUIRED", user=NOBODY)
		# another organisation's account is masked as having no account
		self.assertFails("BDS_ACCOUNT_REQUIRED", user=PETER, organisation=AFYA)
		self.accounts.orgs[AFYA]["account_status"] = "Suspended"
		self.assertFails("BDS_ACCOUNT_SUSPENDED")
		self.accounts.orgs[AFYA]["account_status"] = "Pending verification"
		self.assertFails("BDS_ACCOUNT_REQUIRED")
		self.accounts.orgs[AFYA]["account_status"] = "Active"
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete", "missing": ["support"]}):
			self.assertFails("BDS_PORTAL_INFORMATION_UNAVAILABLE")
		self.at("2027-07-01 09:00:00")
		self.assertFails("BDS_TENDER_NOT_OPEN")

	def test_an_unknown_tender_is_not_found(self):
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			start_bid.start_bid(tender_reference="TND-NOPE-0000-000", organisation=AFYA, arrangement=self.single(), notice_contact_id=f"{AFYA}-C1", idempotency_key=key(), user=DAVID)
		self.assertEqual(ctx.exception.code, "BDS_TENDER_NOT_FOUND")

	def test_an_unverified_notice_email_is_returned_as_data_and_creates_nothing(self):
		result = self.start(notice_contact_id="not-a-verified-contact")
		self.assertEqual((result["ok"], result["code"], list(result["errors"])), (False, "BDS_NOTICE_CONTACT_REQUIRED", ["notice_contact_id"]))
		self.assertNothingCreated()

	def test_an_unsupported_definition_creates_no_partial_bid(self):
		with mock.patch("kentender_procurement.bid_submission.services.tenders_gateway.release_status", return_value={"lifecycle": "Withdrawn", "integrity_ok": True, "renderer_ok": True}):
			self.assertFails("BDS_DEFINITION_UNSUPPORTED")
		with mock.patch("kentender_procurement.bid_submission.services.tenders_gateway.release_status", return_value={"lifecycle": "Available", "site_switch": "Off", "integrity_ok": False, "renderer_ok": True}):
			self.assertFails("BDS_DEFINITION_UNSUPPORTED")
		current = bid_definition.current(self.name)
		tampered = dict(current, definition=dict(current["definition"], submission_deadline="2099-01-01T00:00:00+03:00"))
		with mock.patch("kentender_procurement.bid_submission.services.tenders_gateway.current_definition", return_value=tampered):
			self.assertFails("BDS_DEFINITION_UNSUPPORTED")

	def test_a_new_bid_binds_the_template_release_of_the_current_template_standard(self):
		# owner, 28 Sep 2026 ("Match the new template version"): integration
		# tests run on template release 1.2 — the release STD-TPL-001 v0.13
		# authorised — switched On; release 1.1 takes no new binding
		workspace = frappe.get_doc("Bid Workspace", self.start()["bid_reference"])
		release_id = bid_definition.definition_for(self.name, workspace.definition_version)["definition"]["template_release_id"]
		release = frappe.db.get_value("Installed STD Release", release_id, ["template_key", "template_release", "lifecycle_status", "site_switch"], as_dict=True)
		self.assertEqual((release.template_key, release.template_release, release.lifecycle_status, release.site_switch), ("IT-EQUIPMENT-OPEN-V1", "1.3", "Available", "On"))
		self.assertEqual(frappe.get_all("Installed STD Release", filters={"template_key": "IT-EQUIPMENT-OPEN-V1", "template_release": "1.1", "site_switch": "On"}), [])

	def test_a_release_switched_off_still_permits_a_bid_on_a_published_tender(self):
		with mock.patch("kentender_procurement.bid_submission.services.tenders_gateway.release_status", return_value={"lifecycle": "Available", "site_switch": "Off", "integrity_ok": True, "renderer_ok": True}):
			self.assertTrue(self.start()["created"])

	def test_a_failure_after_the_arrangement_leaves_no_arrangement(self):
		with mock.patch("kentender_procurement.bid_submission.services.start_bid._create_workspace", side_effect=RuntimeError("storage failure")):
			with self.assertRaises(RuntimeError):
				self.start()
		self.assertNothingCreated()


class TestStartJointVenture(StartBidCase):
	def test_peter_starts_a_joint_venture_with_an_account_backed_member(self):
		result = self.start(user=PETER, organisation=KISIWA, arrangement=self.joint_venture(), notice_contact_id=f"{KISIWA}-C1")
		arrangement = frappe.get_doc("Bidder Arrangement", result["bidder_arrangement_id"])
		self.assertEqual(
			(arrangement.arrangement_type, arrangement.joint_venture_name, arrangement.agreement_evidence, arrangement.authorised_signatory_assignment),
			("Joint venture", "Kisiwa–Jua Technology JV", "EVD-BDST-JV", f"ASG-{KISIWA}-bdst.grace"),
		)
		self.assertEqual([(m.member_order, m.organisation_id, m.legal_name) for m in arrangement.members], [(1, KISIWA, "Kisiwa Digital Limited"), (2, JUA, "Jua Technology Limited")])
		facts = json.loads(frappe.db.get_value("Bid Organisation Snapshot", frappe.db.get_value("Bid Workspace", result["bid_reference"], "organisation_snapshot"), "facts_json"))
		self.assertEqual([m["legal_name"] for m in facts["members"]], ["Kisiwa Digital Limited", "Jua Technology Limited"])

	def test_each_joint_venture_problem_is_named_and_creates_nothing(self):
		cases = {
			"joint_venture_name": self.joint_venture(joint_venture_name=""),
			"members": self.joint_venture(members=[]),
			"members.0": self.joint_venture(members=[{"country": "Kenya", "registration_number": "PVT-NOBODY"}]),
			"agreement_evidence_id": self.joint_venture(agreement_evidence_id="EVD-NOT-OURS"),
			"signatory_assignment_id": self.joint_venture(signatory_assignment_id=f"ASG-{KISIWA}-bdst.peter"),
		}
		cases["members.0 (lead)"] = self.joint_venture(members=[{"country": "Kenya", "registration_number": "PVT-KSW001"}])
		for field, arrangement in cases.items():
			with self.subTest(field=field):
				result = self.start(user=PETER, organisation=KISIWA, arrangement=arrangement, notice_contact_id=f"{KISIWA}-C1")
				self.assertEqual((result["ok"], result["code"]), (False, "BDS_ARRANGEMENT_INVALID"))
				self.assertIn(field.split(" ")[0], result["errors"])
				self.assertNothingCreated()

	def test_an_arrangement_the_tender_does_not_permit_is_refused(self):
		result = self.start(user=PETER, organisation=KISIWA, arrangement={"arrangement_type": "Consortium"}, notice_contact_id=f"{KISIWA}-C1")
		self.assertEqual((result["code"], list(result["errors"])), ("BDS_ARRANGEMENT_INVALID", ["arrangement_type"]))
		self.assertNothingCreated()
