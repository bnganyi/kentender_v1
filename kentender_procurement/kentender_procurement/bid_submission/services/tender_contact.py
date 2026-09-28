# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bid's Tender contact (BDS-CHG-001 v0.8 §4.3 and §4.4.8).

The Tender contact is bid-specific: Start bid pre-fills it from the person
who starts the bid, it is required before the Company task can be Complete,
and it never changes the organisation's Account contacts or another bid.
Template release 1.2 shows it read-only as the tenderer's authorised
representative (owner decision, 27 Sep 2026: "3. Tender contact").

BDS-CHG-001 v0.8 §7.2 names no command for it; `UpdateTenderContact` is
built here so the telephone number can be given (follow-up FU-V08-34)."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.utils import cstr, validate_email_address

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import bid_context, clock, records, save
from kentender_procurement.bid_submission.services.errors import field_errors

PHONE = re.compile(r"^\+?[0-9][0-9 ()-]{6,19}$")


def update_tender_contact(*, bid_reference: str, email: str, phone: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "email": cstr(email).strip().lower(), "phone": cstr(phone).strip(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "UpdateTenderContact", payload, lambda: _update(actor=actor, **payload), actor=actor, organisation=payload["organisation"])


def _update(*, actor: str, bid_reference: str, email: str, phone: str, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	authz.active_account(ctx.workspace.lead_organisation)  # a suspended Account cannot edit its Draft (BDS01-AC-010)
	save.require_open(ctx)
	arrangement = ctx.arrangement
	records.check_version(arrangement, expected_record_version)
	from kentender_procurement.bid_submission.services import addendum

	refreshed = addendum.refresh(ctx, actor=actor, at=at)
	if refreshed:
		return refreshed
	problems = {}
	if not email or not validate_email_address(email, throw=False):
		problems["email"] = "Enter the Tender contact's email address."
	if not PHONE.match(phone):
		problems["phone"] = "Enter the Tender contact's telephone number, for example +254 709 555 015."
	if problems:
		return field_errors(problems)
	with records.atomic("update-tender-contact"):
		records.bump(arrangement, tender_contact_email=email, tender_contact_phone=phone)
		ctx.arrangement = arrangement
		status = save.refresh_derived(ctx)
		if ctx.workspace.status != status:
			records.save(ctx.workspace.update({"status": status, "status_since": at}))
		records.emit("TenderContactChanged", tender=arrangement.tender, arrangement=arrangement.name, workspace=ctx.workspace.name, organisation=arrangement.lead_organisation, actor=actor, at=at)
	return {"ok": True, "record_version": int(arrangement.record_version), "status": status}
