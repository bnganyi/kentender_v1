# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`tenders.seeds.clear` — removing a Tender leaves nothing behind.

Found 26 Sep 2026: the seed reset, the full wipe and the browser fixtures
deleted the Tender family's rows directly, which left their child-table rows
and attached files behind (749 rows and 1,734 files on the dev site), and a
plain canonical reseed never removed a stray Tender at all.

Rows are planted raw (`db_insert`): selection reads only the identity
columns, and the Tender controllers refuse ordinary deletes by design.
"""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tenders.seeds import clear


def _plant(doctype: str, name: str, **values) -> None:
	frappe.get_doc({"doctype": doctype, "name": name, **values}).db_insert()


def _plant_child(doctype: str, parenttype: str, parent: str, parentfield: str) -> str:
	name = f"SC-{uuid4().hex[:10]}"
	_plant(doctype, name, parenttype=parenttype, parent=parent, parentfield=parentfield)
	return name


def _plant_file(document: str) -> str:
	return (
		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"seed-clear-{uuid4().hex[:8]}.txt",
				"content": uuid4().hex.encode(),
				"attached_to_doctype": "Tender Document",
				"attached_to_name": document,
				"is_private": 1,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _canonical_family() -> dict[str, int]:
	tenders = clear.canonical_tenders()
	return {doctype: frappe.db.count(doctype, {"tender": ("in", tenders or ("",))}) for doctype in clear.TENDER_DOCTYPES[:-1]}


class TestSeedClear(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		tag = uuid4().hex[:8]
		self.tender = f"TDR-SC-{tag}"
		self.version = f"TDV-SC-{tag}"
		self.document = f"TDOC-SC-{tag}"
		self.planted: list[tuple[str, str]] = []
		self.addCleanup(self._purge)
		_plant("Tender", self.tender, tender_reference=f"SC-{tag}", requisition=f"PRQ-SC-{tag}")
		_plant("Tender Version", self.version, tender=self.tender)
		self.finding = _plant_child("Tender Review Finding", "Tender Version", self.version, "review_findings")
		_plant("Tender Document", self.document, tender=self.tender)
		self.file = _plant_file(self.document)
		self.planted += [
			("Tender", self.tender),
			("Tender Version", self.version),
			("Tender Review Finding", self.finding),
			("Tender Document", self.document),
			("File", self.file),
		]

	def _purge(self):
		for doctype, name in reversed(self.planted):
			if doctype == "File":
				if frappe.db.exists("File", name):
					frappe.delete_doc("File", name, force=1, ignore_permissions=True)
			else:
				frappe.db.delete(doctype, {"name": name})
		frappe.db.commit()

	def _assert_gone(self):
		for doctype, name in self.planted:
			self.assertFalse(frappe.db.exists(doctype, name), f"{doctype} {name} was left behind")

	def test_a_tender_off_the_canonical_requisition_is_not_canonical(self):
		self.assertIn(self.tender, clear.non_canonical_tenders())
		self.assertNotIn(self.tender, clear.canonical_tenders())
		for tender in clear.canonical_tenders():
			self.assertNotIn(tender, clear.non_canonical_tenders())

	def test_delete_tenders_removes_child_rows_and_attached_files(self):
		clear.delete_tenders([self.tender])
		self._assert_gone()

	def test_clear_removes_a_stray_tender_and_keeps_the_canonical_one(self):
		canonical = sorted(clear.canonical_tenders())
		family = _canonical_family()
		clear.clear_tender_fixture_rows()
		self._assert_gone()
		self.assertEqual(sorted(clear.canonical_tenders()), canonical)
		self.assertEqual(_canonical_family(), family)

	def test_clear_removes_rows_whose_tender_is_already_gone(self):
		"""A family row whose Tender was deleted by an earlier, incomplete
		clean-up has no Tender left to be found through."""
		frappe.db.delete("Tender", {"name": self.tender})
		clear.clear_tender_fixture_rows()
		self._assert_gone()
