# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Saved Account documents a bid may reuse (BDS-CHG-001 §4.7, §5.5 item 4).

The supplier Account keeps reusable evidence (a certificate of incorporation,
a tax compliance certificate, a reservation certificate). Until now the bid
asked for the same files again every time. This says which saved documents suit
which requirement, offers them on the read, and checks a link: the right kind,
still in date and not already in the requirement. Linking still copies the
exact bytes into the bid (`evidence.link_account_evidence_to_bid`), so replacing
the Account copy never changes a bid.

Which requirement takes which kind is owned here, not by the template: the
published definition names an evidence kind in words only, and a mapping in a
release would force a new release for a Bid Submission rule. Only two
requirements have a natural saved document; a tender security, a datasheet,
experience or any per-Tender proof is never offered."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr, getdate

from kentender_procurement.bid_submission.services import labels, supplier_gateway
from kentender_procurement.bid_submission.services.errors import BidSubmissionError

#: (response rule, field) -> the Account evidence types that may serve it.
ALLOWED: dict[tuple[str, str], tuple[str, ...]] = {
	("RR-EVIDENCE-ELIGIBILITY-DOCUMENTS", "evidence"): ("Certificate of incorporation", "Tax compliance certificate", "Joint-venture agreement", "Other"),
	("RR-RESERVATION", "certificate_evidence"): ("Reservation evidence",),
}
WRONG_KIND = "Choose a saved document of the right kind for this requirement."
NONE_FOR_THIS = "Saved documents cannot be used for this requirement. Upload the file."
EXPIRED = "This saved document is out of date. Replace it in your Account or upload a current file."
DUPLICATE = "This saved document is already in this requirement."


def allowed_types(field) -> tuple[str, ...]:
	return ALLOWED.get((field.group.rule_id, field.field_key), ())


def expired(valid_until, at) -> bool:
	"""A document is out of date from the day after its `valid_until`."""
	return bool(valid_until) and getdate(valid_until) < getdate(at)


def account_rows(ctx) -> list[dict[str, Any]]:
	"""The organisation's Account evidence, read once per request; none when no Account provider is configured."""
	cached = getattr(ctx, "_account_evidence_rows", None)
	if cached is None:
		try:
			cached = supplier_gateway.account_evidence(organisation_id=ctx.workspace.lead_organisation)
		except BidSubmissionError:
			cached = []
		ctx._account_evidence_rows = cached
	return cached


def linked(ctx, field) -> set[str]:
	return {cstr(e.get("source")) for e in ctx.evidence.get(field.key, []) if e.get("source")}


def options(ctx, field, *, at) -> list[dict[str, Any]]:
	"""The saved documents offered for this requirement: Available, of an allowed kind and
	not already in it. Never a digest, a file name path or an internal identity."""
	kinds, taken = allowed_types(field), linked(ctx, field)
	return [
		{
			"id": row["evidence_id"], "title": cstr(row.get("title") or row.get("file_name")), "type": row["evidence_type"], "reference": cstr(row.get("reference")),
			"valid_until": labels.date_label(row.get("valid_until")), "expired": expired(row.get("valid_until"), at),
		}
		for row in account_rows(ctx)
		if row.get("status") == "Available" and row.get("evidence_type") in kinds and row["evidence_id"] not in taken
	]


def refusal(ctx, field, row: dict[str, Any], *, at) -> str:
	"""Why this saved document may not be linked to this requirement, or ""."""
	kinds = allowed_types(field)
	if not kinds:
		return NONE_FOR_THIS
	if row.get("evidence_type") not in kinds:
		return WRONG_KIND
	if row["evidence_id"] in linked(ctx, field):
		return DUPLICATE
	if expired(row.get("valid_until"), at):
		return EXPIRED
	return ""
