# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Read and inspect STD seed package zips without database writes."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kentender_procurement.std_engine.package_import.checksum_verifier import ChecksumFailure, verify_package_checksums
from kentender_procurement.std_engine.package_import.manifest_validator import validate_manifest
from kentender_procurement.std_engine.package_import.package_contract import (
	OPTIONAL_WHEN_PRESENT,
	PAYLOAD_PATH_BY_KEY,
	REQUIRED_ANY_IMPORT,
	REQUIRED_VERTICAL_SLICE,
	SKIPPED_PREFIXES,
)


class PackageReaderError(Exception):
	pass


@dataclass
class PackageInspectionResult:
	zip_path: str
	package_root: str
	package_id: str
	family_code: str
	version_code: str
	manifest: dict[str, Any]
	checksums: dict[str, Any]
	files_total: int
	files_listed: list[str]
	missing_required_files: list[str]
	missing_optional_files: list[str]
	checksum_status: str
	checksum_failures: list[dict[str, str]]
	parsed_payloads: dict[str, Any]
	activation_allowed: bool
	activation_blockers: list[str]
	skipped_paths: list[str]
	manifest_errors: list[str] = field(default_factory=list)

	def to_dict(self) -> dict[str, Any]:
		return {
			"zip_path": self.zip_path,
			"package_root": self.package_root,
			"package_id": self.package_id,
			"family_code": self.family_code,
			"version_code": self.version_code,
			"files_total": self.files_total,
			"files_listed": self.files_listed,
			"missing_required_files": self.missing_required_files,
			"missing_optional_files": self.missing_optional_files,
			"checksum_status": self.checksum_status,
			"checksum_failures": self.checksum_failures,
			"activation_allowed": self.activation_allowed,
			"activation_blockers": self.activation_blockers,
			"skipped_paths": self.skipped_paths,
			"manifest_errors": self.manifest_errors,
			"parsed_payload_keys": sorted(self.parsed_payloads.keys()),
		}


class PackageReader:
	def __init__(self, zip_path: str | Path) -> None:
		self.zip_path = Path(zip_path)

	def inspect(self) -> PackageInspectionResult:
		if not self.zip_path.is_file():
			raise PackageReaderError(f"Package zip not found: {self.zip_path}")

		with zipfile.ZipFile(self.zip_path, "r") as zf:
			package_root = _detect_package_root(zf)
			files_listed = _list_package_files(zf, package_root)
			manifest = _read_json(zf, package_root, "manifest.json")
			checksums = _read_json(zf, package_root, "checksums.json")
			manifest_errors = validate_manifest(manifest)

			missing_required = [
				rel for rel in (*REQUIRED_ANY_IMPORT, *REQUIRED_VERTICAL_SLICE) if rel not in files_listed
			]
			missing_optional = [rel for rel in OPTIONAL_WHEN_PRESENT if rel not in files_listed]
			skipped_paths = [rel for rel in files_listed if _is_skipped(rel)]

			checksum_status, checksum_failures = verify_package_checksums(
				checksums=checksums,
				read_file=lambda rel: zf.read(package_root + rel),
			)

			parsed_payloads = _parse_payloads(zf, package_root, files_listed)

		return PackageInspectionResult(
			zip_path=str(self.zip_path),
			package_root=package_root,
			package_id=str(manifest.get("package_code") or ""),
			family_code=str(manifest.get("family_code") or ""),
			version_code=str(manifest.get("version_code") or ""),
			manifest=manifest,
			checksums=checksums,
			files_total=len(files_listed),
			files_listed=files_listed,
			missing_required_files=missing_required,
			missing_optional_files=missing_optional,
			checksum_status=checksum_status,
			checksum_failures=[
				{"relative_path": f.relative_path, "expected": f.expected, "actual": f.actual}
				for f in checksum_failures
			],
			parsed_payloads=parsed_payloads,
			activation_allowed=bool(manifest.get("activation_allowed")),
			activation_blockers=list(manifest.get("activation_blockers") or []),
			skipped_paths=skipped_paths,
			manifest_errors=manifest_errors,
		)


def _detect_package_root(zf: zipfile.ZipFile) -> str:
	manifest_paths = [name for name in zf.namelist() if _is_package_manifest_path(name)]
	if not manifest_paths:
		raise PackageReaderError("manifest.json not found in package zip")
	# Prefer canonical seed package root; ignore calibration/fixture manifests.
	manifest_paths.sort(
		key=lambda p: (
			0 if "seed_package_v0_2" in p else 1,
			1 if "/fixtures/" in p else 0,
			p,
		)
	)
	manifest_path = manifest_paths[0]
	if "/" in manifest_path:
		return manifest_path.rsplit("/", 1)[0] + "/"
	return ""


def _is_package_manifest_path(path: str) -> bool:
	return path.endswith("/manifest.json") or path == "manifest.json"


def _list_package_files(zf: zipfile.ZipFile, package_root: str) -> list[str]:
	files: list[str] = []
	prefix_len = len(package_root)
	for name in zf.namelist():
		if not name.startswith(package_root) or name.endswith("/"):
			continue
		files.append(name[prefix_len:])
	return sorted(files)


def _read_json(zf: zipfile.ZipFile, package_root: str, relative_path: str) -> dict[str, Any]:
	try:
		raw = zf.read(package_root + relative_path)
	except KeyError as exc:
		raise PackageReaderError(f"Missing required file: {relative_path}") from exc
	try:
		data = json.loads(raw.decode("utf-8"))
	except json.JSONDecodeError as exc:
		raise PackageReaderError(f"Invalid JSON in {relative_path}: {exc}") from exc
	if not isinstance(data, dict):
		raise PackageReaderError(f"Expected JSON object in {relative_path}")
	return data


def _parse_payloads(
	zf: zipfile.ZipFile,
	package_root: str,
	files_listed: list[str],
) -> dict[str, Any]:
	payloads: dict[str, Any] = {}
	for key, relative_path in PAYLOAD_PATH_BY_KEY.items():
		if relative_path not in files_listed:
			continue
		payloads[key] = _read_json(zf, package_root, relative_path)
	return payloads


def _is_skipped(relative_path: str) -> bool:
	return any(relative_path.startswith(prefix) for prefix in SKIPPED_PREFIXES)
