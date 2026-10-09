# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 §5.1, §7.4, §9.1, §9.1A and REQ-SC-SEQUENTIAL, proven with a
REAL Tender start (not the seed stand-in): a partial Requisition is authorised,
Tender Preparation starts a Tender from its handoff (consuming it), and the
next Requisition can use only what the first left over.

Consumption releases the one-open slot. It must not restore quantity or money
already authorised: the Planning drawdown and the Budget reservations stay
exactly as authorised, the scope lock stays, and revocation is refused.

v1.15 workflow: the requester types each item quantity once and one estimated
total cost per source; the requested quantity is derived from the items."""

from __future__ import annotations

from decimal import Decimal

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import authorise as authorise_service
from kentender_procurement.procurement_requisitions.services import draft_commands as req_cmd
from kentender_procurement.procurement_requisitions.services import eligibility_gateway
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import draft_commands as tender_cmd
from kentender_procurement.tenders.tests import fixtures as fx

SHARE = Decimal("0.4")  # the first Requisition asks for 40% of what each source has left


class TestPartialRequisitionThenRemainder(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_all()
		self.addCleanup(frappe.set_user, "Administrator")

	def _code(self, ctx) -> str:
		return getattr(ctx.exception, "code", None)

	def _partial_authorised(self) -> tuple[str, str, dict, dict[str, int], dict[str, str]]:
		"""A Requisition for 40% of each source, driven through the real commands to authorisation."""
		_, item_id = req_fx.active_item(quantity=250)
		requisition = req_fx.prepare(item_id)["requisition"]
		view = req_fx.editor(requisition)
		self.original_quantity = sum(Decimal(r["remaining_quantity_value"]) for r in view["amounts"])
		self.original_value = sum(Decimal(r["remaining_value_value"]) for r in view["amounts"])
		quantities: dict[str, int] = {}
		estimates: dict[str, str] = {}
		for row in view["amounts"]:
			quantity = Decimal(row["remaining_quantity_value"]) * SHARE
			value = Decimal(row["remaining_value_value"]) * SHARE
			self.assertEqual(quantity, quantity.to_integral_value(), "the fixture's 40% must be a whole number of Each")
			quantities[row["drawdown_line_id"]] = int(quantity)
			estimates[row["drawdown_line_id"]] = f"{value:.2f}"
		req_fx.fill_request_information(requisition)
		req_fx.add_laptops(requisition, quantities=quantities)
		req_fx.enter_estimates(requisition, values=estimates)
		req_fx.apply_standard_package(requisition)
		req_fx.send(requisition)
		req_fx.submit_as_hod(requisition)
		authorised = req_fx.authorise(requisition)
		frappe.set_user("Administrator")
		return item_id, requisition, authorised, quantities, estimates

	def _reservations(self, requisition: str) -> dict[str, tuple[str, Decimal, Decimal]]:
		"""drawdown_line_id -> (status, original, remaining) for this Requisition's Budget funding reservations."""
		version = frappe.db.get_value("Procurement Requisition", requisition, "current_version")
		line_ids = frappe.get_all("Requisition Drawdown Line", filters={"parent": version}, pluck="drawdown_line_id")
		out = {}
		for row in frappe.get_all("Funding Reservation", filters={"drawdown_line_id": ["in", line_ids]}, fields=["drawdown_line_id", "status", "original_amount", "remaining_amount"]):
			out[row.drawdown_line_id] = (row.status, Decimal(str(row.original_amount)), Decimal(str(row.remaining_amount)))
		return out

	def _drawdowns(self, requisition: str) -> list[str]:
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		frappe.set_user(req_fx.HOPF)  # Planning's drawdown read is for the authoriser
		try:
			rows = eligibility_gateway.list_requisition_drawdowns(reference)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(rows, "the authorised Requisition has a Planning drawdown")
		return sorted(repr(sorted((k, str(v)) for k, v in d.items() if k in ("plan_item_line_id", "allocation_id", "quantity", "amount", "state", "status"))) for d in rows)

	def test_a_partial_requisition_consumed_by_a_real_tender_leaves_exactly_the_remainder(self):
		item_id, first, authorised, quantities, estimates = self._partial_authorised()
		first_quantity = sum(quantities.values())
		first_value = sum(Decimal(v) for v in estimates.values())

		# --- authorised, handoff unconsumed ---------------------------------
		before = eligibility_gateway.get_requisition_eligible_plan_item(item_id)
		self.assertTrue(before.get("eligible"), "an authorised partial draw leaves the item eligible for the remainder")
		remaining_value_before = Decimal(str(before["remaining_value"]))
		scope_before = (before.get("scope") or {}).get("locked_since")
		self.assertTrue(scope_before, "first authorisation fixes the scope")
		reservations_before = self._reservations(first)
		self.assertEqual(len(reservations_before), len(quantities), "one Budget reservation per drawdown line")
		self.assertEqual(sum(r[1] for r in reservations_before.values()), first_value, "the reservations equal the entered estimated total costs")
		drawdowns_before = self._drawdowns(first)
		self.assertEqual(len(drawdowns_before), len(quantities))
		self.assertTrue(frappe.db.get_value("Procurement Requisition", first, "open_slot_key"), "an authorised, unconsumed Requisition holds the open slot")

		# A second Prepare routes to the existing open Requisition and creates nothing.
		again = req_fx.prepare(item_id)
		self.assertEqual(again.get("action"), "existing")
		self.assertEqual(again["requisition"], first)

		# --- Tender Preparation starts a Tender: the handoff is consumed -------
		started = tender_cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		self.assertTrue(started.get("tender"))
		frappe.set_user("Administrator")

		root = frappe.get_doc("Procurement Requisition", first)
		self.assertFalse(root.open_slot_key, "consumption releases the one-open slot")
		self.assertEqual(root.current_state, "Authorised", "consumption does not change the authorised state")

		# Nothing authorised was restored or released.
		self.assertEqual(self._drawdowns(first), drawdowns_before, "the Planning drawdown is unchanged by consumption")
		self.assertEqual(self._reservations(first), reservations_before, "the Budget reservations are unchanged by consumption")
		after = eligibility_gateway.get_requisition_eligible_plan_item(item_id)
		self.assertEqual(Decimal(str(after["remaining_value"])), remaining_value_before, "consumption restores no money")
		self.assertEqual((after.get("scope") or {}).get("locked_since"), scope_before, "the scope lock stays the first lock")

		# Revocation after consumption is refused and changes nothing.
		frappe.set_user(req_fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise_service.revoke_unconsumed_authorisation(
				requisition=first, reason="Too late: Tender Preparation already began.",
				expected_record_version=req_fx.root_version(first), idempotency_key=req_fx.key(),
			)
		self.assertEqual(self._code(ctx), "REQ_HANDOFF_CONSUMED")
		frappe.set_user("Administrator")
		self.assertEqual(self._reservations(first), reservations_before)

		# --- the second Requisition can use only the remainder ----------------
		second = req_fx.prepare(item_id)
		self.assertEqual(second.get("action"), "created", "the slot is free, so a new Draft is created")
		self.assertNotEqual(second["requisition"], first)
		view = req_fx.editor(second["requisition"])
		offered_quantity = sum(Decimal(r["remaining_quantity_value"]) for r in view["amounts"])
		offered_value = sum(Decimal(r["remaining_value_value"]) for r in view["amounts"])
		self.assertEqual(offered_value, remaining_value_before, "the second Draft is offered exactly what the first left")
		self.assertEqual(Decimal(first_quantity) + offered_quantity, self.original_quantity, "the first draw plus the remainder is exactly the original quantity")
		self.assertEqual(first_value + offered_value, self.original_value, "the first draw plus the remainder is exactly the original value")
		self.assertEqual(len(view["amounts"]), len(quantities), "no extra source and no fresh allowance appeared")
		# v1.15: nothing is requested until the requester types it.
		self.assertEqual([(r["requested_quantity_value"], r["requested_value_value"]) for r in view["amounts"]], [("0", "")] * len(view["amounts"]))

		# One Each or one cent more than the remainder is refused, with the real limit named.
		row = view["amounts"][0]
		too_many = int(Decimal(row["remaining_quantity_value"])) + 1
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			req_cmd.add_same_specification_items(
				requisition=second["requisition"], shared={"equipment_category": "Laptop", "item_name": "Business laptops"},
				rows=[{"drawdown_line_id": row["drawdown_line_id"], "quantity": too_many, "intended_use": "Field deployment for the remainder"}],
				expected_record_version=view["package_record_version"], idempotency_key=req_fx.key(),
			)
		self.assertEqual(self._code(ctx), "REQ_QUANTITY_EXCEEDS_AVAILABLE")
		self.assertIn(f"{int(Decimal(row['remaining_quantity_value'])):,}", str(ctx.exception))
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			req_cmd.save_requisition_summary(
				requisition=second["requisition"],
				values={"drawdown_lines": [{"drawdown_line_id": row["drawdown_line_id"], "requested_value": f"{Decimal(row['remaining_value_value']) + Decimal('0.01'):.2f}"}]},
				expected_record_version=view["header"]["version_record_version"], idempotency_key=req_fx.key(),
			)
		self.assertEqual(self._code(ctx), "REQ_ESTIMATE_EXCEEDS_ALLOWANCE")
