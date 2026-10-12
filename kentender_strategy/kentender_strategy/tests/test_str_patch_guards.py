# Copyright (c) 2026, KenTender and contributors
"""AUD-XC-125 — the Strategy teardown patches never remove what the app still ships.

On a site that has not logged them (a restored backup, a rebuilt droplet) both
patches run after model sync. They must leave the current Strategic Plan and
Strategy Node doctypes and their data alone, and a second run must change nothing.

These tests never run a patch against the real database: they call the patch
functions against a mocked `frappe.db` / `frappe.delete_doc` that report every
doctype as present and every table as holding rows, and assert on what the
patch tried to do."""

from __future__ import annotations

from unittest import TestCase
from unittest.mock import MagicMock, patch

from kentender_core.utils.patch_guards import doctype_is_shipped
from kentender_strategy.patches import mvp1_teardown_drop_legacy_strategy_doctypes as teardown
from kentender_strategy.patches import str_chg_001_phase1_domain_model_rebuild as rebuild

CURRENT = ("Strategic Plan", "Strategy Node", "Strategic Plan Version")


def _present_everywhere():
	db = MagicMock()
	db.exists.return_value = True
	db.table_exists.return_value = True
	db.has_column.return_value = True
	return db


class TestStrategyPatchGuards(TestCase):
	def test_no_listed_doctype_is_one_the_app_still_ships(self):
		for name in teardown.LEGACY_DOCTYPES + rebuild.REMOVED_DOCTYPES:
			self.assertFalse(doctype_is_shipped(name), f"{name} is shipped but listed for removal")
		for name in CURRENT:
			self.assertTrue(doctype_is_shipped(name), name)

	def test_teardown_never_deletes_a_current_doctype_and_is_repeatable(self):
		db, delete_doc = _present_everywhere(), MagicMock()
		with patch("frappe.db", db), patch("frappe.delete_doc", delete_doc), patch.object(teardown, "_ensure_placeholder_workspace"):
			teardown.execute()
			teardown.execute()  # double run
		deleted = [c.args[1] for c in delete_doc.call_args_list if c.args[0] == "DocType"]
		for name in CURRENT:
			self.assertNotIn(name, deleted)
		self.assertEqual(sorted(set(deleted)), sorted(teardown.LEGACY_DOCTYPES))

	def test_rebuild_never_deletes_a_current_doctype_or_a_current_plan_row(self):
		db, delete_doc = _present_everywhere(), MagicMock()
		with patch("frappe.db", db), patch("frappe.delete_doc", delete_doc):
			rebuild.execute()
			rebuild.execute()  # double run
		deleted = {c.args[1] for c in delete_doc.call_args_list if c.args[0] == "DocType"}
		self.assertFalse(deleted & set(CURRENT))
		statements = [c.args[0] for c in db.sql.call_args_list]
		self.assertTrue(statements, "the legacy-row clean-up did not run")
		for sql in statements:
			self.assertIn("WHERE", sql)
			self.assertIn("plan_id", sql)  # only rows without the rebuilt identity

	def test_rebuild_skips_the_row_clean_up_when_the_table_has_no_rebuilt_identity_column_yet(self):
		db = _present_everywhere()
		db.has_column.return_value = False
		with patch("frappe.db", db), patch("frappe.delete_doc", MagicMock()):
			rebuild.execute()
		db.sql.assert_not_called()
