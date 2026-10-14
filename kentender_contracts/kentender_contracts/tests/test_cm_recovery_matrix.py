# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §5.17 and §5.18 (tracker CM8-304): the eight operation rows and the nine correction rows are in the code, in
the specification's order and words, and `reconciliation/recovery_matrix.md` is generated from them, so it cannot drift.
Table-driven: every row is probed for every state of every operation kind it names."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import intents, recovery
from kentender_contracts.services.capabilities import CAPABILITIES

RECONCILIATION = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/reconciliation"
DISPATCH_KINDS = {"Report dispatch", "Notice dispatch"}  # §5.17 lists no blocked consequence for a failed dispatch
ALL_STATES = ("Recorded", "Attempting", "Succeeded", "Failed", "Uncertain", "Reconciled")


def generator():
	spec = importlib.util.spec_from_file_location("build_recovery_matrix", RECONCILIATION / "tools/build_recovery_matrix.py")
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


class TestRecoveryMatrix(IntegrationTestCase):
	def test_the_model_has_the_specifications_eight_and_nine_rows_in_order(self):
		gen = generator()
		self.assertEqual([c[0] for _, c in gen.operations()], [r.name for r in recovery.OPERATIONS])
		self.assertEqual([c[0] for _, c in gen.corrections()], [r.name for r in recovery.CORRECTIONS])
		self.assertEqual((len(recovery.OPERATIONS), len(recovery.CORRECTIONS)), (8, 9))

	def test_the_generated_document_is_current(self):
		self.assertEqual((RECONCILIATION / "recovery_matrix.md").read_text(), generator().render(), "regenerate with tools/build_recovery_matrix.py")

	def test_the_wording_the_screens_use_is_the_specifications(self):
		spec = {c[0]: " ".join(c).lower() for _, c in generator().operations()}
		for row in recovery.OPERATIONS:
			if row.display:
				self.assertIn(row.display.lower(), spec[row.name], row.id)

	def test_every_operation_kind_has_a_row_except_the_dispatches(self):
		kinds = intents.kinds()
		covered = {kind for row in recovery.OPERATIONS for kind in row.kinds}
		self.assertEqual(kinds - covered, DISPATCH_KINDS)
		self.assertEqual(covered - kinds, set(), "a row names an operation kind the intent record does not have")

	def test_every_row_blocks_something_or_says_what_it_invalidates(self):
		for row in recovery.OPERATIONS:
			self.assertTrue(row.blocks and row.owner, row.id)
		for row in recovery.CORRECTIONS:
			self.assertTrue(row.owner and (row.blocks or row.invalidates), row.id)
			self.assertFalse(set(row.blocks) - set(CAPABILITIES), row.id)

	def test_each_row_is_found_for_exactly_the_states_it_applies_in(self):
		for row in recovery.OPERATIONS:
			subject = row.subject + ":probe" if row.subject else "probe"
			for kind in row.kinds:
				for state in ALL_STATES:
					found = recovery.operation_for(kind, subject, state)
					self.assertEqual(found is row, state in row.states, f"{row.id} {kind} {state}")

	def test_a_row_raised_by_a_state_not_an_intent_names_its_condition(self):
		self.assertEqual([r.id for r in recovery.OPERATIONS if not r.kinds], ["R17-06"])
		self.assertEqual(recovery.OPERATIONS[5].condition, "settlement_unconfirmed")

	def test_a_signature_that_is_definitively_refused_blocks_nothing_but_an_unknown_one_does(self):
		self.assertIsNone(recovery.operation_for("Signing attempt", "agreement", "Failed"))
		self.assertEqual(recovery.operation_for("Signing attempt", "agreement", "Uncertain").id, "R17-01")

	def test_a_reversal_never_starts_with_the_receipt(self):
		firsts, thens = zip(*recovery.REVERSAL_ORDER)
		self.assertEqual(set(thens), {"Purchase Receipt"})
		self.assertNotIn("Purchase Receipt", firsts)
