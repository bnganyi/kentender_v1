# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 10 — template seed loader tests.

Covers STEP10-AC-001..014 from the Step 10 specification, plus the §10
status mapping table and §18 validation extras (invalid JSON / missing
files). Spec §19 defers a "full automated test suite"; the workspace TDD
gate still requires regression evidence, so this focused test module
extends the **STD-POC-004..010** pattern (see **STD-POC-011**).

Run:
    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_works_poc_step10_loader
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_loader
from kentender_procurement.tender_management.services.std_template_loader import (
	MANIFEST_TO_TEMPLATE_STATUS,
	PACKAGE_FOLDER_NAME,
	REQUIRED_JSON_FILES,
	REQUIRED_NON_HASH_FILES,
	TEMPLATE_CODE,
	build_combined_package_payload,
	compute_package_hash,
	get_template_package_path,
	import_std_works_poc_template,
	load_json_file,
	load_template_package,
	map_manifest_status_to_template_status,
	upsert_std_template,
	validate_required_files,
	validate_template_package,
)

REQUIRED_FUNCTIONS = (
	"get_template_package_path",
	"load_json_file",
	"validate_required_files",
	"load_template_package",
	"validate_template_package",
	"compute_package_hash",
	"build_combined_package_payload",
	"map_manifest_status_to_template_status",
	"upsert_std_template",
	"import_std_works_poc_template",
)

EXPECTED_PACKAGE_KEYS = {
	"manifest",
	"sections",
	"fields",
	"rules",
	"forms",
	"render_map",
	"sample_tender",
}

EXPECTED_PAYLOAD_KEYS = EXPECTED_PACKAGE_KEYS | {"package_hash", "import_metadata"}
EXPECTED_IMPORT_METADATA_KEYS = {"imported_at", "imported_by", "source_folder"}
EXPECTED_RESULT_KEYS = {
	"ok",
	"action",
	"template_code",
	"std_template_name",
	"package_hash",
	"status",
}

SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _delete_existing_std_template() -> None:
	if frappe.db.exists("STD Template", TEMPLATE_CODE):
		frappe.delete_doc(
			"STD Template",
			TEMPLATE_CODE,
			ignore_permissions=True,
			force=True,
		)


def _copy_package_to(tmp_dir: Path) -> Path:
	source = get_template_package_path()
	destination = Path(tmp_dir) / PACKAGE_FOLDER_NAME
	shutil.copytree(source, destination)
	return destination


class TestStdWorksPocStep10Loader(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def test_step10_ac001_module_exists(self) -> None:
		self.assertTrue(
			std_template_loader.__file__.endswith(
				"tender_management/services/std_template_loader.py"
			),
			"STEP10-AC-001: loader must live at tender_management/services/std_template_loader.py",
		)
		self.assertEqual(PACKAGE_FOLDER_NAME, "ke_ppra_works_building_2022_04_poc")
		self.assertEqual(TEMPLATE_CODE, "KE-PPRA-WORKS-BLDG-2022-04-POC")

	def test_step10_ac002_required_functions_exist(self) -> None:
		for name in REQUIRED_FUNCTIONS:
			with self.subTest(function=name):
				self.assertTrue(
					hasattr(std_template_loader, name),
					f"STEP10-AC-002: loader must expose {name}",
				)
				self.assertTrue(
					callable(getattr(std_template_loader, name)),
					f"STEP10-AC-002: {name} must be callable",
				)

	def test_step10_ac003_required_files_validated(self) -> None:
		self.assertIsNone(validate_required_files(get_template_package_path()))

		with tempfile.TemporaryDirectory() as tmp:
			with self.assertRaises(FileNotFoundError) as ctx:
				validate_required_files(Path(tmp))
		message = str(ctx.exception)
		for expected in REQUIRED_JSON_FILES + REQUIRED_NON_HASH_FILES:
			with self.subTest(file=expected):
				self.assertIn(
					expected,
					message,
					f"STEP10-AC-003: missing-file error must list {expected}",
				)

	def test_step10_ac004_parses_all_seven_json_files(self) -> None:
		package = load_template_package()
		self.assertEqual(set(package.keys()), EXPECTED_PACKAGE_KEYS)
		for key, value in package.items():
			with self.subTest(component=key):
				self.assertIsInstance(value, dict)
				self.assertGreater(
					len(value),
					0,
					f"STEP10-AC-004: {key} component must not be empty",
				)

	def test_step10_ac005_template_code_consistency(self) -> None:
		package = load_template_package()
		self.assertTrue(validate_template_package(package))

		bogus_sample = json.loads(json.dumps(package))
		bogus_sample["sample_tender"]["template_code"] = "BOGUS-CODE"
		with self.assertRaises(ValueError) as ctx_sample:
			validate_template_package(bogus_sample)
		self.assertIn("sample_tender", str(ctx_sample.exception))

		bogus_fields = json.loads(json.dumps(package))
		bogus_fields["fields"]["template_code"] = "BOGUS-CODE"
		with self.assertRaises(ValueError) as ctx_fields:
			validate_template_package(bogus_fields)
		self.assertIn("fields", str(ctx_fields.exception))

		missing_keys = json.loads(json.dumps(package))
		missing_keys["manifest"].pop("authority")
		with self.assertRaises(ValueError) as ctx_missing:
			validate_template_package(missing_keys)
		self.assertIn("authority", str(ctx_missing.exception))

	def test_step10_ac006_deterministic_sha256_hash(self) -> None:
		first = compute_package_hash()
		second = compute_package_hash()
		self.assertEqual(first, second, "STEP10-AC-006: hash must be deterministic")
		self.assertIsNotNone(
			SHA256_HEX_PATTERN.match(first),
			f"STEP10-AC-006: hash {first!r} must be 64 lowercase hex chars",
		)

	def test_step10_ac007_readme_excluded_from_hash(self) -> None:
		real_hash = compute_package_hash()

		with tempfile.TemporaryDirectory() as tmp:
			package_dir = _copy_package_to(Path(tmp))
			tampered_readme = package_dir / "README.md"
			tampered_readme.write_text(
				"# Tampered README — content unrelated to canonical README\n",
				encoding="utf-8",
			)
			tampered_hash = compute_package_hash(package_dir)

		self.assertEqual(
			real_hash,
			tampered_hash,
			"STEP10-AC-007: README.md must be excluded from package hash",
		)

	def test_step10_ac008_combined_payload_shape(self) -> None:
		package = load_template_package()
		package_hash = compute_package_hash()
		payload = build_combined_package_payload(
			package, package_hash, get_template_package_path()
		)
		self.assertEqual(set(payload.keys()), EXPECTED_PAYLOAD_KEYS)
		self.assertEqual(payload["package_hash"], package_hash)
		self.assertEqual(
			set(payload["import_metadata"].keys()), EXPECTED_IMPORT_METADATA_KEYS
		)
		serialized = json.dumps(payload)
		self.assertIsInstance(serialized, str)
		self.assertGreater(len(serialized), 0)

	def test_step10_ac009_creates_record_when_missing(self) -> None:
		_delete_existing_std_template()
		self.assertFalse(
			frappe.db.exists("STD Template", TEMPLATE_CODE),
			"Pre-condition: no STD Template before upsert",
		)

		result = upsert_std_template()
		self.assertEqual(result["action"], "created")
		self.assertEqual(result["template_code"], TEMPLATE_CODE)
		self.assertTrue(frappe.db.exists("STD Template", TEMPLATE_CODE))
		self.assertEqual(result["package_hash"], compute_package_hash())
		self.assertEqual(result["std_template_name"], TEMPLATE_CODE)
		self.assertTrue(result["ok"])

	def test_step10_ac010_updates_record_on_rerun(self) -> None:
		_delete_existing_std_template()
		first = upsert_std_template()
		self.assertEqual(first["action"], "created")

		second = upsert_std_template()
		self.assertEqual(second["action"], "updated")
		self.assertEqual(
			frappe.db.count("STD Template", {"template_code": TEMPLATE_CODE}),
			1,
			"STEP10-AC-010: rerun must not create duplicate STD Template records",
		)

	def test_step10_ac011_metadata_mapping(self) -> None:
		_delete_existing_std_template()
		upsert_std_template()
		doc = frappe.get_doc("STD Template", TEMPLATE_CODE)

		self.assertEqual(doc.template_code, TEMPLATE_CODE)
		self.assertEqual(
			doc.template_name,
			"PPRA Standard Tender Document for Procurement of Works — "
			"Building and Associated Civil Engineering Works",
		)
		self.assertEqual(doc.template_short_name, "PPRA Works STD — Building and Civil Works")
		self.assertEqual(doc.authority, "Public Procurement Regulatory Authority")
		self.assertEqual(doc.country, "KE")
		self.assertEqual(doc.procurement_category, "WORKS")
		self.assertEqual(
			doc.template_family, "BUILDING_AND_ASSOCIATED_CIVIL_ENGINEERING_WORKS"
		)
		self.assertEqual(doc.version_label, "April 2022")
		self.assertEqual(doc.package_version, "0.1.0-poc")
		self.assertEqual(doc.status, "Draft Package")
		self.assertEqual(doc.allowed_for_import, 1)
		self.assertEqual(doc.allowed_for_tender_creation, 0)
		self.assertEqual(doc.source_document_code, "DOC. 1")
		self.assertIn("STD FOR WORKS", doc.source_file_name)
		self.assertEqual(doc.package_hash, compute_package_hash())
		self.assertIsNotNone(doc.imported_at)

		stored_payload = json.loads(doc.package_json)
		self.assertEqual(set(stored_payload.keys()), EXPECTED_PAYLOAD_KEYS)
		self.assertEqual(stored_payload["package_hash"], compute_package_hash())

		stored_manifest = json.loads(doc.manifest_json)
		self.assertEqual(stored_manifest["template_code"], TEMPLATE_CODE)
		self.assertEqual(stored_manifest["status"]["package_status"], "DRAFT_PACKAGE")

	def test_step10_ac012_structured_result_shape(self) -> None:
		_delete_existing_std_template()
		result = import_std_works_poc_template()
		self.assertEqual(set(result.keys()), EXPECTED_RESULT_KEYS)
		self.assertTrue(result["ok"])
		self.assertEqual(result["template_code"], TEMPLATE_CODE)
		self.assertEqual(result["std_template_name"], TEMPLATE_CODE)
		self.assertEqual(result["status"], "Draft Package")
		self.assertIsNotNone(SHA256_HEX_PATTERN.match(result["package_hash"]))
		self.assertIn(result["action"], {"created", "updated"})

	def test_step10_ac013_does_not_create_procurement_tender(self) -> None:
		_delete_existing_std_template()
		before = frappe.db.count("Procurement Tender")
		import_std_works_poc_template()
		after = frappe.db.count("Procurement Tender")
		self.assertEqual(
			before,
			after,
			"STEP10-AC-013: importing the template must not create Procurement Tender records",
		)

	def test_step10_ac014_no_downstream_implementation(self) -> None:
		baseline_tenders = frappe.db.count("Procurement Tender")
		_delete_existing_std_template()
		import_std_works_poc_template()
		doc = frappe.get_doc("STD Template", TEMPLATE_CODE)

		self.assertEqual(
			doc.allowed_for_tender_creation,
			0,
			"STEP10-AC-014: allowed_for_tender_creation must reflect manifest (false)",
		)

		std_meta = frappe.get_meta("STD Template")
		std_fieldnames = {df.fieldname for df in std_meta.fields}
		for downstream_field in (
			"required_forms",
			"generated_tender_pack_html",
			"validation_messages",
			"boq_items",
		):
			with self.subTest(field=downstream_field):
				self.assertNotIn(
					downstream_field,
					std_fieldnames,
					f"STEP10-AC-014: STD Template must not own downstream field {downstream_field}",
				)

		self.assertEqual(
			frappe.db.count("Procurement Tender"),
			baseline_tenders,
			"STEP10-AC-014: loader must not initialize tenders (Step 11 work)",
		)

	def test_section10_status_mapping_table(self) -> None:
		expected = {
			"DRAFT_PACKAGE": "Draft Package",
			"IMPORTED": "Imported",
			"POC_APPROVED": "POC Approved",
			"SUSPENDED": "Suspended",
			"SUPERSEDED": "Superseded",
			"RETIRED": "Retired",
		}
		self.assertEqual(MANIFEST_TO_TEMPLATE_STATUS, expected)
		for code, label in expected.items():
			with self.subTest(code=code):
				self.assertEqual(map_manifest_status_to_template_status(code), label)

		with self.assertRaises(ValueError) as ctx:
			map_manifest_status_to_template_status("BOGUS")
		self.assertIn("BOGUS", str(ctx.exception))

	def test_section18_invalid_json_raises_clear_error(self) -> None:
		with tempfile.TemporaryDirectory() as tmp:
			bad_path = Path(tmp) / "bad.json"
			bad_path.write_text("{ not valid json", encoding="utf-8")
			with self.assertRaises(ValueError) as ctx:
				load_json_file(bad_path)
		message = str(ctx.exception)
		self.assertIn("bad.json", message)
		self.assertIn("Invalid JSON", message)
