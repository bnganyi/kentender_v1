# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.30 §4.3 — a Need-origin entry starts from the accepted Need's
estimated total cost (PLN30-AC-001 to 008).

The estimate prefills the entry's `indicative_amount` only where none has been
entered, never overwrites an entered amount, is shown beside any change, is frozen
in the certified snapshot and is never summed into a total. Budget Line is never
prefilled."""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import frappe

from kentender_core.services.command_write_guard import maintenance_write
from kentender_procurement.departmental_needs.write_family import NEEDS_WRITE_FAMILY
from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_read, needs_intake
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_dpp_lifecycle import PlanningCommandCase, key

REASON = "The department will defer this requirement to the following financial year."


NEED_V2 = "NEED-PLNT-0001-V2"


class EstimateCase(PlanningCommandCase):
	def successor_revision(self):
		"""A second accepted revision of the fixture Need, so a refresh can pin to it."""
		if not frappe.db.exists("Departmental Need Revision", NEED_V2):
			with maintenance_write(NEEDS_WRITE_FAMILY, reason="Planning test: a successor accepted revision"):
				frappe.get_doc(
					{
						"doctype": "Departmental Need Revision", "need_revision_id": NEED_V2, "departmental_need": fx.NEED,
						"revision_number": 2, "revision_status": "Accepted", "title": "Test requirement",
						"description": "Procure and implement the test requirement.",
						"expected_operational_result": "The department can operate the tested capability.",
						"indicative_quantity": 1, "unit": fx.UNIT, "required_by_date": "2102-05-31", "fixture_namespace": fx.NS,
					}
				).insert(ignore_permissions=True)
		self.addCleanup(self._drop_revision)
		return NEED_V2

	def _drop_revision(self):
		frappe.db.delete("Departmental Plan Entry", {"need_revision": NEED_V2})
		frappe.db.delete("Departmental Need Revision", {"name": NEED_V2})

	def source(self, estimate, *, version=fx.NEED_V1):
		self._sources.stop()
		self._sources = patch.object(
			needs_intake, "current_accepted_sources", return_value=[fx.accepted_source(version=version, estimate=estimate)]
		)
		self._sources.start()
		current = patch.object(needs_intake, "current_accepted_revision_of", return_value=version)
		current.start()
		self.addCleanup(current.stop)

	def entry(self, opened, entry_id=None):
		filters = {"dpp_version": opened["current_version"], "need": fx.NEED}
		if entry_id:
			filters["entry_id"] = entry_id
		return frappe.get_doc("Departmental Plan Entry", filters)

	def fund(self, opened, entry_id, amount, record_version=None):
		frappe.set_user(fx.AUTHOR)
		with patch.object(dpp_lifecycle.budget_gateway, "money_precision", return_value=2):
			return dpp_lifecycle.save_need_funding(
				dpp_version=opened["current_version"], entry_id=entry_id, budget_line=fx.BUDGET_LINE, indicative_amount=amount,
				expected_record_version=record_version or opened["record_version"], idempotency_key=key(),
			)

	def read_row(self, opened, entry_id):
		frappe.set_user(fx.HOD)
		read = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		return next(r for r in read["entries"] if r["entry_id"] == entry_id)


class TestPrefill(EstimateCase):
	def test_an_estimate_starts_the_amount_and_never_the_budget_line(self):
		self.source("80000000")
		opened = self.open_alpha()
		entry = self.entry(opened)
		self.assertEqual(entry.indicative_amount, 80000000)
		self.assertEqual(entry.need_estimated_total_cost, 80000000)
		self.assertFalse(entry.budget_line)
		# still incomplete until a Budget Line is chosen
		row = self.read_row(opened, entry.entry_id)
		self.assertEqual(row["status"], "Funding details needed")
		self.assertEqual(row["amount_display"], "KES 80,000,000")
		self.assertEqual(row["estimate_change_display"], "")

	def test_no_estimate_prefills_nothing(self):
		self.source(None)
		opened = self.open_alpha()
		entry = self.entry(opened)
		self.assertEqual(entry.indicative_amount, 0)
		self.assertEqual(entry.need_estimated_total_cost, 0)
		row = self.read_row(opened, entry.entry_id)
		self.assertEqual(row["amount_display"], "Not entered")
		self.assertEqual(row["need_estimate_display"], "")

	def test_a_v2_replay_with_no_estimate_key_prefills_nothing(self):
		payload = fx.accepted_source()
		payload.pop("estimated_total_cost")
		self.assertEqual(needs_intake._estimate(payload), 0.0)

	def test_an_entered_amount_is_never_overwritten_by_a_successor_revision(self):
		self.source("80000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		funded = self.fund(opened, entry_id, 85000000)
		# a successor revision with a different estimate is accepted
		self.source("90000000", version=self.successor_revision())
		version_doc = frappe.get_doc("Departmental Plan Version", opened["current_version"])
		needs_intake.refresh_draft_entries(version_doc)
		entry = self.entry(opened, entry_id)
		self.assertEqual(entry.indicative_amount, 85000000)  # the department's amount stands
		self.assertEqual(entry.need_estimated_total_cost, 90000000)  # the reference moves
		self.assertTrue(entry.budget_line)
		row = self.read_row({**opened, "record_version": funded["record_version"]}, entry_id)
		self.assertEqual(row["need_estimate_display"], "KES 90,000,000")
		self.assertEqual(row["estimate_change_display"], "−KES 5,000,000")

	def test_an_empty_entry_starts_from_a_successors_estimate(self):
		self.source(None)
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		self.source("45000000", version=self.successor_revision())
		needs_intake.refresh_draft_entries(frappe.get_doc("Departmental Plan Version", opened["current_version"]))
		self.assertEqual(self.entry(opened, entry_id).indicative_amount, 45000000)


class TestChangeDisplay(EstimateCase):
	def test_a_revised_amount_shows_the_accepted_estimate_and_the_signed_change(self):
		self.source("30000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		funded = self.fund(opened, entry_id, 35000000)
		row = self.read_row({**opened, "record_version": funded["record_version"]}, entry_id)
		self.assertEqual(row["need_estimate_display"], "KES 30,000,000")
		self.assertEqual(row["estimate_change_display"], "+KES 5,000,000")

	def test_equal_amounts_show_no_change(self):
		self.source("30000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		funded = self.fund(opened, entry_id, 30000000)
		row = self.read_row({**opened, "record_version": funded["record_version"]}, entry_id)
		self.assertEqual(row["estimate_change_display"], "")

	def test_the_estimate_is_never_summed_into_the_cost_entered_so_far(self):
		self.source("80000000")
		opened = self.open_alpha()
		frappe.set_user(fx.HOD)
		read = dpp_read.get_departmental_plan(dpp_reference=opened["dpp_reference"])
		# a prefilled amount without a Budget Line is not "cost entered so far"
		self.assertNotIn("80,000,000", json.dumps(read.get("totals_caption", "")))

	def test_the_editor_carries_the_prefilled_amount_and_the_reference(self):
		self.source("80000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		frappe.set_user(fx.AUTHOR)
		editor = dpp_read.get_dpp_entry_editor(dpp_reference=opened["dpp_reference"], entry_id=entry_id)
		self.assertEqual(editor["entry"]["indicative_amount"], 80000000)
		self.assertEqual(editor["entry"]["need_estimate_display"], "KES 80,000,000")


class TestExcludeAndRestore(EstimateCase):
	def test_exclusion_clears_the_amount_and_keeps_the_reference_and_restore_starts_from_the_estimate(self):
		self.source("30000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		funded = self.fund(opened, entry_id, 35000000)
		frappe.set_user(fx.AUTHOR)
		marked = dpp_lifecycle.set_need_planning_disposition(
			dpp_version=opened["current_version"], entry_id=entry_id, disposition="Do not proceed", reason=REASON,
			expected_record_version=funded["record_version"], idempotency_key=key(),
		)
		entry = self.entry(opened, entry_id)
		self.assertEqual(entry.indicative_amount, 0)
		self.assertEqual(entry.need_estimated_total_cost, 30000000)
		restored = dpp_lifecycle.set_need_planning_disposition(
			dpp_version=opened["current_version"], entry_id=entry_id, disposition="Restore",
			expected_record_version=marked["record_version"], idempotency_key=key(),
		)
		self.assertEqual(restored["action"], "need_restored")
		entry = self.entry(opened, entry_id)
		self.assertEqual(entry.indicative_amount, 30000000)  # the estimate, never the cleared 35,000,000
		self.assertFalse(entry.budget_line)


class TestCertificationFreezesTheReference(EstimateCase):
	def test_the_submitted_snapshot_carries_the_need_estimate(self):
		self.source("30000000")
		opened = self.open_alpha()
		entry_id = self.entry(opened).entry_id
		funded = self.fund(opened, entry_id, 35000000)
		with patch.object(dpp_lifecycle.budget_gateway, "money_precision", return_value=2):
			self.submit({**opened, "record_version": funded["record_version"]})
		submission = frappe.get_all("Departmental Plan Submission", filters={"dpp_version": opened["current_version"]}, fields=["name", "entry_snapshots"])[0]
		snapshot = json.loads(submission.entry_snapshots)[0]
		self.assertEqual(snapshot["need_estimated_total_cost"], 30000000)
		self.assertEqual(snapshot["indicative_amount"], 35000000)
		# a later change to the live reference cannot alter the frozen figure
		frappe.db.set_value("Departmental Plan Entry", self.entry(opened, entry_id).name, "need_estimated_total_cost", 1)
		frozen = json.loads(frappe.db.get_value("Departmental Plan Submission", submission.name, "entry_snapshots"))[0]
		self.assertEqual(frozen["need_estimated_total_cost"], 30000000)
