# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's view of the sealed close and the tender box (BOP-CHG-001
v0.10 §3, §7; plan D4). It goes only through Bid Submission's published seam,
`bid_submission.services.opening_gateway`, and passes the four TRUST-ADR-001
v0.1 §4 outcomes through unchanged."""

from __future__ import annotations

from typing import Any

from kentender_procurement.bid_submission.services import opening_gateway as seam

VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = seam.VERIFIED, seam.REJECTED, seam.UNAVAILABLE, seam.INDETERMINATE


def closed_manifest(tender: str) -> dict[str, Any] | None:
	return seam.closed_manifest(tender)


def current_envelopes(manifest: dict[str, Any]) -> list[dict[str, Any]]:
	"""The current timely envelopes to open, in receipt order: Submitted
	versions in the box's own inventory. Withdrawn and superseded versions stay
	as lineage and are never opened (BOP-CHG-001 v0.10 §5, BOP-N03, BOP-N04)."""
	payload = manifest["payload"]
	inventory = set(payload["closed_box"].get("custody_inventory") or [])
	rows = [e for e in payload["envelopes"] if e["status"] == "Submitted" and e["envelope_id"] in inventory]
	return sorted(rows, key=lambda e: (e["accepted_at"], e["envelope_id"]))


def acknowledge(handoff_id: str) -> None:
	seam.acknowledge_handoff(handoff_id)


def healthy() -> bool:
	return seam.custody_healthy()


def confirm_participation(*, tender: str, member: str, independent: bool, manifest_digest: str, roster_digest: str, correlation_id: str) -> dict[str, Any]:
	return seam.confirm_custody_participation(tender=tender, member=member, independent=independent, manifest_digest=manifest_digest, roster_digest=roster_digest,
		correlation_id=correlation_id)


def reveal(*, tender: str, envelope_id: str, manifest_digest: str, roster_digest: str, correlation_id: str) -> dict[str, Any]:
	return seam.reveal_envelope(tender=tender, envelope_id=envelope_id, manifest_digest=manifest_digest, roster_digest=roster_digest, correlation_id=correlation_id)
