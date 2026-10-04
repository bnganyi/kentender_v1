# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Submission side of the Award contract (AWD-CHG-001 v0.4 §3,
§5.4–§5.5, AWD-IF-03; Award plan D5).

Award notifies every person who submitted a tender, from the sealed
submission and withdrawal history — never the candidate registry or
Evaluation's responsive-only list — and addresses each through the tender's
mandatory notice contact. Who may accept or decline an award is the
organisation's active Authorised Signatory at the trusted instant; a
Supplier Representative may read and ask for an explanation only. Account
roles alone confer nothing (§3)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import opening_gateway, supplier_gateway

ARRANGEMENT = "Bidder Arrangement"


def audience(tender: str) -> list[dict[str, Any]]:
	"""One row per bidder arrangement that sealed a submission: its final
	submission's status (Submitted / Withdrawn), the replaced versions it
	superseded, its organisation and its current notice contact."""
	manifest = opening_gateway.closed_manifest(tender)
	if not manifest:
		return []
	final: dict[str, dict[str, Any]] = {}
	for env in manifest["payload"].get("envelopes") or []:
		key = cstr(env.get("bidder_arrangement"))
		if not key:
			continue
		current = final.get(key)
		if current is None or int(env.get("version_number") or 0) >= int(current.get("version_number") or 0):
			if current is not None:
				env = {**env, "replaced": (current.get("replaced") or []) + [current.get("submission_version")]}
			final[key] = env
	out = []
	for key, env in sorted(final.items()):
		arrangement = frappe.db.get_value(ARRANGEMENT, key, ["lead_organisation", "lead_legal_name", "mandatory_notice_email", "notice_contact_version"], as_dict=True) or {}
		status = "Withdrawn" if cstr(env.get("status")) == "Withdrawn" else "Submitted"
		out.append({"bidder_arrangement": key, "organisation": cstr(arrangement.get("lead_organisation")), "organisation_name": cstr(arrangement.get("lead_legal_name")),
			"bid_reference": cstr(env.get("bid_reference")), "submission_version": cstr(env.get("submission_version")), "status": status,
			"replaced": env.get("replaced") or [], "contact_email": cstr(arrangement.get("mandatory_notice_email")),
			"contact_version": int(arrangement.get("notice_contact_version") or 0)})
	return out


def notice_contact(bidder_arrangement: str) -> dict[str, Any]:
	"""The current authoritative notice contact (owned by Bid Submission)."""
	row = frappe.db.get_value(ARRANGEMENT, bidder_arrangement, ["mandatory_notice_email", "notice_contact_version"], as_dict=True) or {}
	return {"email": cstr(row.get("mandatory_notice_email")), "version": int(row.get("notice_contact_version") or 0)}


def signatory(user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
	"""The person's active Authorised Signatory assignment in `organisation`."""
	try:
		rows = supplier_gateway.active_assignments(user=user, at=at)
	except Exception:
		return None
	return next((a for a in rows if a.get("active") and a.get("organisation_id") == organisation and a.get("responsibility") == authz.SIGNATORY), None)


def acting_for(user: str, organisation: str, *, at=None) -> dict[str, Any] | None:
	"""Any active preparing assignment (representative or signatory)."""
	try:
		rows = supplier_gateway.active_assignments(user=user, at=at)
	except Exception:
		return None
	mine = [a for a in rows if a.get("active") and a.get("organisation_id") == organisation and a.get("responsibility") in authz.PREPARERS]
	return sorted(mine, key=lambda a: a["responsibility"] != authz.SIGNATORY)[0] if mine else None


def organisations_of(user: str, *, at=None) -> list[str]:
	try:
		rows = supplier_gateway.active_assignments(user=user, at=at)
	except Exception:
		return []
	return sorted({a["organisation_id"] for a in rows if a.get("active") and a.get("responsibility") in authz.PREPARERS})


def organisation_users(organisation: str, *, at=None) -> list[dict[str, Any]]:
	try:
		return [p for p in supplier_gateway.organisation_people(organisation_id=organisation, at=at) if p.get("active")]
	except Exception:
		return []


def organisation_name(organisation: str) -> str:
	try:
		row = supplier_gateway.organisation(organisation_id=organisation) or {}
	except Exception:
		row = {}
	return cstr(row.get("legal_name"))
