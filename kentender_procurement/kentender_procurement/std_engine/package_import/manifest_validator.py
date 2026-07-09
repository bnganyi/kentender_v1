# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Manifest validation for STD seed packages."""

from __future__ import annotations

from typing import Any


REQUIRED_MANIFEST_KEYS: tuple[str, ...] = (
	"package_code",
	"family_code",
	"version_code",
	"schema_version",
	"authority",
)


def validate_manifest(manifest: dict[str, Any] | None) -> list[str]:
	errors: list[str] = []
	if not isinstance(manifest, dict) or not manifest:
		return ["manifest.json is missing or not a JSON object"]
	for key in REQUIRED_MANIFEST_KEYS:
		value = manifest.get(key)
		if value is None or (isinstance(value, str) and not value.strip()):
			errors.append(f"manifest.{key} is required")
	return errors
