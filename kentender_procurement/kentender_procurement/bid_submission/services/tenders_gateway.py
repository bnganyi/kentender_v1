# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The one door from Bid Submission into Tenders and STD (BDS-CHG-001 v0.8
plan D3). Bid Submission reads published Tender facts, documents, answers,
candidate notices and the Published Bid Definition only through the
Tenders-owned seams named here, so a Tenders change has one place to land."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tenders.services import bid_definition, bidder_projection

ROOT_FIELDS = ["name", "tender_reference", "overall_status", "submission_deadline", "clarification_deadline", "publication", "fixture_namespace"]


def available_tenders(*, at) -> list[dict[str, Any]]:
	return bidder_projection.available_tenders(at=at)


def published_tender(reference: str, *, at) -> dict[str, Any] | None:
	return bidder_projection.published_tender(reference, at=at)


def tender_root(reference: str) -> dict[str, Any] | None:
	"""The published Tender's identity and dates, or None when no published
	Tender has that reference."""
	name = bidder_projection.resolve_published(reference)
	return frappe.db.get_value("Tender", name, ROOT_FIELDS, as_dict=True) if name else None


def availability(reference: str, *, at) -> str | None:
	return bidder_projection.availability(reference, at=at)


def current_definition(tender_name: str) -> dict[str, Any] | None:
	"""The bidder-current (Effective) Published Bid Definition."""
	return bid_definition.current(tender_name)


def definition_for(tender_name: str, definition_version) -> dict[str, Any] | None:
	return bid_definition.definition_for(tender_name, definition_version)


def verify_definition_digest(definition: dict[str, Any]) -> bool:
	from kentender_procurement.std_templates.compiler.definition import verify_definition_digest as verify

	return bool(definition) and verify(definition)


def release_status(release_id: str) -> dict[str, Any]:
	"""The bound template release's lifecycle, site switch and live health;
	a command re-hashes the release assets (STD-TPL-IMP-001 `bid_work_status`)."""
	from kentender_procurement.std_templates.services import runtime

	return runtime.bid_work_status(release_id, verify=True)


def submit_clarification(*, tender: str, candidate_registration_id: str, question: str, inbound_event_id: str, received_at, producer: str) -> dict[str, Any]:
	"""Hand one supplier question to Tenders' clarification intake as the
	bidder-facing producer identity (TPR-CHG-001 v0.12 §4.9). Tenders owns the
	question from here; Bid Submission stores no parallel record."""
	from kentender_procurement.tenders.services import clarifications

	return clarifications.receive_tender_clarification(
		tender=tender, candidate_registration_id=candidate_registration_id, question=question, inbound_event_id=inbound_event_id, received_at=received_at, user=producer,
	)


def addendum_reference(tender_name: str, addendum_id: str) -> str:
	"""The public reference of one of the Tender's addenda (the acknowledgement
	label names it)."""
	return frappe.db.get_value("Tender Addendum", {"name": addendum_id, "tender": tender_name}, "addendum_reference") or ""


def map_addendum(tender_name: str, *, from_version: int, to_version: int) -> dict[str, Any]:
	"""`MapBidDefinitionAddendum`: the stored identity maps from one supplier
	definition version to a later effective one, one step per addendum."""
	return bid_definition.map_bid_definition_addendum(tender=tender_name, from_version=from_version, to_version=to_version)
