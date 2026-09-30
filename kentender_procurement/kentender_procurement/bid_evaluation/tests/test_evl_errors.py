# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EVL-CHG-001 v0.4 §8 (plan D3; tracker EVL4-309): the error contract is
exactly the fifteen blocking codes and two nonblocking conditions of
`reconciliation/error_contract.md` (copied verbatim from the spec), every
applicable guard is returned together, and Proceedings errors reach the
screen in Evaluation's words."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_evaluation.services import errors

CONTRACT = Path(frappe.get_app_path("kentender_procurement")).parent.parent / "docs/mvp-1-r1/15_bid_evaluation/reconciliation/error_contract.md"


class TestErrorContract(IntegrationTestCase):
	def test_the_codes_and_messages_are_the_spec_contract(self):
		text = CONTRACT.read_text(encoding="utf-8")
		blocking = dict(re.findall(r"^\| `(EVL_[A-Z_]+)` \| (.+?) \| .+? \| EVL v0\.4 line \d+ \|$", text, flags=re.M))
		nonblocking = dict(re.findall(r"^\| `(EVL_[A-Z_]+)` \| ([^|]+?) \|$", text, flags=re.M))
		self.assertEqual(len(blocking), 15)
		self.assertEqual(errors.MESSAGES, blocking)
		self.assertEqual(errors.CONDITIONS, nonblocking)

	def test_every_applicable_guard_is_returned_together(self):
		guards = errors.Guards()
		guards.add("EVL_DECLARATION_REQUIRED", member="Test Member").add("EVL_SUSPENDED", instruction="MOH/REVIEW/TEST")
		with self.assertRaises(errors.EvaluationError) as ctx:
			guards.raise_if_any()
		self.assertEqual([r["code"] for r in ctx.exception.reasons], ["EVL_DECLARATION_REQUIRED", "EVL_SUSPENDED"])
		self.assertEqual(ctx.exception.reasons[1]["detail"], {"instruction": "MOH/REVIEW/TEST"})
		errors.Guards().raise_if_any()  # nothing to refuse
		with self.assertRaises(ValueError):
			errors.reason("EVL_NOT_A_CODE")

	def test_proceedings_errors_in_evaluation_words(self):
		self.assertEqual(errors.from_prc("PRC_EVIDENCE_INCOMPLETE", {"absent": ["x"]}), "EVL_MEMBERS_ABSENT")
		self.assertEqual(errors.from_prc("PRC_EVIDENCE_INCOMPLETE", {"missing": ["targets"]}), "EVL_REPORT_INCOMPLETE")
		self.assertEqual(errors.from_prc("PRC_TARGET_CHANGED"), "EVL_TARGET_CHANGED")
		self.assertEqual(errors.from_prc("PRC_PROOF_UNVERIFIED"), "EVL_SIGNATURE_UNCONFIRMED")
		self.assertEqual(errors.from_prc("PRC_VERSION_CONFLICT"), "EVL_VERSION_CONFLICT")
