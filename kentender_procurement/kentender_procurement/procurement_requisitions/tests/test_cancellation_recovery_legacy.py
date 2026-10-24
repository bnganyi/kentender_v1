# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reconciling a Tender cancelled before the recovery existed (REQ-CHG-001 v1.20 §19.1; handoff step 6; REQ-CR-AC-006).

The legacy state is made by cancelling a real Tender through the real command and then removing everything the recovery registered — the
recovery, its holds, its events and the cancellation's reference to it — which is exactly what a cancellation decided before this
existed looks like. The reconciliation then runs against the real Planning, Requisitions, Tenders and Budget adapters: a read-only
inventory first, a dry run that writes nothing, then the registration of the SAME recovery, carried out by the same worker."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_core.utils.raw_delete import delete_rows
from kentender_procurement.procurement_requisitions.services import cancellation_recovery as recovery_service
from kentender_procurement.procurement_requisitions.services import funding_gateway, recovery_sweep
from kentender_procurement.procurement_requisitions.tests import cancellation_world as world
from kentender_procurement.procurement_requisitions.tests.test_cancellation_recovery_integration import WorldCase
from kentender_procurement.tenders.services import award_seam, recovery_reconciliation as reconciliation

RECOVERY = recovery_service.DOCTYPE


class TestLegacyCancellation(WorldCase):
	@classmethod
	def build_world(cls):
		return world.single_source_requisition()

	@classmethod
	def snapshot(cls) -> dict:
		reservations = world.reservations_of(cls.authorised["requisition"])
		line = world.budget_line_of(reservations[0])
		return {"item": world.planning_remaining(cls.authorised["item_id"]), "line": line, "position": world.budget_position(line), "reservations": reservations}

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# a cancellation decided before the recovery existed: nothing registered, nothing held, no event, no reference
		cancellation = cls.cancelled["cancellation"]
		delete_rows(RECOVERY, {"cancellation": cancellation})
		frappe.db.delete("Plan Cancellation Recovery Hold", {"cancellation_id": cancellation})
		frappe.db.delete("Requisition Event", {"event_type": "CancellationResourceRecoveryOutcome.v1", "requisition": cls.authorised["requisition"]})
		frappe.db.set_value("Tender Cancellation", cancellation, "resource_recovery", None, update_modified=False)
		frappe.db.commit()

	def row(self, report=None):
		report = report or reconciliation.inventory([self.tender])
		return next(r for r in report["tenders"] if r["tender"] == self.tender)

	def test_the_inventory_names_it_eligible_and_writes_nothing(self):
		report = reconciliation.inventory([self.tender])
		row = self.row(report)
		self.assertEqual((row["class"], row.get("reason", "")), ("eligible", ""))
		self.assertEqual(report["counts"]["eligible"], sum(1 for r in report["tenders"] if r["class"] == "eligible"))
		self.assertEqual(frappe.db.count(RECOVERY, {"tender": self.tender}), 0)
		self.assertEqual(frappe.db.count("Plan Cancellation Recovery Hold", {"plan_item_id": self.authorised["item_id"]}), 0)

	def test_a_dry_run_registers_nothing(self):
		with self.trial():
			result = reconciliation.reconcile(dry_run=True, tenders=[self.tender])
			mine = next(a for a in result["actions"] if a["tender"] == self.tender)
			self.assertEqual(mine["action"], "would register")
			self.assertEqual(frappe.db.count(RECOVERY, {"tender": self.tender}), 0)

	def test_a_reservation_released_for_another_reason_is_reported_and_held_not_repaired(self):
		reservation = self.sources_before["reservations"][0]
		with self.trial():
			funding_gateway.release_reservation(
				reservation=reservation, requisition_reference=frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "requisition_reference"),
				downstream_event_id="legacy-other", idempotency_key=uuid4().hex,
			)
			row = self.row()
			self.assertEqual(row["class"], "released for another reason")
			result = reconciliation.reconcile(dry_run=False, tenders=[self.tender])
			registered = next(a for a in result["actions"] if a["tender"] == self.tender)
			self.assertEqual(registered["action"], "registered")
			recovery = frappe.get_doc(RECOVERY, registered["recovery"])
			self.assertEqual((recovery.origin, recovery.reconciliation_version), ("Legacy reconciliation", "CR-LEGACY-1"))
			outcome = recovery_sweep.run_one(recovery.name)
			self.assertEqual(outcome["status"], "Needs attention")
			self.assertEqual(world.planning_remaining(self.authorised["item_id"]), self.sources_before["item"])  # nothing guessed, nothing restored
			self.assertEqual(frappe.db.count("Plan Cancellation Recovery Hold", {"recovery_id": recovery.name, "state": "Active"}), 1)  # the source stays held for the owner

	def test_a_surviving_award_obligation_is_named(self):
		with self.trial(), patch.object(award_seam, "downstream_disposition", return_value={"known": True, "notification_status": "Issued", "case": "AWC-1", "package_status": ""}):
			self.assertEqual(self.row()["class"], "converted or surviving obligation")

	def test_a_lineage_that_cannot_be_found_is_unmapped(self):
		with self.trial():
			frappe.db.set_value("Requisition Drawdown Line", {"parent": frappe.db.get_value("Procurement Requisition", self.authorised["requisition"], "authorised_version")}, "planning_drawdown_reference", "", update_modified=False)
			self.assertEqual(self.row()["class"], "unmapped")
			result = reconciliation.reconcile(dry_run=False, tenders=[self.tender])
			registered = next(a for a in result["actions"] if a["tender"] == self.tender)
			self.assertEqual(registered["action"], "registered")  # recorded as Needs attention with a typed reason; nothing is restored or guessed
			self.assertEqual(frappe.db.get_value(RECOVERY, registered["recovery"], "status"), "Needs attention")

	def test_zz_applied_it_is_restored_exactly_and_a_second_run_creates_nothing(self):
		first = reconciliation.reconcile(dry_run=False, tenders=[self.tender])
		mine = next(a for a in first["actions"] if a["tender"] == self.tender)
		self.assertEqual(mine["action"], "registered")
		recovery = mine["recovery"]
		self.assertEqual(frappe.db.get_value("Tender Cancellation", self.cancelled["cancellation"], "resource_recovery"), recovery)
		outcome = recovery_sweep.run_one(recovery)
		frappe.db.commit()
		self.assertEqual(outcome["status"], "Completed")
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])
		position, before = world.budget_position(self.sources_before["line"]), self.sources_before["position"]
		self.assertEqual(float(position["available"]), float(before["available"]) + 6_000_000.0)
		# the decision itself is untouched: no cancellation or approval event was fabricated
		self.assertEqual(frappe.db.count("Tender Event", {"tender": self.tender, "event_type": "TenderCancelled"}), 1)
		self.assertEqual(frappe.db.get_value("Tender", self.tender, "overall_status"), "Cancelled")

		counts = (frappe.db.count(RECOVERY), frappe.db.count("Reservation Cancellation Release"), frappe.db.count("Requisition Event"), frappe.db.count("Plan Cancellation Recovery Hold"))
		second = reconciliation.reconcile(dry_run=False, tenders=[self.tender])
		mine = next(a for a in second["actions"] if a["tender"] == self.tender)
		self.assertEqual((mine["action"], mine["why"]), ("skipped", "already registered"))
		self.assertEqual(recovery_sweep.run_one(recovery)["acted"], False)
		self.assertEqual((frappe.db.count(RECOVERY), frappe.db.count("Reservation Cancellation Release"), frappe.db.count("Requisition Event"), frappe.db.count("Plan Cancellation Recovery Hold")), counts)
		self.assertEqual([float(x) for x in world.planning_remaining(self.authorised["item_id"])], [100.0, 10_000_000.0])
