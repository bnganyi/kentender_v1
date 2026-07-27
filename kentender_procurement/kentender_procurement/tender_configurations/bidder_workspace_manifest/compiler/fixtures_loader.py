# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Load closed machine-readable fixture packs for tests (not production entry points)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.types import (
	CompileRequestDTO,
	SourceSet,
)

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixtures_root() -> Path:
	return _FIXTURES


def load_json(rel: str) -> Any:
	path = _FIXTURES / rel
	with path.open(encoding="utf-8") as fh:
		return json.load(fh)


def source_set_from_raw(raw: dict[str, Any], *, shuffle_keys: bool = False) -> SourceSet:
	"""Production-shaped injection: bind an already-digitized source object graph."""
	keys = [
		"std_source",
		"catalogue",
		"blueprint",
		"manifest_contract",
		"tender_configuration",
		"document_package",
	]
	if shuffle_keys:
		keys = list(reversed(keys))
	return SourceSet(raw=raw, insertion_order=keys)


def load_nssf_calibration_source_set(*, shuffle_keys: bool = False) -> SourceSet:
	return source_set_from_raw(load_json("nssf_calibration/source_set.json"), shuffle_keys=shuffle_keys)


def load_synthetic_std_source_set(*, shuffle_keys: bool = False) -> SourceSet:
	return source_set_from_raw(load_json("synthetic_std_profile/source_set.json"), shuffle_keys=shuffle_keys)


def compile_request_from_source_set(raw: dict[str, Any], **overrides: Any) -> CompileRequestDTO:
	cr = raw["compile_request"]
	dto = CompileRequestDTO(
		compile_mode=cr["compile_mode"],
		target_manifest_id=cr["target_manifest_id"],
		target_manifest_version=int(cr["target_manifest_version"]),
		published_tender_ref=cr["published_tender_ref"],
		published_tender_version=int(cr["published_tender_version"]),
		compiler_version=cr.get("compiler_version") or "1.0.0",
		expected_input_digests=dict(cr.get("expected_input_digests") or {}),
	)
	gp = raw.get("golden_projection_payload")
	if isinstance(gp, dict):
		# optional — NSSF only
		pass
	# Prefer golden control when present on disk
	golden_path = _FIXTURES / "nssf_calibration" / "golden_projection.json"
	if golden_path.exists() and raw.get("profile") == "nssf_calibration":
		gp_full = json.loads(golden_path.read_text(encoding="utf-8"))
		dto.compiler_run_id = gp_full["control"]["compiler_run_id"]
		dto.generated_by = gp_full["control"]["generated_by"]
		dto.generated_at = gp_full["control"]["generated_at"]
		dto.validation_report_ref = gp_full["control"].get("validation_report_ref") or ""
	for k, v in overrides.items():
		setattr(dto, k, v)
	return dto


def nssf_compile_request(**overrides: Any) -> CompileRequestDTO:
	raw = load_json("nssf_calibration/source_set.json")
	return compile_request_from_source_set(raw, **overrides)


def synthetic_compile_request(**overrides: Any) -> CompileRequestDTO:
	raw = load_json("synthetic_std_profile/source_set.json")
	return compile_request_from_source_set(raw, **overrides)
