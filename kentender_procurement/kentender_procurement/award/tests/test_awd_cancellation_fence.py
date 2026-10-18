# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The cancellation side of the shared Tender fence (AWD-CHG-001 v0.9 §5.11
"One current fence", §7.2; TPR-CHG-001 v0.24 §5.12, §7.6; AWD-OF-AC-004,
AC-005).

`cancellation_fence` is the structured answer Tenders asks before it cancels:
allowed only while the Tender-level notification status is Not issued, with every
blocker naming its reason, holder and route. The cancellation stamps its
reference on the Tender's record in its own transaction. Every Award command
takes the record's lock before the case's, so nothing can invert the order
Tender → record → case against a cancellation."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F  # noqa: F401
from kentender_procurement.award.test_services.timeline import W  # noqa: F401
import frappe

from kentender_procurement.award.services import authority, records, tender_authority
from kentender_procurement.award.tests.support import CASE, NS, AwardCase
from kentender_procurement.tests.two_connections import WAIT, Conn

TENDER = "TND-AWT-2100-901"


def _in_world():
	frappe.flags.kt_awd_fixture_namespace = NS
	frappe.flags.kt_awd_clock = W("2027-06-17 09:00:00")


def _register():
	frappe.flags.kt_awd_fixture_namespace = NS
	return tender_authority.register(tender=TENDER, tender_reference="TND-AWT-2100-901", source_event="publication:fence")


class TestFenceAnswer(AwardCase):
	def test_allowed_only_while_not_issued(self):
		_register()
		fence = authority.cancellation_fence(tender=TENDER)
		self.assertEqual((fence["allowed"], fence["blockers"]), (True, []))
		self.assertEqual(fence["status"]["notification_status"], "Not issued")

	def test_each_blocker_names_a_reason_a_holder_and_a_route(self):
		_register()
		cases = (("Issue in progress", "issue_in_progress"), ("Unknown", "status_unknown"), ("Issued", "issued"))
		for status, reason in cases:
			frappe.db.set_value(tender_authority.DOCTYPE, TENDER, "notification_status", status)
			fence = authority.cancellation_fence(tender=TENDER)
			self.assertFalse(fence["allowed"], status)
			blocker = fence["blockers"][0]
			self.assertEqual(blocker["reason"], reason, status)
			self.assertTrue(blocker["message"] and blocker["holder"] and blocker["route"] is not None, blocker)

	def test_a_tender_with_no_record_is_blocked_as_unknown_not_allowed(self):
		fence = authority.cancellation_fence(tender="SYN-NO-SUCH-TENDER-2")
		self.assertFalse(fence["allowed"])
		self.assertEqual([b["reason"] for b in fence["blockers"]], ["no_authority_record"])
		self.assertEqual(fence["blockers"][0]["holder"], "Award service owner")

	def test_a_tampered_or_disagreeing_record_is_blocked_as_unknown(self):
		self.deliver()
		doc = self.case()
		frappe.db.set_value("Award Case", doc.name, "notification_status", "Issued")
		fence = authority.cancellation_fence(tender=doc.tender)
		self.assertEqual([b["reason"] for b in fence["blockers"]], ["status_unknown"])

	def test_a_case_names_itself_in_the_route(self):
		self.deliver()
		fence_route = authority.cancellation_fence(tender=self.case().tender)
		self.assertTrue(fence_route["allowed"])
		frappe.db.set_value("Award Case", CASE, "notification_status", "Issued")
		frappe.db.set_value(tender_authority.DOCTYPE, self.case().tender, "notification_status", "Issued")
		blocked = authority.cancellation_fence(tender=self.case().tender)
		self.assertEqual(blocked["blockers"][0]["route"], {"area": "Award", "case": CASE})

	def test_the_guard_is_the_first_blocker_message(self):
		_register()
		frappe.db.set_value(tender_authority.DOCTYPE, TENDER, "notification_status", "Issued")
		self.assertEqual(authority.cancellation_guard(tender=TENDER), authority.cancellation_fence(tender=TENDER)["blockers"][0]["message"])


class TestCancellationStamp(AwardCase):
	def test_the_stamp_is_idempotent_and_conflicts_with_another_reference(self):
		_register()
		first = tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-A", cancelled_at=W("2027-06-17 09:00:00"))
		self.assertTrue(first["changed"])
		self.assertFalse(tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-A")["changed"])
		with self.assertRaises(Exception):
			tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-B")
		self.assertEqual(frappe.db.get_value(tender_authority.DOCTYPE, TENDER, "cancellation_ref"), "TCN-A")

	def test_a_stamped_record_still_reads_not_issued_and_a_repeat_cancellation_is_not_blocked(self):
		_register()
		tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-A")
		self.assertEqual(authority.status(tender=TENDER)["notification_status"], "Not issued")
		self.assertEqual(authority.status(tender=TENDER)["cancellation_ref"], "TCN-A")
		self.assertTrue(authority.cancellation_fence(tender=TENDER)["allowed"])

	def test_a_notice_status_change_cannot_pass_an_open_cancellation_transaction(self):
		"""Both orderings under real concurrency, cancellation holding the fence: the status change waits, then sees the committed stamp."""
		_register()
		frappe.db.commit()
		cancel = Conn("Administrator", lambda: tender_authority.record_cancellation(TENDER, cancellation_ref="TCN-HOLD"), hold=True, setup=_in_world)
		self.assertTrue(cancel.ran.wait(WAIT))
		self.assertIsNone(cancel.error, cancel.error)
		issuing = Conn("Administrator", lambda: authority.cancellation_fence(tender=TENDER), setup=_in_world)
		self.assertFalse(issuing.finished.wait(1.5), "a reader of the fence must wait for the cancellation that holds it")
		cancel.commit()
		self.assertTrue(issuing.finished.wait(WAIT))
		self.assertIsNone(issuing.error, issuing.error)
		self.assertEqual(issuing.value["status"]["cancellation_ref"], "TCN-HOLD")


class TestLockOrder(AwardCase):
	def test_an_award_command_takes_the_record_lock_before_the_case_lock(self):
		"""Tender → record → case on every Award command: while a connection holds the Tender's record, an Award command on its case waits."""
		self.deliver()
		tender = self.case().tender
		frappe.db.commit()
		holder = Conn("Administrator", lambda: tender_authority.lock(tender), hold=True, setup=_in_world)
		self.assertTrue(holder.ran.wait(WAIT))
		command = Conn("Administrator", lambda: records.command("NoOp", case=CASE, idempotency_key="awd-fence-noop-1", actor="system", payload={}, body=lambda: {"ok": True}),
			setup=_in_world)
		self.assertFalse(command.finished.wait(1.5), "an Award command must wait for the Tender's record before it locks the case")
		holder.commit()
		self.assertTrue(command.finished.wait(WAIT))
		self.assertIsNone(command.error, command.error)
		frappe.db.delete(records.JOURNAL, {"idempotency_key": "awd-fence-noop-1"})
		frappe.db.commit()
