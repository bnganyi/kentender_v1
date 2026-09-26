# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Requisitions' clean-ups take child-table rows with their records.

Found 26 Sep 2026: the test wipe, the browser-fixture wipe and the seed
clears deleted Requisitions, their Versions and their package Versions
directly, which left contributing units, drawdown lines, package items and
requirements behind — about 49,000 rows on the dev site that no screen could
reach. Rows are planted raw (`db_insert`) on a plan that does not exist, so
they are test-world rows by `fixtures.test_requisitions()`'s own rule.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.procurement_requisitions.seeds import playwright_ui_fixtures as pw
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


def _plant(doctype: str, name: str, **values) -> tuple[str, str]:
	# `db_insert` stamps the session user as owner unless `creation` is set.
	frappe.get_doc({"doctype": doctype, "name": name, "creation": now_datetime(), **values}).db_insert()
	return doctype, name


class TestCleanUpChildRows(IntegrationTestCase):
	def _world(self, owner: str) -> list[tuple[str, str]]:
		tag = uuid4().hex[:8]
		requisition, version, package, package_version = (f"PRQ-CU-{tag}", f"RQV-CU-{tag}", f"RQP-CU-{tag}", f"PKV-CU-{tag}")
		rows = [
			_plant("Procurement Requisition", requisition, owner=owner, plan_id=f"PLN-GONE-{tag}"),
			_plant("Requisition Version", version, owner=owner, requisition=requisition),
			_plant("IT Equipment Requirement Package", package, owner=owner, requisition=requisition),
			_plant("IT Equipment Requirement Package Version", package_version, owner=owner, package=package),
		]
		for doctype, parenttype, parent, parentfield in (
			("Requisition Contributing Unit", "Procurement Requisition", requisition, "contributing_org_units"),
			("Requisition Drawdown Line", "Requisition Version", version, "drawdown_lines"),
			("Requisition Item", "IT Equipment Requirement Package Version", package_version, "items"),
			("Requisition Technical Requirement", "IT Equipment Requirement Package Version", package_version, "technical_requirements"),
		):
			rows.append(_plant(doctype, f"CU-{uuid4().hex[:10]}", parenttype=parenttype, parent=parent, parentfield=parentfield))
		for doctype, name in rows:
			self.addCleanup(frappe.db.delete, doctype, {"name": name})
		return rows

	def _assert_gone(self, rows: list[tuple[str, str]]) -> None:
		for doctype, name in rows:
			self.assertFalse(frappe.db.exists(doctype, name), f"{doctype} {name} was left behind")

	def test_the_test_wipe_takes_child_rows(self):
		rows = self._world(owner="Administrator")
		fx.wipe_requisition_rows()
		self._assert_gone(rows)

	def test_the_browser_fixture_wipe_takes_child_rows(self):
		rows = self._world(owner=pw.AUTHOR)
		pw._wipe_requisitions_side()
		self._assert_gone(rows)
