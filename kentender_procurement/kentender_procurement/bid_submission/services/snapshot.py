# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The bid's organisation snapshot (BDS-CHG-001 v0.8 §4.4.8, §4.5): the exact
Account-owned facts a Draft uses, copied at Start bid and changed only by the
explicit refresh command. Later Account changes never reach a Draft or a
submitted Version on their own. For a joint venture it also holds each
member's facts from that member's own Account (template release 1.2
`SV-ARRANGEMENT-MEMBER`)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from kentender_procurement.bid_submission.services import records, supplier_gateway

SNAPSHOT = "Bid Organisation Snapshot"
ORGANISATION_FACTS = ("organisation_id", "legal_name", "country", "registration_number", "tax_identifier", "registered_address", "year_of_registration")
MEMBER_FACTS = ("organisation_id", "legal_name", "country", "registration_number", "registered_address", "year_of_registration")
#: The standing business facts of an entity's Account profile (release 1.4, `SV-ENTITY-PROFILE`).
PROFILE_FACTS = (
	"business_structure", "sole_proprietor_name", "sole_proprietor_age", "sole_proprietor_nationality", "sole_proprietor_country_of_origin", "sole_proprietor_citizenship",
	"partners", "company_type", "nominal_capital", "issued_capital", "directors", "trade_licence_number", "trade_licence_expiry", "maximum_business_value", "state_owned",
)
LIST_FACTS = ("partners", "directors")
PROFILE_LABELS = {
	"business_structure": "Business structure", "sole_proprietor_name": "Sole proprietor: name in full", "sole_proprietor_age": "Sole proprietor: age",
	"sole_proprietor_nationality": "Sole proprietor: nationality", "sole_proprietor_country_of_origin": "Sole proprietor: country of origin",
	"sole_proprietor_citizenship": "Sole proprietor: citizenship", "partners": "Partners", "company_type": "Company type", "nominal_capital": "Nominal capital",
	"issued_capital": "Issued capital", "directors": "Directors", "trade_licence_number": "Trade licence number", "trade_licence_expiry": "Trade licence expiry",
	"maximum_business_value": "Maximum value of business handled", "state_owned": "State-owned",
}


def _pick(row: dict[str, Any] | None, keys: tuple[str, ...]) -> dict[str, Any]:
	return {k: (row or {}).get(k) or "" for k in keys}


def _identity(organisation_id: str, keys: tuple[str, ...]) -> dict[str, Any]:
	"""An organisation's identity facts, with its year of registration, which the Account keeps in the business profile."""
	picked = _pick(supplier_gateway.organisation(organisation_id=organisation_id), keys)
	if "year_of_registration" in keys:
		picked["year_of_registration"] = (supplier_gateway.business_profile(organisation_id=organisation_id) or {}).get("year_of_registration") or ""
	return picked


def _profile(organisation_id: str) -> dict[str, Any]:
	"""One entity's profile facts as its Account holds them now (blank where nothing is saved)."""
	row = supplier_gateway.business_profile(organisation_id=organisation_id) or {}
	return {k: (list(row.get(k) or []) if k in LIST_FACTS else (row.get(k) or "")) for k in PROFILE_FACTS}


def facts(lead: str, members: list[str]) -> dict[str, Any]:
	organisation = supplier_gateway.organisation(organisation_id=lead)
	entities = list(members) or [lead]  # a joint venture's lead is its first member
	return {
		"organisation": _identity(lead, ORGANISATION_FACTS),
		"members": [_identity(m, MEMBER_FACTS) for m in members],
		"profiles": {entity: _profile(entity) for entity in entities},
		"account_record_version": int((organisation or {}).get("record_version") or 0),
	}


def digest(value: dict[str, Any]) -> str:
	return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def take(*, arrangement, workspace: str, version: int, actor: str, at) -> Any:
	value = facts(arrangement.lead_organisation, [m.organisation_id for m in arrangement.members])
	return records.insert(frappe.get_doc({
		"doctype": SNAPSHOT, "bidder_arrangement": arrangement.name, "bid_workspace": workspace, "organisation_id": arrangement.lead_organisation,
		"snapshot_version": version, "account_record_version": value["account_record_version"], "facts_json": json.dumps(value, sort_keys=True),
		"facts_digest": digest(value), "taken_at": at, "taken_by": actor,
	}))


def compare(workspace) -> dict[str, Any]:
	"""The Draft's snapshot against the Account now: which facts differ."""
	current = json.loads(frappe.db.get_value(SNAPSHOT, workspace.organisation_snapshot, "facts_json") or "{}")
	arrangement = frappe.get_doc("Bidder Arrangement", workspace.bidder_arrangement)
	latest = facts(arrangement.lead_organisation, [m.organisation_id for m in arrangement.members])
	changed = [k for k in ORGANISATION_FACTS if current.get("organisation", {}).get(k) != latest["organisation"].get(k)]
	members_before = current.get("members") or []
	for index, member in enumerate(latest["members"]):
		before = members_before[index] if index < len(members_before) else {}
		changed += [f"members.{index}.{k}" for k in MEMBER_FACTS if before.get(k) != member.get(k)]
	profiles_before = current.get("profiles") or {}
	for entity, profile in latest["profiles"].items():
		before = profiles_before.get(entity) or {}
		changed += [f"profiles.{entity}.{k}" for k in PROFILE_FACTS if before.get(k, [] if k in LIST_FACTS else "") != profile.get(k)]
	return {"changed": changed, "current": current, "latest": latest}


def refresh_bid_organisation_snapshot(*, bid_reference: str, confirm: bool, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	"""`RefreshBidOrganisationSnapshot` (§7.2): compare, and only after an
	explicit confirmation freeze a new Draft-only snapshot. Never touches the
	Account, bid-specific answers or a submitted Version."""
	from frappe.utils import cstr

	from kentender_procurement.bid_submission.services import bid_authorization as authz
	from kentender_procurement.bid_submission.services import clock
	from kentender_procurement.bid_submission.services.errors import fail

	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "confirm": bool(confirm), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}

	def run() -> dict[str, Any]:
		at = clock.now()
		lead = authz.acting_assignment(actor, payload["organisation"], at=at)["organisation_id"]
		authz.active_account(lead)
		if not frappe.db.exists("Bid Workspace", {"name": payload["bid_reference"], "lead_organisation": lead}):
			fail("BDS_TENDER_NOT_FOUND")
		workspace = frappe.get_doc("Bid Workspace", payload["bid_reference"])
		if workspace.status in ("Submitted", "Withdrawn", "Closed without submission"):
			fail("BDS_ALREADY_SUBMITTED" if workspace.status == "Submitted" else "BDS_TENDER_NOT_OPEN")
		records.check_version(workspace, expected_record_version)
		diff = compare(workspace)
		if not diff["changed"] or not payload["confirm"]:
			return {"ok": True, "refreshed": False, "changed": diff["changed"], "snapshot_version": int(workspace.organisation_snapshot_version)}
		arrangement = frappe.get_doc("Bidder Arrangement", workspace.bidder_arrangement)
		version = int(workspace.organisation_snapshot_version or 0) + 1
		with records.atomic("refresh-snapshot"):
			taken = take(arrangement=arrangement, workspace=workspace.name, version=version, actor=actor, at=at)
			records.bump(workspace, organisation_snapshot=taken.name, organisation_snapshot_version=version)
			records.emit("OrganisationSnapshotRefreshed", tender=workspace.tender, arrangement=arrangement.name, workspace=workspace.name, organisation=lead, actor=actor, at=at, payload={"snapshot_version": version, "changed": diff["changed"]})
		return {"ok": True, "refreshed": True, "changed": diff["changed"], "snapshot_version": version, "record_version": int(workspace.record_version)}

	return records.idempotent(idempotency_key, "RefreshBidOrganisationSnapshot", payload, run, actor=actor, organisation=payload["organisation"])
