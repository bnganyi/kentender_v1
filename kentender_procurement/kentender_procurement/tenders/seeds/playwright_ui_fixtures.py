# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Playwright fixtures for the Tenders browser specs (TPR-CHG-001 v0.8,
plan D19 / tracker TND-701..714). Invoked via `bench execute`; never
imported by `api.py`.

The world extends Procurement Requisitions' own Playwright world
(`procurement_requisitions.seeds.playwright_ui_fixtures`, FY 2099-2100):
an authorised, unconsumed `AuthorisedRequisitionHandoff` can only come from
Requisitions' real commands, and that world already builds one
(`reset_authorised_fixture`) as named Planning/Requisitions actors. Tenders
adds its own actors — a Procurement Officer, an Accounting Officer, a
"both" actor holding every Tenders responsibility (segregation), the
bidder-facing service identity — and the two masters its forms need. Every
fixture below drives the real Tenders commands as those actors with the
§13.3 clock injected (`frappe.flags.kt_tenders_clock`), so a screen renders
the instants the boards show. This world and the Python suite never run
concurrently on one site (both move the same flags; PLN-CHG-001 D13)."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any
from uuid import uuid4

import frappe

from kentender_procurement.procurement_requisitions.seeds import playwright_ui_fixtures as req_pw

NS_PW = "KENTENDER_TND_PLAYWRIGHT"
OFFICER = "pw.tnd.officer@example.test"
HOPF = req_pw.HOPF
AO = "pw.tnd.ao@example.test"
BOTH = "pw.tnd.both@example.test"
AUDITOR = req_pw.AUDITOR
OUTSIDER = req_pw.OUTSIDER
NOBODY = req_pw.NOBODY
PRODUCER = "pw.tnd.producer@example.test"
TND_ACTORS = (OFFICER, AO, BOTH, PRODUCER)
ALL_ACTORS = TND_ACTORS + (HOPF, AUDITOR, OUTSIDER, NOBODY)

LOCATION = "Playwright — Tenders Delivery Location"
CONTACT_OFFICE = "Playwright — Tenders Contact Office"
CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")

# §13.3 instants, pinned.
CLOCK = {
	"start": "2027-03-20 09:00:00", "submit": "2027-03-20 11:40:00", "return": "2027-03-25 14:00:00", "resubmit": "2027-04-15 09:15:00",
	"approve": "2027-04-20 10:00:00", "authorise": "2027-05-15 07:55:00", "confirm": "2027-05-15 08:03:00", "addendum": "2027-05-31 08:30:00",
	"addendum_confirm": "2027-05-31 09:00:00", "inquiry": "2027-06-01 09:00:00", "respond": "2027-06-01 11:00:00", "cancel": "2027-06-10 09:30:00", "close": "2027-06-12 11:00:00",
}
AVAILABLE = {"STATE_PORTAL": "2027-05-15 08:00:00", "MINISTRY_WEBSITE": "2027-05-15 08:00:00", "NOTICE_BOARD": "2027-05-15 08:15:00", "NATIONAL_NEWSPAPERS": "2027-05-15 08:20:00"}

TENDER_DOCTYPES = (
	"Tender Event", "Tender Document", "Tender Submission Handoff", "Tender Channel Confirmation", "Tender Addendum Inquiry", "Tender Addendum",
	"Tender Cancellation", "Tender Publication", "Tender Decision", "Tender Task", "Tender Version", "Tender",
)


def _key() -> str:
	return f"tnd-pw-{uuid4().hex}"


def _clock(name: str) -> None:
	frappe.flags.kt_tenders_clock = CLOCK[name]


def _as(user: str):
	return req_pw._as(user)


def _user(email: str, full_name: str) -> None:
	req_pw._user(email, full_name)


def _grant(email: str, role: str) -> None:
	from kentender_core.services import responsibility_administration as administration

	administration.grant(user=email, business_role=role, organisation_unit="", fixture_namespace=NS_PW, actor="Administrator")


def evidence_file(file_name: str) -> str:
	"""A real one-pixel PNG as a private File (Frappe runs images through
	Pillow on insert) — publication evidence a spec never has to upload."""
	from PIL import Image

	buffer = BytesIO()
	Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format="PNG")
	return frappe.get_doc({"doctype": "File", "file_name": file_name, "is_private": 1, "content": buffer.getvalue()}).insert(ignore_permissions=True).name


# --- world -------------------------------------------------------------------


def ensure_world(*, commit: bool = True) -> dict[str, Any]:
	req_pw._guard()
	frappe.set_user("Administrator")
	world = req_pw.ensure_world(commit=False)
	from kentender_core.seeds import site_setup
	from kentender_core.services.business_role_registry import ensure_roles
	from kentender_procurement.tender_templates import registry
	from kentender_procurement.tenders.services import inquiries
	from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

	ensure_roles()
	for email, name in ((OFFICER, "Playwright Tenders Officer"), (AO, "Playwright Tenders AO"), (BOTH, "Playwright Tenders Both"), (PRODUCER, "Playwright Tenders Bidder Service")):
		_user(email, name)
	inquiries.ensure_producer_role()
	producer = frappe.get_doc("User", PRODUCER)
	if INQUIRY_PRODUCER_ROLE not in {r.role for r in producer.roles}:
		producer.add_roles(INQUIRY_PRODUCER_ROLE)
	_grant(OFFICER, "Procurement Officer")
	_grant(AO, "Accounting Officer")
	_grant(BOTH, "Procurement Officer")
	_grant(BOTH, "Head of Procurement Function")
	_grant(BOTH, "Accounting Officer")
	for doctype, field, name in (("Delivery Location", "location_name", LOCATION), ("Contact Office", "office_name", CONTACT_OFFICE)):
		if not frappe.db.exists(doctype, name):
			values = {"doctype": doctype, field: name, "address": "Playwright fixture address, Nairobi", "status": "Active", "fixture_namespace": NS_PW}
			if doctype == "Contact Office":
				values.update({"contact_email": "procurement@example.test", "contact_phone": "+254 700 000000"})
			frappe.get_doc(values).insert(ignore_permissions=True)
	registry.install()
	site_setup._seed_publication_obligations()
	if commit:
		frappe.db.commit()
	return {**world, "officer": OFFICER, "hopf": HOPF, "ao": AO, "both": BOTH, "auditor": AUDITOR}


def _wipe_tenders() -> None:
	"""Every Tender this world's actors created, children first, at the
	database level (controllers refuse plain deletes by design)."""
	names = frappe.get_all("Tender", filters={"owner": ("in", ALL_ACTORS)}, pluck="name")
	if names:
		for doctype in TENDER_DOCTYPES[:-1]:
			frappe.db.delete(doctype, {"tender": ("in", names)})
		frappe.db.delete("Tender Command Journal", {"document_name": ("in", names)})
		frappe.db.delete("Tender", {"name": ("in", names)})
	frappe.db.delete("Tender Command Journal", {"idempotency_key": ("like", "tnd-pw-%")})
	frappe.db.delete("Tender Command Journal", {"actor": ("in", ALL_ACTORS)})
	frappe.db.delete("Notification Log", {"for_user": ("in", TND_ACTORS)})


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	req_pw._guard()
	frappe.set_user("Administrator")
	_wipe_tenders()
	frappe.flags.kt_tenders_clock = None
	out = req_pw.restore_site(commit=False)
	if commit:
		frappe.db.commit()
	return {**out, "tenders_wiped": True}


def reset_all(*, commit: bool = True) -> dict[str, Any]:
	req_pw._guard()
	frappe.set_user("Administrator")
	_wipe_tenders()
	req_pw.reset_all(commit=False)
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS_PW}


def _reset() -> dict[str, Any]:
	world = ensure_world(commit=False)
	_wipe_tenders()
	req_pw._wipe_requisitions_side()
	req_pw._wipe_planning_side()
	return world


# --- journeys (real commands as the fixture actors) --------------------------


def _authorised() -> dict[str, Any]:
	world = _reset()
	state = req_pw.reset_authorised_fixture(commit=False)
	return {**world, **state}


def officer_values(**overrides) -> dict[str, Any]:
	values = {
		"tender_title": "Supply and delivery of business laptops", "issue_date": "2027-05-15", "clarification_deadline": "2027-05-27 17:00:00",
		"submission_deadline": "2027-06-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000.00, "pre_tender_meeting": False,
		"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True, "minimum_comparable_contracts": 2,
		"experience_period_years": 5, "after_sales_evidence_required": True, "after_sales_evidence": "Kenya service-centre details and escalation contacts",
		"inspection_location": LOCATION, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
		"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": CONTACT_OFFICE,
	}
	values.update(overrides)
	return values


def _root(name: str):
	return frappe.get_doc("Tender", name)


def _start(handoff: str, *, user: str = OFFICER) -> dict[str, Any]:
	from kentender_procurement.tenders.services import draft_commands as cmd

	_clock("start")
	with _as(user):
		started = cmd.start_tender(handoff=handoff, idempotency_key=_key())
	root = _root(started["tender"])
	return {"tender": root.name, "tender_reference": root.tender_reference, "version": root.current_version}


def _save(name: str, values: dict[str, Any], *, user: str = OFFICER) -> None:
	from kentender_procurement.tenders.services import draft_commands as cmd

	with _as(user):
		result = cmd.save_tender_draft(tender=name, values=values, expected_record_version=_root(name).record_version, idempotency_key=_key())
	if not result.get("ok", True):
		frappe.throw(f"Tenders Playwright fixture: save refused {json.dumps(result.get('errors'))}")


def _submit(name: str, *, user: str = OFFICER) -> dict[str, Any]:
	from kentender_procurement.tenders.services import lifecycle

	_clock("submit")
	with _as(user):
		return lifecycle.submit_tender_for_approval(tender=name, expected_record_version=_root(name).record_version, idempotency_key=_key())


def _approve(name: str, task: str, *, user: str = HOPF) -> dict[str, Any]:
	from kentender_procurement.tenders.services import lifecycle

	_clock("approve")
	with _as(user):
		return lifecycle.approve_tender_package(tender=name, task=task, expected_record_version=_root(name).record_version, idempotency_key=_key())


def _authorise(name: str, task: str, *, user: str = AO) -> dict[str, Any]:
	from kentender_procurement.tenders.services import publication

	_clock("authorise")
	with _as(user):
		return publication.authorise_tender_publication(tender=name, task=task, expected_record_version=_root(name).record_version, idempotency_key=_key())


def _confirm(name: str, channel: str, *, addendum: str = "", available_at: str | None = None, user: str = HOPF) -> dict[str, Any]:
	from kentender_procurement.tenders.services import addenda, configuration_gateway, publication

	root = _root(name)
	online = channel in configuration_gateway.ONLINE_CHANNELS
	common = dict(
		available_at=available_at or AVAILABLE[channel], evidence_reference=f"REF-{channel}", evidence_file=evidence_file(f"{channel}.png"),
		public_url=f"https://portal.example.test/{channel.lower()}" if online else "", url_not_applicable_reason="" if online else "Physical channel",
		expected_record_version=root.record_version, idempotency_key=_key(), attestation_confirmed=True,
	)
	with _as(user):
		if addendum:
			return addenda.confirm_addendum_publication_channel(tender=name, addendum=addendum, channel=channel, addendum_digest=frappe.db.get_value("Tender Addendum", addendum, "addendum_digest"), **common)
		return publication.confirm_publication_channel(tender=name, channel=channel, package_digest=frappe.db.get_value("Tender Publication", root.publication, "package_digest"), **common)


def _done(state: dict[str, Any], commit: bool) -> dict[str, Any]:
	if commit:
		frappe.db.commit()
	root = frappe.db.get_value("Tender", state.get("tender"), ["tender_reference", "overall_status", "record_version"], as_dict=True) if state.get("tender") else None
	if root:
		state.update({"tender_reference": root.tender_reference, "overall_status": root.overall_status, "record_version": root.record_version})
	return state


# --- fixtures ---------------------------------------------------------------


def reset_start_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-01/02 opening state: one authorised, unconsumed handoff, no Tender."""
	return _done(_authorised(), commit)


def reset_unsupported_start_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-02 unsupported variant: the handoff's planned method is not Open Tender."""
	state = _authorised()
	handoff = frappe.get_doc("Authorised Requisition Handoff", state["handoff"])
	payload = json.loads(handoff.payload_json)
	payload["planned_method"] = "Restricted Tender"
	frappe.db.set_value("Authorised Requisition Handoff", handoff.name, "payload_json", json.dumps(payload), update_modified=False)
	return _done(state, commit)


def reset_draft_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-03 opening state: a fresh Draft, no officer values yet."""
	state = _authorised()
	state.update(_start(state["handoff"]))
	return _done(state, commit)


def reset_draft_complete_fixture(*, commit: bool = True, meeting: str = "No") -> dict[str, Any]:
	"""TPR-DES-04/05 "Ready to submit": every officer value complete."""
	state = reset_draft_fixture(commit=False)
	values = officer_values()
	if meeting == "Physical":
		values.update({"pre_tender_meeting": True, "meeting_datetime": "2027-05-22 10:00:00", "meeting_mode": "Physical", "meeting_venue": LOCATION})
	elif meeting == "Online":
		values.update({"pre_tender_meeting": True, "meeting_datetime": "2027-05-22 10:00:00", "meeting_mode": "Online", "online_joining_information": "Microsoft Teams — https://meet.example.test/tnd-pw"})
	_save(state["tender"], values)
	return _done(state, commit)


def reset_needs_attention_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-05 "Needs attention": complete except the inspection location."""
	state = reset_draft_fixture(commit=False)
	values = officer_values()
	values.pop("inspection_location")
	_save(state["tender"], values)
	return _done(state, commit)


def reset_awaiting_hopf_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-06 opening state: submitted, awaiting the HoPF."""
	state = reset_draft_complete_fixture(commit=False)
	submitted = _submit(state["tender"])
	state["task"] = submitted["task"]
	return _done(state, commit)


def reset_returned_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-13 "Returned": the HoPF returned Version 1; Version 2 is the copied Draft."""
	from kentender_procurement.tenders.services import lifecycle

	state = reset_awaiting_hopf_fixture(commit=False)
	_clock("return")
	with _as(HOPF):
		returned = lifecycle.return_tender_for_correction(tender=state["tender"], task=state["task"], reason="Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement.", affected_task="Supplier and contract requirements", expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	state["copied_draft"] = returned["copied_draft"]
	return _done(state, commit)


def reset_awaiting_ao_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-07 opening state: approved, awaiting the Accounting Officer."""
	state = reset_awaiting_hopf_fixture(commit=False)
	approved = _approve(state["tender"], state["task"])
	state["task"] = approved["task"]
	return _done(state, commit)


def reset_segregation_fixture(*, commit: bool = True, stage: str = "hopf") -> dict[str, Any]:
	"""The "both" actor prepared and submitted (stage=hopf: the HoPF decision
	is blocked for them) or also approved (stage=ao: the AO decision is)."""
	state = _authorised()
	state.update(_start(state["handoff"], user=BOTH))
	_save(state["tender"], officer_values(), user=BOTH)
	submitted = _submit(state["tender"], user=BOTH)
	state["task"] = submitted["task"]
	if stage == "ao":
		approved = _approve(state["tender"], state["task"], user=HOPF)
		state["task"] = approved["task"]
	return _done(state, commit)


def reset_publication_fixture(*, commit: bool = True, confirmed: int = 2) -> dict[str, Any]:
	"""TPR-DES-08 opening state: publication authorised, `confirmed` of four channels confirmed."""
	state = reset_awaiting_ao_fixture(commit=False)
	authorised = _authorise(state["tender"], state["task"])
	state["publication"] = authorised["publication"]
	_clock("confirm")
	for channel in CHANNELS[: max(0, int(confirmed))]:
		_confirm(state["tender"], channel)
	return _done(state, commit)


def reset_published_fixture(*, commit: bool = True, with_addendum: bool = False, with_inquiry: bool = False) -> dict[str, Any]:
	"""TPR-DES-09 opening state: Published — open; optionally one issued,
	fully confirmed addendum and one inquiry awaiting response."""
	state = reset_publication_fixture(commit=False, confirmed=4)
	if with_addendum or with_inquiry:
		state.update(_issued_addendum(state["tender"]))
	if with_inquiry:
		state.update(_inquiry(state["tender"], state["addendum"]))
	return _done(state, commit)


def reset_ended_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-09 "Submission ended": the system closed the period."""
	from kentender_procurement.tenders.services import submission_close

	state = reset_published_fixture(commit=False)
	_clock("close")
	closed = submission_close.close_tender_submission_period(tender=state["tender"], idempotency_key=_key(), user="Administrator", force=True)
	state["handoff_record"] = closed["handoff"]
	return _done(state, commit)


ADDENDUM_VALUES = {
	"change_class": "Administrative clarification", "affected_area": "Goods/delivery schedule", "affected_reference_key": "delivery_location",
	"revised_value": "Playwright — Requisitions Delivery Location, Loading Bay 3", "reason": "Loading bay reassigned after warehouse reorganisation.",
	"materiality_statement": "Same site; no change to scope, quantity, value or evaluation basis.", "revised_submission_deadline": "2027-06-12 11:00:00",
}


def _addendum_draft(name: str, *, values: dict[str, Any] | None = None) -> dict[str, Any]:
	from kentender_procurement.tenders.services import addenda

	_clock("addendum")
	with _as(OFFICER):
		created = addenda.create_addendum_draft(tender=name, expected_record_version=_root(name).record_version, idempotency_key=_key())
		addendum = created["addendum"]["name"]
		if values is not None:
			saved = addenda.update_addendum_draft(tender=name, addendum=addendum, values=values, expected_record_version=_root(name).record_version, idempotency_key=_key())
			if not saved.get("ok", True):
				frappe.throw(f"Tenders Playwright fixture: addendum save refused {json.dumps(saved.get('errors'))}")
	return {"addendum": addendum}


def _issued_addendum(name: str) -> dict[str, Any]:
	from kentender_procurement.tenders.services import addenda

	state = _addendum_draft(name, values=ADDENDUM_VALUES)
	with _as(OFFICER):
		addenda.submit_addendum_for_issue(tender=name, addendum=state["addendum"], expected_record_version=_root(name).record_version, idempotency_key=_key())
	with _as(HOPF):
		addenda.issue_addendum(tender=name, addendum=state["addendum"], expected_record_version=_root(name).record_version, idempotency_key=_key())
	for channel in CHANNELS:
		_confirm(name, channel, addendum=state["addendum"], available_at=CLOCK["addendum_confirm"])
	return state


def _inquiry(name: str, addendum: str, *, late: bool = False) -> dict[str, Any]:
	from kentender_procurement.tenders.services import inquiries

	_clock("inquiry")
	with _as(PRODUCER):
		received = inquiries.receive_addendum_inquiry(tender=name, addendum=addendum, candidate_identity="SUP-PW-0001", question="Does the clarified delivery point in the addendum apply to all lots, or only the lot originally delivered to the Central Warehouse?", received_at="2027-06-10 09:00:00" if late else CLOCK["inquiry"], inbound_event_id=_key())
	return {"inquiry": received["inquiry"], "inquiry_status": received["status"]}


def reset_addendum_draft_fixture(*, commit: bool = True, saved: bool = True) -> dict[str, Any]:
	"""TPR-DES-10 "Draft (Procurement Officer)": a saved (or empty) draft addendum."""
	state = reset_published_fixture(commit=False)
	state.update(_addendum_draft(state["tender"], values=ADDENDUM_VALUES if saved else None))
	return _done(state, commit)


def reset_addendum_awaiting_issue_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-10 "HOPF issue": submitted for issue."""
	from kentender_procurement.tenders.services import addenda

	state = reset_addendum_draft_fixture(commit=False)
	with _as(OFFICER):
		addenda.submit_addendum_for_issue(tender=state["tender"], addendum=state["addendum"], expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	return _done(state, commit)


def reset_addendum_confirming_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-10 after issue: awaiting its four channel confirmations."""
	from kentender_procurement.tenders.services import addenda

	state = reset_addendum_awaiting_issue_fixture(commit=False)
	with _as(HOPF):
		addenda.issue_addendum(tender=state["tender"], addendum=state["addendum"], expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	return _done(state, commit)


def reset_inquiry_fixture(*, commit: bool = True, late: bool = False) -> dict[str, Any]:
	"""TPR-DES-11 opening state: one inquiry awaiting response (or Late)."""
	state = reset_published_fixture(commit=False, with_addendum=True)
	state.update(_inquiry(state["tender"], state["addendum"], late=late))
	return _done(state, commit)


def reset_cancel_fixture(*, commit: bool = True, recommended: bool = False) -> dict[str, Any]:
	"""TPR-DES-12 decision state, optionally with the HoPF recommendation."""
	from kentender_procurement.tenders.services import cancellation

	state = reset_published_fixture(commit=False)
	if recommended:
		_clock("cancel")
		with _as(HOPF):
			cancellation.recommend_tender_cancellation(tender=state["tender"], ground="INADEQUATE_BUDGET", reason="Delivery timeline no longer meets user-department need following supplier market changes.", expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	return _done(state, commit)


def reset_cancelled_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-12 "Cancelled detail": cancelled by the AO with its obligations."""
	from kentender_procurement.tenders.services import cancellation

	state = reset_cancel_fixture(commit=False, recommended=True)
	_clock("cancel")
	with _as(AO):
		cancelled = cancellation.cancel_tender(tender=state["tender"], ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.", expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	state["cancellation"] = cancelled["cancellation"]
	return _done(state, commit)


def reset_correction_requested_fixture(*, commit: bool = True) -> dict[str, Any]:
	"""TPR-DES-13 "Correction requested" (+ "Corrected successor ready": the
	released handoff is itself the authorised successor in this world)."""
	from kentender_procurement.tenders.services import correction

	state = reset_awaiting_hopf_fixture(commit=False)
	_clock("return")
	with _as(HOPF):
		correction.request_requisition_correction(tender=state["tender"], reason="The authorised battery-runtime requirement must be corrected before this Tender can continue.", expected_record_version=_root(state["tender"]).record_version, idempotency_key=_key())
	return _done(state, commit)
