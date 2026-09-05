# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.1 — accepted-Need intake from Departmental Needs.

Planning consumes Needs only through the published contract (decision D5):
`DepartmentalNeedAccepted.v2` and its replay reads in
`departmental_needs.services.events`. The projection here is idempotent and
runs only inside commands (invariant 1: reads create nothing): every current
accepted Need in the exact PE/FY/OU appears exactly once as a read-only
Need-origin entry in the Draft DPP Version, carrying the six Need facts;
Planning adds only Budget Line and indicative amount, which survive a fact
refresh from a successor accepted version.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt

CONSUMER = "procurement_planning"

NEED_ORIGIN = "Accepted Departmental Need"
DIRECT_ORIGIN = "Direct departmental requirement"


def current_accepted_sources(
	financial_year: str, organisation_unit: str = ""
) -> list[dict[str, Any]]:
	from kentender_procurement.departmental_needs.services.events import (
		current_accepted_events,
	)

	# `current_accepted_events` already returns the decoded §7.1 payload dicts
	# themselves (`accepted_payload`'s own field set — `need_id`,
	# `accepted_version_id`, etc.), not a `{"payload": ...}` envelope around
	# them; every caller of this function before this phase mocked it away,
	# so the mismatch was never actually exercised. The site Procuring
	# Entity is implicit (AUTH-ADR-001 v1.6 §1.1) — there is no PE parameter.
	return current_accepted_events(
		financial_year=financial_year,
		organisation_unit=organisation_unit,
	)


def need_version_number(need_version: str) -> int:
	"""The version ordinal encoded in a Need Version's own deterministic id
	(`{need_reference}-V{number:03d}`, set once at creation by
	`departmental_needs.services.lifecycle._create_version` and never
	renamed). Planning already legitimately holds this exact string — it is
	the published event's own `accepted_version_id` (§7.1), pinned onto the
	allocation/entry it sourced — so deriving a display number from it reads
	no Needs table and needs no new contract surface; a fresh
	`get_current_accepted_need` read would also be *wrong* here, since it
	answers for the Need's current accepted version, not the pinned
	(possibly since-superseded) one this reference line names."""
	tail = cstr(need_version).rsplit("-V", 1)
	if len(tail) != 2 or not tail[1].isdigit():
		return 0
	return int(tail[1])


def current_accepted_version_of(need: str, financial_year: str) -> str:
	"""The Need's current accepted version through the published §8.1 contract,
	or "" when it has none / is out of scope. Never reads Needs tables (D5)."""
	from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
	from kentender_procurement.departmental_needs.services.workspace import (
		get_current_accepted_need,
	)

	try:
		# System principal, deliberately: this is Planning's server-side source
		# consistency check, not a user read. NDS's viewer model (owner-author /
		# HoD / Planner with an explicit OU-scoped or Site-wide responsibility
		# assignment, AUTH-ADR-001 v1.6) governs people opening Needs; Planning
		# actors hold no Financial Year assignment at all (Fiscal Year is never
		# a per-user grant) and a departmental colleague may legitimately
		# enrich a Need they did not author. The acting user was already
		# authorised for the DPP scope by the calling command.
		payload = get_current_accepted_need(
			need=need,
			expected_financial_year=financial_year,
			user="Administrator",
		)
	except DepartmentalNeedError:
		return ""
	return cstr(payload.get("accepted_version"))


def _facts(payload: dict[str, Any]) -> dict[str, Any]:
	return {
		"title": cstr(payload.get("title")),
		"description": cstr(payload.get("description")),
		"expected_operational_result": cstr(payload.get("expected_operational_result")),
		"quantity": flt(payload.get("indicative_quantity")),
		"unit": cstr(payload.get("unit_id")),
		"required_by_date": payload.get("required_by_date"),
	}


def refresh_draft_entries(version_doc) -> dict[str, Any]:
	"""Project every current accepted Need into a mutable Draft Version once.

	- a new accepted Need gains a new Need-origin entry (funding empty);
	- a successor accepted version refreshes the six facts and the pinned
	  need_version, keeping the Planning-owned funding specification;
	- a withdrawn Need's unsubmitted entry is removed.
	Direct entries are never touched. Idempotent by construction."""
	if version_doc.version_status not in ("Draft",):
		return {"ok": False, "reason": "NOT_DRAFT"}
	root = frappe.db.get_value(
		"Departmental Plan",
		version_doc.departmental_plan,
		["organisation_unit", "fiscal_year", "dpp_reference", "fixture_namespace"],
		as_dict=True,
	)
	sources = current_accepted_sources(root.fiscal_year, root.organisation_unit)
	by_need = {cstr(payload["need_id"]): payload for payload in sources}
	existing = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": version_doc.name, "source_origin": NEED_ORIGIN},
		fields=["name", "need", "need_version", "entry_id"],
		limit_page_length=0,
	)
	added, refreshed, removed = [], [], []
	for row in existing:
		payload = by_need.pop(cstr(row.need), None)
		if payload is None:
			frappe.delete_doc(
				"Departmental Plan Entry", row.name,
				force=True, ignore_permissions=True, delete_permanently=True,
			)
			removed.append(row.entry_id)
			continue
		if cstr(row.need_version) != cstr(payload["accepted_version_id"]):
			entry = frappe.get_doc("Departmental Plan Entry", row.name)
			entry.update(_facts(payload))
			entry.need_version = payload["accepted_version_id"]
			entry.save(ignore_permissions=True)
			refreshed.append(row.entry_id)
	for payload in by_need.values():
		from kentender_procurement.procurement_planning.services import references

		entry = frappe.get_doc(
			{
				"doctype": "Departmental Plan Entry",
				"entry_id": references.entry_id(root.dpp_reference),
				"dpp_version": version_doc.name,
				"source_origin": NEED_ORIGIN,
				"need": payload["need_id"],
				"need_version": payload["accepted_version_id"],
				"fixture_namespace": version_doc.fixture_namespace or root.fixture_namespace,
				**_facts(payload),
			}
		)
		entry.insert(ignore_permissions=True)
		added.append(entry.entry_id)
	return {"ok": True, "added": added, "refreshed": refreshed, "removed": removed}


def coverage_gaps(version_doc) -> list[str]:
	"""Need references whose current accepted version is not represented
	exactly once on this Version — the §5.1 submission blocker."""
	root = frappe.db.get_value(
		"Departmental Plan",
		version_doc.departmental_plan,
		["organisation_unit", "fiscal_year"],
		as_dict=True,
	)
	sources = current_accepted_sources(root.fiscal_year, root.organisation_unit)
	rows = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": version_doc.name, "source_origin": NEED_ORIGIN},
		fields=["need", "need_version"],
		limit_page_length=0,
	)
	pinned = {cstr(row.need): cstr(row.need_version) for row in rows}
	gaps = []
	for payload in sources:
		need = cstr(payload["need_id"])
		if pinned.get(need) != cstr(payload["accepted_version_id"]):
			gaps.append(cstr(payload.get("need_reference") or need))
	return gaps
