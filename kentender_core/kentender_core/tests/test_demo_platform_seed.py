# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demo platform seed — PE cleanup + validate invariants (site-scoped)."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.seeds.demo_platform_seed.constants import PE_MOE, PE_MOH
from kentender_core.seeds.demo_platform_seed.pe_cleanup import cleanup_procuring_entities
from kentender_core.seeds.demo_platform_seed.validate import validate_demo_platform_seed


class TestDemoPlatformPeCleanup(FrappeTestCase):
	def test_cleanup_ensures_canonical_entities(self):
		result = cleanup_procuring_entities()
		self.assertTrue(result.get("ok"))
		self.assertTrue(frappe.db.exists("Procuring Entity", PE_MOH))
		self.assertTrue(frappe.db.exists("Procuring Entity", PE_MOE))


class TestDemoPlatformValidateWhenLoaded(FrappeTestCase):
	"""Soft check: if demo pack already loaded on site, validation must pass key PE checks."""

	def test_validate_pe_shape_or_skip(self):
		# Always require PE cleanup shape after cleanup call
		cleanup_procuring_entities()
		v = validate_demo_platform_seed()
		# PE checks must pass even if full pack not loaded
		pe_checks = {
			c["name"]: c["ok"]
			for c in v.get("checks") or []
			if c["name"] in ("pe_moh", "pe_moe", "home_has_pe_moh", "home_has_pe_moe")
		}
		self.assertTrue(pe_checks.get("pe_moh"))
		self.assertTrue(pe_checks.get("pe_moe"))
		self.assertTrue(pe_checks.get("home_has_pe_moh"))
		self.assertTrue(pe_checks.get("home_has_pe_moe"))
