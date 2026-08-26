# Copyright (c) 2026, KenTender and contributors
"""STD-CHG-001 v1.3 Phase 1 — backbone domain model.

Covers: package/Draft/Active uniqueness (§7.1), required-section non-deletion
(§7.5), content-block four-treatment guard (§4/§7.6), display-order uniqueness.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

PACKAGE_CODE = "KE-TEST-STD-P1"


class TestSTDChg001Phase1DomainModel(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup()

	def tearDown(self):
		self._cleanup()

	def _cleanup(self):
		# Scoped to THIS test's own package only — a blanket `{"section_id":
		# ["like", "%"]}"`-style wildcard here would delete every OTHER
		# package's content blocks too (including the real golden `KE-PPRA-IT`
		# fixture, Phase 9) since section_id values aren't otherwise filtered.
		# Confirmed live: this exact class of bug silently passed for 8 phases
		# because each phase's tests were the only content on the site at the
		# time — it only surfaced once Phase 9 introduced persistent content.
		for section in frappe.get_all("STD Cfg Section", {"package_id": PACKAGE_CODE}, pluck="name"):
			frappe.db.delete("STD Cfg Content Block", {"section_id": section})
			frappe.db.delete("STD Cfg Section", {"name": section})
		frappe.db.delete("STD Cfg Draft", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Version", {"package_id": PACKAGE_CODE})
		frappe.db.delete("STD Cfg Source Document", {"official_title": ["like", "Test Source%"]})
		frappe.db.delete("STD Cfg Package", {"package_code": PACKAGE_CODE})
		frappe.db.commit()

	def _make_package(self):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Package",
				"package_code": PACKAGE_CODE,
				"official_title": "Test Package for Phase 1",
				"requirement_profile": "Information Technology",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def _make_source_document(self, ref_doctype, ref_name, title="Test Source Document"):
		doc = frappe.get_doc(
			{
				"doctype": "STD Cfg Source Document",
				"reference_doctype": ref_doctype,
				"reference_name": ref_name,
				"official_title": title,
				"official_issue_label": "Test edition",
				"file_id": "/files/test-source.pdf",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def test_package_generates_immutable_id_equal_to_code(self):
		pkg = self._make_package()
		self.assertEqual(pkg.package_id, PACKAGE_CODE)
		self.assertEqual(pkg.name, PACKAGE_CODE)

	def test_one_open_draft_per_package(self):
		self._make_package()
		first = frappe.get_doc(
			{
				"doctype": "STD Cfg Draft",
				"package_id": PACKAGE_CODE,
				"proposed_version_number": 1,
				"official_issue_label": "April 2021 edition",
			}
		)
		first.insert(ignore_permissions=True)
		self.assertTrue(first.draft_id)
		self.assertEqual(first.name, first.draft_id)

		second = frappe.get_doc(
			{
				"doctype": "STD Cfg Draft",
				"package_id": PACKAGE_CODE,
				"proposed_version_number": 1,
				"official_issue_label": "April 2021 edition",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			second.insert(ignore_permissions=True)

	def test_draft_id_immutable_after_insert(self):
		self._make_package()
		draft = frappe.get_doc(
			{
				"doctype": "STD Cfg Draft",
				"package_id": PACKAGE_CODE,
				"proposed_version_number": 1,
				"official_issue_label": "April 2021 edition",
			}
		)
		draft.insert(ignore_permissions=True)
		draft.draft_id = "SOMETHING-ELSE"
		with self.assertRaises(frappe.ValidationError):
			draft.save(ignore_permissions=True)

	def _make_draft(self, version_number=1):
		draft = frappe.get_doc(
			{
				"doctype": "STD Cfg Draft",
				"package_id": PACKAGE_CODE,
				"proposed_version_number": version_number,
				"official_issue_label": "April 2021 edition",
			}
		)
		draft.insert(ignore_permissions=True)
		return draft

	def test_one_active_version_per_package(self):
		self._make_package()
		draft = self._make_draft()
		src = self._make_source_document("STD Cfg Draft", draft.name)

		first = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 1,
				"status": "Active",
				"official_issue_label": "April 2021 edition",
				"official_source_file_id": src.name,
			}
		)
		first.insert(ignore_permissions=True)

		second = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 2,
				"status": "Active",
				"official_issue_label": "June 2028 revision",
				"official_source_file_id": src.name,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			second.insert(ignore_permissions=True)

	def test_version_number_unique_per_package(self):
		self._make_package()
		draft = self._make_draft()
		src = self._make_source_document("STD Cfg Draft", draft.name)
		first = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 1,
				"status": "Superseded",
				"official_issue_label": "April 2021 edition",
				"official_source_file_id": src.name,
			}
		)
		first.insert(ignore_permissions=True)

		duplicate = frappe.get_doc(
			{
				"doctype": "STD Cfg Version",
				"package_id": PACKAGE_CODE,
				"version_number": 1,
				"status": "Retired",
				"official_issue_label": "April 2021 edition (dup)",
				"official_source_file_id": src.name,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			duplicate.insert(ignore_permissions=True)

	def test_required_section_cannot_be_renamed_or_deleted(self):
		self._make_package()
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": PACKAGE_CODE,
				"section_code": "SEC-II",
				"title": "Section II — Tender Data Sheet",
				"coverage_area_number": 3,
				"display_order": 3,
				"is_required": 1,
			}
		)
		section.insert(ignore_permissions=True)

		section.title = "Renamed"
		with self.assertRaises(frappe.ValidationError):
			section.save(ignore_permissions=True)

		section.reload()
		with self.assertRaises(frappe.ValidationError):
			section.delete()

	def test_optional_section_can_be_deleted(self):
		self._make_package()
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": PACKAGE_CODE,
				"section_code": "SEC-OPT",
				"title": "Optional section",
				"coverage_area_number": 5,
				"display_order": 99,
				"is_required": 0,
			}
		)
		section.insert(ignore_permissions=True)
		section.delete()
		self.assertFalse(frappe.db.exists("STD Cfg Section", section.name))

	def _make_section(self, code="SEC-II", order=3):
		self._make_package()
		self.draft = self._make_draft()
		section = frappe.get_doc(
			{
				"doctype": "STD Cfg Section",
				"package_id": PACKAGE_CODE,
				"section_code": code,
				"title": "Section II — Tender Data Sheet",
				"coverage_area_number": 3,
				"display_order": order,
				"is_required": 1,
			}
		)
		section.insert(ignore_permissions=True)
		return section

	def _owner(self):
		return {"reference_doctype": "STD Cfg Draft", "reference_name": self.draft.name}

	def test_locked_text_block_requires_text_and_forbids_binding_key(self):
		section = self._make_section()

		missing_text = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Locked text",
				"display_order": 1,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			missing_text.insert(ignore_permissions=True)

		with_binding_key = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Locked text",
				"display_order": 1,
				"locked_text": "Tender Data Sheet introduction",
				"binding_key": "not.allowed",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			with_binding_key.insert(ignore_permissions=True)

		valid = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Locked text",
				"display_order": 1,
				"locked_text": "Tender Data Sheet introduction",
			}
		)
		valid.insert(ignore_permissions=True)
		self.assertTrue(valid.content_block_id)

	def test_non_locked_block_requires_binding_key_and_forbids_locked_text(self):
		section = self._make_section()

		missing_binding = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Parameter",
				"display_order": 4,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			missing_binding.insert(ignore_permissions=True)

		with_locked_text = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Parameter",
				"display_order": 4,
				"binding_key": "tender.validity_days",
				"locked_text": "not allowed here",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			with_locked_text.insert(ignore_permissions=True)

		valid = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Parameter",
				"display_order": 4,
				"binding_key": "tender.validity_days",
			}
		)
		valid.insert(ignore_permissions=True)
		self.assertTrue(valid.content_block_id)

	def test_undefined_block_type_rejected_by_framework(self):
		section = self._make_section()
		bogus = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Other",
				"display_order": 5,
				"binding_key": "whatever",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			bogus.insert(ignore_permissions=True)

	def test_display_order_unique_within_section(self):
		section = self._make_section()
		first = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Parameter",
				"display_order": 4,
				"binding_key": "tender.validity_days",
			}
		)
		first.insert(ignore_permissions=True)

		clash = frappe.get_doc(
			{
				"doctype": "STD Cfg Content Block",
				**self._owner(),
				"section_id": section.name,
				"block_type": "Generated value",
				"display_order": 4,
				"binding_key": "pe.official_name",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			clash.insert(ignore_permissions=True)
