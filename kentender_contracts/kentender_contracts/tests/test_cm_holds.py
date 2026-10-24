# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §5.17 first paragraph and §5.18 (tracker CM8-303): every open hold is evaluated independently, the permitted
set is the intersection of all guards, a hold has an explicit scope, owner and clearing evidence, and the most prominent hold
never masks another."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import errors, holds, intents, records

NS = "CM_TEST"


def hold(key, blocks, *, scope=(), owner="Head of procurement", kind="Issue"):
	return holds.Hold(key=key, kind=kind, reason=f"{key} needs attention.", blocks=frozenset(blocks), owner=owner, clearing="Authorised disposition", scope=scope)


class TestHoldEvaluation(IntegrationTestCase):
	"""The evaluator on its own, with providers it registers itself."""

	def setUp(self) -> None:
		self.saved = dict(holds.PROVIDERS)
		holds.PROVIDERS.clear()
		self.open: list[holds.Hold] = []
		holds.provider("test")(lambda case: list(self.open))

	def tearDown(self) -> None:
		holds.PROVIDERS.clear()
		holds.PROVIDERS.update(self.saved)

	def test_a_hold_blocks_only_the_consequences_it_names(self):
		self.open = [hold("H1", ["pay"])]
		self.assertFalse(holds.permitted("C", "pay"))
		self.assertTrue(holds.permitted("C", "post_receipt"))

	def test_every_hold_that_blocks_is_named_so_none_masks_another(self):
		self.open = [hold("H1", ["pay"]), hold("H2", ["pay", "use_goods"], owner="Finance")]
		with self.assertRaises(errors.ContractError) as caught:
			holds.require("C", "pay")
		self.assertEqual(caught.exception.code, "CM_HOLD")
		self.assertEqual([r["detail"]["hold"] for r in caught.exception.reasons], ["H1", "H2"])
		self.assertEqual(caught.exception.reasons[1]["detail"]["holder"], "Finance")
		self.assertEqual(caught.exception.reasons[0]["detail"]["clears_with"], "Authorised disposition")

	def test_the_permitted_set_is_the_intersection_of_all_guards(self):
		self.open = [hold("H1", ["pay"]), hold("H2", ["post_receipt"])]
		blocked = {cap: [h.key for h in hs] for cap, hs in holds.permitted_set("C").items() if hs}
		self.assertEqual(blocked, {"pay": ["H1"], "post_receipt": ["H2"]})
		self.assertIn("certify_invoice", [cap for cap, hs in holds.permitted_set("C").items() if not hs])

	def test_a_scoped_hold_leaves_an_unaffected_subject_eligible(self):
		self.open = [hold("H1", ["pay"], scope=("line-1",))]
		self.assertFalse(holds.permitted("C", "pay", "line-1"))
		self.assertTrue(holds.permitted("C", "pay", "line-2"))
		self.assertFalse(holds.permitted("C", "pay"), "a read or command that names no subject sees every hold")

	def test_a_whole_case_hold_blocks_every_subject(self):
		self.open = [hold("H1", ["pay"])]
		self.assertFalse(holds.permitted("C", "pay", "line-2"))

	def test_a_consequence_that_does_not_exist_cannot_be_held_or_asked_about(self):
		with self.assertRaises(ValueError):
			hold("H1", ["pya"])
		with self.assertRaises(ValueError):
			holds.blocking("C", "pya")

	def test_holds_are_read_fresh_so_no_stale_copy_allows_an_action(self):
		self.assertTrue(holds.permitted("C", "pay"))
		self.open = [hold("H1", ["pay"])]
		self.assertFalse(holds.permitted("C", "pay"))
		self.open = []
		self.assertTrue(holds.permitted("C", "pay"))

	def test_an_invalidating_correction_places_no_hold_and_a_holding_one_is_scoped(self):
		with self.assertRaises(ValueError):
			holds.correction_hold("R18-07", key="x", reason="x", scope=(), clearing="x")
		h = holds.correction_hold("R18-05", key="correction:1", reason="The accepted quantity changed after liability posting.", scope=("invoice:INV-1",), clearing="Finance adjustment reconciled")
		self.assertEqual((h.kind, set(h.blocks), h.owner, h.scope), ("Correction", {"pay"}, "Finance", ("invoice:INV-1",)))


class TestPendingOperationHolds(IntegrationTestCase):
	"""The built-in provider: a pending or failed operation holds the consequences its §5.17 row names, and nothing else."""

	def setUp(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = NS
		self.case = records.new("Contract Case", contract_id="CM-TEST-H1", source_kind="External record")
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = ""
		records.wipe(NS)
		frappe.db.commit()

	def intent(self, kind, subject, *, key="k", state=None, owner="Technical recovery"):
		doc = intents.record(self.case.name, subject, 1, kind, key, recovery_owner=owner)
		if state:
			doc.state = state
			records.save(doc)
		return doc

	def blocked(self, capability, subject=None):
		return [h.key for h in holds.blocking(self.case.name, capability, subject)]

	def test_a_case_with_no_pending_operation_holds_nothing(self):
		self.assertEqual(holds.open_holds(self.case.name), [])

	def test_an_uncertain_receipt_holds_certification_payment_and_use_of_the_goods_but_not_new_spending(self):
		doc = self.intent("Accepted receipt", "acceptance:A-1", state="Uncertain")
		for capability in ("certify_invoice", "pay", "use_goods"):
			self.assertEqual(self.blocked(capability), [f"operation:{doc.name}"], capability)
		self.assertEqual(self.blocked("new_spending"), [])
		self.assertEqual(holds.open_holds(self.case.name)[0].owner, "Technical recovery")

	def test_two_pending_operations_each_hold_payment_and_both_are_named(self):
		receipt = self.intent("Accepted receipt", "acceptance:A-1", key="r", state="Uncertain")
		invoice = self.intent("Native invoice", "invoice:I-1", key="i", state="Failed", owner="Finance")
		with self.assertRaises(errors.ContractError) as caught:
			holds.require(self.case.name, "pay")
		self.assertEqual({r["detail"]["hold"] for r in caught.exception.reasons}, {f"operation:{receipt.name}", f"operation:{invoice.name}"})

	def test_the_hold_ends_when_the_operation_reconciles(self):
		doc = self.intent("Native payment", "payment:P-1", state="Uncertain")
		self.assertFalse(holds.permitted(self.case.name, "confirm_settlement"))
		intents.reconcile(doc.name, lambda identity: "PAY-1", native_doctype="Payment Entry")
		self.assertTrue(holds.permitted(self.case.name, "confirm_settlement"))
		self.assertTrue(holds.permitted(self.case.name, "pay"))

	def test_a_funding_conversion_failure_at_formation_shows_the_specifications_own_wording(self):
		self.intent("Funding conversion", "agreement", state="Failed", owner="Budget owner")
		reason = holds.open_holds(self.case.name)[0].reason
		self.assertEqual(reason, "Contract signed — funding/order update pending")
		self.assertFalse(holds.permitted(self.case.name, "post_receipt"))

	def test_a_purchase_order_is_told_apart_by_what_it_is_for(self):
		self.intent("Purchase order", "agreement", key="po", state="Failed")
		self.assertEqual(self.blocked("pay"), [h.key for h in holds.open_holds(self.case.name)])
		other = self.intent("Purchase order", "amendment:1", key="po2", state="Failed")
		by_key = {h.key: h for h in holds.open_holds(self.case.name)}
		self.assertEqual(set(by_key[f"operation:{other.name}"].blocks), {"new_spending", "pay"})
		with self.assertRaises(ValueError):
			self.intent("Purchase order", "something else", key="po3", state="Failed")
			holds.open_holds(self.case.name)

	def test_a_failed_signing_attempt_holds_nothing_but_an_uncertain_one_blocks_a_new_attempt_and_activation(self):
		doc = self.intent("Signing attempt", "agreement", state="Failed", owner="Trust recovery")
		self.assertTrue(holds.permitted(self.case.name, "new_signing_attempt"))
		doc.state = "Uncertain"
		records.save(doc)
		for capability in ("new_signing_attempt", "activate_contract", "convert_funding", "create_order"):
			self.assertFalse(holds.permitted(self.case.name, capability), capability)
		self.assertTrue(holds.permitted(self.case.name, "pay"))

	def test_a_dispatch_that_failed_holds_nothing(self):
		self.intent("Report dispatch", "acceptance:A-1", state="Failed")
		self.intent("Notice dispatch", "agreement", key="n", state="Uncertain")
		self.assertEqual(holds.open_holds(self.case.name), [])

	def test_a_closure_finalisation_failure_does_not_hold_the_closed_state_only_the_financial_claims(self):
		self.intent("Funding closure", "closure", state="Uncertain", owner="Budget owner")
		self.assertFalse(holds.permitted(self.case.name, "mark_financially_finalised"))
		self.assertFalse(holds.permitted(self.case.name, "release_funds"))
		self.assertTrue(holds.permitted(self.case.name, "close_contract"))
