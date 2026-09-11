# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §16 — the deterministic Ministry of Health Tender
Preparation walkthrough, chained after Procurement Requisitions' own §16
pack (plan D19): one real `PrepareTender` by Brian Wafula on the canonical
authorised handoff, the five tasks, readiness (0 Blocking · 1 Warning),
submission, a return by Charles Mutiso, the corrected resubmission, approval,
the Ready publication handoff, the downstream acknowledgment on 15 May 2027
and the milestone actual published to Planning — every step through the
module's own commands as the named actors, then the §16.2 instants stamped
onto the rows this module owns.

**Decision D19 as built (recorded in the tracker's decision log).** The plan
assumed a *second* authorised Requisition profile so REQ's fixture 4 could
stay unconsumed. Requisitions' own seed proves that impossible on the
canonical world: the combined item is the only Goods-classified, IT-equipment-
eligible Plan Item, and REQ_PLAN_INELIGIBLE allows one non-terminal
Requisition per item. §16.2 itself says the walkthrough consumes
`REQ-MOH-2027-033-001`'s handoff, so this seed consumes the one base
handoff — replacing Requisitions' retired synthetic `seed_consumed_handoff()`
with a real consumption by a real Tender — and the "Ready to prepare"
state is exercised by the Playwright world, never the canonical seed.

Requisitions' own consumption columns are stamped by Requisitions'
`stamp_handoff_consumption_clock()`; Planning's milestone actual is written
through `planning_gateway` inside the real acknowledgment; this module never
writes a sibling module's row directly (the seed contract test pins that).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_requisitions.seeds import kentender_mvp_v1 as req_seed

NS = "KENTENDER_MVP_1_R1_TPR"

OFFICER = "brian.wafula@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"

CONTACT_OFFICE = "Ministry of Health Procurement Office"
INSPECTION_LOCATION = req_seed.DELIVERY_LOCATION
PUBLISHED_ON = "2027-05-15"

# The MoH walkthrough's own officer values — the template fixture
# (`tender_templates/it_equipment_open_v1/fixtures/moh_input.json`) renders
# exactly these, so the seeded Tender and the curated render agree.
TASK1 = {
	"tender_title": "Supply and delivery of business laptops", "issue_date": "2027-05-15", "clarification_deadline": "2027-05-27 17:00:00",
	"submission_deadline": "2027-06-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000, "pre_tender_meeting": False,
}
TASK4 = {
	"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True, "minimum_comparable_contracts": "2",
	"experience_period_years": "5", "after_sales_evidence_required": True, "after_sales_evidence": "Kenya service-centre details and escalation contacts",
}
TASK5 = {
	"inspection_location": INSPECTION_LOCATION, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
	"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": CONTACT_OFFICE,
}
RETURN_REASON = "Confirm whether manufacturer authorisation is necessary for business laptops and update the evidence requirement accordingly."
UPSTREAM_REASON = "The department's confirmed quantity for the second item no longer matches the authorised package; correct it upstream."

# §16.2's exact instants. The site's system time zone is Africa/Nairobi and
# Frappe stores naive site-local datetimes, so these are the EAT wall-clock
# values exactly as §16.2 states them (the read models label them "EAT").
CLOCK = {
	"draft_created": "2027-03-20 09:00:00",  # handoff consumed; Draft Version 1
	"tasks_completed": "2027-03-20 11:30:00",
	"readiness_run": "2027-03-20 11:35:00",  # 0 Blocking · 1 Warning
	"submitted": "2027-03-20 11:40:00",
	"returned": "2027-03-25 14:00:00",  # Draft Version 2
	"resubmitted": "2027-04-15 09:15:00",
	"approved": "2027-04-20 10:00:00",  # publication handoff Ready
	"consumed": "2027-05-15 08:00:00",  # acknowledged; milestone actual published
}

FAMILY = ("Tender Preparation Event", "Tender Preparation Decision", "Tender Preparation Task", "Tender Publication Handoff", "Tender Preparation Version")


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _key(step: str) -> str:
	return f"tpr-seed:{step}"


def _prepare_key(handoff: str, profile: str) -> str:
	"""The one command that runs before a Tender name exists. Every later key
	carries the minted Tender name and is unique by construction; this one
	takes a nonce instead, because Requisitions' own command journal keeps
	the consumption row keyed off it across a Tender-side reset and would
	refuse a replay whose payload names a different (new) Tender. Seed
	idempotency rests on the pre-check in `upsert_tender_preparation`, never
	on journal replay."""
	return _key(f"{handoff}:{profile}:prepare:{frappe.generate_hash(length=8)}")


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw("Tender Preparation seed fixtures are test/demo data. Enable developer_mode or allow_tests on this site before building them.")


# --- prerequisites -----------------------------------------------------------


def verify_prerequisites() -> dict[str, Any]:
	"""Requisitions' world plus the Tender-side masters and responsibilities
	this walkthrough needs; the template bundle registered and Available."""
	from kentender_procurement.tender_templates import registry

	prereqs = dict(req_seed.verify_prerequisites())
	missing = []
	for user, role in ((OFFICER, "Procurement Officer"), (HOPF, "Head of Procurement Function")):
		if not frappe.db.exists("User Responsibility Assignment", {"user": user, "business_role": role, "status": "Enabled"}):
			missing.append(f"{user} lacks an Enabled {role} responsibility")
	if not frappe.db.exists("Contact Office", {"office_name": CONTACT_OFFICE, "status": "Active"}):
		missing.append(f"Contact Office '{CONTACT_OFFICE}' is not Active")
	if not frappe.db.exists("Delivery Location", {"location_name": INSPECTION_LOCATION, "status": "Active"}):
		missing.append(f"Delivery Location '{INSPECTION_LOCATION}' is not Active")
	if missing:
		frappe.throw("Tender Preparation seed prerequisites missing: " + "; ".join(missing))
	installed = registry.install()
	prereqs["template"] = installed.get("name") or installed.get("template") or str(installed)
	return prereqs


def _base_handoff() -> tuple[str, str]:
	"""The canonical authorised Requisition and its handoff, building
	Requisitions' fixture 4 first when it is absent (idempotent on its side)."""
	base = req_seed.upsert_requisitions_base(commit=False)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": base["requisition"]}, "name")
	if not handoff:
		frappe.throw(f"{base['requisition']} has no authorised handoff to prepare a Tender from.")
	return base["requisition"], handoff


def _tenders_on(handoff: str) -> list[dict[str, Any]]:
	return frappe.get_all("Prepared Tender", filters={"requisition_handoff": handoff}, fields=["name", "tender_reference", "current_state", "publication_consumed_at", "publication_handoff", "record_version"], order_by="creation asc")


# --- the integrated walkthrough (§16.2) -------------------------------------


def upsert_tender_preparation(*, commit: bool = False) -> dict[str, Any]:
	"""§16.2 end to end, through the real commands as the named actors.
	Idempotent: a rerun that finds the walkthrough already approved and
	acknowledged on the canonical handoff returns it untouched (seeds and
	retries never duplicate a Tender, Version, task, decision or handoff)."""
	from kentender_procurement.tender_preparation.services import draft_commands as cmd
	from kentender_procurement.tender_preparation.services import lifecycle, publication

	_guard()
	frappe.set_user("Administrator")
	verify_prerequisites()
	requisition, handoff = _base_handoff()

	existing = _tenders_on(handoff)
	if existing:
		row = existing[-1]
		if row.current_state == "Approved for publication" and row.publication_consumed_at:
			if commit:
				frappe.db.commit()
			return {"ok": True, "idempotent": True, "tender": row.name, "tender_reference": row.tender_reference, "publication_handoff": row.publication_handoff, "requisition": requisition, "handoff": handoff}
		frappe.throw(f"{row.name} exists mid-lifecycle on the canonical handoff ({row.current_state}) — run reset_tender_preparation_seed() before reseeding.")

	def _root(tender: str):
		return frappe.get_doc("Prepared Tender", tender)

	with _as(OFFICER):
		prepared = cmd.prepare_tender(handoff=handoff, idempotency_key=_prepare_key(handoff, "walkthrough"))
		tender = prepared["tender"]
		saved = cmd.save_tender_draft(tender=tender, values={**TASK1, **TASK4, **TASK5}, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v1:save"))
		if not saved.get("ok"):
			frappe.throw(f"Seed draft did not save: {saved}")
		cmd.run_tender_readiness(tender=tender, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v1:readiness"))
		submitted = lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v1:submit"))

	with _as(HOPF):
		returned = lifecycle.return_tender_for_correction(task=submitted["task"], reason=RETURN_REASON, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v1:return"))

	with _as(OFFICER):
		# the correction confirms manufacturer authorisation as proportionate
		# for business laptops (the Warning stays, by design) and resubmits
		saved = cmd.save_tender_draft(tender=tender, values={**TASK1, **TASK4, **TASK5}, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v2:save"))
		if not saved.get("ok"):
			frappe.throw(f"Seed correction did not save: {saved}")
		cmd.run_tender_readiness(tender=tender, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v2:readiness"))
		resubmitted = lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v2:submit"))

	with _as(HOPF):
		approved = lifecycle.approve_tender_for_publication(task=resubmitted["task"], expected_record_version=_root(tender).record_version, idempotency_key=_key(f"{tender}:v2:approve"))

	frappe.set_user("Administrator")
	acknowledged = publication.acknowledge_publication_consumed(tender=tender, correlation_id=_key(f"{tender}:ack"), published_on=PUBLISHED_ON)

	_stamp_design_clock(tender)
	req_seed.stamp_handoff_consumption_clock(requisition, when=CLOCK["draft_created"])
	if commit:
		frappe.db.commit()
	return {
		"ok": True, "idempotent": False, "tender": tender, "tender_reference": prepared["tender_reference"], "requisition": requisition, "handoff": handoff,
		"returned_version": returned["returned_version"], "approved_version": approved["tender_version"], "publication_handoff": approved["publication_handoff"],
		"acknowledged": acknowledged.get("action"), "actual_invitation_date": acknowledged.get("actual_invitation_date"),
	}


def _stamp_design_clock(tender: str) -> None:
	"""§16.2 instants on the rows this module owns (never a sibling's)."""
	versions = frappe.get_all("Tender Preparation Version", filters={"tender": tender}, fields=["name", "version_number"], order_by="version_number asc")
	stamps = {
		1: {"creation": CLOCK["draft_created"], "prepared_at": CLOCK["draft_created"], "readiness_run_at": CLOCK["readiness_run"], "submitted_at": CLOCK["submitted"], "decided_at": CLOCK["returned"]},
		2: {"creation": CLOCK["returned"], "prepared_at": CLOCK["returned"], "readiness_run_at": CLOCK["resubmitted"], "submitted_at": CLOCK["resubmitted"], "decided_at": CLOCK["approved"]},
	}
	for version in versions:
		values = {**stamps.get(version.version_number, {}), "fixture_namespace": NS}
		frappe.db.set_value("Tender Preparation Version", version.name, values, update_modified=False)
	by_decision = {"Return for correction": CLOCK["returned"], "Approve for publication": CLOCK["approved"]}
	for decision in frappe.get_all("Tender Preparation Decision", filters={"tender": tender}, fields=["name", "decision"]):
		values = {"fixture_namespace": NS}
		when = by_decision.get(decision.decision)
		if when:
			values["decided_at"] = when
		frappe.db.set_value("Tender Preparation Decision", decision.name, values, update_modified=False)
	version_clock = {v.name: (CLOCK["submitted"] if v.version_number == 1 else CLOCK["resubmitted"]) for v in versions}
	for task in frappe.get_all("Tender Preparation Task", filters={"tender": tender}, fields=["name", "tender_version"]):
		frappe.db.set_value("Tender Preparation Task", task.name, {"creation": version_clock.get(task.tender_version), "fixture_namespace": NS}, update_modified=False)
	for handoff in frappe.get_all("Tender Publication Handoff", filters={"tender": tender}, pluck="name"):
		frappe.db.set_value("Tender Publication Handoff", handoff, {"generated_at": CLOCK["approved"], "consumed_at": CLOCK["consumed"], "fixture_namespace": NS}, update_modified=False)
	frappe.db.set_value("Prepared Tender", tender, {"creation": CLOCK["draft_created"], "publication_consumed_at": CLOCK["consumed"], "fixture_namespace": NS}, update_modified=False)


# --- reset and the on-demand stopped-Version profile -------------------------


def reset_tender_preparation_seed(*, commit: bool = False) -> dict[str, int]:
	"""Remove the canonical walkthrough: release the handoff consumption
	through Requisitions' published seam (as the Head of Procurement Function,
	a Tender caller) while the Requisition is still Authorised, then delete the
	Tender-family rows this module owns. Planning's milestone actual is never
	unwritten (§10.5 never-overwrite); a reseed offers the same date, which
	the gateway accepts."""
	from kentender_procurement.tender_preparation.services import handoff_gateway

	_guard()
	frappe.set_user("Administrator")
	deleted: dict[str, int] = {}
	plan_item_id = req_seed._plan_item_id(req_seed.COMBINED_ITEM_TITLE)
	requisitions = frappe.get_all("Procurement Requisition", filters={"plan_item_id": plan_item_id}, pluck="name") if plan_item_id else []
	handoffs = frappe.get_all("Authorised Requisition Handoff", filters={"requisition": ("in", requisitions or ("",))}, fields=["name", "requisition", "tender", "consumed_at"])
	tenders = set(frappe.get_all("Prepared Tender", filters={"fixture_namespace": NS}, pluck="name"))
	for handoff in handoffs:
		tenders |= set(frappe.get_all("Prepared Tender", filters={"requisition_handoff": handoff.name}, pluck="name"))
		if handoff.consumed_at and handoff.tender in tenders and cstr(frappe.db.get_value("Procurement Requisition", handoff.requisition, "current_state")) == "Authorised":
			with _as(HOPF):
				handoff_gateway.release_consumption(handoff=handoff.name, tender=handoff.tender, reason="KENTENDER_MVP_V1 Tender Preparation reseed.", idempotency_key=_key(f"{handoff.name}:{handoff.tender}:reset-release"), user=HOPF)
	names = list(tenders) or [""]
	for doctype in FAMILY:
		rows = frappe.get_all(doctype, filters={"tender": ("in", names)}, pluck="name")
		if rows:
			frappe.db.delete(doctype, {"name": ("in", rows)})
		deleted[doctype] = len(rows)
	if tenders:
		frappe.db.delete("Prepared Tender", {"name": ("in", list(tenders))})
	deleted["Prepared Tender"] = len(tenders)
	journal = frappe.get_all("Tender Preparation Command Journal", filters={"idempotency_key": ("like", "tpr-seed:%")}, pluck="name")
	if journal:
		frappe.db.delete("Tender Preparation Command Journal", {"name": ("in", journal)})
	deleted["Tender Preparation Command Journal"] = len(journal)
	if commit:
		frappe.db.commit()
	return deleted


def seed_upstream_correction_profile(*, commit: bool = False) -> dict[str, Any]:
	"""§16.2's stopped Tender Version — on demand, mutually exclusive with the
	integrated walkthrough (it shares the one canonical handoff): a fresh
	Draft whose officer requests an upstream correction, releasing the
	handoff. The corrected Requisition successor handoff waits on a
	Requisitions successor command (FOLLOW_UPS FU-12)."""
	from kentender_procurement.tender_preparation.services import draft_commands as cmd
	from kentender_procurement.tender_preparation.services import lifecycle

	_guard()
	frappe.set_user("Administrator")
	verify_prerequisites()
	reset_tender_preparation_seed(commit=False)
	_, handoff = _base_handoff()
	with _as(OFFICER):
		prepared = cmd.prepare_tender(handoff=handoff, idempotency_key=_prepare_key(handoff, "upstream"))
		tender = prepared["tender"]
		root = frappe.get_doc("Prepared Tender", tender)
		stopped = lifecycle.request_tender_upstream_correction(tender=tender, reason=UPSTREAM_REASON, expected_record_version=root.record_version, idempotency_key=_key(f"{tender}:upstream"))
	frappe.set_user("Administrator")
	frappe.db.set_value("Prepared Tender", tender, {"creation": CLOCK["draft_created"], "fixture_namespace": NS}, update_modified=False)
	frappe.db.set_value("Tender Preparation Version", stopped["tender_version"], {"fixture_namespace": NS}, update_modified=False)
	if commit:
		frappe.db.commit()
	return {"ok": True, "tender": tender, "tender_version": stopped["tender_version"], "handoff": handoff, "handoff_release": stopped.get("handoff_release")}


# --- validator ---------------------------------------------------------------


def validate_tender_preparation_seed() -> list[dict[str, Any]]:
	"""§16 — validate the integrated walkthrough through the same reads the
	page uses, as check rows for the core validator."""
	from kentender_procurement.tender_preparation.services import events, planning_gateway, read

	checks: list[dict[str, Any]] = []

	def check(name: str, ok: bool, detail: str = "") -> None:
		checks.append({"check": f"tender_preparation.v16.{name}", "ok": bool(ok), "detail": detail})

	plan_item_id = req_seed._plan_item_id(req_seed.COMBINED_ITEM_TITLE)
	root_name = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised"}, "name") if plan_item_id else None
	check("requisition.authorised", bool(root_name), str(root_name))
	if not root_name:
		return checks
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": root_name}, ["name", "tender", "consumed_at"], as_dict=True)
	check("handoff.exists", bool(handoff), str(handoff and handoff.name))
	if not handoff:
		return checks
	tenders = _tenders_on(handoff.name)
	check("tender.one", len(tenders) == 1, str(len(tenders)))
	if not tenders:
		return checks
	tender = frappe.get_doc("Prepared Tender", tenders[0].name)
	check("tender.reference_shape", cstr(tender.tender_reference).startswith("TND-MOH-2027-"), tender.tender_reference)
	check("tender.approved", tender.current_state == "Approved for publication", tender.current_state)
	check("handoff.consumed_by_this_tender", handoff.tender == tender.name and bool(handoff.consumed_at), f"{handoff.tender} @ {handoff.consumed_at}")
	versions = frappe.get_all("Tender Preparation Version", filters={"tender": tender.name}, fields=["name", "version_number", "version_status", "blocking_count", "warning_count", "submitted_at", "decided_at"], order_by="version_number asc")
	check("versions.two", len(versions) == 2, str([(v.version_number, v.version_status) for v in versions]))
	if len(versions) == 2:
		check("version1.returned", versions[0].version_status == "Returned", versions[0].version_status)
		check("version2.approved", versions[1].version_status == "Approved" and tender.approved_version == versions[1].name, versions[1].version_status)
		check("readiness.0_blocking_1_warning", (versions[0].blocking_count or 0) == 0 and (versions[0].warning_count or 0) == 1, f"{versions[0].blocking_count}/{versions[0].warning_count}")
		check("clock.submitted_20_mar", cstr(versions[0].submitted_at).startswith("2027-03-20 11:40"), cstr(versions[0].submitted_at))
		check("clock.approved_20_apr", cstr(versions[1].decided_at).startswith("2027-04-20 10:00"), cstr(versions[1].decided_at))
	check("decisions.two", frappe.db.count("Tender Preparation Decision", {"tender": tender.name}) == 2, str(frappe.db.count("Tender Preparation Decision", {"tender": tender.name})))
	check("tasks.two_completed", frappe.db.count("Tender Preparation Task", {"tender": tender.name, "status": "Completed"}) == 2, "")
	handoffs = frappe.get_all("Tender Publication Handoff", filters={"tender": tender.name}, fields=["name", "status", "published_on", "package_digest", "consumed_at"])
	check("publication_handoff.one_consumed", len(handoffs) == 1 and handoffs[0].status == "Consumed" and bool(handoffs[0].package_digest), str([(h.status, cstr(h.published_on)) for h in handoffs]))
	if handoffs:
		check("publication_handoff.published_on_15_may", cstr(handoffs[0].published_on) == PUBLISHED_ON, cstr(handoffs[0].published_on))
	check("milestone.event", bool(events.find(events.EVENT_MILESTONE_ACTUAL, _key(f"{tender.name}:ack"))), "")
	actual = planning_gateway.current_actual_invitation_date(tender.plan_item_id)
	check("planning.actual_invitation_15_may", bool(actual) and getdate(actual) == getdate(PUBLISHED_ON), cstr(actual))
	approved_view = read.get_approved_tender(tender=tender.name, user=AUDITOR)
	check("read.approved_by_charles", approved_view.get("outcome") == "OK" and (approved_view.get("approved_by") or {}).get("name") == "Charles Mutiso", str(approved_view.get("approved_by")))
	check("read.approved_at_20_apr_10_00_eat", (approved_view.get("approved_by") or {}).get("at") == "20 April 2027, 10:00 EAT", str((approved_view.get("approved_by") or {}).get("at")))
	check("read.consumed_at_15_may_08_00_eat", (approved_view.get("publication_handoff") or {}).get("consumed_at") == "15 May 2027, 08:00 EAT", str((approved_view.get("publication_handoff") or {}).get("consumed_at")))
	check("read.mappings_complete", all(approved_view.get("mappings", {}).get(k) for k in ("supplier_response_schema", "evaluation_contract", "contract_obligations")), "")
	workspace = read.get_tender_preparation_workspace(user=OFFICER)
	check("read.officer_workspace", workspace.get("outcome") == "OK" and any(t["tender"] == tender.name for t in workspace.get("tenders", [])), "")
	check("read.handoff_not_offered_again", workspace.get("outcome") == "OK" and not any(r.get("handoff") == handoff.name for r in workspace.get("ready_to_prepare", [])), "")
	return checks
