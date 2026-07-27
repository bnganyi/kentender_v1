# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Deterministic content_addressed_chunked support (synthetic resources; not NSSF)."""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.repository.cas import (
	canonical_json_bytes,
	content_ref_for_bytes,
	get_verified,
	physical_digest_for_bytes,
	put_canonical_json,
)

CHUNKING_ALGORITHM_VERSION = "bwmf-chunk-v1"


def chunk_items(
	items: list[dict[str, Any]],
	*,
	identity_key: str,
	chunk_size: int,
	organization: str = "ORG-UNSPECIFIED",
) -> list[dict[str, Any]]:
	"""Split ordered items into deterministic chunks; store each chunk in CAS."""
	if chunk_size < 1:
		raise ValueError("chunk_size must be >= 1")
	chunks: list[dict[str, Any]] = []
	for index, start in enumerate(range(0, len(items), chunk_size)):
		part = items[start : start + chunk_size]
		data = canonical_json_bytes(part)
		stored = put_canonical_json(part, organization=organization)
		chunks.append(
			{
				"index": index,
				"first_item_key": part[0][identity_key],
				"last_item_key": part[-1][identity_key],
				"item_count": len(part),
				"item_range_start": start,
				"item_range_end": start + len(part),
				"content_ref": stored["content_ref"],
				"chunk_content_digest": physical_digest_for_bytes(data),
				"byte_size": len(data),
				"algorithm": CHUNKING_ALGORITHM_VERSION,
			}
		)
	return chunks


def validate_chunks(
	chunks: list[dict[str, Any]],
	*,
	expected_item_count: int,
	verify_bytes: bool = False,
) -> None:
	"""Reject missing, duplicate, reordered, overlapping, or corrupt chunk metadata."""
	if not chunks:
		raise ValueError("chunks missing")
	indexes = [c.get("index") for c in chunks]
	if indexes != list(range(len(chunks))):
		raise ValueError("chunk indexes must be contiguous zero-based")
	total = 0
	seen_refs: set[str] = set()
	cursor = 0
	for c in chunks:
		ref = c.get("content_ref") or ""
		if ref in seen_refs:
			raise ValueError("duplicate chunk content_ref")
		seen_refs.add(ref)
		if not ref.startswith("bwmf-cas:v1:"):
			raise ValueError("invalid chunk content_ref")
		count = int(c.get("item_count") or 0)
		if count < 1:
			raise ValueError("chunk item_count must be >= 1")
		start = c.get("item_range_start")
		end = c.get("item_range_end")
		if start is not None and end is not None:
			if int(start) != cursor or int(end) != cursor + count:
				raise ValueError("overlapping or gapped item ranges")
			cursor = int(end)
		total += count
		expected_digest = c.get("chunk_content_digest")
		if not expected_digest:
			raise ValueError("chunk_content_digest required")
		declared_size = c.get("byte_size")
		if declared_size is None:
			raise ValueError("chunk byte_size required")
		if verify_bytes:
			raw = get_verified(ref)
			if len(raw) != int(declared_size):
				raise ValueError("incorrect chunk byte_size")
			if physical_digest_for_bytes(raw) != expected_digest:
				raise ValueError("corrupted chunk bytes")
			if content_ref_for_bytes(raw) != ref:
				raise ValueError("corrupted chunk bytes")
	if total != expected_item_count:
		raise ValueError(f"chunk item_count sum {total} != {expected_item_count}")
	if cursor and cursor != expected_item_count:
		raise ValueError("chunk ranges do not cover full item array")
