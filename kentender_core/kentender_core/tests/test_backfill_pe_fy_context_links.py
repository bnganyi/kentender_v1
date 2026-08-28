"""AUTH-ADR-001 Phase 2 — backfill patch: resolvable rows get pe_fy_context,
unresolvable rows are left alone (not blocked, not guessed at).
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.patches.v1_0.backfill_pe_fy_context_links import execute


class TestBackfillPeFyContextLinks(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:6]
		ou = frappe.get_all("Organisation Unit", filters={"procuring_entity": ["is", "set"]}, fields=["name", "procuring_entity"], limit=1)[0]
		self.pe = ou.procuring_entity
		self.ou = ou.name
		self.start_year = 5000 + int(self.suffix[:4], 16) % 900
		self.fy = frappe.get_doc({"doctype": "Financial Year", "start_year": self.start_year}).insert(ignore_permissions=True)
		self.ctx = frappe.get_doc({
			"doctype": "PE Fiscal Year Context",
			"procuring_entity": self.pe,
			"financial_year": self.fy.name,
			"context_status": "Scheduled",
			"active_from": self.fy.start_date,
			"active_to": self.fy.end_date,
		}).insert(ignore_permissions=True)

	def tearDown(self):
		# Departmental Need rows are permanently retained (on_trash forbids
		# delete even with force) — IntegrationTestCase rolls back the whole
		# test transaction, so no explicit cleanup is needed or possible here.
		frappe.delete_doc("PE Fiscal Year Context", self.ctx.name, force=True, ignore_permissions=True)
		frappe.delete_doc("Financial Year", self.fy.name, force=True, ignore_permissions=True)

	def _departmental_need(self, target_financial_year: str) -> str:
		doc = frappe.get_doc({
			"doctype": "Departmental Need",
			"need_reference": f"NEED-{uuid4().hex[:8]}",
			"title": "Backfill test need",
			"procuring_entity": self.pe,
			"organisation_unit": self.ou,
			"target_financial_year": target_financial_year,
			"submitted_by": "Administrator",
			"concurrency_token": uuid4().hex,
			"status": "Draft",
		}).insert(ignore_permissions=True)
		return doc.name

	def test_resolvable_row_gets_pe_fy_context(self):
		name = self._departmental_need(self.fy.label)

		execute()

		self.assertEqual(frappe.db.get_value("Departmental Need", name, "pe_fy_context"), self.ctx.name)

	def test_unresolvable_row_is_left_alone(self):
		name = self._departmental_need("1901/02")

		execute()

		self.assertIn(frappe.db.get_value("Departmental Need", name, "pe_fy_context"), (None, ""))

	def test_idempotent_on_second_run(self):
		name = self._departmental_need(self.fy.label)

		execute()
		execute()

		self.assertEqual(frappe.db.get_value("Departmental Need", name, "pe_fy_context"), self.ctx.name)

	def test_already_set_row_is_not_reprocessed(self):
		name = self._departmental_need(self.fy.label)
		frappe.db.set_value("Departmental Need", name, "pe_fy_context", "SOME-OTHER-CTX", update_modified=False)

		execute()

		# Backfill only targets blank pe_fy_context — an already-set value (even
		# a manually-set one, as here) is left untouched, not overwritten.
		self.assertEqual(frappe.db.get_value("Departmental Need", name, "pe_fy_context"), "SOME-OTHER-CTX")
