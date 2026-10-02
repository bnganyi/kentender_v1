# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The row-group control (release 1.4): a bounded table of named columns. The
server stores one canonical form (rows in column order, blanks dropped, decimals
at their scale), names the row and the cell that is wrong, and checks the
table's own rules (minimum rows, totals) as its named validation."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_submission.services import controls, validation

PARAMS = {
	"columns": [
		{"key": "recipient", "label": "Name of recipient", "type": "text", "max_length": 80},
		{"key": "amount", "label": "Amount", "type": "decimal", "scale": 2, "minimum": "0"},
		{"key": "currency", "label": "Currency", "type": "choice", "options": ["KES", "USD", "EUR"]},
	],
	"minimum_rows": 1, "maximum_rows": 3, "totals": [],
}
SHARES = {
	"columns": [{"key": "name", "label": "Name", "type": "text"}, {"key": "shares", "label": "Shares", "type": "decimal", "scale": 2}],
	"minimum_rows": 1, "maximum_rows": 10, "totals": [{"column": "shares", "equals": "100"}],
}


class TestRowGroupControl(IntegrationTestCase):
	def test_rows_are_stored_in_column_order_with_blank_rows_dropped(self):
		raw = [{"currency": "KES", "amount": "1,500", "recipient": "  Acme  Agents "}, {"recipient": "", "amount": "", "currency": ""}]
		value, problem = controls.canonical("CTL-ROW-GROUP", raw, PARAMS)
		self.assertEqual((value, problem), ([{"recipient": "Acme Agents", "amount": "1500.00", "currency": "KES"}], None))
		self.assertEqual(list(value[0]), ["recipient", "amount", "currency"])

	def test_nothing_entered_is_not_answered(self):
		for raw in (None, [], [{"recipient": "", "amount": "", "currency": ""}]):
			with self.subTest(raw=raw):
				self.assertEqual(controls.canonical("CTL-ROW-GROUP", raw, PARAMS), (None, None))

	def test_the_problem_names_the_row_and_the_cell(self):
		raw = [{"recipient": "Acme", "amount": "ten", "currency": "KES"}, {"recipient": "Beta", "amount": "5", "currency": "GBP"}]
		value, problem = controls.canonical("CTL-ROW-GROUP", raw, PARAMS)
		self.assertIsNone(value)
		self.assertEqual(problem["rows"], {0: {"amount": "Enter a number."}, 1: {"currency": "Choose one of the listed options."}})

	def test_more_rows_than_the_limit_is_refused_as_a_table_problem(self):
		raw = [{"recipient": f"R{i}", "amount": "1", "currency": "KES"} for i in range(4)]
		value, problem = controls.canonical("CTL-ROW-GROUP", raw, PARAMS)
		self.assertIsNone(value)
		self.assertEqual(problem["table"], ["Enter at most 3 rows."])

	def test_a_value_that_is_not_a_list_of_rows_is_refused(self):
		self.assertEqual(controls.canonical("CTL-ROW-GROUP", "x", PARAMS)[0], None)
		self.assertIn("table", controls.canonical("CTL-ROW-GROUP", ["x"], PARAMS)[1])

	def test_problems_become_flat_field_errors_the_portal_can_place(self):
		problem = {"table": ["Enter at most 3 rows."], "rows": {1: {"amount": "Enter a number."}}}
		self.assertEqual(controls.flatten("fabc", problem), {"fabc": "Enter at most 3 rows.", "fabc.1.amount": "Enter a number."})
		self.assertEqual(controls.flatten("fabc", "Choose Yes or No."), {"fabc": "Choose Yes or No."})

	def test_the_portal_sees_a_row_group_kind(self):
		self.assertEqual(controls.KINDS["CTL-ROW-GROUP"], "row_group")


class TestRowGroupValidation(IntegrationTestCase):
	def test_shares_must_total_the_published_figure(self):
		rows = [{"name": "A", "shares": "60.00"}, {"name": "B", "shares": "30.00"}]
		self.assertEqual(validation.check("VAL-ROW-GROUP", SHARES, rows), "Shares must add up to 100; they add up to 90.00.")
		rows[1]["shares"] = "40.00"
		self.assertIsNone(validation.check("VAL-ROW-GROUP", SHARES, rows))

	def test_the_minimum_number_of_rows_is_checked(self):
		params = {**SHARES, "minimum_rows": 2, "totals": []}
		self.assertEqual(validation.check("VAL-ROW-GROUP", params, [{"name": "A", "shares": "100.00"}]), "Add at least 2 rows.")


class TestRowGroupSurfaces(IntegrationTestCase):
	def test_rows_read_as_one_line_for_a_summary(self):
		rows = [{"recipient": "Acme", "amount": "1500.00", "currency": "KES"}, {"recipient": "Beta", "amount": "", "currency": "USD"}]
		self.assertEqual(controls.describe_rows(PARAMS["columns"], rows), "Acme · 1500.00 · KES; Beta · USD")

	def test_a_seed_sample_is_accepted_by_the_control_and_meets_the_total(self):
		from kentender_procurement.bid_submission.seeds.filling import sample_value

		for params in (PARAMS, SHARES):
			with self.subTest(params["columns"][0]["key"]):
				sample = sample_value({"kind": "row_group", "row_group": params})
				value, problem = controls.canonical("CTL-ROW-GROUP", sample, params)
				self.assertIsNone(problem)
				self.assertIsNone(validation.check("VAL-ROW-GROUP", params, value))
