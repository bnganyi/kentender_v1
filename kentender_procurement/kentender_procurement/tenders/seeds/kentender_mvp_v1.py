# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §13.3 — the deterministic canonical Tender lifecycle,
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
08:00, so published_at = 08:00 under plan D15) -> Afya Digital Supplies
Limited registers as a Tender candidate through the Start-bid stand-in
19 May 09:20 -> its general clarification arrives 26 May 09:00 and is
answered to all registered candidates 11:00 (notice Delivered 11:01) ->
HOPF decides one addendum 31 May 08:30, confirmed through the four channels
09:03–09:07 with availability 08:50–09:00, so it is effective 09:00 and the
deadline moves to 12 Jun 11:00 (its candidate notice is Delivered 09:08) ->
the scheduler closes the submission period 12 Jun 11:00 with its handoff.

Two deliberate departures from the §10.1/§13.3 text (FOLLOW_UPS FU-28/29):
the addendum notice is Delivered at 09:08, not 09:02, because the addendum
only becomes effective (and its audience is frozen) at the final 09:07
attestation; and §13.3's "1 Jun 11:00 no-effect response" row is not
seeded because TPR-DES-09's fixture shows exactly one clarification.

Idempotent: a rerun that finds the canonical Tender already at
"Submission period ended" returns it untouched."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.seeds import clear

NS = "KENTENDER_MVP_1_R1_TND"

OFFICER = "brian.wafula@moh.example.test"
HOPF = "charles.mutiso@moh.example.test"
AO = "amina.hassan@moh.example.test"
AUDITOR = "naomi.chebet@moh.example.test"
PRODUCER = "tender.inquiry.producer@moh.example.test"  # the bidder-facing service identity (plan D8′)

DELIVERY_LOCATION = "Ministry of Health Headquarters, Afya House, Nairobi"
CONTACT_OFFICE = "Ministry of Health Procurement Office"
CHANNELS = ("STATE_PORTAL", "MINISTRY_WEBSITE", "NOTICE_BOARD", "NATIONAL_NEWSPAPERS")
#: §10.1 publication confirmations: (reference, public URL, evidence file, attested step).
PUBLICATION_EVIDENCE = {
	"STATE_PORTAL": ("PPIP-MOH-2027-033", "https://portal.example.test/tenders/PPIP-MOH-2027-033", "PPIP-MOH-2027-033.pdf", "confirm_1"),
	"MINISTRY_WEBSITE": ("WEB-MOH-2027-033", "https://health.example.test/tenders/TND-MOH-2027-033", "WEB-MOH-2027-033.pdf", "confirm_2"),
	"NOTICE_BOARD": ("NB-MOH-2027-033", "", "NB-MOH-2027-033.jpg", "confirm_3"),
	"NATIONAL_NEWSPAPERS": ("NP-MOH-2027-033", "", "NP-MOH-2027-033.pdf", "confirm_4"),
}
#: §10.1 addendum confirmations: (reference, URL, evidence, available at, attested step).
ADDENDUM_EVIDENCE = {
	"STATE_PORTAL": ("PPIP-MOH-2027-033-A1", "https://portal.example.test/tenders/PPIP-MOH-2027-033/addenda/1", "PPIP-MOH-2027-033-A1.pdf", "2027-05-31 08:50:00", "addendum_confirm_1"),
	"MINISTRY_WEBSITE": ("WEB-MOH-2027-033-A1", "https://health.example.test/tenders/TND-MOH-2027-033/addenda/1", "WEB-MOH-2027-033-A1.pdf", "2027-05-31 08:50:00", "addendum_confirm_2"),
	"NOTICE_BOARD": ("NB-MOH-2027-033-A1", "", "NB-MOH-2027-033-A1.jpg", "2027-05-31 08:55:00", "addendum_confirm_3"),
	"NATIONAL_NEWSPAPERS": ("NP-MOH-2027-033-A1", "", "NP-MOH-2027-033-A1.pdf", "2027-05-31 09:00:00", "addendum_confirm_4"),
}
# The candidate registers through Bid Submission's Start bid (TPR FU-25): the
# arrangement identity is minted there, so only the facts are fixed here.
CANDIDATE = {"candidate_name": "Afya Digital Supplies Limited", "notice_address": "tenders@afyadigital.example"}
QUESTION = "May the two comparable contracts be from different customers?"
ANSWER = "Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer."
RETURN_COMMENT = "Confirm whether manufacturer authorisation is necessary and update the supplier evidence requirement."

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
	"candidate": "2027-05-19 09:20:00",
	"clarification_received": "2027-05-26 09:00:00",
	"clarification_answered": "2027-05-26 11:00:00",
	"clarification_delivered": "2027-05-26 11:01:00",
	"addendum_draft": "2027-05-31 08:15:00",
	"addendum_submit": "2027-05-31 08:25:00",
	"addendum_issue": "2027-05-31 08:30:00",
	"addendum_confirm_1": "2027-05-31 09:03:00",
	"addendum_confirm_2": "2027-05-31 09:04:00",
	"addendum_confirm_3": "2027-05-31 09:06:00",
	"addendum_confirm_4": "2027-05-31 09:07:00",
	"addendum_delivered": "2027-05-31 09:08:00",
	"close": "2027-06-12 11:00:00",
}
AVAILABLE_AT = "2027-05-15 08:00:00"

ADDENDUM_VALUES = {
	"change_class": "Administrative clarification",
	"affected_area": "Goods/delivery schedule",
	"affected_reference_key": "delivery_location",
	"revised_value": "Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi",
	"reason": "The published address omitted the internal delivery point",
	"materiality_statement": "Same site; no change to scope, quantity, value or evaluation basis.",
	"revised_submission_deadline": "2027-06-12 11:00:00",
}


OPEN_STATUS = "Published — open"
CLOSED_STATUS = "Submission period ended"


class CanonicalTenderNeedsRebuild(frappe.ValidationError):
	"""The canonical Tender exists but not in the shape this run builds on
	(left open for bids, closed, or half-built by a failed run). The
	Requisition's hand-off is consumed once, so `canonical.run` rebuilds."""


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
	"""A real file of the type its name states (the integrity check sniffs
	the content): a minimal PDF, or a one-pixel JPEG/PNG."""
	from io import BytesIO

	from PIL import Image

	extension = file_name.rsplit(".", 1)[-1].lower()
	if extension == "pdf":
		content = _minimal_pdf(file_name)
	else:
		buffer = BytesIO()
		Image.new("RGB", (1, 1), (255, 255, 255)).save(buffer, format="JPEG" if extension in ("jpg", "jpeg") else "PNG")
		content = buffer.getvalue()
	return frappe.get_doc({"doctype": "File", "file_name": file_name, "is_private": 1, "content": content}).insert(ignore_permissions=True).name


def _minimal_pdf(title: str) -> bytes:
	"""A one-page PDF with a correct cross-reference table — Frappe's upload
	check parses every PDF (frappe.utils.pdf.pdf_contains_js), so a header
	alone is refused."""
	text = f"KenTender seed publication evidence: {title}".replace("(", "[").replace(")", "]")
	stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
	objects = [
		b"<< /Type /Catalog /Pages 2 0 R >>",
		b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
		b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
		b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
	]
	out = bytearray(b"%PDF-1.4\n")
	offsets = []
	for number, body in enumerate(objects, start=1):
		offsets.append(len(out))
		out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
	xref = len(out)
	out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
	for offset in offsets:
		out += f"{offset:010d} 00000 n \n".encode()
	out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
	return bytes(out)


def _seed_transport(delivered_step: str):
	"""A provider that confirms delivery at the §13.3 instant (plan W3)."""

	def transport(notice) -> dict[str, Any]:
		frappe.flags.kt_tenders_clock = CLOCK[delivered_step]
		return {"result": "Delivered", "provider_reference": f"seed-delivery:{notice.name}", "failure_reason": ""}

	return transport


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
	from kentender_procurement.tenders.services import candidate_gateway
	from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

	candidate_gateway.ensure_producer_role()
	if not frappe.db.exists("User", PRODUCER):
		user = frappe.get_doc({"doctype": "User", "email": PRODUCER, "first_name": "Tender Inquiry Producer", "send_welcome_email": 0, "enabled": 1}).insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", PRODUCER)
	if frappe.db.get_value("User", PRODUCER, "user_type") != "System User":
		user.add_roles("Desk User")
	if INQUIRY_PRODUCER_ROLE not in {r.role for r in user.roles}:
		user.add_roles(INQUIRY_PRODUCER_ROLE)
	return PRODUCER


def register_candidate(*, tender_reference: str, at, supplier: dict[str, Any] | None = None) -> str:
	"""A candidate registered by Bid Submission's Start bid through the
	`kt_tender_seed_candidate` hook (the canonical Afya bid unless `supplier`
	names another); returns its registration identity."""
	hooks = frappe.get_hooks("kt_tender_seed_candidate") or []
	if not hooks:
		frappe.throw("No candidate seed is installed (hook kt_tender_seed_candidate): the Tenders stand-in is retired (FU-25).")
	return frappe.get_attr(hooks[-1])(tender_reference=tender_reference, at=at, supplier=supplier)


def upsert_tenders_base(*, commit: bool = False, interleave=None, stop_before_close: bool = False) -> dict[str, Any]:
	"""§13.3 fixture — the primary Tender lifecycle through to a closed
	submission period, built through the real commands. Idempotent: a
	rerun that finds the canonical Tender already ended returns it
	untouched.

	`stop_before_close` (owner, 4 Oct 2026: a demo Tender anyone can see and
	bid on) ends the story just before the 12 Jun 2027 deadline, leaving the
	Tender published and open. A Tender in the other shape raises
	`CanonicalTenderNeedsRebuild`.

	`interleave(step, tender=…, tender_reference=…)` lets a downstream seed
	act at named moments of this chronology without this module knowing
	what it does (BDS-CHG-001 v0.8 plan D19: the canonical bid's lifecycle):
	"candidate_registered", "addendum_effective", "before_close" and
	"closed". Each callback's result is returned under `interleaved`."""
	interleaved: dict[str, Any] = {}

	def _step(step: str) -> None:
		if interleave is not None:
			root_now = frappe.db.get_value("Tender", name, "tender_reference")
			interleaved[step] = interleave(step, tender=name, tender_reference=root_now)

	from kentender_procurement.std_templates.services import installer as std_installer
	from kentender_procurement.tenders.services import addenda, clarifications, configuration_gateway, draft_commands as cmd, lifecycle, publication, submission_close

	_guard()
	std_installer.ensure_site_release()
	from kentender_core.seeds import site_setup

	site_setup._seed_publication_obligations()
	ensure_producer_role()
	prereqs = verify_prerequisites()

	existing = frappe.db.get_value("Tender", {"requisition": prereqs["requisition"]}, ["name", "overall_status", "fixture_namespace"], as_dict=True)
	if existing:
		wanted = OPEN_STATUS if stop_before_close else CLOSED_STATUS
		if existing.overall_status != wanted:
			frappe.throw(
				f"The canonical Tender {existing.name} is {existing.overall_status!r}, not {wanted!r}. Rebuild the canonical world: make seed-canonical REBUILD=True.",
				exc=CanonicalTenderNeedsRebuild,
			)
		# Seeded before 26 Sep 2026 without the stamp; its other rows keep
		# theirs until the next rebuild.
		if existing.fixture_namespace != NS:
			frappe.db.set_value("Tender", existing.name, "fixture_namespace", NS, update_modified=False)
		if commit:
			frappe.db.commit()
		return {"ok": True, "idempotent": True, "tender": existing.name}

	if not prereqs["handoff"]:
		frappe.throw(f"The canonical Requisition's Authorised Requisition Handoff is already consumed (by {prereqs.get('existing_consumer') or 'another Tender'}) — run reset_tenders_seed() first.")
	handoff = prereqs["handoff"]

	_clock("start")
	# The start consumes Requisitions' handoff, which stamps the process
	# clock rather than the Tenders clock flag: freeze it too, so fixture 6's
	# consumption instant (REQ-CHG-001 §16.4, 20 Mar 2027 09:00) is recorded
	# by the command itself (until 26 Sep 2026 it carried the seeding time).
	from kentender_core.seeds import clock as core_clock

	with _as(OFFICER), core_clock.at(CLOCK["start"]):
		started = cmd.start_tender(handoff=handoff, idempotency_key=_key("start"), fixture_namespace=NS)
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
			tender=name, task=submitted["task"], reason=RETURN_COMMENT,
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

	for channel in CHANNELS:
		reference, url, evidence, step = PUBLICATION_EVIDENCE[channel]
		_clock(step)
		with _as(HOPF):
			publication.confirm_publication_channel(
				tender=name, channel=channel, available_at=AVAILABLE_AT, evidence_reference=reference, evidence_file=_evidence_file(evidence),
				package_digest=frappe.db.get_value("Tender Publication", authorised["publication"], "package_digest"), public_url=url,
				attestation_confirmed=True, expected_record_version=root.record_version, idempotency_key=_key(f"confirm-{channel}"),
			)
		root.reload()

	# §13.3: David Ouma starts Afya's bid through Bid Submission's Start bid,
	# which registers the candidate (TPR FU-25 retired the Tenders stand-in).
	_clock("candidate")
	candidate = register_candidate(tender_reference=root.tender_reference, at=CLOCK["candidate"])
	_step("candidate_registered")

	frappe.flags.kt_tenders_notice_sync = True
	_clock("clarification_received")
	with _as(PRODUCER):
		received = clarifications.receive_tender_clarification(
			tender=name, candidate_registration_id=candidate, question=QUESTION, received_at=CLOCK["clarification_received"], inbound_event_id=_key("clarification-1"),
		)
	clarification = received["clarification"]
	root.reload()
	_clock("clarification_answered")
	frappe.flags.kt_tenders_notice_transport = _seed_transport("clarification_delivered")
	with _as(OFFICER):
		clarifications.respond_to_tender_clarification(
			tender=name, clarification=clarification, response=ANSWER, affects_published_tender=False, response_audience="All registered candidates",
			expected_record_version=root.record_version, idempotency_key=_key("clarification-respond"),
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
		_clock("addendum_submit")
		addenda.submit_addendum_for_issue(tender=name, addendum=addendum, expected_record_version=root.record_version, idempotency_key=_key("addendum-submit"))
	root.reload()
	_clock("addendum_issue")
	with _as(HOPF):
		addenda.issue_addendum(tender=name, addendum=addendum, expected_record_version=root.record_version, idempotency_key=_key("addendum-issue"))
	root.reload()

	frappe.flags.kt_tenders_notice_transport = _seed_transport("addendum_delivered")
	for channel in CHANNELS:
		reference, url, evidence, available_at, step = ADDENDUM_EVIDENCE[channel]
		_clock(step)
		with _as(HOPF):
			addenda.confirm_addendum_publication_channel(
				tender=name, addendum=addendum, channel=channel, available_at=available_at, evidence_reference=reference, evidence_file=_evidence_file(evidence),
				addendum_digest=frappe.db.get_value("Tender Addendum", addendum, "addendum_digest"), public_url=url,
				attestation_confirmed=True, expected_record_version=root.record_version, idempotency_key=_key(f"addendum-confirm-{channel}"),
			)
		root.reload()
	frappe.flags.kt_tenders_notice_transport = None
	frappe.flags.kt_tenders_notice_sync = False
	_step("addendum_effective")
	_step("before_close")
	root.reload()
	frappe.flags.kt_tenders_clock = None
	if stop_before_close:
		if commit:
			frappe.db.commit()
		return {"ok": True, "idempotent": False, "open": True, "tender": name, "addendum": addendum, "clarification": clarification, "interleaved": interleaved}

	_clock("close")
	closed = submission_close.close_tender_submission_period(tender=name, idempotency_key=_key("close"), user="Administrator", force=True)
	_step("closed")

	frappe.flags.kt_tenders_clock = None
	if commit:
		frappe.db.commit()
	return {"ok": True, "idempotent": False, "tender": name, "addendum": addendum, "clarification": clarification, "handoff": closed.get("handoff"), "interleaved": interleaved}


def reset_tenders_seed(*, commit: bool = False) -> dict[str, int]:
	"""Removes the canonical Tender (every child row, then the root). Never
	touches the Requisitions stage's own rows — this stage owns only what it
	created — so a fresh `upsert_tenders_base()` needs an unconsumed handoff,
	i.e. the Requisitions stage rebuilt as well (see the note below)."""
	from kentender_procurement.procurement_requisitions.seeds.kentender_mvp_v1 import COMBINED_ITEM_TITLE, _plan_item_id

	_guard()
	frappe.set_user("Administrator")
	deleted: dict[str, int] = {}
	plan_item_id = _plan_item_id(COMBINED_ITEM_TITLE)
	requisition = frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id}, "name") if plan_item_id else None
	tender = frappe.db.get_value("Tender", {"requisition": requisition}, "name") if requisition else None
	if tender:
		deleted = clear.delete_tenders([tender])
	frappe.db.delete("Tender Command Journal", {"idempotency_key": ("like", "tnd-seed:%")})
	# REQ-CHG-001 v1.11 (handoff v1.4) has no command that releases a consumed
	# handoff: consumption is final. This stage therefore never touches the
	# Requisition's handoff; rebuilding the Tender needs the Requisitions stage
	# rebuilt too, which `canonical.run(rebuild=True)` does straight after this.
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
	return clear.wipe_all_tender_rows()


def validate_tenders_seed(*, open_tender: bool = False) -> list[dict[str, Any]]:
	"""One row per §13.3 event this fixture must have produced, plus the
	digest/idempotency facts the plan's own gate names. Never mutates.
	`open_tender`: the story stopped before the deadline, so the Tender is
	open and nothing about its close is expected."""
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
	check(frappe.db.get_value("Tender", tender.name, "fixture_namespace") == NS, f"the Tender carries the {NS} stamp")
	wanted = OPEN_STATUS if open_tender else CLOSED_STATUS
	check(tender.overall_status == wanted, f"overall_status is {wanted!r} (got {tender.overall_status!r})")
	versions = frappe.get_all("Tender Version", filters={"tender": tender.name}, fields=["version_number", "status"], order_by="version_number asc")
	check(len(versions) == 2, f"exactly two Tender Versions exist (got {len(versions)})")
	check(bool(versions) and versions[0]["status"] == "Returned", "Version 1 is Returned")
	check(len(versions) > 1 and versions[-1]["status"] == "Approved", "Version 2 is Approved")
	publication = frappe.db.get_value("Tender Publication", {"tender": tender.name}, ["name", "publication_status", "published_at"], as_dict=True)
	check(bool(publication) and publication.publication_status == "Published", "the publication is Published")
	check(bool(publication) and cstr(publication.published_at) == AVAILABLE_AT, f"published_at is {AVAILABLE_AT} (D15 max available_at)")
	confirmations = frappe.get_all("Tender Channel Confirmation", filters={"publication": publication.name if publication else "", "subject_type": "Tender package", "status": "Confirmed"}, pluck="name")
	check(len(confirmations) == 4, f"all four publication channels are Confirmed (got {len(confirmations)})")
	addendum = frappe.db.get_value("Tender Addendum", {"tender": tender.name}, ["name", "status", "revised_submission_deadline"], as_dict=True)
	check(bool(addendum) and addendum.status == "Issued", "the addendum is Issued")
	check(bool(addendum) and cstr(addendum.revised_submission_deadline) == "2027-06-12 11:00:00", "the addendum's revised submission deadline is 12 Jun 2027, 11:00 EAT")
	addendum_confirmations = frappe.get_all("Tender Channel Confirmation", filters={"subject_type": "Addendum", "subject_id": addendum.name if addendum else "", "status": "Confirmed"}, pluck="name")
	check(len(addendum_confirmations) == 4, f"all four addendum channels are Confirmed (got {len(addendum_confirmations)})")
	check(bool(addendum) and cstr(frappe.db.get_value("Tender Addendum", addendum.name, "issued_at")) == "2027-05-31 09:00:00", "the addendum is effective at 31 May 2027, 09:00 EAT (latest availability)")
	definitions = frappe.get_all("Tender Bid Definition", filters={"tender": tender.name}, fields=["status", "definition_version"], order_by="definition_version asc")
	check([d["status"] for d in definitions] == ["Superseded", "Effective"], f"the original definition is Superseded and the addendum's successor is Effective (got {[d['status'] for d in definitions]})")
	from kentender_procurement.tenders.services import candidate_gateway

	candidates = [c["candidate_registration_id"] for c in candidate_gateway.candidate_audience(tender=tender.name, at=CLOCK["clarification_received"])]
	check(
		len(candidates) == 1 and candidate_gateway.candidate_name(tender=tender.name, candidate_registration_id=candidates[0]) == CANDIDATE["candidate_name"],
		f"Afya Digital Supplies Limited is the one registered candidate (got {candidates})",
	)
	clarification_rows = frappe.get_all("Tender Clarification", filters={"tender": tender.name}, fields=["status", "response_audience"])
	check(len(clarification_rows) == 1, f"exactly one supplier clarification exists (got {len(clarification_rows)})")
	check(bool(clarification_rows) and clarification_rows[0]["status"] == "Answered" and clarification_rows[0]["response_audience"] == "All registered candidates", "the clarification is Answered to all registered candidates")
	notices = frappe.get_all("Tender Candidate Notice", filters={"tender": tender.name}, fields=["notice_type", "status"], order_by="creation asc")
	check([(n["notice_type"], n["status"]) for n in notices] == [("Clarification response", "Delivered"), ("Addendum issued", "Delivered")], f"one Delivered clarification notice and one Delivered addendum notice (got {notices})")
	handoff = frappe.db.get_value("Tender Submission Handoff", {"tender": tender.name}, "name")
	if open_tender:
		check(not handoff, "no Tender Submission Handoff yet (the Tender is open)")
	else:
		check(bool(handoff), "one Tender Submission Handoff was written")
		check(tender.name == frappe.db.get_value("Tender Submission Handoff", handoff, "tender") if handoff else False, "the handoff references this Tender")
	events = frappe.get_all("Tender Event", filters={"tender": tender.name}, pluck="event_type")
	for expected in ("PublicationAuthorised", "AddendumIssued", "ClarificationReceived", "ClarificationAnswered", *(() if open_tender else ("TenderSubmissionPeriodEnded",))):
		check(expected in events, f"the outbox carries a {expected} event")
	# second-run idempotency: the base upsert must be a no-op on a Tender already in this shape
	rerun = upsert_tenders_base(commit=False, stop_before_close=open_tender)
	check(rerun.get("idempotent") is True, "a second upsert_tenders_base() call is idempotent")
	check(rerun.get("tender") == tender.name, "the idempotent rerun names the same Tender")
	return rows
