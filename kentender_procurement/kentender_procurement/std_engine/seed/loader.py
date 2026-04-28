from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import frappe
import yaml
from frappe.utils.data import parse_json

from .manifest_schema import validate_seed_manifest


DOCTYPE_MAPPING = {
	"source_documents": ("Source Document Registry", "source_document_code"),
	"template_families": ("STD Template Family", "template_code"),
	"template_versions": ("STD Template Version", "version_code"),
	"applicability_profiles": ("STD Applicability Profile", "profile_code"),
	"parts": ("STD Part Definition", "part_code"),
	"sections": ("STD Section Definition", "section_code"),
	"itt_clauses": ("STD Clause Definition", "clause_code"),
	"invitation_to_tender_clauses": ("STD Clause Definition", "clause_code"),
	"tds_clause_index": ("STD Clause Definition", "clause_code"),
	"evaluation_clause_index": ("STD Clause Definition", "clause_code"),
	"forms_clause_index": ("STD Clause Definition", "clause_code"),
	"boq_clause_index": ("STD Clause Definition", "clause_code"),
	"specification_clauses": ("STD Clause Definition", "clause_code"),
	"drawing_clauses": ("STD Clause Definition", "clause_code"),
	"gcc_clauses": ("STD Clause Definition", "clause_code"),
	"scc_clause_index": ("STD Clause Definition", "clause_code"),
	"contract_form_clauses": ("STD Clause Definition", "clause_code"),
	"tender_identity_parameters": ("STD Parameter Definition", "parameter_code"),
	"tds_parameters": ("STD Parameter Definition", "parameter_code"),
	"scc_parameters": ("STD Parameter Definition", "parameter_code"),
	"evaluation_parameters": ("STD Parameter Definition", "parameter_code"),
	"boq_parameters": ("STD Parameter Definition", "parameter_code"),
	"parameter_dependencies": ("STD Parameter Dependency", "dependency_code"),
	"tendering_forms": ("STD Form Definition", "form_code"),
	"qualification_forms": ("STD Form Definition", "form_code"),
	"security_forms": ("STD Form Definition", "form_code"),
	"other_tender_forms": ("STD Form Definition", "form_code"),
	"contract_forms": ("STD Form Definition", "form_code"),
	"works_requirement_components": ("STD Works Requirement Component Definition", "component_code"),
	"boq_definition": ("STD BOQ Definition", "boq_definition_code"),
	"boq_bills": ("STD BOQ Bill Definition", "bill_code"),
	"boq_item_schema": ("STD BOQ Item Schema Definition", "schema_field_code"),
	"bundle_mappings": ("STD Extraction Mapping", "mapping_code"),
	"dsm_mappings": ("STD Extraction Mapping", "mapping_code"),
	"dom_mappings": ("STD Extraction Mapping", "mapping_code"),
	"dem_mappings": ("STD Extraction Mapping", "mapping_code"),
	"dcm_mappings": ("STD Extraction Mapping", "mapping_code"),
	"seed_instance_fixture": ("STD Instance", "instance_code"),
	"addendum_fixture": ("STD Addendum Impact Analysis", "impact_analysis_code"),
}


class SeedLoadError(frappe.ValidationError):
	pass


def load_std_seed_package(package_path: str, *, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
	root = Path(package_path).resolve()
	manifest_path = root / "00_manifest.yaml"
	if not manifest_path.exists():
		raise SeedLoadError(f"Missing manifest at {manifest_path}")

	manifest = _read_yaml(manifest_path)
	validate_seed_manifest(manifest, root)

	report: dict[str, Any] = {
		"package_path": str(root),
		"dry_run": dry_run,
		"force": force,
		"created": 0,
		"updated": 0,
		"skipped": 0,
		"processed": [],
	}

	for entry in manifest["load_order"]:
		entry_path = root / entry
		if entry_path.is_dir():
			files = sorted(entry_path.rglob("*.yaml"))
		else:
			files = [entry_path]
		for file_path in files:
			if file_path.name == "00_manifest.yaml":
				continue
			loaded = _read_yaml(file_path)
			stats = _process_payload(loaded, dry_run=dry_run, force=force)
			report["created"] += stats["created"]
			report["updated"] += stats["updated"]
			report["skipped"] += stats["skipped"]
			report["processed"].append(str(file_path.relative_to(root)))

	if not dry_run:
		frappe.db.commit()

	return report


def _process_payload(payload: dict[str, Any], *, dry_run: bool, force: bool) -> dict[str, int]:
	stats = {"created": 0, "updated": 0, "skipped": 0}
	for key, value in payload.items():
		if key not in DOCTYPE_MAPPING:
			continue
		doctype, code_field = DOCTYPE_MAPPING[key]
		records = value if isinstance(value, list) else [value]
		for record in records:
			if not isinstance(record, dict) or code_field not in record:
				continue
			operation = _upsert_record(doctype, code_field, record, dry_run=dry_run, force=force)
			stats[operation] += 1
	return stats


def _upsert_record(
	doctype: str,
	code_field: str,
	record: dict[str, Any],
	*,
	dry_run: bool,
	force: bool,
) -> str:
	meta = frappe.get_meta(doctype)
	meta_fields = {f.fieldname for f in meta.fields if f.fieldname}
	json_fields = {f.fieldname for f in meta.fields if f.fieldname and f.fieldtype == "JSON"}
	check_fields = {f.fieldname for f in meta.fields if f.fieldname and f.fieldtype == "Check"}
	payload = {k: v for k, v in record.items() if k in meta_fields or k == code_field}
	for field in json_fields:
		if field in payload and isinstance(payload[field], (list, dict)):
			payload[field] = json.dumps(payload[field])
	for field in check_fields:
		if field in payload:
			payload[field] = int(bool(payload[field]))
	if doctype == "STD Clause Definition" and not (
		payload.get("source_page_start") or payload.get("source_page_end") or payload.get("source_text_hash")
	):
		payload["source_text_hash"] = f"seed:{payload.get(code_field)}"
	code_value = payload[code_field]
	name = frappe.db.get_value(doctype, {code_field: code_value}, "name")

	if not name:
		if not dry_run:
			payload["doctype"] = doctype
			frappe.get_doc(payload).insert(ignore_permissions=True)
		return "created"

	doc = frappe.get_doc(doctype, name)
	current = {k: doc.get(k) for k in payload if k != "doctype"}
	if _records_equal(payload, current, json_fields=json_fields, check_fields=check_fields):
		return "skipped"

	if _is_immutable(doc) and not force:
		raise SeedLoadError(
			f"Refusing to mutate active/immutable record {doctype}:{code_value} without force=True"
		)

	if not _is_mutable_draft(doc) and not force:
		raise SeedLoadError(
			f"Refusing to mutate non-draft record {doctype}:{code_value} without force=True"
		)

	if not dry_run:
		for field, value in payload.items():
			doc.set(field, value)
		doc.save(ignore_permissions=True)
	return "updated"


def _is_mutable_draft(doc: frappe.model.document.Document) -> bool:
	status_fields = ("version_status", "profile_status", "family_status", "instance_status", "status")
	for field in status_fields:
		value = doc.get(field)
		if isinstance(value, str) and value.strip():
			return value in {"Draft", "In Progress"}
	return True


def _is_immutable(doc: frappe.model.document.Document) -> bool:
	immutable_flags = ("immutable_after_activation",)
	for field in immutable_flags:
		if int(doc.get(field) or 0):
			return True
	status_fields = ("version_status", "instance_status", "status")
	for field in status_fields:
		value = doc.get(field)
		if value in {"Active", "Published Locked", "Published"}:
			return True
	return False


def _read_yaml(path: Path) -> dict[str, Any]:
	with path.open("r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}


def _stable_hash(payload: dict[str, Any]) -> str:
	canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _records_equal(
	payload: dict[str, Any],
	current: dict[str, Any],
	*,
	json_fields: set[str],
	check_fields: set[str],
) -> bool:
	def norm(field: str, value: Any) -> Any:
		if field in json_fields:
			if isinstance(value, str):
				try:
					return parse_json(value)
				except Exception:
					return value
			return value
		if field in check_fields:
			return int(bool(value))
		return value

	for field, value in payload.items():
		if norm(field, value) != norm(field, current.get(field)):
			return False
	return True

