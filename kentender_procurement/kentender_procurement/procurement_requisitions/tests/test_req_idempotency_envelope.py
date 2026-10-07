# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-131 / AUD-XC-130 (Requisitions) — a command's idempotency key is
answered only after the caller is authorised and only to the actor, command and
payload that recorded it; two requests with one key run once; a stale version
is the typed `REQ_STALE_VERSION` under real concurrency; and the reference
generator takes the next free number even when its snapshot predates the
request that just committed one (REQ-CHG-001 section 10; NDS/PLN `*_IDEMPOTENCY_CONFLICT`
pattern). The races use `kentender_procurement.tests.two_connections`."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd, references
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn

JOURNAL = "Requisition Command Journal"


class TestRequisitionIdempotencyEnvelope(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		self.addCleanup(self._purge)

	def _purge(self):
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()

	def _draft(self) -> tuple[str, int]:
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		frappe.set_user("Administrator")
		return requisition, fx.editor(requisition)["header"]["version_record_version"]

	def _save(self, requisition, version, *, key, user=fx.AUTHOR, latest="2102-04-30"):
		return cmd.save_requisition_summary(requisition=requisition, values={"latest_delivery_date": latest}, expected_record_version=version, idempotency_key=key, user=user)

	# ----- authorise first, then answer ------------------------------------------

	def test_a_caller_without_the_responsibility_gets_no_replay(self):
		requisition, version = self._draft()
		key = fx.key()
		first = self._save(requisition, version, key=key)
		self.assertTrue(first["ok"])
		with self.assertRaises(frappe.DoesNotExistError):  # masked: the requisition is not theirs to see
			self._save(requisition, version, key=key, user=fx.OUTSIDER)
		replay = self._save(requisition, version, key=key)  # the owner still gets the original
		self.assertTrue(replay["idempotent"])
		self.assertEqual(replay["record_version"], first["record_version"])

	# ----- the key is bound to the command and the payload ------------------------

	def test_the_same_key_with_another_payload_is_a_typed_conflict(self):
		requisition, version = self._draft()
		key = fx.key()
		self._save(requisition, version, key=key)
		with self.assertRaises(ProcurementRequisitionsError) as caught:
			self._save(requisition, version, key=key, latest="2102-05-31")
		self.assertEqual(caught.exception.code, "REQ_IDEMPOTENCY_CONFLICT")

	def test_the_same_key_for_another_command_is_a_typed_conflict(self):
		requisition, version = self._draft()
		key = fx.key()
		self._save(requisition, version, key=key)
		view = fx.editor(requisition)
		with self.assertRaises(ProcurementRequisitionsError) as caught:
			cmd.reset_standard_values(requisition=requisition, expected_record_version=view["package_record_version"], idempotency_key=key, user=fx.AUTHOR)
		self.assertEqual(caught.exception.code, "REQ_IDEMPOTENCY_CONFLICT")

	def test_a_failed_command_leaves_no_claim_that_blocks_a_corrected_retry(self):
		requisition, version = self._draft()
		key = fx.key()
		with self.assertRaises(ProcurementRequisitionsError) as caught:
			cmd.save_requisition_summary(requisition=requisition, values={"requirement_title": "x"}, expected_record_version=version, idempotency_key=key, user=fx.AUTHOR)
		self.assertEqual(caught.exception.code, "REQ_CONTROL_INVALID")
		self.assertTrue(self._save(requisition, version, key=key)["ok"])  # same actor, the corrected request reuses the key

	# ----- real concurrency ---------------------------------------------------------

	def test_two_requests_with_one_key_execute_once_and_both_get_the_result(self):
		requisition, version = self._draft()
		frappe.db.commit()
		key = fx.key()
		conn_a = Conn(fx.AUTHOR, lambda: self._save(requisition, version, key=key), hold=True)
		self.assertTrue(conn_a.ran.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b = Conn(fx.AUTHOR, lambda: self._save(requisition, version, key=key))
		self.assertFalse(conn_b.finished.wait(BLOCKED_FOR), "the duplicate must wait for the first execution")
		conn_a.commit()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertEqual(conn_b.value["record_version"], conn_a.value["record_version"])
		self.assertTrue(conn_b.value["idempotent"])
		frappe.db.commit()
		self.assertEqual(frappe.db.count(JOURNAL, {"idempotency_key": key}), 1)
		current = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
		self.assertEqual(frappe.db.get_value("Requisition Version", current, "record_version"), version + 1)

	def test_a_stale_version_is_the_typed_refusal_not_a_save_timestamp_error(self):
		requisition, version = self._draft()
		frappe.db.commit()
		conn_b = Conn(fx.AUTHOR, lambda: self._save(requisition, version, key=fx.key(), latest="2102-06-30"), snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))
		conn_a = Conn(fx.AUTHOR, lambda: self._save(requisition, version, key=fx.key()))
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsInstance(conn_b.error, ProcurementRequisitionsError, repr(conn_b.error))
		self.assertEqual(conn_b.error.code, "REQ_STALE_VERSION")

	def test_the_reference_generator_takes_the_next_free_number_after_a_competing_commit(self):
		plan_item = f"PPI-MOH-2102-{fx.key()[:6].upper()}"
		fiscal_year = "2027-2028"
		mint = lambda: references.requisition_reference(fiscal_year=fiscal_year, plan_item_id_value=plan_item)  # noqa: E731
		conn_b = Conn("Administrator", mint, snapshot_first=True)
		self.assertTrue(conn_b.snapshot_open.wait(WAIT))

		def competing():
			reference = mint()
			frappe.db.sql("insert into `tabProcurement Requisition` (name, creation, modified, owner, modified_by, requisition_reference) values (%s, now(), now(), 'Administrator', 'Administrator', %s)", (reference, reference))
			return reference

		conn_a = Conn("Administrator", competing)
		self.assertTrue(conn_a.finished.wait(WAIT))
		self.assertIsNone(conn_a.error, conn_a.error)
		self.addCleanup(lambda: (frappe.db.delete("Procurement Requisition", {"requisition_reference": conn_a.value}), frappe.db.commit()))
		conn_b.start_gate.set()
		self.assertTrue(conn_b.finished.wait(WAIT))
		self.assertIsNone(conn_b.error, conn_b.error)
		self.assertTrue(conn_a.value.endswith("-001"))
		self.assertTrue(conn_b.value.endswith("-002"), conn_b.value)
