# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-WORKS-POC Step 10 — template seed loader.

Imports the developer-controlled STD-WORKS-POC JSON package into Frappe as a
single ``STD Template`` record. Idempotent, upsert by ``template_code``.

Implements every public function required by Step 10 spec §11:
``get_template_package_path``, ``load_json_file``, ``validate_required_files``,
``load_template_package``, ``validate_template_package``,
``compute_package_hash``, ``build_combined_package_payload``,
``map_manifest_status_to_template_status``, ``upsert_std_template``,
``import_std_works_poc_template``.

Hashing policy (§7): SHA-256 over the 7 runtime JSON files in fixed order with
the literal separator ``\\n---FILE:{file_name}---\\n`` between files;
``README.md`` is excluded from the hash but required to exist.

This module is an admin-only utility (§15): not whitelisted, not exposed to
ordinary users, and does not accept arbitrary package paths from user input.

See **STD-POC-011** for the slice ``services/`` placement decision (spec §4 /
§17 path ``<app>/procurement/std_template_loader.py`` adapted via
``Path(__file__).resolve().parent.parent`` to match the workspace internal
slice convention documented in
``apps/kentender_v1/kentender_procurement/PROCUREMENT_INTERNAL_STRUCTURE.md``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import now_datetime

PACKAGE_FOLDER_NAME = "ke_ppra_works_building_2022_04_poc"
TEMPLATE_CODE = "KE-PPRA-WORKS-BLDG-2022-04-POC"

REQUIRED_JSON_FILES: list[str] = [
	"manifest.json",
	"sections.json",
	"fields.json",
	"rules.json",
	"forms.json",
	"render_map.json",
	"sample_tender.json",
]
REQUIRED_NON_HASH_FILES: list[str] = ["README.md"]

MANIFEST_TO_TEMPLATE_STATUS: dict[str, str] = {
	"DRAFT_PACKAGE": "Draft Package",
	"IMPORTED": "Imported",
	"POC_APPROVED": "POC Approved",
	"SUSPENDED": "Suspended",
	"SUPERSEDED": "Superseded",
	"RETIRED": "Retired",
}

_PACKAGE_KEY_BY_FILE_NAME: dict[str, str] = {
	"manifest.json": "manifest",
	"sections.json": "sections",
	"fields.json": "fields",
	"rules.json": "rules",
	"forms.json": "forms",
	"render_map.json": "render_map",
	"sample_tender.json": "sample_tender",
}

_REQUIRED_TOP_LEVEL_KEYS: dict[str, tuple[str, ...]] = {
	"manifest": (
		"template_code",
		"template_name",
		"template_short_name",
		"description",
		"authority",
		"jurisdiction",
		"classification",
		"source_document",
		"versioning",
		"status",
		"applicability",
		"poc_scope",
		"package_files",
		"import_policy",
		"runtime_policy",
		"audit_policy",
		"ownership",
		"notes",
	),
	"sections": (
		"template_code",
		"section_model_version",
		"section_mutability_types",
		"sections",
	),
	"fields": (
		"template_code",
		"field_model_version",
		"field_types",
		"field_groups",
		"fields",
	),
	"rules": (
		"template_code",
		"rule_model_version",
		"rule_types",
		"message_severities",
		"operator_definitions",
		"rules",
	),
	"forms": (
		"template_code",
		"form_model_version",
		"form_categories",
		"respondent_types",
		"workflow_stages",
		"evidence_policies",
		"forms",
	),
	"sample_tender": (
		"sample_code",
		"sample_name",
		"template_code",
		"sample_status",
		"purpose",
		"tender",
		"configuration",
		"lots",
		"boq",
		"expected_activated_forms",
		"expected_validation_profile",
		"scenario_variants",
		"notes",
	),
}


def get_template_package_path() -> Path:
	"""Return absolute path to the STD-WORKS-POC template package folder.

	Resolves relative to this file (services/std_template_loader.py),
	independent of the current working directory. STD-POC-011: the loader
	lives one level deeper than the spec §17 skeleton assumes, so the
	package sits at ``parent.parent / std_templates / PACKAGE_FOLDER_NAME``.
	"""
	return (
		Path(__file__).resolve().parent.parent
		/ "std_templates"
		/ PACKAGE_FOLDER_NAME
	)


def load_json_file(path: Path) -> dict[str, Any]:
	"""Parse a UTF-8 JSON file. Raise ``ValueError`` with file context on parse failure."""
	try:
		with Path(path).open("r", encoding="utf-8") as handle:
			return json.load(handle)
	except json.JSONDecodeError as exc:
		raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def validate_required_files(package_path: Path) -> None:
	"""Confirm all §6 required files exist; raise ``FileNotFoundError`` listing missing files."""
	package_path = Path(package_path)
	expected = REQUIRED_JSON_FILES + REQUIRED_NON_HASH_FILES
	missing = [name for name in expected if not (package_path / name).is_file()]
	if missing:
		raise FileNotFoundError(
			f"STD template package is missing required files at {package_path}: "
			f"{', '.join(missing)}"
		)


def load_template_package(package_path: Path | None = None) -> dict[str, Any]:
	"""Validate required files, parse all 7 JSON components, return §11.4 dict."""
	package_path = Path(package_path) if package_path else get_template_package_path()
	validate_required_files(package_path)
	return {
		_PACKAGE_KEY_BY_FILE_NAME[name]: load_json_file(package_path / name)
		for name in REQUIRED_JSON_FILES
	}


def validate_template_package(package: dict[str, Any]) -> bool:
	"""Validate §11.5 invariants: template_code consistency + required keys + manifest file list."""
	manifest = package.get("manifest")
	if not isinstance(manifest, dict):
		raise ValueError("Package is missing parsed manifest.json")
	manifest_template_code = manifest.get("template_code")
	if not manifest_template_code:
		raise ValueError("manifest.json is missing template_code")

	for component_key, required_keys in _REQUIRED_TOP_LEVEL_KEYS.items():
		component = package.get(component_key)
		if not isinstance(component, dict):
			raise ValueError(f"Package is missing parsed {component_key}.json")
		missing_keys = [k for k in required_keys if k not in component]
		if missing_keys:
			raise ValueError(
				f"{component_key}.json is missing required top-level keys: {missing_keys}"
			)
		if "template_code" in required_keys:
			if component.get("template_code") != manifest_template_code:
				raise ValueError(
					f"{component_key}.json template_code "
					f"{component.get('template_code')!r} does not match manifest "
					f"{manifest_template_code!r}"
				)

	render_map = package.get("render_map")
	if isinstance(render_map, dict) and "template_code" in render_map:
		if render_map.get("template_code") != manifest_template_code:
			raise ValueError(
				f"render_map.json template_code {render_map.get('template_code')!r} "
				f"does not match manifest {manifest_template_code!r}"
			)

	expected_files = set(REQUIRED_JSON_FILES + REQUIRED_NON_HASH_FILES)
	listed_files = {
		entry.get("file_name")
		for entry in (manifest.get("package_files") or [])
		if isinstance(entry, dict)
	}
	unknown_in_manifest = sorted(listed_files - expected_files)
	if unknown_in_manifest:
		raise ValueError(
			"manifest.package_files lists files not in the §6 required set: "
			f"{unknown_in_manifest}"
		)
	missing_in_manifest = sorted(expected_files - listed_files)
	if missing_in_manifest:
		raise ValueError(
			"manifest.package_files is missing required files: "
			f"{missing_in_manifest}"
		)

	return True


def compute_package_hash(package_path: Path | None = None) -> str:
	"""SHA-256 hex digest over the 7 §7 files in fixed order with the spec separator. README excluded."""
	package_path = Path(package_path) if package_path else get_template_package_path()
	digest = hashlib.sha256()
	for file_name in REQUIRED_JSON_FILES:
		digest.update((package_path / file_name).read_bytes())
		digest.update(f"\n---FILE:{file_name}---\n".encode("utf-8"))
	return digest.hexdigest()


def build_combined_package_payload(
	package: dict[str, Any],
	package_hash: str,
	package_path: Path,
) -> dict[str, Any]:
	"""Build the §8 combined-package payload stored on ``STD Template.package_json``."""
	imported_by = getattr(getattr(frappe, "session", None), "user", None)
	return {
		"manifest": package["manifest"],
		"sections": package["sections"],
		"fields": package["fields"],
		"rules": package["rules"],
		"forms": package["forms"],
		"render_map": package["render_map"],
		"sample_tender": package["sample_tender"],
		"package_hash": package_hash,
		"import_metadata": {
			"imported_at": now_datetime().isoformat(),
			"imported_by": imported_by,
			"source_folder": str(package_path),
		},
	}


def map_manifest_status_to_template_status(manifest_status: str) -> str:
	"""§10: map machine-oriented manifest status to the user-facing ``STD Template.status`` value."""
	try:
		return MANIFEST_TO_TEMPLATE_STATUS[manifest_status]
	except KeyError as exc:
		raise ValueError(
			f"Unknown manifest status: {manifest_status!r}. Expected one of "
			f"{sorted(MANIFEST_TO_TEMPLATE_STATUS)}"
		) from exc


def upsert_std_template(
	package: dict[str, Any] | None = None,
	package_path: Path | None = None,
	commit: bool = False,
) -> dict[str, Any]:
	"""Create or update the ``STD Template`` record from the developer package.

	Idempotent on ``manifest.template_code``. Returns the §11.9 result dict.
	Internal helpers do not commit; ``commit=True`` is opt-in for the
	convenience caller.
	"""
	package_path = Path(package_path) if package_path else get_template_package_path()
	if package is None:
		package = load_template_package(package_path)

	validate_template_package(package)
	package_hash = compute_package_hash(package_path)
	payload = build_combined_package_payload(package, package_hash, package_path)

	manifest = package["manifest"]
	template_code = manifest["template_code"]
	manifest_status = (manifest.get("status") or {}).get("package_status")
	template_status = map_manifest_status_to_template_status(manifest_status)

	authority = (manifest.get("authority") or {}).get("name")
	country = (manifest.get("jurisdiction") or {}).get("country_code")
	classification = manifest.get("classification") or {}
	versioning = manifest.get("versioning") or {}
	source_document = manifest.get("source_document") or {}
	status_block = manifest.get("status") or {}

	if frappe.db.exists("STD Template", template_code):
		doc = frappe.get_doc("STD Template", template_code)
		action = "updated"
	else:
		doc = frappe.new_doc("STD Template")
		doc.template_code = template_code
		action = "created"

	doc.template_name = manifest.get("template_name")
	doc.template_short_name = manifest.get("template_short_name")
	doc.authority = authority
	doc.country = country
	doc.procurement_category = classification.get("procurement_category")
	doc.template_family = classification.get("template_family")
	doc.version_label = versioning.get("source_version_label")
	doc.package_version = versioning.get("package_version")
	doc.status = template_status
	doc.allowed_for_import = 1 if status_block.get("allowed_for_import") else 0
	doc.allowed_for_tender_creation = (
		1 if status_block.get("allowed_for_tender_creation") else 0
	)
	doc.source_document_code = source_document.get("source_document_code")
	doc.source_file_name = source_document.get("source_file_name")
	doc.source_file_hash = source_document.get("source_file_hash")
	doc.package_hash = package_hash
	doc.package_json = json.dumps(payload, indent=2, ensure_ascii=False)
	doc.manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
	doc.imported_at = now_datetime()
	doc.imported_by = getattr(getattr(frappe, "session", None), "user", None)

	if action == "created":
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	if commit:
		frappe.db.commit()

	return {
		"ok": True,
		"action": action,
		"template_code": template_code,
		"std_template_name": doc.name,
		"package_hash": package_hash,
		"status": template_status,
	}


def import_std_works_poc_template() -> dict[str, Any]:
	"""Convenience wrapper: import the STD-WORKS-POC package, commit, return §11.9 result."""
	return upsert_std_template(commit=True)
