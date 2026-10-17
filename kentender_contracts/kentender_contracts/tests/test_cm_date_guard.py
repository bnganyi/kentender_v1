# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""A date a person types is read with `records.day`, never with `getdate` straight from the form.

`frappe.utils.getdate("")` is today's date, so a command that parsed a blank date with it recorded the day the person pressed the button, passed every "is it a date" check and asked for nothing (found 15 Oct 2026 in
nine Phase 8 commands: a claim's notice date, the return and outcome dates, the termination notice and its effective date, a report's submission date, the source date and the publication date, the signed-copy date).
`records.day` is None for a blank or an invalid value, so the command's own "Enter the date" message applies.

This guard walks every service and fails on a new `getdate(...)` or `get_datetime(...)` whose argument is a bare function parameter unless it has been reviewed and listed: its blank is refused before the parse, or the
parameter is an internal date the service computed rather than one a person typed."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import ast
import unittest
from pathlib import Path

import frappe

from kentender_contracts.services import records

#: (file, function, parameter): reviewed. A user-typed one is refused when blank before it is parsed; an internal one is a date the service passes itself.
REVIEWED = {
	# typed, and refused when blank by the line before the parse (`cstr(x).strip()`)
	("advance.py", "record_guarantee", "issued_on"), ("advance.py", "record_guarantee", "expires_on"), ("advance.py", "verify_guarantee", "received_on"),
	("security.py", "record_security", "issued_on"), ("security.py", "record_security", "expires_on"), ("security.py", "verify_security", "received_on"),
	("payment.py", "submit_invoice", "invoice_date"), ("payment.py", "apparent_duplicate", "invoice_date"),
	("payment.py", "_settle_advance", "effective_date"), ("payment.py", "record_finance_settlement", "effective_date"), ("payment.py", "correct_finance_settlement", "effective_date"),
	("delivery.py", "record_arrival", "received_at"),
	# optional, and read only when given
	("delivery.py", "recommend_inspectors", "from_date"), ("delivery.py", "recommend_inspectors", "until_date"), ("delivery.py", "appoint_inspectors", "from_date"), ("delivery.py", "appoint_inspectors", "until_date"),
	("issues.py", "open_issue", "reply_by"),
	# internal: a date the service computed or read from a record
	("bindings.py", "effective_appointment", "at"), ("clock.py", "when", "value"), ("formation_rules.py", "window", "now"),
	("reporting.py", "period_of", "on"), ("reporting.py", "latest", "start"), ("reporting.py", "covered_cases", "period_end"), ("reporting.py", "variation_rows", "start"), ("reporting.py", "variation_rows", "end"),
	("reporting.py", "termination_rows", "start"), ("reporting.py", "termination_rows", "end"), ("reporting.py", "generate", "period_start"),
}


def _parses_of_a_parameter() -> set[tuple[str, str, str]]:
	found = set()
	for path in sorted((Path(frappe.get_app_path("kentender_contracts")) / "services").glob("*.py")):
		for fn in ast.walk(ast.parse(path.read_text())):
			if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
				continue
			params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
			for node in ast.walk(fn):
				if not (isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in params):
					continue
				name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
				if name in ("getdate", "get_datetime"):
					found.add((path.name, fn.name, node.args[0].id))
	return found


class TestDatesTypedByAPerson(unittest.TestCase):
	def test_a_blank_or_invalid_date_is_none_never_today(self):
		for value in ("", "   ", None, "not a date", "2027-13-45"):
			self.assertIsNone(records.day(value), repr(value))
		self.assertEqual(str(records.day(D("2027-07-02"))), D("2027-07-02"))
		self.assertEqual(str(records.day(f" {D('2027-07-02')} ")), D("2027-07-02"))

	def test_no_service_parses_a_typed_date_with_getdate_without_review(self):
		unreviewed = sorted(_parses_of_a_parameter() - REVIEWED)
		self.assertEqual(unreviewed, [], "Parse a date a person typed with `records.day` (None when blank), or review it and add it to REVIEWED with the reason it is safe.")

	def test_the_reviewed_list_names_only_parses_that_still_exist(self):
		self.assertEqual(sorted(REVIEWED - _parses_of_a_parameter()), [], "Remove a reviewed entry once the parse it names is gone.")
