# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BE-01 — STD Engine core DocType schema gates."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.constants import (
	COMMIT_TARGET_STATE_M1,
	FRAPPE_MODULE,
	LIFECYCLE_STATES,
	UI_MODE_READ_ONLY_INSPECTION,
)
from kentender_procurement.std_engine.doctype_schema import (
	CHILD_TABLE_DOCTYPES,
	CORE_DOCTYPES,
	OBJECT_IDENTITY_FIELDS,
	PACKAGE_CONTEXT_FIELDS,
	STD_IMPORT_RUN_REQUIRED_FIELDS,
	STD_VALIDATION_FINDING_REQUIRED_FIELDS,
	STD_VERSION_REQUIRED_FIELDS,
)


def _field_names(doctype: str) -> set[str]:
	return {df.fieldname for df in frappe.get_meta(doctype).fields}


class TestBe01CoreDoctypeRegistry(IntegrationTestCase):
	def test_all_core_doctypes_registered(self) -> None:
		for name in CORE_DOCTYPES:
			with self.subTest(doctype=name):
				self.assertTrue(frappe.db.exists("DocType", name), name)

	def test_all_core_doctypes_use_std_engine_module(self) -> None:
		for name in CORE_DOCTYPES:
			with self.subTest(doctype=name):
				module = frappe.db.get_value("DocType", name, "module")
				self.assertEqual(module, FRAPPE_MODULE)

	def test_std_form_field_is_child_table(self) -> None:
		self.assertEqual(int(frappe.get_meta("STD Form Field").istable or 0), 1)

	def test_child_table_doctypes_are_istable_only(self) -> None:
		for name in CORE_DOCTYPES:
			if name in CHILD_TABLE_DOCTYPES:
				continue
			with self.subTest(doctype=name):
				self.assertEqual(int(frappe.get_meta(name).istable or 0), 0)


class TestBe01StdVersionSchema(IntegrationTestCase):
	def test_std_version_required_fields(self) -> None:
		names = _field_names("STD Version")
		for fn in STD_VERSION_REQUIRED_FIELDS:
			with self.subTest(field=fn):
				self.assertIn(fn, names)

	def test_std_version_autoname_is_package_id(self) -> None:
		self.assertEqual(frappe.get_meta("STD Version").autoname, "field:package_id")

	def test_std_version_lifecycle_select_includes_draft_and_active(self) -> None:
		lifecycle = frappe.get_meta("STD Version").get_field("lifecycle_state")
		options = [o.strip() for o in (lifecycle.options or "").split("\n") if o.strip()]
		self.assertEqual(options, list(LIFECYCLE_STATES))
		self.assertIn(COMMIT_TARGET_STATE_M1, options)

	def test_std_version_ui_mode_default_read_only_inspection(self) -> None:
		ui_mode = frappe.get_meta("STD Version").get_field("ui_mode")
		self.assertEqual(ui_mode.default, UI_MODE_READ_ONLY_INSPECTION)


class TestBe01PackageContextOnVersionLinkedObjects(IntegrationTestCase):
	VERSION_LINKED = (
		"STD Source Document",
		"STD Source Anchor",
		"STD Section",
		"STD Clause",
		"STD Parameter",
		"STD Rule",
		"STD Form Schema",
		"STD Requirement Schema",
		"STD Price Schedule Schema",
		"STD Evaluation Schema",
		"STD Render Block",
	)

	def test_package_context_fields_present(self) -> None:
		for doctype in self.VERSION_LINKED:
			names = _field_names(doctype)
			for fn in PACKAGE_CONTEXT_FIELDS:
				with self.subTest(doctype=doctype, field=fn):
					self.assertIn(fn, names)

	def test_object_identity_fields_on_structured_objects(self) -> None:
		for doctype in (
			"STD Section",
			"STD Clause",
			"STD Parameter",
			"STD Rule",
			"STD Form Schema",
			"STD Requirement Schema",
			"STD Price Schedule Schema",
			"STD Evaluation Schema",
			"STD Render Block",
		):
			names = _field_names(doctype)
			for fn in OBJECT_IDENTITY_FIELDS:
				with self.subTest(doctype=doctype, field=fn):
					self.assertIn(fn, names)


class TestBe01GovernanceDoctypes(IntegrationTestCase):
	def test_std_import_run_required_fields(self) -> None:
		names = _field_names("STD Import Run")
		for fn in STD_IMPORT_RUN_REQUIRED_FIELDS:
			with self.subTest(field=fn):
				self.assertIn(fn, names)

	def test_std_validation_finding_required_fields(self) -> None:
		names = _field_names("STD Validation Finding")
		for fn in STD_VALIDATION_FINDING_REQUIRED_FIELDS:
			with self.subTest(field=fn):
				self.assertIn(fn, names)

	def test_std_usage_binding_has_fixture_source(self) -> None:
		self.assertIn("fixture_source", _field_names("STD Usage Binding"))


class TestBe01StdVersionInsertValidation(IntegrationTestCase):
	_FAMILY = "BE01-TEST-FAMILY"
	_PACKAGE = "BE01-TEST-PKG-2022-04"

	def tearDown(self) -> None:
		frappe.db.delete("STD Version", {"package_id": self._PACKAGE})
		frappe.db.delete("STD Family", {"family_code": self._FAMILY})
		super().tearDown()

	def test_insert_minimal_family_and_version_draft(self) -> None:
		family = frappe.get_doc(
			{
				"doctype": "STD Family",
				"family_code": self._FAMILY,
				"family_name": "BE-01 Test Family",
				"authority_code": "PPRA",
				"procurement_category": "INFORMATION_TECHNOLOGY",
			}
		)
		family.insert()

		version = frappe.get_doc(
			{
				"doctype": "STD Version",
				"package_id": self._PACKAGE,
				"family_code": self._FAMILY,
				"version_code": self._PACKAGE,
				"lifecycle_state": COMMIT_TARGET_STATE_M1,
				"activation_allowed": 0,
				"ui_mode": UI_MODE_READ_ONLY_INSPECTION,
				"is_immutable": 0,
				"package_quality": "RECONCILED_DRAFT_NOT_ACTIVATABLE",
				"validation_status": "OPEN",
			}
		)
		version.insert()
		reloaded = frappe.get_doc("STD Version", self._PACKAGE)
		self.assertEqual(reloaded.lifecycle_state, "DRAFT")
		self.assertEqual(int(reloaded.activation_allowed or 0), 0)
		self.assertEqual(reloaded.ui_mode, UI_MODE_READ_ONLY_INSPECTION)

	def test_std_version_rejects_invalid_lifecycle(self) -> None:
		frappe.get_doc(
			{
				"doctype": "STD Family",
				"family_code": self._FAMILY,
				"family_name": "BE-01 Test Family",
				"authority_code": "PPRA",
				"procurement_category": "INFORMATION_TECHNOLOGY",
			}
		).insert()
		version = frappe.get_doc(
			{
				"doctype": "STD Version",
				"package_id": self._PACKAGE,
				"family_code": self._FAMILY,
				"version_code": self._PACKAGE,
				"lifecycle_state": "NOT_A_REAL_STATE",
				"activation_allowed": 0,
				"ui_mode": UI_MODE_READ_ONLY_INSPECTION,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			version.insert()
