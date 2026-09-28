# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §4.4.4, §5.12–5.13, §10.3 and §10.7 (plan Phase 13;
TPR-CHG-001 v0.13 approved by the Project Owner, 28 Sep 2026): the template
release a published Tender is bound to. Switched Off or Superseded, every bid
action continues on the same definition. Withdrawn, or failing its checks,
it takes no new Start, Draft change, submission or replacement, while the
Draft, receipts and public reads stay readable and a current Submitted bid
may still be withdrawn before the deadline. Nothing rebinds; the Tender's
Procurement Officer holds the resolution."""

from __future__ import annotations

from unittest import mock

import frappe
from frappe.utils import get_datetime

from kentender_core.services import next_step as ns

from kentender_procurement.bid_submission.services import bid_context, evidence, guidance, overview, reads, receipt_view, save, simulation, start_bid, tenders_gateway
from kentender_procurement.bid_submission.services.overview import SUPERSEDED_TEXT, WITHDRAWN_RELEASE_TEXT
from kentender_procurement.bid_submission.tests.support import DAVID, KISIWA, MARY, PETER, key, pdf
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase
from kentender_procurement.bid_submission.tests.test_submission import SUBMIT_AT

GATEWAY = "kentender_procurement.bid_submission.services.tenders_gateway"


class ReleaseCase(ChangeCase):
	def release(self, state: str) -> None:
		simulation.set_controls(bound_release_state=state)

	def binding(self) -> tuple:
		return tuple(frappe.db.get_value("Bid Workspace", self.bid, ["bid_definition_id", "definition_version", "definition_digest"]))

	def officer(self) -> str:
		return frappe.db.get_value("User", tenders_gateway.resolution_holder(self.name), "full_name")

	def start_peter(self):
		return start_bid.start_bid(tender_reference=self.reference, organisation=KISIWA, arrangement=self.single(), notice_contact_id=f"{KISIWA}-C1", idempotency_key=key(), user=PETER)

	def save_offer(self, value="ApexBook Pro 14 G2"):
		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		return save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: value}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)

	def upload(self):
		handle = next(f["handle"] for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["kind"] == "evidence")
		return evidence.upload_bid_evidence(bid_reference=self.bid, handle=handle, filename="datasheet.pdf", content=pdf(), expected_record_version=self.version(), idempotency_key=key(), user=DAVID)

	def guard_blocker(self, user=MARY):
		ctx = bid_context.load(self.bid, actor=user, at=get_datetime(SUBMIT_AT))
		guard = guidance.submit_guard(ctx, actor=user, at=get_datetime(SUBMIT_AT))
		return next((b for b in ns.blockers_of(guard) if b["reason_code"] == "BDS_DEFINITION_UNSUPPORTED"), None)


class TestPermittedReleases(ReleaseCase):
	def test_a_superseded_release_keeps_every_action_on_the_same_definition(self):
		bound = self.binding()
		self.release("Superseded")
		self.assertTrue(self.save_offer()["ok"])
		self.assertTrue(self.start_peter()["created"])
		guest = overview.get_tender_overview(tender_reference=self.reference, user="Guest")
		self.assertEqual((guest["release_notice"], guest["action"]["kind"]), ({"tone": "info", "text": SUPERSEDED_TEXT}, "sign_in"))
		self.assertIsNone(self.guard_blocker())
		receipt = self.submitted()
		self.assertTrue(receipt)
		self.at("2027-05-31 08:30:00")
		self.assertTrue(self.replace()["ok"])
		self.assertEqual(self.binding(), bound)  # never rebound to a successor

	def test_a_release_switched_off_keeps_draft_changes_and_submission(self):
		off = {"lifecycle": "Available", "site_switch": "Off", "integrity_ok": True, "renderer_ok": True}
		with mock.patch(f"{GATEWAY}.release_status", return_value=off):
			self.assertTrue(self.save_offer()["ok"])
			self.assertTrue(self.submitted())
			self.assertIsNone(overview.get_tender_overview(tender_reference=self.reference, user=PETER)["release_notice"])


class TestWithdrawnRelease(ReleaseCase):
	def test_the_draft_stays_readable_and_takes_no_new_work(self):
		bound = self.binding()
		arrangements = frappe.db.count("Bidder Arrangement", {"tender": self.name})
		mine = lambda: next(r for r in reads.get_my_bids(user=DAVID)["rows"] if r["bid_reference"] == self.bid)  # noqa: E731
		self.assertEqual([a["label"] for a in mine()["actions"]], ["Review bid"])  # the same list, before
		self.release("Withdrawn")
		self.assertEqual(self.code(self.start_peter), "BDS_DEFINITION_UNSUPPORTED")
		self.assertEqual(frappe.db.count("Bidder Arrangement", {"tender": self.name}), arrangements)
		for command in (self.save_offer, self.upload, self.prepare):
			with self.subTest(command=command.__name__):
				self.assertEqual(self.code(command), "BDS_DEFINITION_UNSUPPORTED")
		# BDS-DES-06-WITHDRAWN-RELEASE: waiting on the Tender's Procurement Officer
		view = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)
		officer = self.officer()
		self.assertTrue(officer)
		self.assertEqual(
			(view["next_step"]["kind"], view["next_step"]["headline"]),
			("waiting", f"Procurement Officer {officer} holds the governed Tender resolution; this Draft is saved but cannot be submitted against the withdrawn format."),
		)
		holder = ns.holder(guidance.PROCUREMENT_OFFICER, [officer])["display"]
		self.assertEqual([(s["marker"], s["holder"]) for s in view["journey"]["stages"]], [(ns.MARKER_BLOCKED, holder), (ns.MARKER_NOT_STARTED, ""), (ns.MARKER_NOT_STARTED, "")])
		self.assertEqual((view["header"]["action"], view["availability_notice"]), (None, None))
		self.assertEqual([link["label"] for link in view["guidance_links"]], ["View current Tender", "Supplier support"])
		self.assertEqual(view["guidance_links"][0]["href"], f"/tenders/{self.reference}")
		self.assertEqual({t["action"]["label"] for t in view["tasks"]}, {"View"})
		task = reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)
		self.assertFalse(task["bid"]["editable"])
		self.assertFalse(any(f["editable"] for g in task["groups"] for f in g["fields"]))
		blocker = self.guard_blocker()
		self.assertEqual((blocker["figures"]["release"], blocker["fixes"][0]["person"]), ("Withdrawn", officer))
		# BDS-DES-02-WITHDRAWN-RELEASE: the Tender stays readable; no Start
		david = overview.get_tender_overview(tender_reference=self.reference, user=DAVID)
		self.assertEqual((david["release_notice"], [a["kind"] for a in david["actions"]]), ({"tone": "warning", "text": WITHDRAWN_RELEASE_TEXT}, ["view_documents", "view_bid"]))
		peter = overview.get_tender_overview(tender_reference=self.reference, user=PETER)
		self.assertEqual(([a["kind"] for a in peter["actions"]], peter["start"]), (["view_documents"], None))
		self.assertTrue(peter["documents"])
		self.assertEqual([a["label"] for a in mine()["actions"]], ["View bid"])
		self.assertEqual(self.binding(), bound)

	def test_a_submitted_bid_may_be_withdrawn_but_not_replaced(self):
		receipt = self.submitted()
		self.release("Withdrawn")
		page = receipt_view.get_receipt_page(tender_reference=self.reference, receipt_reference=receipt, user=MARY)
		self.assertEqual([a["key"] for a in page["actions"]], ["withdraw_bid", "print"])
		mary = overview.get_tender_overview(tender_reference=self.reference, user=MARY)
		self.assertEqual([(a["kind"], a["tone"]) for a in mary["actions"]], [("view_documents", "secondary"), ("view_receipt", "secondary"), ("withdraw_bid", "danger")])
		self.assertEqual(mary["actions"][2]["href"], f"/tenders/{self.reference}/bid/receipt/{receipt}?action=withdraw")
		david = overview.get_tender_overview(tender_reference=self.reference, user=DAVID)
		self.assertEqual([a["kind"] for a in david["actions"]], ["view_documents", "view_receipt"])
		step = reads.get_bid_workspace(bid_reference=self.bid, user=MARY)["next_step"]
		self.assertEqual([f["fix_id"] for f in step["fixes"]], ["withdraw_bid"])
		self.assertTrue(step["headline"].startswith("You may withdraw before "))
		self.at("2027-05-31 08:30:00")
		self.assertEqual(self.code(self.replace), "BDS_DEFINITION_UNSUPPORTED")
		self.assertTrue(self.withdraw(receipt=receipt)["ok"])
		row = next(r for r in reads.get_my_bids(user=MARY)["rows"] if r["bid_reference"] == self.bid)
		self.assertNotIn("Start replacement", [a["label"] for a in row["actions"]])

	def test_a_release_that_fails_its_checks_stops_new_work_the_same_way(self):
		self.release("Integrity failed")
		self.assertEqual(self.code(self.save_offer), "BDS_DEFINITION_UNSUPPORTED")
		step = reads.get_bid_workspace(bid_reference=self.bid, user=DAVID)["next_step"]
		self.assertTrue(step["headline"].endswith("this Draft is saved but cannot be submitted while the Tender format fails its checks."), step["headline"])
		self.assertEqual(self.guard_blocker()["figures"]["release"], "Failed verification")


class TestTamperedDefinition(ReleaseCase):
	def test_a_definition_whose_digest_fails_stops_reads_and_signing(self):
		bound = tenders_gateway.definition_for(self.name, frappe.db.get_value("Bid Workspace", self.bid, "definition_version"))
		tampered = dict(bound, definition=dict(bound["definition"], submission_deadline="2099-01-01T00:00:00+03:00"))
		with mock.patch(f"{GATEWAY}.definition_for", return_value=tampered):
			self.assertEqual(self.code(reads.get_bid_workspace, bid_reference=self.bid, user=DAVID), "BDS_DEFINITION_UNSUPPORTED")
			self.assertEqual(self.code(self.prepare), "BDS_DEFINITION_UNSUPPORTED")
