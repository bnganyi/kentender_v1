# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 1 scope baseline.

Anchors the controlling scope markdown (§19 ``OFFICER-SCOPE-AC-*``, §21 boundary
prompt, §22 exit). Full acceptance evidence for ``OFFICER-SCOPE-AC-*`` is delivered
in later officer steps per tracker.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step1_scope_baseline
"""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	OFFICER_FLOW_TENDER_STATUSES,
	OFFICER_SCOPE_BOUNDARY_FORBIDDEN_PHRASES,
	OFFICER_UX_PREVIEW_GENERATED,
	OFFICER_UX_READY_FOR_REVIEW,
	TENDER_STATUS_POC_DEMONSTRATED,
	TENDER_STATUS_TENDER_PACK_GENERATED,
	officer_ux_label_to_tender_status,
	tender_status_to_officer_ux_label,
)


def _officer_scope_document_path() -> Path:
	repo_v1 = Path(__file__).resolve().parents[4]
	return (
		repo_v1
		/ "docs"
		/ "prompts"
		/ "std poc"
		/ "tender configuration"
		/ "1. procurement_officer_tender_configuration_poc_scope_document.md"
	)


REQUIRED_ANCHORS: tuple[str, ...] = (
	"## 19. Acceptance Criteria",
	"OFFICER-SCOPE-AC-001",
	"## 21. Cursor Boundary Prompt for Later Implementation",
	"This workstream is the Procurement Officer Tender Configuration POC only.",
	"## 22. Exit Condition",
)


class TestOfficerPocStep1ScopeBaseline(UnitTestCase):
	def test_officer_scope_document_exists_with_stable_anchors(self) -> None:
		path = _officer_scope_document_path()
		self.assertTrue(path.is_file(), f"Expected scope doc at {path}")
		text = path.read_text(encoding="utf-8")
		for anchor in REQUIRED_ANCHORS:
			with self.subTest(anchor=anchor):
				self.assertIn(anchor, text)

	def test_boundary_prompt_lists_core_forbidden_streams(self) -> None:
		path = _officer_scope_document_path()
		text = path.read_text(encoding="utf-8")
		for phrase in OFFICER_SCOPE_BOUNDARY_FORBIDDEN_PHRASES:
			with self.subTest(phrase=phrase):
				self.assertIn(phrase, text)

	def test_tender_status_to_ux_label_planning_map(self) -> None:
		self.assertEqual(tender_status_to_officer_ux_label("Draft"), "Draft")
		self.assertEqual(tender_status_to_officer_ux_label("Configured"), "Configuring")
		self.assertEqual(tender_status_to_officer_ux_label("Validation Failed"), "Validation Failed")
		self.assertEqual(tender_status_to_officer_ux_label("Validated"), "Validated")
		self.assertEqual(
			tender_status_to_officer_ux_label("Tender Pack Generated"),
			OFFICER_UX_PREVIEW_GENERATED,
		)
		self.assertEqual(
			tender_status_to_officer_ux_label("POC Demonstrated"),
			OFFICER_UX_READY_FOR_REVIEW,
		)

	def test_ux_label_to_tender_status_round_trip_for_officer_flow(self) -> None:
		for status in OFFICER_FLOW_TENDER_STATUSES:
			label = tender_status_to_officer_ux_label(status)
			back = officer_ux_label_to_tender_status(label)
			with self.subTest(status=status, label=label):
				self.assertEqual(back, status)
		self.assertEqual(
			officer_ux_label_to_tender_status(OFFICER_UX_PREVIEW_GENERATED),
			TENDER_STATUS_TENDER_PACK_GENERATED,
		)
		self.assertEqual(
			officer_ux_label_to_tender_status(OFFICER_UX_READY_FOR_REVIEW),
			TENDER_STATUS_POC_DEMONSTRATED,
		)
