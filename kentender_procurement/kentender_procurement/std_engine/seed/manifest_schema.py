from __future__ import annotations

from pathlib import Path


class SeedManifestValidationError(ValueError):
	"""Raised when STD seed manifest contract validation fails."""


REQUIRED_KEYS = (
	"manifest_code",
	"seed_package_title",
	"source_document_code",
	"template_code",
	"version_code",
	"profile_code",
	"load_order",
	"idempotency_key",
)

REQUIRED_LOAD_ORDER = [
	"01_source_documents.yaml",
	"02_template_family.yaml",
	"03_template_version.yaml",
	"04_applicability_profiles.yaml",
	"05_parts.yaml",
	"06_sections.yaml",
	"07_clauses",
	"08_parameters",
	"09_forms",
	"10_works_requirements.yaml",
	"11_boq",
	"12_evaluation_rules.yaml",
	"13_contract_carry_forward.yaml",
	"14_extraction_mappings",
	"15_readiness_rules.yaml",
	"16_seed_instance_fixture.yaml",
	"17_generated_output_expectations.yaml",
	"18_addendum_fixture.yaml",
	"19_smoke_expected_results.yaml",
]


def validate_seed_manifest(manifest: dict, package_root: Path) -> None:
	"""Validate manifest structure and deterministic load-order contract."""
	if not isinstance(manifest, dict):
		raise SeedManifestValidationError("Manifest must be a mapping object.")

	for key in REQUIRED_KEYS:
		if key not in manifest:
			raise SeedManifestValidationError(f"Missing required manifest key: {key}")

	for key in (
		"manifest_code",
		"seed_package_title",
		"source_document_code",
		"template_code",
		"version_code",
		"profile_code",
		"idempotency_key",
	):
		value = manifest.get(key)
		if not isinstance(value, str) or not value.strip():
			raise SeedManifestValidationError(f"Manifest key '{key}' must be a non-empty string.")

	if manifest["manifest_code"] != manifest["idempotency_key"]:
		raise SeedManifestValidationError("manifest_code must match idempotency_key.")

	load_order = manifest.get("load_order")
	if not isinstance(load_order, list) or not all(isinstance(i, str) and i.strip() for i in load_order):
		raise SeedManifestValidationError("load_order must be a list of non-empty strings.")

	if load_order != REQUIRED_LOAD_ORDER:
		raise SeedManifestValidationError("load_order does not match required deterministic order.")

	unknown = [entry for entry in load_order if entry not in REQUIRED_LOAD_ORDER]
	if unknown:
		raise SeedManifestValidationError(f"load_order contains unknown entries: {unknown}")

	for entry in load_order:
		entry_path = package_root / entry
		if not entry_path.exists():
			raise SeedManifestValidationError(f"Manifest load entry does not exist: {entry}")
		if entry_path.is_dir():
			yaml_files = list(entry_path.rglob("*.yaml"))
			if not yaml_files:
				raise SeedManifestValidationError(
					f"Manifest directory entry has no yaml files: {entry}"
				)

