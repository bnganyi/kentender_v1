# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.13 proposal, owner decision 1 (16 October 2026): reopening a contract record in Contract Management does not reopen or change its funding.

The funding owner closed the commitment when the contract was closed. Reopening the contract for a correction restores activity in Contract Management only: it asks the funding owner nothing, the
owner's record of the closure is unchanged, and the contract still shows its commitment as closed by the funding owner. A funding change after that goes through Budget's own correction process."""

from __future__ import annotations

import frappe

from kentender_contracts.services import closeout, closure_correction, funding_closure
from kentender_contracts.simulation.funding import LEDGER
from kentender_contracts.tests.test_cm_completion import CompletionCase


class Recorder:
	"""A funding owner that records every call it is asked, and answers none."""

	def __init__(self):
		self.calls: list[str] = []

	def lookup(self, **kw):
		self.calls.append("lookup")

	def convert(self, **kw):
		self.calls.append("convert")

	def adjust(self, **kw):
		self.calls.append("adjust")

	def close(self, **kw):
		self.calls.append("close")

	def recall(self, **kw):
		self.calls.append("recall")


class TestReopeningChangesNoFunding(CompletionCase):
	def setUp(self):
		super().setUp()
		self.completed()
		self.close()

	def funding_rows(self):
		return frappe.get_all(LEDGER, fields=["*"], order_by="creation asc")

	def test_reopening_asks_the_funding_owner_nothing_and_changes_no_funding_record(self):
		rows_before = self.funding_rows()
		state_before = (funding_closure.status(self.case, closeout.CLOSURE_SUBJECT), closeout.funding_state(self.case))
		self.assertEqual(state_before[1], "Commitment closed by the funding owner")

		recorder = Recorder()
		frappe.flags.kt_contract_funding_providers = [recorder]
		self.addCleanup(lambda: setattr(frappe.flags, "kt_contract_funding_providers", None))
		closure_correction.prepare(self.case, fact="Certificate delivery", reason="Delivery was recorded without proof.", evidence_files=[{"label": "Delivery incident", "file": "x"}], submit=True,
			expected_version=self.t.version(), idempotency_key=self.t.key("corr"), actor=self.p["charles"])
		closure_correction.decide(self.case, correction=1, decision="Reopen", reason="Required completion evidence was not established.", survivors=None,
			expected_version=self.t.version(), idempotency_key=self.t.key("dec"), actor=self.p["amina"])

		self.assertEqual(frappe.db.get_value("Contract Case", self.case, "lifecycle"), "Active")
		self.assertEqual(recorder.calls, [], "reopening asked the funding owner for something")
		self.assertEqual(self.funding_rows(), rows_before, "the funding owner's record changed")
		self.assertEqual((funding_closure.status(self.case, closeout.CLOSURE_SUBJECT), closeout.funding_state(self.case)), state_before)
