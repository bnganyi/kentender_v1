# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §9.5/§11.2 — publication acknowledgment and the
milestone write-back: exactly one write on first acknowledgment, none on a
repeat with the same correlation ID, a different overwrite refused, no
milestone beyond invitation (TPR-AC-042/043, SMOKE-17/18)."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_preparation.services import events, planning_gateway, publication
from kentender_procurement.tender_preparation.services.errors import TenderPreparationError
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestAcknowledgeAndPublish(TenderCase):
	def test_first_acknowledgment_writes_exactly_one_invitation_actual(self):
		app = fx.approved()
		frappe.set_user("Administrator")
		correlation = fx.key()
		result = publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=correlation, published_on="2102-02-01")
		self.assertEqual(result["action"], "acknowledged")
		self.assertTrue(result["milestone_published"])
		root = frappe.get_doc("Prepared Tender", app["tender"])
		self.assertTrue(root.publication_consumed_at)
		handoff = frappe.get_doc("Tender Publication Handoff", app["publication_handoff"])
		self.assertEqual((handoff.status, handoff.consumption_correlation_id, str(handoff.published_on)), ("Consumed", correlation, "2102-02-01"))
		self.assertEqual(str(planning_gateway.current_actual_invitation_date(root.plan_item_id)), "2102-02-01")
		self.assertEqual(frappe.db.count("Tender Preparation Event", {"tender": root.name, "event_type": events.EVENT_MILESTONE_ACTUAL}), 1)
		item = frappe.db.get_value("Annual Plan Item", {"plan_item_id": root.plan_item_id, "item_state": "Active"}, ["actual_bid_opening_date", "actual_evaluation_completion_date"], as_dict=True)
		self.assertFalse(item.actual_bid_opening_date or item.actual_evaluation_completion_date)

	def test_a_repeat_with_the_same_correlation_id_publishes_nothing(self):
		app = fx.approved()
		frappe.set_user("Administrator")
		correlation = fx.key()
		publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=correlation, published_on="2102-02-01")
		again = publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=correlation, published_on="2102-02-01")
		self.assertTrue(again["idempotent"])
		self.assertEqual(frappe.db.count("Tender Preparation Event", {"tender": app["tender"], "event_type": events.EVENT_MILESTONE_ACTUAL}), 1)

	def test_an_acknowledgment_for_a_tender_not_yet_approved_is_rejected(self):
		sub = fx.submitted()
		frappe.set_user("Administrator")
		with self.assertRaises(TenderPreparationError) as ctx:
			publication.acknowledge_publication_consumed(tender=sub["tender"], correlation_id=fx.key())
		self.assertEqual(ctx.exception.code, "TPR_MILESTONE_ACTUAL_REJECTED")

	def test_a_second_different_acknowledgment_after_consumption_is_rejected(self):
		app = fx.approved()
		frappe.set_user("Administrator")
		publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-01")
		with self.assertRaises(TenderPreparationError) as ctx:
			publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-02")
		self.assertEqual(ctx.exception.code, "TPR_MILESTONE_ACTUAL_REJECTED")

	def test_a_different_existing_actual_date_is_never_overwritten(self):
		app = fx.approved()
		root = frappe.get_doc("Prepared Tender", app["tender"])
		name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": root.plan_item_id, "item_state": "Active"}, "name")
		frappe.db.set_value("Annual Plan Item", name, "actual_invitation_date", "2102-01-20", update_modified=False)
		frappe.set_user("Administrator")
		with self.assertRaises(TenderPreparationError) as ctx:
			publication.acknowledge_publication_consumed(tender=app["tender"], correlation_id=fx.key(), published_on="2102-02-01")
		self.assertEqual(ctx.exception.code, "TPR_MILESTONE_ACTUAL_REJECTED")
		self.assertEqual(str(frappe.db.get_value("Annual Plan Item", name, "actual_invitation_date")), "2102-01-20")
		# the refused acknowledgment left the handoff Ready (atomic)
		self.assertEqual(frappe.db.get_value("Tender Publication Handoff", app["publication_handoff"], "status"), "Ready")
