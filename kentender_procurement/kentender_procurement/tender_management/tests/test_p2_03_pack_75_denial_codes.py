# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-03 — doc 9 §7.5 / doc 8 stable TM2 denial codes.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p2_03_pack_75_denial_codes
"""

from __future__ import annotations

import unittest

from kentender_procurement.tender_management.security.authorization.decision_engine import (
	AuthorizationDecisionEngine,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	PACK_TM2_DOC9_SECTION_75_DENIAL_CODES,
	StandardDenialPayload,
	all_denial_code_values,
	build_denial,
	is_known_denial_code,
)


class TestP203Pack75DenialCodes(unittest.TestCase):
	def test_p2_03_doc_9_codes_are_known_and_buildable(self) -> None:
		for code in sorted(PACK_TM2_DOC9_SECTION_75_DENIAL_CODES):
			self.assertTrue(is_known_denial_code(code), msg=code)
			payload: StandardDenialPayload = build_denial(code, message="m", risk_level="Medium")
			self.assertEqual(payload["denial_code"], code)

	def test_p2_03_smoke_doc_8_sample_codes(self) -> None:
		"""Doc 8 smoke contract cites these §7.5 strings verbatim."""
		for code in (
			"AUTH_DEM_MISSING_OR_STALE",
			"AUTH_PUBLICATION_SNAPSHOT_MISSING",
			"AUTH_BUNDLE_MISSING_OR_STALE",
			"PACKAGE_NOT_AUTHORIZED",
			"AUTH_SUPPLIER_INELIGIBLE",
			"AUTH_ADDENDUM_ACK_REQUIRED",
			"AUTH_SEALED_BID_DENIED",
			"AUTH_CONTRACT_PRICE_SOURCE_INVALID",
			"AUTH_REASON_REQUIRED",
		):
			self.assertIn(code, PACK_TM2_DOC9_SECTION_75_DENIAL_CODES)
			self.assertIn(code, all_denial_code_values())

	def test_p2_03_engine_preserves_known_tm2_denial(self) -> None:
		"""Legacy ``negative_denial_codes`` path must not collapse AUTH_* codes to STD_AUTH_PERMISSION_DENIED."""
		res = AuthorizationDecisionEngine.evaluate(
			"Administrator",
			"TND2_PUBLISH",
			"TM2 Tender",
			"TND-P203-001",
			context={
				"granted_permissions": ["PERM_TENDER_PUBLISH"],
				"enforce_negative_permission_rules": True,
				"negative_denial_codes": [DenialCode.AUTH_DEM_MISSING_OR_STALE],
			},
		)
		self.assertFalse(res["allowed"])
		self.assertEqual(res.get("denial_code"), "AUTH_DEM_MISSING_OR_STALE")
