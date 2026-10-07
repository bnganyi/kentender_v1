# Copyright (c) 2026, KenTender and contributors
"""AUD-XC-127 — one-shot destructive patches fail closed on a site that holds rows.

Nothing here touches the real database: every patch is called against a mocked
`frappe.db` that reports its tables as holding rows (or as empty), and the
assertions are on what the patch tried to do."""

from __future__ import annotations

import importlib
from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from kentender_core.utils.patch_guards import SITE_FLAG

PATCHES = (
	"tpr_chg_001_v08_retire_tender_preparation",
	"bds_chg_001_v08_retire_bid_slice",
	"tpr_fu25_retire_candidate_stand_in",
	"p6_clear_procurement_tender_dev",
	"pln_chg_001_v12_drop_legacy_planning_doctypes",
)
BASE = "kentender_procurement.patches."


def _db(rows: int) -> MagicMock:
	db = MagicMock()
	db.table_exists.return_value = True
	db.exists.return_value = False
	db.sql.return_value = [[rows]]
	db.get_all.return_value = []
	return db


def _run(name: str, *, rows: int, conf: dict | None = None):
	module = importlib.import_module(BASE + name)
	db, delete_doc = _db(rows), MagicMock()
	with patch("frappe.db", db), patch("frappe.delete_doc", delete_doc), patch("frappe.get_doc"), patch("frappe.conf", conf or {}), patch("frappe.clear_cache"):
		try:
			module.execute()
			error = None
		except frappe.ValidationError as exc:
			error = exc
	return db, delete_doc, error


class TestDestructivePatchGuards(TestCase):
	def test_every_patch_refuses_a_site_that_holds_rows_and_destroys_nothing(self):
		for name in PATCHES:
			db, delete_doc, error = _run(name, rows=3)
			self.assertIsNotNone(error, name)
			self.assertIn("would destroy rows on this site", str(error), name)
			delete_doc.assert_not_called()
			db.delete.assert_not_called()
			db.sql_ddl.assert_not_called()
			self.assertFalse([c for c in db.sql.call_args_list if "delete" in str(c.args[0]).lower() or "update" in str(c.args[0]).lower()], name)

	def test_every_patch_runs_on_a_fresh_site_with_empty_tables(self):
		for name in PATCHES:
			_db_, _delete, error = _run(name, rows=0)
			self.assertIsNone(error, name)

	def test_the_owner_can_authorise_a_development_site_explicitly(self):
		for name in PATCHES:
			_db_, _delete, error = _run(name, rows=3, conf={SITE_FLAG: 1})
			self.assertIsNone(error, name)

	def test_the_guard_covers_every_doctype_a_patch_drops(self):
		"""A doctype that is shipped again under the same name (Tender Evidence Requirement, relocated to
		Tenders) is why the row guard, not the name, is what protects a site."""
		for name in PATCHES:
			module = importlib.import_module(BASE + name)
			listed = set(getattr(module, "RETIRED_DOCTYPES", ())) | set(getattr(module, "LEGACY_DOCTYPES", ())) | ({module.STAND_IN} if hasattr(module, "STAND_IN") else set())
			captured = {}
			with patch.object(module, "require_empty_or_authorised", side_effect=lambda patch_name, doctypes: captured.update(doctypes=set(doctypes))), \
				patch("frappe.db", _db(0)), patch("frappe.delete_doc"), patch("frappe.get_doc"), patch("frappe.conf", {}), patch("frappe.clear_cache"):
				module.execute()
			if listed:
				self.assertEqual(captured["doctypes"], listed, name)
			else:
				self.assertEqual(captured["doctypes"], {"Procurement Tender"}, name)

	def test_the_p6_patch_asks_table_exists_with_a_doctype_name(self):
		"""`table_exists('tabProcurement Tender')` looked for `tabtabProcurement Tender` and could never run."""
		module = importlib.import_module(BASE + "p6_clear_procurement_tender_dev")
		db = _db(0)
		with patch("frappe.db", db), patch("frappe.conf", {}), patch.object(module, "_drop_trigger_if_exists"), patch.object(module, "_null_link"):
			module.execute()
		asked = [c.args[0] for c in db.table_exists.call_args_list]
		self.assertNotIn("tabProcurement Tender", asked)
		self.assertIn("Procurement Tender", asked)
