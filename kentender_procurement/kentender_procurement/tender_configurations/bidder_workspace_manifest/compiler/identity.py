# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable identity from versioned lineage tuples (never labels / indexes / PDF pages)."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable


class IdentityCollisionError(ValueError):
	pass


def lineage_id(*parts: Any) -> str:
	"""Deterministic opaque id from a versioned lineage tuple."""
	material = "\u001f".join("" if p is None else str(p) for p in parts)
	digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
	return f"id_{digest}"


def section_instance_id(*, std_family: str, section_key: str, blueprint_version: Any, compiler_version: str) -> str:
	return lineage_id("section", std_family, section_key, blueprint_version, compiler_version)


def resource_logical_id(*, std_family: str, resource_key: str, source_digest: str, compiler_version: str) -> str:
	return lineage_id("resource", std_family, resource_key, source_digest, compiler_version)


def detect_collisions(ids: Iterable[str]) -> None:
	seen: set[str] = set()
	for i in ids:
		if i in seen:
			raise IdentityCollisionError(f"stable id collision: {i}")
		seen.add(i)
