# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published Tenders seam for Bid Opening (BOP-CHG-001 v0.10 §3, §5,
§7 PrepareOpeningCase, AppointOpeningCommittee, ConsumeTenderCancellation;
plan D8). Additive: no Tenders rule, record or screen changes.

Bid Opening reads the Tender only through these functions:

- `opening_candidates()`: Tenders that are published (open or with the
  submission period ended) or cancelled, for the opening sweep;
- `tender_facts(tender)`: reference, title, status, the effective deadline
  (the opening time equals it: BOP-CHG-001 v0.10 §1) and any cancellation;
- `processing_actors(tender)`: the people who prepared, submitted, approved
  or authorised this Tender, for the independent-member check (§7
  AppointOpeningCommittee "one demonstrably independent of direct
  processing")."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

PUBLISHED = ("Published — open", "Submission period ended")
CANCELLED = "Cancelled"


def opening_candidates() -> list[str]:
	return frappe.get_all("Tender", filters={"overall_status": ("in", (*PUBLISHED, CANCELLED)), "published_at": ("is", "set")}, pluck="name", order_by="published_at asc")


def tender_facts(tender: str) -> dict[str, Any] | None:
	root = frappe.db.get_value("Tender", tender, ["name", "tender_reference", "requirement_title", "overall_status", "submission_deadline", "published_at",
		"approved_version", "current_version", "cancellation", "fixture_namespace"], as_dict=True)
	if not root:
		return None
	from kentender_procurement.tenders.services import serializer

	version = frappe.get_doc("Tender Version", root.approved_version or root.current_version) if (root.approved_version or root.current_version) else None
	title = cstr((serializer.officer_state(version) if version else {}).get("tender_title") or root.requirement_title)
	cancellation = None
	if root.cancellation:
		row = frappe.db.get_value("Tender Cancellation", root.cancellation, ["name", "decided_at", "decided_by"], as_dict=True)
		cancellation = {"reference": row.name, "cancelled_at": row.decided_at, "decided_by": row.decided_by} if row else None
	return {
		"tender": root.name, "tender_reference": root.tender_reference, "title": title, "overall_status": cstr(root.overall_status),
		"published": cstr(root.overall_status) in PUBLISHED or bool(root.published_at), "submission_deadline": root.submission_deadline,
		"opening_datetime": root.submission_deadline, "cancelled": cstr(root.overall_status) == CANCELLED, "cancellation": cancellation,
		"fixture_namespace": cstr(root.fixture_namespace),
	}


def definition_labels(tender: str, definition_version=None) -> dict[str, Any]:
	"""The published bid definition's own words, for rendering a revealed bid
	package (Bid Opening FU-BOP-15): each task's label by section id, and each
	response's label by response id with the addendum reference filled in.
	`{bidder_name}` is left for the renderer, which reads it from the package.
	Empty for an unknown Tender or version."""
	from kentender_procurement.tenders.services import bid_definition

	stored = bid_definition.definition_for(tender, definition_version) if definition_version else bid_definition.current(tender)
	if not stored:
		return {"tasks": {}, "responses": {}}
	definition = stored.get("definition") or {}
	responses: dict[str, str] = {}
	columns: dict[str, list[dict[str, str]]] = {}
	for row in definition.get("response_rows") or []:
		field = row.get("field") or {}
		if field.get("control_id") == "CTL-ROW-GROUP" and row.get("response_id"):
			heads = (row.get("validation") or {}).get("parameters", {}).get("columns") or []
			columns[cstr(row["response_id"])] = [{"key": cstr(c.get("key")), "label": cstr(c.get("label"))} for c in heads]
		text = cstr(field.get("label"))
		if "addendum_reference" in (field.get("label_parameters") or []):
			addendum = cstr((row.get("identity") or {}).get("immutable_source_id"))
			reference = frappe.db.get_value("Tender Addendum", {"name": addendum, "tender": tender}, "addendum_reference") if addendum else ""
			text = text.replace("{addendum_reference}", reference or "the addendum")
		if row.get("response_id") and text:
			responses[cstr(row["response_id"])] = text
	out: dict[str, Any] = {"tasks": {cstr(s.get("section_id")): cstr(s.get("label")) for s in definition.get("sections") or [] if s.get("section_id")}, "responses": responses}
	# release 1.4: the columns of each table answer, and the answers a group repeated per entity holds
	entity_responses = [rid for s in definition.get("sections") or [] for g in s.get("groups") or [] if g.get("repetition") == "per_entity" for rid in g.get("response_ids") or []]
	if columns:
		out["columns"] = columns
	if entity_responses:
		out["entity_responses"] = entity_responses
	return out


def processing_actors(tender: str) -> set[str]:
	people: set[str] = set()
	for row in frappe.get_all("Tender Version", filters={"tender": tender}, fields=["prepared_by", "submitted_by", "approved_by"], limit_page_length=0):
		people.update(v for v in (row.prepared_by, row.submitted_by, row.approved_by) if v)
	for row in frappe.get_all("Tender Publication", filters={"tender": tender}, fields=["authorised_by"], limit_page_length=0):
		if row.authorised_by:
			people.add(row.authorised_by)
	return people
