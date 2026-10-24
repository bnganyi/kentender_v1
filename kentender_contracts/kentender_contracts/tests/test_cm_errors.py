# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §8 (tracker CM8-301, CM8-002): the 17 error codes and their messages are the specification's, verbatim.
`reconciliation/error_contract.md` was copied from §8 by script; this compares the code with it."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import errors

CONTRACT = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management/reconciliation/error_contract.md"


def spec_rows() -> dict[str, tuple[str, str]]:
	rows = {}
	for line in CONTRACT.read_text().splitlines():
		match = re.match(r"^\| (CM_[A-Z]+) \| (.*?) \| (.*?) \| CM v0\.8 line \d+ \|$", line)
		if match:
			rows[match.group(1)] = (match.group(2), match.group(3))
	return rows


class TestContractErrors(IntegrationTestCase):
	def test_the_code_holds_exactly_the_specified_codes_and_messages(self):
		spec = spec_rows()
		self.assertEqual(len(spec), 17)
		self.assertEqual(set(errors.MESSAGES), set(spec))
		for code, (message, _fix) in spec.items():
			self.assertEqual(errors.MESSAGES[code], message, code)

	def test_every_code_names_its_fix_and_holder(self):
		spec = spec_rows()
		self.assertEqual({c: f for c, (_m, f) in spec.items()}, errors.FIXES)

	def test_a_refusal_carries_the_message_the_fix_and_separate_detail(self):
		with self.assertRaises(errors.ContractError) as caught:
			errors.fail("CM_HOLD", reason="Funding update pending", holder="HOP")
		exc = caught.exception
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertEqual(str(exc), errors.MESSAGES["CM_HOLD"])
		self.assertEqual(exc.detail, {"reason": "Funding update pending", "holder": "HOP"})
		self.assertEqual(exc.reasons[0]["fix"], errors.FIXES["CM_HOLD"])

	def test_guards_collect_every_applicable_reason_and_raise_once(self):
		guards = errors.Guards().add("CM_HOLD", scope="line 1").add("CM_RULE", rule="CM-R-08").add("CM_HOLD", scope="line 1")
		self.assertTrue(guards)
		self.assertEqual([r["code"] for r in guards.reasons], ["CM_HOLD", "CM_RULE"])
		with self.assertRaises(errors.ContractError) as caught:
			guards.raise_if_any()
		self.assertEqual([r["code"] for r in caught.exception.reasons], ["CM_HOLD", "CM_RULE"])
		self.assertFalse(errors.Guards())
		errors.Guards().raise_if_any()  # nothing to raise

	def test_an_unknown_code_is_refused_and_a_refusal_is_returned_as_data(self):
		with self.assertRaises(ValueError):
			errors.reason("CM_MADE_UP")
		try:
			errors.fail("CM_CHANGED", record_version=4)
		except errors.ContractError as exc:
			data = errors.as_data(exc)
		self.assertEqual(data["ok"], False)
		self.assertEqual(data["code"], "CM_CHANGED")
		self.assertEqual(data["detail"], {"record_version": 4})

	def test_a_form_value_error_is_not_one_of_the_17_codes(self):
		with self.assertRaises(errors.InputError) as caught:
			errors.required(reason="", amount="10")
		self.assertEqual(caught.exception.fields, {"reason": "Enter the reason."})
		self.assertEqual(caught.exception.code, "CM_INPUT")
		self.assertNotIn("CM_INPUT", errors.MESSAGES)

	def test_business_messages_never_show_internals(self):
		for message in errors.MESSAGES.values():
			self.assertNotRegex(message.lower(), r"traceback|sha-?256|doctype|tab[a-z]+|\bsql\b")
