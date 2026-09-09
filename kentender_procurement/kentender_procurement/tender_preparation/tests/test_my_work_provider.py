# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""My Work rows for Tender Preparation — read-offer parity with the gates."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_preparation.services import lifecycle, my_work_provider
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase


class TestMyWorkRows(TenderCase):
	def test_the_head_sees_the_approval_task_and_nobody_else_does(self):
		sub = fx.submitted()
		rows = my_work_provider.my_work_rows(user=fx.HOPF)["assigned"]
		self.assertEqual([r["task_id"] for r in rows], [sub["task"]])
		self.assertEqual(rows[0]["route"], ["tender-preparation", "task", sub["task"]])
		for user in (fx.OFFICER, fx.AUDITOR, fx.OUTSIDER):
			self.assertEqual([r for r in my_work_provider.my_work_rows(user=user)["assigned"] if r["task_type"] == "tender_preparation.approval"], [], user)

	def test_a_returned_draft_reaches_the_officer(self):
		sub = fx.submitted()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Prepared Tender", sub["tender"])
		lifecycle.return_tender_for_correction(task=sub["task"], reason="Please correct the submission deadline before approval.", expected_record_version=root.record_version, idempotency_key=fx.key())
		rows = my_work_provider.my_work_rows(user=fx.OFFICER)["assigned"]
		self.assertEqual([r["task_type"] for r in rows], ["tender_preparation.correction"])
		self.assertEqual(rows[0]["route"], ["tender-preparation", sub["tender"]])
		self.assertEqual(my_work_provider.my_work_rows(user=fx.HOPF)["assigned"], [])

	def test_the_provider_is_hooked(self):
		self.assertIn("kentender_procurement.tender_preparation.services.my_work_provider.my_work_rows", frappe.get_hooks("kt_my_work_providers"))
