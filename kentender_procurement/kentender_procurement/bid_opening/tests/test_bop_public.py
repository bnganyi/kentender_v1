# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The public opening page (BOP-CHG-001 v0.10 §10.5; boards p0–p6; plan
Phase 9, BOP10-901…903): what a visitor sees at each stage, joining through
the published attendance channel, the live readout only after the recorder
confirms it, and the register request for a verified submitting supplier."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_opening.services import public, register_copy, simulation
from kentender_procurement.bid_opening.tests.support import CHAIR, MEMBER, OUTSIDER
from kentender_procurement.bid_opening.tests.test_bop_record import RecordCase
from kentender_procurement.bid_submission.tests.support import DAVID, PETER, key


class TestPublicOpening(RecordCase):
	def view(self, user: str = "Guest") -> dict:
		return public.get_public_opening(tender_reference=self.reference, user=user)

	def test_p0_to_p1_details_then_the_join_window(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		with self.assertRaises(frappe.DoesNotExistError):
			public.get_public_opening(tender_reference="TND-DOES-NOT-EXIST", user="Guest")
		self.prepare_case()
		p0 = self.view()
		self.assertEqual((p0["phase"], p0["arrangements"]["published"], p0["readout"], p0["can_join"]), ("details-coming", False, [], False))
		self.assertEqual(p0["arrangements"]["message"], "Details on how to attend the opening are coming soon")
		self.appoint()
		self.publish()
		self.assertEqual(self.view()["phase"], "before-join")
		self.at(self.minutes_before(3))
		guest = self.view()
		self.assertEqual((guest["phase"], guest["can_join"], guest["signed_in"]), ("join", False, False))  # a guest signs in first
		self.assertTrue(self.view(DAVID)["can_join"])
		with self.assertRaises(frappe.PermissionError):
			public.join_public_opening(tender=self.name, idempotency_key=key(), user="Guest")
		joined = public.join_public_opening(tender=self.name, idempotency_key=key(), user=DAVID)
		self.assertTrue(joined["joined"])
		after = self.view(DAVID)
		self.assertTrue(after["joined_label"])
		self.assertFalse(after["can_join"])
		# the Desk attendee list names whom they say they represent, not a bid
		from kentender_procurement.bid_opening.services import reads

		[attendee] = reads.get_opening(tender=self.name, user=CHAIR)["attendees"]
		self.assertEqual((attendee["capacity"], bool(attendee["represents"])), ("Tenderer representative", True))
		self.assertFalse(public.join_public_opening(tender=self.name, idempotency_key=key(), user=DAVID)["joined"])  # once only

	def test_the_public_endpoints(self):
		from kentender_procurement.bid_opening import api

		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.at(self.minutes_before(3))
		frappe.set_user("Guest")
		try:
			self.assertEqual(api.get_public_opening(self.reference)["phase"], "join")
			with self.assertRaises(frappe.PermissionError):
				api.join_public_opening(self.reference, key())
		finally:
			frappe.set_user("Administrator")
		frappe.set_user(DAVID)
		try:
			self.assertTrue(api.join_public_opening(self.reference, key())["joined"])
			with self.assertRaises(frappe.DoesNotExistError):
				api.download_opening_register(self.reference)  # nothing requested, nothing to download
		finally:
			frappe.set_user("Administrator")

	def test_the_portal_answers_the_opening_path_through_bid_openings_resolver(self):
		from kentender_procurement.bid_submission import portal

		self.prepared()
		out = portal.resolve(path=f"/tenders/{self.reference}/opening", query={}, user="Guest")
		self.assertEqual((out["verdict"], out["payload"]["screen"], out["payload"]["data"]["phase"]), ("OK", "public-opening", "before-join"))
		self.assertEqual(portal.resolve(path="/tenders/TND-DOES-NOT-EXIST/opening", query={}, user="Guest")["verdict"], "NOT_FOUND")

	def test_the_public_tender_page_links_to_the_opening(self):
		"""BOP-CHG-001 v0.10 §9: "The public Tender shows the published opening
		arrangement". The Tender overview carries a Bid opening entry linking to
		the opening page once the opening exists, for anyone."""
		from kentender_procurement.bid_submission.services import overview

		self.assertEqual(overview.get_tender_overview(tender_reference=self.reference, user="Guest").get("related_links"), [])
		self.prepared()
		[link] = overview.get_tender_overview(tender_reference=self.reference, user="Guest")["related_links"]
		self.assertEqual((link["label"], link["href"]), ("Bid opening", f"/tenders/{self.reference}/opening"))
		self.assertTrue(link["value"])

	def test_the_attendance_service_being_down_refuses_the_join(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepared()
		self.at(self.minutes_before(3))
		simulation.set_controls(attendance_service_down=1)
		self.assertFalse(self.view(PETER)["can_join"])
		refused = public.join_public_opening(tender=self.name, idempotency_key=key(), user=PETER)
		self.assertEqual((refused["ok"], refused["code"]), (False, "BOP_ATTENDANCE_SERVICE_UNAVAILABLE"))

	def test_p2_the_readout_appears_only_after_the_recorder_confirms_it(self):
		entry = self.opened()
		opened = self.view()
		self.assertEqual((opened["phase"], opened["status"], opened["readout"]), ("in-session", "In session", []))  # opened, not yet confirmed
		self.assertNotIn("KES", frappe.as_json(opened))
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		[row] = self.view()["readout"]
		self.assertEqual(row["number"], 1)
		self.assertTrue(row["submitted_total"].startswith("KES"))

	def test_p3_to_p6_the_register_request_after_completion(self):
		self.completed()
		self.assertEqual(self.view()["register"]["state"], "not-a-submitter")
		self.assertEqual(self.view(PETER)["register"]["state"], "not-a-submitter")  # a supplier who did not bid
		self.assertEqual(self.view(OUTSIDER)["register"]["state"], "not-a-submitter")
		self.assertEqual(self.view(DAVID)["register"]["state"], "can-request")
		register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=DAVID)
		ready = self.view(DAVID)["register"]
		self.assertEqual(ready["state"], "ready")
		self.assertEqual(ready["message"], "Your copy of the opening register is ready. It lists the one bid opened, as read aloud.")
		self.assertEqual(self.view(DAVID)["status"], "Opening complete")

	def test_p4_a_request_waits_while_the_accounting_officer_provides_it(self):
		settings = frappe.get_doc("Bid Opening Settings")
		settings.register_self_service = 0
		settings.flags.kt_bop_command = True
		settings.save(ignore_permissions=True)
		self.addCleanup(lambda: frappe.db.set_single_value("Bid Opening Settings", "register_self_service", None))
		self.completed()
		register_copy.request_opening_register(tender=self.name, idempotency_key=key(), user=DAVID)
		preparing = self.view(DAVID)["register"]
		self.assertEqual(preparing["state"], "preparing")
		self.assertTrue(preparing["message"].endswith("We will notify you when it is ready to download."))

	def test_before_start_the_page_never_implies_a_count(self):
		self.prepared()
		self.at(self.minutes_before(3))
		empty = self.view(MEMBER)
		for key_ in ("readout", "repeats"):
			self.assertEqual(empty[key_], [])
		self.assertEqual(empty["register"]["state"], "after-completion")
