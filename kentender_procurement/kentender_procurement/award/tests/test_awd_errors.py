# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.4 §8 (plan D3; AWD4-103): the error contract is exactly the
thirteen codes of `reconciliation/error_contract.md` (copied verbatim from
the spec), and every applicable guard is returned together."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.award.services import errors

CONTRACT = Path(frappe.get_app_path("kentender_procurement")).parent.parent / "docs/mvp-1-r1/16_award/reconciliation/error_contract.md"


class TestErrorContract(IntegrationTestCase):
	def test_the_codes_and_messages_are_the_spec_contract(self):
		text = CONTRACT.read_text(encoding="utf-8")
		spec = dict(re.findall(r"^\| `(AWD_[A-Z_]+)` \| (.+?) \| .+? \|$", text, flags=re.M))
		self.assertEqual(len(spec), 13)
		self.assertEqual(errors.MESSAGES, spec)

	def test_every_applicable_guard_is_returned_together(self):
		guards = errors.Guards()
		guards.add("AWD_ON_HOLD", issue="X").add("AWD_VALIDITY_EXPIRED", valid_until="10 Oct 2027, 11:00 EAT")
		with self.assertRaises(errors.AwardError) as ctx:
			guards.raise_if_any()
		self.assertEqual([r["code"] for r in ctx.exception.reasons], ["AWD_ON_HOLD", "AWD_VALIDITY_EXPIRED"])
		errors.Guards().raise_if_any()
		with self.assertRaises(ValueError):
			errors.reason("AWD_NOT_A_CODE")

	def test_messages_carry_no_technical_detail(self):
		for message in errors.MESSAGES.values():
			self.assertNotRegex(message, r"tab[A-Z]|Traceback|[0-9a-f]{32}|_json")
