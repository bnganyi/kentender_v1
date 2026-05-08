# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0110 — action availability contract for library header actions."""

from __future__ import annotations

from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.std_library_action_availability import (
	ACTION_IMPORT,
	ACTION_REGISTER_SOURCE,
	ACTION_VALIDATE_LIBRARY,
	get_std_library_action_availability,
)


class TestStdLibraryActionAvailabilityStdLib0110(IntegrationTestCase):
	def test_returns_required_keys_for_default_actions(self) -> None:
		out = get_std_library_action_availability()
		self.assertTrue(out.get("ok"))
		actions = out.get("actions") or []
		codes = {row.get("action_code") for row in actions}
		self.assertTrue({ACTION_IMPORT, ACTION_REGISTER_SOURCE, ACTION_VALIDATE_LIBRARY}.issubset(codes))

		for row in actions:
			self.assertIn("action_code", row)
			self.assertIn("allowed", row)
			self.assertIn("denial_code", row)
			self.assertIn("message", row)
			self.assertIn("requires_confirmation", row)
			self.assertIn("risk_level", row)

	def test_denies_when_user_has_no_matching_roles(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_action_availability.frappe.get_roles",
			return_value=["Accounts User"],
		):
			out = get_std_library_action_availability([ACTION_IMPORT])
		actions = out.get("actions") or []
		self.assertEqual(len(actions), 1)
		row = actions[0]
		self.assertEqual(row.get("action_code"), ACTION_IMPORT)
		self.assertFalse(row.get("allowed"))
		self.assertEqual(row.get("denial_code"), "STD_AUTH_PERMISSION_DENIED")
		self.assertIn("Unavailable", str(row.get("message") or ""))

	def test_allows_import_when_codes_are_passed_as_comma_string(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_action_availability.frappe.get_roles",
			return_value=["Administrator"],
		):
			out = get_std_library_action_availability(
				"IMPORT_OFFICIAL_STD_PACKAGE,REGISTER_SOURCE_DOCUMENT,VALIDATE_LIBRARY"
			)
		actions = out.get("actions") or []
		by_code = {str(row.get("action_code")): row for row in actions}
		self.assertTrue(by_code[ACTION_IMPORT].get("allowed"))
		self.assertTrue(by_code[ACTION_REGISTER_SOURCE].get("allowed"))
		self.assertTrue(by_code[ACTION_VALIDATE_LIBRARY].get("allowed"))

	def test_allows_import_when_codes_are_json_array_string(self) -> None:
		with patch(
			"kentender_procurement.tender_management.api.std_library_action_availability.frappe.get_roles",
			return_value=["Administrator"],
		):
			out = get_std_library_action_availability(
				'["IMPORT_OFFICIAL_STD_PACKAGE","REGISTER_SOURCE_DOCUMENT","VALIDATE_LIBRARY"]'
			)
		actions = out.get("actions") or []
		by_code = {str(row.get("action_code")): row for row in actions}
		self.assertTrue(by_code[ACTION_IMPORT].get("allowed"))
		self.assertTrue(by_code[ACTION_REGISTER_SOURCE].get("allowed"))
		self.assertTrue(by_code[ACTION_VALIDATE_LIBRARY].get("allowed"))
