# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §13.3 — the deterministic canonical Tender lifecycle,
chained after Procurement Requisitions' own §16 authorised handoff (plan
decision D19: Tenders is a canonical seed stage — unlike Requisitions'
own D7 choice not to be one for its own cycle). This module never builds
its own Requisition: `verify_prerequisites()` requires the canonical
Requisitions stage's own `upsert_requisitions_base()` output already
present and unconsumed, and throws naming exactly what is missing rather
than inventing a substitute.

The one fixture (`upsert_tenders_base`) drives every real Tenders command
as the canonical actors (Brian Wafula — Procurement Officer, Charles
Mutiso — Head of Procurement Function, Amina Hassan — Accounting Officer,
Naomi Chebet — Auditor; all already hold their site-wide responsibility
from `kentender_core.seeds.site_setup`) with `frappe.flags.kt_tenders_clock`
injected at each step, matching §13.3's own instants exactly: start
20 Mar 09:00 EAT -> submit V1 11:40 -> HOPF returns 25 Mar 14:00 -> officer
resubmits V2 15 Apr 09:15 -> HOPF approves 20 Apr 10:00 -> AO authorises
15 May 07:55 -> four channels confirmed 08:03/08:04/08:06/08:07 (available
08:00, so published_at = 08:00 under plan D15) -> HOPF issues one addendum,
fully confirmed, 31 May 09:00 (deadline extended to 12 Jun 11:00) -> the
bidder-service producer delivers one inquiry 1 Jun 09:00, answered 11:00 ->
the scheduler closes the submission period 12 Jun 11:00 with its handoff.

Idempotent: a rerun that finds the canonical Tender already at
"Submission period ended" returns it untouched."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

NS = "KENTENDER_MVP_1_R1_TND"

OFFICER = "brian.wafula@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
AO = "amina.hassan@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"
PRODUCER = "tender.inquiry.producer@moh.example.test"  # the bidder-facing service identity (plan D8)

DELIVERY_LOCATION = "Ministry of Health Headquarters, Afya House, Nairobi"
CONTACT_OFFICE = "Ministry of Health Procurement Office"
CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")

# §13.3's own instants, stored as the naive site-local (EAT) values the
# services themselves store and the read models render back unchanged.
CLOCK = {
	"start": "2027-03-20 09:00:00",
	"submit_v1": "2027-03-20 11:40:00",
	"return": "2027-03-25 14:00:00",
	"resubmit_v2": "2027-04-15 09:15:00",
	"approve": "2027-04-20 10:00:00",
	"authorise": "2027-05-15 07:55:00",
	"confirm_1": "2027-05-15 08:03:00",
	"confirm_2": "2027-05-15 08:04:00",
	"confirm_3": "2027-05-15 08:06:00",
	"confirm_4": "2027-05-15 08:07:00",
	"addendum_draft": "2027-05-31 08:30:00",
	"addendum_confirm": "2027-05-31 09:00:00",
	"inquiry_received": "2027-06-01 09:00:00",
	"inquiry_answered": "2027-06-01 11:00:00",
	"close": "2027-06-12 11:00:00",
}
AVAILABLE_AT = "2027-05-15 08:00:00"

ADDENDUM_VALUES = {
	"change_class": "Administrative clarification",
	"affected_area": "Goods/delivery schedule",
	"affected_reference_key": "delivery_location",
	"revised_value": "Ministry of Health Headquarters, Afya House, Nairobi — Loading Bay 3",
	"reason": "The published address omitted the internal delivery point suppliers must use.",
	"materiality_statement": "Same site; no change to scope, quantity, value or evaluation basis.",
	"revised_submission_deadline": "2027-06-12 11:00:00",
}


def _guard() -> None:
	if frappe.flags.in_test or frappe.conf.get("developer_mode") or frappe.conf.get("allow_tests"):
		return
	frappe.throw("Tenders seed fixtures are canonical demo data. Enable developer_mode or allow_tests on this site before building them.")


@contextmanager
def _as(user: str):
	previous = frappe.session.user
	frappe.set_user(user)
	try:
		yield
	finally:
		frappe.set_user(previous)


def _key(step: str) -> str:
	return f"tnd-seed:{step}"


def _clock(step: str) -> None:
	frappe.flags.kt_tenders_clock = CLOCK[step]


def officer_values(**overrides: Any) -> dict[str, Any]:
	values = {
		"tender_title": "Supply and delivery of business laptops", "issue_date": "2027-05-15", "clarification_deadline": "2027-05-27 17:00:00",
		"submission_deadline": "2027-06-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000.00, "pre_tender_meeting": False,
		"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True, "minimum_comparable_contracts": 2,
		"experience_period_years": 5, "after_sales_evidence_required": True, "after_sales_evidence": "Kenya service-centre details and escalation contacts",
		"inspection_location": DELIVERY_LOCATION, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
		"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": CONTACT_OFFICE,
	}
	values.update(overrides)
	return values


def _evidence_file(file_name: str) -> str:
	from io import BytesIO

	from PIL import Image

	buffer = BytesIO()
	Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format="PNG")
	return frappe.get_doc({"doctype": "File", "file_name": file_name, "is_private": 1, "content": buffer.getvalue()}).insert(ignore_permissions=True).name


def verify_prerequisites() -> dict[str, str]:
	"""§13.1 — the canonical Requisitions stage's own authorised, unconsumed
	handoff on the combined item, or one loud failure naming it. Nothing
	here builds a second Requisition; that stage owns its own seed."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import COMBINED_ITEM_TITLE, _plan_item_id

	missing: list[str] = []

	def need(label: str, ok) -> None:
		if not ok:
			missing.append(label)

	need("Charles Mutiso holds Head of Procurement Function", frappe.db.exists("User Responsibility Assignment", {"user": HOPF, "business_role": "Head of Procurement Function", "status": "Enabled"}))
	need("Brian Wafula holds Procurement Officer", frappe.db.exists("User Responsibility Assignment", {"user": OFFICER, "business_role": "Procurement Officer", "status": "Enabled"}))
	need("Amina Hassan holds Accounting Officer", frappe.db.exists("User Responsibility Assignment", {"user": AO, "business_role": "Accounting Officer", "status": "Enabled"}))
	need("Naomi Chebet holds Auditor", frappe.db.exists("User Responsibility Assignment", {"user": AUDITOR, "business_role": "Auditor", "status": "Enabled"}))
	need(f"Delivery Location '{DELIVERY_LOCATION}'", frappe.db.get_value("Delivery Location", DELIVERY_LOCATION, "status") == "Active")
	need(f"Contact Office '{CONTACT_OFFICE}'", frappe.db.get_value("Contact Office", CONTACT_OFFICE, "status") == "Active")
	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	need(f"Active Plan Item '{COMBINED_ITEM_TITLE}' (run make seed-canonical THROUGH=planning first)", plan_item_id)
	requisition = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": "Authorised"}, "name") if plan_item_id else None
	need(f"an Authorised Requisition on '{COMBINED_ITEM_TITLE}' (run make seed-canonical THROUGH=requisitions first)", requisition)
	handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": requisition, "consumed_at": ("is", "not set")}, "name") if requisition else None
	consumer = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": requisition}, "tender") if requisition else None
	if missing:
		frappe.throw("TPR §13 seed prerequisites are absent or differ — seeds never invent a substitute. Missing: " + "; ".join(missing))
	return {"plan_item_id": plan_item_id, "requisition": requisition, "handoff": handoff, "existing_consumer": consumer}


def ensure_producer_role() -> str:
	from kentender_procurement.tenders.services import inquiries
	from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

	inquiries.ensure_producer_role()
	if not frappe.db.exists("User", PRODUCER):
		user = frappe.get_doc({"doctype": "User", "email": PRODUCER, "first_name": "Tender Inquiry Producer", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", PRODUCER)
	if frappe.db.get_value("User", PRODUCER, "user_type") != "System User":
		user.add_roles("Desk User")
	if INQUIRY_PRODUCER_ROLE not in {r.role for r in user.roles}:
		user.add_roles(INQUIRY_PRODUCER_ROLE)
	return PRODUCER


def upsert_tenders_base(*, commit: bool = False) -> dict[str, Any]:
	"""§13.3 fixture — the primary Tender lifecycle through to a closed
	submission period, built through the real commands. Idempotent: a
	rerun that finds the canonical Tender already ended returns it
	untouched."""
	from kentender_procurement.tender_templates import registry
	from kentender_procurement.tenders.services import addenda, cancellation, channel_confirmation, configuration_gateway, draft_commands as cmd, inquiries, lifecycle, publication, submission_close

	_guard()
	registry.install()
	from kentender_core.seeds import site_setup

	site_setup._seed_publication_obligations()
	ensure_producer_role()
	prereqs = verify_prerequisites()

	existing = frappe.db.get_value("Tender", {"requisition": prereqs["requisition"]}, ["name", "overall_status"], as_dict=True)
	if existing:
		if existing.overall_status != "Submission period ended":
			frappe.throw(f"{existing.name} exists mid-lifecycle on the canonical Requisition ({existing.overall_status}) — run reset_tenders_seed() before reseeding the base fixture.")
		if commit:
			frappe.db.commit()
		return {"ok": True, "idempotent": True, "tender": existing.name}

	if not prereqs["handoff"]:
		frappe.throw(f"The canonical Requisition's Authorised Requisition Handoff is already consumed (by {prereqs.get('existing_consumer') or 'another Tender'}) — run reset_tenders_seed() first.")
	handoff = prereqs["handoff"]

	_clock("start")
	with _as(OFFICER):
		started = cmd.start_tender(handoff=handoff, idempotency_key=_key("start"))
	name = started["tender"]
	root = frappe.get_doc("Tender", name)

	with _as(OFFICER):
		saved = cmd.save_tender_draft(tender=name, values=officer_values(), expected_record_version=root.record_version, idempotency_key=_key("save-v1"))
		if not saved.get("ok", True):
			frappe.throw(f"Tenders seed: officer values refused {saved.get('errors')}")
	root.reload()

	_clock("submit_v1")
	with _as(OFFICER):
		submitted = lifecycle.submit_tender_for_approval(tender=name, expected_record_version=root.record_version, idempotency_key=_key("submit-v1"))
	root.reload()

	_clock("return")
	with _as(HOPF):
		returned = lifecycle.return_tender_for_correction(
			tender=name, task=submitted["task"], reason="Confirm the manufacturer authorisation criterion is proportionate to this purchase and reconfirm the tender security amount.",
			affected_task="Supplier and contract requirements", expected_record_version=root.record_version, idempotency_key=_key("return"),
		)
	root.reload()

	_clock("resubmit_v2")
	with _as(OFFICER):
		resubmitted = lifecycle.submit_tender_for_approval(tender=name, expected_record_version=root.record_version, idempotency_key=_key("resubmit-v2"))
	root.reload()

	_clock("approve")
	with _as(HOPF):
		approved = lifecycle.approve_tender_package(tender=name, task=resubmitted["task"], expected_record_version=root.record_version, idempotency_key=_key("approve"))
	root.reload()

	_clock("authorise")
	with _as(AO):
		authorised = publication.authorise_tender_publication(tender=name, task=approved["task"], expected_record_version=root.record_version, idempotency_key=_key("authorise"))
	root.reload()

	confirm_steps = ("confirm_1", "confirm_2", "confirm_3", "confirm_4")
	for channel, step in zip(CHANNELS, confirm_steps):
		_clock(step)
		online = channel in configuration_gateway.ONLINE_CHANNELS
		with _as(HOPF):
			publication.confirm_publication_channel(
				tender=name, channel=channel, available_at=AVAILABLE_AT, evidence_reference=f"{channel}-MOH-2027-033", evidence_file=_evidence_file(f"{channel}.png"),
				package_digest=frappe.db.get_value("Tender Publication", authorised["publication"], "package_digest"), public_url=f"https://portal.example.test/{channel.lower()}" if online else "",
				url_not_applicable_reason="" if online else "Physical channel", attestation_confirmed=True, expected_record_version=root.record_version, idempotency_key=_key(f"confirm-{channel}"),
			)
		root.reload()

	_clock("addendum_draft")
	with _as(OFFICER):
		created = addenda.create_addendum_draft(tender=name, expected_record_version=root.record_version, idempotency_key=_key("addendum-draft"))
		addendum = created["addendum"]["name"]
		root.reload()
		saved_addendum = addenda.update_addendum_draft(tender=name, addendum=addendum, values=ADDENDUM_VALUES, expected_record_version=root.record_version, idempotency_key=_key("addendum-save"))
		if not saved_addendum.get("ok", True):
			frappe.throw(f"Tenders seed: addendum values refused {saved_addendum.get('errors')}")
		root.reload()
		addenda.submit_addendum_for_issue(tender=name, addendum=addendum, expected_record_version=root.record_version, idempotency_key=_key("addendum-submit"))
	root.reload()
	with _as(HOPF):
		addenda.issue_addendum(tender=name, addendum=addendum, expected_record_version=root.record_version, idempotency_key=_key("addendum-issue"))
	root.reload()

	_clock("addendum_confirm")
	for channel in CHANNELS:
		online = channel in configuration_gateway.ONLINE_CHANNELS
		with _as(HOPF):
			addenda.confirm_addendum_publication_channel(
				tender=name, addendum=addendum, channel=channel, available_at=CLOCK["addendum_confirm"], evidence_reference=f"{channel}-ADD-MOH-2027-033",
				evidence_file=_evidence_file(f"{channel}-addendum.png"), addendum_digest=frappe.db.get_value("Tender Addendum", addendum, "addendum_digest"),
				public_url=f"https://portal.example.test/{channel.lower()}/addendum" if online else "", url_not_applicable_reason="" if online else "Physical channel",
				attestation_confirmed=True, expected_record_version=root.record_version, idempotency_key=_key(f"addendum-confirm-{channel}"),
			)
		root.reload()

	_clock("inquiry_received")
	with _as(PRODUCER):
		received = inquiries.receive_addendum_inquiry(
			tender=name, addendum=addendum, candidate_identity="SUP-MOH-2027-0001", question="Does the clarified delivery point apply to all lots under this Tender?",
			received_at=CLOCK["inquiry_received"], inbound_event_id=_key("inquiry-1"),
		)
	inquiry = received["inquiry"]
	root.reload()

	_clock("inquiry_answered")
	with _as(OFFICER):
		inquiries.respond_to_addendum_inquiry(
			tender=name, inquiry=inquiry, response="The clarified delivery point applies to all lots under this Tender. No other delivery terms change.",
			affects_requirements=False, expected_record_version=root.record_version, idempotency_key=_key("inquiry-respond"),
		)
	root.reload()

	_clock("close")
	closed = submission_close.close_tender_submission_period(tender=name, idempotency_key=_key("close"), user="Administrator", force=True)

	frappe.flags.kt_tenders_clock = None
	if commit:
		frappe.db.commit()
	return {"ok": True, "idempotent": False, "tender": name, "addendum": addendum, "inquiry": inquiry, "handoff": closed.get("handoff")}


TENDER_DOCTYPES = (
	"Tender Event", "Tender Document", "Tender Submission Handoff", "Tender Channel Confirmation", "Tender Addendum Inquiry", "Tender Addendum",
	"Tender Cancellation", "Tender Publication", "Tender Decision", "Tender Task", "Tender Version", "Tender",
)


def reset_tenders_seed(*, commit: bool = False) -> dict[str, int]:
	"""Removes the canonical Tender (every child row, then the root) and
	releases its Requisition handoff so `upsert_tenders_base()` can rebuild
	from a clean, unconsumed state. Never touches the Requisitions stage's
	own rows — this stage owns only what it created."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import COMBINED_ITEM_TITLE, _plan_item_id

	_guard()
	frappe.set_user("Administrator")
	deleted: dict[str, int] = {}
	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	requisition = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id}, "name") if plan_item_id else None
	tender = frappe.db.get_value("Tender", {"requisition": requisition}, "name") if requisition else None
	if tender:
		for doctype in TENDER_DOCTYPES[:-1]:
			count = frappe.db.count(doctype, {"tender": tender})
			frappe.db.delete(doctype, {"tender": tender})
			if count:
				deleted[doctype] = count
		frappe.db.delete("Tender Command Journal", {"document_name": tender})
		frappe.db.delete("Tender", {"name": tender})
		deleted["Tender"] = 1
	frappe.db.delete("Tender Command Journal", {"idempotency_key": ("like", "tnd-seed:%")})
	if requisition:
		handoff = frappe.db.get_value("Authorised Requisition Handoff", {"requisition": requisition}, "name")
		if handoff and frappe.db.get_value("Authorised Requisition Handoff", handoff, "consumed_at"):
			from kentender_procurement.procurement_requisitions.services import handoff as handoff_service
			from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION

			with _as(HOPF):
				handoff_service.release_handoff_consumption(handoff=handoff, tender=tender or "", reason="Tenders canonical seed reset.", idempotency_key=_key("release"), user=HOPF)
	if commit:
		frappe.db.commit()
	return {"ok": True, "namespace": NS, "deleted": deleted}


def wipe_all_tenders() -> dict[str, int]:
	"""Unconditional: every row this module owns, regardless of which
	Requisition it references. `reset_tenders_seed` selects by looking up
	the current combined Plan Item's title, then its Requisition, then the
	Tender tied to that Requisition — the same live-parent lookup pattern
	Requisitions/Planning had, and the same failure mode: a Tender whose
	Requisition (or that Requisition's own Plan Item) was already deleted
	by some other, unrelated cycle has no parent left to be found through,
	and survives every wipe forever. Only safe unconditionally under a
	full site `wipe`, which clears Requisitions/Planning in the same pass."""
	deleted: dict[str, int] = {}
	for doctype in TENDER_DOCTYPES:
		deleted[doctype] = frappe.db.count(doctype)
		frappe.db.delete(doctype)
	journal = frappe.db.count("Tender Command Journal")
	frappe.db.delete("Tender Command Journal")
	deleted["Tender Command Journal"] = journal
	return deleted


def validate_tenders_seed() -> list[dict[str, Any]]:
	"""One row per §13.3 event this fixture must have produced, plus the
	digest/idempotency facts the plan's own gate names. Never mutates."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import COMBINED_ITEM_TITLE, _plan_item_id

	rows: list[dict[str, Any]] = []

	def check(ok: bool, label: str) -> None:
		rows.append({"ok": bool(ok), "check": label, "detail": "" if ok else "failed"})

	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	requisition = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id}, "name") if plan_item_id else None
	check(bool(requisition), f"canonical Requisition '{COMBINED_ITEM_TITLE}' exists")
	tender = frappe.db.get_value("Tender", {"requisition": requisition}, ["name", "overall_status", "record_version"], as_dict=True) if requisition else None
	check(bool(tender), "a Tender exists on the canonical Requisition")
	if not tender:
		return rows
	check(tender.overall_status == "Submission period ended", f"overall_status is 'Submission period ended' (got {tender.overall_status!r})")
	versions = frappe.get_all("Tender Version", filters={"tender": tender.name}, fields=["version_number", "status"], order_by="version_number asc")
	check(len(versions) == 2, f"exactly two Tender Versions exist (got {len(versions)})")
	check(bool(versions) and versions[0]["status"] == "Returned", "Version 1 is Returned")
	check(len(versions) > 1 and versions[-1]["status"] == "Approved", "Version 2 is Approved")
	publication = frappe.db.get_value("Tender Publication", {"tender": tender.name}, ["name", "publication_status", "published_at"], as_dict=True)
	check(bool(publication) and publication.publication_status == "Published", "the publication is Published")
	check(bool(publication) and cstr(publication.published_at) == AVAILABLE_AT, f"published_at is {AVAILABLE_AT} (D15 max available_at)")
	confirmations = frappe.get_all("Tender Channel Confirmation", filters={"publication": publication.name if publication else "", "subject_type": "Publication", "status": "Confirmed"}, pluck="name")
	check(len(confirmations) == 4, f"all four publication channels are Confirmed (got {len(confirmations)})")
	addendum = frappe.db.get_value("Tender Addendum", {"tender": tender.name}, ["name", "status", "revised_submission_deadline"], as_dict=True)
	check(bool(addendum) and addendum.status == "Issued", "the addendum is Issued")
	check(bool(addendum) and cstr(addendum.revised_submission_deadline) == "2027-06-12 11:00:00", "the addendum's revised submission deadline is 12 Jun 2027, 11:00 EAT")
	addendum_confirmations = frappe.get_all("Tender Channel Confirmation", filters={"subject_type": "Addendum", "subject_id": addendum.name if addendum else "", "status": "Confirmed"}, pluck="name")
	check(len(addendum_confirmations) == 4, f"all four addendum channels are Confirmed (got {len(addendum_confirmations)})")
	inquiries_rows = frappe.get_all("Tender Addendum Inquiry", filters={"tender": tender.name}, fields=["status"])
	check(len(inquiries_rows) == 1, f"exactly one addendum inquiry exists (got {len(inquiries_rows)})")
	check(bool(inquiries_rows) and inquiries_rows[0]["status"] == "Answered", "the inquiry is Answered")
	handoff = frappe.db.get_value("Tender Submission Handoff", {"tender": tender.name}, "name")
	check(bool(handoff), "one Tender Submission Handoff was written")
	check(tender.name == frappe.db.get_value("Tender Submission Handoff", handoff, "tender") if handoff else False, "the handoff references this Tender")
	events = frappe.get_all("Tender Event", filters={"tender": tender.name}, pluck="event_type")
	for expected in ("PublicationAuthorised", "AddendumIssued", "AddendumInquiryReceived", "AddendumInquiryAnswered", "TenderSubmissionPeriodEnded"):
		check(expected in events, f"the outbox carries a {expected} event")
	# second-run idempotency: the base upsert must be a no-op on an already-ended Tender
	rerun = upsert_tenders_base(commit=False)
	check(rerun.get("idempotent") is True, "a second upsert_tenders_base() call is idempotent")
	check(rerun.get("tender") == tender.name, "the idempotent rerun names the same Tender")
	return rows
