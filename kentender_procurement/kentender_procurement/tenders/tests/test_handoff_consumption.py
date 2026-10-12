# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-REQ-001 (REQ-CHG-001 v1.14 §9.2) — a requisition handoff is consumed only
inside Tenders' own Start command, by a Tender that exists, was created from
that very handoff and is the only one holding it. There is no web endpoint that
consumes a handoff for an arbitrary Tender string."""

from __future__ import annotations

import frappe

from kentender_procurement.procurement_requisitions import api as req_api
from kentender_procurement.tenders.services import draft_commands as cmd, handoff_gateway
from kentender_procurement.tenders.services.errors import TendersError
from kentender_procurement.tenders.tests import fixtures as fx
from kentender_procurement.tenders.tests.test_lifecycle import TenderLifecycleCase

TEMPLATE = {"template_key": "IT-EQUIPMENT-OPEN-V1", "template_version": "1.4"}


class TestHandoffConsumptionOnlyThroughStartTender(TenderLifecycleCase):
	def _consumed(self, handoff: str):
		return frappe.db.get_value("Authorised Requisition Handoff", handoff, ["consumed_at", "tender"], as_dict=True)

	def test_requisitions_publishes_no_web_endpoint_for_consumption(self):
		self.assertFalse(hasattr(req_api, "record_handoff_consumption"))
		with self.assertRaises(AttributeError):
			frappe.get_attr("kentender_procurement.procurement_requisitions.api.record_handoff_consumption")

	def test_a_tender_that_does_not_exist_cannot_be_bound(self):
		authorised = fx.authorised_handoff()
		with self.assertRaises(TendersError) as ctx:
			handoff_gateway.consume(handoff=authorised["handoff"], tender="NOPE", tender_version="x", **TEMPLATE, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TND_HANDOFF_INVALID")
		self.assertFalse(self._consumed(authorised["handoff"]).consumed_at)
		# and the handoff is still startable by the real command
		started = cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertEqual(started["action"], "started")

	def test_a_tender_created_from_another_handoff_cannot_consume_this_one(self):
		first, started = self._started()
		version = frappe.get_doc("Tender", started["tender"]).current_version
		with self.assertRaises(TendersError) as ctx:
			handoff_gateway.consume(handoff="RQH-NOT-THIS-ONE", tender=started["tender"], tender_version=version, **TEMPLATE, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TND_HANDOFF_INVALID")
		self.assertEqual(self._consumed(first["handoff"]).tender, started["tender"])

	def test_a_version_that_was_not_created_from_this_handoff_is_refused(self):
		first, started = self._started()
		for version in ("TNV-NOPE", ""):
			with self.assertRaises(TendersError) as ctx:
				handoff_gateway.consume(handoff=first["handoff"], tender=started["tender"], tender_version=version, **TEMPLATE, idempotency_key=fx.key())
			self.assertEqual(ctx.exception.code, "TND_HANDOFF_INVALID", version)
		frappe.db.set_value("Tender Version", started["tender_version"], "requisition_handoff", "RQH-OTHER", update_modified=False)
		with self.assertRaises(TendersError) as ctx:
			handoff_gateway.consume(handoff=first["handoff"], tender=started["tender"], tender_version=started["tender_version"], **TEMPLATE, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "TND_HANDOFF_INVALID")

	def test_the_start_command_still_consumes_atomically_and_replays(self):
		authorised, started = self._started()
		row = self._consumed(authorised["handoff"])
		self.assertTrue(row.consumed_at)
		self.assertEqual(row.tender, started["tender"])
		again = handoff_gateway.consume(handoff=authorised["handoff"], tender=started["tender"], tender_version=started["tender_version"], **TEMPLATE, idempotency_key=fx.key())
		self.assertEqual(again["action"], "already_consumed")
