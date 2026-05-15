# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0100 — publication readiness finding schema, factory, and validator.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_readiness_finding_0100
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tender_publication.readiness.readiness_finding import (
	publication_finding_from_code,
	publication_finding_from_std_blocker,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	PUBLICATION_CRITICAL_BLOCKER_CODES,
	PUBLICATION_READINESS_BRIDGE_UNKNOWN,
	PUBLICATION_READINESS_FINDING_INVALID,
	PUBLICATION_WARNING_CODES,
)
from kentender_procurement.tender_management.tender_publication.readiness.validator import (
	validate_publication_readiness_finding,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


_EXPECTED_CRITICAL: tuple[str, ...] = (
	"APPROVAL_REQUIRED",
	"BOQ_INCOMPLETE",
	"BUNDLE_NOT_CURRENT",
	"DCM_NOT_CURRENT",
	"DEM_NOT_CURRENT",
	"DOM_NOT_CURRENT",
	"DRAWINGS_INCOMPLETE",
	"DSM_NOT_CURRENT",
	"EVIDENCE_PACKAGE_FAILED",
	"OUTPUT_TRACE_MISSING",
	"RELEASE_RECORD_MISSING",
	"SCC_INCOMPLETE",
	"SNAPSHOT_CREATION_FAILED",
	"STD_BINDING_MISSING",
	"STD_INSTANCE_MISSING",
	"STD_INSTANCE_NOT_READY",
	"TDS_INCOMPLETE",
	"TEMPLATE_LINEAGE_INVALID",
	"WORKS_REQUIREMENTS_INCOMPLETE",
)

_EXPECTED_WARNINGS: tuple[str, ...] = (
	"AUDIT_NONCRITICAL_EVENT_MISSING",
	"OPTIONAL_ATTACHMENT_MISSING",
	"REVIEW_NOTE_UNRESOLVED",
	"SOURCE_HASH_MISSING",
)


class TestPubReadinessFinding0100(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.clear_messages()
		super().tearDown()

	def test_pub_0100_critical_codes_exactly_pack_set(self) -> None:
		self.assertEqual(len(PUBLICATION_CRITICAL_BLOCKER_CODES), 19)
		self.assertEqual(tuple(sorted(PUBLICATION_CRITICAL_BLOCKER_CODES)), _EXPECTED_CRITICAL)

	def test_pub_0100_warning_codes_exactly_pack_set(self) -> None:
		self.assertEqual(len(PUBLICATION_WARNING_CODES), 4)
		self.assertEqual(tuple(sorted(PUBLICATION_WARNING_CODES)), _EXPECTED_WARNINGS)

	def test_pub_0100_critical_finding_blocks_approval_and_publication(self) -> None:
		row = publication_finding_from_code("DEM_NOT_CURRENT")
		self.assertTrue(row["blocks_approval"])
		self.assertTrue(row["blocks_publication"])
		self.assertEqual(row["severity"], "Critical")

	def test_pub_0100_warning_finding_non_blocking_by_default(self) -> None:
		row = publication_finding_from_code("SOURCE_HASH_MISSING")
		self.assertFalse(row["blocks_approval"])
		self.assertFalse(row["blocks_publication"])
		self.assertEqual(row["severity"], "Warning")

	def test_pub_0100_unknown_code_raises(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			publication_finding_from_code("NOT_A_PACK_CODE")
		self.assertEqual(_last_msg_title(), PUBLICATION_READINESS_FINDING_INVALID)

	def test_pub_0100_validate_rejects_bad_severity(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_publication_readiness_finding(
				{
					"code": "DEM_NOT_CURRENT",
					"severity": "Fatal",
					"message": "m",
					"affected_area": "Generated Outputs",
					"resolution_action": "r",
					"blocks_approval": True,
					"blocks_publication": True,
				},
			)
		self.assertEqual(_last_msg_title(), PUBLICATION_READINESS_FINDING_INVALID)

	def test_pub_0100_validate_rejects_critical_without_blocks(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			validate_publication_readiness_finding(
				{
					"code": "BUNDLE_NOT_CURRENT",
					"severity": "Critical",
					"message": "m",
					"affected_area": "Generated Outputs",
					"resolution_action": "r",
					"blocks_approval": False,
					"blocks_publication": True,
				},
			)
		self.assertEqual(_last_msg_title(), PUBLICATION_READINESS_FINDING_INVALID)

	def test_pub_0100_std_bridge_bundle_missing(self) -> None:
		row = publication_finding_from_std_blocker("BUNDLE_MISSING", message="Custom")
		self.assertEqual(row["code"], "BUNDLE_NOT_CURRENT")
		self.assertEqual(row["message"], "Custom")
		self.assertTrue(row["blocks_approval"])

	def test_pub_0100_std_bridge_unknown_raises(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			publication_finding_from_std_blocker("STALE_OUTPUTS_PRESENT")
		self.assertEqual(_last_msg_title(), PUBLICATION_READINESS_BRIDGE_UNKNOWN)
