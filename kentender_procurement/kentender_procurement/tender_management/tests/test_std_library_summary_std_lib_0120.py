# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0120 — summary API contract for library cards."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api import std_library_summary as summary_api


class TestStdLibrarySummaryStdLib0120(IntegrationTestCase):
	def test_summary_contract_keys_and_non_negative_ints(self) -> None:
		out = summary_api.get_std_library_summary_counts()
		for key in (
			"active_count",
			"needs_attention_count",
			"ready_for_review_count",
			"superseded_count",
			"package_import_count",
			"bundle_issue_count",
		):
			self.assertIn(key, out)
			self.assertIsInstance(out[key], int)
			self.assertGreaterEqual(out[key], 0)

	def test_summary_count_mapping_uses_expected_status_groups(self) -> None:
		with (
			patch.object(summary_api, "_count_by_lifecycle") as m_lifecycle,
			patch.object(summary_api, "_count_needs_attention") as m_attention,
			patch.object(summary_api, "_count_by_validation") as m_validation,
		):
			def lifecycle_side_effect(statuses):
				mapping = {
					(summary_api.gov.STATUS_ACTIVE,): 9,
					(
						summary_api.gov.STATUS_VALIDATED,
						summary_api.gov.STATUS_SUBMITTED,
						summary_api.gov.STATUS_APPROVED,
					): 5,
					(summary_api.gov.STATUS_SUPERSEDED,): 2,
					(summary_api.gov.STATUS_IMPORTED,): 7,
				}
				return mapping.get(tuple(statuses), 0)

			m_lifecycle.side_effect = lifecycle_side_effect
			m_attention.return_value = 4
			m_validation.return_value = 3

			out = summary_api.get_std_library_summary_counts()

		self.assertEqual(out["active_count"], 9)
		self.assertEqual(out["needs_attention_count"], 4)
		self.assertEqual(out["ready_for_review_count"], 5)
		self.assertEqual(out["superseded_count"], 2)
		self.assertEqual(out["package_import_count"], 7)
		self.assertEqual(out["bundle_issue_count"], 3)
