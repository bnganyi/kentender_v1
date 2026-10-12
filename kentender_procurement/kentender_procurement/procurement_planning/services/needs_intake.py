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
refresh from a successor accepted revision.
"""

from __future__ import annotations

from typing import Any

import frappe
from decimal import Decimal, InvalidOperation

from frappe.utils import cstr, flt
from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.write_family import planning_command

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


def need_revision_number(need_revision: str) -> int:
	"""The revision ordinal encoded in a Need Revision's own deterministic id
	(`{need_reference}-V{number:03d}` — the `-V` suffix is an opaque
	identifier kept through the NDS-CHG-001 v1.10 §4.3 rename, set once at
	creation and never renamed). Planning already legitimately holds this
	exact string — it is the published event's own `accepted_version_id`
	(§7.1 frozen wire key), pinned onto the allocation/entry it sourced — so
	deriving a display number from it reads no Needs table and needs no new
	contract surface; a fresh `get_current_accepted_need` read would also be
	*wrong* here, since it answers for the Need's current accepted revision,
	not the pinned (possibly since-superseded) one this reference line names."""
	tail = cstr(need_revision).rsplit("-V", 1)
	if len(tail) != 2 or not tail[1].isdigit():
		return 0
	return int(tail[1])


def current_accepted_revision_of(need: str, financial_year: str) -> str:
	"""The Need's current accepted revision through the published §8.1 contract,
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
	return cstr(payload.get("accepted_revision"))


def need_acceptance_evidence(need: str, need_revision: str) -> dict[str, Any] | None:
	"""Who accepted this exact pinned revision for planning, and when
	(§10.11's "Need accepted by" evidence) — through the published contract,
	never a direct `Departmental Need Decision` read (D5)."""
	from kentender_procurement.departmental_needs.services.workspace import (
		get_need_acceptance_evidence,
	)

	# System principal — the same server-side consistency-check pattern as
	# `current_accepted_revision_of` above, not a user-facing Needs read.
	return get_need_acceptance_evidence(need=need, need_revision=need_revision, user="Administrator")


def _quantity(payload: dict[str, Any]) -> float:
	"""`indicative_quantity` arrives as an exact decimal string
	(DepartmentalNeedAccepted.v2, NDS v1.16 §4.9). It is parsed exactly and only
	then narrowed to the entry's Float column; text that is not a decimal is a
	broken source, never a silent zero. A JSON number from an older replay is
	accepted by the same parse."""
	raw = payload.get("indicative_quantity")
	if raw in (None, ""):
		return 0.0
	try:
		quantity = Decimal(cstr(raw).strip())
	except InvalidOperation:
		fail("PLN_REFERENCE_UNAVAILABLE", "The accepted Need's quantity is not an exact decimal.", {"need": cstr(payload.get("need_id"))})
	if not quantity.is_finite():
		fail("PLN_REFERENCE_UNAVAILABLE", "The accepted Need's quantity is not an exact decimal.", {"need": cstr(payload.get("need_id"))})
	return float(quantity)


def _estimate(payload: dict[str, Any]) -> float:
	"""`estimated_total_cost` arrives on `DepartmentalNeedAccepted.v3` as an
	exact decimal string, or null for a revision without one (NDS-CHG-001 v1.17
	§7.1A) — and is absent from a `.v2` replay. Absence is zero here: the entry's
	Currency column has no null, and zero reads as "no estimate" everywhere. Text
	that is not a decimal is a broken source, never a silent zero."""
	raw = payload.get("estimated_total_cost")
	if raw in (None, ""):
		return 0.0
	try:
		amount = Decimal(cstr(raw).strip())
	except InvalidOperation:
		fail("PLN_REFERENCE_UNAVAILABLE", "The accepted Need's estimated cost is not an exact decimal.", {"need": cstr(payload.get("need_id"))})
	if not amount.is_finite() or amount < 0:
		fail("PLN_REFERENCE_UNAVAILABLE", "The accepted Need's estimated cost is not an exact decimal.", {"need": cstr(payload.get("need_id"))})
	return float(amount)


def _facts(payload: dict[str, Any]) -> dict[str, Any]:
	return {
		"title": cstr(payload.get("title")),
		"description": cstr(payload.get("description")),
		"expected_operational_result": cstr(payload.get("expected_operational_result")),
		"quantity": _quantity(payload),
		"unit": cstr(payload.get("unit_id")),
		"required_by_date": payload.get("required_by_date"),
		# PLN-CHG-001 v1.30 §4.3 — read-only reference to the accepted Need's estimate
		"need_estimated_total_cost": _estimate(payload),
	}


def prefill_amount(entry) -> bool:
	"""PLN-CHG-001 v1.30 §4.3 rules 1 and 6 — a Need-origin entry with no
	operative amount, that is not excluded, starts from the accepted Need's
	estimate. Never replaces an entered amount; never sets a Budget Line.
	Returns whether it set one."""
	if cstr(entry.not_proceeding_reason).strip() or flt(entry.indicative_amount) > 0:
		return False
	estimate = flt(entry.need_estimated_total_cost)
	if estimate <= 0:
		return False
	entry.indicative_amount = estimate
	return True


def submission_cohort(submission_name: str) -> set[str]:
	"""§5.1.2 — the stable source keys certified by a Submission."""
	import json

	snapshots = json.loads(frappe.db.get_value("Departmental Plan Submission", submission_name, "entry_snapshots") or "[]")
	return {cstr(row.get("source_line_id")) for row in snapshots if cstr(row.get("source_line_id"))}


def _cohort_filter(version_doc, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""A correction Draft (copied from a returned Submission) consumes only the
	current accepted revisions of the Needs in that Submission's cohort; a Need
	accepted later is pending input to a subsequent update (§5.1.2)."""
	returned_from = cstr(version_doc.get("returned_from_submission"))
	if not returned_from:
		return sources
	cohort = submission_cohort(returned_from)
	return [payload for payload in sources if cstr(payload["need_id"]) in cohort]


@planning_command
def refresh_draft_entries(version_doc) -> dict[str, Any]:
	"""Project every current accepted Need into a mutable Draft Version once.

	- a new accepted Need gains a new Need-origin entry (Budget Line empty; the
	  amount starts from the Need's estimate when it has one, v1.30 §4.3);
	- a successor accepted revision refreshes the six facts and the pinned
	  need_revision, keeping the Planning-owned funding specification (an
	  entered amount is never replaced; an empty one starts from the estimate);
	- a withdrawn Need's unsubmitted entry is removed.
	Direct entries are never touched. Idempotent by construction.
	Wire keys (`accepted_version_id`, `version_number`) are frozen per
	NDS-CHG-001 v1.10 §7.1 — consumers read the keys, not the word."""
	if version_doc.version_status not in ("Draft",):
		return {"ok": False, "reason": "NOT_DRAFT"}
	root = frappe.db.get_value(
		"Departmental Plan",
		version_doc.departmental_plan,
		["organisation_unit", "fiscal_year", "dpp_reference", "fixture_namespace"],
		as_dict=True,
	)
	sources = _cohort_filter(version_doc, current_accepted_sources(root.fiscal_year, root.organisation_unit))
	by_need = {cstr(payload["need_id"]): payload for payload in sources}
	existing = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": version_doc.name, "source_origin": NEED_ORIGIN},
		fields=["name", "need", "need_revision", "entry_id"],
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
		# `accepted_version_id` is a frozen wire key (NDS-CHG-001 v1.10 §7.1); it carries the accepted revision.
		if cstr(row.need_revision) != cstr(payload["accepted_version_id"]):
			entry = frappe.get_doc("Departmental Plan Entry", row.name)
			entry.update(_facts(payload))
			entry.need_revision = payload["accepted_version_id"]
			prefill_amount(entry)
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
				"need_revision": payload["accepted_version_id"],
				"fixture_namespace": version_doc.fixture_namespace or root.fixture_namespace,
				**_facts(payload),
			}
		)
		prefill_amount(entry)
		entry.insert(ignore_permissions=True)
		added.append(entry.entry_id)
	return {"ok": True, "added": added, "refreshed": refreshed, "removed": removed}


def _pinned(version_name: str) -> dict[str, str]:
	"""Need → the revision this Version carries for it."""
	rows = frappe.get_all(
		"Departmental Plan Entry",
		filters={"dpp_version": version_name, "source_origin": NEED_ORIGIN},
		fields=["need", "need_revision"],
		limit_page_length=0,
	)
	return {cstr(row.need): cstr(row.need_revision) for row in rows}


def missing_sources(version_doc) -> list[dict[str, Any]]:
	"""The current accepted Needs whose current revision this Version does
	not carry, as their §7.1 payloads (`need_id`, `need_reference`,
	`accepted_version_id`) — within a correction's cohort, as `coverage_gaps`."""
	root = frappe.db.get_value(
		"Departmental Plan",
		version_doc.departmental_plan,
		["organisation_unit", "fiscal_year"],
		as_dict=True,
	)
	sources = _cohort_filter(version_doc, current_accepted_sources(root.fiscal_year, root.organisation_unit))
	pinned = _pinned(version_doc.name)
	return [payload for payload in sources if pinned.get(cstr(payload["need_id"])) != cstr(payload["accepted_version_id"])]


def coverage_gaps(version_doc) -> list[str]:
	"""Need references whose current accepted revision is not represented
	exactly once on this Version — the §5.1 submission blocker."""
	return [cstr(payload.get("need_reference") or payload["need_id"]) for payload in missing_sources(version_doc)]


def late_needs(root) -> list[dict[str, Any]]:
	"""An accepted departmental plan with no open candidate, and the accepted
	Needs it does not carry: each accepted (or given a new accepted revision)
	after the plan was, so only a departmental update can add it (§5.1.2 "a
	different Need accepted while a submission is under review" and §5.1.3's
	agreed clarification; owner decision 26 Sep 2026). Empty in every other
	state — a Draft takes new Needs in by itself and a submission under review
	is waited out."""
	if root.current_state != "Accepted" or not root.current_accepted_version:
		return []
	if cstr(root.current_version) != cstr(root.current_accepted_version):
		return []
	return missing_sources(frappe.get_doc("Departmental Plan Version", root.current_accepted_version))


def late_needs_since(late: list[dict[str, Any]]):
	"""When the plan started missing a Need: the earliest acceptance among
	them, through the published acceptance-evidence read (D5)."""
	instants = []
	for payload in late:
		evidence = need_acceptance_evidence(cstr(payload["need_id"]), cstr(payload["accepted_version_id"]))
		if evidence and evidence.get("occurred_at"):
			instants.append(evidence["occurred_at"])
	return min(instants) if instants else None


def need_list(late: list[dict[str, Any]]) -> str:
	"""`NDS-…-0005` or `NDS-…-0005 and NDS-…-0006`; three or more are counted."""
	refs = [cstr(payload.get("need_reference") or payload["need_id"]) for payload in late]
	if len(refs) == 1:
		return refs[0]
	if len(refs) == 2:
		return f"{refs[0]} and {refs[1]}"
	return f"{len(refs)} accepted needs"


# --------------------------------------------------------------------------
# Where each accepted Need stands against its department's plan, projected
# back to Departmental Needs (owner decision 26 Sep 2026) so the need's own
# page can say it is not in the plan yet. Planning reconciles the whole
# department after every change to its plan and every Need acceptance; the
# consumer ignores an unchanged position, so this is safe to repeat.
# --------------------------------------------------------------------------

POSITION_NO_UPDATE = "No update needed"
POSITION_UPDATE_REQUIRED = "Update required"
POSITION_AFTER_SUBMISSION = "After current submission"


def need_positions(organisation_unit: str, fiscal_year: str) -> tuple[str, list[dict[str, str]]]:
	"""(departmental plan reference, one position per current accepted Need)."""
	root = frappe.db.get_value(
		"Departmental Plan",
		{"organisation_unit": organisation_unit, "fiscal_year": fiscal_year},
		["name", "dpp_reference", "current_state", "current_version", "current_accepted_version"],
		as_dict=True,
	)
	if not root or not root.current_version:
		return "", []
	sources = current_accepted_sources(fiscal_year, organisation_unit)
	if not sources:
		return cstr(root.dpp_reference), []
	version = frappe.db.get_value(
		"Departmental Plan Version", root.current_version, ["name", "version_status", "returned_from_submission"], as_dict=True,
	)
	pinned = _pinned(version.name)
	cohort = submission_cohort(version.returned_from_submission) if version.returned_from_submission else None
	accepted_as_current = root.current_state == "Accepted" and cstr(root.current_version) == cstr(root.current_accepted_version)
	positions = []
	for payload in sources:
		need, revision = cstr(payload["need_id"]), cstr(payload["accepted_version_id"])
		carried = ""
		if version.version_status == "Draft":
			# A Draft takes every current accepted Need in by itself, except a
			# correction, which keeps the cohort Procurement returned (§5.1.2).
			position = POSITION_AFTER_SUBMISSION if cohort is not None and need not in cohort else POSITION_NO_UPDATE
		elif version.version_status == "Submitted":
			position = POSITION_NO_UPDATE if pinned.get(need) == revision else POSITION_AFTER_SUBMISSION
		elif accepted_as_current and pinned.get(need) != revision:
			position, carried = POSITION_UPDATE_REQUIRED, pinned.get(need, "")
		else:
			# In the accepted plan, or a first plan withdrawn before
			# acceptance, which Start departmental plan reopens with every
			# accepted Need in it: no update is owed on the Need.
			position = POSITION_NO_UPDATE
		positions.append({"need": need, "need_revision": revision, "position": position, "carried_revision": carried})
	return cstr(root.dpp_reference), positions


def publish_need_positions(organisation_unit: str, fiscal_year: str, *, source: str) -> int:
	"""Project every current accepted Need's position through Departmental
	Needs' published consumer (never a table write); returns how many it sent.
	A Need Departmental Needs does not confirm as currently accepted is
	skipped: an event payload can outlive the acceptance it announced."""
	from frappe.utils import now_datetime

	from kentender_procurement.departmental_needs.services import usage as needs_usage

	reference, positions = need_positions(organisation_unit, fiscal_year)
	occurred = now_datetime()
	sent = 0
	for row in positions:
		if current_accepted_revision_of(row["need"], fiscal_year) != row["need_revision"]:
			continue
		needs_usage.project_planning_intake(
			departmental_need=row["need"],
			need_revision=row["need_revision"],
			position=row["position"],
			departmental_plan=reference,
			carried_revision=row["carried_revision"],
			source_event_id=f"{cstr(source)}:{row['need']}",
			source_event_time=occurred,
			user="Administrator",
		)
		sent += 1
	return sent
