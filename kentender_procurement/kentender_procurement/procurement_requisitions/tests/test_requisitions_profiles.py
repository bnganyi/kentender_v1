# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §16.4A — the thirteen named demo-data profiles.

A static contract (exactly the spec's thirteen names, each documented, only
published services used) and, on a seeded site, every profile loaded in turn
with every observed result green, then the §16.4 base restored.

Heavy by design: each load returns the item to a clean namespace (a Planning
rebuild when an earlier profile locked or held the item). Run it on its own,
never beside a Playwright run.
"""

from __future__ import annotations

import ast
import os
import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.seeds import kentender_mvp_v1 as base
from kentender_procurement.procurement_requisitions.seeds import profiles

SPEC_PROFILES = (
	"REQ-SC-HOLD", "REQ-SC-MULTIPLE-REQUESTS", "REQ-SC-CORRECTION-RESOLVED", "REQ-SC-CLOSED-NO-CHANGE", "REQ-SC-OUTCOME-ORDERING",
	"REQ-SC-SHARED-LINE-SHORT", "REQ-SC-SCOPE-LOCK", "REQ-SC-SEQUENTIAL", "REQ-SC-LEAD-CHANGE", "REQ-SC-REVOKE-CONSUME-RACE",
	"REQ-SC-PRECISION", "REQ-SC-COMPATIBILITY", "REQ-SC-OPEN-SLOT",
)
SOURCE = os.path.abspath(profiles.__file__)


def _world_available() -> bool:
	try:
		base.verify_prerequisites()
		return True
	except Exception:
		return False


class TestProfileContract(IntegrationTestCase):
	def test_exactly_the_spec_profiles_in_spec_order(self):
		self.assertEqual(tuple(profiles.PROFILES), SPEC_PROFILES)

	def test_every_profile_is_documented_for_the_list_target(self):
		self.assertTrue(all(row["summary"] for row in profiles.list_profiles()))

	def test_profiles_touch_other_modules_only_through_published_services(self):
		tree = ast.parse(open(SOURCE, encoding="utf-8").read())
		modules = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
		self.assertFalse(any(".doctype" in m for m in modules), modules)
		source = open(SOURCE, encoding="utf-8").read()
		# the only direct write is Requisitions' own stop-decision clock
		writes = [line.strip() for line in source.splitlines() if "frappe.db.set_value(" in line]
		self.assertEqual(len(writes), 1)
		self.assertIn('"Requisition Decision"', writes[0])

	def test_an_unknown_profile_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			profiles.load_profile(profile="REQ-SC-NOT-A-PROFILE", commit=False)


@unittest.skipUnless(_world_available(), "the canonical Requisitions world is not seeded (make seed-canonical THROUGH=requisitions)")
class TestEveryProfile(IntegrationTestCase):
	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		profiles.restore_base(commit=False)
		super().tearDownClass()

	def _load(self, name: str) -> None:
		frappe.set_user("Administrator")
		report = profiles.load_profile(profile=name, commit=False)
		failed = [row for row in report["results"] if not row["ok"]]
		self.assertEqual(failed, [], name)
		self.assertTrue(report["results"], f"{name} observed nothing")
		self.assertEqual(frappe.defaults.get_global_default(profiles.LOADED_KEY), name)


for _name in SPEC_PROFILES:
	setattr(TestEveryProfile, f"test_{_name.lower().replace('-', '_')}", lambda self, n=_name: self._load(n))
