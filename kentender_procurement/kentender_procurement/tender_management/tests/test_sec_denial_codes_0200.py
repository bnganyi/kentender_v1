# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0200 — central denial code catalogue and stable denial object shape.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_denial_codes_0200
"""

from __future__ import annotations

import unittest

from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
	EXTENSION_DENIAL_CODES,
	PACK_SEC_0200_CODES,
	PACK_TM2_DOC9_SECTION_75_DENIAL_CODES,
	StandardDenialPayload,
	all_denial_code_values,
	build_denial,
	is_known_denial_code,
)


class TestSecDenialCodes0200(unittest.TestCase):
	def test_pack_0200_catalogue_complete(self) -> None:
		self.assertEqual(len(PACK_SEC_0200_CODES), 35)
		self.assertEqual(len(PACK_TM2_DOC9_SECTION_75_DENIAL_CODES), 36)
		values = all_denial_code_values()
		self.assertTrue(PACK_SEC_0200_CODES <= values)
		self.assertTrue(PACK_TM2_DOC9_SECTION_75_DENIAL_CODES <= values)
		self.assertFalse(PACK_SEC_0200_CODES & EXTENSION_DENIAL_CODES)
		self.assertFalse(PACK_SEC_0200_CODES & PACK_TM2_DOC9_SECTION_75_DENIAL_CODES)
		self.assertFalse(EXTENSION_DENIAL_CODES & PACK_TM2_DOC9_SECTION_75_DENIAL_CODES)
		self.assertEqual(
			values,
			PACK_SEC_0200_CODES | EXTENSION_DENIAL_CODES | PACK_TM2_DOC9_SECTION_75_DENIAL_CODES,
		)

	def test_denial_code_enum_values_unique(self) -> None:
		raw = [m.value for m in DenialCode]
		self.assertEqual(len(raw), len(set(raw)))

	def test_build_denial_shape_and_validation(self) -> None:
		payload: StandardDenialPayload = build_denial(
			DenialCode.POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED,
			message="Use the addendum workflow.",
			risk_level="Critical",
		)
		self.assertFalse(payload["allowed"])
		self.assertEqual(
			payload["denial_code"],
			"POST_PUBLICATION_EDIT_DENIED_ADDENDUM_REQUIRED",
		)
		self.assertIn("addendum", payload["message"].lower())
		self.assertEqual(payload["risk_level"], "Critical")

	def test_build_denial_rejects_unknown_code(self) -> None:
		with self.assertRaises(ValueError):
			build_denial("NOT_A_PACK_CODE", message="x")

	def test_is_known_denial_code(self) -> None:
		self.assertTrue(is_known_denial_code(DenialCode.STD_AUTH_PERMISSION_DENIED))
		self.assertTrue(is_known_denial_code("OUTPUT_STALE"))
		self.assertFalse(is_known_denial_code("RANDOM_STRING"))
