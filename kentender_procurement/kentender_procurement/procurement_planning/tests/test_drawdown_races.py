# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-107 — a Requisition drawdown rechecks the correction hold, the Plan
Item state and the record version from the latest committed rows.

MariaDB runs at REPEATABLE READ: a plain read after `SELECT ... FOR UPDATE`
returns the transaction's older snapshot, so a drawdown that waited for (or
simply started before) a competing command read the pre-commit state and could
bypass a hold already acknowledged to the Planner. These are real
two-connection snapshot races (`kentender_procurement.tests.two_connections`):
the drawdown's connection opens its snapshot, the competing command commits,
then the drawdown runs."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import envelope, plan_requisition
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase, key
from kentender_procurement.tests.two_connections import WAIT, Conn


class TestDrawdownSnapshotRaces(RequisitionCase):
	def _world(self):
		_accepted, item_id = self.active_item(indicative_amount=1000000)
		allocation_id = self.allocation_id_of(item_id)
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		# A first authorised drawdown locks the scope: from then on the guard
		# writes nothing, so a stale read raises no timestamp conflict that could
		# mask the missing recheck.
		frappe.set_user(fx.HOPF)
		plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}",
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "0.2", "amount": "200000"}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		frappe.set_user("Administrator")
		frappe.db.commit()
		return item_id, allocation_id, read["record_version"]

	def _drawdown(self, item_id, allocation_id, record_version):
		def run():
			frappe.set_user(fx.HOPF)
			return plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}",
				allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "0.3", "amount": "300000"}],
				expected_record_version=record_version, idempotency_key=key(),
			)

		return Conn(fx.HOPF, run, snapshot_first=True)

	def test_a_correction_hold_committed_after_the_drawdowns_snapshot_still_blocks_it(self):
		item_id, allocation_id, record_version = self._world()
		drawdown = self._drawdown(item_id, allocation_id, record_version)
		self.assertTrue(drawdown.snapshot_open.wait(WAIT))

		def hold():
			frappe.set_user(fx.HOD)
			return plan_requisition.receive_plan_item_correction_request(
				plan_item_id=item_id, requisition_reference="REQ-RACE-1", requisition_version="RQV-RACE-1",
				reason="The authorised warranty period does not match the department's actual need.", idempotency_key=key(),
			)

		correction = Conn(fx.HOD, hold)
		self.assertTrue(correction.finished.wait(WAIT))
		self.assertIsNone(correction.error, correction.error)
		drawdown.start_gate.set()
		self.assertTrue(drawdown.finished.wait(WAIT))
		self.assertIsInstance(drawdown.error, ProcurementPlanningError, repr(drawdown.error))
		self.assertEqual(drawdown.error.code, "PLN_ITEM_AUTHORISATION_HELD")
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 1)  # the first, locking drawdown only

	def test_a_record_version_changed_after_the_drawdowns_snapshot_is_a_stale_write(self):
		item_id, allocation_id, record_version = self._world()
		drawdown = self._drawdown(item_id, allocation_id, record_version)
		self.assertTrue(drawdown.snapshot_open.wait(WAIT))

		def supersede():
			frappe.set_user("Administrator")
			item_name = plan_requisition._requisition_item_name(item_id)
			envelope.bump(envelope.locked("Annual Plan Item", item_name))

		change = Conn("Administrator", supersede)
		self.assertTrue(change.finished.wait(WAIT))
		self.assertIsNone(change.error, change.error)
		drawdown.start_gate.set()
		self.assertTrue(drawdown.finished.wait(WAIT))
		self.assertIsInstance(drawdown.error, ProcurementPlanningError, repr(drawdown.error))
		self.assertEqual(drawdown.error.code, "PLN_STALE_WRITE")
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 1)

	def test_an_item_that_stopped_being_active_after_the_snapshot_is_refused(self):
		item_id, allocation_id, record_version = self._world()
		drawdown = self._drawdown(item_id, allocation_id, record_version)
		self.assertTrue(drawdown.snapshot_open.wait(WAIT))

		def retire():
			item_name = plan_requisition._requisition_item_name(item_id)
			frappe.db.set_value("Annual Plan Item", item_name, "item_state", "Superseded", update_modified=False)

		change = Conn("Administrator", retire)
		self.assertTrue(change.finished.wait(WAIT))
		self.assertIsNone(change.error, change.error)
		drawdown.start_gate.set()
		self.assertTrue(drawdown.finished.wait(WAIT))
		self.assertIsNotNone(drawdown.error)
		self.assertIn("not currently eligible", str(drawdown.error))
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 1)

	def test_a_funding_state_changed_after_the_drawdowns_snapshot_is_refused(self):
		"""RG-23 — the Annual Plan Version's funding state is a different row from the locked Plan Item;
		it is read as a locking read, not from the snapshot."""
		item_id, allocation_id, record_version = self._world()
		drawdown = self._drawdown(item_id, allocation_id, record_version)
		self.assertTrue(drawdown.snapshot_open.wait(WAIT))
		plan_version = frappe.db.get_value("Annual Plan Item", plan_requisition._requisition_item_name(item_id), "plan_version")

		def stale():
			frappe.db.set_value("Annual Plan Version", plan_version, "funding_state", "Stale", update_modified=False)

		change = Conn("Administrator", stale)
		self.assertTrue(change.finished.wait(WAIT))
		self.assertIsNone(change.error, change.error)
		self.addCleanup(lambda: (frappe.db.set_value("Annual Plan Version", plan_version, "funding_state", "Confirmed", update_modified=False), frappe.db.commit()))
		drawdown.start_gate.set()
		self.assertTrue(drawdown.finished.wait(WAIT))
		self.assertIsNotNone(drawdown.error)
		self.assertIn("not currently eligible", str(drawdown.error))
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 1)

	def test_an_allowance_drawn_after_the_drawdowns_snapshot_still_counts(self):
		"""RG-23 — the drawn totals are summed from the latest committed Plan Drawdown References, so two
		drawdowns that start together cannot both fit into the same remaining balance."""
		item_id, allocation_id, record_version = self._world()
		drawdown = self._drawdown(item_id, allocation_id, record_version)  # asks 0.3 / 300000 of the 0.8 / 800000 left
		self.assertTrue(drawdown.snapshot_open.wait(WAIT))

		def competing():
			frappe.set_user(fx.HOPF)
			return plan_requisition.authorise_requisition_drawdown(
				plan_item_id=item_id, requisition_reference=f"REQ-{key()[:8]}",
				allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "0.6", "amount": "600000"}],
				expected_record_version=record_version, idempotency_key=key(),
			)

		other = Conn(fx.HOPF, competing)
		self.assertTrue(other.finished.wait(WAIT))
		self.assertIsNone(other.error, other.error)
		drawdown.start_gate.set()
		self.assertTrue(drawdown.finished.wait(WAIT))
		self.assertIsInstance(drawdown.error, ProcurementPlanningError, repr(drawdown.error))
		self.assertEqual(drawdown.error.code, "PLN_ALLOWANCE_EXCEEDED")
		frappe.db.commit()
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 2)  # the first and the competing one
