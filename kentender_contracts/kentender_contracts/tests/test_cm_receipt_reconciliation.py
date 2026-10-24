# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 9.1 (plan Phase 6, tracker CM8-605, gate CM-G06 `cm-native-gate`; proof level L2): the stock, the assets and the ledger ERPNext holds agree with what an acceptance decided.

Read only. After the accepted-subset receipt is posted, the receipt's quantity and value for each catalogue item, the stock a stock item put on the ledger, the assets a fixed-asset item made and the balance of
the receipt's ledger are compared with the accepted units at the contract rate. A difference is reported and sent to the technical operator, never adjusted by Contract Management."""

from __future__ import annotations

from unittest import mock

import frappe

from kentender_contracts.native import adapter
from kentender_contracts.services import delivery, work
from kentender_contracts.tests import native_world as world
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase

CONTROLS = "Contract Test Environment Controls"


class ReconciliationCase(ContractCase):
	native = True
	item = ""  # the catalogue item the single line is mapped to; the fixed asset by default

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		frappe.db.set_single_value(CONTROLS, "signing_outcome", "")
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24], item=self.item)
		self.case = self.t.active()
		self.units = tw.fresh_serials(10)
		self.t.appointed()
		self.arrival = self.t.arrive(self.units)["arrival"]
		self.t.inspect(self.arrival, self.units, bad=tuple(self.units[8:]))

	def v(self):
		return self.t.version()

	def k(self, step):
		return self.t.key(step)

	def accepted(self):
		delivery.sign_technical_certificate(self.case, arrival=self.arrival, expected_version=self.v(), idempotency_key=self.k("c"), actor=self.p["peter"])
		report = delivery.prepare_acceptance_report(self.case, arrivals=[self.arrival], expected_version=self.v(), idempotency_key=self.k("p"), actor=self.p["julia"])["acceptance"]
		for person in ("julia", "peter", "brian"):
			delivery.sign_acceptance_report(self.case, acceptance=report, expected_version=self.v(), idempotency_key=self.k("s"), actor=self.p[person])
		return report, delivery.posted_receipts(self.case)[0]


class TestAssetReconciliation(ReconciliationCase):
	def test_the_receipt_ERPNext_holds_agrees_with_what_was_accepted_in_quantity_value_assets_and_ledger(self):
		name, receipt = self.accepted()
		report = frappe.get_doc("Contract Acceptance", name)
		facts = adapter.receipt_facts(receipt)
		self.assertEqual((facts["items"][world.ITEM_FA]["qty"], facts["items"][world.ITEM_FA]["amount"], facts["assets"]), (8, 800000, 8), "eight units at the contract rate, an asset for each")
		self.assertEqual(delivery.reconcile_receipt(self.case, receipt, report), [], "the stock, the assets and Finance agree with the acceptance")
		events = frappe.get_all("Contract Event", filters={"contract_case": self.case, "event_type": ["in", ["Receipt reconciled", "Receipt differs"]]}, pluck="event_type")
		self.assertEqual(events, ["Receipt reconciled"])

	def test_a_receipt_that_differs_from_the_acceptance_is_reported_and_opens_technical_recovery_not_silently_accepted(self):
		name, receipt = self.accepted()
		report = frappe.get_doc("Contract Acceptance", name)
		real = adapter.receipt_facts(receipt)
		for change, needle in ((lambda f: f["items"][world.ITEM_FA].update(qty=9), "9 on the receipt, 8 accepted"), (lambda f: f["items"][world.ITEM_FA].update(amount=700000.0), "worth 700,000.00"),
				(lambda f: f.update(assets=7), "7 asset(s) made from the receipt, 8 accepted"), (lambda f: f["ledger"].update(credit=1.0), "ledger does not balance")):
			doctored = frappe.parse_json(frappe.as_json(real))
			change(doctored)
			with mock.patch.object(adapter, "receipt_facts", return_value=doctored):
				found = delivery.reconcile_receipt(self.case, receipt, report)
			self.assertTrue([d for d in found if needle in d], (needle, found))
		with mock.patch.object(adapter, "receipt_facts", return_value={**real, "assets": 7}):
			delivery.post_accepted_receipt(self.case, acceptance=name, actor=self.p["julia"])
		self.assertTrue(frappe.db.exists("Contract Event", {"contract_case": self.case, "event_type": "Receipt differs"}))
		self.assertTrue([1 for t in work.live(self.case) if t["title"] == "Reconcile the stock or asset update"], "the technical operator is asked to recover it")


class TestStockReconciliation(ReconciliationCase):
	"""A stock item, not an asset: the stock ledger holds what was accepted and the receipt is worth the accepted units at the contract rate."""

	item = world.ITEM_PLAIN

	def test_the_stock_ledger_holds_the_accepted_units_and_nothing_else(self):
		name, receipt = self.accepted()
		facts = adapter.receipt_facts(receipt)
		self.assertEqual((facts["items"][world.ITEM_PLAIN]["qty"], facts["stock"], facts["assets"]), (8, {world.ITEM_PLAIN: 8}, 0), "eight units on the stock ledger, no asset")
		self.assertEqual(facts["amount"], 800000)
		self.assertEqual(delivery.reconcile_receipt(self.case, receipt, frappe.get_doc("Contract Acceptance", name)), [])
		with mock.patch.object(adapter, "receipt_facts", return_value={**facts, "stock": {world.ITEM_PLAIN: 7}}):
			found = delivery.reconcile_receipt(self.case, receipt, frappe.get_doc("Contract Acceptance", name))
		self.assertEqual(found, [f"{world.ITEM_PLAIN}: 7 on the stock ledger, 8 accepted."])
