# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`PrepareReplacementBid` (BDS-CHG-001 v0.8 §5.8, §7.3, §10.15).

Before the deadline the Authorised Signatory reopens the bid as a successor
Draft: the next Draft version, the organisation's working responses and the
current published requirements (an effective addendum still moves the Draft
on its first change). The submitted Version and its receipt stay current and
sealed until a replacement is accepted into the tender box; if the
replacement is never submitted, the deadline leaves them current. After a
withdrawal the same command is **Start replacement**: a new Draft with no
current submission.

The replacement is then submitted through `SubmitBid` with every rule of an
initial submission."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import addendum, bid_context, clock, readiness, records, signature
from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services.errors import fail

OPEN_DRAFT = ("Draft", "Needs attention", "Ready to submit")


def derived_status(ctx) -> str:
	if addendum.pending(ctx) is not None:
		return "Needs attention"
	return readiness.bid_status(readiness.evaluate(ctx, attention=addendum.attention(ctx)))


def prepare_replacement_bid(*, bid_reference: str, expected_record_version=None, idempotency_key: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"bid_reference": cstr(bid_reference), "expected_record_version": cstr(expected_record_version)}
	return records.idempotent(idempotency_key, "PrepareReplacementBid", payload, lambda: _prepare(actor, bid_reference, expected_record_version, organisation), actor=actor, organisation=organisation)


def _prepare(actor: str, bid_reference: str, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	signature.signatory_of(ctx, actor)
	authz.active_account(ctx.workspace.lead_organisation)
	ws = ctx.workspace
	if ws.status not in ("Submitted", "Withdrawn"):
		fail("BDS_STALE_VERSION", detail={"record_version": int(ws.record_version or 0)})  # nothing submitted to replace, or a replacement is already open
	signature.require_before_deadline(ctx, at)
	records.check_version(ws, expected_record_version)
	started_from = ws.status
	status = derived_status(ctx)
	records.bump(ws, status=status, status_since=at, current_draft_version=int(ws.current_draft_version or 0) + 1)
	records.emit(
		"ReplacementDraftPrepared", tender=ws.tender, arrangement=ctx.arrangement.name, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at,
		payload={"started_from": started_from, "current_submission_version": cstr(ws.current_submission_version), "draft_version": ws.current_draft_version},
	)
	return {"ok": True, "bid_reference": ws.name, "status": status, "draft_version": int(ws.current_draft_version), "record_version": int(ws.record_version), "started_from": started_from}
