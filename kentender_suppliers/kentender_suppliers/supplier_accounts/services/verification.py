# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`SendAccountVerification` / `VerifyAccountCommunication` (BDS-CHG-001 v0.8
§4.1, §5.1–5.2, §7.2, §11.3; BDS03-IMP-009).

The configured channel is email: a single-use link (random token; only its
SHA-256 is stored) valid for 24 hours; a new link supersedes the previous
one; at most three links per organisation per rolling hour, and a limited
request answers the same way whether or not a link went out. Verifying
proves control of that address only — it activates a Pending verification
Account and marks the contact Verified; it never approves, qualifies or
verifies the organisation's legal facts, and never reactivates a Suspended
Account."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, get_url

from kentender_suppliers.supplier_accounts.services import audit, clock, messages, records
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services.errors import fail

DOCTYPE = "Supplier Account Verification"
ORGANISATION = "Supplier Organisation"
TTL = timedelta(hours=24)
LIMIT_PER_HOUR = 3
SUBJECT = "Verify your KenTender supplier account email"
LIMITED_TEXT = "A verification link was sent recently. Check your inbox, or try again later."
INVALID_TEXT = "This verification link is not valid. Send a new link from your Account."
EXPIRED_TEXT = "This verification link has expired. Send a new link from your Account."
SUPERSEDED_TEXT = "A newer verification link was sent. Use the most recent link."


def token_hash(token: str) -> str:
	return hashlib.sha256(cstr(token).encode("utf-8")).hexdigest()


def link_for(token: str) -> str:
	return f"{get_url()}/account/verify?token={token}"


def _body(legal_name: str, link: str) -> str:
	return (
		f"<p>Verify this email address for the KenTender supplier account of {frappe.utils.escape_html(legal_name)}.</p>"
		f'<p><a href="{link}">Verify email</a></p>'
		"<p>The link works once and expires in 24 hours. Verifying proves you control this address. "
		"It does not approve or qualify the organisation for any Tender.</p>"
	)


def issue(org, *, email: str, actor: str) -> dict[str, Any]:
	"""Send one challenge to `email` for `org` unless the hourly limit is reached."""
	now = clock.now()
	recent = frappe.db.count(DOCTYPE, {"organisation": org.name, "sent_at": (">", now - timedelta(hours=1))})
	if recent >= LIMIT_PER_HOUR:
		return {"sent": False, "limited": True}
	for name in frappe.get_all(DOCTYPE, filters={"organisation": org.name, "contact_value": email, "status": "Sent"}, pluck="name"):
		records.save(frappe.get_doc(DOCTYPE, name).update({"status": "Superseded"}))
	token = secrets.token_urlsafe(32)
	row = records.insert(frappe.get_doc({
		"doctype": DOCTYPE, "organisation": org.name, "channel": "Email", "contact_value": email, "token_hash": token_hash(token),
		"status": "Sent", "sent_at": now, "expires_at": now + TTL, "sent_by": actor, "fixture_namespace": org.fixture_namespace,
	}))
	link = link_for(token)
	try:
		result = messages.send({"kind": "account_verification", "to": email, "subject": SUBJECT, "body": _body(org.legal_name, link), "link": link, "organisation": org.name})
	except Exception:
		frappe.logger("kentender.supplier_accounts").error("verification message transport failed", exc_info=True)
		result = {"result": "Failed"}
	return {"sent": True, "limited": False, "challenge": row.name, "transport": cstr((result or {}).get("result"))}


def unverified_official_email(org) -> str:
	for row in org.contacts:
		if row.channel == "Email" and row.is_official and row.verification_status != "Verified":
			return cstr(row.value)
	return ""


def send_account_verification(*, organisation: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	authz.require_member(organisation, principal)
	org = frappe.get_doc(ORGANISATION, organisation)
	if org.account_status == "Suspended":
		fail("BDS_ACCOUNT_SUSPENDED")

	def _do() -> dict[str, Any]:
		email = unverified_official_email(org)
		if not email:
			return {"ok": True, "organisation": organisation, "sent": False, "already_verified": True}
		sent = issue(org, email=email, actor=principal)
		if sent["sent"]:
			audit.record(doctype=ORGANISATION, name=organisation, action="send_account_verification", actor=principal, metadata={"channel": "Email", "challenge": sent["challenge"]})
		return {"ok": True, "organisation": organisation, "sent": sent["sent"], "limited": sent["limited"], "sent_to": email, "message": LIMITED_TEXT if sent["limited"] else ""}

	return records.idempotent(idempotency_key, "SendAccountVerification", {"organisation": organisation}, _do, actor=principal, organisation=organisation)


def verify_account_communication(*, token: str, user: str | None = None) -> dict[str, Any]:
	"""The link is its own idempotency: a used link answers "already verified"."""
	principal = authz.require_signed_in(user)
	row = frappe.db.get_value(DOCTYPE, {"token_hash": token_hash(token)}, ["name", "organisation", "contact_value", "status", "expires_at"], as_dict=True) if cstr(token).strip() else None
	if not row or not authz.assignments_of(principal, organisation=row.organisation):
		return {"ok": False, "reason": "invalid", "message": INVALID_TEXT}
	if row.status == "Verified":
		return {"ok": True, "already_verified": True, "organisation": row.organisation, "account_status": frappe.db.get_value(ORGANISATION, row.organisation, "account_status")}
	if row.status == "Superseded":
		return {"ok": False, "reason": "superseded", "message": SUPERSEDED_TEXT}
	now = clock.now()
	challenge = frappe.get_doc(DOCTYPE, row.name)
	if row.status == "Expired" or now >= get_datetime(row.expires_at):
		if challenge.status != "Expired":
			records.save(challenge.update({"status": "Expired"}))
		return {"ok": False, "reason": "expired", "message": EXPIRED_TEXT}
	org = frappe.get_doc(ORGANISATION, row.organisation)
	if org.account_status == "Suspended":
		fail("BDS_ACCOUNT_SUSPENDED")
	records.save(challenge.update({"status": "Verified", "verified_at": now, "verified_by": principal}))
	for contact in org.contacts:
		if contact.channel == "Email" and cstr(contact.value).lower() == cstr(row.contact_value).lower():
			contact.verification_status, contact.verified_at, contact.verified_by = "Verified", now, principal
	values: dict[str, Any] = {}
	if org.account_status == "Pending verification":
		values = {"account_status": "Active", "status_since": now}
	records.bump(org, **values)
	audit.record(doctype=ORGANISATION, name=org.name, action="verify_account_communication", actor=principal, metadata={"channel": "Email", "challenge": row.name, "account_status": org.account_status})
	return {"ok": True, "organisation": org.name, "account_status": org.account_status, "record_version": int(org.record_version)}
