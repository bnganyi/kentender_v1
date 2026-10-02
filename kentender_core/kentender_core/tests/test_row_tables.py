# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared row-table rules (STD-TPL-001 v0.15 row group; Account business
profile): a bounded table of named columns whose rows are checked cell by cell
and, where the owner decided it, by a column total (shares add up to 100).
Pure logic: no database."""

from __future__ import annotations

from unittest import TestCase

from kentender_core.utils import row_tables

OWNERS = [
	{"key": "name", "label": "Name", "type": "text", "max_length": 40},
	{"key": "nationality", "label": "Nationality", "type": "text", "max_length": 40},
	{"key": "citizenship", "label": "Citizenship", "type": "text", "max_length": 40},
	{"key": "shares", "label": "Shares owned (%)", "type": "decimal", "scale": 2, "minimum": "0.01", "maximum": "100"},
]
TOTALS = [{"column": "shares", "equals": "100"}]
KIND = {"key": "kind", "label": "Kind", "type": "choice", "options": ["Gift", "Fee"]}


def row(name="Amina Yusuf", nationality="Kenyan", citizenship="Kenyan", shares="60"):
	return {"name": name, "nationality": nationality, "citizenship": citizenship, "shares": shares}


class TestNormalise(TestCase):
	def run_rows(self, rows, columns=OWNERS, **kw):
		return row_tables.normalise(columns, rows, **{"minimum_rows": 1, "maximum_rows": 10, **kw})

	def test_a_valid_table_is_canonical_in_column_order_with_decimals_at_their_scale(self):
		out = self.run_rows([row(shares="60"), row("Brian Otieno", shares=40)], totals=TOTALS)
		self.assertTrue(out.ok, out.problems)
		self.assertEqual(out.rows, [
			{"name": "Amina Yusuf", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "60.00"},
			{"name": "Brian Otieno", "nationality": "Kenyan", "citizenship": "Kenyan", "shares": "40.00"}])
		self.assertEqual(list(out.rows[0]), ["name", "nationality", "citizenship", "shares"])

	def test_blank_rows_are_dropped_and_errors_keep_the_position_the_person_typed(self):
		out = self.run_rows([row(), {}, row(name="", shares="30")], totals=TOTALS)
		self.assertFalse(out.ok)  # the third row is wrong; the blank second is not an error and not counted as a position shift
		self.assertEqual(out.rows, [])  # nothing is accepted while any row is wrong
		self.assertEqual(out.problems["rows"], {2: {"name": "Enter Name."}})

	def test_a_half_filled_row_names_each_missing_cell(self):
		out = self.run_rows([{"name": "Amina", "shares": "100"}])
		self.assertEqual(out.problems["rows"], {0: {"nationality": "Enter Nationality.", "citizenship": "Enter Citizenship."}})

	def test_cells_are_checked_by_type(self):
		out = self.run_rows([row(name="x" * 41, shares="abc"), row(shares="100.005"), row(shares="0"), row(shares="101")])
		self.assertEqual(out.problems["rows"][0], {"name": "Use at most 40 characters.", "shares": "Enter a number."})
		self.assertEqual(out.problems["rows"][1]["shares"], "Use at most 2 decimal places.")
		self.assertEqual(out.problems["rows"][2]["shares"], "Enter 0.01 or more.")
		self.assertEqual(out.problems["rows"][3]["shares"], "Enter 100 or less.")

	def test_a_choice_cell_takes_only_its_options_and_an_integer_cell_a_whole_number(self):
		columns = [KIND, {"key": "count", "label": "Count", "type": "integer", "minimum": 1, "maximum": 9}]
		out = row_tables.normalise(columns, [{"kind": "Bribe", "count": "2"}, {"kind": "Gift", "count": "2.5"}, {"kind": "Fee", "count": 3}], minimum_rows=0, maximum_rows=5)
		self.assertEqual(out.problems["rows"][0], {"kind": "Choose one of the listed options."})
		self.assertEqual(out.problems["rows"][1], {"count": "Enter a whole number."})
		self.assertEqual(out.rows, [])

	def test_an_optional_column_may_stay_empty(self):
		columns = [{"key": "who", "label": "Who", "type": "text"}, {"key": "note", "label": "Note", "type": "text", "required": False}]
		out = row_tables.normalise(columns, [{"who": "A"}], minimum_rows=1, maximum_rows=3)
		self.assertTrue(out.ok, out.problems)
		self.assertEqual(out.rows, [{"who": "A", "note": ""}])

	def test_the_row_limits(self):
		self.assertEqual(self.run_rows([]).problems["table"], ["Add at least 1 row."])
		self.assertEqual(self.run_rows([{}, {}]).problems["table"], ["Add at least 1 row."])  # blank rows do not count
		self.assertTrue(self.run_rows([], minimum_rows=0).ok)
		eleven = [row(shares="9.09")] * 11
		self.assertEqual(self.run_rows(eleven).problems["table"], ["Enter at most 10 rows."])
		self.assertEqual(self.run_rows([row(), row()], minimum_rows=3, maximum_rows=3).problems["table"], ["Add at least 3 rows."])

	def test_shares_must_add_up_to_100_and_the_message_says_what_they_add_up_to(self):
		out = self.run_rows([row(shares="60"), row("B", shares="25")], totals=TOTALS)
		self.assertEqual(out.problems["table"], ["Shares owned (%) must add up to 100; they add up to 85.00."])
		self.assertEqual(out.rows, [])  # nothing is accepted while the table is wrong
		self.assertTrue(self.run_rows([row(shares="33.33"), row("B", shares="33.33"), row("C", shares="33.34")], totals=TOTALS).ok)

	def test_a_total_is_not_checked_while_a_cell_in_that_column_is_wrong(self):
		out = self.run_rows([row(shares="abc"), row("B", shares="40")], totals=TOTALS)
		self.assertNotIn("table", out.problems)
		self.assertIn("shares", out.problems["rows"][0])

	def test_input_that_is_not_a_list_of_rows_is_refused(self):
		self.assertEqual(self.run_rows("x").problems["table"], ["Enter the rows as a list."])
		self.assertEqual(self.run_rows(["x"]).problems["table"], ["Each row must name its cells."])
		self.assertTrue(self.run_rows(None, minimum_rows=0).ok)


class TestDefinition(TestCase):
	def problems(self, columns=OWNERS, **kw):
		return row_tables.check_definition(columns, **{"minimum_rows": 1, "maximum_rows": 10, "totals": [], **kw})

	def test_the_owner_tables_are_a_valid_definition(self):
		self.assertEqual(self.problems(totals=TOTALS), [])

	def test_a_definition_is_refused_for_each_way_it_could_be_unsafe_or_unusable(self):
		bad = {
			"no columns": ([], "at least one column"),
			"too many columns": ([{"key": f"c{i}", "label": "C", "type": "text"} for i in range(9)], "at most 8 columns"),
			"duplicate key": ([{"key": "a", "label": "A", "type": "text"}, {"key": "a", "label": "B", "type": "text"}], "unique"),
			"bad key": ([{"key": "Bad Key", "label": "A", "type": "text"}], "lower-case"),
			"unknown type": ([{"key": "a", "label": "A", "type": "file"}], "type"),
			"choice without options": ([{"key": "a", "label": "A", "type": "choice"}], "options"),
			"no label": ([{"key": "a", "label": "", "type": "text"}], "label"),
		}
		for name, (columns, word) in bad.items():
			with self.subTest(name):
				self.assertTrue(any(word in p for p in self.problems(columns)), self.problems(columns))

	def test_limits_and_totals_are_checked(self):
		self.assertTrue(any("at most 10" in p for p in self.problems(maximum_rows=11)))
		self.assertTrue(any("minimum" in p for p in self.problems(minimum_rows=5, maximum_rows=3)))
		self.assertTrue(any("numeric" in p for p in self.problems(totals=[{"column": "name", "equals": "100"}])))
		self.assertTrue(any("unknown" in p for p in self.problems(totals=[{"column": "nope", "equals": "100"}])))
		self.assertTrue(any("equals" in p for p in self.problems(totals=[{"column": "shares", "equals": "lots"}])))
