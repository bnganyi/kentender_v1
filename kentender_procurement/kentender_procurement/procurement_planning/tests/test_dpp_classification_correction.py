# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §4.4 / §5.1.6 — accepted-classification derivation and
the Planning-owned correction of it (PLN21-AC-001..006).

Two things are being protected here.

**Derivation.** The Planner picks a requirement type; the server picks the
category from the same governed catalogue entry. A caller that tries to supply
a category is refused rather than quietly ignored, because silently dropping it
would let the caller believe it had been honoured.

**Immutability with an escape hatch.** An accepted classification is evidence
and never changes. When it turns out to be wrong, a correction is *appended*,
and what happens next depends entirely on what already consumed the source:
nothing, a Draft item, a governed Plan, or an item whose procurement has
already been authorised. Those four outcomes are the feature.
"""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	budget_gateway,
	dpp_classification,
	dpp_lifecycle,
	dpp_validation,
	needs_intake,
	plan_workbench,
)
from kentender_procurement.procurement_planning.tests import fixtures as fx


def key() -> str:
	return uuid4().hex


REASON = "The requirement is for a managed technical service and contains no construction work."


class ClassificationCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_planning_rows()
		self.addCleanup(frappe.set_user, "Administrator")
		for target, value, result in (
			(budget_gateway, "eligible_line_ids", {fx.BUDGET_LINE}),
			(needs_intake, "current_accepted_sources", []),
		):
			patched = patch.object(target, value, return_value=result)
			patched.start()
			self.addCleanup(patched.stop)

	def accepted(self, *, requirement_type: str = "Works") -> tuple[str, str]:
		"""An accepted submission with one proceeding direct entry.

		Returns `(submission_name, entry_id)`.
		"""
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN,
			idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		dpp_validation.accept_departmental_plan(
			task=task.name, classifications={added["entry_id"]: requirement_type},
			task_token=task.task_token, idempotency_key=key(),
		)
		return task.submission, added["entry_id"]

	def form(self, entry: str) -> dict:
		"""Form one Draft item from a single accepted entry."""
		frappe.set_user(fx.PLANNER)
		version = frappe.db.get_value("Annual Plan", {"fiscal_year": fx.FY_OPEN}, "open_successor_version")
		return plan_workbench.form_plan_items(
			plan_version=frappe.db.get_value("Annual Plan Version", version, "version_reference"),
			dpp_entries=[entry], mode="each",
			expected_record_version=frappe.db.get_value("Annual Plan Version", version, "record_version"),
			idempotency_key=key(),
		)

	def head(self, submission: str, entry_id: str) -> str:
		return dpp_classification.effective_classification(submission, entry_id)["evidence_id"]

	def correct(self, submission, entry_id, *, new_type="Non-consulting services", reason=REASON, expected=None, user=fx.PLANNER):
		frappe.set_user(user)
		return dpp_classification.correct_accepted_requirement_classification(
			dpp_submission=submission, dpp_entry_id=entry_id,
			expected_evidence_id=expected if expected is not None else self.head(submission, entry_id),
			new_requirement_type=new_type, reason=reason, idempotency_key=key(),
		)


class TestServerSideDerivation(ClassificationCase):
	"""PLN21-AC-001."""

	def test_the_category_comes_from_the_governed_catalogue_entry(self):
		for requirement_type, expected in (
			("Goods", "Goods"),
			("Works", "Works"),
			("Non-consulting services", "Services"),
			("Consulting services", "Services"),
		):
			self.assertEqual(dpp_classification.category_for(requirement_type), expected)

	def test_acceptance_freezes_both_the_selected_type_and_the_derived_category(self):
		submission, entry_id = self.accepted(requirement_type="Works")
		decision = frappe.get_doc(
			"Departmental Plan Validation Decision",
			{"submission": submission, "decision": "Accept departmental plan"},
		)
		self.assertEqual(json.loads(decision.classifications), {entry_id: "Works"})
		self.assertEqual(json.loads(decision.derived_categories), {entry_id: "Works"})

	def test_a_client_supplied_category_is_rejected_not_ignored(self):
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(
			organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN,
			idempotency_key=key(), fixture_namespace=fx.NS,
		)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True,
			expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementPlanningError) as caught:
			dpp_validation.accept_departmental_plan(
				task=task.name, classifications={added["entry_id"]: "Goods"},
				task_token=task.task_token, idempotency_key=key(),
				procurement_category="Works",
			)
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_INCOMPLETE")

	def test_an_unknown_or_retired_type_fails_the_whole_acceptance(self):
		frappe.db.set_value("Requirement Type", "Consulting services", "status", "Retired", update_modified=False)
		self.addCleanup(
			frappe.db.set_value, "Requirement Type", "Consulting services", "status", "Active", update_modified=False
		)
		with self.assertRaises(ProcurementPlanningError):
			self.accepted(requirement_type="Consulting services")


class TestCorrectionGuards(ClassificationCase):
	"""PLN21-AC-003."""

	def test_a_correction_appends_immutable_evidence_and_shifts_the_projection(self):
		submission, entry_id = self.accepted()
		before = dpp_classification.effective_classification(submission, entry_id)
		self.assertEqual((before["requirement_type"], before["procurement_category"]), ("Works", "Works"))
		self.assertFalse(before["corrected"])

		result = self.correct(submission, entry_id)
		self.assertEqual(result["previous_requirement_type"], "Works")
		self.assertEqual(result["new_requirement_type"], "Non-consulting services")
		self.assertEqual(result["new_procurement_category"], "Services")

		after = dpp_classification.effective_classification(submission, entry_id)
		self.assertEqual((after["requirement_type"], after["procurement_category"]), ("Non-consulting services", "Services"))
		self.assertTrue(after["corrected"])
		# The accepted decision is untouched evidence.
		self.assertEqual(after["original"]["requirement_type"], "Works")
		decision = frappe.get_doc(
			"Departmental Plan Validation Decision",
			{"submission": submission, "decision": "Accept departmental plan"},
		)
		self.assertEqual(json.loads(decision.classifications), {entry_id: "Works"})

	def test_a_recorded_correction_cannot_be_edited_or_deleted(self):
		submission, entry_id = self.accepted()
		self.correct(submission, entry_id)
		frappe.set_user("Administrator")
		correction = frappe.get_doc("DPP Classification Correction", {"dpp_entry_id": entry_id})
		correction.reason = "A different reason entirely, long enough to pass validation."
		with self.assertRaises(ProcurementPlanningError):
			correction.save(ignore_permissions=True)
		with self.assertRaises(ProcurementPlanningError):
			frappe.delete_doc("DPP Classification Correction", correction.name, ignore_permissions=True)

	def test_an_unchanged_type_is_rejected(self):
		submission, entry_id = self.accepted()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.correct(submission, entry_id, new_type="Works")
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_UNCHANGED")

	def test_a_stale_evidence_head_is_rejected_and_writes_nothing(self):
		submission, entry_id = self.accepted()
		stale = self.head(submission, entry_id)
		self.correct(submission, entry_id, new_type="Goods")
		before = frappe.db.count("DPP Classification Correction", {"dpp_entry_id": entry_id})
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.correct(submission, entry_id, new_type="Consulting services", expected=stale)
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_CORRECTION_STALE")
		self.assertEqual(frappe.db.count("DPP Classification Correction", {"dpp_entry_id": entry_id}), before)

	def test_a_short_reason_is_rejected(self):
		submission, entry_id = self.accepted()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.correct(submission, entry_id, reason="too short")
		self.assertEqual(caught.exception.code, "PLN_ENTRY_INCOMPLETE")

	def test_an_entry_with_no_accepted_classification_cannot_be_corrected(self):
		submission, _entry_id = self.accepted()
		with self.assertRaises(ProcurementPlanningError) as caught:
			self.correct(submission, "DPPE-DOES-NOT-EXIST", expected="whatever")
		self.assertEqual(caught.exception.code, "PLN_CLASSIFICATION_CORRECTION_BLOCKED")

	def test_only_the_planner_may_correct(self):
		submission, entry_id = self.accepted()
		with self.assertRaises(Exception):
			self.correct(submission, entry_id, user=fx.AUTHOR)
		self.assertEqual(frappe.db.count("DPP Classification Correction", {"dpp_entry_id": entry_id}), 0)

	def test_corrections_chain_and_keep_their_order(self):
		submission, entry_id = self.accepted()
		self.correct(submission, entry_id, new_type="Goods")
		self.correct(submission, entry_id, new_type="Non-consulting services")
		history = dpp_classification.correction_history(submission, entry_id)
		self.assertEqual([h["requirement_type"] for h in history], ["Goods", "Non-consulting services"])
		self.assertEqual(history[1]["supersedes_evidence_id"], history[0]["evidence_id"])
		current = dpp_classification.effective_classification(submission, entry_id)
		self.assertEqual(current["requirement_type"], "Non-consulting services")


class TestAffectedWorkRecovery(ClassificationCase):
	"""PLN21-AC-004 and AC-005 — the four outcomes."""

	def test_an_unallocated_source_simply_becomes_available_corrected(self):
		submission, entry_id = self.accepted()
		result = self.correct(submission, entry_id)
		self.assertEqual(result["recovery"], dpp_classification.RECOVERY_NONE)
		self.assertEqual(result["draft_items"], [])
		self.assertEqual(result["governed_items"], [])
		self.assertEqual(result["locked_items"], [])

	def test_a_draft_item_is_marked_source_correction_required_and_nothing_is_rewritten(self):
		submission, entry_id = self.accepted()
		frappe.set_user(fx.PLANNER)
		entry = frappe.db.get_value("Departmental Plan Entry", {"entry_id": entry_id}, "name")
		formed = self.form(entry)
		item_id = formed["created_items"][0]
		item = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": item_id},
			["requirement_type", "procurement_category"], as_dict=True,
		)
		self.assertEqual((item.requirement_type, item.procurement_category), ("Works", "Works"))
		self.assertFalse(dpp_classification.source_correction_required(item_id))

		result = self.correct(submission, entry_id)
		self.assertEqual(result["recovery"], dpp_classification.RECOVERY_REFORM_DRAFT)
		self.assertEqual([row["plan_item_id"] for row in result["draft_items"]], [item_id])
		# The item keeps its exact classification: nothing is silently replaced.
		after = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": item_id},
			["requirement_type", "procurement_category"], as_dict=True,
		)
		self.assertEqual((after.requirement_type, after.procurement_category), ("Works", "Works"))
		# But it is now flagged for re-formation.
		self.assertTrue(dpp_classification.source_correction_required(item_id))

	def test_the_allocation_snapshot_is_never_rewritten_by_a_later_correction(self):
		submission, entry_id = self.accepted()
		frappe.set_user(fx.PLANNER)
		entry = frappe.db.get_value("Departmental Plan Entry", {"entry_id": entry_id}, "name")
		self.form(entry)
		allocation = frappe.db.get_value(
			"Plan Source Allocation", {"dpp_entry": entry},
			["classification_evidence", "classification_requirement_type", "classification_procurement_category"],
			as_dict=True,
		)
		self.assertTrue(allocation.classification_evidence)
		self.assertEqual(allocation.classification_requirement_type, "Works")

		self.correct(submission, entry_id)
		after = frappe.db.get_value(
			"Plan Source Allocation", {"dpp_entry": entry},
			["classification_evidence", "classification_requirement_type"], as_dict=True,
		)
		self.assertEqual(after.classification_evidence, allocation.classification_evidence)
		self.assertEqual(after.classification_requirement_type, "Works")

	def test_re_formation_after_a_correction_uses_the_corrected_classification(self):
		submission, entry_id = self.accepted()
		frappe.set_user(fx.PLANNER)
		entry = frappe.db.get_value("Departmental Plan Entry", {"entry_id": entry_id}, "name")
		formed = self.form(entry)
		self.correct(submission, entry_id)
		frappe.set_user(fx.PLANNER)
		item_name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": formed["created_items"][0]}, "name")
		plan_workbench.dissolve_plan_item(
			plan_item=formed["created_items"][0],
			expected_record_version=frappe.db.get_value("Annual Plan Item", item_name, "record_version"),
			idempotency_key=key(),
		)
		reformed = self.form(entry)
		item = frappe.db.get_value(
			"Annual Plan Item", {"plan_item_id": reformed["created_items"][0]},
			["requirement_type", "procurement_category"], as_dict=True,
		)
		self.assertEqual((item.requirement_type, item.procurement_category), ("Non-consulting services", "Services"))
		self.assertFalse(dpp_classification.source_correction_required(reformed["created_items"][0]))


class TestClassificationRead(ClassificationCase):
	"""PLN21-AC-002 / §7.1 `GetAcceptedDPPClassification`."""

	def test_the_read_returns_original_effective_and_history_with_the_catalogue(self):
		submission, entry_id = self.accepted()
		self.correct(submission, entry_id)
		frappe.set_user(fx.PLANNER)
		read = dpp_classification.get_accepted_dpp_classification(dpp_submission=submission)
		self.assertTrue(read["can_correct"])
		self.assertEqual(
			{row["requirement_type"] for row in read["requirement_types"]},
			{"Goods", "Works", "Consulting services", "Non-consulting services"},
		)
		row = next(r for r in read["rows"] if r["dpp_entry_id"] == entry_id)
		self.assertTrue(row["can_correct"])
		self.assertEqual(row["classification"]["requirement_type"], "Non-consulting services")
		self.assertEqual(row["classification"]["original"]["requirement_type"], "Works")
		self.assertEqual(len(row["classification"]["corrections"]), 1)

	def test_a_technical_reader_sees_the_evidence_but_is_offered_no_correction(self):
		submission, entry_id = self.accepted()
		frappe.set_user("Administrator")
		read = dpp_classification.get_accepted_dpp_classification(dpp_submission=submission)
		self.assertFalse(read["can_correct"])
		self.assertTrue(read["rows"])
