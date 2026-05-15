# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0700 — security seed fixtures (users + NEG-SEC cases)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.permissions.seed_security_fixtures_0700 import (
	FIXTURE_USERS,
	NEGATIVE_ACCESS_CASES,
	negative_access_cases,
	upsert_security_seed_fixtures,
)


class TestSecSecuritySeedFixtures0700(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_sec_0700_seed_idempotent_and_users_exist(self) -> None:
		r1 = upsert_security_seed_fixtures()
		self.assertTrue(r1["ok"])
		self.assertEqual(r1["users_total"], 9)
		self.assertEqual(r1["negative_cases_total"], 8)

		for spec in FIXTURE_USERS:
			email = spec["email"]
			actor_user_code = spec["actor_user_code"]
			name = frappe.db.get_value("User", {"email": email}, "name")
			self.assertTrue(name, msg=f"Missing fixture user for {actor_user_code}")
			row = frappe.db.get_value("User", name, ["enabled", "user_type", "username"], as_dict=True)
			self.assertEqual(int(row.get("enabled") or 0), 1)
			self.assertEqual((row.get("user_type") or "").strip(), "System User")
			self.assertEqual((row.get("username") or "").strip(), actor_user_code)

		r2 = upsert_security_seed_fixtures()
		self.assertTrue(r2["ok"])
		self.assertEqual(r2["users_created"], 0)

	def test_sec_0700_negative_cases_match_pack(self) -> None:
		cases = negative_access_cases()
		self.assertEqual(len(cases), 8)
		self.assertEqual({c["case_code"] for c in cases}, {f"NEG-SEC-00{i}" for i in range(1, 9)})

		index = {c["case_code"]: c for c in cases}
		self.assertEqual(index["NEG-SEC-001"]["expected_denial_code"], "RELEASE_PERMISSION_DENIED")
		self.assertEqual(index["NEG-SEC-004"]["expected_denial_code"], "PUBLISH_PERMISSION_DENIED")
		self.assertEqual(index["NEG-SEC-006"]["expected_denial_code"], "BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION")
		self.assertEqual(index["NEG-SEC-007"]["expected_denial_code"], "MANUAL_EVALUATION_CRITERIA_DENIED")

	def test_sec_0700_negative_cases_reference_fixture_users(self) -> None:
		user_codes = {u["actor_user_code"] for u in FIXTURE_USERS}
		for case in NEGATIVE_ACCESS_CASES:
			with self.subTest(case_code=case["case_code"]):
				self.assertIn(case["actor_user_code"], user_codes)
				self.assertTrue(case["action_code"].strip())
				self.assertTrue(case["expected_denial_code"].strip())
