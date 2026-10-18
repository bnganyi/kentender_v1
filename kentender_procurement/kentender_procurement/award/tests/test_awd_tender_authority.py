# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The durable Tender-level Award authority record (AWD-CHG-001 v0.9 §5.11, §7
GetAwardAuthorityStatus, §7.2; AWD-OF-AC-004).

Before an Award case exists, the only proof that no notice was issued is a
durable Tender-level record registered by Award's Tender-publication
integration. A missing, unreadable, tampered or disagreeing record answers
Unknown — never a negative synthesised from "no case found"."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F  # noqa: F401
from kentender_procurement.award.test_services.timeline import W  # noqa: F401
import frappe

from kentender_procurement.award.services import authority, tender_authority
from kentender_procurement.award.tests.support import NS, AwardCase

TENDER = "TND-AWT-2100-900"
RECORD = tender_authority.DOCTYPE


def _register(tender: str = TENDER, **kwargs):
	frappe.flags.kt_awd_fixture_namespace = NS
	return tender_authority.register(tender=tender, tender_reference=kwargs.pop("tender_reference", "TND-AWT-2100-900"), source_event=kwargs.pop("source_event", f"publication:{tender}"), **kwargs)


class TestTenderAuthorityRecord(AwardCase):
	def test_registering_creates_one_not_issued_record_and_replay_never_resets_it(self):
		first = _register()
		self.assertEqual((first["notification_status"], first["created"]), ("Not issued", True))
		row = frappe.get_doc(RECORD, TENDER)
		self.assertEqual((row.source_kind, row.award_case or "", int(row.record_version)), ("Publication", "", 1))
		# a later notice is recorded, then the publication is replayed: nothing is reset
		tender_authority.set_notification(TENDER, "Issue in progress", token="tok-1")
		tender_authority.set_notification(TENDER, "Issued", token="tok-1")
		again = _register()
		self.assertEqual((again["created"], again["notification_status"]), (False, "Issued"))
		self.assertEqual(frappe.db.count(RECORD, {"tender": TENDER}), 1)

	def test_a_recorded_cancellation_is_not_reset_by_a_replayed_publication(self):
		_register()
		tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-1")
		again = _register()
		self.assertEqual(again["cancellation_ref"], "TCN-1")

	def test_no_record_means_unknown_not_not_issued(self):
		s = authority.status(tender="SYN-NO-SUCH-TENDER")
		self.assertEqual((s["decision_status"], s["notification_status"]), ("Unknown", "Unknown"))
		self.assertEqual(s["source"], "No Tender authority record")
		self.assertIn("could not be confirmed", authority.cancellation_guard(tender="SYN-NO-SUCH-TENDER"))
		self.assertEqual(authority.tender_status(tender="SYN-NO-SUCH-TENDER")["status"], "Unknown")
		self.assertFalse(authority.downstream_disposition(tender="SYN-NO-SUCH-TENDER")["known"])

	def test_a_registered_tender_without_a_case_answers_not_issued_from_the_record(self):
		_register()
		s = authority.status(tender=TENDER)
		self.assertEqual((s["decision_status"], s["notification_status"]), ("No decision recorded", "Not issued"))
		self.assertEqual(s["source"], f"Award Tender Authority {TENDER}")
		self.assertEqual(s["source_revision"], 1)
		self.assertTrue(s["evidence"]["source_event"])
		self.assertIsNotNone(s["checked_at"])
		self.assertEqual(authority.cancellation_guard(tender=TENDER), "")
		self.assertEqual(authority.tender_status(tender=TENDER)["status"], "No award decision recorded")
		disposition = authority.downstream_disposition(tender=TENDER)
		self.assertEqual((disposition["known"], disposition["notification_status"], disposition["case"]), (True, "Not issued", ""))
		self.assertFalse(frappe.db.exists("Award Case", {"tender": TENDER}))

	def test_the_expected_revision_must_match_or_the_answer_is_unknown(self):
		_register()
		self.assertEqual(authority.status(tender=TENDER, expected_revision=1)["notification_status"], "Not issued")
		self.assertEqual(authority.status(tender=TENDER, expected_revision=7)["notification_status"], "Unknown")

	def test_a_tampered_record_answers_unknown(self):
		_register()
		frappe.db.set_value(RECORD, TENDER, "source_event", "tampered")
		self.assertEqual(authority.status(tender=TENDER)["notification_status"], "Unknown")
		self.assertIn("could not be confirmed", authority.cancellation_guard(tender=TENDER))

	def test_a_case_that_disagrees_with_its_record_answers_unknown(self):
		self.deliver()
		doc = self.case()
		self.assertEqual(authority.status(tender=doc.tender)["notification_status"], "Not issued")
		frappe.db.set_value("Award Case", doc.name, "notification_status", "Issued")
		s = authority.status(tender=doc.tender)
		self.assertEqual(s["notification_status"], "Unknown")
		self.assertIn("could not be confirmed", authority.cancellation_guard(tender=doc.tender))

	def test_a_case_gets_a_record_derived_from_it_and_the_record_follows_the_case(self):
		self.deliver()
		doc = self.case()
		row = frappe.get_doc(RECORD, doc.tender)
		self.assertEqual((row.source_kind, row.award_case, row.notification_status), ("Derived from case", doc.name, "Not issued"))
		self.awarded()
		self.assertEqual(frappe.db.get_value(RECORD, doc.tender, "notification_status"), "Issued")
		self.assertEqual(authority.status(tender=doc.tender)["notification_status"], "Issued")

	def test_an_existing_publication_record_is_linked_to_its_case_not_replaced(self):
		reference = self.reference
		tender = f"SYN-{reference}"  # the synthetic Evaluation world names its Tender this way
		_register(tender, tender_reference=reference, source_event="publication:early")
		self.deliver()
		row = frappe.get_doc(RECORD, tender)
		self.assertEqual((row.source_kind, row.award_case, row.source_event), ("Publication", self.case().name, "publication:early"))

	def test_issued_never_returns_to_not_issued(self):
		_register()
		tender_authority.set_notification(TENDER, "Issue in progress", token="a")
		tender_authority.set_notification(TENDER, "Issued", token="a")
		with self.assertRaises(Exception):
			tender_authority.set_notification(TENDER, "Not issued", token="a")
		# a second batch cannot move the Tender-level fact backwards
		tender_authority.set_notification(TENDER, "Issue in progress", token="b")
		self.assertEqual(frappe.db.get_value(RECORD, TENDER, "notification_status"), "Issued")

	def test_unknown_returns_to_not_issued_only_with_evidence_that_nothing_was_sent(self):
		_register()
		tender_authority.set_notification(TENDER, "Issue in progress", token="a")
		tender_authority.set_notification(TENDER, "Unknown", token="a")
		with self.assertRaises(Exception):
			tender_authority.set_notification(TENDER, "Not issued", token="a")
		tender_authority.set_notification(TENDER, "Not issued", token="a", no_send_evidence="Mail service log shows no message left the server for batch 1.")
		self.assertEqual(frappe.db.get_value(RECORD, TENDER, "notification_status"), "Not issued")

	def test_the_repair_sweep_registers_only_what_the_lifecycle_proves(self):
		facts = [
			{"tender": "TND-R-OPEN", "tender_reference": "R-OPEN", "overall_status": "Published — open", "published": True, "cancelled": False},
			{"tender": "TND-R-CANCELLED", "tender_reference": "R-CANCELLED", "overall_status": "Cancelled", "published": True, "cancelled": True},
			{"tender": "TND-R-ENDED", "tender_reference": "R-ENDED", "overall_status": "Submission period ended", "published": True, "cancelled": False},
		]
		frappe.flags.kt_awd_fixture_namespace = NS
		result = tender_authority.backfill(facts)
		self.assertEqual(result, {"registered": 2, "left_unknown": 1})
		self.assertEqual(frappe.db.get_value(RECORD, "TND-R-OPEN", "source_kind"), "Backfill")
		self.assertTrue(frappe.db.exists(RECORD, "TND-R-CANCELLED"))
		self.assertFalse(frappe.db.exists(RECORD, "TND-R-ENDED"))
		self.assertEqual(authority.status(tender="TND-R-ENDED")["notification_status"], "Unknown")
		self.assertEqual(tender_authority.backfill(facts), {"registered": 0, "left_unknown": 1})
