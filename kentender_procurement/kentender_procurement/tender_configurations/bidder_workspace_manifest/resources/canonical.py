# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Project, order, and digest canonical resource item arrays."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.jcs import (
	pack_equivalent_digest,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.compiler.ordering import (
	sort_by_keys,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.resources.item_schemas import (
	FORBIDDEN_ITEM_KEYS,
	NSSF_RESOURCE_ORDER,
	NSSF_RESOURCE_SPECS,
)


def project_item(row: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
	out: dict[str, Any] = {}
	for k in fields:
		if k not in row:
			raise ValueError(f"canonical item missing required field {k!r}")
		if k in FORBIDDEN_ITEM_KEYS:
			raise ValueError(f"forbidden field {k!r}")
		out[k] = row[k]
	extra = set(row.keys()) - set(fields) - FORBIDDEN_ITEM_KEYS
	# Drop unknown non-forbidden keys silently (extraction noise); forbid listed keys if present
	for k in row:
		if k in FORBIDDEN_ITEM_KEYS:
			raise ValueError(f"forbidden field present: {k!r}")
	_ = extra
	return out


def canonicalize_items(
	rows: list[dict[str, Any]],
	*,
	fields: tuple[str, ...],
	ordering_contract: list[str],
	identity_key: str,
) -> list[dict[str, Any]]:
	projected = [project_item(r, fields) for r in rows]
	ordered = sort_by_keys(projected, tuple(ordering_contract))
	seen: set[Any] = set()
	for row in ordered:
		ident = row.get(identity_key)
		if ident in seen:
			raise ValueError(f"duplicate item identity {identity_key}={ident!r}")
		seen.add(ident)
	return ordered


def logical_resource_digest(items: list[dict[str, Any]]) -> str:
	"""§7.1: NFC + sorted-key compact JSON + SHA-256 over the ordered logical array."""
	return pack_equivalent_digest(items)


def descriptor_set_digest(resource_digests_in_order: list[str]) -> str:
	"""Ordered descriptor-set digest over the nine (or N) resource digests."""
	return pack_equivalent_digest(list(resource_digests_in_order))


def freeze_nssf_resources_from_collections(
	collections: dict[str, Any],
) -> dict[str, dict[str, Any]]:
	"""Build frozen resource payloads from Phase 3 collections."""
	out: dict[str, dict[str, Any]] = {}
	digests: list[str] = []
	for rid in NSSF_RESOURCE_ORDER:
		spec = NSSF_RESOURCE_SPECS[rid]
		rows = list(collections.get(spec["collection"]) or [])
		items = canonicalize_items(
			rows,
			fields=spec["fields"],
			ordering_contract=list(spec["ordering_contract"]),
			identity_key=spec["identity_key"],
		)
		digest = logical_resource_digest(items)
		digests.append(digest)
		out[rid] = {
			"resource_id": rid,
			"resource_type": spec["resource_type"],
			"schema_ref": spec["schema_ref"],
			"schema_version": spec["schema_version"],
			"item_count": len(items),
			"ordering_contract": list(spec["ordering_contract"]),
			"resource_digest": digest,
			"items": items,
		}
	out["__descriptor_set_digest__"] = descriptor_set_digest(digests)
	out["__resource_digests__"] = digests
	return out
