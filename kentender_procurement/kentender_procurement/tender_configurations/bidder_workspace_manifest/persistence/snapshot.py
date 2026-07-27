# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Closed immutable submission snapshot payload (Phase 2A)."""

from __future__ import annotations

import json
from typing import Any

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.decimal_money import (
	decimal_to_storage_str,
	exact_decimal_roundtrip,
)

SNAPSHOT_SCHEMA_VERSION = "1.0.0"

REQUIRED_SNAPSHOT_KEYS: frozenset[str] = frozenset(
	{
		"snapshot_schema_version",
		"submission_id",
		"submission_version",
		"organization",
		"bidder_party",
		"jv_identity",
		"workspace_id",
		"manifest",
		"resources",
		"responses",
		"evidence",
		"legal_texts",
		"confirmations",
		"authority",
		"totals",
	}
)


def build_submission_snapshot(
	*,
	submission_id: str,
	submission_version: int,
	organization: str,
	bidder_party: str,
	workspace_id: str,
	manifest: dict[str, Any],
	resources: list[dict[str, Any]] | None = None,
	responses: list[dict[str, Any]] | None = None,
	evidence: list[dict[str, Any]] | None = None,
	legal_texts: list[dict[str, Any]] | None = None,
	confirmations: list[dict[str, Any]] | None = None,
	authority: list[dict[str, Any]] | None = None,
	jv_identity: dict[str, Any] | None = None,
	totals: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Build a closed snapshot binding exact versioned identities.

	Money in ``totals`` must be str/Decimal (never float); stored as decimal strings.
	"""
	totals = totals or {}
	money_totals: dict[str, str] = {}
	for key, value in totals.items():
		money_totals[key] = decimal_to_storage_str(exact_decimal_roundtrip(value))

	snap = {
		"snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
		"submission_id": submission_id,
		"submission_version": int(submission_version),
		"organization": organization,
		"bidder_party": bidder_party,
		"jv_identity": jv_identity
		or {
			"party_ref": bidder_party,
			"party_version": "1",
			"capacity": "sole",
		},
		"workspace_id": workspace_id,
		"manifest": {
			"manifest_id": manifest["manifest_id"],
			"manifest_version": int(manifest["manifest_version"]),
			"payload_digest": manifest["payload_digest"],
			"manifest_doc": manifest.get("manifest_doc"),
		},
		"resources": resources or [],
		"responses": responses or [],
		"evidence": evidence or [],
		"legal_texts": legal_texts or [],
		"confirmations": confirmations or [],
		"authority": authority or [],
		"totals": money_totals,
	}
	assert_closed_submission_snapshot(snap)
	return snap


def assert_closed_submission_snapshot(snapshot: dict[str, Any]) -> None:
	missing = sorted(REQUIRED_SNAPSHOT_KEYS - set(snapshot.keys()))
	if missing:
		raise ValueError(f"submission snapshot missing keys: {missing}")
	if snapshot.get("snapshot_schema_version") != SNAPSHOT_SCHEMA_VERSION:
		raise ValueError("unsupported snapshot_schema_version")
	for key in ("manifest_id", "manifest_version", "payload_digest"):
		if key not in (snapshot.get("manifest") or {}):
			raise ValueError(f"submission snapshot.manifest missing {key}")
	for amount in (snapshot.get("totals") or {}).values():
		if isinstance(amount, float):
			raise TypeError("float is not allowed in submission snapshot totals")
		exact_decimal_roundtrip(amount)


def snapshot_to_json(snapshot: dict[str, Any]) -> str:
	assert_closed_submission_snapshot(snapshot)
	return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
