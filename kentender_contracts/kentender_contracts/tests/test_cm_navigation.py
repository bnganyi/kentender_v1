# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FU-CM-58: Contract Management takes over the rail slot reserved for it through core's `kt_navigation_overrides` hook, and nothing else."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts import navigation
from kentender_core.services import navigation_overrides as nav


class TestNavigation(IntegrationTestCase):
	def test_the_app_declares_the_hook_and_it_replaces_only_its_own_slot_and_route(self):
		self.assertIn("kentender_contracts.navigation.overrides", frappe.get_hooks(nav.HOOK))
		payload = navigation.overrides()
		self.assertEqual(list(payload), ["Procurement"])
		self.assertEqual(list(payload["Procurement"]["items"]), ["Contract Management"])
		self.assertEqual(payload["Procurement"]["routes"], ["contracts"])
		self.assertTrue(frappe.db.exists("Page", "contracts"), "the slot points at a Page this app ships")

	def test_every_field_it_overrides_is_one_core_allows(self):
		fields = navigation.overrides()["Procurement"]["items"]["Contract Management"]
		self.assertLessEqual(set(fields), set(nav.LINK_FIELDS))
