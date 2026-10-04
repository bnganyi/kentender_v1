# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kentender_core.utils.raw_delete` — a direct delete that takes the
record's child-table rows with it (found 26 Sep 2026: seed and fixture
clean-ups had left about 50,000 unreachable child rows on the dev site)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.utils.raw_delete import delete_rows


class TestRawDelete(IntegrationTestCase):
	def _plant(self) -> tuple[str, str]:
		calendar = f"CAL-RD-{uuid4().hex[:8]}"
		holiday = f"HOL-RD-{uuid4().hex[:8]}"
		frappe.get_doc({"doctype": "Business Day Calendar", "name": calendar, "calendar_name": calendar}).db_insert()
		frappe.get_doc(
			{"doctype": "Business Day Calendar Holiday", "name": holiday, "parenttype": "Business Day Calendar", "parent": calendar, "parentfield": "holidays"}
		).db_insert()
		self.addCleanup(frappe.db.delete, "Business Day Calendar Holiday", {"name": holiday})
		self.addCleanup(frappe.db.delete, "Business Day Calendar", {"name": calendar})
		return calendar, holiday

	def test_the_record_and_its_child_rows_go_together(self):
		calendar, holiday = self._plant()
		deleted: dict[str, int] = {}
		self.assertEqual(delete_rows("Business Day Calendar", {"name": calendar}, deleted=deleted), 1)
		self.assertFalse(frappe.db.exists("Business Day Calendar", calendar))
		self.assertFalse(frappe.db.exists("Business Day Calendar Holiday", holiday))
		self.assertEqual(deleted, {"Business Day Calendar": 1, "Business Day Calendar Holiday": 1})

	def test_other_records_and_their_child_rows_stay(self):
		calendar, holiday = self._plant()
		other, other_holiday = self._plant()
		delete_rows("Business Day Calendar", {"name": calendar})
		self.assertTrue(frappe.db.exists("Business Day Calendar", other))
		self.assertTrue(frappe.db.exists("Business Day Calendar Holiday", other_holiday))

	def test_a_record_without_child_tables_is_a_plain_delete(self):
		self.assertFalse(frappe.get_meta("ToDo").get_table_fields())
		name = f"RD-{uuid4().hex[:8]}"
		frappe.get_doc({"doctype": "ToDo", "name": name, "description": name}).db_insert()
		self.addCleanup(frappe.db.delete, "ToDo", {"name": name})
		self.assertEqual(delete_rows("ToDo", {"name": name}), 1)
		self.assertFalse(frappe.db.exists("ToDo", name))
