# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Tenders) — a command's idempotency key is answered
only after the caller is authorised and only to the actor, command and payload
that recorded it; two requests with one key run once and both get the Tender's
identity (TPR09-AC-007); a stale version is the typed `TND_STALE_VERSION` under
real concurrency (TPR09-AC-025); and the reference generator takes the next free
number even when its snapshot predates the request that just committed one.
The races use `kentender_procurement.tests.two_connections`."""

from __future__ import annotations

import frappe

from kentender_procurement.tenders.services import draft_commands as cmd, envelope, lifecycle, references
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx, sample
from kentender_procurement.tenders.tests.test_lifecycle import TenderLifecycleCase
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn

JOURNAL = "Tender Command Journal"


class TestTenderIdempotencyEnvelope(TenderLifecycleCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(fx.wipe_all)

	def _values(self, **overrides):
		values = sample.officer_values(inspection_location=fx.LOCATION, contact_office=fx.CONTACT_OFFICE)
		values.update(overrides)
		return values

	def _save(self, tender, version, *, key, user=fx.OFFICER, **overrides):
		return cmd.save_tender_draft(tender=tender, values=self._values(**overrides), expected_record_version=version, idempotency_key=key, user=user)

	def _commit(self):
		"""Make the fixtures visible to another connection, and let go of the named reference locks this
		connection took while building them: they belong to the session, which a test keeps open for far
		longer than a request does."""
		frappe.db.commit()
		frappe.db.sql("select release_all_locks()")

	def _draft(self) -> tuple[str, int]:
		_, started = self._started()
		root = frappe.get_doc("Tender", started["tender"])
		return root.name, root.record_version

	# ----- authorise first, then answer ------------------------------------------

	def test_a_caller_without_the_responsibility_gets_no_replay(self):
		tender, version = self._draft()
		key = fx.key()
		first = self._save(tender, version, key=key)
		self.assertTrue(first["ok"])
		for user in (fx.HOPF, fx.NOBODY, fx.AUDITOR):
			with self.assertRaises((TendersError, frappe.DoesNotExistError), msg=user):  # refused (or masked as not found), never the recorded result
				self._save(tender, version, key=key, user=user)
		replay = self._save(tender, version, key=key)  # the officer who acted still gets the original
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["record_version"], first["record_version"])

	# ----- the key is bound to the command and the payload ------------------------

	def test_the_same_key_with_another_payload_is_a_typed_conflict(self):
		tender, version = self._draft()
		key = fx.key()
		self._save(tender, version, key=key)
		with self.assertRaises(TendersError) as caught:
			self._save(tender, version, key=key, tender_validity_days=150)
		self.assertEqual(caught.exception.code, "TND_IDEMPOTENCY_CONFLICT")

	def test_the_same_key_for_another_command_is_a_typed_conflict(self):
		tender, version = self._draft()
		key = fx.key()
		saved = self._save(tender, version, key=key)
		with self.assertRaises(TendersError) as caught:
			lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=saved["record_version"], idempotency_key=key, user=fx.OFFICER)
		self.assertEqual(caught.exception.code, "TND_IDEMPOTENCY_CONFLICT")

	def test_a_refusal_returned_as_data_leaves_the_key_free_for_the_corrected_attempt(self):
		tender, version = self._draft()
		key = fx.key()
		refused = self._save(tender, version, key=key, tender_validity_days=0)
		self.assertFalse(refused["ok"])
		self.assertEqual(frappe.db.count(JOURNAL, {"idempotency_key": key}), 0)
		self.assertTrue(self._save(tender, version, key=key)["ok"])

	# ----- real concurrency ---------------------------------------------------------

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		tender, version = self._draft()
		self._commit()
		key = fx.key()
		conn_a = Conn(fx.OFFICER, lambda: self._save(tender, version, key=key), hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(fx.OFFICER, lambda: self._save(tender, version, key=key))
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value["record_version"], conn_a.value["record_version"])
		self.assertTrue(conn_b.value["idempotent"])
		frappe.db.commit()
		self.assertEqual(frappe.db.count(JOURNAL, {"idempotency_key": key}), 1)
		self.assertEqual(frappe.db.get_value("Tender", tender, "record_version"), conn_a.value["record_version"])  # one execution, not two

	def test_two_starts_for_one_handoff_with_one_key_make_one_tender_and_both_return_it(self):
		authorised = fx.authorised_handoff()
		self._commit()
		key = fx.key()
		start = lambda: cmd.start_tender(handoff=authorised["handoff"], idempotency_key=key, user=fx.OFFICER)  # noqa: E731
		conn_a = Conn(fx.OFFICER, start, hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(fx.OFFICER, start)
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first start")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual((conn_b.value["tender"], conn_b.value["tender_version"]), (conn_a.value["tender"], conn_a.value["tender_version"]))
		frappe.db.commit()
		self.assertEqual(len(fx.test_tenders()), 1)

	def test_a_stale_version_is_the_typed_refusal_not_a_save_timestamp_error(self):
		tender, version = self._draft()
		self._commit()
		conn_b = Conn(fx.OFFICER, lambda: self._save(tender, version, key=fx.key(), tender_validity_days=150), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(fx.OFFICER, lambda: self._save(tender, version, key=fx.key()))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, TendersError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "TND_STALE_VERSION")

	def test_the_reference_generator_takes_the_next_free_number_after_a_competing_commit(self):
		plan_item = f"PPI-MOH-2102-{fx.key()[:6].upper()}"
		mint = lambda: references.tender_reference(fiscal_year="2027-2028", plan_item_id_value=plan_item)  # noqa: E731
		conn_b = Conn("Administrator", mint, snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))

		def competing():
			reference = mint()
			envelope.insert(frappe.get_doc({"doctype": "Tender", "tender_reference": reference, "overall_status": "Draft", "record_version": 0, "fixture_namespace": fx.NS}))
			return reference

		conn_a = Conn("Administrator", competing)
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value, f"{conn_a.value}-002")
