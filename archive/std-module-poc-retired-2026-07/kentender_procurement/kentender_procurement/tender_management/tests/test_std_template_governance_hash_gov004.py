# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-004 — governance constants and package hash helpers (doc 7 §§11–12).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_hash_gov004
"""

from __future__ import annotations

import json

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov


class TestStdTemplateGovernanceHashGov004(IntegrationTestCase):
	def test_std_gov_004_section_11_constants_exact(self) -> None:
		self.assertEqual(gov.STATUS_IMPORTED, "Imported")
		self.assertEqual(gov.STATUS_VALIDATION_FAILED, "Validation Failed")
		self.assertEqual(gov.STATUS_VALIDATED, "Validated")
		self.assertEqual(gov.STATUS_SUBMITTED, "Submitted for Approval")
		self.assertEqual(gov.STATUS_RETURNED, "Returned for Correction")
		self.assertEqual(gov.STATUS_REJECTED, "Rejected")
		self.assertEqual(gov.STATUS_APPROVED, "Approved")
		self.assertEqual(gov.STATUS_ACTIVE, "Active")
		self.assertEqual(gov.STATUS_SUSPENDED, "Suspended")
		self.assertEqual(gov.STATUS_SUPERSEDED, "Superseded")
		self.assertEqual(gov.STATUS_RETIRED, "Retired")
		self.assertEqual(gov.STATUS_ARCHIVED, "Archived")

		self.assertEqual(gov.VALIDATION_NOT_RUN, "Not Run")
		self.assertEqual(gov.VALIDATION_PASS, "Pass")
		self.assertEqual(gov.VALIDATION_PASS_WARNINGS, "Pass with Warnings")
		self.assertEqual(gov.VALIDATION_BLOCKED, "Blocked")
		self.assertEqual(gov.VALIDATION_FAILED, "Failed")

		self.assertEqual(gov.HASH_ALGORITHM, "SHA-256")
		self.assertEqual(gov.CANONICALIZATION_VERSION, "V1")

	def test_std_gov_004_protected_and_controlled_sets(self) -> None:
		self.assertEqual(
			gov.PROTECTED_STATES,
			frozenset(
				{
					gov.STATUS_SUBMITTED,
					gov.STATUS_REJECTED,
					gov.STATUS_APPROVED,
					gov.STATUS_ACTIVE,
					gov.STATUS_SUSPENDED,
					gov.STATUS_SUPERSEDED,
					gov.STATUS_RETIRED,
					gov.STATUS_ARCHIVED,
				}
			),
		)
		self.assertEqual(
			gov.CONTROLLED_REPLACEMENT_STATES,
			frozenset(
				{
					gov.STATUS_IMPORTED,
					gov.STATUS_VALIDATION_FAILED,
					gov.STATUS_VALIDATED,
					gov.STATUS_RETURNED,
				}
			),
		)

	def test_std_gov_004_section_12_event_codes_exact(self) -> None:
		expected = {
			"EVT_IMPORTED": "STD_TEMPLATE_IMPORTED",
			"EVT_PACKAGE_REPLACED": "STD_TEMPLATE_PACKAGE_REPLACED",
			"EVT_VALIDATION_STARTED": "STD_TEMPLATE_VALIDATION_STARTED",
			"EVT_VALIDATION_COMPLETED": "STD_TEMPLATE_VALIDATION_COMPLETED",
			"EVT_SUBMITTED": "STD_TEMPLATE_SUBMITTED_FOR_APPROVAL",
			"EVT_RETURNED": "STD_TEMPLATE_RETURNED_FOR_CORRECTION",
			"EVT_REJECTED": "STD_TEMPLATE_REJECTED",
			"EVT_APPROVED": "STD_TEMPLATE_APPROVED",
			"EVT_ACTIVATED": "STD_TEMPLATE_ACTIVATED",
			"EVT_SUSPENDED": "STD_TEMPLATE_SUSPENDED",
			"EVT_REINSTATED": "STD_TEMPLATE_REINSTATED",
			"EVT_SUPERSEDED": "STD_TEMPLATE_SUPERSEDED",
			"EVT_RETIRED": "STD_TEMPLATE_RETIRED",
			"EVT_ARCHIVED": "STD_TEMPLATE_ARCHIVED",
			"EVT_USED_FOR_TENDER": "STD_TEMPLATE_USED_FOR_TENDER",
			"EVT_USAGE_BLOCKED": "STD_TEMPLATE_USAGE_BLOCKED",
			"EVT_MUTATION_BLOCKED": "STD_TEMPLATE_MUTATION_BLOCKED",
			"EVT_DELETE_BLOCKED": "STD_TEMPLATE_DELETE_BLOCKED",
			"EVT_OVERRIDE_USED": "STD_TEMPLATE_OVERRIDE_USED",
			"EVT_SNAPSHOT_GENERATED": "STD_TEMPLATE_SNAPSHOT_GENERATED",
			"EVT_ACTIVE_CONFLICT_BLOCKED": "STD_TEMPLATE_ACTIVE_CONFLICT_BLOCKED",
			"EVT_HASH_MISMATCH_BLOCKED": "STD_TEMPLATE_HASH_MISMATCH_BLOCKED",
			"EVT_PERMISSION_BLOCKED": "STD_TEMPLATE_PERMISSION_BLOCKED",
		}
		for attr, val in expected.items():
			with self.subTest(attr=attr):
				self.assertEqual(getattr(gov, attr), val)

	def test_std_gov_004_canonicalization_key_order_independent(self) -> None:
		a = {"z": 1, "m": {"b": 2, "a": 3}}
		b = {"m": {"a": 3, "b": 2}, "z": 1}
		self.assertEqual(
			gov.canonicalize_std_package_payload(a),
			gov.canonicalize_std_package_payload(b),
		)
		self.assertEqual(
			gov.canonicalize_std_package_payload(a),
			'{"m":{"a":3,"b":2},"z":1}',
		)

	def test_std_gov_004_canonicalize_accepts_json_string(self) -> None:
		raw = '{"z":1,"m":{"b":2,"a":3}}'
		self.assertEqual(
			gov.canonicalize_std_package_payload(raw),
			gov.canonicalize_std_package_payload(json.loads(raw)),
		)

	def test_std_gov_004_hash_stable_and_sha256_hex(self) -> None:
		payload = {"sections": {"x": 1}, "manifest": {"y": 2}}
		h1 = gov.compute_std_package_hash(payload)
		h2 = gov.compute_std_package_hash({"manifest": {"y": 2}, "sections": {"x": 1}})
		self.assertEqual(h1, h2)
		self.assertEqual(len(h1), 64)
		self.assertEqual(h1, h1.lower())
		for c in h1:
			self.assertIn(c, "0123456789abcdef")

	def test_std_gov_004_hash_changes_when_content_changes(self) -> None:
		p1 = {"a": 1}
		p2 = {"a": 2}
		self.assertNotEqual(
			gov.compute_std_package_hash(p1),
			gov.compute_std_package_hash(p2),
		)

	def test_std_gov_004_invalid_json_string_raises(self) -> None:
		with self.assertRaises(ValueError):
			gov.canonicalize_std_package_payload("not json {")

	def test_std_gov_004_non_serializable_raises(self) -> None:
		class Opaque:
			pass

		with self.assertRaises(TypeError):
			gov.canonicalize_std_package_payload({"x": Opaque()})
