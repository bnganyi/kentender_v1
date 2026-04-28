from __future__ import annotations

from pathlib import Path
from typing import Any

import frappe
import yaml

from .manifest_schema import SeedManifestValidationError, validate_seed_manifest


PLACEHOLDER_TEXT_MARKERS = ("sample text", "lorem ipsum")
MANDATORY_SECTION_CODES = {
	"DOC1-WORKS-SECTION-INVITATION",
	"DOC1-WORKS-SECTION-I-ITT",
	"DOC1-WORKS-SECTION-II-TDS",
	"DOC1-WORKS-SECTION-III-EVALUATION",
	"DOC1-WORKS-SECTION-IV-FORMS",
	"DOC1-WORKS-SECTION-V-BOQ",
	"DOC1-WORKS-SECTION-VI-SPECIFICATIONS",
	"DOC1-WORKS-SECTION-VII-DRAWINGS",
	"DOC1-WORKS-SECTION-VIII-GCC",
	"DOC1-WORKS-SECTION-IX-SCC",
	"DOC1-WORKS-SECTION-X-CONTRACT-FORMS",
}


class SeedPackageValidationError(frappe.ValidationError):
	"""Validation error for seed package command."""


@frappe.whitelist()
def validate_seed_package(package_path: str) -> dict[str, Any]:
	"""Validate seed package structure and business consistency before loading."""
	root = Path(package_path).resolve()
	manifest_path = root / "00_manifest.yaml"
	if not manifest_path.exists():
		raise SeedPackageValidationError(f"Missing manifest file: {manifest_path}")

	manifest = _read_yaml(manifest_path)
	try:
		validate_seed_manifest(manifest, root)
	except SeedManifestValidationError as exc:
		raise SeedPackageValidationError(f"Manifest validation failed: {exc}") from exc

	payloads = _read_payloads(root, manifest["load_order"])
	_validate_no_placeholder_legal_text(payloads)
	_validate_unique_business_codes(payloads)
	_validate_references(payloads)
	_validate_sections(payloads)
	_validate_mapping_presence(payloads)
	_validate_required_groups(payloads)

	return {"status": "ok", "package_path": str(root), "validated_groups": sorted(payloads.keys())}


def _read_payloads(root: Path, load_order: list[str]) -> dict[str, list[dict[str, Any]]]:
	aggregated: dict[str, list[dict[str, Any]]] = {}
	for entry in load_order:
		entry_path = root / entry
		files = sorted(entry_path.rglob("*.yaml")) if entry_path.is_dir() else [entry_path]
		for file_path in files:
			payload = _read_yaml(file_path)
			for key, value in payload.items():
				records = value if isinstance(value, list) else [value]
				aggregated.setdefault(key, []).extend([r for r in records if isinstance(r, dict)])
	return aggregated


def _validate_no_placeholder_legal_text(payloads: dict[str, list[dict[str, Any]]]) -> None:
	for group, records in payloads.items():
		for idx, record in enumerate(records):
			for field, value in record.items():
				if not isinstance(value, str):
					continue
				lower = value.lower()
				for marker in PLACEHOLDER_TEXT_MARKERS:
					if marker in lower:
						raise SeedPackageValidationError(
							f"Placeholder legal text detected in {group}[{idx}].{field}: contains '{marker}'"
						)


def _validate_unique_business_codes(payloads: dict[str, list[dict[str, Any]]]) -> None:
	for group, records in payloads.items():
		code_fields = [k for k in records[0].keys()] if records else []
		code_field = next((f for f in code_fields if f.endswith("_code")), None)
		if not code_field:
			continue
		seen: set[str] = set()
		for record in records:
			code = str(record.get(code_field) or "").strip()
			if not code:
				continue
			if code in seen:
				raise SeedPackageValidationError(f"Duplicate business code in {group}: {code}")
			seen.add(code)


def _validate_references(payloads: dict[str, list[dict[str, Any]]]) -> None:
	known_codes: set[str] = set()
	for records in payloads.values():
		for record in records:
			for field, value in record.items():
				if field.endswith("_code") and isinstance(value, str) and value.strip():
					known_codes.add(value.strip())

	for group, records in payloads.items():
		for idx, record in enumerate(records):
			for field, value in record.items():
				if not field.endswith("_code") or field in {"rule_code", "manifest_code"}:
					continue
				if not isinstance(value, str) or not value.strip():
					continue
				if value.strip() not in known_codes:
					raise SeedPackageValidationError(
						f"Unresolved reference in {group}[{idx}].{field}: {value}"
					)


def _validate_sections(payloads: dict[str, list[dict[str, Any]]]) -> None:
	sections = payloads.get("sections", [])
	by_code = {s.get("section_code"): s for s in sections if s.get("section_code")}

	missing = sorted(MANDATORY_SECTION_CODES - set(by_code.keys()))
	if missing:
		raise SeedPackageValidationError(f"Missing mandatory sections: {missing}")

	itt = by_code.get("DOC1-WORKS-SECTION-I-ITT")
	gcc = by_code.get("DOC1-WORKS-SECTION-VIII-GCC")
	tds = by_code.get("DOC1-WORKS-SECTION-II-TDS")
	scc = by_code.get("DOC1-WORKS-SECTION-IX-SCC")
	if itt and itt.get("editability") != "Locked":
		raise SeedPackageValidationError("ITT section editability must be Locked.")
	if gcc and gcc.get("editability") != "Locked":
		raise SeedPackageValidationError("GCC section editability must be Locked.")
	if tds and tds.get("editability") != "Parameter Only":
		raise SeedPackageValidationError("TDS section editability must be Parameter Only.")
	if scc and scc.get("editability") != "Parameter Only":
		raise SeedPackageValidationError("SCC section editability must be Parameter Only.")


def _validate_mapping_presence(payloads: dict[str, list[dict[str, Any]]]) -> None:
	dem = payloads.get("dem_mappings", [])
	dsm = payloads.get("dsm_mappings", [])
	if not dem:
		raise SeedPackageValidationError("Section III must have DEM mappings (dem_mappings empty).")
	if not dsm:
		raise SeedPackageValidationError("Section IV must have DSM mappings (dsm_mappings empty).")


def _validate_required_groups(payloads: dict[str, list[dict[str, Any]]]) -> None:
	if not payloads.get("boq_definition"):
		raise SeedPackageValidationError(
			"BOQ definition missing (expected in 11_boq/11a_boq_definition.yaml)."
		)
	if not payloads.get("scc_parameters"):
		raise SeedPackageValidationError(
			"SCC parameters missing (expected in 08_parameters/08c_scc_parameters.yaml)."
		)
	if not payloads.get("readiness_rules"):
		raise SeedPackageValidationError(
			"Readiness rules missing (expected in 15_readiness_rules.yaml)."
		)


def _read_yaml(path: Path) -> dict[str, Any]:
	with path.open("r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}

