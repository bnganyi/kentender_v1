# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-17 / AUD-XC-130 / AUD-XC-131 — Bid Submission references are allocated from
the latest committed rows, and the command journal is claimed by the actor.

At the submission deadline many bidders commit within the same second. A number
read as `count() + 1` from a transaction's older REPEATABLE READ snapshot repeats
the number another bidder has just committed; the second bidder then fails on a
unique reference, for a receipt after the deposit has been accepted. These tests
open the snapshot first, commit the competing row from a second connection, and
then ask for the next reference."""

from __future__ import annotations

import threading
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import errors, records, references
from kentender_procurement.tests.two_connections import WAIT as _WAIT
from kentender_procurement.tests.two_connections import commit_on_other_connection, raw_row


class TestReferencesAreAllocatedFromCommittedRows(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.tender = f"RG17-TND-{uuid4().hex[:8]}"
		self.reference = "TND-MOH-2100-901"
		self.addCleanup(self.purge)
		frappe.db.commit()

	def purge(self):
		frappe.db.rollback()
		for doctype in ("Bid Submission Attempt", "Bid Receipt", "Bidder Arrangement"):
			frappe.db.delete(doctype, {"tender": self.tender})
		frappe.db.delete("Bid Command Journal", {"idempotency_key": ("like", "rg17-%")})
		frappe.db.commit()

	def _competitor(self, doctype: str, **values) -> None:
		"""The competing bidder's row, committed from another connection after this snapshot was opened."""
		frappe.db.sql("select count(*) from `tabBid Submission Attempt`")  # this transaction's snapshot opens here
		commit_on_other_connection(lambda: raw_row(doctype, tender=self.tender, **values))

	def test_a_correlation_id_follows_an_attempt_another_bidder_just_committed(self):
		self._competitor("Bid Submission Attempt", correlation_id="COR-BDS-2100-901-01")
		self.assertEqual(references.correlation_id(self.tender, self.reference), "COR-BDS-2100-901-02")

	def test_a_support_reference_follows_one_another_bidder_just_committed(self):
		self._competitor("Bid Submission Attempt", support_reference="SUP-BDS-2100-901-01")
		self.assertEqual(references.support_reference(self.tender, self.reference), "SUP-BDS-2100-901-02")

	def test_a_receipt_reference_follows_a_receipt_another_bidder_just_committed(self):
		self._competitor("Bid Receipt", receipt_reference="RCPT-MOH-2100-901-001")
		self.assertEqual(references.receipt_reference(self.tender, self.reference), "RCPT-MOH-2100-901-002")

	def test_an_arrangement_number_follows_one_another_bidder_just_committed(self):
		self._competitor("Bidder Arrangement", bidder_arrangement_id="ARR-MOH-2100-901-001")
		self.assertEqual(references.next_number(self.tender), 2)


class TestTheJournalBelongsToTheActor(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.addCleanup(lambda: (frappe.db.delete("Bid Command Journal", {"idempotency_key": ("like", "rg17-%")}), frappe.db.commit()))

	def test_a_key_run_by_one_user_is_a_conflict_for_another_and_a_replay_for_the_same_user(self):
		key, runs = f"rg17-{uuid4().hex[:8]}", []

		def effect():
			runs.append(1)
			return {"ok": True, "n": len(runs)}

		first = records.idempotent(key, "SaveBidTask", {"x": 1}, effect, actor="Administrator")
		self.assertEqual(first, {"ok": True, "n": 1})
		with self.assertRaises(errors.BidSubmissionError) as ctx:
			records.idempotent(key, "SaveBidTask", {"x": 1}, effect, actor="Guest")
		self.assertEqual(ctx.exception.code, "BDS_IDEMPOTENCY_CONFLICT")
		self.assertEqual(records.idempotent(key, "SaveBidTask", {"x": 1}, effect, actor="Administrator"), {"ok": True, "n": 1})
		self.assertEqual(len(runs), 1)

	def test_two_connections_with_one_key_run_the_command_once(self):
		key, runs = f"rg17-{uuid4().hex[:8]}", []
		release, entered = threading.Event(), threading.Event()
		site, sites_path = frappe.local.site, frappe.local.sites_path
		outcomes: list[dict] = []

		def effect():
			runs.append(1)
			entered.set()
			release.wait(_WAIT)
			return {"ok": True, "n": len(runs)}

		def first_bidder():
			frappe.init(site=site, sites_path=sites_path)
			frappe.connect()
			frappe.set_user("Administrator")
			outcomes.append(records.idempotent(key, "SaveBidTask", {"x": 2}, effect, actor="Administrator"))
			frappe.db.commit()
			frappe.db.close()

		thread = threading.Thread(target=first_bidder, daemon=True)
		thread.start()
		self.assertTrue(entered.wait(_WAIT))
		timer = threading.Timer(1.5, release.set)  # the first request finishes while the second waits on its claim
		timer.start()
		second = records.idempotent(key, "SaveBidTask", {"x": 2}, effect, actor="Administrator")
		thread.join(_WAIT)
		timer.cancel()
		self.assertEqual(len(runs), 1)
		self.assertEqual(second, {"ok": True, "n": 1})
		self.assertEqual(outcomes, [{"ok": True, "n": 1}])
