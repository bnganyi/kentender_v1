# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`GetSupplierAccount` (BDS-CHG-001 v0.8 §7.1, §10.5 BDS-DES-04, §11.3).

The signed-in person's Account: the exact organisation facts, the people
and their immutable assignments, reusable evidence, verified Tender notice
contacts, what is missing, the actions this person may take and the
Account next step and journey. A person assigned to several organisations
names one per request (never a session default); with none named, they
choose first. Another organisation's Account is Not found. Reads create
nothing. Nothing here says approved, qualified or verified supplier."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_core.services import public_portal
from kentender_suppliers.supplier_accounts.services import authorization as authz
from kentender_suppliers.supplier_accounts.services import clock, facts, guidance
from kentender_suppliers.supplier_accounts.services.errors import not_found
from kentender_suppliers.supplier_accounts.services.labels import date_label

ORGANISATION = "Supplier Organisation"
EVIDENCE = "Supplier Account Evidence"
EVIDENCE_LABELS = {"Reservation evidence": "Reservation evidence", "Signatory authority": "Signatory authority"}


def _period(row: dict[str, Any]) -> str:
	start, end = date_label(row["effective_from"]), date_label(row["effective_to"]) if row.get("effective_to") else ""
	return f"From {start} to {end}" if end else f"From {start}"


def _people(organisation: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(authz.ASSIGNMENT, filters={"organisation": organisation}, fields=["name", "user", "responsibility", "job_title", "effective_from", "effective_to", "authority_evidence"], order_by="assigned_at asc, creation asc", limit_page_length=0)
	out = []
	for row in rows:
		if row.effective_to and not authz.is_active(row) and getdate(row.effective_to) < getdate(clock.now()):
			continue  # ended assignments are history, not current people
		out.append({"assignment": row.name, "person": guidance.full_name(row.user), "responsibility": row.responsibility, "job_title": cstr(row.job_title), "effective_period": _period(row), "active": authz.is_active(row)})
	return out


def _evidence(organisation: str) -> list[dict[str, Any]]:
	today = getdate(clock.now())
	rows = frappe.get_all(EVIDENCE, filters={"organisation": organisation}, fields=["name", "evidence_type", "title", "reference", "valid_until", "status", "file_name"], order_by="uploaded_at asc, creation asc", limit_page_length=0)
	out = []
	for row in rows:
		status = "Expired" if row.status == "Available" and row.valid_until and getdate(row.valid_until) < today else row.status
		out.append({"evidence": row.name, "label": cstr(row.title) or row.evidence_type, "evidence_type": row.evidence_type, "reference": cstr(row.reference), "valid_until": date_label(row.valid_until) if row.valid_until else "—", "status": status, "file_name": cstr(row.file_name)})
	return out


def _notice_contacts(org) -> list[dict[str, str]]:
	"""Verified emails a bid may choose for notices, and the official email
	while it waits for verification (listed as pending, never usable)."""
	return [
		{"email": cstr(r.value), "status": "Verified" if r.verification_status == "Verified" else "Pending verification"}
		for r in org.contacts
		if r.channel == "Email" and (r.verification_status == "Verified" or r.is_official)
	]


def _status(org, missing: list) -> dict[str, str] | None:
	"""The head badge (§10.5): an incomplete Account shows none — it is
	never called unverified — and suspension is always stated."""
	if org.account_status == "Suspended":
		return {"label": "Account suspended", "tone": "critical"}
	if missing:
		return None
	if org.account_status == "Pending verification":
		return {"label": "Pending verification", "tone": "attention"}
	return {"label": "Active", "tone": "live"} if org.account_status == "Active" else None


def _allowed_actions(org, responsibility: str) -> list[str]:
	if org.account_status == "Suspended":
		return ["view_receipts"]
	actions = ["edit_organisation", "add_evidence"]
	if org.account_status == "Pending verification":
		actions.append("send_account_verification")
	if responsibility == authz.SIGNATORY:
		actions.append("add_person")
	return actions


def _links(org) -> list[dict[str, str]]:
	"""A suspended Account keeps its receipts and one way to reach support
	(§10.5 BDS-DES-04-SUSPENDED); it never offers a way to reactivate itself."""
	if org.account_status != "Suspended":
		return []
	links = [{"key": "view_receipts", "label": "View receipts", "href": "/account/receipts"}]
	email = cstr((public_portal.get_public_portal_information().get("support") or {}).get("email"))
	if email:
		links.append({"key": "supplier_support", "label": "Supplier support", "href": f"mailto:{email}"})
	return links


def get_supplier_account(*, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	principal = authz.require_signed_in(user)
	mine = [] if authz.is_internal_user(principal) else authz.organisations_of(principal)
	if organisation:
		if organisation not in mine:
			not_found()
		chosen = organisation
	elif len(mine) == 1:
		chosen = mine[0]
	elif not mine:
		return {"state": "no_account", "organisations": [], **guidance.for_new_account(principal)}
	else:
		return {"state": "choose_organisation", "organisations": [{"organisation": o, "legal_name": cstr(frappe.db.get_value(ORGANISATION, o, "legal_name"))} for o in mine]}
	org = frappe.get_doc(ORGANISATION, chosen)
	responsibility = authz.responsibility_of(chosen, principal)
	missing = facts.missing_items(org)
	return {
		"state": "account",
		"organisations": [{"organisation": o, "legal_name": cstr(frappe.db.get_value(ORGANISATION, o, "legal_name"))} for o in mine],
		"organisation": {
			"organisation": org.name, "legal_name": org.legal_name, "country": org.country, "registration_number": org.registration_number,
			"tax_identifier": cstr(org.tax_identifier), "registered_address": org.registered_address, "official_email": org.official_email,
			"official_phone": cstr(org.official_phone), "account_status": org.account_status, "record_version": int(org.record_version or 0),
		},
		"viewer": {"responsibility": responsibility},
		"people": _people(org.name),
		"evidence": _evidence(org.name),
		"notice_contacts": _notice_contacts(org),
		"missing": missing,
		"status": _status(org, missing),
		"allowed_actions": _allowed_actions(org, responsibility),
		"links": _links(org),
		**guidance.for_account(org, viewer=principal),
	}
