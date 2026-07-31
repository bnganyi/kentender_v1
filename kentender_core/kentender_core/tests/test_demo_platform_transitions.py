# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demo platform transition probes — run after seed_demo_platform on the site."""

from __future__ import annotations

from frappe.tests.utils import FrappeTestCase

from kentender_core.seeds.demo_platform_seed.transitions import probe_demo_platform_transitions
from kentender_core.seeds.demo_platform_seed.validate import validate_demo_platform_seed


class TestDemoPlatformTransitions(FrappeTestCase):
	def test_validate_and_transitions_when_seeded(self):
		v = validate_demo_platform_seed()
		if not v.get("ok"):
			self.skipTest("Demo platform seed not loaded on this site")
		probes = probe_demo_platform_transitions(mutate=False)
		self.assertTrue(probes.get("ok"), probes.get("failed"))
		names = {p["name"] for p in probes.get("probes") or []}
		self.assertIn("cfg_walkable_home", names)
		self.assertIn("bid_landing_stages", names)
