# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Section 11 — TM2 workbench terminology simplification mappings."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.services.tm2_workbench_terminology import (
	business_label_for_audit_event,
	business_label_for_checklist_row,
	business_label_for_denial_code,
	business_label_for_derived_output,
	business_label_for_output_field,
	business_label_for_queue_slug,
	business_label_for_technical_term,
	business_label_for_tender_status,
	format_denied_action_display_line,
	format_lifecycle_audit_display_line,
)


class TestTm2WorkbenchTerminology(UnitTestCase):
	def test_technical_terms_map_to_business_labels(self) -> None:
		self.assertIn("package", business_label_for_technical_term("Bundle").lower())
		self.assertIn("checklist", business_label_for_technical_term("DSM").lower())
		self.assertIn("opening", business_label_for_technical_term("DOM").lower())
		self.assertIn("evaluation", business_label_for_technical_term("DEM").lower())
		self.assertIn("contract", business_label_for_technical_term("DCM").lower())

	def test_tender_status_simplification(self) -> None:
		label = business_label_for_tender_status("STD Instance Incomplete")
		self.assertNotIn("STD", label)
		self.assertIn("document", label.lower())

	def test_checklist_rows_avoid_raw_tokens(self) -> None:
		for row_id in ("bundle_current", "dsm_current", "dom_current", "dem_current", "dcm_current"):
			label = business_label_for_checklist_row(row_id, "fallback")
			self.assertNotIn("current", label.lower())
			for token in ("Bundle", "DSM", "DOM", "DEM", "DCM"):
				self.assertNotIn(token, label)

	def test_derived_output_labels(self) -> None:
		self.assertEqual(
			business_label_for_derived_output("dem", "DEM"),
			business_label_for_technical_term("DEM"),
		)

	def test_output_field_labels(self) -> None:
		self.assertIn("package", business_label_for_output_field("bundle_output_code").lower())
		self.assertIn("snapshot", business_label_for_output_field("publication_snapshot_code").lower())

	def test_queue_slug_std_incomplete(self) -> None:
		label = business_label_for_queue_slug("std-incomplete")
		self.assertNotIn("STD", label)
		self.assertIn("document", label.lower())

	def test_audit_event_labels_hide_internal_tokens(self) -> None:
		label = business_label_for_audit_event("Tender STD Bound")
		self.assertNotIn("STD", label)
		self.assertIn("document", label.lower())

	def test_lifecycle_audit_line_uses_business_labels(self) -> None:
		line = format_lifecycle_audit_display_line(
			"19-05-2026 00:17:34",
			"Tender STD Bound",
			"Draft",
			"STD Instance Incomplete",
		)
		self.assertIn("Official document linked", line)
		self.assertIn("Document setup incomplete", line)
		self.assertNotIn("STD Bound", line)
		self.assertNotIn("STD Instance", line)

	def test_denial_code_labels_hide_internal_tokens(self) -> None:
		label = business_label_for_denial_code("AUTH_SEALED_BID_DENIED")
		self.assertNotIn("AUTH_", label)
		self.assertIn("sealed", label.lower())

	def test_denied_action_display_line_uses_business_labels(self) -> None:
		line = format_denied_action_display_line(
			"proc@example.com",
			"BID2_VIEW_SEALED_CONTENT",
			"AUTH_SEALED_BID_DENIED",
		)
		self.assertIn("proc@example.com", line)
		self.assertNotIn("BID2_", line)
		self.assertNotIn("AUTH_", line)
		self.assertIn("sealed", line.lower())
